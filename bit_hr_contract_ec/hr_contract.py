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
from datetime import date
from openerp.report import report_sxw
from number_to_text import Numero_a_Texto

type_of_change = {
    'wage': 'wage',
    'type_id': 'contract',
    'job_id': 'job',
    'horas_x_dia': 'horas_x_dia',
    'state': 'state'
}

class hr_contract(osv.osv):
    _inherit = 'hr.contract'
    _description = 'Contratos'
    
    def get_amount_in_letters(self, wage):
        return Numero_a_Texto(wage)
    
    #def get_fecha_in_letters(self, date_start):
    #    res ={}
        
        

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
        'horas_x_dia':fields.integer('Horas de trabajo por dia',required=True),
        'activo': fields.boolean('Activo?'),
        'pagar_rol_l': fields.boolean('Pagar rol en liquidacion?'),
        'change_control_ids': fields.one2many('change.control', 'contract_id', 'Control de Cambios', ondelete='cascade'),
        'state': fields.selection([('open', 'Abierto'), ('close', 'Terminado')], 'Estado'),
        'name_contractor': fields.char(string="nombre contratante"),
        'identity_contractor': fields.char(string="cedula contratante"),
      }
    _defaults = {
        'horas_x_dia': lambda *a: '8',
        'activo': lambda *a: True,
        'state': 'open'
    }
    _sql_constraints = [
            ('unique_active', 'unique(employee_id, activo)', 'El empleado ya tiene ACTIVO un contrato')
            ]

    def create_change_control(self, cr, uid, ids, vals, context=None):
        # wage, type_id, job_id
        if isinstance(ids, int):
            ids = [ids]
        contract = self.browse(cr, uid, ids[0])
        user = self.pool.get('res.users').browse(cr, uid, uid)
        login = user.login
        print 'este es el login:', login
        values = []
        change_control_pool = self.pool.get('change.control')
        if 'wage' in vals:
            values.append({'field_change': 'wage', 'old_value': contract.wage, 'new_value': vals.get('wage')})
        if 'type_id' in vals:
            type = self.pool.get('hr.contract.type').browse(cr, uid, vals.get('type_id'))
            values.append({'field_change': 'type_id', 'old_value': contract.type_id.name, 'new_value': type.name})
        if 'job_id' in vals:
            job = self.pool.get('hr.job').browse(cr, uid, vals.get('job_id'))
            values.append({'field_change': 'job_id', 'old_value': contract.job_id.name, 'new_value': job.name})
        if 'horas_x_dia' in vals:
            values.append({'field_change': 'horas_x_dia', 'old_value': contract.horas_x_dia, 'new_value': vals.get('horas_x_dia')})
        if 'state' in vals:
            values.append({'field_change': 'liq', 'old_value': contract.state, 'new_value': vals.get('state')})

        for element in values:
            vals = {
                'contract_id': contract.id,
                'change': type_of_change[element['field_change']],
                'old_value': element['old_value'],
                'current_value': element['new_value'],
                'user': login,
                'change_date': date.today()
            }
            change_control_pool.create(cr, uid, vals)

        return True

    def create(self, cr, uid, values, context=None):
        contract_id = super(hr_contract, self).create(cr, uid, values, context)
        change_control_pool = self.pool.get('change.control')
        user = self.pool.get('res.users').browse(cr, uid, uid)
        vals = {
                'contract_id': contract_id,
                'change': 'init',
                'old_value': '-',
                'current_value': values['wage'],
                'user': user.login,
                'change_date': values['date_start']
            }
        change_control_pool.create(cr, uid, vals)
        return contract_id

    def write(self, cr, uid, ids, values, context=None):
        if 'wage' in values or 'type_id' in values or 'job_id' in values or 'horas_x_dia' in values or 'sate' in values:
            self.create_change_control(cr, uid,ids, values)
        return super(hr_contract, self).write(cr, uid, ids, values, context=None)


hr_contract()


class hr_contract_type(osv.osv):
    _inherit = 'hr.contract.type'

    _columns = {
        'report_adm': fields.text('Reporte Para Administrativos'),
        'report_oper': fields.text('Reporte para Operativos'),
      }
hr_contract_type()

# class bit_type_of_change(osv.osv):
#     _name = 'type.of.change'
#     _columns = {
#         'name': fields.char('Tipo de Cambio'),
#         'description': fields.char('Descripcion',size=70)
#     }
# bit_type_of_change()

class bit_change_control(osv.osv):
    _name = 'change.control'
    _columns = {
        'contract_id': fields.many2one('hr.contract', 'Contrato'),
        'change': fields.selection([('wage', 'Salario'), ('contract', 'Tipo de Contrato'),
                                    ('job', 'Puesto de Trabajo'), ('other', 'Othres'), ('horas_x_dia', 'Horas Diarias'),
                                    ('reint', 'Reingreso'), ('liq', 'Liquidacion'), ('init', 'Inicio Contrato')], 'Tipo de Cambio',
                                   required=True),
        'old_value': fields.char('Valor Anterior'),
        'current_value': fields.char('Valor actual'),
        'user': fields.char('Responsable'),
        'change_date': fields.date('Fecha del Cambio')
    }
bit_change_control()

class resource_calendar(osv.osv):
    _inherit = 'resource.calendar'
    _name = 'resource.calendar' 
       
     
    _columns = {
       'desde': fields.char(string='De', required=1),
       'hasta': fields.char(string='Hasta las', required=1),
        }
 
resource_calendar()    

