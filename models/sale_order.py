from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    shop_id = fields.Many2one(
        'pos.config',
        string="Destination Shop",
        compute='_compute_shop',
        store=True,
        readonly=False,
        index=True,
        domain="[('is_shop', '=', True), ('company_id', '=', company_id)]",
        help="Shop of the order: for an online order, the local shop linked to the website.",
    )
    shop_website_id = fields.Many2one(
        'website',
        string="Online Shop",
        compute='_compute_shop',
        store=True,
        readonly=False,
        index=True,
        domain="[('is_shop', '=', True), ('local_shop_id', '=', False), ('company_id', '=', company_id)]",
        help="Shop of the order when it comes from a website that is a shop of its own.",
    )

    @api.depends('website_id.is_shop', 'website_id.local_shop_id')
    def _compute_shop(self):
        """An online order is destined to the shop of its website.

        A website linked to a local shop gives that local shop; a website that is a shop of its own
        is the shop itself.
        """
        for order in self:
            website = order.website_id
            if website.is_shop:
                order.shop_id = website.local_shop_id
                order.shop_website_id = website if not website.local_shop_id else False

    @api.depends('website_id.warehouse_id')
    def _compute_warehouse_id(self):
        """Online orders take the warehouse of their website (shared stock of a linked shop).

        The open orders (carts and quotations) follow the warehouse of the website when it
        changes. A confirmed order keeps the warehouse its deliveries were created from.
        """
        open_orders = self.filtered(lambda order: not order.ids or order.state in ('draft', 'sent'))
        super(SaleOrder, open_orders)._compute_warehouse_id()
