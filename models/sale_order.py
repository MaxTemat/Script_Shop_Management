from odoo import api, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.depends('website_id.warehouse_id')
    def _compute_warehouse_id(self):
        """Online orders take the warehouse of their website (shared stock of a linked shop).

        The open orders (carts and quotations) follow the warehouse of the website when it
        changes. A confirmed order keeps the warehouse its deliveries were created from.
        """
        open_orders = self.filtered(lambda order: not order.ids or order.state in ('draft', 'sent'))
        super(SaleOrder, open_orders)._compute_warehouse_id()
