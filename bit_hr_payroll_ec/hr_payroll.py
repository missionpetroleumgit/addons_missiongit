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

import time
from datetime import date
from datetime import datetime
from datetime import timedelta
from dateutil import relativedelta
from dateutil.relativedelta import *
from dateutil import parser
import calendar
from openerp.tools.translate import _
from openerp.osv import fields, orm
from utils import thirdty_days_months, thirty_days_months2


MONTHS = {
    1: 31, 2: 29, 3: 31, 4: 30, 5: 31, 6: 30,
    7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31
}


def total_anios_laborados(inicio_contrato, fin_periodo, estado, fecha_sali):
    if estado:
        init_cont = inicio_contrato + timedelta(days=365)
        if estado == 'sold_out':
            if (inicio_contrato.month == fin_periodo.month and fecha_sali >= init_cont) or (fin_periodo.month > inicio_contrato.month and fecha_sali >= init_cont):
                num = fin_periodo.year - inicio_contrato.year
            else:
                num = fin_periodo.year - inicio_contrato.year - 1
        if estado == 'active':
            if (inicio_contrato.month == fin_periodo.month and fin_periodo.day >= inicio_contrato.day) or (fin_periodo.month > inicio_contrato.month):
                num = fin_periodo.year - inicio_contrato.year
            else:
                num = fin_periodo.year - inicio_contrato.year - 1
    return num


def work_years(datetime_start, datetime_end):
    num = round(float((datetime_end-datetime_start).days / 365.00),2)
    return num


class hr_salary_rule_percentage_base(osv.osv):
    _name = "hr.salary.rule.percentage.base"
    _columns = {
        'name':fields.char('Description', size=64, required=True),
        'base':fields.char('Percentage based on',size=1024, required=True, help='result will be affected to a variable'),
    }
hr_salary_rule_percentage_base()


class hr_payslip_input(osv.osv):
    _inherit = 'hr.payslip.input'

    _columns = {
        'horas' : fields.float('Horas', digits=(6, 2)),
        'income_id' : fields.many2one('hr.income', 'Ingreso'),
        'expense_id' : fields.many2one('hr.expense', 'Egreso'),
        'loan_id': fields.many2one('hr.loan', 'Prestamos')
    }
    _order = 'payslip_id, sequence'
    _defaults = {
        'sequence': 10,
        'amount': 0.0,
    }
hr_payslip_input()


class hr_payslip_run(osv.osv):
    _inherit = 'hr.payslip.run'

    def _get_type(self, cr, uid, context=None):
        if context is None:
            context = {}
        if ('type' in context):
            if context['type'] == 'quincena':
                type = context.get('type', 'quincena')
            elif context['type'] == 'rol':
                type = context.get('type', 'rol')
            else:
                type = context.get('type', 'liquidation')
            return type
        else:
            return False

    def _get_struct_id(self, cr, uid, context=None):
        if context is None:
            context = {}
        print 'CONTEXTOOOOO', context
        struct_id = False
        if ('type' in context):
            if context['type'] == 'quincena':
                hr_payroll_struct_obj = self.pool['hr.payroll.structure']
                search_struct = hr_payroll_struct_obj.search(cr, uid, [('code','=', 'Quincenas')])
                if len(search_struct) > 0:
                    struct_id = context.get('struct_id', search_struct[0])
                else:
                    raise osv.except_osv(_('Estructura invalida !'), _('Revise el codigo de la estructura QUINCENAS es Quincenas !'))
            elif context['type'] == 'rol':
                hr_payroll_struct_obj = self.pool['hr.payroll.structure']
                search_struct = hr_payroll_struct_obj.search(cr, uid, [('code','=', 'Nomina')])
                if len(search_struct) > 0:
                    struct_id = context.get('struct_id', search_struct[0])
                else:
                    raise osv.except_osv(_('Estructura invalida !'), _('Revise el codigo de la estructura NOMINA es Nomina !'))
            elif context['type'] == 'liquidation':
                hr_payroll_struct_obj = self.pool['hr.payroll.structure']
                search_struct = hr_payroll_struct_obj.search(cr, uid, [('code','=', 'Liquidacion')])
                if len(search_struct) > 0:
                    struct_id = context.get('struct_id', search_struct[0])
                else:
                    raise osv.except_osv(_('Estructura invalida !'), _('Revise el codigo de la estructura LIQIDACIONES es Liquidacion !'))
            return struct_id
        else:
            return False

    def _get_fiscalyear_id(self, cr, uid, context=None):
        fiscalyear_id = self.pool.get('hr.salary.rule').get_current_fiscalyear(cr, uid, context=None)
        return fiscalyear_id

    def draft_payslip_run(self, cr, uid, ids, context=None):
        obj_payslip = self.pool.get('hr.payslip')
        for payslip_run in self.browse(cr, uid, ids):
            for slip in payslip_run.slip_ids:
                obj_payslip.cancel_sheet(cr, uid, [slip.id], context=None)
                obj_payslip.signal_workflow(cr, uid, [slip.id], 'draft')

        return self.write(cr, uid, ids, {'state': 'draft'}, context=context)

    def validate_payslip_run(self, cr, uid, ids, context=None):
        obj_payslip = self.pool['hr.payslip']
        obj_payslip_run = self.browse(cr, uid, ids)
        for roles in obj_payslip_run.slip_ids:
            obj_payslip.process_sheet(cr, uid, [roles.id], context=context)
        return self.write(cr, uid, ids, {'state': 'validate'}, context=context)

    _columns = {
        'struct_id': fields.many2one('hr.payroll.structure', 'Estructura'),
        'type': fields.selection([
            ('rol','Rol'),
            ('quincena', 'Quincena'),
            ('liquidation', 'Liquidación'),
        ],'Tipo', select=True),
        'state': fields.selection([
            ('draft', 'Draft'),
            ('close', 'Close'),
            ('validate', 'Validado'),
        ], 'Status', select=True, readonly=True, copy=False),
        'fiscalyear_id': fields.many2one('account.fiscalyear', 'Año Fiscal'),

    }
    _defaults = {
        'type': _get_type,
        'struct_id': _get_struct_id,
        'fiscalyear_id': _get_fiscalyear_id,
    }

hr_payslip_run()


