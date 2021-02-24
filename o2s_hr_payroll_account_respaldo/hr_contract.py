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

class hr_contract(osv.osv):
    _inherit = 'hr.contract'
    _description = 'Contratos'

    def onchange_completa_nombre(self, cr, uid, ids, employee):
        res ={}
        nombre = ""
        
        if employee:
            obj_employee = self.pool.get('hr.employee')
            reads = obj_employee.read(cr, uid, employee, ['name'])
            nombre = reads['name']
        res['value']={'name':"Contrato " + nombre}
        return res
    
    _columns = {
        'horas_x_dia':fields.integer('Horas de trabajo por día',required=True),
        'activo': fields.boolean('Activo?'),
      }
    _defaults = {
        'horas_x_dia': lambda *a: '8',
        'activo': lambda *a: True,
    }
    _sql_constraints = [
            ('unique_active', 'unique(employee_id, activo)', 'El empleado ya tiene ACTIVO un contrato')
            ]
hr_contract()


class hr_contract_type(osv.osv):
    _inherit = 'hr.contract.type'

    _columns = {
        'report_adm': fields.text('Reporte Para Administrativos'),
        'report_oper': fields.text('Reporte para Operativos'),
      }
hr_contract_type()