# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    'name': 'Caja Chica',
    'version': '1.1',
    'author': 'Cristobal Sanchez',
    'summary': ' Manejo Caja Chica, Creacion de facturas',
    'description': """
Modulo Manejo Caja chica / Registro de gastos
======================
Este módulo ayuda al manejo de gastos de caja chica y genera las facturas

Key Features
------------
* Caja Chica (periodica y automatica)
* Creacion de facturas caja chica

Dashboard / Reports for Warehouse Management includes:
------------------------------------------------------
* Caja Chica at given date (support dates in the past)
    """,
    'website': 'https://www.odoo.com/page/warehouse',
    'images': [],
    'depends': ['account'], # Quitado la dependencia de point of sale  para mission petroleum
    'category': 'Hidden',
    'sequence': 16,
    'demo': [
        'caja_chica_demo.xml'
    ],
    'data': [
        #'security/stock_account_security.xml',
        #'security/ir.model.access.csv',
        'views/account_caja_chica_menu.xml',
        'views/view_account_invoice_cchica.xml',
        'views/product_view.xml',
    ],
    'test': [

    ],
    'installable': True,
    'auto_install': False,
}
