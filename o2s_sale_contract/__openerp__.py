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
    'name' : 'Contract',
    'version' : '1.1',
    'author' : 'BitConsultores SA',
    'category': 'Hidden',
    'description' : """

""",
    'website': 'http://bitconsultores-ec.com',
    'images' : [],
    'depends' : [
                    'analytic', 'sale', 'stock', 'hr', 'o2s_account_tiw'
                ],
    'data': [
        'report/report_definition.xml',
        'report/report_service_ticket.xml',
        'report/service_ticket_non_grouping_report.xml',
        'report/work_report.xml',
        'views/analytic.xml',
        'views/pricelist.xml',
        'views/services_view.xml',
        'views/sale_view.xml',
        'views/account_invoice.xml',
        'data/service_ticket_data.xml',
        'views/product_view.xml',
        'views/stock_view.xml',
        'security/groups.xml',
        'report/purchase_order_report.xml'
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
