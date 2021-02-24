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
    'name': 'Reportes Compras',
    'version': '1.0',
    'category': '',
    'author': "Daniel Aldaz, MissionPetroleum Developer",
    'description': """
Reportes dinamico de compras F4, generacion de reporte para el area de compras
======================
    """,
    'depends': [
        'purchase', 'purchase_tiw',
    ],
    'data': [
        'views/purchase_report_view.xml',
        # Se comenta esta vista para realizar bien la herencia a modulos base
        # 'views/res_partner_view.xml',
    ],
    'test': [
    ],
    'installable': True,
}
