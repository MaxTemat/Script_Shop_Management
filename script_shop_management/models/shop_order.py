from odoo import api, fields, models, tools


class ShopOrder(models.Model):
    """Orders of the shops, on one list: the point of sale orders and the website orders (SQL view)."""
    _name = 'shop.order'
    _description = "Shop Order"
    _auto = False
    _order = 'date_order desc, id desc'

    name = fields.Char(string="Reference", readonly=True)
    date_order = fields.Datetime(string="Order Date", readonly=True)
    channel = fields.Selection(
        [('local', "Local"), ('online', "Online")], string="Channel", readonly=True)
    shop_id = fields.Many2one('pos.config', string="Destination Shop", readonly=True)
    shop_website_id = fields.Many2one('website', string="Online Shop", readonly=True)
    partner_id = fields.Many2one('res.partner', string="Customer", readonly=True)
    currency_id = fields.Many2one('res.currency', readonly=True)
    amount_total = fields.Monetary(string="Total", currency_field='currency_id', readonly=True)
    amount_untaxed = fields.Monetary(string="Untaxed Amount", currency_field='currency_id', readonly=True)
    state = fields.Selection(
        [('confirmed', "Validated"), ('done', "Completed"), ('cancel', "Cancelled")],
        string="Status", readonly=True)
    company_id = fields.Many2one('res.company', readonly=True)
    res_model = fields.Char(readonly=True)
    res_id = fields.Integer(readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                SELECT po.id * 2 AS id,
                       po.name AS name,
                       po.date_order AS date_order,
                       'local' AS channel,
                       po.config_id AS shop_id,
                       NULL::integer AS shop_website_id,
                       po.partner_id AS partner_id,
                       company.currency_id AS currency_id,
                       po.amount_total AS amount_total,
                       po.amount_total - po.amount_tax AS amount_untaxed,
                       CASE po.state WHEN 'cancel' THEN 'cancel' WHEN 'paid' THEN 'confirmed' ELSE 'done' END AS state,
                       po.company_id AS company_id,
                       'pos.order' AS res_model,
                       po.id AS res_id
                  FROM pos_order po
                  JOIN pos_config config ON config.id = po.config_id AND config.is_shop
                  JOIN res_company company ON company.id = po.company_id
                 WHERE po.state != 'draft'
                UNION ALL
                SELECT so.id * 2 + 1,
                       so.name,
                       so.date_order,
                       'online',
                       so.shop_id,
                       so.shop_website_id,
                       so.partner_id,
                       so.currency_id,
                       so.amount_total,
                       so.amount_untaxed,
                       CASE so.state WHEN 'cancel' THEN 'cancel' WHEN 'sale' THEN 'confirmed' ELSE 'done' END,
                       so.company_id,
                       'sale.order',
                       so.id
                  FROM sale_order so
                 WHERE so.website_id IS NOT NULL
                   AND (so.shop_id IS NOT NULL OR so.shop_website_id IS NOT NULL)
                   AND so.state NOT IN ('draft', 'sent')
            )
        """ % self._table)

    def action_open_order(self):
        """Open the point of sale order or the sales order behind the line."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': self.res_model,
            'res_id': self.res_id,
            'view_mode': 'form',
            'target': 'current',
        }
