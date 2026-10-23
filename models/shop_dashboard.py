# -*- coding: utf-8 -*-
import base64
from datetime import datetime, time, timedelta

import pytz

from odoo import _, api, fields, models
from odoo.exceptions import AccessError
from odoo.tools.image import image_process

TOP_LIMIT = 5
SOLD_STATES = ('paid', 'done', 'invoiced')
PURCHASE_STATES = ('purchase', 'done')
ONLINE_STATES = ('sale', 'done')


class ShopDashboard(models.AbstractModel):
    """Data provider of the Script Shop Management dashboard (no table).

    A dashboard scope is made of local shops (point of sale sales) and of online shops (website
    orders): a local shop comes with the websites linked to it, a website that is not linked is a
    scope of its own, and "all shops" gathers everything.
    """
    _name = 'shop.dashboard'
    _description = "Shop Dashboard"

    # ----------------------------------------------------------------------- access

    @api.model
    def _check_access_group(self):
        if not self.env.user.has_group('script_shop_management.group_shop_user'):
            raise AccessError(_("You are not allowed to access the shop dashboard."))

    @api.model
    def _get_shops(self):
        return self.env['pos.config'].search([('is_shop', '=', True)])

    @api.model
    def _search_websites(self, domain):
        """Shop websites. The dashboard users do not need website rights: the company rule is applied here."""
        return self.env['website'].sudo().search(
            [('is_shop', '=', True), ('company_id', 'in', self.env.companies.ids), *domain])

    @api.model
    def _get_unlinked_websites(self):
        return self._search_websites([('local_shop_id', '=', False)])

    # ------------------------------------------------------------------------ cards

    @api.model
    def get_shops(self):
        """Cards of the dashboard: all the shops, then each local shop and each online shop of its own."""
        self._check_access_group()
        company = self.env.company
        shops = self._get_shops()
        websites = self._get_unlinked_websites()
        cards = [{
            'key': 'all',
            'id': False,
            'website_id': False,
            'name': _("All shops"),
            'image_url': f'/web/image/res.company/{company.id}/logo',
            'shop_count': len(shops) + len(websites),
        }]
        for shop in shops:
            cards.append({
                'key': f'shop_{shop.id}',
                'id': shop.id,
                'website_id': False,
                'name': shop.name,
                'image_url': f'/web/image/pos.config/{shop.id}/shop_image?unique={shop.write_date.timestamp()}'
                             if shop.shop_image else '/web/static/img/placeholder.png',
                'shop_count': 1,
                'online': bool(self._search_websites([('local_shop_id', '=', shop.id)])),
            })
        for website in websites:
            cards.append({
                'key': f'website_{website.id}',
                'id': False,
                'website_id': website.id,
                'name': website.name,
                'image_url': self._get_website_image_url(website),
                'shop_count': 1,
                'online': True,
            })
        return cards

    @api.model
    def _get_website_image_url(self, website):
        if not website.shop_image:
            return '/web/static/img/placeholder.png'
        thumbnail = image_process(base64.b64decode(website.shop_image), size=(256, 256), output_format='PNG')
        return 'data:image/png;base64,' + base64.b64encode(thumbnail).decode()

    # ------------------------------------------------------------------------- data

    @api.model
    def _to_utc(self, day, end=False):
        """Convert a local date (YYYY-MM-DD) to a naive UTC datetime, in the user's timezone."""
        tz = pytz.timezone(self.env.user.tz or 'UTC')
        day = fields.Date.from_string(day)
        local = tz.localize(datetime.combine(day + timedelta(days=1 if end else 0), time.min))
        return local.astimezone(pytz.utc).replace(tzinfo=None)

    @api.model
    def get_data(self, shop_id, date_from, date_to, website_id=False):
        """Indicators of a local shop, of an online shop that is not linked, or of all the shops."""
        self._check_access_group()
        if website_id:
            shops = self.env['pos.config']
            websites = self._search_websites([('id', '=', website_id)])
        elif shop_id:
            shops = self.env['pos.config'].browse(shop_id)
            websites = self._search_websites([('local_shop_id', 'in', shops.ids)])
        else:
            shops = self._get_shops()
            websites = self._search_websites([])
        start, end = self._to_utc(date_from), self._to_utc(date_to, end=True)
        scope = {'shops': shops, 'websites': websites, 'start': start, 'end': end}
        sales = self._get_sales(**scope)
        return {
            'currency_id': self.env.company.currency_id.id,
            'purchases': self._get_purchases(**scope),
            'sales': sales,
            'channels': self._get_channels(sales),
            'stock': self._get_stock(**scope),
            'top_products': self._get_products(most=True, **scope),
            'flop_products': self._get_products(most=False, **scope),
            'timeline': self._get_timeline(**scope),
            'by_shop': self._get_by_shop(**scope) if not (shop_id or website_id) else [],
        }

    # --------------------------------------------------------------------- helpers

    @api.model
    def _get_sold_orders(self, shops, start, end):
        return self.env['pos.order'].search([
            ('config_id', 'in', shops.ids),
            ('state', 'in', SOLD_STATES),
            ('date_order', '>=', start),
            ('date_order', '<', end),
        ])

    @api.model
    def _get_online_orders(self, websites, start, end):
        """Confirmed website orders. Read with sudo: the dashboard users may not have sales rights."""
        if not websites:
            return self.env['sale.order']
        return self.env['sale.order'].sudo().search([
            ('website_id', 'in', websites.ids),
            ('state', 'in', ONLINE_STATES),
            ('date_order', '>=', start),
            ('date_order', '<', end),
            ('company_id', 'in', self.env.companies.ids),
        ])

    @api.model
    def _get_own_warehouses(self, websites):
        """Warehouses of the websites that are not linked to a local shop."""
        return websites.filtered(lambda w: not w.local_shop_id).warehouse_id

    @api.model
    def _get_warehouses(self, shops, websites):
        return shops.picking_type_id.warehouse_id | websites.warehouse_id

    # ----------------------------------------------------------------------- sales

    @api.model
    def _get_sales(self, shops, websites, start, end):
        orders = self._get_sold_orders(shops, start, end)
        refunds = orders.filtered('is_refund')
        online = self._get_online_orders(websites, start, end)
        local_amount = sum(orders.mapped('amount_total'))
        # Real turnover: tax excluded, refunds already counted as negative orders
        local_revenue = local_amount - sum(orders.mapped('amount_tax'))
        online_amount = sum(online.mapped('amount_total'))
        online_revenue = sum(online.mapped('amount_untaxed'))
        return {
            'count': len(orders) - len(refunds) + len(online),
            'refund_count': len(refunds),
            'amount': local_amount + online_amount,
            'real_revenue': local_revenue + online_revenue,
            'local': {'count': len(orders) - len(refunds), 'amount': local_amount, 'real_revenue': local_revenue},
            'online': {'count': len(online), 'amount': online_amount, 'real_revenue': online_revenue},
        }

    @api.model
    def _get_channels(self, sales):
        """Online against local: figures of each channel and share of the real turnover."""
        total = sales['real_revenue']
        online_share = round(sales['online']['real_revenue'] * 100 / total, 1) if total else 0.0
        return {
            'local': sales['local'],
            'online': sales['online'],
            'online_share': online_share,
            'local_share': round(100 - online_share, 1) if total else 0.0,
        }

    # -------------------------------------------------------------------- purchases

    @api.model
    def _get_purchase_orders(self, shops, websites, start, end):
        domain = [('state', 'in', PURCHASE_STATES), ('date_approve', '>=', start), ('date_approve', '<', end)]
        own_warehouses = self._get_own_warehouses(websites)
        if own_warehouses:
            # an online shop of its own receives its purchases in its warehouse
            domain += ['|', ('shop_id', 'in', shops.ids), ('picking_type_id.warehouse_id', 'in', own_warehouses.ids)]
        else:
            domain += [('shop_id', 'in', shops.ids)]
        return self.env['purchase.order'].search(domain)

    @api.model
    def _get_purchases(self, shops, websites, start, end):
        orders = self._get_purchase_orders(shops, websites, start, end)
        return {'count': len(orders), 'amount': sum(orders.mapped('amount_total'))}

    # ------------------------------------------------------------------------ stock

    @api.model
    def _get_stock(self, shops, websites, start, end):
        locations = self._get_warehouses(shops, websites).lot_stock_id
        quants = self.env['stock.quant'].search([('location_id', 'child_of', locations.ids)]) if locations else \
            self.env['stock.quant']
        received = self.env['stock.picking'].search_count([
            ('state', '=', 'done'),
            ('date_done', '>=', start),
            ('date_done', '<', end),
            '|', ('shop_id', 'in', shops.ids),
            '&', ('picking_type_code', '=', 'incoming'),
            ('picking_type_id.warehouse_id', 'in', self._get_own_warehouses(websites).ids),
        ])
        return {
            'quantity': sum(quants.mapped('quantity')),
            'value': sum(q.quantity * q.product_id.standard_price for q in quants),
            'received_transfers': received,
        }

    # --------------------------------------------------------------------- products

    @api.model
    def _get_sold_quantities(self, shops, websites, start, end):
        """Quantity sold by product, in the shops (point of sale) and on the websites together."""
        lines = self.env['pos.order.line']._read_group([
            ('order_id.config_id', 'in', shops.ids),
            ('order_id.state', 'in', SOLD_STATES),
            ('order_id.date_order', '>=', start),
            ('order_id.date_order', '<', end),
        ], ['product_id'], ['qty:sum'])
        sold = {product.id: qty for product, qty in lines}
        online_orders = self._get_online_orders(websites, start, end)
        if online_orders:
            online_lines = self.env['sale.order.line'].sudo()._read_group([
                ('order_id', 'in', online_orders.ids),
                ('display_type', '=', False),
            ], ['product_id'], ['product_uom_qty:sum'])
            for product, qty in online_lines:
                sold[product.id] = sold.get(product.id, 0) + qty
        return sold

    @api.model
    def _get_products(self, shops, websites, start, end, most):
        """Most (or least) sold products of the scope over the period, zero sales included."""
        sold = self._get_sold_quantities(shops, websites, start, end)
        if most:
            ranking = sorted(sold.items(), key=lambda item: -item[1])
            ranking = [(pid, qty) for pid, qty in ranking if qty > 0]
        else:
            # Products assigned to the shops but never (or hardly) sold come first
            catalog = self.env['product.product'].search([
                '|', ('product_tmpl_id.shop_ids', 'in', shops.ids),
                ('product_tmpl_id.shop_website_ids', 'in', websites.ids),
            ])
            ranking = sorted(((product.id, sold.get(product.id, 0)) for product in catalog),
                             key=lambda item: item[1])
        ranking = ranking[:TOP_LIMIT]
        names = {p.id: p.display_name for p in self.env['product.product'].sudo().browse([r[0] for r in ranking])}
        return [{'id': pid, 'name': names[pid], 'qty': qty} for pid, qty in ranking]

    # --------------------------------------------------------------------- timeline

    @api.model
    def _get_timeline(self, shops, websites, start, end):
        """Local and online turnover, and purchases, over time: one point per day, or per month on long periods."""
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
        local, online, purchases = (dict.fromkeys(keys, 0.0) for _i in range(3))

        for order in self._get_sold_orders(shops, start, end):
            local[bucket(local_day(order.date_order))] += order.amount_total - order.amount_tax
        for order in self._get_online_orders(websites, start, end):
            online[bucket(local_day(order.date_order))] += order.amount_untaxed
        for order in self._get_purchase_orders(shops, websites, start, end):
            purchases[bucket(local_day(order.date_approve))] += order.amount_total
        return {
            'labels': [key.strftime(label_format) for key in keys],
            'sales': [round(local[key], 2) for key in keys],
            'online': [round(online[key], 2) for key in keys],
            'purchases': [round(purchases[key], 2) for key in keys],
        }

    # ---------------------------------------------------------------------- by shop

    @api.model
    def _get_by_shop(self, shops, websites, start, end):
        """Real turnover of each shop, for the "all shops" card. Online sales count for the linked shop."""
        orders = self._get_sold_orders(shops, start, end)
        result = []
        for shop in shops:
            shop_orders = orders.filtered(lambda o: o.config_id == shop)
            shop_websites = websites.filtered(lambda w: w.local_shop_id == shop)
            online = self._get_online_orders(shop_websites, start, end)
            result.append({
                'id': shop.id,
                'name': shop.name,
                'amount': round(sum(shop_orders.mapped('amount_total')) - sum(shop_orders.mapped('amount_tax'))
                                + sum(online.mapped('amount_untaxed')), 2),
            })
        for website in websites.filtered(lambda w: not w.local_shop_id):
            online = self._get_online_orders(website, start, end)
            result.append({
                'id': False,
                'name': website.name,
                'amount': round(sum(online.mapped('amount_untaxed')), 2),
            })
        return result
