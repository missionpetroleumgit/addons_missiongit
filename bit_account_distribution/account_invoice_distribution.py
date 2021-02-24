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

import itertools
from lxml import etree

from openerp import models, fields, api, _
from openerp.osv import fields, osv
from openerp.exceptions import except_orm, Warning, RedirectWarning
from openerp.tools import float_compare
import openerp.addons.decimal_precision as dp

import openerp.addons.decimal_precision as dp
from datetime import datetime, date, time, timedelta
import calendar
import logging

_logger = logging.getLogger(__name__)

#-----------------------------------
#    Inherit - Invoice
#-----------------------------------
class account_invoice(osv.osv):
    _inherit = 'account.invoice'
    _description = 'Invoice'
    
    _columns = {

    }

    @api.multi
    def action_move_create(self):
        """ Creates invoice related analytics and financial move lines """
        account_invoice_tax = self.env['account.invoice.tax']
        account_move = self.env['account.move']

        l_iml = []

        for inv in self:
            if not inv.journal_id.sequence_id:
                raise except_orm(_('Error!'), _('Please define sequence on the journal related to this invoice.'))
            if not inv.invoice_line:
                raise except_orm(_('No Invoice Lines!'), _('Please create some invoice lines.'))
            # if inv.move_id:
            #     continue

            ctx = dict(self._context, lang=inv.partner_id.lang)

            if not inv.date_invoice:
                now = datetime.today().date()
                inv.with_context(ctx).write({'date_invoice': now})
            date_invoice = inv.date_invoice

            company_currency = inv.company_id.currency_id
            # create the analytical lines, one move line per invoice line
            iml = inv._get_analytic_lines()
            # check if taxes are all computed
            compute_taxes = account_invoice_tax.compute(inv.with_context(lang=inv.partner_id.lang))
            inv.check_tax_lines(compute_taxes)

            # I disabled the check_total feature
            if self.env['res.users'].has_group('account.group_supplier_inv_check_total'):
                if inv.type in ('in_invoice', 'in_refund') and abs(inv.check_total - inv.amount_total) >= (inv.currency_id.rounding / 2.0):
                    raise except_orm(_('Bad Total!'), _('Please verify the price of the invoice!\nThe encoded total does not match the computed total.'))

            if inv.payment_term:
                total_fixed = total_percent = 0
                for line in inv.payment_term.line_ids:
                    if line.value == 'fixed':
                        total_fixed += line.value_amount
                    if line.value == 'procent':
                        total_percent += line.value_amount
                total_fixed = (total_fixed * 100) / (inv.amount_total or 1.0)
                if (total_fixed + total_percent) > 100:
                    raise except_orm(_('Error!'), _("Cannot create the invoice.\nThe related payment term is probably misconfigured as it gives a computed amount greater than the total invoiced amount. In order to avoid rounding issues, the latest line of your payment term must be of type 'balance'."))

            # one move line per tax line
            iml += account_invoice_tax.move_line_get(inv.id)
            _logger.error("DATOS DE LA VARIABLE iml: " + str(iml))
            if inv.type in ('in_invoice', 'in_refund'):
                ref = inv.reference
            else:
                ref = inv.number

            diff_currency = inv.currency_id != company_currency
            # create one move line for the total and possibly adjust the other lines amount
            total, total_currency, iml = inv.with_context(ctx).compute_invoice_totals(company_currency, ref, iml)

            name = inv.supplier_invoice_number or inv.name or '/'
            totlines = []
            if inv.payment_term:
                totlines = inv.with_context(ctx).payment_term.compute(total, date_invoice)[0]
            if totlines:
                res_amount_currency = total_currency
                ctx['date'] = date_invoice
                for i, t in enumerate(totlines):
                    if inv.currency_id != company_currency:
                        amount_currency = company_currency.with_context(ctx).compute(t[1], inv.currency_id)
                    else:
                        amount_currency = False

                    # last line: add the diff
                    res_amount_currency -= amount_currency or 0
                    if i + 1 == len(totlines):
                        amount_currency += res_amount_currency
                    _logger.error("DATOS DE LA VARIABLE t[1]: " + str(t[1]) + " REDONDEADO " + str(round(t[1],2)))
                    iml.append({
                        'type': 'dest',
                        'name': name,
                        'price': round(t[1],2),
                        'account_id': inv.account_id.id,
                        'date_maturity': t[0],
                        'amount_currency': diff_currency and amount_currency,
                        'currency_id': diff_currency and inv.currency_id.id,
                        'ref': ref,
                    })
                    #_logger.error("DATOS DE LA VARIABLE iml.append: " + str(iml))
            else:
                analytic = ''
                dist_total = total
                line_val = valor = total_currency
                # for invoice_line in inv.invoice_line:
                #     cant = len(invoice_line.analytics_id.account_ids) or 1
                #     sum_total = sumatoria = i = 0
                #     while cant > 0:
                #         if invoice_line.analytics_id.account_ids:
                #             percent = invoice_line.analytics_id.account_ids[i]
                #             line_val = valor * float(percent.rate / 100)
                #             dist_total = total * float(percent.rate / 100)
                #             sum_total += dist_total
                #             analytic = percent.analytic_account_id.id
                #         if invoice_line.analytics_id.account_ids and cant == 1:
                #             res_total = total - sum_total
                #             dist_total += res_total
                #             resto = valor - sumatoria
                #             line_val += resto
                #         cant -= 1
                #         i += 1

                dicc_iml = {
                    'type': 'dest',
                    'name': name,
                    'price': round(dist_total,2),
                    'account_id': inv.account_id.id,
                    'date_maturity': inv.date_due,
                    'amount_currency': diff_currency and line_val,
                    'currency_id': diff_currency and inv.currency_id.id,
                    'ref': ref,
                    'my_analytics': analytic
                }
                _logger.error("DATOS DE LA VARIABLE dicc_iml: " + str(dicc_iml))
                iml.append(dicc_iml)
                l_iml.append(dicc_iml)
                    # break
            date = date_invoice

            part = self.env['res.partner']._find_accounting_partner(inv.partner_id)
            #_logger.error("DATOS DEL MOVIMIENTO CONTABLE: " + str(iml))
            line = [(0, 0, self.line_get_convert(l, part.id, date)) for l in iml]
            any_analytics = False
            for item_line in inv.invoice_line:
                if item_line.analytics_id:
                    any_analytics = True
                    break
            if not any_analytics:
                line = inv.group_lines(iml, line)

            journal = inv.journal_id.with_context(ctx)
            if journal.centralisation:
                raise except_orm(_('User Error!'),
                        _('You cannot create an invoice on a centralized journal. Uncheck the centralized counterpart box in the related journal from the configuration menu.'))

            line = inv.finalize_invoice_move_lines(line)
            # if inv.is_third:
            #     # for item in line:
            #     #     account = self.env['account.account'].browse(item[2]['account_id'])
            #     #     if account.user_type.code == 'expense':
            #     #         item[2]['debit'] -= inv.third_amount
            #     #         break
            #     for third in inv.terceros_line:
            #         dict_line = {
            #             'account_id': inv.company_id.exp_account_id.id,
            #             'date': inv.date_invoice,
            #             'name': '/',
            #             'partner_id': self.env['res.partner'].search([('employee_id', '=', third.employee.id)]).id,
            #             'debit': third.amount
            #         }
            #         line.append((0, 0, dict_line))
            suma_round = 0.0000
            for item in line:
                suma_round += round((item[2]['debit'] - item[2]['credit']), 4)
            if suma_round:
                for item in line:
                    if (suma_round > 0) and (item[2]['credit'] > 0):
                        item[2]['credit'] += suma_round
                        break
                    elif (suma_round < 0) and (item[2]['debit'] > 0):
                        item[2]['debit'] += -suma_round
                        break
            move_vals = {
                'ref': inv.reference or inv.name,
                'line_id': line,
                'journal_id': journal.id,
                'date': inv.date_invoice,
                'narration': inv.comment,
                'company_id': inv.company_id.id,
            }
            ctx['company_id'] = inv.company_id.id
            period = inv.period_id
            if not period:
                period = period.with_context(ctx).find(date_invoice)[:1]
            if inv.move_id:
                for element in line:
                    element[2].update({'move_id': inv.move_id.id})
                    self.env['account.move.line'].create(element[2])
                move = inv.move_id
            else:
                move_vals = {
                    'ref': inv.reference or inv.name,
                    'line_id': line,
                    'journal_id': journal.id,
                    'date': inv.date_invoice,
                    'narration': inv.comment,
                    'company_id': inv.company_id.id,
                }
                ctx['company_id'] = inv.company_id.id
                if period:
                    move_vals['period_id'] = period.id
                    for i in line:
                        i[2]['period_id'] = period.id

                ctx['invoice'] = inv
                ctx_nolang = ctx.copy()
                ctx_nolang.pop('lang', None)
                move = account_move.with_context(ctx_nolang).create(move_vals)

            # make the invoice point to that move
            vals = {
                'move_id': move.id,
                'period_id': period.id,
                'move_name': move.name,
            }
            inv.with_context(ctx).write(vals)

            temp_aux = []
            for l in move.line_id:
                for aux_iml in l_iml:
                    tmp_price = round(float(aux_iml.get('price')),2)
                    if inv.type in ('in_invoice', 'in_refund'):
                        mov_price = round(float(l.credit * -1), 2)
                    else:
                        mov_price = round(float(l.debit), 2)
                    if mov_price == tmp_price:
                        temp_aux.append( { 'analytic_id' : aux_iml.get('my_analytics'), 'move_id' : l.id } )

            # Pass invoice in context in method post: used if you want to get the same
            # account move reference when creating the same invoice after a cancelled one:
            # debit = 0.00
            # credit = 0.00
            # for rim in move.line_id:
            #     debit += rim.debit
            #     credit += rim.credit
            # print 'debit , credit *****', (debit, credit)
            move.post()
            
            for aa in temp_aux:
                if aa.get('analytic_id') and aa.get('move_id'):
                    self._cr.execute('update account_move_line set analytic_account_id=%s where id=%s', (aa.get('analytic_id'), aa.get('move_id')))

        self._log_event()
        return True
    
    @api.multi
    def invoice_validate(self):
        res = super(account_invoice, self).invoice_validate()
        self.number = self.internal_number
        return res

account_invoice()

#-----------------------------------
#    Inherit - Plan instance
#-----------------------------------
class aa_plan_instance(osv.osv):
    _inherit = "account.analytic.plan.instance"
    _description = "Analytic Instance"

    _columns = {

    }
    
    def compute_percent(self, cr, uid, ids, value):
        suma = 0
        if ids:
            obj = self.browse(cr, uid, ids[0])
            for line in obj.account_ids:
                suma += line.rate
        for acc in value:
                if acc[2] and acc[2].get('rate'):
                    suma += acc[2].get('rate')
        
        print "suma: ", suma
        
        if not int(suma) == 100.0:
            print "suma: ", suma
            return False
        return True

    def create(self, cr, uid, vals, context=None):
        if 'account_ids' in vals and vals.get('account_ids'):
            suma = 0
            for acc in vals.get('account_ids'):
                if acc[2] and acc[2].get('rate'):
                    suma += acc[2].get('rate')
            
            print "suma: ", suma
            
            if not int(suma) == 100.0:
                print "suma: ", suma
                raise except_orm(_('Error!'), _('La sumatoria de los porcientos debe ser igual a 100.'))
        return super(aa_plan_instance, self).create(cr, uid, vals, context=context)
    
    def write(self, cr, uid, ids, vals, context=None):
        if 'account_ids' in vals and vals.get('account_ids'):
            valid = self.compute_percent(cr, uid, ids, vals.get('account_ids'))
            if not valid:
                raise except_orm(_('Error!'), _('La sumatoria de los porcientos debe ser igual a 100.'))
        return super(aa_plan_instance, self).write(cr, uid, ids, vals, context=None)
    
aa_plan_instance()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
