# -*- coding: utf-8 -*-
from odoo import fields, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    shop_id = fields.Many2one(
        'pos.config',
        string="Boutique de destination",
        domain="[('is_shop', '=', True)]",
        index=True,
        tracking=True,
        help="Boutique vers laquelle ce transfert est effectué.",
    )
