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
    'name': 'Invoice Control',
    'version': '1.0',
    'category': 'Generic Modules/Sale',
    'author': "Daniel Aldaz, MissionPetroleum Developer",
    'description': """
Seguimiento de Facturas por medio de la venta
======================
    """,
    'depends': [
        'sale', 'bit_payment',
    ],
    'data': [
        'views/invoice_control_view.xml',
        'views/account_invoice_view.xml',
        'views/wizard_invoice_control_view.xml',
        'views/wizard_invoice_control_date_view.xml',
        'views/partner_view.xml',
    ],
    'test': [
    ],
    'installable': True,
}
