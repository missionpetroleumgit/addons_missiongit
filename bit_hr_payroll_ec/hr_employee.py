# -*- encoding: utf-8 -*-
##############################################################################
#
#    Author :  Guillermo Herrera Banda: guillermo.herrera@bitconsultores-ec.com
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import fields, osv
from datetime import date, datetime
import time


class hr_employee(osv.osv):
    _inherit = 'hr.employee'
    _description = 'Employee'
    
    def _last_pay_slip(self,cr,uid,ids,field,arg,context=None):
        res = {}        
        for employee in self.browse(cr,uid,ids,context):
            amount = 0.0
            last_date = date.today().strftime("%Y-%m-%d")
            cr.execute('''
                select                    
                    pl.employee_id,                    
                    l.amount,  
                    pl.date_to
                from hr_payslip pl
                inner join  hr_payslip_line l on pl.id = l.slip_id
                inner join  hr_salary_rule r on l.salary_rule_id = r.id
                where pl.date_from = (SELECT DISTINCT ON (date_from) date_from from hr_payslip order by date_from desc limit 1) 
                and r.appears_on_payslip = true
                and r.code = 'NR'
                and pl.employee_id = %s             
                group by  pl.employee_id, l.amount, pl.date_to
                order by pl.employee_id''',([employee.id]))
            values = cr.fetchall()
            if len(values) > 0:
                amount = values[0][1] 
                last_date = values[0][2]
            res[employee.id] = {
                'last_pay_slip_amount' : amount,
                'last_pay_slip_date' : datetime.strptime(last_date, '%Y-%m-%d'),
            }            
        return res

    _columns = {
        'last_pay_slip_amount':fields.function(_last_pay_slip,string='Last Slip Amount',type='float',method=True,multi='_last_pay_slip'),
        'last_pay_slip_date':fields.function(_last_pay_slip,string='Last Slip Date',type='date',method=True,multi='_last_pay_slip'),
        'bank_account': fields.related('bank_account_id', 'acc_number', type='char', string='Account Number', readonly=True),
        'company_ids': fields.many2many('res.company', 'company_employee_relation', 'employee_id', 'company_id', string='Companias que pagan 10%'),
        'pay_10': fields.boolean('cobra 10% ?')
      }

    def last_igbs_amount(self, cr, uid, ids, context=None):
        amount = 0
        for employee in self.browse(cr, uid, ids, context):
            slip_pool = self.pool.get('hr.payslip')
            slip_ids = slip_pool.search(cr, uid, [('employee_id', '=', employee.id), ('type', '=', 'rol')], order='date_to DESC')
            if slip_ids:
                slip_id = slip_ids[0]
                for slip in slip_pool.browse(cr, uid, slip_id):
                    for line in slip.line_ids:
                        if line.category_id.code == 'IGBS':
                            amount += line.total
        return round(amount, 2)

    #Write para actualizar las regiones de los empleados, debe estar comentado si no se va a usar

    # def write(self, cr, uid, ids, values, context=None):
    #     slip_ids = self.pool.get('hr.payslip').search(cr, uid, [])
    #     slips = self.pool.get('hr.payslip').browse(cr, uid, slip_ids, context)
    #     for slip in slips:
    #         self.pool.get('hr.payslip').write(cr, uid, slip.id, {'region': slip.employee_id.region})
    #     return super(hr_employee, self).write(cr, uid, ids, values, context)

    #Write para actualizar el control de cambios en contratos de los empleados, debe estar comentado si no se va a usar

    # def write(self, cr, uid, ids, values, context=None):
    #     contract_pool = self.pool.get('hr.contract')
    #     contract_ids = contract_pool.search(cr, uid, [])
    #     contracts = contract_pool.browse(cr, uid, contract_ids, context)
    #     change_control_pool = self.pool.get('change.control')
    #     for contract in contracts:
    #         user = self.pool.get('res.users').browse(cr, uid, uid)
    #         vals = {
    #                 'contract_id': contract.id,
    #                 'change': 'init',
    #                 'old_value': '-',
    #                 'current_value': contract.wage,
    #                 'user': user.login,
    #                 'change_date': contract.date_start
    #             }
    #         change_control_pool.create(cr, uid, vals)
    #     return super(hr_employee, self).write(cr, uid, ids, values, context)

    #Write para actualizar el campo change_date en el control de cambios, debe estar comentado si no se va a usar

    # def write(self, cr, uid, ids, values, context=None):
    #     control_pool = self.pool.get('change.control')
    #     control_ids = control_pool.search(cr, uid, [('change_date', '=', False)])
    #     controls = control_pool.browse(cr, uid, control_ids, context)
    #     for control in controls:
    #         new_date = datetime.strptime(control.create_date, '%Y-%m-%d %H:%M:%S').strftime("%Y-%m-%d")
    #         control_pool.write(cr, uid, control.id, {'change_date': new_date})
    #     return super(hr_employee, self).write(cr, uid, ids, values, context)
    
hr_employee()
