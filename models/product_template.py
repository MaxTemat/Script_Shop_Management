# -*- coding: utf-8 -*-
from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    shop_ids = fields.Many2many(
        'pos.config',
        'product_template_shop_rel',
        'product_tmpl_id',
        'pos_config_id',
        string="Disponible dans les boutiques",
        domain="[('is_shop', '=', True)]",
        help="Boutiques dans lesquelles ce produit est vendu.",
    )