class hr_holidays(orm.Model):
    _inherit = 'hr.holidays'

    def is_day_leave(self, cr, uid, dt, employee_id, context=None):
        if not dt:
            return False
        print "is_day_leave dt:", dt
        hr_holiday_obj = self.pool['hr.holidays']
        holidays_line_ids = hr_holiday_obj.search(cr, uid, [('employee_id','=', employee_id),('date_from','<=', date.strftime(dt, "%Y-%m-%d")),('date_to','>=', date.strftime(dt, "%Y-%m-%d")),('state', 'not in', ['cancel', 'refuse'])])
        print "holidays_line_ids: ", holidays_line_ids
        if len(holidays_line_ids)>0:

            print "True"
            return True
        return False

    _columns = {
        'finalizado': fields.boolean('Finalizado'),
        'date_from': fields.date('Start Date', readonly=True, states={'draft':[('readonly',False)], 'confirm':[('readonly',False)]}, select=True, copy=False),
        'date_to': fields.date('End Date', readonly=True, states={'draft':[('readonly',False)], 'confirm':[('readonly',False)]}, copy=False),
        'amount': fields.float('Monto pagado'),
        'move_id': fields.many2one('account.move', 'Asiento contable', readonly=True)

    }
    _defaults = {
        'finalizado': lambda *a: False,
        'amount': 0.00
    }

    def onchange_date_from(self, cr, uid, ids, date_to, date_from):

        result = {'value': {}}
        """
        If there are no date set for date_to, automatically set one 8 hours later than
        the date_from.
        Also update the number_of_days.
        """
        # date_to has to be greater than date_from
        if (date_from and date_to) and (date_from > date_to):
            warning = {
                'title': _('Warning!'),
                'message': _('The start date must be anterior to the end date.'),
            }
            # raise osv.except_osv(_('Warning!'),_('The start date must be anterior to the end date.'))

            result['value'] = {'date_from': None}
            result['warning'] = warning
            return result

        # Compute and update the number of days
        if (date_to and date_from) and (date_from <= date_to):
            date_from = parser.parse(date_from)
            date_to = parser.parse(date_to)
            diff_day = date_to.date() - date_from.date()
            result['value']['number_of_days_temp'] = diff_day.days.real + 1
        else:
            result['value']['number_of_days_temp'] = 0

        return result

    def onchange_date_to(self, cr, uid, ids, date_to, date_from):
        """
        Update the number_of_days.
        """

        # date_to has to be greater than date_from
        result = {'value': {}}
        if (date_from and date_to) and (date_from > date_to):
            warning = {
                'title': _('Warning!'),
                'message': _('The start date must be anterior to the end date.'),
            }
            result['value'] = {'date_from': None}
            result['warning'] = warning
            return result

        # Compute and update the number of days
        if (date_to and date_from) and (date_from <= date_to):
            date_from = parser.parse(date_from)
            date_to = parser.parse(date_to)
            diff_day = date_to.date() - date_from.date()
            result['value']['number_of_days_temp'] = diff_day.days.real + 1
        else:
            result['value']['number_of_days_temp'] = 0

        return result

    def create(self, cr, uid, values, context=None):
        date_from = parser.parse(values.get('date_from'))
        date_to = parser.parse(values.get('date_to'))
        values.update({'date_from': date_from.date()})
        values.update({'date_to': date_to.date()})
        return super(hr_holidays, self).create(cr, uid, values, context=None)

    def write(self, cr, uid, ids, values, context=None):
        if values.get('date_from'):
            date_from = parser.parse(values.get('date_from'))
            values.update({'date_from': date_from.date()})
        if values.get('date_to'):
            date_to = parser.parse(values.get('date_to'))
            values.update({'date_to': date_to.date()})
        return super(hr_holidays, self).write(cr, uid, ids, values, context=None)

    def get_days_from_date(self, employee, date_to, res_company):
        available = 0.0
        vacations_days = 0.0
        if employee.contract_id:
            d30 = thirty_days_months2(employee.contract_id.date_start, date_to)
            work = parser.parse(date_to) - parser.parse(employee.contract_id.date_start)
            work = work.days.real - d30
            total_acumulated = self.pool.get('hr.employee').get_multiplicity(work, int(work / 360.0), res_company)
            for holiday in employee.holidays:
                vacations_days += holiday.number_of_days_temp

            available = total_acumulated - vacations_days
        return available

    def holidays_validate(self, cr, uid, ids, context=None):
        if context is None:
            context = dict()
        user = self.pool.get('res.users').browse(cr, uid, uid)
        if user.company_id.vacation_entry:
            holidays = self.browse(cr, uid, ids[0])
            acumulate_pool = self.pool.get('hr.acumulados')
            if holidays.holiday_status_id.name == 'VACACIONES':
                if holidays.employee_id.availables_days < holidays.number_of_days_temp:
                    raise osv.except_osv('Error', 'Los dias de vacaciones deben ser menor o igual a los disponibles')
                paysilp_lines_pool = self.pool.get('hr.payslip.line')
                contract_pool = self.pool.get('hr.contract')
                amount = 0.00
                pay_amount = 0.00
                contract_ids = contract_pool.search(cr, uid, [('activo', '=', True), ('employee_id', '=', holidays.employee_id.id)])
                if not contract_ids:
                    raise osv.except_osv('Error!!', 'El empleado no tiene contrato asociado')
                contract = contract_pool.browse(cr, uid, contract_ids[0])
                date_to_parser = parser.parse(holidays.date_from) - relativedelta(months=1)
                date_tuple = calendar.monthrange(date_to_parser.year, date_to_parser.month)
                month = str(date_to_parser.month)
                if date_to_parser.month < 10:
                    month = '0' + str(date_to_parser.month)
                date_to = str(date_to_parser.year) + '-' + month + '-' + str(date_tuple[1])
                date_h = holidays.date_from
                available = self.get_days_from_date(holidays.employee_id, date_h, user.company_id)
                if holidays.number_of_days_temp > available:
                    raise osv.except_osv('Error!!', 'No puede asignar mas dias de los que tiene disponible: (%s)' % holidays.employee_id.availables_days)
                # limit = None
                # cant_nom = holidays.number_of_days_temp/1.25
                # rest_cant_nom = holidays.number_of_days_temp % 1.25
                # if rest_cant_nom > 0:
                #     limit = int(cant_nom) + 1
                # else:
                #     limit = int(cant_nom)
                if holidays.employee_id.holidays:
                    holi_ids = self.search(cr, uid, [('employee_id', '=', holidays.employee_id.id), ('holiday_status_id.name', '=', 'VACACIONES'), ('id', '!=', holidays.id),
                                                     ('state', '=', 'validate')],
                                           order='date_from desc')
                    date_from = self.browse(cr, uid, holi_ids[0]).date_from
                else:
                    date_from = contract.date_start

                payslip_lines = paysilp_lines_pool.search(cr, uid, [('slip_id.date_to', '>=', date_from),
                                                                    ('employee_id', '=', holidays.employee_id.id),
                                                                    ('code', '=', 'PROVAC'), ('active', '=', True)])

                for slip_line in paysilp_lines_pool.browse(cr, uid, payslip_lines):
                    if parser.parse(slip_line.slip_id.date_from).month != parser.parse(holidays.date_from).month or \
                            (parser.parse(slip_line.slip_id.date_from).month == parser.parse(holidays.date_from).month and
                                     parser.parse(slip_line.slip_id.date_from).year != parser.parse(holidays.date_from).year):
                        amount += slip_line.total
                # acumulate_ids = acumulate_pool.search(cr, uid, [('employee_id', '=', holidays.employee_id.id), ('fch_contrato', '=', contract.date_start)])
                # if acumulate_ids:
                #     for acumulate_obj in acumulate_pool.browse(cr, uid, acumulate_ids):
                #         for line in acumulate_obj.acumulados_line:
                #             amount += line.vacaciones
                if round(holidays.employee_id.pending_payment, 2) == round(amount, 2):
                    pass
                else:
                    amount += holidays.employee_id.pending_payment
                pay_amount = amount * holidays.number_of_days_temp / available
                self.pool.get('hr.employee').write(cr, uid, holidays.employee_id.id, {'pending_payment': amount - pay_amount})
                move = self.create_move(cr, uid, holidays.employee_id.business_unit_id.id, pay_amount, holidays.date_from, contract.journal_id.id,
                                        holidays.employee_id, holidays, contract)
                self.write(cr, uid, holidays.id, {'amount': pay_amount, 'move_id': move})
        return super(hr_holidays, self).holidays_validate(cr, uid, ids, context)

    def create_move(self, cr, uid, business_unit_id, amount, date_created, journal_id, employee, holidays, contract):
        salary_account_pool = self.pool.get('hr.salary.rule.account')
        salary_account_ids = salary_account_pool.search(cr, uid, [('salary_rule_id.code', '=', 'CONFIG'), ('business_unit_id', '=', business_unit_id)])
        if not salary_account_ids:
            raise osv.except_osv('Error!!', 'No hay configuracion salarial de vacaciones para la unidad de negocios del empleado')
        salary_account = salary_account_pool.browse(cr, uid, salary_account_ids[0])
        name = 'Registro Vacaciones %s' % employee.name_related
        period_ids = self.pool.get('account.period').search(cr, uid, [('date_start', '<=', date_created), ('date_stop', '>=', date_created)])
        if not period_ids:
            raise osv.except_osv('Error', 'No hay un periodo que contenga la fecha de inicio de vacaciones')
        move_id = self.pool.get('account.move').create(cr, uid, {'ref': name, 'journal_id': journal_id,
                                                                 'date': date_created, 'narration': holidays.id, 'period_id': period_ids[0]})
        line_pool = self.pool.get('account.move.line')
        partner_pool = self.pool.get('res.partner')
        partner_ids = partner_pool.search(cr, uid, [('employee_id', '=', employee.id)])
        if not partner_ids:
            raise osv.except_osv('Error!!', 'El empleado no tiene un partner asociado')
        partner = partner_pool.browse(cr, uid, partner_ids[0])
        debit = {
            'name': holidays.name if holidays.name else 'Vacaciones',
            'quantity': 0,
            'date': date_created,
            'debit': round(amount, 2),
            'credit': 0.00,
            'account_id': salary_account.debit_account_id.id,
            'move_id': move_id,
            'partner_id': partner.id
        }
        line_pool.create(cr, uid, debit)
        if contract.contract_analytic_ids:
            diff = 0.00
            count=1
            for analytic in contract.contract_analytic_ids:
                if count==len(contract.contract_analytic_ids):
                    credit_amount = amount-diff
                else:
                    credit_amount = round((amount*analytic.rate)/100, 2)
                credit = {
                    'name': holidays.name if holidays.name else 'Vacaciones',
                    'quantity': 0,
                    'date': date_created,
                    'credit': credit_amount,
                    'debit': 0.00,
                    'analytic_account_id': analytic.account_analytic_id.id,
                    'account_id': salary_account.credit_account_id.id,
                    'move_id': move_id,
                    'partner_id': partner.id
                }
                line_id = line_pool.create(cr, uid, credit)
            if 1 > round(amount, 2) - diff > 0.00:
                line = line_pool.browse(cr, uid, line_id)
                line_pool.write(cr, uid, line_id, {'credit': line.credit + (amount - diff)})
                self.pool.get('account.move').post(cr, uid, move_id)
        else:
            credit = {
                'name': holidays.name if holidays.name else 'Vacaciones',
                'quantity': 0,
                'date': date_created,
                'credit': round(amount, 2),
                'debit': 0.00,
                'account_id': salary_account.credit_account_id.id,
                'move_id': move_id,
                'partner_id': partner.id
            }
            line_pool.create(cr, uid, credit)
        return move_id

    def holidays_refuse(self, cr, uid, ids, context = None):
        if context is None:
            context = dict()
        user = self.pool.get('res.users').browse(cr, uid, uid)
        obj_emp = self.pool.get('hr.employee')
        move_pool = self.pool.get('account.move')
        paysilp_lines_pool = self.pool.get('hr.payslip.line')
        contract_pool = self.pool.get('hr.contract')
        for holiday in self.browse(cr, uid, ids):
            contract_ids = contract_pool.search(cr, uid, [('activo', '=', True), ('employee_id', '=', holiday.employee_id.id)])
            contract = contract_pool.browse(cr, uid, contract_ids[0])
            if user.company_id.vacation_entry:
                amount = 0.0
                if holiday.employee_id.holidays:
                    holi_ids = self.search(cr, uid, [('employee_id', '=', holiday.employee_id.id),
                                                     ('holiday_status_id.name', '=', 'VACACIONES'),
                                                     ('id', '!=', holiday.id),
                                                     ('state', '=', 'validate')], order='date_from desc')
                    if holi_ids:
                        date_from = self.browse(cr, uid, holi_ids[0]).date_from
                    else:
                        date_from = contract.date_start
                else:
                    date_from = contract.date_start
                payslip_lines = paysilp_lines_pool.search(cr, uid, [('slip_id.date_to', '>=', date_from),
                                                                    ('employee_id', '=', holiday.employee_id.id),
                                                                    ('code', '=', 'PROVAC'),
                                                                    ('active', '=', True)])
                for slip_line in paysilp_lines_pool.browse(cr, uid, payslip_lines):
                    if parser.parse(slip_line.slip_id.date_from).month != parser.parse(holiday.date_from).month or \
                            (parser.parse(slip_line.slip_id.date_from).month == parser.parse(holiday.date_from).month and
                                     parser.parse(slip_line.slip_id.date_from).year != parser.parse(holiday.date_from).year):
                        amount += slip_line.total
                date_to_parser = parser.parse(holiday.date_from) - relativedelta(months=1)
                date_tuple = calendar.monthrange(date_to_parser.year, date_to_parser.month)
                month = str(date_to_parser.month)
                if date_to_parser.month < 10:
                    month = '0' + str(date_to_parser.month)
                date_to = str(date_to_parser.year) + '-' + month + '-' + str(date_tuple[1])
                available = self.get_days_from_date(holiday.employee_id, date_to, user.company_id)
                amount_before = holiday.amount * (available - holiday.number_of_days) / holiday.number_of_days
                obj_emp.write(cr, uid, holiday.employee_id.id, {'pending_payment': -amount_before - amount})
            move_ids = move_pool.search(cr, uid, [('narration', '=', str(holiday.id))])
            if move_ids:
                move_pool.button_cancel(cr, uid, move_ids)
                move_pool.unlink(cr, uid, move_ids)

        return super(hr_holidays, self).holidays_refuse(cr, uid, ids, context)


hr_holidays()

class hr_holidays_public(orm.Model):
    _inherit = 'hr.holidays.public'

    def is_public_holiday(self, cr, uid, dt, employee_id=None, context=None):

        if not dt:
            return False

        hr_holiday_public_line_obj = self.pool['hr.holidays.public.line']
        holidays_line_ids = hr_holiday_public_line_obj.search(cr, uid, [])
        lines_obj = hr_holiday_public_line_obj.browse(cr, uid, holidays_line_ids)
        for line in lines_obj:
            if date.strftime(dt, "%Y-%m-%d") == line.date:
                return True

        return False

hr_holidays_public()

class hr_payslip(osv.osv):
    '''
    Pay Slip
    '''
    _inherit = 'hr.payslip'

    def get_contract(self, cr, uid, employee, date_from, date_to, context=None):

        print "***get_contract: "
        print "employee: ", employee
        print "date_from: ", date_from
        print "date_to: ", date_to
        """
        @param employee: browse record of employee
        @param date_from: date field
        @param date_to: date field
        @return: returns the ids of all the contracts for the given employee that need to be considered for the given dates
        """
        contract_obj = self.pool.get('hr.contract')
        clause = []
        #a contract is valid if it ends between the given dates
        clause_1 = ['&',('date_end', '<=', date_to),('date_end','>=', date_from)]
        #OR if it starts between the given dates
        clause_2 = ['&',('date_start', '<=', date_to),('date_start','>=', date_from)]
        #OR if it starts before the date_from and finish after the date_end (or never finish)
        clause_3 = ['&',('date_start','<=', date_from),'|',('date_end', '=', False),('date_end','>=', date_to)]
        clause_final =  [('employee_id', '=', employee.id), ('activo', '=', True),'|','|'] + clause_1 + clause_2 + clause_3
        print "clause_final: ", clause_final
        contract_ids = contract_obj.search(cr, uid, clause_final, context=context)
        print "contract_ids: ", contract_ids
        return contract_ids

    def get_inputs(self, cr, uid, contract_ids, date_from, date_to, context=None):
        print "****context: ", context
        print "uid"
        tipo = context['type']
        res = []
        contract_obj = self.pool.get('hr.contract')
        if tipo in ['rol', 'liquidation']:

            for contract in contract_obj.browse(cr, uid, contract_ids, context=context):
                res = super(hr_payslip, self).get_inputs(cr, uid, contract_ids, date_from, date_to, context=context)

                # Ingresos
                income_obj = self.pool.get('hr.income')
                income_ids = income_obj.search(cr, uid, [('employee_id','=', contract.employee_id.id),('date','<=', date_to),('date','>=', date_from),('fijo','=',False)])
                print "income_ids: ", income_ids

                for income in income_obj.browse(cr, uid, income_ids):
                    input = {
                        'name': income.adm_id.name,
                        'code': income.adm_id.code,
                        'amount': income.value,
                        'contract_id': contract.id,
                        'horas': income.horas,
                        'income_id':income.id,
                    }
                    res += [input]
                    income_obj.write(cr, uid, income.id, {"state":'procesado'})

                # Prestamos
                loan_line_pool = self.pool.get('hr.loan.line')
                loan_pool = self.pool.get('hr.loan')
                payslip = self.pool.get('hr.payslip')
                loan_line_ids = loan_line_pool.search(cr, uid, [('loan_id.state', '=', 'approve'),
                                                                ('employee_id', '=', contract.employee_id.id),
                                                                ('paid_date', '>=', date_from),
                                                                ('paid_date', '<=', date_to)])

                for line in loan_line_pool.browse(cr, uid, loan_line_ids):
                    if not line.paid:
                        self.pool.get('hr.loan.line').write(cr, uid, line.id, {'paid': True})
                #20AG2015: Modificación Ingresos FIJOS
                income_f_ids = income_obj.search(cr,uid,[('employee_id','=', contract.employee_id.id),('fijo','=',True)])
                print "income_f_ids: ", income_f_ids
                for income_f in income_obj.browse(cr, uid, income_f_ids):
                    input = {
                        'name': income_f.adm_id.name,
                        'code': income_f.adm_id.code,
                        'amount': income_f.value,
                        'contract_id': contract.id,
                        'income_id':income_f.id,
                    }
                    res += [input]
                    income_obj.write(cr, uid, income_f.id, {"state":'procesado'})

                # Egresos
                expense_obj = self.pool.get('hr.expense')
                expense_ids = expense_obj.search(cr,uid,[('employee_id','=', contract.employee_id.id),('date','<=', date_to),('date','>=', date_from),('fijo','=',False)])
                for expense in expense_obj.browse(cr,uid,expense_ids):
                    output = {
                        'name': expense.expense_type_id.name,
                        'code': expense.expense_type_id.code,
                        'amount': expense.value,
                        'contract_id': contract.id,
                        'expense_id':expense.id,

                    }
                    res += [output]
                    expense_obj.write(cr, uid, expense.id, {"state":'procesado'})

                #GH20AG2015: Modificación Egresos FIJOS
                expense_f_ids = expense_obj.search(cr,uid,[('employee_id','=', contract.employee_id.id),('fijo','=',True)])
                for expense in expense_obj.browse(cr,uid,expense_f_ids):
                    output = {
                        'name': expense.expense_type_id.name,
                        'code': expense.expense_type_id.code,
                        'amount': expense.value,
                        'contract_id': contract.id,
                    }
                    res += [output]
                    expense_obj.write(cr, uid, expense.id, {"state":'procesado'})

                # Quincena
                egreso_obj = self.pool.get('hr.expense.type')
                egreso_ids = egreso_obj.search(cr,uid,[('code','=','EGRANTQA')])
                if egreso_ids:
                    egreso_ids = egreso_obj.search(cr,uid,[('code','=','EGRANTQA')])[0]
                    egreso_quincena = egreso_obj.browse(cr,uid,egreso_ids)
                    print "egreso_quincena: ", egreso_quincena

                    payslip_obj = self.pool.get('hr.payslip')
                    payslip_ids = payslip_obj.search(cr,uid,[('employee_id','=', contract.employee_id.id),('date_from','=', date_from),('type','=', 'quincena')])
                    print "QUINCENA IDS: ", payslip_ids
                    for quincena in payslip_obj.browse(cr,uid,payslip_ids):
                        for line in quincena.line_ids:
                            if line.code == 'INGANTQUI':
                                output = {
                                    'name': egreso_quincena.name,
                                    'code': egreso_quincena.code,
                                    'amount': line.amount,
                                    'contract_id': contract.id,
                                }
                                res += [output]

        return res

    def get_worked_day_lines(self, cr, uid, contract_ids, date_from, date_to, context=None):
        """
        @param contract_ids: list of contract id
        @return: returns a list of dict containing the input that should be applied for the given contract between date_from and date_to
        """
        def was_on_leave(employee_id, datetime_day, context=None):
            res = False
            day = datetime_day.strftime("%Y-%m-%d")
            holiday_ids = self.pool.get('hr.holidays').search(cr, uid, [('state', '=', 'validate'), ('employee_id','=',employee_id),('type','=','remove'),('date_from','<=',day),('date_to','>=',day)])
            if holiday_ids:
                res = self.pool.get('hr.holidays').browse(cr, uid, holiday_ids, context=context)[0].holiday_status_id.name
            return res


        res = []
        holi_pool = self.pool.get('hr.holidays')
        for contract in self.pool.get('hr.contract').browse(cr, uid, contract_ids, context=context):
            if not contract.working_hours:
                #fill only if the contract as a working schedule linked
                continue
            attendances = {
                'name': _("Normal Working Days paid at 100%"),
                'sequence': 1,
                'code': 'WORK100',
                'number_of_days': 0.0,
                'number_of_hours': 0.0,
                'contract_id': contract.id,
            }
            # Para los dias Reales de Trabajo: Alimentacion
            dias_reales = {
                'name': ("Dias reales de trabajo"),
                'sequence': 5,
                'code': 'BA',
                'number_of_days': 0.0,
                'number_of_hours': 0.0,
                'contract_id': contract.id,
            }
            leaves = {}
            mes_periodo = date_from.split('-')[1]
            anio_periodo = date_from.split('-')[0]
            mes_contrato = contract.date_start.split('-')[1]
            dias_contrato = contract.date_start.split('-')[2]
            anio_contrato = contract.date_start.split('-')[0]
            day_from = datetime.strptime(date_from,"%Y-%m-%d")
            day_to = datetime.strptime(date_to,"%Y-%m-%d")
            dias_aux_enfer = 0
            v_working_hours_on_day = 0
            band_parcial = 0
            band_falta = 0
            dias_mes = 30
            diff = 0

            dias_mes_real = 30 if ((day_to - day_from).days + 1) > 30 else ((day_to - day_from).days + 1)

            if anio_periodo == anio_contrato and mes_periodo == mes_contrato and int(dias_contrato) > 1:
                nb_of_days_p = (day_to - day_from).days + 1
                if nb_of_days_p > 30:
                    band_parcial = 1
                day_from = datetime.strptime(contract.date_start, "%Y-%m-%d")

            if contract.employee_id.state_emp == 'sold_out':
                day_to = datetime.strptime(contract.date_end, "%Y-%m-%d")

            nb_of_days = 30 if ((day_to - day_from).days + 1) > 30 else ((day_to - day_from).days + 1)
            dias_mes = nb_of_days
            if nb_of_days <= 0:
                continue

            if band_parcial == 1:
                if contract.employee_id.state_emp == 'active':
                    if int(dias_contrato) == 31:
                        nb_of_days = nb_of_days
                    else:
                        nb_of_days -= 1
                elif contract.employee_id.state_emp == 'sold_out':
                    if int(dias_contrato) == 31:
                        nb_of_days = nb_of_days
                    print "aaa: ", contract.date_end.split('-')[2]
                    if contract.date_end.split('-')[2] == '31':
                        nb_of_days = nb_of_days -1


            affliction_pool = self.pool.get('hr.holidays')
            affliction_ids = affliction_pool.search(cr, uid, [('employee_id', '=', contract.employee_id.id),
                                                              ('holiday_status_id.name', '=', 'ENFERMEDAD'),
                                                              ('date_to', '>=', date_from), ('date_from', '<=', date_to ), ('state','=','validate')])
            if affliction_ids:
                for afliction_id in affliction_ids:
                    affliction = affliction_pool.browse(cr, uid, afliction_id)
                    date_from_a = parser.parse(date_from)
                    date_from_b = parser.parse(affliction.date_from)
                    if date_from_a < date_from_b:
                        date_from_a = date_from_a + relativedelta(months=1)
                        days = date_from_a - date_from_b
                        diff = days.days.real
                        if diff > 2:
                            if affliction.number_of_days_temp > 3:
                                diff = 0
                            else:
                                diff = 3
                        elif diff == 2:
                            if affliction.number_of_days_temp > 3:
                                diff = 1
                            else:
                                diff = 3
                        elif diff == 1:
                            if affliction.number_of_days_temp > 3:
                                diff = 2
                            else:
                                diff = 3
                        elif diff == 0:
                            if affliction.number_of_days_temp > 3:
                                diff = 3

                    else:
                        days = date_from_a - date_from_b
                        diff = days.days.real
                        if diff == 3 and date_from_b.month.real < date_from_a.month.real:
                            date_before = date_from_a - timedelta(days=30)
                            if MONTHS[date_before.month.real] == 31:
                                diff -= 1
                    # print 'days:', days.days.real
                    # dias_aux_enfer = days.days.real
                    # if (3 - (days.days.real+1)) > 0:
                    for_paid = {
                        'name': "Días pendientes de pago a mayor %",
                        'sequence': 1,
                        'code': 'MAYPOR',
                        'number_of_days': (3-diff),
                        'number_of_hours': (3-diff) * contract.horas_x_dia,
                        'contract_id': contract.id,
                    }

                    # if days.days.real == 0:
                    #     for_paid = {
                    #         'name': "Días pendientes de pago a mayor %",
                    #         'sequence': 1,
                    #         'code': 'MAYPOR',
                    #         'number_of_days': 3,
                    #         'number_of_hours': 3 * contract.horas_x_dia,
                    #         'contract_id': contract.id,
                    #     }
                    if 3 >= for_paid['number_of_days'] >= 0:
                        diff = for_paid['number_of_days']
                    elif for_paid['number_of_days'] < 0:
                        diff = 0
                    if diff > 0:
                        res.append(for_paid)
            if len(res) > 1:
                number_of_days = 0
                number_of_hours = 0
                for dictio in res:
                    number_of_days += dictio['number_of_days']
                    number_of_hours+= dictio['number_of_hours']
                for_paid = {
                    'name': "Días pendientes de pago a mayor %",
                    'sequence': 1,
                    'code': 'MAYPOR',
                    'number_of_days': number_of_days,
                    'number_of_hours': number_of_hours,
                    'contract_id': contract.id,
                }
                res = []
                diff = for_paid['number_of_days']
                res.append(for_paid)


            working_hours_on_day = 0
            for day in range(0, nb_of_days):
                working_hours_on_day = self.pool.get('resource.calendar').working_hours_on_day(cr, uid, contract.working_hours, day_from + timedelta(days=day), context)
                leave_type = was_on_leave(contract.employee_id.id, day_from + timedelta(days=day), context=context)
                if leave_type in ('ENFERMEDAD','MATERNIDAD','FALTA',"PATERNIDAD","CALAMIDAD","LICENCIA SIN REMUNERACION MAT/PAT"):
                    # band_falta = 1
                    if leave_type == 'ENFERMEDAD':
                        dias_aux_enfer += 1.0
                        v_working_hours_on_day = contract.horas_x_dia

                    if leave_type in leaves:
                        if leaves[leave_type]['number_of_days'] < 30:
                            leaves[leave_type]['number_of_days'] += 1.0
                            leaves[leave_type]['number_of_hours'] += contract.horas_x_dia
                    else:
                        leaves[leave_type] = {
                            'name': leave_type,
                            'sequence': 5,
                            'code': leave_type,
                            'number_of_days': 1.0,
                            'number_of_hours': contract.horas_x_dia,
                            'contract_id': contract.id,
                        }
                else:
                    if attendances['number_of_days'] < 30:
                        attendances['number_of_days'] += 1.0
                        attendances['number_of_hours'] += contract.horas_x_dia
                    if working_hours_on_day:
                        if not self.pool.get('hr.holidays.public').is_public_holiday(cr, uid, day_from + timedelta(days=day), None, None):
                            if not leave_type:
                                dias_reales['number_of_days'] += 1.0
                                dias_reales['number_of_hours'] += contract.horas_x_dia

            if mes_periodo == '02':
                if contract.employee_id.state_emp == 'active':
                    if dias_mes_real == 28:
                        nb_of_days += 2
                        if (leaves.get('MATERNIDAD') and (leaves['MATERNIDAD']['number_of_days'] == 28)):
                            leaves['MATERNIDAD']['number_of_days'] = leaves['MATERNIDAD']['number_of_days'] + 2
                            leaves['MATERNIDAD']['number_of_hours'] = leaves['MATERNIDAD']['number_of_hours'] + (2 * contract.horas_x_dia)
                        elif (leaves.get('ENFERMEDAD') and leaves['ENFERMEDAD']['number_of_days'] == 28):
                            leaves['ENFERMEDAD']['number_of_days'] = leaves['ENFERMEDAD']['number_of_days'] + 2
                            leaves['ENFERMEDAD']['number_of_hours'] = leaves['ENFERMEDAD']['number_of_hours'] + (2 * contract.horas_x_dia)
                            dias_aux_enfer = dias_aux_enfer + 2
                        else:
                            attendances['number_of_days'] = attendances['number_of_days'] + 2
                            attendances['number_of_hours'] = (attendances['number_of_days'] + 2 )* v_working_hours_on_day
                    elif dias_mes_real == 29:
                        nb_of_days += 1
                        if (leaves.get('MATERNIDAD') and leaves['MATERNIDAD']['number_of_days'] == 29):
                            leaves['MATERNIDAD']['number_of_days'] = leaves['MATERNIDAD']['number_of_days'] + 1
                            leaves['MATERNIDAD']['number_of_hours'] = leaves['MATERNIDAD']['number_of_hours'] + (1 * contract.horas_x_dia)
                        elif (leaves.get('ENFERMEDAD') and (leaves['ENFERMEDAD']['number_of_days'] == 29)):
                            leaves['ENFERMEDAD']['number_of_days'] = leaves['ENFERMEDAD']['number_of_days'] + 1
                            leaves['ENFERMEDAD']['number_of_hours'] = leaves['ENFERMEDAD']['number_of_hours'] + (1 * contract.horas_x_dia)
                            dias_aux_enfer = dias_aux_enfer + 1
                        else:
                            attendances['number_of_days'] = attendances['number_of_days'] + 1
                            attendances['number_of_hours'] = (attendances['number_of_days'] + 1 )* v_working_hours_on_day
                if contract.employee_id.state_emp == 'sold_out':
                    if dias_mes_real == 28 and nb_of_days ==28:
                        attendances['number_of_days'] = 30
                        attendances['number_of_hours'] = 30 * contract.horas_x_dia
                        nb_of_days = 30
                    if dias_mes_real == 29 and nb_of_days ==29:
                        attendances['number_of_days'] = 30
                        attendances['number_of_hours'] = 30 * contract.horas_x_dia
                        nb_of_days = 30





            print "nb_of_days: ", nb_of_days

            if leaves.get('ENFERMEDAD'):
                leaves['ENFERMEDAD']['number_of_days'] = dias_aux_enfer - diff
                leaves['ENFERMEDAD']['number_of_hours'] = (dias_aux_enfer - diff) * contract.horas_x_dia

            # GH051115: Para pagar faltas sobre 30 dias
            if leaves.get('FALTA'):
                if (attendances['number_of_days'] + leaves['FALTA']['number_of_days'] > 30):
                    diferencia_f = 30 - leaves['FALTA']['number_of_days']
                    attendances['number_of_days'] = diferencia_f
                    attendances['number_of_hours'] = diferencia_f * contract.horas_x_dia

            if dias_aux_enfer <=3 and dias_aux_enfer > 0:
                attendances['number_of_days'] = attendances['number_of_days']
                attendances['number_of_hours'] = attendances['number_of_days'] * v_working_hours_on_day

            if dias_aux_enfer > 3:
                print "Enfermedad > 3: ", attendances['number_of_days']
                print "dias_aux_enfer: ", dias_aux_enfer
                # VERIFICAR
                #                 if attendances['number_of_days'] + dias_aux_enfer > 30:
                #                     attendances['number_of_days'] = attendances['number_of_days'] -1

                print "FINAL: ", attendances['number_of_days']
                # attendances['number_of_days'] = attendances['number_of_days'] + 3
                # attendances['number_of_hours'] = attendances['number_of_days'] * v_working_hours_on_day
            for a_id in affliction_ids:
                affliction = affliction_pool.browse(cr, uid, a_id)
                if affliction.number_of_days_temp <= 3:
                    attendances['number_of_days'] = attendances['number_of_days'] + affliction.number_of_days_temp
                    attendances['number_of_hours'] = attendances['number_of_days'] * v_working_hours_on_day
                    leaves['ENFERMEDAD']['number_of_days'] -= affliction.number_of_days_temp
                    leaves['ENFERMEDAD']['number_of_hours'] = leaves['ENFERMEDAD']['number_of_days'] * contract.horas_x_dia

            if attendances['number_of_days'] > 30:
                attendances['number_of_days'] = 30
                attendances['number_of_hours'] = 30 * contract.horas_x_dia

            # Para controlar las faltas en meses de 31 dias
            # if band_falta ==1 and dias_mes > 30:
            #     attendances['number_of_days'] = attendances['number_of_days'] - 1
            #     attendances['number_of_hours'] = attendances['number_of_days'] * v_working_hours_on_day
            leaves = [value for key,value in leaves.items()]
            #for item in leaves:
            #    if item['code'] == 'ENFERMEDAD' and item['number_of_days'] == 0.0:
            #        leaves.remove(item)
            res += [attendances] + leaves + [dias_reales]

        return res

    def unlink(self, cr, uid, ids, context=None):
        if not context:
            context = {}
        unlink_ids = []
        for payslips_line in self.browse(cr, uid, ids, context):
            if payslips_line.state != 'draft':
                raise osv.except_osv(_('Invalid action !'), _('Cannot delete delivery payslip(s) that are already Done. Change its to draft state !'))
            else:
                loan_line_pool = self.pool.get('hr.loan.line')
                loan_line_ids = loan_line_pool.search(cr, uid, [('loan_id.state', '=', 'approve'),
                                                                ('employee_id', '=', payslips_line.employee_id.id),
                                                                ('paid_date', '>=', payslips_line.date_from),
                                                                ('paid_date', '<=', payslips_line.date_to),
                                                                ('paid', '=', True)])
                if payslips_line.type == 'liquidation':
                    detail_pool = self.pool.get('detail.liquidation.history')
                    detail_ids = detail_pool.search(cr, uid, [('employee_id', '=', payslips_line.employee_id.id), ('role_id', '=', payslips_line.payslip_run_id.id)])
                    if detail_ids:
                        detail_pool.unlink(cr, uid, detail_ids)
                for line in loan_line_pool.browse(cr, uid, loan_line_ids):
                    if line.paid:
                        self.pool.get('hr.loan.line').write(cr, uid, line.id, {'paid': False})
                for input_line in payslips_line.input_line_ids:
                    if input_line.income_id:
                        self.pool.get('hr.income').write(cr, uid, input_line.income_id.id, {'state':'draft'})
                    elif input_line.expense_id:
                        self.pool.get('hr.expense').write(cr, uid, input_line.expense_id.id, {'state':'draft'})
                cr.execute('''delete from hr_payslip_input where payslip_id=%s''' %(payslips_line.id))

        return super(hr_payslip, self).unlink(cr, uid, ids)

    def _compute_year(self, cr, uid, ids, field, arg, context=None):
        print "** _compute_year **"
        ''' Función que calcula el número de años de servicio de un empleado trabajando para la empresa.'''

        res = {}
        DATETIME_FORMAT = "%Y-%m-%d"
        #today = datetime.now()

        for payslip in self.browse(cr, uid, ids, context=context):
            if payslip.date_to and payslip.contract_id.date_start:
                date_start = datetime.strptime(payslip.contract_id.date_start, DATETIME_FORMAT)
                today=datetime.strptime(payslip.date_to, DATETIME_FORMAT)
                diffyears = today.year - date_start.year
                difference = today - date_start.replace(today.year)
                days_in_year = calendar.isleap(today.year) and 366 or 365
                difference_in_years = diffyears + (difference.days + difference.seconds / 86400.0) / days_in_year
                total_years = relativedelta(today, date_start).years
                total_months = relativedelta(today, date_start).months
                months_in_years = total_months*0.083333333
                year_month = float(total_months) / 100 + total_years
                number_of_year = total_years + months_in_years
                res[payslip.id] = number_of_year
            else:
                res[payslip.id] = 0.0
        return res

    def _calcular_anios(self, cr, uid, ids, field, arg, context=None):
        ''' Función que calcula el número de años de servicio de un empleado trabajando para la empresa.'''
        DATETIME_FORMAT = "%Y-%m-%d"
        res = {}
        number_of_year = 0
        control_pool = self.pool.get('change.control')
        first_date = False
        second_date = False
        for payslip in self.browse(cr, uid, ids, context=context):
            number_of_year = 0
            control_ids1 = control_pool.search(cr, uid, [('contract_id', '=', payslip.contract_id.id), ('change', '=', 'reint')])
            if control_ids1:
                control_ids = control_pool.search(cr, uid, [('contract_id', '=', payslip.contract_id.id), ('change', 'in', ('init', 'liq', 'reint'))],
                                                  order='change_date')
                for control in control_pool.browse(cr, uid, control_ids):
                    if control.change in ['init', 'reint']:
                        first_date = control.change_date
                    else:
                        second_date = control.change_date
                    if second_date and first_date:
                        contract_date_end = ''
                        employee_state = payslip.employee_id.state_emp
                        if employee_state == 'sold_out':
                            contract_date_end = datetime.strptime(payslip.contract_id.date_end, DATETIME_FORMAT)
                        number_of_year += total_anios_laborados(datetime.strptime(first_date, DATETIME_FORMAT), datetime.strptime(second_date, DATETIME_FORMAT), employee_state, contract_date_end)
                        first_date = False
                        second_date = False
            if payslip.contract_id.date_start:
                contract_date_end = ''
                employee_state = payslip.employee_id.state_emp
                contract_date_start = datetime.strptime(payslip.contract_id.date_start, DATETIME_FORMAT)
                if employee_state == 'sold_out':
                    contract_date_end = datetime.strptime(payslip.contract_id.date_end, DATETIME_FORMAT)
                payslip_day_to = datetime.strptime(payslip.date_to, DATETIME_FORMAT)
                number_of_year += total_anios_laborados(contract_date_start, payslip_day_to, employee_state, contract_date_end)
                res[payslip.id] = number_of_year
            else:
                res[payslip.id] = 0.0

        return res

    def get_payslip_lines(self, cr, uid, contract_ids, payslip_id, context):
        def _sum_salary_rule_category(localdict, category, amount):
            if category.parent_id:
                localdict = _sum_salary_rule_category(localdict, category.parent_id, amount)
            localdict['categories'].dict[category.code] = category.code in localdict['categories'].dict and localdict['categories'].dict[category.code] + amount or amount
            return localdict

        class BrowsableObject(object):
            def __init__(self, pool, cr, uid, employee_id, dict):
                self.pool = pool
                self.cr = cr
                self.uid = uid
                self.employee_id = employee_id
                self.dict = dict

            def __getattr__(self, attr):
                return attr in self.dict and self.dict.__getitem__(attr) or 0.0

        class InputLine(BrowsableObject):
            """a class that will be used into the python code, mainly for usability purposes"""
            def sum(self, code, from_date, to_date=None):
                if to_date is None:
                    to_date = datetime.now().strftime('%Y-%m-%d')
                result = 0.0
                self.cr.execute("SELECT sum(amount) as sum\
                            FROM hr_payslip as hp, hr_payslip_input as pi \
                            WHERE hp.employee_id = %s AND hp.state = 'done' \
                            AND hp.date_from >= %s AND hp.date_to <= %s AND hp.id = pi.payslip_id AND pi.code = %s",
                                (self.employee_id, from_date, to_date, code))
                res = self.cr.fetchone()[0]
                return res or 0.0

        class WorkedDays(BrowsableObject):
            """a class that will be used into the python code, mainly for usability purposes"""
            def _sum(self, code, from_date, to_date=None):
                if to_date is None:
                    to_date = datetime.now().strftime('%Y-%m-%d')
                result = 0.0
                self.cr.execute("SELECT sum(number_of_days) as number_of_days, sum(number_of_hours) as number_of_hours\
                            FROM hr_payslip as hp, hr_payslip_worked_days as pi \
                            WHERE hp.employee_id = %s AND hp.state = 'done'\
                            AND hp.date_from >= %s AND hp.date_to <= %s AND hp.id = pi.payslip_id AND pi.code = %s",
                                (self.employee_id, from_date, to_date, code))
                return self.cr.fetchone()

            def sum(self, code, from_date, to_date=None):
                res = self._sum(code, from_date, to_date)
                return res and res[0] or 0.0

            def sum_hours(self, code, from_date, to_date=None):
                res = self._sum(code, from_date, to_date)
                return res and res[1] or 0.0

        class Payslips(BrowsableObject):
            """a class that will be used into the python code, mainly for usability purposes"""

            def sum(self, code, from_date, to_date=None):
                if to_date is None:
                    to_date = datetime.now().strftime('%Y-%m-%d')
                self.cr.execute("SELECT sum(case when hp.credit_note = False then (pl.total) else (-pl.total) end)\
                            FROM hr_payslip as hp, hr_payslip_line as pl \
                            WHERE hp.employee_id = %s AND hp.state = 'done' \
                            AND hp.date_from >= %s AND hp.date_to <= %s AND hp.id = pl.slip_id AND pl.code = %s",
                                (self.employee_id, from_date, to_date, code))
                res = self.cr.fetchone()
                return res and res[0] or 0.0

        #we keep a dict with the result because a value can be overwritten by another rule with the same code
        result_dict = {}
        rules = {}
        categories_dict = {}
        blacklist = []
        payslip_obj = self.pool.get('hr.payslip')
        inputs_obj = self.pool.get('hr.payslip.worked_days')
        obj_rule = self.pool.get('hr.salary.rule')
        payslip = payslip_obj.browse(cr, uid, payslip_id, context=context)
        worked_days = {}
        for worked_days_line in payslip.worked_days_line_ids:
            worked_days[worked_days_line.code] = worked_days_line
        inputs = {}
        for input_line in payslip.input_line_ids:
            inputs[input_line.code] = input_line

        categories_obj = BrowsableObject(self.pool, cr, uid, payslip.employee_id.id, categories_dict)
        input_obj = InputLine(self.pool, cr, uid, payslip.employee_id.id, inputs)
        worked_days_obj = WorkedDays(self.pool, cr, uid, payslip.employee_id.id, worked_days)
        payslip_obj = Payslips(self.pool, cr, uid, payslip.employee_id.id, payslip)
        rules_obj = BrowsableObject(self.pool, cr, uid, payslip.employee_id.id, rules)

        baselocaldict = {'categories': categories_obj, 'rules': rules_obj, 'payslip': payslip_obj, 'worked_days': worked_days_obj, 'inputs': input_obj}
        #get the ids of the structures on the contracts and their parent id as well
        # BITGH: 14 Julio 2015: Para procesar structura del Payroll
        #structure_ids = self.pool.get('hr.contract').get_all_structures(cr, uid, contract_ids, context=context)
        structure_ids = payslip.struct_id.id
        #get the rules of the structure and thier children
        rule_ids = self.pool.get('hr.payroll.structure').get_all_rules(cr, uid, structure_ids, context=context)
        #run the rules by sequence
        sorted_rule_ids = [id for id, sequence in sorted(rule_ids, key=lambda x:x[1])]

        for contract in self.pool.get('hr.contract').browse(cr, uid, contract_ids, context=context):
            employee = contract.employee_id
            localdict = dict(baselocaldict, employee=employee, contract=contract)
            for rule in obj_rule.browse(cr, uid, sorted_rule_ids, context=context):
                key = rule.code + '-' + str(contract.id)
                localdict['result'] = None
                localdict['result_qty'] = 1.0
                localdict['result_rate'] = 100
                #check if the rule can be applied
                if obj_rule.satisfy_condition(cr, uid, rule.id, localdict, context=context) and rule.id not in blacklist:
                    #compute the amount of the rule
                    amount, qty, rate = obj_rule.compute_rule(cr, uid, rule.id, localdict, context=context)
                    #check if there is already a rule computed with that code
                    previous_amount = rule.code in localdict and localdict[rule.code] or 0.0
                    #set/overwrite the amount computed for this rule in the localdict
                    # if rule.code != 'D3LIQUD':
                    tot_rule = amount * qty * rate / 100.0
                    # else:
                    #     tot_rule = amount * qty * rate
                    #     amount /= 100
                    localdict[rule.code] = tot_rule
                    rules[rule.code] = rule
                    #sum the amount for its salary category
                    localdict = _sum_salary_rule_category(localdict, rule.category_id, tot_rule - previous_amount)
                    #create/overwrite the rule in the temporary results
                    result_dict[key] = {
                        'salary_rule_id': rule.id,
                        'contract_id': contract.id,
                        'name': rule.name,
                        'code': rule.code,
                        'category_id': rule.category_id.id,
                        'sequence': rule.sequence,
                        'appears_on_payslip': rule.appears_on_payslip,
                        'condition_select': rule.condition_select,
                        'condition_python': rule.condition_python,
                        'condition_range': rule.condition_range,
                        'condition_range_min': rule.condition_range_min,
                        'condition_range_max': rule.condition_range_max,
                        'amount_select': rule.amount_select,
                        'amount_fix': rule.amount_fix,
                        'amount_python_compute': rule.amount_python_compute,
                        'amount_percentage': rule.amount_percentage,
                        'amount_percentage_base': rule.amount_percentage_base,
                        'register_id': rule.register_id.id,
                        'amount': amount,
                        'employee_id': contract.employee_id.id,
                        'quantity': qty,
                        'rate': rate,
                    }
                else:
                    #blacklist this rule and its children
                    blacklist += [id for id, seq in self.pool.get('hr.salary.rule')._recursive_search_of_rules(cr, uid, [rule], context=context)]

        result = [value for code, value in result_dict.items()]
        return result


    def compute_sheet(self, cr, uid, ids, context=None):
        slip_line_pool = self.pool.get('hr.payslip.line')
        sequence_obj = self.pool.get('ir.sequence')

        for payslip in self.browse(cr, uid, ids, context=context):
            number = payslip.number or sequence_obj.get(cr, uid, 'salary.slip')
            #delete old payslip lines
            old_slipline_ids = slip_line_pool.search(cr, uid, [('slip_id', '=', payslip.id)], context=context)
            #            old_slipline_ids
            if old_slipline_ids:
                slip_line_pool.unlink(cr, uid, old_slipline_ids, context=context)
            if payslip.contract_id:
                #set the list of contract for which the rules have to be applied
                contract_ids = [payslip.contract_id.id]
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
                                               'business_unit_id':payslip.employee_id.business_unit_id.id}, context=context)
        return True

    def create(self, cr, uid, vals, context=None):
        if context is None:
            context = {}
        if 'journal_id' in context:
            vals.update({'journal_id': context.get('journal_id')})
        return super(hr_payslip, self).create(cr, uid, vals, context=context)

    def _get_type(self, cr, uid, context=None):
        if context is None:
            context = {}
        type = context.get('type', 'quincena')
        return type

    _columns={

        #               'number_of_year': fields.function(_compute_year, string='No. of years of service', type='float', store=False, method=True, help='Total years of work experience'),
        'anios_trabajados': fields.function(_calcular_anios, string='Años Trabajados', type='float', store=False, method=True, help='Total years of work experience'),
        'department_id': fields.many2one('hr.department', 'Department'),
        'type': fields.selection([
            ('rol','Rol'),
            ('quincena', 'Quincena'),
            ('liquidation', 'Liquidación'),
        ],'Tipo', select=True),
        'provincia_id':fields.many2one('res.country.state','Provincia'),
        'region': fields.char('Region')
    }

    _defaults = {
        'type': lambda *a: 'rol',
        'type': _get_type,
    }

    # _sql_constraints = [
    #     ('payslip_uniq', 'unique (employee_id,date_from,type)', 'Solo se puede generar un Rol/Quincena por período !')
    # ]

    def _check_slip_company(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0], context=context)
        exist = self.search(cr, uid, [('company_id', '=', obj.company_id.id), ('type', '=', obj.type),
                                      ('employee_id', '=', obj.employee_id.id), ('date_from', '=', obj.date_from),
                                      ('id', '!=', obj.id)])
        if exist:
            return False
        return True

    _constraints = [
        (_check_slip_company, 'Solo se puede generar un tipo de rol por período para cada empleado! ', ['type']),
    ]

    # def onchange_employee_id(self, cr, uid, ids, date_from, date_to, employee_id=False, contract_id=False, context=None):
    #     res = super(hr_payslip, self).onchange_employee_id(cr, uid, ids, date_from, date_to, employee_id, contract_id, context)
    #     employee = self.pool.get('hr.employee').browse(cr, uid, employee_id)
    #     res['value'].update({'region': employee.region})
    #     return res

    def create(self, cr, uid, values, context=None):
        if 'employee_id' in values:
            employee = self.pool.get('hr.employee').browse(cr, uid, values['employee_id'])
            values.update({'region': employee.region})
        return super(hr_payslip, self).create(cr, uid, values, context)

    def work_years_function(self, cr, uid, slip):
        ''' Función que calcula el número de años de servicio de un empleado trabajando para la empresa.'''
        DATETIME_FORMAT = "%Y-%m-%d"
        res = {}
        number_of_year = 0
        control_pool = self.pool.get('change.control')
        first_date = False
        second_date = False
        for payslip in self.browse(cr, uid, [slip]):
            control_ids1 = control_pool.search(cr, uid, [('contract_id', '=', payslip.contract_id.id), ('change', '=', 'reint')])
            if control_ids1:
                control_ids = control_pool.search(cr, uid, [('contract_id', '=', payslip.contract_id.id), ('change', 'in', ('init', 'liq', 'reint'))],
                                                  order='change_date')
                for control in control_pool.browse(cr, uid, control_ids):
                    if control.change in ['init', 'reint']:
                        first_date = control.change_date
                    else:
                        second_date = control.change_date
                    if second_date and first_date:
                        number_of_year += work_years(datetime.strptime(first_date, DATETIME_FORMAT), datetime.strptime(second_date, DATETIME_FORMAT))
                        first_date = False
                        second_date = False
            if payslip.contract_id.date_start:
                contract_date_start = datetime.strptime(payslip.contract_id.date_start, DATETIME_FORMAT)
                payslip_day_to = datetime.strptime(payslip.date_to, DATETIME_FORMAT)
                number_of_year = work_years(contract_date_start, payslip_day_to)
        return number_of_year

