# -*- coding: utf-8 -*-
from odoo import fields, models


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
