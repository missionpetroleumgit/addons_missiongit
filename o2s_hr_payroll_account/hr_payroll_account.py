#-*- coding:utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    d$
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
import time
from datetime import date, datetime, timedelta

from openerp.osv import fields, osv
from openerp.tools import float_compare, float_is_zero
from openerp.tools.translate import _

class hr_payslip(osv.osv):
    _inherit = 'hr.payslip'

    _columns = {
        'move_provition_id': fields.many2one('account.move', 'Asiento Provision', readonly=True, copy=False),
    }

    def process_sheet(self, cr, uid, ids, context=None):
        print "02s_hr_payroll_account::process_sheet:: ", ids
        move_pool = self.pool.get('account.move')
        period_pool = self.pool.get('account.period')
        precision = self.pool.get('decimal.precision').precision_get(cr, uid, 'Payroll')
        timenow = time.strftime('%Y-%m-%d')
        partner_employee_pool = self.pool.get('res.partner')
        input_obj = self.pool.get('hr.payslip.input')

        for slip in self.browse(cr, uid, ids, context=context):
            partner_employee_ids = partner_employee_pool.search(cr, uid, [('employee_id', '=', slip.employee_id.id)])
            if not partner_employee_ids:
                raise osv.except_osv(('Alerta!'),('En empleado "%s" no tiene vinculado un partner!')%(slip.employee_id.name))
            line_ids = []
            line_provition_ids = []
            debit_sum = 0.0
            credit_sum = 0.0
            debit_provition_sum = 0.0
            credit_provition_sum = 0.0
            is_provition = 0
            if not slip.period_id:
                search_periods = period_pool.search(cr, uid, [('date_start', '<=', slip.date_to), ('date_stop', '>=', slip.date_to), ('company_id', '=', slip.company_id.id)])
                if not search_periods:
                    raise osv.except_orm('Error!', 'No existe un perido que contenga la fecha del slip %s para la compania %s' % (slip.date_to, slip.company_id.name))
                period_id = search_periods[0]
            else:
                period_id = slip.period_id.id
            period = self.pool.get('account.period').browse(cr, uid, period_id)

            name = _('Payslip of %s') % (slip.employee_id.name)
            name_provition = ('Provisiones de %s') % (slip.employee_id.name)
            move = {
                'narration': name,
                'date': period.date_stop,
                'ref': slip.payslip_run_id.name + ' ' + slip.number,
                'journal_id': slip.journal_id.id,
                'period_id': period_id,
            }

            move_provition = {
                'narration': name_provition,
                'date': period.date_stop,
                'ref': slip.payslip_run_id.name + ' ' + slip.number,
                'journal_id': slip.journal_id.id,
                'period_id': period_id,
            }
            for line in slip.details_by_salary_rule_category:
                debit_account_id = 0
                credit_account_id = 0
                is_provition = 0
                amt = slip.credit_note and -line.total or line.total
                if float_is_zero(amt, precision_digits=precision):
                    continue
                print "line.salary_rule_id: ", line.salary_rule_id.name
                print "line.salary_rule_id.category_id.code: ", line.salary_rule_id.category_id.code
                if line.salary_rule_id.category_id.code == 'PRO':
                    is_provition = 1
                    
                if line.salary_rule_id.category_id.code == 'SUBTOTAL':
                    continue

                if line.salary_rule_id.rule_account_ids:
                    for cuentas in line.salary_rule_id.rule_account_ids:
                        if cuentas.business_unit_id.id == slip.employee_id.business_unit_id.id:
                            debit_account_id  = cuentas.debit_account_id.id
                            credit_account_id  = cuentas.credit_account_id.id
                            if cuentas.credit_account_id.type in ('view', 'consolidation'):
                                print "AQUI: ", cuentas.credit_account_id.name 
                                raise osv.except_osv(('Error de configuracion!'),('La Cuenta "%s" no se ha configurado correctamente la cuenta de Debito!')%(line.salary_rule_id.name))
                
                if line.salary_rule_id.category_id.code in ('IGBS','OINGNBS'):
                    if not debit_account_id:
                        raise osv.except_osv(('Error de configuracion!'),('En la Regla "%s" no se ha configurado correctamente la cuenta de Debito!')%(line.salary_rule_id.name))
                     
                if line.salary_rule_id.category_id.code in ('EGRE'):
                    if not credit_account_id:
                        raise osv.except_osv(('Error de configuracion!'),('En la Regla "%s" no se ha configurado correctamente la cuenta de Credito!')%(line.salary_rule_id.name))

                # Distribucion
                if line.code in ('INGHXT','INGHNOC','INGHSUP','INGHRF') or line.category_id.code == 'EGRE':
                    if line.category_id.code != 'EGRE':
                        input_ids = input_obj.search(cr,uid,[('payslip_id','=', slip.id),('code','=', line.code)])
                        for input in input_obj.browse(cr, uid, input_ids):
                            if debit_account_id:
                                debit_line = (0, 0, {
                                    'name': line.name,
                                    'date': period.date_stop,
                                    'partner_id': (partner_employee_ids[0] or False),
                                    'account_id': debit_account_id,
                                    'journal_id': slip.journal_id.id,
                                    'period_id': period_id,
                                    'debit': input.amount > 0.0 and round(input.amount, 4) or 0.0,
                                    'credit': input.amount < 0.0 and -round(input.amount, 4) or 0.0,
                                    # 'analytic_account_id': input.income_id.analytic_id.id or False,
                                    'tax_code_id': line.salary_rule_id.account_tax_id and line.salary_rule_id.account_tax_id.id or False,
                                    'tax_amount': line.salary_rule_id.account_tax_id and input.amount or 0.0,
                                })
                                line_ids.append(debit_line)
                                debit_sum += debit_line[2]['debit'] - debit_line[2]['credit']
                    else:
                        if credit_account_id:
                            credit_line = (0, 0, {
                                'name': line.name,
                                'date': period.date_stop,
                                'partner_id': (partner_employee_ids[0] or False),
                                'account_id': credit_account_id,
                                'journal_id': slip.journal_id.id,
                                'period_id': period_id,
                                'debit': line.total < 0.0 and -round(line.total, 4) or 0.0,
                                'credit': line.total > 0.0 and round(line.total, 4) or 0.0,
                                'analytic_account_id': False,
                                'tax_code_id': line.salary_rule_id.account_tax_id and line.salary_rule_id.account_tax_id.id or False,
                                'tax_amount': line.salary_rule_id.account_tax_id and line.total or 0.0,
                            })
                            if is_provition:
                                line_provition_ids.append(credit_line)
                                credit_provition_sum += credit_line[2]['credit'] - credit_line[2]['debit']
                            else:
                                line_ids.append(credit_line)
                                credit_sum += credit_line[2]['credit'] - credit_line[2]['debit']
                else:
                    # for distribucion in line.contract_id.contract_analytic_ids:
                    #     print "Distribucion rate: ", distribucion.rate
                    #     if distribucion.rate <= 0:
                    #          raise osv.except_osv(('Error de configuracion!'),('Revisar los Centros de Costo del Empleado "%s" !')%(line.employee_id.name_related))
                    #     vd_amt = amt * distribucion.rate / 100.00
                    #     print "amt: ", amt
                    #     print "vd_amt: ", vd_amt

                    if debit_account_id:
                        debit_line = (0, 0, {
                            'name': line.name,
                            'date': period.date_stop,
                            'partner_id': (partner_employee_ids[0] or False),
                            'account_id': debit_account_id,
                            'journal_id': slip.journal_id.id,
                            'period_id': period_id,
                            'debit': amt > 0.0 and round(amt, 4) or 0.0,
                            'credit': amt < 0.0 and -round(amt, 4) or 0.0,
                            # 'analytic_account_id': distribucion.account_analytic_id.id or False,
                            'tax_code_id': line.salary_rule_id.account_tax_id and line.salary_rule_id.account_tax_id.id or False,
                            'tax_amount': line.salary_rule_id.account_tax_id and amt or 0.0,
                        })
                        if is_provition:
                            line_provition_ids.append(debit_line)
                            debit_provition_sum += debit_line[2]['debit'] - debit_line[2]['credit']
                        else:
                            line_ids.append(debit_line)
                            debit_sum += debit_line[2]['debit'] - debit_line[2]['credit']

                    if credit_account_id:
                        credit_line = (0, 0, {
                            'name': line.name,
                            'date': period.date_stop,
                            'partner_id': (partner_employee_ids[0] or False),
                            'account_id': credit_account_id,
                            'journal_id': slip.journal_id.id,
                            'period_id': period_id,
                            'debit': amt < 0.0 and -round(amt, 4) or 0.0,
                            'credit': amt > 0.0 and round(amt, 4) or 0.0,
                            # 'analytic_account_id': distribucion.account_analytic_id.id if not is_provition else False,
                            'tax_code_id': line.salary_rule_id.account_tax_id and line.salary_rule_id.account_tax_id.id or False,
                            'tax_amount': line.salary_rule_id.account_tax_id and amt or 0.0,
                        })
                        if is_provition:
                            line_provition_ids.append(credit_line)
                            credit_provition_sum += credit_line[2]['credit'] - credit_line[2]['debit']
                        else:
                            line_ids.append(credit_line)
                            credit_sum += credit_line[2]['credit'] - credit_line[2]['debit']

            if float_compare(credit_sum, debit_sum, precision_digits=precision) == -1:
                acc_id = slip.journal_id.default_credit_account_id.id
                if not acc_id:
                    raise osv.except_osv(_('Configuration Error!'),_('The Expense Journal "%s" has not properly configured the Credit Account!')%(slip.journal_id.name))
                adjust_credit = (0, 0, {
                    'name': _('Adjustment Entry'),
                    'date': period.date_stop,
                    'partner_id': partner_employee_ids[0],
                    'account_id': acc_id,
                    'journal_id': slip.journal_id.id,
                    'period_id': period_id,
                    'debit': 0.0,
                    'credit': round(debit_sum - credit_sum, 4),
                })
                line_ids.append(adjust_credit)

            
            # Para provisiones
            if float_compare(credit_provition_sum, debit_provition_sum, precision_digits=precision) == -1:
                acc_id = slip.journal_id.default_credit_account_id.id
                if not acc_id:
                    raise osv.except_osv(_('Configuration Error!'),_('The Expense Journal "%s" has not properly configured the Credit Account!')%(slip.journal_id.name))
                adjust_provition_credit = (0, 0, {
                    'name': _('Adjustment Entry'),
                    'date': period.date_stop,
                    'partner_id': partner_employee_ids[0],
                    'account_id': acc_id,
                    'journal_id': slip.journal_id.id,
                    'period_id': period_id,
                    'debit': 0.0,
                    'credit': round(debit_provition_sum - credit_provition_sum, 4),
                })
                line_provition_ids.append(adjust_provition_credit)

            elif float_compare(debit_sum, credit_sum, precision_digits=precision) == -1:
                acc_id = slip.journal_id.default_debit_account_id.id
                if not acc_id:
                    raise osv.except_osv(_('Configuration Error!'),_('The Expense Journal "%s" has not properly configured the Debit Account!')%(slip.journal_id.name))
                adjust_debit = (0, 0, {
                    'name': _('Adjustment Entry'),
                    'date': period.date_stop,
                    'partner_id': False,
                    'account_id': acc_id,
                    'journal_id': slip.journal_id.id,
                    'period_id': period_id,
                    'debit': round(credit_sum - debit_sum, 4),
                    'credit': 0.0,
                })
                line_ids.append(adjust_debit)
            
            # Para provisiones 
            elif float_compare(debit_provition_sum, credit_provition_sum, precision_digits=precision) == -1:
                acc_id = slip.journal_id.default_debit_account_id.id
                if not acc_id:
                    raise osv.except_osv(_('Configuration Error!'),_('The Expense Journal "%s" has not properly configured the Debit Account!')%(slip.journal_id.name))
                adjust_provition_debit = (0, 0, {
                    'name': _('Adjustment Entry'),
                    'date': period.date_stop,
                    'partner_id': False,
                    'account_id': acc_id,
                    'journal_id': slip.journal_id.id,
                    'period_id': period_id,
                    'debit': round(credit_sum - debit_sum, 4),
                    'credit': 0.0,
                })
                line_provition_ids.append(adjust_provition_debit)
                
            line_ids = self.validate_move(line_ids)
            move.update({'line_id': line_ids})
            move_id = move_pool.create(cr, uid, move, context=context)
            if slip.type == 'rol':
                line_provition_ids = self.validate_move(line_provition_ids)
                move_provition.update({'line_id': line_provition_ids})
                move_provition_id = move_pool.create(cr, uid, move_provition, context=context)
            else:
                move_provition_id = False
            self.write(cr, uid, [slip.id], {'move_id': move_id, 'period_id' : period_id, 'move_provition_id' : move_provition_id}, context=context)
            # if slip.journal_id.entry_posted:
            #     move_pool.post(cr, uid, [move_id, move_provition_id], context=context)
        return self.write(cr, uid, ids, {'paid': True, 'state': 'done'}, context=context)
