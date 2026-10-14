# -*- coding: utf-8 -*-
from odoo import fields, models


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    shop_id = fields.Many2one(
        'pos.config',
        string="Boutique de destination",
        domain="[('is_shop', '=', True)]",
        index=True,
        tracking=True,
        help="Boutique qui recevra les produits de cet achat.",
    )
