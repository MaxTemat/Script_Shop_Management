# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class PosConfig(models.Model):
    _inherit = 'pos.config'

    is_shop = fields.Boolean(
        string="Is a Shop",
        help="Check this box to manage this point of sale as a shop "
             "in Script Shop Management.",
    )
    shop_image = fields.Image(
        string="Shop Image",
        max_width=512,
        max_height=512,
    )

    @api.constrains('is_shop', 'picking_type_id')
    def _check_shop_warehouse(self):
        """A warehouse is the stock of one shop only: the stock of a shop is shown once, for that shop."""
        for shop in self.filtered('is_shop'):
            warehouse = shop.picking_type_id.warehouse_id
            if not warehouse:
                continue
            owner = self.sudo().search([
                ('is_shop', '=', True),
                ('id', '!=', shop.id),
                ('picking_type_id.warehouse_id', '=', warehouse.id),
            ], limit=1) or self.env['website'].sudo().search([
                ('is_shop', '=', True),
                ('local_shop_id', '=', False),
                ('warehouse_id', '=', warehouse.id),
            ], limit=1)
            if owner:
                raise ValidationError(_(
                    "The warehouse %(warehouse)s is already the stock of the shop %(shop)s. "
                    "A warehouse can only belong to one shop: choose another operation type.",
                    warehouse=warehouse.display_name,
                    shop=owner.display_name,
                ))
