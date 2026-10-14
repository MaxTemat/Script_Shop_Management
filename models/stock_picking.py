# -*- coding: utf-8 -*-
from odoo import fields, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    shop_id = fields.Many2one(
        'pos.config',
        string="Destination Shop",
        domain="[('is_shop', '=', True)]",
        index=True,
        tracking=True,
        help="Shop this transfer is sent to.",
    )