#         return super(hr_payslip, self).process_sheet(cr, uid, [slip.id], context=context)

    def validate_move(self, move_lines):
        suma_round = 0.0000
        for linea in move_lines:
            suma_round += round(linea[2]['debit'] - linea[2]['credit'], 4)
        if suma_round and suma_round < 1:
            for linea in move_lines:
                if (suma_round > 0) and (linea[2]['credit'] > 0):
                    to_update = linea[2]['credit'] + suma_round
                    linea[2].update({'credit': to_update})
                    break
                elif (suma_round < 0) and (linea[2]['debit'] > 0):
                    to_update = linea[2]['debit'] + -suma_round
                    linea[2].update({'debit': to_update})
                    break
        return move_lines

    def cancel_sheet(self, cr, uid, ids, context=None):
        print "o2s_hr_payroll_account: cancel_sheet:: ", ids
        move_pool = self.pool.get('account.move')
        move_ids = []
        move_to_cancel = []
        loan_line_obj = self.pool.get('hr.loan.line')
        move_provition_ids = []
        move_provition_to_cancel = []
        
        for slip in self.browse(cr, uid, ids, context=context): 
            if slip.move_id:
                move_ids.append(slip.move_id.id)
                if slip.move_id.state == 'posted':
                    move_to_cancel.append(slip.move_id.id)

            if slip.move_provition_id:
                move_provition_ids.append(slip.move_provition_id.id)
                if slip.move_provition_id.state == 'posted':
                    move_provition_to_cancel.append(slip.move_provition_id.id)
            print "paso append"
            loan_ids = loan_line_obj.search(cr, uid, [('employee_id', '=', slip.employee_id.id),('paid','=',True),('paid_date','>=',slip.date_from),
                                                ('paid_date','<',slip.date_to)])
            if len(loan_ids)>0:
                loan_line_obj.write(cr, uid, loan_ids, {'paid': False})
            print "paso loan"
            for input_line in slip.input_line_ids:
                if input_line.income_id:
                    self.pool.get('hr.income').write(cr, uid, input_line.income_id.id, {'state':'draft'})
                elif input_line.expense_id:
                    self.pool.get('hr.expense').write(cr, uid, input_line.income_id.id, {'state':'draft'})
            print "paso write ingresos egresos"
                    
        move_pool.button_cancel(cr, uid, move_to_cancel, context=context)
        move_pool.unlink(cr, uid, move_ids, context=context)
        print "paso cancel unlink asiento"
        move_pool.button_cancel(cr, uid, move_provition_to_cancel, context=context)
        move_pool.unlink(cr, uid, move_provition_ids, context=context)
        print "paso cancel unlink provision"
        self.signal_workflow(cr, uid, ids, 'cancel_sheet')
        print "paso signal_workflow cancel_shet"
