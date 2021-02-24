# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2010-2015
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
    'name' : 'Personal Expense Tracker',
    'version' : '1.0',
    'author' : 'BitConsultores SA',
    'category' : 'Human Resources',
    'description' : """

""",
    'website': 'http://bitconsultores-ec.com',
    'images' : [],
    'depends' : [
                    'bit_hr_payroll_ec'
                ],
    'data': [
        #'hr_expense_view.xml',
        'hr_income_tax.xml',
        'hr_income_inherit.xml',
        'export_xml/export_xml.xml',
        'utilities_rol.xml',
        'negative_taxes.xml',
    ],
    'js': [
       
    ],
    'qweb' : [
       
    ],
    'css':[
        
    ],
    'demo': [
        
    ],
    'test': [
        
    ],
    'installable': True,
    'auto_install': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
