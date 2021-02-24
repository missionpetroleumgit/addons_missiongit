'''
Created on 28/04/2015

@author: Pavel Ernesto Navarro Guerrero
'''
# -*- encoding: utf-8 -*-
from openerp.osv import fields, osv
from openerp.tools.translate import _

import openerp.addons.decimal_precision as dp
from openerp.osv.osv import osv_abstract
import time
from dateutil import parser
from datetime import datetime

class hr_income_tax(osv.osv):
    _name = "hr.income.tax"
    
    _description = "Income tax"
    
    def _get_currency(self, cr, uid, context=None):
        user = self.pool.get('res.users').browse(cr, uid, [uid], context=context)[0]
        return user.company_id.currency_id.id
    
    _columns = {
        'name': fields.char('Nombre', required=True, select=True),
        'fiscalyear_id': fields.many2one('account.fiscalyear', 'Anio Fiscal', required=True),
        #'company_id': fields.related('fiscalyear_id', 'company_id', type='many2one', relation='res.company', string='Company', store=True, readonly=True),
        'tax_lines': fields.one2many('hr.income.tax.line', 'income_tax_id', 'Lineas de impuesto', copy=True),
        'state': fields.selection([('draft', 'Nuevo'), ('confirm', 'Activo'), ('cancelled', 'Inactivo')], 'Estado'),
        'currency_id': fields.many2one('res.currency', 'Moneda', required=True),
     }
    
    _defaults = {
        #'company_id': lambda s, cr, uid, c: s.pool.get('res.company')._company_default_get(cr, uid, 'hr.employee', context=c),
        'state': 'draft',
        'currency_id': _get_currency,
    }

    def find_base_fraction(self, cr, uid, tax_obj, base_calc, context=None):
        for line in tax_obj.tax_lines:
            if line.basic_fraction < base_calc <= line.excess_up:
                return line
        return False

    def confirm(self, cr, uid, ids, context=None):
        for rec in self.browse(cr, uid, ids, context):
            if self.check_active(cr, uid, context):
                raise osv.except_orm('Error!', 'No pueden haber dos tablas de impuestos activas')
            self.write(cr, uid, [rec.id], {'state': 'confirm'})

    def cancel(self, cr, uid, ids, context=None):
        for rec in self.browse(cr, uid, ids, context):
            self.write(cr, uid, [rec.id], {'state': 'cancelled'})

    def check_active(self, cr, uid, context=None):
        tax_incomes = self.search(cr, uid, [('state', '=', 'confirm')])
        if tax_incomes:
            return True
        return False

hr_income_tax()   

class hr_income_tax_line(osv.osv):
    _name = "hr.income.tax.line"
    
    _description = "Income tax line"
    
    def _get_currency(self, cr, uid, context=None):
        user = self.pool.get('res.users').browse(cr, uid, [uid], context=context)[0]
        return user.company_id.currency_id.id
    
    def _score_calc(self,cr,uid,ids,field,arg,context=None):
        res = {}
        for tax in self.browse(cr,uid,ids,context=context):            
            tax_basic_fraction = tax.basic_fraction * tax.tax_surplus_fraction / 100 if tax.tax_surplus_fraction > 0 else 1
            res[tax.id] = tax_basic_fraction
        return res
    
    
    _columns = {
        'basic_fraction': fields.float('Fraccion Basica', digits_compute=dp.get_precision('Account'), required=True),
        'excess_up': fields.float('Exceso hasta', digits_compute=dp.get_precision('Account'), required=True),
        #'tax_basic_fraction':fields.function(_score_calc,type='float',method=True, string='tax basic fraction'),
        'tax_basic_fraction': fields.float('Impuesto fraccion basica', digits_compute=dp.get_precision('Account'), required=True),
        'tax_surplus_fraction': fields.float('% fraccion excedente', digits_compute=dp.get_precision('Account'), required=True),
        'currency_id': fields.related('income_tax_id', 'currency_id', type='many2one', relation='res.currency', string='Moneda', store=True, readonly=True),
        'income_tax_id': fields.many2one('hr.income.tax', 'Income Tax'),
     }
    
    _defaults = {
        'top_value': 0,
        'less_value': 0,
        'tax_basic_fraction': 0,
        'tax_surplus_fraction': 10,
    }

hr_income_tax_line() 

