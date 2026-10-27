from odoo import api, fields, models


class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'

    is_shop_warehouse = fields.Boolean(
        string="Is the Stock of a Shop",
        compute='_compute_is_shop_warehouse',
        search='_search_is_shop_warehouse',
    )

    @api.model
    def _get_shop_warehouses(self):
        """Warehouses that are the stock of a local shop or of an online shop of its own."""
        shops = self.env['pos.config'].sudo().search([('is_shop', '=', True)])
        websites = self.env['website'].sudo().search([('is_shop', '=', True), ('local_shop_id', '=', False)])
        return shops.picking_type_id.warehouse_id | websites.warehouse_id

    def _compute_is_shop_warehouse(self):
        shop_warehouses = self._get_shop_warehouses()
        for warehouse in self:
            warehouse.is_shop_warehouse = warehouse in shop_warehouses

    @api.model
    def _search_is_shop_warehouse(self, operator, value):
        # the ORM may give '=' as 'in' [True]: handle =, !=, in and not in
        if operator not in ('=', '!=', 'in', 'not in'):
            raise NotImplementedError(operator)
        values = value if isinstance(value, (list, tuple, set)) else [value]
        positive = (operator in ('=', 'in')) == any(values)
        return [('id', 'in' if positive else 'not in', self._get_shop_warehouses().ids)]
