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
from dateutil import parser

from openerp.osv import osv
from openerp.tools.translate import _
from openerp.osv import fields


class hr_salary_rule(osv.osv):
    _inherit = 'hr.salary.rule'

    def compute_rule(self, cr, uid, rule_id, localdict, context=None):
        obj = self.browse(cr, uid, rule_id)
        if obj.code == 'EGRIR':
            # tax_pool = self.pool.get('hr.income.tax')
            table_tax_obj = self.get_current_tax_table(cr, uid, context=None)
            if not table_tax_obj:
                raise osv.except_orm('Error!', 'Configure la tabla de impuestos')
            # rule = self.browse(cr, uid, rule_id, context=None)
            # tuple_ingresos = super(hr_salary_rule, self).compute_rule(cr, uid, rule_id, localdict, context=None)
            employee = localdict['employee']
            contract = localdict['contract']
            slip_pool = self.pool.get('hr.payslip')
            base_imp = 0.00
            last_wage = contract.wage
            # base_imp += incomes_amount
            # ba = self.get_food_vouchers_amount(cr, uid, [contract.id], context.get('active_id'), context=None)
            # antique = self.get_antique_amount(cr, uid, contract, context.get('active_id'), context=None)
            # base_imp += (ba + antique)
            amount_not_average = 0.00
            amount_expenses = 0.00
            fiscalyear_id = self.get_current_fiscalyear(cr, uid, context=None)
            payslip_run = self.pool.get('hr.payslip.run').browse(cr, uid, context.get('active_id'), context=None)
            fiscalyear_obj = self.pool.get('account.fiscalyear').browse(cr, uid, fiscalyear_id)
            days = parser.parse(fiscalyear_obj.date_stop) - parser.parse(payslip_run.date_start)
            average = parser.parse(payslip_run.date_end).month - parser.parse(fiscalyear_obj.date_start).month + 1
            months = int(days.days.real/30)
            for personal_expense in employee.personal_expense_ids:
                if personal_expense.fiscalyear_id.id == fiscalyear_id:
                    amount_expenses += personal_expense.total_annual_cost
            incomes_amount = 0.00
            valquid = util = 0.00
            for income in self.get_incomes(cr, uid, context.get('active_id'), employee.id):
                if income.adm_id.code != 'UTIL' and not income.adm_id.not_generate_benefits and income.adm_id.average:
                    # util = income.value
                    if income.adm_id.code == 'VALIQUD':
                        valquid = income.value
                    incomes_amount += income.value
                if income.adm_id.code != 'UTIL' and not income.adm_id.average:
                    amount_not_average += income.value
            incomes_amount += contract.wage

            base_imp = incomes_amount
            payslip_ids = slip_pool.search(cr, uid, [('employee_id', '=', employee.id),
                                                     ('payslip_run_id.fiscalyear_id', '=', fiscalyear_id),
                                                     ('type', '=', 'rol'),
                                                     ('state', '=', 'done'),
                                                     ('date_to', '<', payslip_run.date_end)])
            tax_acumulated = 0.00
            if payslip_ids:
                for slip in slip_pool.browse(cr, uid, payslip_ids, context=None):
                    for line in slip.line_ids:
                        if line.salary_rule_id.category_id.code == 'IGBS' and line.salary_rule_id.code not in ('BANP','BONCEX'):
                            base_imp += line.total
                        elif line.salary_rule_id.category_id.code == 'IGBS' and line.salary_rule_id.code in ('BANP','BONCEX'):
                            amount_not_average += line.total
                        if line.salary_rule_id.code == 'EGRIR':
                            tax_acumulated += line.total
            taxutil = self.get_util_tax(cr, uid, fiscalyear_obj, employee.id)
            tax_acumulated += taxutil
            util = self.get_utilities(cr, uid, fiscalyear_obj, employee.id, payslip_run.date_start)
            acumulated = base_imp
            base_imp /= average
            base_imp *= (months - 1)
            base_imp += acumulated + amount_not_average
            iess = (base_imp - valquid) * 0.0945
            base_imp += util
            base_calc = base_imp - iess - amount_expenses
            line_fraction = self.pool.get('hr.income.tax').find_base_fraction(cr, uid, table_tax_obj, base_calc, context=None)
            taxes = 0.00
            if line_fraction:
                excessive = base_calc - line_fraction.basic_fraction
                taxes = (excessive * line_fraction.tax_surplus_fraction/100) + line_fraction.tax_basic_fraction
                if taxes > 0:
                    taxes -= tax_acumulated  # Si se va a calcular el impuesto del anyo comentar esta linea y las 2 de abajo
                if taxes < 0:
                    self.pool.get('negative.taxes').create(cr, uid, {'employee_id': employee.id, 'amount': taxes, 'user_id': uid})
                    taxes = 0.00
                taxes /= months
            return taxes, 1, 100
        return super(hr_salary_rule, self).compute_rule(cr, uid, rule_id, localdict, context=None)

    def get_utilities(self, cr, uid, fiscalyear, employee_id, date_slip):
        amount = 0.00
        income_pool = self.pool.get('hr.income')
        util_income = income_pool.search(cr, uid, [('date', '>=', fiscalyear.date_start),
                                                   ('date', '<=', fiscalyear.date_stop),
                                                   ('employee_id', '=', employee_id), ('adm_id.code', '=', 'UTIL')])
        for income in income_pool.browse(cr, uid, util_income):
            # if parser.parse(income.date).month != parser.parse(date_slip).month:
            amount += income.value
        return amount

    def get_util_tax(self, cr, uid, fiscalyear, employee_id):
        amount = 0.00
        expense_pool = self.pool.get('hr.expense')
        expense_ir_util = expense_pool.search(cr, uid, [('date', '>=', fiscalyear.date_start), ('date', '<=', fiscalyear.date_stop),
                                                        ('employee_id', '=', employee_id), ('expense_type_id.code', '=', 'IRUTIL')])
        for expense in expense_pool.browse(cr, uid, expense_ir_util):
            amount += expense.value
        return amount