class hr_employee(osv.osv):
    _inherit = 'hr.employee'
    
    def _personal_expense_calc(self,cr,uid,ids,field,arg,context=None):
        res = {}
        for expense in self.browse(cr,uid,ids,context=context):
            total = 0
            for personal_expense in expense.personal_expense_ids:
                total += personal_expense.total_annual_cost            
            res[expense.id] = total
        return res
    
    def _get_payslips(self,cr,uid,ids,field,arg,context=None):
        res = {}
        payslip_obj = self.pool.get('hr.payslip.line')        
        for employee in self.browse(cr, uid, ids, context=context):
            res[employee.id] = payslip_obj.search(cr, uid , [('employee_id', '=', employee.id),('salary_rule_id', '=', employee.salary_rule_income_id.id)]) 
            #payslip_ids = payslip_obj.search(cr, uid , [('employee_id', '=', employee.id),('salary_rule_id', '=', employee.salary_rule_id.id)]) 
            #payslip_ids = payslip_obj.browse(cr,uid,payslip_ids,context=context)           
            #res[employee.id].extend([x for x in payslip_ids])
        return res
    
    def _get_payslip_income_taxs(self,cr,uid,ids,field,arg,context=None):
        res = {}
        payslip_obj = self.pool.get('hr.payslip.line')        
        for employee in self.browse(cr, uid, ids, context=context):
            res[employee.id] = payslip_obj.search(cr, uid , [('employee_id', '=', employee.id), ('salary_rule_id.code',
                                                                                                 '=', 'EGRIR')])
        return res
    
    def _get_current_income_tax(self,cr,uid,ids,field,arg,context):
        #pbh2
        res = {}  
        for employee in self.browse(cr, uid, ids):
            salary_rule_income_id = employee.salary_rule_income_id.id if employee.salary_rule_income_id.id else 0
            
            total_amount = 0
            incomes = 0
            current_tax = 0
            total_proyected_income = 0
            last_slip_date = datetime.now()
            # GH
            if employee.genera_imp_r:
                cr.execute('''
                    select hr_payslip_line.name as line, hr_payslip.name as payslip, amount, date_to, date_from 
                    from hr_payslip_line inner join hr_payslip on hr_payslip_line.slip_id = hr_payslip.id 
                    where hr_payslip_line.employee_id = %s and salary_rule_id = %s 
                    and extract(year from date_to) = extract(year from Now()) and extract(year from date_from) = extract(year from Now()) 
                    order by date_to''',(employee.id,salary_rule_income_id))
                values = cr.fetchall()
                if len(values)>0:
                    incomes = sum([float(x[2]) for x in values])
                    last_date = values[-1][3]
                    current_time = datetime.now()
                    current_month = '{:02d}'.format(current_time.month)
                    last_slip_date = datetime.strptime(last_date, '%Y-%m-%d')
                    last_slip_month = '{:02d}'.format(last_slip_date.month)
                    total_proyected_income = incomes + values[-1][2] * (13 - last_slip_date.month)
                    total_amount = total_proyected_income - employee.total_annual_personal_expense
            
            current_income_tax_id = employee.current_income_tax_id.id if employee.current_income_tax_id.id else 0
            
            # GH
            if employee.genera_imp_r:
                cr.execute(''' 
                    select id, tax_basic_fraction, basic_fraction, excess_up, tax_surplus_fraction 
                    from hr_income_tax_line where income_tax_id = %s 
                    and %s between basic_fraction and excess_up''',(current_income_tax_id,
                                                                     total_amount));
                income_tax_lines = cr.fetchall()
                if len(income_tax_lines) > 0:
                    tax_basic_fraction = income_tax_lines[0][1]
                    basic_fraction = income_tax_lines[0][2]
                    excess_up = income_tax_lines[0][3]
                    tax_surplus_fraction = income_tax_lines[0][4]
                    
                    diference = excess_up - total_amount
                    tax_total = tax_basic_fraction + (tax_surplus_fraction * diference / 100)
                    current_tax = tax_total / (13 - last_slip_date.month)
            
            res[employee.id] = {
                'current_total_income' : incomes,
                'income_tax' : current_tax,
                'last_slip_date' : last_slip_date,
                'total_proyected_income' : total_proyected_income,
                
            } 
        return res
    
    _columns = {
       'last_slip_date': fields.function(_get_current_income_tax, type="date", string="Fecha Ultimo Slip", multi="income_tax"),
       'total_proyected_income': fields.function(_get_current_income_tax, type="float", string="Ingreso proyectado total", multi="income_tax"),
       'current_total_income': fields.function(_get_current_income_tax, type="float", string="Ingreso anual", multi="income_tax"),
       'income_tax': fields.function(_get_current_income_tax, type="float", string="Impuesto", multi="income_tax"),
       'payslip_tax_line_ids': fields.function(_get_payslip_income_taxs, type="one2many",relation="hr.payslip.line"),
       'payslip_line_ids': fields.function(_get_payslips, type="one2many",relation="hr.payslip.line"),
       'salary_rule_income_id': fields.many2one('hr.salary.rule', 'Regla salarial de pago', required=True),
       'current_income_tax_id': fields.many2one('hr.income.tax', 'Impuesto actual', required=True),
       'salary_rule_income_tax_id': fields.many2one('hr.salary.rule', 'Regla salarial de pago', required=True),
       'personal_expense_ids': fields.one2many('hr.personal.expense', 'employee_id', 'Gastos Personales'),
       #'payslip_line_ids': fields.one2many('hr.payslip.line', 'employee_id', 'Payslips Lines'),
       'total_annual_personal_expense':fields.function(_personal_expense_calc,type='float',method=True, string='Gasto mensual desglosado'),
       
       #BITGH290715:Para filtrar solo de los que se desee generar IR
       'genera_imp_r' : fields.boolean('Generar Impuesto a la Renta?', help='Marcar si desea generar Impuesto a la Renta'),   
   }
    _defaults = {
        'genera_imp_r': lambda *a: False,
    }
    
