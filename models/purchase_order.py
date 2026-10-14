# -*- coding: utf-8 -*-
from odoo import fields, models


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    shop_id = fields.Many2one(
        'pos.config',
        string="Destination Shop",
        domain="[('is_shop', '=', True)]",
        index=True,
        tracking=True,
        help="Shop that will receive the products of this purchase.",
    )
