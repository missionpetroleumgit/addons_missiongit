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
#from openerp.osv import fields, osv
from openerp import models, fields, api
from dateutil import parser
from dateutil.relativedelta import relativedelta
from openerp.exceptions import except_orm

# BEGIN COMMON

# END COMMON
class account_invoice(models.Model):
    _inherit = 'account.invoice'
    _description = 'Invoice'
    
    is_cchica = fields.Boolean('C.Chica ?', help="Marque esta opcion si es una factura de caja chica")
    is_tarjet = fields.Boolean('Tarjetas ?', help="Marque esta opcion si es una factura de tarjeta que asume retencion")
    is_asum = fields.Boolean('Asume Ret ?', help="Marque esta opcion si la empresa asume la retención")
    is_importa = fields.Boolean('Importacion', help="Indica si la factura es de tipo importacion esta no me afecta al ats")
    account_retiva = fields.Many2one('account.account', 'Cuenta Ret Iva/Renta', domain="[('type','!=','view')]", help="Escoger la cuenta para iva retenido que se asumira")
    #'account_retrenta': fields.many2one('account.account', 'Cuenta Ret Renta', domain="[('type','!=','view')]", help="Escoger la cuenta para renta retenida que se asumira"),

    _defaults = {
        'is_cchica' : lambda * a: False,
        'is_tarjet' : lambda * a: False,
    }

    # JJM 2018-02-28 comento siguiente metodo repetido en bit_point_of_sale