hr_employee()
    
# class hr_contract(osv.osv):
#     _inherit = 'hr.contract'
#     def _personal_expense_calc(self,cr,uid,ids,field,arg,context=None):
#         res = {}
#         for expense in self.browse(cr,uid,ids,context=context):
#             total = 0
#             for personal_expense in expense.personal_expense_ids:
#                 total += personal_expense.total_annual_cost            
#             res[expense.id] = total / len(expense.personal_expense_ids) if len(expense.personal_expense_ids) > 0 else None
#         return res
#     
# #     def _get_users(self, cr, uid, ids, field_name, arg, context=None):
# #         res = {}
# #         users_list=[]
# #         officer_ids = self.search(cr, uid , 'bpl.officer', [('is_user', '=', True)])
# #         officer_obj = self.browse(cr, uid, officer_ids, context=context)
# #         for record in officer_obj:
# #             users_list.append(record.user_id.id) 
# #         user_obj = self.pool.get('res.users')
# #         for data in self.browse(cr, uid, ids, context=context):
# #             res[data.id] = users_list
# #         return res
#     
#     
#     _columns = {
#        'salary_rule_id': fields.many2one('hr.salary.rule', 'Payment Salary Rule', required=True),
#        'personal_expense_ids': fields.one2many('hr.personal.expense', 'contract_id', 'Personal Expenses'),
#        'salary_rule_ids': fields.one2many('hr.salary.rule', '_id', 'Personal Expenses'),
#        'total_annual_personal_expense':fields.function(_personal_expense_calc,type='float',method=True, string='monthly expenditure broken down'),
#        #'payslip_ids': fields.related('payslip_ids', 'employee_id', type='one2many', relation='hr.payslip', string='Pay Slip', readonly=True),
#     }
#     
# #     _defaults = {
# #         'user_id': _get_users,
# #     }
# 
# hr_contract()

class hr_personal_expense(osv.osv):
    _name = 'hr.personal.expense'
    def monthly_expenditure_calc(self,cr,uid,ids,field,arg,context=None):
        res = {}
        for expense in self.browse(cr,uid,ids,context=context):            
            monthly_expenditure_broken_down = expense.total_annual_cost / 12
            res[expense.id] = monthly_expenditure_broken_down
        return res
    
    _columns = {
        'fiscalyear_id': fields.many2one('account.fiscalyear', 'Anio Fiscal', required=True),
        'personal_expense_catalog_id': fields.many2one('hr.personal.expense.catalog', 'Gasto Personal'),
        'total_annual_cost': fields.float('Costo total anual', digits_compute=dp.get_precision('Account'), required=True),
        'monthly_expenditure_broken_down':fields.function(monthly_expenditure_calc,type='float',method=True, string='Gasto mensual desglosado'),
        'employee_id': fields.many2one('hr.employee', 'Employee'),
    }
hr_personal_expense()

class hr_personal_expense_catalog(osv.osv):
    _name = 'hr.personal.expense.catalog'
    
    _columns = {
        'name': fields.char('Nombre', required=True),
        'description': fields.text('Descripcion'),
    }
hr_personal_expense_catalog()

# class hr_personal_payments(osv.osv):
#     _name = 'hr.personal.payments'
#     
#     _columns = {
#         'fiscalyear_id': fields.many2one('account.fiscalyear', 'Fiscal Year', required=True),
#         'personal_expense_catalog_id': fields.many2one('hr.personal.expense.catalog', 'Personal Expense'),
#         'total_annual_cost': fields.float('Total Annual Cost', digits_compute=dp.get_precision('Account'), required=True),
#         
#         'contract_id': fields.many2one('hr.contract', 'Contract'),
#     }
# hr_personal_payments()
