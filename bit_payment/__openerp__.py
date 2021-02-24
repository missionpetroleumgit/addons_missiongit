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
    'name' : 'Payment Management',
    'version' : '1.1',
    'author' : 'BitConsultores SA',
    'category' : 'Accounting & Finance',
    'description' : """

""",
    'website': 'http://bitconsultores-ec.com',
    'images' : [],
    'depends' : ['account_payment', 'bit_account'], #, 'hr_payroll'
    'data': 
    [
        'account_checkbook_workflow.xml',
        'account_checkbook_view.xml',
#         'account_invoice_workflow.xml',
#         'account_invoice_view.xml',
        'wizard/statement_load_voucher_view.xml',
        'wizard/account_bank_statement_payment.xml',
        'wizard/payment_file.xml',
        'voucher_view.xml',
	'cheques.xml',
#         'account_payment_order_view.xml',
#        'account_payment_workflow.xml',
        'data/report_cheque.xml',
        'report/account_check_report.xml',
        'report/report_check_supp.xml',
        'report/report_check_egreso.xml',
        'report/report_check_bco_pacifico.xml',
        'report/report_check_bco_internacional.xml',
	'report/report_print_egreso_cheque.xml',
    ],
    'depends' : ['account_payment', 'bit_account', 'account'], #, 'hr_payroll'
    'data':
        [
            'account_checkbook_workflow.xml',
            'account_checkbook_view.xml',
            #         'account_invoice_workflow.xml',
            #         'account_invoice_view.xml',
            'wizard/statement_load_voucher_view.xml',
            'wizard/account_bank_statement_payment.xml',
            'wizard/payment_file.xml',
            'voucher_view.xml',
            #'cheques.xml',
            #         'account_payment_order_view.xml',
            #        'account_payment_workflow.xml',
            'data/report_cheque.xml',
            'report/account_check_report.xml',
            'report/report_check_supp.xml',
            'report/report_check_egreso.xml',
            'report/report_check_bco_pacifico.xml',
            'report/report_print_egreso_cheque.xml',
            'report/report_check_bco_internacional.xml',
            'report/report_statement_inter_check.xml',
            'report/voucher_solidario_check_report.xml',
            'report/statement_solidario_check_report.xml',
            'report/a_statement_pichincha_check_report.xml',
            'report/a_voucher_pichincha_check_report.xml',
            #'templates/templates.xml',
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
