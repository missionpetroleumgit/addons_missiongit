# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution - Ecuador
#    Copyright (C) 2014 BitConsultores (<http://http://bitconsultores-ec.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
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

import openerp.addons.decimal_precision as dp

from datetime import datetime, date, time, timedelta
import calendar
from openerp.tools.translate import _
from openerp.osv import fields, osv
from openerp import models, api
from dateutil import parser
from dateutil.relativedelta import relativedelta
from openerp.exceptions import except_orm

# BEGIN COMMON

# END COMMON

class account_invoice(osv.osv):
    _inherit = 'account.invoice'
    _description = 'Invoice'
    
    _columns = {
        'is_third' : fields.boolean('Terceros ?', help="Marque esta opcion si es una factura de terceros"),
        # 
        'terceros_line' : fields.one2many('account.terceros', 'terceros_id', string='Terceros Lines', copy=True, states={'draft': [('readonly', False)]}),
        'expense_type_id': fields.many2one('hr.expense.type', 'Tipo de egreso'),
        'salary_rule_id': fields.many2one('hr.salary.rule', 'Tipo de egreso'),
        'period_tercero_id': fields.many2one('account.period', 'Periodo de Nomina', domain="[('special', '=', False)]"),
        'third_amount': fields.float('Total'),
        
        #O2SGH: Para varias cuotas 
        'varias_cuotas' : fields.boolean('Varias Cuotas ?', help="Marque si desea generar varias coutas a ser descontadas en RRHH"),
        'num_cuotas':fields.integer('N° Coutas'),
        'period_ini_couta' : fields.many2one('account.period', 'Periodo Inicio Cuota', domain="[('special', '=', False)]", help="Registre la fecha de la primera couta para generar los egresos"),
        'type_emp' : fields.selection([('adm', 'Administrativo'), ('ope', 'Operativo')], 'Tipo'),
    }
    
    _defaults = {
        'varias_cuotas' : lambda * a: False,
    }

    def onchange_isthird(self, cr, uid, ids, is_third, context=None):
        res = {}
        third_ids = []
        if ids and not is_third:
            for invoice in self.browse(cr, uid, ids):
                for line in invoice.terceros_line:
                    third_ids.append(line.id)
                    sentence = 'delete from account_terceros  where id = %s' % line.id
                    cr.execute(sentence)
                res['value'] = {'terceros_line': None, 'third_amount': 0.00}
                self.write(cr,uid, [invoice.id], {'third_amount': 0.00})

        return res

    def onchange_amount_tercero(self, cr, uid, ids, terceros_line, context=None):
#         for invoice in self.browse(cr, uid, ids):
        terc_list = terceros_line[0][2] if terceros_line else []
        total = 0.0
        for terc in self.pool.get('account.terceros').browse(cr, uid, terc_list):
            total += terc.amount
        return {'value': {'third_amount': total} }

    def update_amount(self, cr, uid, ids, context=None):
        total = 0.00
        for record in self.browse(cr, uid, ids):
            for line in record.terceros_line:
                total += line.amount
        return self.write(cr, uid, ids, {'third_amount': total})
    
    def calculate_quotes(self, employee):
        """
        Este metodo debe reimplementarse para determinar la cuota por empleado
        recibe como parametro el objeto empleado
        :return: Devuelve la cuota a pagar del empleado
        """
        return 8.63

    def load_employee(self, cr, uid, ids, context=None):
        total = 0.00
        if ids:
            for invoice in self.browse(cr, uid, ids):
                obj_employee = self.pool.get('hr.employee')
                if invoice.type_emp:
                    if invoice.type_emp == 'adm':
                        type_ids = self.pool.get('hr.business.unit').search(cr,uid,[('codigo','in',['ADM','ADMOPE'])])
                    elif invoice.type_emp == 'ope': 
                        type_ids = self.pool.get('hr.business.unit').search(cr,uid,[('codigo','=','OPE')])
                        
                    args = [('state_emp', '=', 'active'), \
                        ('business_unit_id', 'in', type_ids)]
                else:
                    args = [('state_emp', '=', 'active')]
                    
                print "args: ", args
                employee_ids = obj_employee.search(cr, uid, args)
                
                del_inv_exp_ids = map(lambda x: x.id, invoice.terceros_line)
                self.pool.get('account.terceros').unlink(cr, uid, del_inv_exp_ids, context)
                
                for employee in obj_employee.browse(cr, uid, employee_ids):
                    vals = {
                        'terceros_id': invoice.id,
                        'employee': employee.id,
                        'amount': self.calculate_quotes(employee),
                    }
                    total += self.calculate_quotes(employee)
                    self.pool.get('account.terceros').create(cr, uid, vals, context=None)
                self.write(cr, uid, [invoice.id], {'third_amount': total})
        return True

    def load_third(self, cr, uid, ids, context=None):
        total = 0.00
        if ids:
            for invoice in self.browse(cr, uid, ids):
                print "period: ", invoice.period_tercero_id.date_start
                expense_pool = self.pool.get('hr.payslip.line')
                args = [('code', '=', invoice.expense_type_id.code), \
                        ('slip_id.date_from', '>=', invoice.period_tercero_id.date_start), \
                        ('slip_id.date_to', '<=', invoice.period_tercero_id.date_stop)]
                print "args: ", args
                expense_ids = expense_pool.search(cr, uid, args)
                
                del_inv_exp_ids = map(lambda x: x.id, invoice.terceros_line)
                self.pool.get('account.terceros').unlink(cr, uid, del_inv_exp_ids, context)
                
                for expense in expense_pool.browse(cr, uid, expense_ids):
                    vals = {
                        'terceros_id': invoice.id,
                        'employee': expense.employee_id.id,
                        'amount': expense.total,
                    }
                    total+=expense.total
                    self.pool.get('account.terceros').create(cr, uid, vals, context=None)
                self.write(cr, uid, [invoice.id], {'third_amount': total})
        return True

    @api.one
    def create_expenses(self, employee, quotes, date_start, amount):
        expense_pool = self.env['hr.expense']
        expense_ids = list()
        if quotes > 0:
            amount /= quotes
            if self.expense_type_id.code == 'EGRPEMP':
                expenses = expense_pool.search([('expense_type_id.code', '=', 'EGRPEMP'), ('state', '=', 'draft'), ('date', '>=', date_start),
                                                ('employee_id', '=', employee.id)], order='date')
                for expense in expenses:
                    expense_ids.append(expense.id)
                if expense_ids:
                    expense_ids.reverse()
                    max_expense = expense_pool.browse(expense_ids[0])
                    date_start = max_expense.date
            # i = 1
            relative_date = parser.parse(date_start)
            while quotes > 0:
                vals = {'expense_type_id': self.expense_type_id.id, 'value': amount, 'employee_id': employee.id,
                        'date': relative_date.strftime('%Y-%m-%d'), 'invoice_id': self.id}
                expense_pool.create(vals)
                relative_date = relative_date + relativedelta(months=1)
                # i += 1
                quotes -= 1
        else:
            vals = {'expense_type_id': self.expense_type_id.id, 'value': amount, 'employee_id': employee.id, 'date': date_start, 'invoice_id': self.id}
            expense_pool.create(vals)
        return True

    @api.multi
    def invoice_validate(self):
        self.update_amount()
        if self.amount_total == 0:
            raise osv.except_osv(_('¡¡ Alerta !!'), _('El monto de la factura no puede ser cero.'))
        if self.terceros_line:
            for invoice_line in self.invoice_line:
                if invoice_line.discount_third and self.third_amount > invoice_line.price_subtotal:
                    raise osv.except_osv(_('¡¡ Alerta !!'), _('El monto a pagar por los ' + \
                                            'empleados debe ser menor al monto de la linea de terceros de la factura.'))
