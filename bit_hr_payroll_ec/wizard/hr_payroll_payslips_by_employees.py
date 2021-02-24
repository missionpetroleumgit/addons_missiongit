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

import time
from datetime import datetime
from dateutil import relativedelta

from openerp.osv import fields, osv
from openerp.tools.translate import _

class hr_payslip_employees(osv.osv_memory):
    _inherit = 'hr.payslip.employees'

    def get_slip_period(self, cr, uid, end_date):
        period_id = self.pool.get('account.period').search(cr, uid, [('date_start', '<=', end_date), ('date_stop', '>=', end_date), ('special', '=', False)])
        if period_id:
            return period_id[0]
        return False
    
    def compute_sheet(self, cr, uid, ids, context=None):
        emp_pool = self.pool.get('hr.employee')
        slip_pool = self.pool.get('hr.payslip')
        run_pool = self.pool.get('hr.payslip.run')
        slip_ids = []
        if context is None:
            context = {}
        data = self.read(cr, uid, ids, context=context)[0]
        run_data = {}
        if context and context.get('active_id', False):
            run_data = run_pool.read(cr, uid, [context['active_id']], ['date_start', 'date_end', 'credit_note','type','struct_id'])[0]
        from_date =  run_data.get('date_start', False)
        to_date = run_data.get('date_end', False)
        type = run_data.get('type', False)
        credit_note = run_data.get('credit_note', False)
        if not data['employee_ids']:
            raise osv.except_osv(_("Warning!"), _("You must select employee(s) to generate payslip(s)."))
        for emp in emp_pool.browse(cr, uid, data['employee_ids'], context=context):
            slip_data = slip_pool.onchange_employee_id(cr, uid, [], from_date, to_date, emp.id, contract_id=False, context=context)
            if not slip_data['value'].get('contract_id'):
                continue
            if run_data.get('type') == 'rol':
                name = 'ROL DE ' + emp.name

            elif run_data.get('type') == 'quincena':
                name = 'QUINCENA DE ' + emp.name

            elif run_data.get('type') == 'liquidation':
                name = 'LIQUIDACION DE ' + emp.name

            elif run_data.get('type') == 'serv10':
                name = 'PAGO 10% DE ' + emp.name
            res = {
                'employee_id': emp.id,
                'type': run_data.get('type', False),
                'struct_id': run_data.get('struct_id')[0],
                'contract_id': slip_data['value'].get('contract_id', False),
                'payslip_run_id': context.get('active_id', False),
                'input_line_ids': [(0, 0, x) for x in slip_data['value'].get('input_line_ids', False)],
                'worked_days_line_ids': [(0, 0, x) for x in slip_data['value'].get('worked_days_line_ids', False)],
                'date_from': from_date,
                'date_to': to_date,
                'credit_note': credit_note,
                'period_id': self.get_slip_period(cr, uid, run_data['date_end'])
            }
            res.update({'name': name})
            slip_ids.append(slip_pool.create(cr, uid, res, context=context))
        slip_pool.compute_sheet(cr, uid, slip_ids, context=context)
        return {'type': 'ir.actions.act_window_close'}


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
