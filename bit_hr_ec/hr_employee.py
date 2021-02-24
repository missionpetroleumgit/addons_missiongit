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
from openerp import api
from utils import cedula_validation, ruc_validation, thirdty_days_months, MONTHS
from datetime import date, datetime
from dateutil import parser
from openerp import models, api
import openerp
from dateutil.relativedelta import relativedelta
import time


class res_country_canton(osv.osv):
    _description = "Canton"
    _name = 'res.country.canton'
    _columns = {
        'name': fields.char('Cantón', size=64),
        'country_canton_id': fields.many2one('res.country.state', 'Country State'),
    }
res_country_canton()

class hr_employee(osv.osv):
    _inherit = 'hr.employee'
    _description = 'Employee'

    def _birthday_celebration_day(self,cr,uid,ids,field,arg,context=None):
        res = {}
        current_date = date.today()
        for employee in self.browse(cr,uid,ids,context):
            if employee.birthday:
                birthday = datetime.strptime(employee.birthday, "%Y-%M-%d").date()
                res[employee.id] = datetime(current_date.year, birthday.month, birthday.day).strftime("%Y-%M-%d %H:%M:%S")
            else:
                res[employee.id] = date.today().strftime("%Y-%M-%d %H:%M:%S")
        return res

    def onchange_valida_ced_ruc(self, cr, uid, ids, identification_number, tipo_doc):
        res = {'value':{}}
        if tipo_doc=='c':
            cedula_validation(identification_number)
        elif tipo_doc=='r':
            ruc_validation(identification_number)
        elif tipo_doc=='p':
            print 'tipo pasaporte'
            print 'S/N'
        return res

    def onchange_completa_nombre(self, cr, uid, ids, emp_nombres, emp_apellidos):
        res ={}
        if not emp_nombres:
            emp_nombres = ""
        if not emp_apellidos:
            emp_apellidos = ""
        res['value']={'name':emp_apellidos + " " + emp_nombres}
        return res

    def _get_holidays(self, cr, uid, ids, field, arg, context=None):
        res = {}
        holidays_obj = self.pool.get('hr.holidays')
        for employee in self.browse(cr, uid, ids, context=context):
            res[employee.id] = holidays_obj.search(cr, uid , [('employee_id', '=', employee.id),
                                                              ('holiday_status_id.name', '=', 'VACACIONES'),
                                                              ('state', '=', 'validate')])
        return res

    def get_multiplicity(self, work, years, company):
        base = company.base
        available_days = 0
        if years < company.start_counting:
            d = work / 30.00 * base
            return d
        else:
            days = work
            if years > company.limit:
                days = company.limit * 365
            days_count = days - (365 * company.start_counting)
            available_days += (365 * company.start_counting)/30.00 * base
            while days_count > 0:
                days_count -= 365
                base += company.increase
                if days_count >= 0:
                    available_days += 365/30.00*base
                else:
                    available_days += (days_count + 365)/30.00*base
        return available_days

    def _get_available_days(self, cr, uid, ids, field, arg, context=None):
        res = {}
        analysis_date = date.today().strftime('%Y-%m-%d')
        vacations_days = 0
        res_company = self.pool.get('res.users').browse(cr, uid, uid).company_id
        for employee in self.browse(cr, uid, ids, context=context):
            if employee.state_emp == 'sold_out':
                contract = self.pool.get('hr.contract').search(cr, uid, [('employee_id', '=', employee.id)])
                liquidation_date = self.pool.get('hr.contract').read(cr, uid, contract[0], ['date_end'], context)
                analysis_date = liquidation_date['date_end']
            if not res_company.start_counting and not res_company.limit and not res_company.increase:
                res[employee.id] = 0
            else:
                if employee.contract_id:
                    d30 = thirdty_days_months(parser.parse(employee.contract_id.date_start).month.real, parser.parse(analysis_date).month.real)
                    work = parser.parse(analysis_date) - parser.parse(employee.contract_id.date_start)
                    a = MONTHS[parser.parse(analysis_date).month] - parser.parse(analysis_date).day
                    b = MONTHS[parser.parse(employee.contract_id.date_start).month] - \
                        (MONTHS[parser.parse(employee.contract_id.date_start).month] - parser.parse(employee.contract_id.date_start).day) - 1
                    work = work.days.real + d30 + 2 - a - b
                    total_acumulated = self.get_multiplicity(work, int(work/360.00), res_company)
                    for holiday in employee.holidays:
                        vacations_days += holiday.number_of_days_temp
                    available_days = total_acumulated - vacations_days
                    res[employee.id] = available_days
                else:
                    res[employee.id] = 0
        return res

    @api.onchange('emp_porcentaje_disc')
    def onchange_disc_percentage(self):
        if self.emp_porcentaje_disc:
            self.disc_percentage = self.emp_porcentaje_disc
        else:
            self.disc_percentage = '0.00'

    _columns = {
        'birthday_celebration_day':fields.function(_birthday_celebration_day,type='date',method=True),
        'emp_nombres':fields.char('Nombres', size=32),
        'emp_apellidos':fields.char('Apellidos', size=32),
        'emp_tipo_doc':fields.selection((('c','Cedula'),('p','Pasaporte')), "Tipo Identificacion"),
        # Para nomina
        'emp_modo_pago': fields.selection([('transferencia', 'Transferencia'), ('cheque', 'Cheque')], 'Modo de Pago'),

        'emp_quincena': fields.boolean('Cobra Quincena', help='Seleccionar si al empleado se le paga quincena'),
        'emp_quincena_tipo':fields.boolean('Quin. en Valor?', help="Marque este campo si paga la quincena en Valor, "
                                                                    "Desmarcar para pagar en Porcentaje"),
        'emp_quincena_valor': fields.float('Quin. Valor/Porcentaje', digits=(6, 2)),
        'emp_fondo_reserva': fields.boolean('Acumula Fondos de Reserva', help="Marque este campo cuando el empleado "
                                                                              "desee ahorrar el valor de Fondo "
                                                                              "de Reserva"),
        # Discapacidad
        'emp_discapacidad':fields.boolean('Discapacidad', help='Seleccionar si el empleado posee algun tipo de Discapacidad'),
        'emp_tipo_disc':fields.selection((('visual', 'Visual'), ('auditiva', 'Auditiva'),
                                           ('intelectual', 'Intelectual'), ('mental', 'Mental'), ('fisica', 'Fisica')),
                                          "Tipo"),
        'emp_porcentaje_disc': fields.float('Porcentaje'),
        'state_emp': fields.selection([('active', 'Activo'), ('inactive', 'Inactivo'), ('sold_out', 'Liquidado')],
                                      'Estado'),
        'provincia_id': fields.many2one('res.country.state', 'Provincia'),
        'canton_id': fields.many2one('res.country.canton', 'Canton', domain="[('country_canton_id','=',provincia_id)]"),
        'pagar_rol_l': fields.boolean('Pagar rol en liquidación?'),
        # Cargas
        'child_ids': fields.one2many('hr.family.burden', 'employee_id', 'Hijos', ),
        'wife_id': fields.many2one('hr.family.burden', 'Esposo/a'),
        'education_ids': fields.one2many('hr.education.level', 'employee_id', 'Nivel de Estudios', ),
        # Decimos
        'emp_dec_tercero': fields.boolean('Décimo Tercero', help="Marque este campo si desea que al Empleado se le "
                                                                 "pague el Decimo Tercero"),
        'emp_dec_cuarto': fields.boolean('Décimo Cuarto', help="Marque este campo si desea que al Empleado se le pague "
                                                               "el Decimo Cuarto"),
        # Estado Civil
        'marital': fields.selection([('single', 'Single'), ('married', 'Married'), ('widower', 'Widower'),
                                     ('divorced', 'Divorced'), ('union', 'Unión Libre')], 'Marital Status'),
        'bank_account_id': fields.many2one('res.partner.bank', 'Bank Account Number',
                                           domain="[('partner_id','=',address_home_id), "
                                                  "('employee_id','=',id)]",
                                           help="Employee bank salary account"),
        'region': fields.selection([('sierra', 'Sierra - Oriente'), ('costa', 'Costa')], 'Región', required=True),
        'holidays': fields.function(_get_holidays, type="one2many", relation="hr.holidays",
                                    string='Vacaciones'),
        'availables_days': fields.function(_get_available_days, type="float", string='Dias de vacaciones disponibles'),
        'pending_payment': fields.float('Pago pendiente por vacaciones'),
        'emp_ext_cony':fields.boolean('Extensión Conyugue/Hijo IESS', help="Marque este campo si desea la Extensión de Salud para cónyuges/hijos"),

        'f_reserva_reingreso':fields.boolean('Fondo Reserva Reingreso', help="Marque si es reingreso y se debe pagar Fondo de Reserva"),
        'fourth_date': fields.date('Fecha Inicio'),
        'third_date': fields.date('Fecha Inicio'),
        'disc_percentage': fields.float('Porcentaje'),
        'change_type': fields.selection((('monetary', '$'), ('percent', '%'))),

        # JJM nuevos campos 2018-05-05
        # datos caso de emergencia
        'emergency_family': fields.char('Familiar caso de emergencia'),
        'family_relationship': fields.char('Parentesco'),
        'emergency_phone': fields.char('Telefono de emergencia'),
        # datos personales
        'height': fields.float('Estatura', digits=(4, 2)),
        'weight': fields.float('Peso', digits=(5, 2)),
        'driver_licence': fields.char('Tipo de Licencia'),

        'blood_type': fields.selection([('a+', 'A+'), ('a-', 'A-'), ('b+', 'B+'), ('b-', 'B-'),
                                        ('ab+', 'AB+'), ('ab-', 'AB-'),  ('o+', 'O+'), ('o-', 'O-')],
                                      'Tipo de sangre'),

        'work_experience_ids': fields.one2many('hr.employee.work.experience', 'employee_id', 'Experiencia', ),

    }
    _defaults = {
        'emp_tipo_doc': lambda *a: 'c',
        'emp_modo_pago':lambda *a: 'cheque',
        'state_emp': lambda *a: 'active',
        'emp_dec_tercero': lambda *a: False,
        'emp_dec_cuarto': lambda *a: False,
        'pagar_rol_l':False,
        'pending_payment': 0.00,
        'fourth_date': lambda *a: time.strftime('%Y-%m-%d'),
        'third_date': lambda *a: time.strftime('%Y-%m-%d'),
    }

    @api.onchange('emp_quincena_tipo')
    def onchange_change_type(self):
        if self.emp_quincena_tipo == True:
            self.change_type = 'monetary'
        else:
            self.change_type = 'percent'

    def create(self, cr, uid, data, context=None):
        partner_pool = self.pool.get('res.partner')
        context = dict(context or {})
        if context.get("mail_broadcast"):
            context['mail_create_nolog'] = True

        employee_id = super(hr_employee, self).create(cr, uid, data, context=context)
        values = {
            'name': data.get('emp_nombres') + ' ' + data.get('emp_apellidos'),
            'part_type': 'c',
            'part_number': data.get('identification_id'),
            'is_employee': True,
            'employee_id': employee_id
        }
        partner_pool.create(cr, uid, values, context=None)

        if context.get("mail_broadcast"):
            self._broadcast_welcome(cr, uid, employee_id, context=context)
        return employee_id

    def unlink(self, cr, uid, ids, context=None):
        partner_employee_pool = self.pool.get('res.partner')
        for employee in self.browse(cr, uid, ids, context=None):
            partner_employee_ids = partner_employee_pool.search(cr, uid, [('employee_id', '=', employee.id)])
            partner_employee_pool.unlink(cr, uid, partner_employee_ids, context=None)
        return super(hr_employee, self).unlink(cr, uid, ids, context=None)

