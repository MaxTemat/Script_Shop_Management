# -*- coding: utf-8 -*-
{
    'name': 'Script Shop Management',
    'version': '19.0.1.0.0',
    'summary': "Gestion des boutiques locales : achats, ventes, stock et tableau de bord",
    'description': """
Script Shop Management
======================
Pilotage des boutiques (points de vente) depuis une seule application :
- Dashboard par boutique (achats, ventes, stock, CA réel, meilleures ventes)
- Achats, commandes de caisse et transferts de stock par boutique
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
    ],
    'assets': {},
    'application': True,
    'installable': True,
}
