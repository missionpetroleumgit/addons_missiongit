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
    'name': 'Account Conciliation',
    'version': '1.1',
    'author': 'Cristobal Sanchez',
    'summary': ' Conciliacion de tarjetas, por diario, calculos propios y creación de asiento ',
    'description': """
Conciliation Accounting module
======================
Este módulo concilia las tarjetas de credito por diario y calcula comisiones y asiento 

Key Features
------------
* Conciliation Valuation (periodical or automatic)
* Invoice from Picking

Dashboard / Reports for Warehouse Management includes:
------------------------------------------------------
* Conciliation Value at given date (support dates in the past)
    """,
    'website': 'https://www.odoo.com/page/warehouse',
    'images': [],
    'depends': ['account','point_of_sale'],
    'category': 'Hidden',
    'sequence': 16,
    'demo': [
        'conciliation_account_demo.xml'
    ],
    'data': [
        #'security/stock_account_security.xml',
        #'security/ir.model.access.csv',
        'views/account_conciliation_menu.xml',
        'views/view_bank_statement_tree.xml',
        'views/view_account_journal.xml',
        'views/view_pos_config.xml',
        'wizard/account_conciliation_tarjet_view.xml',
        #'wizard/account_conciliation_group_view.xml',
    ],
    'test': [

    ],
    'installable': True,
    'auto_install': False,
}
