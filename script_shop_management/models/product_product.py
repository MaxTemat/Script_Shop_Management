# -*- coding: utf-8 -*-
from odoo import models


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def _unrelevant_records(self, config):
        """Same cache cleaning as the product templates, for the product variants."""
        unrelevant_ids = set(super()._unrelevant_records(config))
        if config.is_shop:
            special = config._get_special_products().product_tmpl_id | config.tip_product_id.product_tmpl_id
            for product in self.sudo():
                template = product.product_tmpl_id
                if template not in special and config not in template.shop_ids:
                    unrelevant_ids.add(product.id)
        return list(unrelevant_ids)
