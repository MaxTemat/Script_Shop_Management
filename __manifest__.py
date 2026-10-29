# -*- coding: utf-8 -*-
{
    'name': 'Script Shop Management',
    'version': '19.0.2.1.0',
    'summary': "Run your local and online shops from one place: purchases, orders, shared stock and a modern dashboard",
    'description': """
Script Shop Management
======================
Manage your local shops (Point of Sale) and online shops (websites) from a single Odoo application.

* Flag any Point of Sale or website as a shop and give it an image.
* Link an online shop to a local shop (image, destination shop and stock are shared) or run it on its
  own warehouse, created automatically. One warehouse can only belong to one shop.
* Choose in which shops each product is available: cash registers and websites only show their products.
* Destination shop on purchase orders, online orders and stock transfers.
* Dashboard: one card per shop (and one for all shops) with Local / Online badges, period selector,
  purchases, sales, real turnover, online sales, stock, curves, best / least selling products and
  online against local comparison. Indicators open the matching filtered lists.
* Orders menu gathering point of sale and website orders.
* Stock menu: dashboard of products as cards (status in stock / low / out of stock) and Transfers history.
* User / Manager security groups, multi-company rules. English and French translations.

Not compatible with Odoo Online (contains Python code): use Odoo.sh or on-premise.
""",
    'author': 'Script Consulting',
    'maintainer': 'Script Consulting',
    'website': 'https://github.com/MaxTemat/Script_Shop_Management',
    'category': 'Sales/Point of Sale',
    'license': 'LGPL-3',
    'depends': ['point_of_sale', 'purchase', 'stock', 'website_sale', 'website_sale_stock'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/pos_config_views.xml',
        'views/product_template_views.xml',
        'views/purchase_order_views.xml',
        'views/stock_picking_views.xml',
        'views/purchase_order_list_views.xml',
        'views/sale_order_views.xml',
        'views/shop_order_views.xml',
        'views/shop_stock_views.xml',
        'views/shop_stock_move_views.xml',
        'views/website_views.xml',
        'views/shop_dashboard_views.xml',
        'views/shop_menus.xml',
    ],
    'images': [
        'static/description/screenshot_2_dashboard.jpg',
        'static/description/screenshot_3_charts.jpg',
        'static/description/screenshot_1_shops.jpg',
        'static/description/screenshot_4_purchases.jpg',
        'static/description/screenshot_5_online_vs_local.jpg',
        'static/description/screenshot_6_stock.jpg',
        'static/description/screenshot_7_orders.jpg',
    ],
    'assets': {
        'web.assets_backend': [
            'script_shop_management/static/src/dashboard/shop_dashboard.js',
            'script_shop_management/static/src/dashboard/shop_dashboard.xml',
            'script_shop_management/static/src/dashboard/shop_dashboard.scss',
            'script_shop_management/static/src/stock/shop_stock_kanban.scss',
        ],
    },
    'application': True,
    'installable': True,
}
