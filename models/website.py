from odoo import fields, models


class Website(models.Model):
    _inherit = 'website'

    is_shop = fields.Boolean(
        string="Is a Shop",
        help="Tick this box to manage this website as an online shop in Script Shop Management.",
    )
    shop_image = fields.Image(
        string="Shop Image",
        max_width=512,
        max_height=512,
        help="Image of the online shop. Used when the website is not linked to a local shop.",
    )
    local_shop_id = fields.Many2one(
        'pos.config',
        string="Linked Local Shop",
        domain="[('is_shop', '=', True), ('company_id', '=', company_id)]",
        index=True,
        help="Local shop whose image, destination shop and stock are shared with this website. "
             "Leave empty to manage the website as a shop of its own.",
    )
