# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
#    Copyright (C) 2010-2012 OpenERP s.a. (<http://openerp.com>).
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
    'name': 'Purchase OPEN SOURCE SOLUTION',
    'version': '1.0',
    'author': 'Joaquin Gutierrez',
    'category': 'Purchase Management',
    'website': 'http://www.gutierrezweb.es',
    'summary': 'Purchase Order Cost by Expense',
    'description': """
This module manage your Purchase Expenses
===========================================================

The functionality of this module is to provide the system of management of 
shopping expenses such as freight, transportation, customs, insurance, etc.

Main features:
-------------------------------------------------------------------------------
* Management expense types and type sharing expense calculation.
* Types of distribution based on weight, volume, product price, etc.
* Type marked as default are automatically added to purchase order cost.
* Management orders shopping expenses associated with one or more entry slips.
* Upgrade cost price of products based on the costs.
* Currently only one type of upgrade cost is available, direct upgrade.

Next version:
-------------------------------------------------------------------------------
* Ability to add expenses in multi currency.
* Ability to associate the type of expense, purchase orders and / or purchase invoice related.
* Purchase Order Cost report.

Support and blueprint:
-------------------------------------------------------------------------------
* Freeback is wellcome.
* Suggestions and improvements in launchpad.

Icon:
-------------------------------------------------------------------------------
Thank a Visual Pharm http://icons8.com 

""",

    'depends': ['purchase',
                ],
    'data': ['purchase_expense_distribution_view.xml',
             'security/ir.model.access.csv',
             'purchase_expense_distribution_sequence.xml',
             'wizard/purchase_expense_distribution_wizard_view.xml',
             'cost_type_data.xml', 'purchase_order.xml', 'security/groups.xml'

             ],
    'auto_install': False,
    'application': False,
    'installable': True,
    'images': ['images/purchase_order_expense_main.png', 'images/purchase_order_expense_line.png','images/expenses_types.png','images/order_log_details.png'],




}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
