from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    """Give their shop to the existing online orders and to the existing deliveries (shop menus)."""
    env = api.Environment(cr, SUPERUSER_ID, {})
    orders = env['sale.order'].search([('website_id.is_shop', '=', True)])
    orders._compute_shop()
    pickings = env['stock.picking'].search(['|', ('sale_id', 'in', orders.ids), ('pos_order_id', '!=', False)])
    pickings._compute_shop()
