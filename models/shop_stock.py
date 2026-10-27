from odoo import fields, models, tools

# Each warehouse belongs to one shop: the local shop whose point of sale takes its stock there, or the
# website that is a shop of its own. (A website linked to a local shop shares the warehouse of that shop.)
SHOP_WAREHOUSE_SQL = """
    shop_warehouse AS (
        SELECT DISTINCT ON (candidate.warehouse_id)
               candidate.warehouse_id,
               candidate.config_id,
               candidate.website_id,
               candidate.shop_name,
               candidate.company_id
          FROM (
                SELECT spt.warehouse_id AS warehouse_id,
                       cfg.id AS config_id,
                       NULL::integer AS website_id,
                       cfg.name AS shop_name,
                       cfg.company_id AS company_id
                  FROM pos_config cfg
                  JOIN stock_picking_type spt ON spt.id = cfg.picking_type_id
                 WHERE cfg.is_shop AND spt.warehouse_id IS NOT NULL
                UNION ALL
                SELECT site.warehouse_id,
                       NULL::integer,
                       site.id,
                       site.name,
                       site.company_id
                  FROM website site
                 WHERE site.is_shop AND site.local_shop_id IS NULL AND site.warehouse_id IS NOT NULL
               ) candidate
         ORDER BY candidate.warehouse_id, candidate.config_id NULLS LAST
    )
"""


class ShopStock(models.Model):
    """Products and their quantities in the warehouses of the shops (SQL view).

    One line per product, shop and warehouse: the quantities add up over all the shops, and over the
    selected shop only when the list is filtered on a shop.
    """
    _name = 'shop.stock'
    _description = "Shop Stock"
    _auto = False
    _order = 'product_id, shop_name'

    product_id = fields.Many2one('product.product', string="Product", readonly=True)
    categ_id = fields.Many2one('product.category', string="Product Category", readonly=True)
    shop_id = fields.Many2one('pos.config', string="Destination Shop", readonly=True)
    shop_website_id = fields.Many2one('website', string="Online Shop", readonly=True)
    shop_name = fields.Char(string="Shop", readonly=True)
    warehouse_id = fields.Many2one('stock.warehouse', string="Warehouse", readonly=True)
    quantity = fields.Float(string="Quantity", readonly=True, aggregator='sum')
    reserved_quantity = fields.Float(string="Reserved", readonly=True, aggregator='sum')
    available_quantity = fields.Float(string="Available", readonly=True, aggregator='sum')
    min_quantity = fields.Float(string="Minimum Quantity", readonly=True, aggregator=None)
    stock_status = fields.Selection(
        [('ok', "In Stock"), ('low', "Low Stock"), ('out', "Out of Stock")], string="Stock Status", readonly=True)
    image_128 = fields.Binary(related='product_id.image_128', string="Image", readonly=True)
    write_date = fields.Datetime(string="Last Update", readonly=True)  # the image widget of the cards needs it
    company_id = fields.Many2one('res.company', readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                WITH %s
                -- one line per product and warehouse: the id is stable (it identifies the product image, the card...)
                SELECT (stock.product_id::bigint * 100000 + stock.warehouse_id) AS id,
                       stock.product_id,
                       stock.categ_id,
                       stock.shop_id,
                       stock.shop_website_id,
                       stock.shop_name,
                       stock.warehouse_id,
                       stock.company_id,
                       SUM(stock.quantity) AS quantity,
                       SUM(stock.reserved_quantity) AS reserved_quantity,
                       SUM(stock.quantity - stock.reserved_quantity) AS available_quantity,
                       product_row.write_date AS write_date,
                       COALESCE(reorder.min_quantity, 0) AS min_quantity,
                       CASE
                           WHEN SUM(stock.quantity) <= 0 THEN 'out'
                           WHEN COALESCE(reorder.min_quantity, 0) > 0
                                AND SUM(stock.quantity) <= reorder.min_quantity THEN 'low'
                           ELSE 'ok'
                       END AS stock_status
                  FROM (
                        -- what the warehouses of the shops hold
                        SELECT quant.product_id, template.categ_id, shop.config_id AS shop_id,
                               shop.website_id AS shop_website_id, shop.shop_name, shop.warehouse_id,
                               quant.company_id, quant.quantity, quant.reserved_quantity
                          FROM stock_quant quant
                          JOIN stock_location location ON location.id = quant.location_id AND location.usage = 'internal'
                          JOIN shop_warehouse shop ON shop.warehouse_id = location.warehouse_id
                          JOIN product_product product ON product.id = quant.product_id
                          JOIN product_template template ON template.id = product.product_tmpl_id
                        UNION ALL
                        -- the products assigned to a local shop, so that the out-of-stock ones show with 0
                        SELECT product.id, template.categ_id, shop.config_id, shop.website_id, shop.shop_name,
                               shop.warehouse_id, shop.company_id, 0, 0
                          FROM product_template_shop_rel assignment
                          JOIN shop_warehouse shop ON shop.config_id = assignment.pos_config_id
                          JOIN product_template template ON template.id = assignment.product_tmpl_id AND template.is_storable
                          JOIN product_product product ON product.product_tmpl_id = template.id
                        UNION ALL
                        -- the products assigned to an online shop of its own
                        SELECT product.id, template.categ_id, shop.config_id, shop.website_id, shop.shop_name,
                               shop.warehouse_id, shop.company_id, 0, 0
                          FROM product_template_shop_website_rel assignment
                          JOIN shop_warehouse shop ON shop.website_id = assignment.website_id
                          JOIN product_template template ON template.id = assignment.product_tmpl_id AND template.is_storable
                          JOIN product_product product ON product.product_tmpl_id = template.id
                       ) stock
                  JOIN product_product product_row ON product_row.id = stock.product_id
                  LEFT JOIN (
                        -- the minimum quantity of the reordering rules, when there is one: below it the stock is low
                        SELECT rule.product_id, rule.warehouse_id, SUM(rule.product_min_qty) AS min_quantity
                          FROM stock_warehouse_orderpoint rule
                         WHERE rule.active
                         GROUP BY rule.product_id, rule.warehouse_id
                       ) reorder ON reorder.product_id = stock.product_id AND reorder.warehouse_id = stock.warehouse_id
                 GROUP BY stock.product_id, stock.categ_id, stock.shop_id, stock.shop_website_id,
                          stock.shop_name, stock.warehouse_id, stock.company_id, reorder.min_quantity, product_row.write_date
            )
        """ % (self._table, SHOP_WAREHOUSE_SQL))


    def action_open_product(self):
        """Open the product of the card."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'product.product',
            'res_id': self.product_id.id,
            'view_mode': 'form',
            'target': 'current',
        }


