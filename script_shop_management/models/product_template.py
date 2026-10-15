# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.fields import Domain


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    shop_ids = fields.Many2many(
        'pos.config',
        'product_template_shop_rel',
        'product_tmpl_id',
        'pos_config_id',
        string="Available in Shops",
        domain="[('is_shop', '=', True)]",
        help="Shops where this product is sold.",
    )

    @api.model
    def _load_pos_data_domain(self, data, config):
        """A shop only loads the products assigned to it."""
        domain = super()._load_pos_data_domain(data, config)
        if config.is_shop:
            domain = [*domain, ('shop_ids', 'in', config.ids)]
        return domain

    @api.model
    def load_product_from_pos(self, config_id, domain, offset=0, limit=0):
        """Same restriction for the products searched from the PoS screen.

        The restriction applies whatever the "Restrict Categories" setting is: the
        products of the allowed categories are limited to the shop's products.
        Internal loads by id (archived products of existing orders) are left untouched.
        """
        config = self.env['pos.config'].browse(config_id)
        if config.is_shop and not self.env.context.get('load_archived'):
            domain = Domain(domain) & Domain('shop_ids', 'in', config.ids)
        return super().load_product_from_pos(config_id, domain, offset, limit)

    def _unrelevant_records(self, config):
        """Make the PoS drop, from its local cache, the products that are not assigned to the shop."""
        unrelevant_ids = set(super()._unrelevant_records(config))
        if config.is_shop:
            special = config._get_special_products().product_tmpl_id | config.tip_product_id.product_tmpl_id
            for template in (self - special).sudo():
                if config not in template.shop_ids:
                    unrelevant_ids.add(template.id)
        return list(unrelevant_ids)
