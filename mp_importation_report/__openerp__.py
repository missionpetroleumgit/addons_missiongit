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
    'name': 'Reportes Importaciones',
    'version': '1.0',
    'category': 'Generic Modules/Purchase',
    'author': "Daniel Aldaz, MissionPetroleum Developer",
    'description': """
Reporteria Importaciones
======================
    """,
    'depends': [
        'purchase',
    ],
    'data': [
        'views/mp_importation_report_view.xml',
        'views/mp_importation_warehouse_view.xml',
        'views/mp_importation_operations_report_view.xml',
    ],
    'test': [
    ],
    'installable': True,
}
