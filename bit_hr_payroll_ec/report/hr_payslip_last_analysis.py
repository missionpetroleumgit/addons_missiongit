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

from openerp import tools
from openerp.osv import fields, osv
from .. import hr_payroll
from openerp.addons.decimal_precision import decimal_precision as dp


class hr_payslip_last_analysis(osv.Model):
    _name = "hr.payslip.last.analysis"
    _description = "Analisis por forma de pago"
    _auto = False
    _rec_name = 'employee_name'
    # _order = 'order'

    _columns = {
        # 'order': fields.char('Order', readonly=True, states={'draft': [('readonly', False)]}),
        'paylist_name': fields.char('Payslip Name', readonly=True, states={'draft': [('readonly', False)]}),
        'number': fields.char('Reference', readonly=True, states={'draft': [('readonly', False)]}),
        'employee_id': fields.many2one('hr.employee', 'Employee', readonly=True),
        'identification_id': fields.char('Identity card', readonly=True, states={'draft': [('readonly', False)]}),
        'employee_name': fields.char('Employee Name', readonly=True, states={'draft': [('readonly', False)]}),
        'bank_account_id': fields.many2one('res.partner.bank', 'Bank Account Number'),
        'emp_modo_pago': fields.selection([('transferencia', 'Transferencia'), ('cheque', 'Cheque')], 'Modo de Pago'),
        'amount': fields.float('Amount', digits_compute=dp.get_precision('Payroll')),
        # 'salary_rule': fields.char('Salary Rule', size=64, required=True),
        'date_from': fields.date('Date From', readonly=True),
        'date_to': fields.date('Date To', readonly=True),
    }
    
    def init(self, cr):
        tools.drop_view_if_exists(cr, 'hr_payslip_last_analysis')
        cr.execute("""
            create or replace view hr_payslip_last_analysis as (
                select
                    min(pl.id) as id,
                    pl.name as paylist_name,
                    pl.number as number,
                    pl.employee_id,
                    empl.identification_id,
                    empl.bank_account_id,
                    empl.emp_modo_pago,
                    empl.name_related as employee_name,
                    l.amount,
                    pl.date_from,
                    pl.date_to
                from hr_payslip pl
                inner join  hr_employee empl on pl.employee_id = empl.id
                inner join  hr_payslip_line l on pl.id = l.slip_id and l.name = 'NETO A RECIBIR'
                where pl.type  = 'rol' and pl.date_from = (SELECT DISTINCT ON (date_from) date_from from hr_payslip where type  = 'rol' order by date_from desc limit 1)
                group by  paylist_name, number, pl.employee_id,empl.identification_id, empl.bank_account_id, employee_name, l.amount, pl.date_from, pl.date_to, empl.emp_modo_pago
            )
        """)
        
# miss b.acc_number as acc_number, 
# inner join  res_partner_bank b on empl.bank_account_id = b.id
# and  group by b.acc_number, 
                
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:


