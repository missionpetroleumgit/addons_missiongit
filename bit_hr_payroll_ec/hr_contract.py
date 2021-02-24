# -*- encoding: utf-8 -*-
########################################################################
#
# @authors: Guillermo Herrera
# Copyright (C) 2014 BITConsultores.
#
#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.
#
# This module is GPLv3 or newer and incompatible
# with OpenERP SA "AGPL + Private Use License"!
#
#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License
#along with this program.  If not, see http://www.gnu.org/licenses.
########################################################################

from openerp.osv import fields, osv
from datetime import datetime

import calendar
from dateutil.relativedelta import relativedelta

def total_anios_laborados(inicio_contrato, fin_periodo):
    if (inicio_contrato.month == fin_periodo.month and fin_periodo.day >= inicio_contrato.day) or (fin_periodo.month > inicio_contrato.month):
        num = fin_periodo.year - inicio_contrato.year
    else:
        num = fin_periodo.year - inicio_contrato.year - 1
    return num

class hr_contract(osv.osv):
    _inherit = 'hr.contract'
    _name = 'hr.contract'

    def _compute_year(self, cr, uid, ids, field, arg, context=None):
        print "_compute_year"
        ''' Función que calcula el número de años de servicio de un empleado trabajando para la empresa.'''

        res = {}
        DATETIME_FORMAT = "%Y-%m-%d"
        today = datetime.now()

        today = today.strftime('%Y-%m-%d')

        rol_fecha = today.split('-')
        rol_anio = rol_fecha[0]
        rol_mes = rol_fecha[1]
        number_of_year = 0
        tupla_dias = calendar.monthrange(int(rol_anio),int(rol_mes))

        month_date_end = datetime.strptime(str(rol_anio) + '-' + str(rol_mes) + '-' + str(tupla_dias[1]), DATETIME_FORMAT)
        control_pool = self.pool.get('change.control')
        first_date = False
        second_date = False
        for contract in self.browse(cr, uid, ids, context=context):
            control_ids1 = control_pool.search(cr, uid, [('contract_id', '=', ids), ('change', '=', 'reint')])
            if control_ids1:
                control_ids = control_pool.search(cr, uid, [('contract_id', '=', ids), ('change', 'in', ('init', 'liq', 'reint'))], order='change_date')
                for control in control_pool.browse(cr, uid, control_ids):
                    if control.change in ['init', 'reint']:
                        first_date = control.change_date
                    else:
                        second_date = control.change_date
                    if second_date and first_date:
			number_of_year += total_anios_laborados(datetime.strptime(first_date, DATETIME_FORMAT), datetime.strptime(second_date, DATETIME_FORMAT))
                        first_date = False
                        second_date = False
            if contract.date_start:
                contract_date_start = datetime.strptime(contract.date_start, DATETIME_FORMAT)
                number_of_year += total_anios_laborados(contract_date_start, month_date_end)
                res[contract.id] = number_of_year
            else:
                res[contract.id] = 0.0
        return res

    def _compute_day_pay(self, cr, uid, ids, field, arg, context=None):
        print "_compute_day_pay"
        """Funcion que me ayuda para calcular los fondos de reserva del empleado"""
        res = {}
        DATETIME_FORMAT = "%Y-%m-%d"
        today = datetime.now()
        last_day=30
        for contract in self.browse(cr, uid, ids, context=context):
            date_start = datetime.strptime(contract.date_start, DATETIME_FORMAT)
            if date_start.day<last_day and date_start.day>1:
                res[contract.id]=last_day-date_start.day
            else:
                res[contract.id] = last_day
        return res

    _columns = {
            'horas_x_dia':fields.integer('Horas de trabajo por día',required=True),
            'number_of_year': fields.function(_compute_year, string='No. de años de servicio', type='float', store=False, method=True, help='Total years of work experience'),
            #        'type_id': fields.many2one('hr.contract.type', "Contract Type", required=False),
            'day_pay':fields.function(_compute_day_pay,string="Día de Pago",type='float',store=False,method=True),
            'type_dismissal': fields.selection([('renuncia', 'Renuncia Voluntaria'), ('intem_fijo', 'Despido intempestivo'), ('intem_faltantes', 'Terminacion Periodo Prueba'),
                                                ('deshaucio', 'Deshaucio')], 'Tipo de Despido', readonly=True),
	    'company_id': fields.many2one('res.company', 'Compania'),
        }

    _defaults = {
        'horas_x_dia': lambda *a: '8',
    }


hr_contract()


class resource_calendar(osv.osv):
    _inherit = 'resource.calendar'
    _name = 'resource.calendar'

    def _compute_hours(self, cr, uid, ids, field, arg, context=None):
        print "_compute_hours"
        ''' Función que calcula el número de horas trabajadas a la semana.'''

        res = {}
        hours_per_day = 0
        hours_per_week = 0

        calendar_obj = self.pool.get('resource.calendar')
        calendar = calendar_obj.browse(cr, uid, ids, context=context)[0]

        for hours in calendar.attendance_ids:
            hours_per_day = hours.hour_to - hours.hour_from
            hours_per_week = hours_per_week + hours_per_day

        res[calendar.id] = hours_per_week

        return res

    _columns = {
       'hours_work_per_week': fields.function(_compute_hours, string='Hours per week', type='float', store=False, method=True, help='Number of hours of work per week.'),
        }

resource_calendar()
