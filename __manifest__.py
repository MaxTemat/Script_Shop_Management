# -*- coding: utf-8 -*-
{
    'name': 'Script Shop Management',
    'version': '19.0.1.0.0',
    'summary': "Local shop management: purchases, sales, stock and dashboard",
    'description': """
Script Shop Management
======================
Manage your shops (points of sale) from a single application:
- Dashboard per shop (purchases, sales, stock, real turnover, best sellers)
- Purchases, point of sale orders and stock transfers per shop
""",
    'author': 'Script Consulting',
    'category': 'Sales/Point of Sale',
    'license': 'LGPL-3',
    'depends': ['point_of_sale', 'purchase', 'stock'],
    'data': [
        'views/pos_config_views.xml',
        'views/product_template_views.xml',
        'views/purchase_order_views.xml',
        'views/stock_picking_views.xml',
        'views/purchase_order_list_views.xml',
        'views/pos_order_list_views.xml',
        'views/stock_picking_list_views.xml',
        'views/shop_dashboard_views.xml',
        'views/shop_menus.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'script_shop_management/static/src/dashboard/shop_dashboard.js',
            'script_shop_management/static/src/dashboard/shop_dashboard.xml',
            'script_shop_management/static/src/dashboard/shop_dashboard.scss',
        ],
    },
    'application': True,
    'installable': True,
}