#             for inv in self:
#                 for terc in inv.terceros_line:
#                     terc.expense_id.state = 'procesado'
        if self.is_third:
            if self.varias_cuotas:
                for line in self.terceros_line:
                    self.create_expenses(line.employee, self.num_cuotas, self.period_ini_couta.date_start, line.amount)
            else:
                for line in self.terceros_line:
                    self.create_expenses(line.employee, 0, self.period_tercero_id.date_start, line.amount)
        res = super(account_invoice, self).invoice_validate()
        return res
    
    @api.multi
    def action_cancel(self):
        res = super(account_invoice, self).action_cancel()
        if self.is_third and self.terceros_line:
            expense_pool = self.env['hr.expense']
            expenses = expense_pool.search([('invoice_id', '=', self.ids[0])])
            if expenses:
                expenses.unlink()
            tot_new_line = 0.0
            for inv in self:
                for terc in inv.terceros_line:
#                     terc.expense_id.state = 'draft'
                    rec_partner = self.env['res.partner'].search([('employee_id', '=', terc.employee.id), \
                                                                  ('is_employee', '=', True)]).mapped('id')
                    args = [('move_id', '=', self.move_id.id), ('partner_id', 'in', rec_partner), \
                            ('debit', '=', terc.amount)]
                    self.env['account.move.line'].search(args).unlink()
                    tot_new_line += terc.amount
            
            line_amount = '%.2f' % (float(self.amount_untaxed - tot_new_line))
            for mov_line in self.move_id.line_id:
                if line_amount == '%.2f' % (float(mov_line.debit)):
                    rec_ml = self.env['account.move.line'].browse(mov_line.id)
                    rec_ml.debit = self.amount_untaxed
        return res

account_invoice()

class account_terceros(osv.osv):
    _name = 'account.terceros'
    _description = 'Account terceros line'
    
    _columns = {
        'terceros_id' : fields.many2one('account.invoice', string='Terceros Reference', ondelete='cascade', index=True),        
        'employee': fields.many2one('hr.employee', 'Employee'),
#        'account_id': fields.many2one('account.account', 'Account'),
        'expense_id': fields.many2one('hr.expense', 'Expense'),
        'amount': fields.float('Valor', size=8, help="Valor para terceros"),
        'salary_rule_id': fields.many2one('hr.salary.rule', 'Egreso'),
    }
account_terceros()


class res_company(osv.osv):
    _inherit = 'res.company'
   
    _columns = {
        'exp_account_id' : fields.many2one('account.account', string='Cuenta por cobrar', ondelete='cascade', index=True),
    }

res_company()

#class res_partner(osv.osv):
##    """
#    This document is used in the invoice.
#    """
#    
#    _inherit = 'res.partner'
#    _description = 'Partner'

    #def write(self, cr, uid, ids, vals, context=None):
    #    obj_partner = self.pool['res.partner']
    #    partner_ids = obj_partner.search(cr, uid, [('is_employee', '=', True)], limit=None)
    #    print "partner_ids: ",  partner_ids
        # for partner in obj_partner.browse(cr, uid, partner_ids):
        # if partner.custumer:
        # vals['property_account_receivable'] = 534
        # vals['property_account_payable'] = 1062
        # else:
    #    vals['property_account_receivable'] = 3556
    #    vals['property_account_payable'] = 3875
        # vals['tax_support'] = 1
        # super(res_partner, self).write(cr, uid, partner.id, vals, context=context)
    #    return super(res_partner, self).write(cr, uid, partner_ids, vals, context=context)
#    
#    
#res_partner()

                    
