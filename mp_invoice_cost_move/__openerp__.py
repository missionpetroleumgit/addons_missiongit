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
    'name': 'Product cost move create',
    'version': '1.0',
    'category': 'Generic Modules/Account',
    'author': "Daniel Aldaz, MissionPetroleum Developer",
    'description': """======================
Creación de asientos de costo de los productos/consumibles en facturas de ventas.
======================
    """,
    'depends': [
        'account_accountant', 'bit_account'
    ],
    'data': [
        'views/mp_invoice_product_cost_view.xml'
    ],
    'test': [
    ],
    'installable': True,
}
