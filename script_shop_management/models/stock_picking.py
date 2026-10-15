# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    shop_id = fields.Many2one(
        'pos.config',
        string="Destination Shop",
        domain="[('is_shop', '=', True), ('company_id', '=', company_id)]",
        index=True,
        tracking=True,
        help="Shop this transfer is sent to.",
    )

    @api.constrains('shop_id', 'company_id')
    def _check_shop_company(self):
        for record in self:
            if record.shop_id and record.shop_id.company_id != record.company_id:
                raise ValidationError(_(
                    "The shop %(shop)s does not belong to the company %(company)s.",
                    shop=record.shop_id.display_name,
                    company=record.company_id.display_name,
                ))
