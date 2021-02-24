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
    'name': 'Reportes Compras Ventas',
    'version': '1.0',
    'category': 'Generic Modules/Sale',
    'author': "Daniel Aldaz, MissionPetroleum Developer",
    'description': """
Reporteria
======================
    """,
    'depends': [
        'sale', 'purchase'
    ],
    'data': [
        'views/sale_order_report_view.xml',
        'views/purchase_order_report_view.xml',
        'views/mp_account_invoice_view.xml',
        'views/mp_account_invoice_report_view.xml',
        'views/mp_purchase_order_view.xml',
        'views/mp_invoice_supplier_purchase_report_view.xml',
        'views/sale_invoice_report_view.xml',
        'views/sale_order_states_report_view.xml',
        'views/sale_margin_report_view.xml'
    ],
    'test': [
    ],
    'installable': True,
}
