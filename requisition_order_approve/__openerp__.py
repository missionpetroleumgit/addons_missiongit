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
    'name': 'Aprobacion dinamica de requisiciones',
    'version': '1.0',
    'category': '',
    'author': "Daniel Aldaz, MissionPetroleum Developer",
    'description': """
Aprobacion de las requisiciones mediante la opcion de elegir un tipo de material, se coloca automaticamente el aprobador.
======================
    """,
    'depends': [
        'purchase', 'purchase_tiw',
    ],
    'data': [
        'views/requisition_order_view.xml',
        'security/groups.xml',
    ],
    'test': [
    ],
    'installable': True,
}