class ShopStockMove(models.Model):
    """All the stock movements of the warehouses of the shops (SQL view on the movement lines)."""
    _name = 'shop.stock.move'
    _description = "Shop Stock Movement"
    _auto = False
    _order = 'date desc, id desc'

    date = fields.Datetime(string="Date", readonly=True)
    reference = fields.Char(string="Reference", readonly=True)
    picking_id = fields.Many2one('stock.picking', string="Transfer", readonly=True)
    product_id = fields.Many2one('product.product', string="Product", readonly=True)
    quantity = fields.Float(string="Quantity", readonly=True, aggregator='sum')
    location_id = fields.Many2one('stock.location', string="From", readonly=True)
    location_dest_id = fields.Many2one('stock.location', string="To", readonly=True)
    shop_id = fields.Many2one('pos.config', string="Destination Shop", readonly=True)
    shop_website_id = fields.Many2one('website', string="Online Shop", readonly=True)
    shop_name = fields.Char(string="Shop", readonly=True)
    direction = fields.Selection(
        [('in', "Entry"), ('out', "Exit"), ('internal', "Internal")], string="Direction", readonly=True)
    state = fields.Selection(
        [('draft', "Draft"), ('waiting', "Waiting"), ('assigned', "Ready"), ('done', "Done"), ('cancel', "Cancelled")],
        string="Status", readonly=True)
    company_id = fields.Many2one('res.company', readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                WITH %s
                SELECT line.id AS id,
                       line.date AS date,
                       move.reference AS reference,
                       line.picking_id AS picking_id,
                       line.product_id AS product_id,
                       line.quantity_product_uom AS quantity,
                       line.location_id AS location_id,
                       line.location_dest_id AS location_dest_id,
                       shop.config_id AS shop_id,
                       shop.website_id AS shop_website_id,
                       shop.shop_name AS shop_name,
                       CASE
                           WHEN destination.warehouse_id IS NOT NULL AND source.warehouse_id IS NOT NULL THEN 'internal'
                           WHEN destination.warehouse_id IS NOT NULL THEN 'in'
                           ELSE 'out'
                       END AS direction,
                       CASE line.state
                           WHEN 'draft' THEN 'draft'
                           WHEN 'assigned' THEN 'assigned'
                           WHEN 'done' THEN 'done'
                           WHEN 'cancel' THEN 'cancel'
                           ELSE 'waiting'
                       END AS state,
                       line.company_id AS company_id
                  FROM stock_move_line line
                  JOIN stock_location location_from ON location_from.id = line.location_id
                  JOIN stock_location location_to ON location_to.id = line.location_dest_id
                  LEFT JOIN stock_move move ON move.id = line.move_id
                  LEFT JOIN shop_warehouse source ON source.warehouse_id = location_from.warehouse_id
                  LEFT JOIN shop_warehouse destination ON destination.warehouse_id = location_to.warehouse_id
                  JOIN LATERAL (
                        -- the shop of the movement: the destination shop, or the source shop for an exit
                        SELECT CASE WHEN destination.warehouse_id IS NOT NULL THEN destination.config_id
                                    ELSE source.config_id END AS config_id,
                               CASE WHEN destination.warehouse_id IS NOT NULL THEN destination.website_id
                                    ELSE source.website_id END AS website_id,
                               COALESCE(destination.shop_name, source.shop_name) AS shop_name
                       ) shop ON (destination.warehouse_id IS NOT NULL OR source.warehouse_id IS NOT NULL)
            )
        """ % (self._table, SHOP_WAREHOUSE_SQL))

    def action_open_transfer(self):
        """Open the transfer of the movement, or the movement itself when it belongs to no transfer."""
        self.ensure_one()
        if self.picking_id:
            res_model, res_id = 'stock.picking', self.picking_id.id
        else:
            res_model, res_id = 'stock.move.line', self.id
        return {
            'type': 'ir.actions.act_window',
            'res_model': res_model,
            'res_id': res_id,
            'view_mode': 'form',
            'target': 'current',
        }
