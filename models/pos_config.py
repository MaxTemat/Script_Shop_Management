# -*- coding: utf-8 -*-
from odoo import fields, models


class PosConfig(models.Model):
    _inherit = 'pos.config'

    is_shop = fields.Boolean(
        string="Est une boutique",
        help="Cochez cette case pour que ce point de vente soit géré comme une boutique "
             "dans Script Shop Management.",
    )
    shop_image = fields.Image(
        string="Image de la boutique",
        max_width=512,
        max_height=512,
    )
