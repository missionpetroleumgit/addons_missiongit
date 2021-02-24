# -*- coding:utf-8 -*-
#
#
#    Copyright (C) 2019 Daniel Aldaz <daldaz@mission-petroleum.com>.
#    All Rights Reserved.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.

{
    'name': 'Ajustes de requisiciones',
    'version': '1.0',
    'category': '',
    'author': "Daniel Aldaz, MissionPetroleum Developer",
    'description': """
Controlo el acceso de creacion de requisiciones, tanto de bienes como de servicios, separo en requisiciones
de bienes y servicios, tanto en los menus como en lo seleccionable.
======================
    """,
    'depends': [
        'purchase', 'purchase_tiw', 'stock'
    ],
    'data': [
        'views/purchase_adjustment_view.xml',
        'security/groups_view.xml',
        'views/stock_view.xml',
        'report/report_print_picking_out.xml',
        'report/report_stock_report.xml'
    ],
    'test': [
    ],
    'installable': True,
}