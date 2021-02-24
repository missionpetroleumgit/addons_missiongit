# -*- coding:utf-8 -*-
#    Copyright (C) 2019 Daniel Aldaz <daldaz@mission-petroleum.com>.
#    All Rights Reserved.

{
    'name': 'Control cotizaciones',
    'version': '1.0',
    'category': 'Generic Modules/Sale',
    'author': "Daniel Aldaz, MissionPetroleum Developer",
    'description': """Control cotizaciones de venta """,
    'depends': [
        'sale',
    ],
    'data': [
        'views/mp_sale_order_view.xml',
        'security/groups.xml',
    ],
    'test': [
    ],
    'installable': True,
}
