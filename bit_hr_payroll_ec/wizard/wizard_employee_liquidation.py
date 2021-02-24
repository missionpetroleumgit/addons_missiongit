# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
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
# import wizard
from time import strftime
from string import upper, capitalize
from string import join
from openerp.osv import fields, osv
from openerp.tools.translate import _
import time

class hr_employee_liquidation(osv.osv):
    _name = "hr.employee.liquidation"
    
    _description = "Employee Liquidation"   
    
    
    _columns = {
        'employee_id': fields.many2one('hr.employee', 'Empleado'),
        'contract_id': fields.related('contract_id', 'employee_id', type='many2one', relation='hr.contract', string='Contract', store=True, readonly=True),
        'type': fields.selection([('renuncia', 'Renuncia Voluntaria'), ('intem_fijo', 'Por Despido Intempestivo'),('intem_faltantes', 'Terminación de contrato periodo de prueba'), ('deshaucio', 'Deshaucio')], 'Tipo de liquidacion'),
        'date': fields.date('Fecha'),
        'observation':fields.text('Observacion'),
        'pagar_rol':fields.boolean('Pagar Rol', help='Marcas si desea pagar el Rol proporcional en el periodo'),
        # 'start_period': fields.many2one('hr.period.period', 'Periodo Inicial'),
        # 'end_period': fields.many2one('hr.period.period', 'Periodo Final')
        'company_id': fields.many2one('res.company', 'Empresa'),
    }
    _defaults = {
        'date': lambda *a: time.strftime('%Y-%m-%d'),
        'type': lambda * a: 'renuncia',
        'company_id': lambda s, cr, uid, c: s.pool.get('res.company')._company_default_get(cr, uid, 'hr.employee.liquidation', context=c),
    }

hr_employee_liquidation()


class wizard_employee_liquidation(osv.osv_memory):
    _name = 'wizard.employee.liquidation'
    _description = 'liquidacion de empleados'
    _columns = {
        'employee_id': fields.many2one('hr.employee', 'Empleado'),
        'contract_id': fields.related('contract_id', 'employee_id', type='many2one', relation='hr.contract', string='Contract', store=True, readonly=True),
        'type': fields.selection([('renuncia', 'Renuncia Voluntaria'), ('intem_fijo', 'Por Despido Intempestivo'),('intem_faltantes', 'Terminación de contrato periodo de prueba'), ('deshaucio', 'Deshaucio')], 'Tipo de liquidacion'),
        #'type': fields.selection([('renuncia', 'Renuncia'), ('intem_fijo', 'Por Despido Intempestivo 3 meses'), ('intem_faltantes', 'Por Despido Intempestivo Meses Faltantes'), ('deshaucio', 'Deshaucio')], 'Tipo de liquidacion'),
        'date': fields.date('Fecha'),
        'pagar_rol':fields.boolean('Pagar Rol',help='Marcas si desea pagar el Rol proporcional en el periodo'),
        'observation':fields.text('Observacion'),
        'availables_days': fields.float("Dias de Vacaciones"),
        'start_period': fields.many2one('account.period', 'Periodo Inicial'),
        'end_period': fields.many2one('account.period', 'Periodo Final')
    }
    _defaults = {
       'date': lambda *a: time.strftime('%Y-%m-%d'),
       'type': lambda * a: 'renuncia',
    }

    def onchange_employee(self, cr, uid, ids, employee_id, context=None):
        res = {}
        print employee_id
        if employee_id:
            employee = self.pool.get('hr.employee').browse(cr, uid, employee_id)
            res['value'] = {'availables_days': employee.availables_days}
        return res

    def process_liquidation(self, cr, uid, ids, context=None):
        """
        @param cr: the current row, from the database cursor,
        @param uid: the current user’s ID for security checks,
        @param ids: List of account chart’s IDs
        @return: dictionary of Candidate (employees) for this job and insert in the applications
        """    
        hr_employee_liquidation_obj = self.pool.get('hr.employee.liquidation')
        hr_employee_obj = self.pool.get('hr.employee')        
        hr_contract_obj = self.pool.get('hr.contract')
        change_control_pool = self.pool.get('change.control')
        # employees = []
        vals = {}
        # contract_id = 0
        user = self.pool.get('res.users').browse(cr, uid, uid)
        for form in self.browse(cr, uid, ids):  
            hr_employee_obj.write(cr, uid, [form.employee_id.id],  { 'state_emp': 'sold_out', 'pagar_rol_l': form.pagar_rol})         
            # for contract in form.employee_id.contract_ids:
            #     contract_id = contract.id
            vals = {
                        'employee_id': form.employee_id.id,
                        'type': form.type,
                        'date' : form.date,
                        'observation' : form.observation,
                        'pagar_rol': form.pagar_rol,
                        'start_period': form.start_period.id,
                        'end_period': form.end_period.id
                    }
            hr_employee_liquidation_obj.create(cr, uid, vals)
            hr_contract_obj.write(cr, uid, [form.employee_id.contract_id.id], {'date_end': form.date, 'state': 'close'})
            vals = {
                'contract_id': form.employee_id.contract_id.id,
                'change': 'liq',
                'old_value': form.employee_id.contract_id.wage,
                'current_value': '-',
                'user': user.login,
                'change_date': form.date
            }
            change_control_pool.create(cr, uid, vals)
        models_data = self.pool.get('ir.model.data')
        dummy, search_view = models_data.get_object_reference(cr, uid, 'bit_hr_payroll_ec', 'view_employee_liquidation_filter')
        dummy, form_view = models_data.get_object_reference(cr, uid, 'bit_hr_payroll_ec', 'view_employee_liquidation_form')
        dummy, tree_view = models_data.get_object_reference(cr, uid, 'bit_hr_payroll_ec', 'view_employee_liquidation_tree')

        return {
            'name': _('Employee Liquidation'),           
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'hr.employee.liquidation',
            'view_id': 'hr_employee_liquidation',
            'views': [
                      (tree_view, 'tree'),
                      (form_view, 'form')],
            'type': 'ir.actions.act_window',
        }


wizard_employee_liquidation()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
