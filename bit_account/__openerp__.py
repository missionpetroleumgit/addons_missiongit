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
    'name' : 'eInvoicing of Ecuador',
    'version' : '1.1',
    'author' : 'BitConsultores SA',
    'category' : 'Accounting & Finance',
    'description' : """

""",
    'website': 'http://bitconsultores-ec.com',
    'images' : [],
    'depends' : [
                    'bit_base',
                    'bit_partner_identification',
                    'account_cancel', 
                    'account_accountant',
                    'document'
                ],
    'data': [
        'security/ir.model.access.csv',
        'report/report_103_view.xml',
        'report/report_104_view.xml',
		'tipo_sustento_data.xml',
		'tipo_comprobante_data.xml',
        'account_view.xml',
        'account_invoice_view.xml',
        'account_deduction_seq.xml',
        'account_deduction_workflow.xml',
        'ir_sequence_view.xml',
        'period.xml',
        'report/report_ats.xml',
        'report_check.xml',
       # 'report_check_supp.xml',
        'data/report_cheque.xml',
        'data/sequences.xml',
        'account_check_report.xml',
        'report_account_statement.xml',
        'report_egreso_check.xml',
        'report_asientos_contables_view.xml',
		'report/report_definition.xml',
        'report/report_general_ledger_inherit.xml',
        'report/report_financial_inherited.xml',
        'company_view.xml',
        'report/general_ledger_wizard.xml',
        'common_report_extend.xml',
        'report/payables_account_view.xml',
        'report/report_trialbalance_inherited.xml',
        'report/account_state_by_date.xml',
        'account_bank_reconcile.xml',
        'report/report_reconcile.xml',
        'wizard/provision_view.xml',
        'report/purchase_detail.xml',
        'report/purchase_taxes.xml',
        'report/statement_account_supplier_view.xml',
        'wizard/sale_group_invoice.xml',
        'report/statement_account_customer_view.xml',
        'report/account_payables_statement.xml',
        'report/account_receivables_statement.xml'
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
