# -*- coding: utf-8 -*-
from datetime import datetime, time, timedelta

import pytz

from odoo import _, api, fields, models

TOP_LIMIT = 5
SOLD_STATES = ('paid', 'done', 'invoiced')
PURCHASE_STATES = ('purchase', 'done')


class ShopDashboard(models.AbstractModel):
    """Data provider of the Script Shop Management dashboard (no table)."""
    _name = 'shop.dashboard'
    _description = "Shop Dashboard"

    @api.model
    def _get_shops(self):
        return self.env['pos.config'].search([('is_shop', '=', True)])

    @api.model
    def get_shops(self):
        """Cards of the dashboard: one for all the shops, then one per shop."""
        company = self.env.company
        shops = self._get_shops()
        cards = [{
            'id': False,
            'name': _("All shops"),
            'image_url': f'/web/image/res.company/{company.id}/logo',
            'shop_count': len(shops),
        }]
        for shop in shops:
            cards.append({
                'id': shop.id,
                'name': shop.name,
                'image_url': f'/web/image/pos.config/{shop.id}/shop_image?unique={shop.write_date.timestamp()}'
                             if shop.shop_image else '/web/static/img/placeholder.png',
                'shop_count': 1,
            })
        return cards

    @api.model
    def _to_utc(self, day, end=False):
        """Convert a local date (YYYY-MM-DD) to a naive UTC datetime, in the user's timezone."""
        tz = pytz.timezone(self.env.user.tz or 'UTC')
        day = fields.Date.from_string(day)
        local = tz.localize(datetime.combine(day + timedelta(days=1 if end else 0), time.min))
        return local.astimezone(pytz.utc).replace(tzinfo=None)

    @api.model
    def get_data(self, shop_id, date_from, date_to):
        """Indicators of one shop (or of all the shops when shop_id is falsy) over a period."""
        shops = self.env['pos.config'].browse(shop_id) if shop_id else self._get_shops()
        start, end = self._to_utc(date_from), self._to_utc(date_to, end=True)
        currency = self.env.company.currency_id
        return {
            'currency_id': currency.id,
            'purchases': self._get_purchases(shops, start, end),
            'sales': self._get_sales(shops, start, end),
            'stock': self._get_stock(shops, start, end),
            'top_products': self._get_products(shops, start, end, most=True),
            'flop_products': self._get_products(shops, start, end, most=False),
            'timeline': self._get_timeline(shops, start, end),
            'by_shop': self._get_by_shop(shops, start, end) if not shop_id else [],
        }

    @api.model
    def _get_sold_orders(self, shops, start, end):
        return self.env['pos.order'].search([
            ('config_id', 'in', shops.ids),
            ('state', 'in', SOLD_STATES),
            ('date_order', '>=', start),
            ('date_order', '<', end),
        ])

    @api.model
    def _get_timeline(self, shops, start, end):
        """Real turnover and purchases over time: one point per day, or per month on long periods."""
        tz = pytz.timezone(self.env.user.tz or 'UTC')

        def local_day(value):
            return pytz.utc.localize(value).astimezone(tz).date()

        first, last = local_day(start), local_day(end - timedelta(seconds=1))
        monthly = (last - first).days > 62
        bucket = (lambda d: d.replace(day=1)) if monthly else (lambda d: d)
        label_format = '%m/%Y' if monthly else '%d/%m'

        keys, day = [], first
        while day <= last:
            if not keys or bucket(day) != keys[-1]:
                keys.append(bucket(day))
            day += timedelta(days=1)
        sales, purchases = dict.fromkeys(keys, 0.0), dict.fromkeys(keys, 0.0)

        for order in self._get_sold_orders(shops, start, end):
            sales[bucket(local_day(order.date_order))] += order.amount_total - order.amount_tax
        purchase_orders = self.env['purchase.order'].search([
            ('shop_id', 'in', shops.ids),
            ('state', 'in', PURCHASE_STATES),
            ('date_approve', '>=', start),
            ('date_approve', '<', end),
        ])
        for order in purchase_orders:
            purchases[bucket(local_day(order.date_approve))] += order.amount_total
        return {
            'labels': [key.strftime(label_format) for key in keys],
            'sales': [round(sales[key], 2) for key in keys],
            'purchases': [round(purchases[key], 2) for key in keys],
        }

    @api.model
    def _get_by_shop(self, shops, start, end):
        """Real turnover of each shop, for the "all shops" card."""
        orders = self._get_sold_orders(shops, start, end)
        result = []
        for shop in shops:
            shop_orders = orders.filtered(lambda o: o.config_id == shop)
            result.append({
                'id': shop.id,
                'name': shop.name,
                'amount': round(sum(shop_orders.mapped('amount_total')) - sum(shop_orders.mapped('amount_tax')), 2),
            })
        return result

    @api.model
    def _get_purchases(self, shops, start, end):
        orders = self.env['purchase.order'].search([
            ('shop_id', 'in', shops.ids),
            ('state', 'in', PURCHASE_STATES),
            ('date_approve', '>=', start),
            ('date_approve', '<', end),
        ])
        return {'count': len(orders), 'amount': sum(orders.mapped('amount_total'))}

    @api.model
    def _get_sales(self, shops, start, end):
        orders = self._get_sold_orders(shops, start, end)
        refunds = orders.filtered('is_refund')
        return {
            'count': len(orders) - len(refunds),
            'refund_count': len(refunds),
            'amount': sum(orders.mapped('amount_total')),
            # Real turnover: tax excluded, refunds already counted as negative orders
            'real_revenue': sum(orders.mapped('amount_total')) - sum(orders.mapped('amount_tax')),
        }

    @api.model
    def _get_stock(self, shops, start, end):
        locations = shops.mapped('picking_type_id.warehouse_id.lot_stock_id')
        quants = self.env['stock.quant'].search([('location_id', 'child_of', locations.ids)]) if locations else \
            self.env['stock.quant']
        received = self.env['stock.picking'].search_count([
            ('shop_id', 'in', shops.ids),
            ('state', '=', 'done'),
            ('date_done', '>=', start),
            ('date_done', '<', end),
        ])
        return {
            'quantity': sum(quants.mapped('quantity')),
            'value': sum(q.quantity * q.product_id.standard_price for q in quants),
            'received_transfers': received,
        }

    @api.model
    def _get_products(self, shops, start, end, most):
        """Most (or least) sold products of the shops over the period, zero sales included."""
        lines = self.env['pos.order.line']._read_group([
            ('order_id.config_id', 'in', shops.ids),
            ('order_id.state', 'in', SOLD_STATES),
            ('order_id.date_order', '>=', start),
            ('order_id.date_order', '<', end),
        ], ['product_id'], ['qty:sum'])
        sold = {product.id: qty for product, qty in lines}
        if most:
            ranking = sorted(sold.items(), key=lambda item: -item[1])
            ranking = [(pid, qty) for pid, qty in ranking if qty > 0]
        else:
            # Products assigned to the shops but never (or hardly) sold come first
            catalog = self.env['product.product'].search([('product_tmpl_id.shop_ids', 'in', shops.ids)])
            ranking = sorted(((product.id, sold.get(product.id, 0)) for product in catalog),
                             key=lambda item: item[1])
        ranking = ranking[:TOP_LIMIT]
        names = {p.id: p.display_name for p in self.env['product.product'].browse([r[0] for r in ranking])}
        return [{'id': pid, 'name': names[pid], 'qty': qty} for pid, qty in ranking]
