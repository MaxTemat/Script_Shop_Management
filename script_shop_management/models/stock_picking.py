# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    shop_id = fields.Many2one(
        'pos.config',
        string="Destination Shop",
        compute='_compute_shop',
        store=True,
        readonly=False,
        domain="[('is_shop', '=', True), ('company_id', '=', company_id)]",
        index=True,
        tracking=True,
        help="Shop this transfer is for: the destination of a receipt, the shop of a delivery.",
    )
    shop_website_id = fields.Many2one(
        'website',
        string="Online Shop",
        compute='_compute_shop',
        store=True,
        readonly=False,
        domain="[('is_shop', '=', True), ('local_shop_id', '=', False), ('company_id', '=', company_id)]",
        index=True,
        tracking=True,
        help="Online shop of its own this transfer is for.",
    )

    @api.depends('sale_id.shop_id', 'sale_id.shop_website_id', 'pos_order_id.config_id')
    def _compute_shop(self):
        """The deliveries of the local shops and of the online shops carry the shop of their order."""
        for picking in self:
            pos_shop = picking.pos_order_id.config_id
            if pos_shop.is_shop:
                picking.shop_id = pos_shop
            elif picking.sale_id.shop_id or picking.sale_id.shop_website_id:
                picking.shop_id = picking.sale_id.shop_id
                picking.shop_website_id = picking.sale_id.shop_website_id

    @api.constrains('shop_id', 'company_id')
    def _check_shop_company(self):
        for record in self:
            if record.shop_id and record.shop_id.company_id != record.company_id:
                raise ValidationError(_(
                    "The shop %(shop)s does not belong to the company %(company)s.",
                    shop=record.shop_id.display_name,
                    company=record.company_id.display_name,
                ))

    @api.constrains('shop_website_id', 'company_id')
    def _check_shop_website_company(self):
        for record in self:
            if record.shop_website_id and record.shop_website_id.company_id != record.company_id:
                raise ValidationError(_(
                    "The shop %(shop)s does not belong to the company %(company)s.",
                    shop=record.shop_website_id.display_name,
                    company=record.company_id.display_name,
                ))