#     @api.multi
#     def action_move_create(self):
#         """ Creates invoice related analytics and financial move lines """
#         account_invoice_tax = self.env['account.invoice.tax']
#         account_move = self.env['account.move']
#
#
#         for inv in self:
#             if not inv.journal_id.sequence_id:
#                 raise except_orm(_('Error!'), _('Please define sequence on the journal related to this invoice.'))
#             if not inv.invoice_line:
#                 raise except_orm(_('No Invoice Lines!'), _('Please create some invoice lines.'))
#             if inv.move_id:
#                 continue
#
#             ctx = dict(self._context, lang=inv.partner_id.lang)
#
#             if not inv.date_invoice:
#                 inv.with_context(ctx).write({'date_invoice': fields.Date.context_today(self)})
#             date_invoice = inv.date_invoice
#
#             company_currency = inv.company_id.currency_id
#             # create the analytical lines, one move line per invoice line
#             iml = inv._get_analytic_lines()
#             # check if taxes are all computed
#             compute_taxes = account_invoice_tax.compute(inv.with_context(lang=inv.partner_id.lang))
#             inv.check_tax_lines(compute_taxes)
#
#             # I disabled the check_total feature
#             if self.env['res.users'].has_group('account.group_supplier_inv_check_total'):
#                 if inv.type in ('in_invoice', 'in_refund') and abs(inv.check_total - inv.amount_total) >= (inv.currency_id.rounding / 2.0):
#                     raise except_orm(_('Bad Total!'), _('Please verify the price of the invoice!\nThe encoded total does not match the computed total.'))
#
#             if inv.payment_term:
#                 total_fixed = total_percent = 0
#                 for line in inv.payment_term.line_ids:
#                     if line.value == 'fixed':
#                         total_fixed += line.value_amount
#                     if line.value == 'procent':
#                         total_percent += line.value_amount
#                 total_fixed = (total_fixed * 100) / (inv.amount_total or 1.0)
#                 if (total_fixed + total_percent) > 100:
#                     raise except_orm(_('Error!'), _("Cannot create the invoice.\nThe related payment term is probably misconfigured as it gives a computed amount greater than the total invoiced amount. In order to avoid rounding issues, the latest line of your payment term must be of type 'balance'."))
#
#             # one move line per tax line
#             iml += account_invoice_tax.move_line_get(inv.id)
#
#             if inv.type in ('in_invoice', 'in_refund'):
#                 ref = inv.reference
#             else:
#                 ref = inv.number
#
#             diff_currency = inv.currency_id != company_currency
#             # create one move line for the total and possibly adjust the other lines amount
#             total, total_currency, iml = inv.with_context(ctx).compute_invoice_totals(company_currency, ref, iml)
#
#             name = inv.supplier_invoice_number or inv.name or '/'
#             totlines = []
#             if inv.payment_term:
#                 totlines = inv.with_context(ctx).payment_term.compute(total, date_invoice)[0]
#             if totlines:
#                 res_amount_currency = total_currency
#                 ctx['date'] = date_invoice
#                 for i, t in enumerate(totlines):
#                     if inv.currency_id != company_currency:
#                         amount_currency = company_currency.with_context(ctx).compute(t[1], inv.currency_id)
#                     else:
#                         amount_currency = False
#
#                     # last line: add the diff
#                     res_amount_currency -= amount_currency or 0
#                     if i + 1 == len(totlines):
#                         amount_currency += res_amount_currency
#
#                     iml.append({
#                         'type': 'dest',
#                         'name': name,
#                         'price': t[1],
#                         'account_id': inv.account_id.id,
#                         'date_maturity': t[0],
#                         'amount_currency': diff_currency and amount_currency,
#                         'currency_id': diff_currency and inv.currency_id.id,
#                         'ref': ref,
#                     })
#             else:
#                 iml.append({
#                     'type': 'dest',
#                     'name': name,
#                     'price': total,
#                     'account_id': inv.account_id.id,
#                     'date_maturity': inv.date_due,
#                     'amount_currency': diff_currency and total_currency,
#                     'currency_id': diff_currency and inv.currency_id.id,
#                     'ref': ref
#                 })
#
#             date = date_invoice
#
#             part = self.env['res.partner']._find_accounting_partner(inv.partner_id)
#
#             line = [(0, 0, self.line_get_convert(l, part.id, date)) for l in iml]
#             line = inv.group_lines(iml, line)
#
#             journal = inv.journal_id.with_context(ctx)
#             if journal.centralisation:
#                 raise except_orm(_('User Error!'),
#                         _('You cannot create an invoice on a centralized journal. Uncheck the centralized counterpart box in the related journal from the configuration menu.'))
#
#             line = inv.finalize_invoice_move_lines(line)
# #CSV 11-05-2017 PARA HACER ASIENTO ASUME RETENCION
#             print "IS CAJA CHICA O TARJETA", inv.is_cchica
#             print "IS ASUME O TARJETA", inv.is_asum
#             print "Cuenta Asume Iva/Renta ID", inv.account_retiva.id
#             print "Cuenta Asume Iva/Renta", inv.account_retiva.name
#             if inv.is_asum and inv.is_cchica or inv.is_asum and inv.is_tarjet:
#                 print "ID FACTURA", inv.id
#                 imp_ret_id = self.env['account.invoice.tax'].search([('invoice_id', '=', inv.id)])
#                 print "ID IMPUESTOS", imp_ret_id
#                 # imp_ret_obj = self.env['account.invoice.tax'].browse([imp_ret_id[id]])
#                 # print "ID IMPUESTOS OBJ", imp_ret_obj
#                 valor_asum = 0
#                 for imp_as in imp_ret_id:
#                     print "IMP", imp_as
#                     print "VALOR RET", imp_as.name
#                     if imp_as.amount < 0:
#                         valor_asum += abs(imp_as.amount)
#                 print "VALOR RETENIDO", valor_asum
#                 #raise except_orm(_('No Invoice Lines!'), _('Please create some invoice lines.'))
#                 dict_line = {
#                     'account_id': inv.account_retiva.id,
#                     'date': inv.date_invoice,
#                     'name': 'Retención Asumida',
#                     'partner_id': inv.partner_id.id,
#                     'debit': valor_asum
#                 }
#                 line.append((0, 0, dict_line))
#
#             move_vals = {
#                 'ref': inv.reference or inv.name,
#                 'line_id': line,
#                 'journal_id': journal.id,
#                 'date': inv.date_invoice,
#                 'narration': inv.comment,
#                 'company_id': inv.company_id.id,
#             }
#             ctx['company_id'] = inv.company_id.id
#             period = inv.period_id
#             if not period:
#                 period = period.with_context(ctx).find(date_invoice)[:1]
#             if period:
#                 move_vals['period_id'] = period.id
#                 for i in line:
#                     i[2]['period_id'] = period.id
#
#             ctx['invoice'] = inv
#             ctx_nolang = ctx.copy()
#             ctx_nolang.pop('lang', None)
#             move = account_move.with_context(ctx_nolang).create(move_vals)
#
#             # make the invoice point to that move
#             vals = {
#                 'move_id': move.id,
#                 'period_id': period.id,
#                 'move_name': move.name,
#             }
#             inv.with_context(ctx).write(vals)
#             # Pass invoice in context in method post: used if you want to get the same
#             # account move reference when creating the same invoice after a cancelled one:
# #CSV 11-05-2017 PARA HACER ASIENTO ASUME RETENCION
#             if inv.is_asum and inv.is_cchica or inv.is_asum and inv.is_tarjet:
#                 print "ENTRA A LA ACTUALIZAR LINEA"
#                 for l in move.line_id:
#                     print "VALOR ACTUALIZAR", round(valor_asum+inv.amount_total,2)
#                     print "ID MOV", l.id
#                     print "CUENTA FACTURA ID", inv.account_id.id
#                     print "CUENTA MOVI ID", l.account_id.id
#                     print "ID ASIENTO", l.move_id.id
#                     #raise except_orm(_('No Invoice Lines!'), _('Please create some invoice lines.'))
#                     if l.account_id.id == inv.account_id.id:
#                         print "ENTRA A ACTUALIZAR"
#                         #raise except_orm(_('No Invoice Lines!'), _('Please create some invoice lines.'))
#                         self._cr.execute('update account_move_line set credit=%s where id =%s and account_id=%s', (round(valor_asum+inv.amount_total,2), l.id, inv.account_id.id))
#                 self._cr.execute('update account_move set state=%s where id =%s', ('posted', l.move_id.id))
# #CSV 11-05-2017 PARA HACER ASIENTO ASUME RETENCION
#             if not inv.is_asum:
#                 move.post()
#
#         self._log_event()
#         return True

account_invoice()