#         return super(hr_payslip, self).cancel_sheet(cr, uid, ids, context=context)        
        return self.write(cr, uid, ids, {'state': 'cancel'}, context=context)
        




class hr_salary_rule(osv.osv):
    _inherit = 'hr.salary.rule'
    _columns = {
        'rule_account_ids':fields.one2many('hr.salary.rule.account', 'salary_rule_id', 'Cuentas Contables'),
     }

hr_salary_rule()

class hr_salary_rule_account(osv.osv):
    _name = "hr.salary.rule.account"
    _description = "Cuentas contables por Reglas"

    _columns = {
        'name' : fields.char('Descripcion', size=128),
        'debit_account_id': fields.many2one('account.account', 'Cuenta contable al debe'),
        'credit_account_id': fields.many2one('account.account', 'Cuenta contable al haber'),
        'business_unit_id':fields.many2one('hr.business.unit', 'Unidad de Negocio'),
        'salary_rule_id':fields.many2one('hr.salary.rule','Ingresos'),
    }
hr_salary_rule_account()

class hr_payslip_run(osv.osv):
    _inherit = 'hr.payslip.run'

    def _get_default_journal(self, cr, uid, context=None):
        if context is None:
            context = {}
        struct_id = False
        if 'type' in context:
            if context['type'] in ['quincena', 'serv10']:
                hr_journal_struct_obj = self.pool['account.journal']
                search_struct = hr_journal_struct_obj.search(cr, uid, [('code','=', 'O2SDN')])
                if len(search_struct) > 0:
                    struct_id = context.get('struct_id', search_struct[0])
                else:
                    raise osv.except_osv(_('Diario de nómina invalido !'), _('Revise el codigo del diario de nómina es O2SDN !'))
            elif context['type'] == 'rol':
                hr_journal_struct_obj = self.pool['account.journal']
                search_struct = hr_journal_struct_obj.search(cr, uid, [('code','=', 'O2SDN')])
                if len(search_struct) > 0:
                    struct_id = context.get('struct_id', search_struct[0])
                else:
                    raise osv.except_osv(_('Diario de nómina invalido !'), _('Revise el codigo del diario de nómina es O2SDN !'))
            elif context['type'] == 'liquidation':
                hr_journal_struct_obj = self.pool['account.journal']
                search_struct = hr_journal_struct_obj.search(cr, uid, [('code','=', 'O2SDL')])
                if len(search_struct) > 0:
                    struct_id = context.get('struct_id', search_struct[0])
                else:
                    raise osv.except_osv(_('Diario de nómina invalido !'), _('Revise el codigo del diario de nómina es O2SDL !'))
            return struct_id
        else:
            return False

    _columns = {
        'journal_id': fields.many2one('account.journal', 'Salary Journal', states={'draft': [('readonly', False)]}, readonly=True, required=True),
    }

    _defaults = {
        'journal_id': _get_default_journal,
    }

    def draft_payslip_run(self, cr, uid, ids, context=None):
        print "o2s_hr_payroll_account:: draft_payslip_run:: ", ids
        obj_payslip = self.pool.get('hr.payslip')
        account_move = self.pool.get('account.move')
        for payslip_run in self.browse(cr, uid, ids):
            for slip in payslip_run.slip_ids:
                # print "slip.name: ", slip.name
#                 if slip.move_id:
#                     account_move.unlink(cr, uid, [slip.move_id.id])
                obj_payslip.cancel_sheet(cr, uid, [slip.id], context=None)
                # print "paso obj_payslip.cancel_sheet"
                obj_payslip.signal_workflow(cr, uid, [slip.id], 'draft')
                # print "paso obj_payslip.signal_workflow"

        return self.write(cr, uid, ids, {'state': 'draft'}, context=context)

hr_payslip_run()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
