# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution - Ecuador
#    Copyright (C) 2014 BitConsultores (<http://http://bitconsultores-ec.com>).
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
    'name' : 'Invoicing of Ecuador Terceros',
    'version' : '1.1',
    'author' : 'Crisantino Dos Santos',
    'category' : 'Accounting & Finance',
    'description' : """ Modulo que permite agrupar las responsabilidades de terceros en un periodo

""",
    'website': 'http://bitconsultores-ec.com',
    'images' : [],
    'depends' : [
                    'account_cancel',
                    'bit_account_distribution',
                    'account_accountant',
                    'bit_hr_payroll_ec',
                ],
    'data': [
        'security/ir.model.access.csv',
        'account_invoice_view.xml',
        'res_partner.xml',
        'report_third_wizard.xml'
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