hr_payslip()

class hr_payslip_line(osv.osv):
    _inherit = 'hr.payslip.line'

    _columns = {
        'department_id': fields.many2one('hr.department', 'Department'),
    }

    def create(self, cr, uid, values, context=None):
        if 'slip_id' in values:
            slip = self.pool.get('hr.payslip').browse(cr, uid, values['slip_id'], context)
            values.update({'company_id': slip.company_id.id})
        return super(hr_payslip_line, self).create(cr, uid, values, context)

hr_payslip_line()


class hr_salary_rule(osv.osv):
    _inherit = 'hr.salary.rule'

    def get_current_fiscalyear(self, cr, uid, context=None):
        fiscalyear_ids = self.pool.get('account.fiscalyear').search(cr, uid, [('state', '=', 'draft')],
                                                                    order='date_start')
        fiscalyear_ids.reverse()
        return fiscalyear_ids[0]

    _columns={
        'order': fields.integer('Order'),
        'amount_percentage_base':fields.many2one('hr.salary.rule.percentage.base','Percentage based on', required=False, readonly=False, help='result will be affected to a variable'),
        'partner_id':fields.many2one('res.partner', 'Registro de Contribucion',
                                     help="Eventual third party involved in the salary payment of the employees.",
                                     domain="[('is_employee', '=', False)]")
    }

    def compute_rule(self, cr, uid, rule_id, localdict, context=None):
        obj = self.browse(cr, uid, rule_id)
        if obj.code == 'D3LIQUD':
            return self.third_liquidation(cr, uid, localdict, context), 1, 100
        elif obj.code == 'D4LIQUD':
            return self.four_liquidation(cr, uid, localdict, context), 1, 100
        elif obj.code == 'VALIQUD':
            return self.vacation_liquidation(cr, uid, localdict, context), 1, 100

        return super(hr_salary_rule, self).compute_rule(cr, uid, rule_id, localdict, context=None)

    def get_last_vacation(self, holiday_list):
        date_compare = holiday_list[0].date_from
        for holiday in holiday_list:
            if date_compare and date_compare < holiday.date_from:
                date_compare = holiday.date_from
        return date_compare

    def vacation_liquidation(self, cr, uid, localdict, context):
        context = context or {}
        amount = 0.00
        liquid_pool = self.pool.get('hr.employee.liquidation')
        detail_liquidation_pool = self.pool.get('detail.liquidation.history')
        employee = localdict['employee']
        payslip_run = self.pool.get('hr.payslip.run').browse(cr, uid, context.get('active_id'), context=None)
        liquid_id = liquid_pool.search(cr, uid, [('employee_id', '=', employee.id)])[0]
        liquid = liquid_pool.browse(cr, uid, liquid_id)
        slip_pool = self.pool.get('hr.payslip')
        period_pool = self.pool.get('account.period')
        # Sumo del campo pendiente por pagar del empleado las provisiones despues de la ultima vacacion cogida, la fecha inicial obtengo mes año, concateno, busco el periodo ese y de alli
        # obtengo todos los slips a partir de ese periodo y sumo PROVAC
        if employee.holidays:
            last_vac = datetime.strptime(self.get_last_vacation(employee.holidays), "%Y-%m-%d")
            date_end_rol = datetime.strptime(payslip_run.date_end, "%Y-%m-%d")
            name_from = '0' + str(last_vac.month) + '/' + str(last_vac.year) if last_vac.month < 10 else str(last_vac.month) + '/' + str(last_vac.year)
            period_from = period_pool.search(cr, uid, [('code', '=', name_from)])
            name_to = '0' + str(date_end_rol.month) + '/' + str(date_end_rol.year) if date_end_rol.month < 10 else str(date_end_rol.month) + '/' + str(date_end_rol.year)
            period_to = period_pool.search(cr, uid, [('code', '=', name_to)])
            if not period_from or not period_to:
                raise osv.except_orm('Error', 'No existen periodos definidos para la liquidacion')
            period_from = period_from[0]
            period_to = period_to[0]
            slip_ids = slip_pool.search(cr, uid, [('employee_id', '=', employee.id), ('period_id', '>=', period_from),
                                                  ('period_id', '<', period_to)])
        else:
            slip_ids = slip_pool.search(cr, uid, [('employee_id', '=', employee.id)])
        for slip in slip_pool.browse(cr, uid, slip_ids):
            for line in slip.details_by_salary_rule_category:
                if line.code == 'PROVAC':
                    amount += line.total
                    res = self.set_detail(line, payslip_run.id, employee.id, slip.date_from, slip.date_to)
                    detail_liquidation_pool.create(cr, uid, res)
        return employee.pending_payment + amount

    def third_liquidation(self, cr, uid, localdict, context=None):
        context = context or {}
        amount = 0.00
        employee = localdict['employee']
        detail_liquidation_pool = self.pool.get('detail.liquidation.history')
        payslip_run = self.pool.get('hr.payslip.run').browse(cr, uid, context.get('active_id'), context=None)
        company_pool = self.pool.get('res.company')
        company_id = company_pool._company_default_get(cr, uid, 'hr.salary.rule', context=None)
        company = company_pool.browse(cr, uid, company_id, context)
        payslip_pool = self.pool.get('hr.payslip')
        acumulate = 0.00
        fch_contrato = False
        acumulate_pool = self.pool.get('hr.acumulados')
        if payslip_run.date_end < company.period_decimo3_pay.date_stop:
            date_stop = parser.parse(company.period_decimo3_pay.date_stop)
            date_from = date_stop - relativedelta(years=1)
            date_from_str = date_from.strftime('%Y-%m-%d')
            payslip_ids = payslip_pool.search(cr, uid, [('employee_id', '=', employee.id),
                                                        ('date_from', '>', date_from_str),
                                                        ('date_to', '<=', payslip_run.date_end)])
            payslips = payslip_pool.browse(cr, uid, payslip_ids, context=None)
            for payslip in payslips:
                fch_contrato = payslip.contract_id.date_start
                for detail in payslip.details_by_salary_rule_category:
                    if detail.code == 'D3':
                        amount += detail.total
                        res = self.set_detail(detail, payslip_run.id, payslip.employee_id.id, payslip.date_from, payslip.date_to)
                        detail_liquidation_pool.create(cr, uid, res)
        if payslip_run.date_end > company.period_decimo3_pay.date_stop:
            payslip_ids = payslip_pool.search(cr, uid, [('employee_id', '=', employee.id),
                                                        ('date_from', '>', company.period_decimo3_pay.date_stop),
                                                        ('date_to', '<=', payslip_run.date_end)])
            payslips = payslip_pool.browse(cr, uid, payslip_ids, context=None)
            for payslip in payslips:
                fch_contrato = payslip.contract_id.date_start
                for detail in payslip.details_by_salary_rule_category:
                    if detail.code == 'D3':
                        amount += detail.total
                        res = self.set_detail(detail, payslip_run.id, payslip.employee_id.id, payslip.date_from, payslip.date_to)
                        detail_liquidation_pool.create(cr, uid, res)
        if payslip_ids:
            acumulate_ids = acumulate_pool.search(cr, uid, [('employee_id', '=', employee.id), ('fch_contrato', '=', fch_contrato)])
            if acumulate_ids:
                for acumulate_obj in acumulate_pool.browse(cr, uid, acumulate_ids):
                    for line in acumulate_obj.acumulados_line:
                        detail_liquidation_pool.create(cr, uid, {
                            'name': 'D3',
                            'date_from': line.inicio_mes.date_start,
                            'date_to': line.inicio_mes.date_stop,
                            'amount': line.decimo3,
                            'employee_id': employee.id,
                            'role_id': payslip_run.id
                        })
                        acumulate += line.decimo3
        amount += acumulate
        return amount

    def four_liquidation(self, cr, uid, localdict, context=None):
        context = context or {}
        if not len(context):
            context = dict(context)
            context['active_id'] = localdict['payslip'].payslip_run_id.id
        amount = 0.00
        employee = localdict['employee']
        acumulate_pool = self.pool.get('hr.acumulados')
        detail_liquidation_pool = self.pool.get('detail.liquidation.history')
        contract_pool = self.pool.get('hr.contract')
        contract_ids = contract_pool.search(cr, uid, [('employee_id', '=', employee.id)])
        contract_id = contract_ids[0]
        contract = contract_pool.browse(cr, uid, contract_id)
        remuneration_pool = self.pool.get('hr.remuneration.employee')
        payslip_run = self.pool.get('hr.payslip.run').browse(cr, uid, context.get('active_id'), context=None)
        company_pool = self.pool.get('res.company')
        company_id = company_pool._company_default_get(cr, uid, 'hr.salary.rule', context=None)
        company = company_pool.browse(cr, uid, company_id, context)
        payslip_pool = self.pool.get('hr.payslip')
        employee_liq_pool = self.pool.get('hr.employee.liquidation')
        emp_liq_id = employee_liq_pool.search(cr, uid, [('employee_id', '=', employee.id)])[0]
        emp_liq = employee_liq_pool.browse(cr, uid, emp_liq_id)
        dc4_last_days = parser.parse(payslip_run.date_end) - parser.parse(payslip_run.date_start)
        if dc4_last_days.days.real == 0:
            dc4_last_days = relativedelta(days=1)
        if dc4_last_days.days.real >= MONTHS[parser.parse(payslip_run.date_end).month]:
            thirdty_days_months_days = thirdty_days_months(parser.parse(payslip_run.date_start).month, parser.parse(payslip_run.date_end).month)
        else:
            thirdty_days_months_days = 0
        dc4_val = 0.00
        if dc4_last_days:
            if contract.horas_x_dia == 8:
                days = dc4_last_days.days.real + thirdty_days_months_days + 1
            elif contract.horas_x_dia != 8:
                days = (dc4_last_days.days.real + thirdty_days_months_days + 1) * contract.horas_x_dia * 0.125
            dc4_val = days * (company.base_amount / 360.00)
            detail_liquidation_pool.create(cr, uid, {
                'name': 'D4',
                'date_from': payslip_run.date_start,
                'date_to': payslip_run.date_end,
                'amount': round(dc4_val, 2),
                'employee_id': employee.id,
                'role_id': payslip_run.id
            })

        if payslip_run.date_start < company.fecha_fin_sierra:
            acumulate_ids = acumulate_pool.search(cr, uid, [('employee_id', '=', employee.id), ('fch_contrato', '=', contract.date_start)])
            for acum in acumulate_pool.browse(cr, uid, acumulate_ids):
                for line in acum.acumulados_line:
                    if line.decimo4:
                        detail_liquidation_pool.create(cr, uid, {
                            'name': 'D4',
                            'date_from': line.inicio_mes.date_start,
                            'date_to': line.inicio_mes.date_stop,
                            'amount': line.decimo4,
                            'employee_id': employee.id,
                            'role_id': payslip_run.id
                        })
                        amount += line.decimo4

        if employee.region == 'sierra' and (company.region == employee.region or company.region == 'both'):
            if payslip_run.date_start < company.fecha_fin_sierra:
                date_from = company.fecha_init_sierra#(date_stop - relativedelta(years=1)).strftime('%Y-%m-%d')
                date_to = payslip_run.date_start
                if company.fecha_fin_sierra < contract.date_start:
                    date_from = company.fecha_fin_sierra
                payslip_ids = payslip_pool.search(cr, uid, [('employee_id', '=', employee.id),
                                                            ('date_from', '>', date_from),
                                                            ('date_to', '<=', date_to)])
                payslips = payslip_pool.browse(cr, uid, payslip_ids, context=None)
                for payslip in payslips:
                    for detail in payslip.details_by_salary_rule_category:
                        if detail.code == 'D4':
                            amount += detail.total
                            res = self.set_detail(detail, payslip_run.id, payslip.employee_id.id, payslip.date_from, payslip.date_to)
                            detail_liquidation_pool.create(cr, uid, res)
                            # elif payslip_run.date_end > company.fecha_fin_sierra:
                            #     date_from = company.fecha_fin_sierra
                            #     date_to = payslip_run.date_end
                            # amount, ignore = remuneration_pool.tenth_amount_calculate(cr, uid, [], 'dc4', employee.id, date_from, date_to)
            else:
                payslip_ids = payslip_pool.search(cr, uid, [('employee_id', '=', employee.id),
                                                            ('date_from', '>', company.fecha_fin_sierra)])
                payslips = payslip_pool.browse(cr, uid, payslip_ids, context=None)
                for payslip in payslips:
                    for detail in payslip.details_by_salary_rule_category:
                        if detail.code == 'D4':
                            amount += detail.total
                            res = self.set_detail(detail, payslip_run.id, payslip.employee_id.id, payslip.date_from, payslip.date_to)
                            detail_liquidation_pool.create(cr, uid, res)
            return amount + dc4_val
        elif employee.region == 'costa' and (company.region == employee.region or company.region == 'both'):
            if payslip_run.date_start < company.fecha_fin_costa:
                date_from = company.fecha_init_costa
                date_to = payslip_run.date_start
                if (company.fecha_fin_costa >= contract.date_start > company.fecha_init_costa) or (company.fecha_fin_costa < contract.date_start):
                    date_from = contract.date_start
                payslip_ids = payslip_pool.search(cr, uid, [('employee_id', '=', employee.id),
                                                            ('date_from', '>', date_from),
                                                            ('date_to', '<=', date_to)])
                payslips = payslip_pool.browse(cr, uid, payslip_ids, context=None)
                for payslip in payslips:
                    for detail in payslip.details_by_salary_rule_category:
                        if detail.code == 'D4':
                            amount += detail.total
                            res = self.set_detail(detail, payslip_run.id, payslip.employee_id.id, payslip.date_from, payslip.date_to)
                            detail_liquidation_pool.create(cr, uid, res)
                            # if emp_liq.date <= company.fecha_fin_costa:
                            #     date_stop = parser.parse(company.fecha_fin_costa)
                            #     date_from = (date_stop - relativedelta(years=1)).strftime('%Y-%m-%d')
                            #     date_to = emp_liq.date
                            #
                            # elif payslip_run.date_end > company.fecha_fin_costa:
                            #     date_from = company.fecha_fin_costa
                            #     date_to = payslip_run.date_end
                            # amount, ignore = remuneration_pool.tenth_amount_calculate(cr, uid, [], 'dc4', employee.id, date_from, date_to)
            else:
                payslip_ids = payslip_pool.search(cr, uid, [('employee_id', '=', employee.id),
                                                            ('date_from', '>', company.fecha_fin_costa)])
                payslips = payslip_pool.browse(cr, uid, payslip_ids, context=None)
                for payslip in payslips:
                    for detail in payslip.details_by_salary_rule_category:
                        if detail.code == 'D4':
                            amount += detail.total
                            res = self.set_detail(detail, payslip_run.id, payslip.employee_id.id, payslip.date_from, payslip.date_to)
                            detail_liquidation_pool.create(cr, uid, res)
            return amount + dc4_val
        elif not employee.region:
            raise osv.except_osv('Error', 'El empleado %s no tiene regimen asociado' % employee.name_related)
        else:
            raise osv.except_osv('Error', 'El Regimen del empleado %s no coincide con el de la empresa' % employee.name_related)
        return amount + dc4_val

    def get_current_fiscalyear(self, cr, uid, context=None):
        fiscalyear_ids = self.pool.get('account.fiscalyear').search(cr, uid, [('state', '=', 'draft')],
                                                                    order='date_start')
        fiscalyear_ids.reverse()
        return fiscalyear_ids[0]

    def get_food_vouchers_amount(self, cr, uid, contract_ids, paysilp_run_id, context=None):
        paysilp_run = self.pool.get('hr.payslip.run').browse(cr, uid, paysilp_run_id, context=None)
        lines = self.pool.get('hr.payslip').get_worked_day_lines(cr, uid, contract_ids, paysilp_run.date_start,
                                                                 paysilp_run.date_end, context=None)
        for item in lines:
            if item['code'] == 'BA':
                return item['number_of_days']*5
        return 0

    def get_antique_amount(self, cr, uid, contract, payslip_run_id, context=None):
        paysilp_run = self.pool.get('hr.payslip.run').browse(cr, uid, payslip_run_id, context=None)
        days = parser.parse(paysilp_run.date_end) - parser.parse(contract.date_start)
        years = days.days.real/365
        return years*7

    def get_current_tax_table(self, cr, uid, context=None):
        current_fiscalyear = self.get_current_fiscalyear(cr, uid, context=None)
        tax_table_ids = self.pool.get('hr.income.tax').search(cr, uid, [('fiscalyear_id', '=', current_fiscalyear), ('state', '=', 'confirm')])
        if tax_table_ids:
            return self.pool.get('hr.income.tax').browse(cr, uid, tax_table_ids[0])
        return False

    def get_incomes(self, cr, uid, paysliprun_id, employee_id):
        payslip_run = self.pool.get('hr.payslip.run').browse(cr, uid, paysliprun_id, context=None)
        income_pool = self.pool.get('hr.income')
        #SOLO TIW INICIO
        inputs_ids = []
        income_ids = income_pool.search(cr, uid, [('date', '>=', payslip_run.date_start),
                                                  ('date', '<=', payslip_run.date_end),
                                                  ('employee_id', '=', employee_id)])
        #SOLO TIW FIN
        income_fixed_ids = income_pool.search(cr, uid, [('fijo', '=', True), ('employee_id', '=', employee_id)])

        for item in income_ids:
            inputs_ids.append(item)

        return income_pool.browse(cr, uid, inputs_ids, context=None)

    def set_detail(self, detail, rule, emp, date_fr, date_to):
        return {
            'name': detail.code,
            'date_from': date_fr,
            'date_to': date_to,
            'amount': detail.total,
            'employee_id': emp,
            'role_id': rule
        }

hr_salary_rule()


class detail_liquidation_history(osv.osv):
    _name = 'detail.liquidation.history'
    _columns = {
        'name': fields.char('Tipo de Decimo', readonly=1),
        'date_from': fields.date('Inicio', readonly=1),
        'date_to': fields.date('Fin', readonly=1),
        'amount': fields.float('A pagar', readonly=1),
        'employee_id': fields.many2one('hr.employee', 'Empleado', readonly=1),
        'role_id': fields.many2one('hr.payslip.run', 'Liquidacion', readonly=1)
    }
detail_liquidation_history()