class hr_payslip_run(osv.osv):
    _inherit = 'hr.payslip.run'

    def _get_type(self, cr, uid, context=None):
        if 'type' in context and context['type'] == 'util':
            return 'util'
        else:
            return super(hr_payslip_run, self)._get_type(cr, uid, context)

    _columns = {
        'type': fields.selection([
            ('rol','Rol'),
            ('quincena', 'Quincena'),
            ('liquidation', 'Liquidación'),
            ('serv10', '10% Servicios'),
            ('util', 'Utilidades')
        ], 'Tipo', select=True, readonly=True),
    }
hr_payslip_run()


class hr_payslip(osv.osv):

    _inherit = 'hr.payslip'

    _columns = {
        'type': fields.selection([
            ('rol','Rol'),
            ('quincena', 'Quincena'),
            ('liquidation', 'Liquidación'),
            ('serv10', '10% Servicios'),
            ('util', 'Utilidades')
        ], 'Tipo', select=True),
    }

    def get_inputs(self, cr, uid, contract_ids, date_from, date_to, context=None):
        tipo = context['type']
        res = []
        contract_obj = self.pool.get('hr.contract')
        if tipo == 'util':

            for contract in contract_obj.browse(cr, uid, contract_ids, context=context):
                res = super(hr_payslip, self).get_inputs(cr, uid, contract_ids, date_from, date_to, context=context)

                # Ingresos
                income_obj = self.pool.get('hr.income')
                income_ids = income_obj.search(cr,uid,[('employee_id','=', contract.employee_id.id),('date','<=', date_to),
                                                       ('date','>=', date_from),('fijo','=',False),
                                                       ('adm_id.code', '=', 'UTIL')])
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

                # Egresos
                expense_obj = self.pool.get('hr.expense')
                expense_ids = expense_obj.search(cr,uid,[('employee_id','=', contract.employee_id.id),
                                                         ('date','<=', date_to),('date','>=', date_from),
                                                         ('fijo','=',False), ('expense_type_id.code', '=', 'IRUTIL')])
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

        else:
            return super(hr_payslip, self).get_inputs(cr, uid, contract_ids, date_from, date_to, context)

        return res