#     def write(self, cr, uid, ids, values, context=None):
#         employees_ids = self.search(cr, uid, [])
#         partner_pool = self.pool.get('res.partner')
#         for employee in self.browse(cr, uid, employees_ids):
#             if employee.user_id.id != 1 and employee.name and employee.emp_apellidos and employee.identification_id:
#                 values = {
#                     'name': employee.emp_nombres + ' ' + employee.emp_apellidos,
#                     'part_type': 'c',
#                     'part_number': employee.identification_id,
#                     'is_employee': True,
#                     'employee_id': employee.id
#                 }
#                 partner_pool.create(cr, uid, values, context=None)
#
#         return super(hr_employee, self).write(cr, uid, ids, values, context=None)

    # def write(self, cr, uid, ids, values, context=None):
    #     slip_pool = self.pool.get('hr.payslip')
    #     silp_ids = slip_pool.search(cr, uid, [])
    #     for slip in slip_pool.browse(cr, uid, silp_ids):
    #         date_from = datetime.strptime(slip.date_from, "%Y-%m-%d")
    #         if date_from.month < 10:
    #             code_period = '0' + str(date_from.month) + '/' + str(date_from.year)
    #         else:
    #             code_period = str(date_from.month) + '/' + str(date_from.year)
    #         period_id = self.pool.get('account.period').search(cr, uid, [('code', '=', code_period)])
    #         if not slip.period_id:
    #             slip_pool.write(cr, uid, slip.id, {'period_id': period_id[0]})
    #         elif slip.period_id.id not in period_id:
    #             slip_pool.write(cr, uid, slip.id, {'period_id': period_id[0]})
    #
    #     return super(hr_employee, self).write(cr, uid, ids, values, context=None)

    _sql_constraints = [('name_unique', 'unique(identification_id)', 'La cedula debe ser unica!')]
hr_employee()


class WorkExperience(models.Model):
    _description = "Experiencia Laboral empleado"
    _name = 'hr.employee.work.experience'

    company = openerp.fields.Char('Empresa')
    # time_worked = openerp.fields.Char('Tiempo trabajado')
    position = openerp.fields.Char('Cargo')
    boss = openerp.fields.Char('Jefe Inmediato')
    phone = openerp.fields.Char('Telefono')
    start_date = openerp.fields.Date('Fecha Ingreso')
    end_date = openerp.fields.Date('Fecha Retiro')
    end_reason = openerp.fields.Char('Motivo Retiro')
    employee_id = openerp.fields.Many2one('hr.employee', string="Empleado")

WorkExperience()