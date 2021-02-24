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

class hr_payslip(osv.osv):
    _inherit = 'hr.payslip'
    
    def compute_sheet(self, cr, uid, ids, context=None):
        print "********def compute_sheet************: bit_hr_contract_ec_cc"
        slip_line_pool = self.pool.get('hr.payslip.line')
        sequence_obj = self.pool.get('ir.sequence')

        for payslip in self.browse(cr, uid, ids, context=context):
            account_analytic_id = False
            number = payslip.number or sequence_obj.get(cr, uid, 'salary.slip')
            #delete old payslip lines
            old_slipline_ids = slip_line_pool.search(cr, uid, [('slip_id', '=', payslip.id)], context=context)
#            old_slipline_ids
            if old_slipline_ids:
                slip_line_pool.unlink(cr, uid, old_slipline_ids, context=context)
            if payslip.contract_id:
                #set the list of contract for which the rules have to be applied
                contract_ids = [payslip.contract_id.id]
                if payslip.contract_id.contract_analytic_ids:
                    account_analytic_id = payslip.contract_id.contract_analytic_ids[0].account_analytic_id.id
                else:
                    raise osv.except_osv(" Aviso ", 'Debe configurar centro de costos para el empleado. %s' % (payslip.employee_id.name))
                    
            else:
                #if we don't give the contract, then the rules to apply should be for all current contracts of the employee
                contract_ids = self.get_contract(cr, uid, payslip.employee_id, payslip.date_from, payslip.date_to, context=context)
            #lines = [(0,0,line) for line in self.pool.get('hr.payslip').get_payslip_lines(cr, uid, contract_ids, payslip.id, context=context)]
            lines = []
            for line in self.pool.get('hr.payslip').get_payslip_lines(cr, uid, contract_ids, payslip.id, context=context):
                line['department_id'] = payslip.employee_id.department_id.id
                lines += [(0,0,line)]
            self.write(cr, uid, [payslip.id], {'line_ids': lines, 'number': number,'department_id':payslip.employee_id.department_id.id,
                                               'provincia_id':payslip.employee_id.provincia_id.id,
                                               'business_unit_id':payslip.employee_id.business_unit_id.id,
                                               'account_analytic_id':account_analytic_id}, context=context)
        return True

    _columns = {
        'account_analytic_id': fields.many2one('account.analytic.account', "Centro de Costos"),

    }
hr_payslip()
