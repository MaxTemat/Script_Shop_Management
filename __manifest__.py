# -*- coding: utf-8 -*-
{
    'name': 'Script Shop Management',
    'version': '19.0.2.1.0',
    'summary': "Manage your local shops from one place: purchases, sales, stock and a modern dashboard",
    'description': """
Script Shop Management
======================
Manage your physical shops (Point of Sale configurations) from a single Odoo application.

* Flag any Point of Sale as a shop and give it an image.
* Choose in which shops each product is available: a shop's cash register only loads its own products.
* Set a destination shop on purchase orders and stock transfers.
* Dashboard: one card per shop (and one for all shops) with a period selector, purchases, sales,
  real turnover, stock, turnover/purchases curves and best / least selling products.
* Online shops: flag a website as a shop and link it, or not, to a local shop (image, destination
  shop and stock are shared when linked).
* Dedicated Purchases, Orders and Stock lists with quick search by shop and product.
* User / Manager security groups. English and French translations.
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
