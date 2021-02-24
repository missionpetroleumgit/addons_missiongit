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

from openerp import api, fields, models
from openerp.tools.translate import _
from openerp.exceptions import except_orm, Warning, RedirectWarning
import base64
import StringIO
from string import upper
from time import mktime
from datetime import datetime
import unicodedata
from openerp.tools import float_compare
from openerp import workflow
import time


def delete_ascii(s):
    s = ''.join((c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn'))
    return s


class account_voucher(models.Model):
    _inherit = 'account.voucher'

    account_bank_id = fields.Many2one('res.partner.bank', 'Account Bank')
    bank_statement_line_ids = fields.One2many(
        'account.bank.statement.line', 'voucher_id', string="Statement Lines")
    state = fields.Selection(
        [('draft', 'Draft'),
         ('cancel', 'Cancelled'),
         ('proforma', 'Pro-forma'),
         ('posted', 'Posted'),
         ('reconcile', 'Reconcile')
         ], 'Status', readonly=True, track_visibility='onchange', copy=False, default='draft',
        help=" * The 'Draft' status is used when a user is encoding a new and unconfirmed Voucher.\n"
             " * The 'Pro-forma' status is used when the voucher does not have a voucher number.\n"
             " * The 'Posted' status is used when user create voucher,a voucher number is generated and voucher entries are created in account.\n"
             " * The 'Reconcile' status is used when user reconlice the voucher with bank statement.\n"
             " * The 'Cancelled' status is used when user cancel voucher.")
    check = fields.Boolean('Es beneficiario')
    benef = fields.Char('Cambiar beneficiario ?')
    is_group = fields.Boolean('Reporte Agrupado', help="Marcar esta opcion si quieren que en el reporte salga agrupado por cuenta los asientos")
    check_book_id = fields.Many2one('account.checkbook', 'Talonario de cheques')
    is_check = fields.Boolean("Es cheque ?")
    electronic_transfer_ref = fields.Char('N° Transferencia', size=128)

    @api.onchange('account_bank_id')
    def onchange_account_bank_id(self):
        res = dict()
        accounts = [pba.id for pba in self.env.user.company_id.partner_id.bank_ids]
        res['domain'] = {'account_bank_id': [('id', 'in', accounts)]}
        return res

    @api.multi
    def action_reconcile(self):
        self.write({ 'state' : 'reconcile' })

    @api.multi
    def action_back_posted(self):
        self.write({ 'state' : 'posted' })

    @api.multi
    def proforma_voucher(self):
        checkbook = self.env['account.checkbook']
        res = super(account_voucher, self).proforma_voucher()
        for rec in self:
            if rec.type in ('payment', 'advance') and not rec.is_etransfer:
                rec.no_cheque = checkbook.default_filling(rec.check_book_id.filling, rec.check_book_id.actual_number)
                checkbook.actualizar_consecutivo(rec.check_book_id.id)
                # list_checkb = self.env['account.checkbook'].search([('account_bank_id', '=', rec.account_bank_id.id)])
                # exist_checkbook = False
                # for check_b in list_checkb:
                #     temp = '000000'
                #     my_number = str(check_b.actual_number)
                #     self.number = temp[len(my_number):] + my_number
                #     exist_checkbook = True
                # if exist_checkbook:
                #     check_b.actual_number = int(check_b.actual_number) + 1
                # else:
                #     raise except_orm(_('¡¡ Error !!'), _("La cuenta bancaria debe estar asociado a una chequera."))

        return res

    def to_string(self, value):

        convert = str(round(value, 2))
        decimales = convert[convert.index('.'):len(convert)]
        if len(decimales) == 2:
            convert += '0'
        return convert

    @api.v7
    def voucher_move_line_create(self, cr, uid, voucher_id, line_total, move_id, company_currency, current_currency, context=None):
        '''
        Create one account move line, on the given account move, per voucher line where amount is not 0.0.
        It returns Tuple with tot_line what is total of difference between debit and credit and
        a list of lists with ids to be reconciled with this format (total_deb_cred,list_of_lists).

        :param voucher_id: Voucher id what we are working with
        :param line_total: Amount of the first line, which correspond to the amount we should totally split among all voucher lines.
        :param move_id: Account move wher those lines will be joined.
        :param company_currency: id of currency of the company to which the voucher belong
        :param current_currency: id of currency of the voucher
        :return: Tuple build as (remaining amount not allocated on voucher lines, list of account_move_line created in this method)
        :rtype: tuple(float, list of int)
        '''
        if context is None:
            context = {}
        move_line_obj = self.pool.get('account.move.line')
        currency_obj = self.pool.get('res.currency')
        tax_obj = self.pool.get('account.tax')
        tot_line = line_total
        rec_lst_ids = []

        date = self.read(cr, uid, [voucher_id], ['date'], context=context)[0]['date']
        ctx = context.copy()
        ctx.update({'date': date})
        voucher = self.pool.get('account.voucher').browse(cr, uid, voucher_id, context=ctx)
        voucher_currency = voucher.journal_id.currency or voucher.company_id.currency_id
        ctx.update({
            'voucher_special_currency_rate': voucher_currency.rate * voucher.payment_rate ,
            'voucher_special_currency': voucher.payment_rate_currency_id and voucher.payment_rate_currency_id.id or False,})
        prec = self.pool.get('decimal.precision').precision_get(cr, uid, 'Account')
        voucher_ref = ''
        for line in voucher.line_ids:
            #create one move line per voucher line where amount is not 0.0
            # AND (second part of the clause) only if the original move line was not having debit = credit = 0 (which is a legal value)
            if not line.amount and not (line.move_line_id and not float_compare(line.move_line_id.debit, line.move_line_id.credit, precision_digits=prec) and not float_compare(line.move_line_id.debit, 0.0, precision_digits=prec)):
                continue
            # convert the amount set on the voucher line into the currency of the voucher's company
            # this calls res_curreny.compute() with the right context, so that it will take either the rate on the voucher if it is relevant or will use the default behaviour
            amount = self._convert_amount(cr, uid, line.untax_amount or line.amount, voucher.id, context=ctx)
            # if the amount encoded in voucher is equal to the amount unreconciled, we need to compute the
            # currency rate difference
            if voucher.is_check:
                voucher_ref = voucher.no_cheque
            if voucher.is_etransfer:
                voucher_ref = voucher.electronic_transfer_ref
            if line.amount == line.amount_unreconciled:
                if not line.move_line_id:
                    raise except_orm(_('Wrong voucher line'),_("The invoice you are willing to pay is not valid anymore."))
                sign = line.type =='dr' and -1 or 1
                currency_rate_difference = sign * (line.move_line_id.amount_residual - amount)
            else:
                currency_rate_difference = 0.0
            move_line = {
                'journal_id': voucher.journal_id.id,
                'period_id': voucher.period_id.id,
                'name': line.name or '/',
                'account_id': line.account_id.id,
                'move_id': move_id,
                'partner_id': voucher.partner_id.id,
                'currency_id': line.move_line_id and (company_currency <> line.move_line_id.currency_id.id and line.move_line_id.currency_id.id) or False,
                'analytic_account_id': line.account_analytic_id and line.account_analytic_id.id or False,
                'quantity': 1,
                'credit': 0.0,
                'debit': 0.0,
                'date': voucher.date,
                'other_ref': line.invoice or '/',
                'no_cheque': voucher_ref or '/'
            }
            if amount < 0:
                amount = -amount
                if line.type == 'dr':
                    line.type = 'cr'
                else:
                    line.type = 'dr'

            if (line.type=='dr'):
                tot_line += amount
                move_line['debit'] = amount
            else:
                tot_line -= amount
                move_line['credit'] = amount

            if voucher.tax_id and voucher.type in ('sale', 'purchase'):
                move_line.update({
                    'account_tax_id': voucher.tax_id.id,
                })

            # compute the amount in foreign currency
            foreign_currency_diff = 0.0
            amount_currency = False
            if line.move_line_id:
                # We want to set it on the account move line as soon as the original line had a foreign currency
                if line.move_line_id.currency_id and line.move_line_id.currency_id.id != company_currency:
                    # we compute the amount in that foreign currency.
                    if line.move_line_id.currency_id.id == current_currency:
                        # if the voucher and the voucher line share the same currency, there is no computation to do
                        sign = (move_line['debit'] - move_line['credit']) < 0 and -1 or 1
                        amount_currency = sign * (line.amount)
                    else:
                        # if the rate is specified on the voucher, it will be used thanks to the special keys in the context
                        # otherwise we use the rates of the system
                        amount_currency = currency_obj.compute(cr, uid, company_currency, line.move_line_id.currency_id.id, move_line['debit']-move_line['credit'], context=ctx)
                if line.amount == line.amount_unreconciled:
                    foreign_currency_diff = line.move_line_id.amount_residual_currency - abs(amount_currency)

            move_line['amount_currency'] = amount_currency
            voucher_line = move_line_obj.create(cr, uid, move_line)
            rec_ids = [voucher_line, line.move_line_id.id]

            if not currency_obj.is_zero(cr, uid, voucher.company_id.currency_id, currency_rate_difference):
                # Change difference entry in company currency
                exch_lines = self._get_exchange_lines(cr, uid, line, move_id, currency_rate_difference, company_currency, current_currency, context=context)
                new_id = move_line_obj.create(cr, uid, exch_lines[0],context)
                move_line_obj.create(cr, uid, exch_lines[1], context)
                rec_ids.append(new_id)

            if line.move_line_id and line.move_line_id.currency_id and not currency_obj.is_zero(cr, uid, line.move_line_id.currency_id, foreign_currency_diff):
                # Change difference entry in voucher currency
                move_line_foreign_currency = {
                    'journal_id': line.voucher_id.journal_id.id,
                    'period_id': line.voucher_id.period_id.id,
                    'name': _('change')+': '+(line.name or '/'),
                    'account_id': line.account_id.id,
                    'move_id': move_id,
                    'partner_id': line.voucher_id.partner_id.id,
                    'currency_id': line.move_line_id.currency_id.id,
                    'amount_currency': -1 * foreign_currency_diff,
                    'quantity': 1,
                    'credit': 0.0,
                    'debit': 0.0,
                    'date': line.voucher_id.date,
                    'other_ref': line.invoice or '/',
                    'no_cheque': voucher_ref or '/'
                }
                new_id = move_line_obj.create(cr, uid, move_line_foreign_currency, context=context)
                rec_ids.append(new_id)
            if line.move_line_id.id:
                rec_lst_ids.append(rec_ids)
        return (tot_line, rec_lst_ids)

    @api.v7
    def first_move_line_get(self, cr, uid, voucher_id, move_id, company_currency, current_currency, context=None):
        res = super(account_voucher, self).first_move_line_get(cr, uid, voucher_id, move_id, company_currency, current_currency, context)
        voucher = self.pool.get('account.voucher').browse(cr, uid, voucher_id, context)
        res.update({'no_cheque': voucher.no_cheque})
        return res

    # @api.v7
    # def voucher_move_line_create(self, cr, uid, voucher_id, line_total, move_id, company_currency, current_currency, context=None):
    #     res = super(account_voucher, self).voucher_move_line_create(cr, uid, voucher_id, line_total, move_id, company_currency, current_currency, context)
    #     move_line = self.pool.get('account.move.line')
    #     voucher = self.browse(cr, uid, voucher_id, context)
    #     move_line.write(cr, uid, res[1][0], {'no_cheque': voucher.no_cheque})
    #     return res

account_voucher()

# class hr_payslip(models.Model):
#     _inherit = 'hr.payslip'
#  
#     @api.multi
#     def onchange_employee_id(self, date_from, date_to, employee_id, contract_id):
#         res = super(hr_payslip, self).onchange_employee_id(date_from, date_to, employee_id, contract_id)
#  
#         if contract_id:
#             rec_att = self.env['hr.attendance'].search([('name', '>', date_from), 
#                                 ('name', '<', date_to), ('action', '=', 'sign_out')])
# #             attendances = []
#             days = hours = 0.0
#             for att in rec_att:
#                 hours += att.worked_hours
#                 days += 1
#             attendances = {
#                      'name': _("Normal Working Days paid at 100%"),
#                      'code': 'Desde ' + str(date_from) + ' y hasta el ' + str(date_to),
#                      'contract_id': contract_id or False,
#                      'sequence': 1,
#                      'number_of_days': days,
#                      'number_of_hours': hours,
#                 }
# #                 attendances.append((0, 0, attendance))
#             res['value']['worked_days_line_ids'] = [(0, 0, attendances)]
#             print 'res', res
#         return res
#      
# hr_payslip()


# class account_voucher_line(models.Model):
#     _inherit = 'account.voucher.line'
#
#     invoice = fields.Char('Factura', related='move_line_id.invoice.number_reem')


class account_move_line(models.Model):
    _inherit = 'account.move.line'

    other_ref = fields.Char('Ref 2')
    no_cheque = fields.Char('No. Cheque')
    benef = fields.Char('Beneficiario')

    @api.v7
    def reconcile(self, cr, uid, ids, type='auto', writeoff_acc_id=False, writeoff_period_id=False, writeoff_journal_id=False, context=None):
        account_obj = self.pool.get('account.account')
        move_obj = self.pool.get('account.move')
        move_rec_obj = self.pool.get('account.move.reconcile')
        partner_obj = self.pool.get('res.partner')
        currency_obj = self.pool.get('res.currency')
        lines = self.browse(cr, uid, ids, context=context)
        unrec_lines = filter(lambda x: not x['reconcile_id'], lines)
        credit = debit = 0.0
        currency = 0.0
        account_id = False
        partner_id = False
        if context is None:
            context = {}
        company_list = []
        for line in lines:
            if company_list and not line.company_id.id in company_list:
                raise except_orm(_('Warning!'), _('To reconcile the entries company should be the same for all entries.'))
            company_list.append(line.company_id.id)
        for line in unrec_lines:
            if line.state <> 'valid':
                raise except_orm(_('Error!'),
                        _('Entry "%s" is not valid !') % line.name)
            credit += line['credit']
            debit += line['debit']
            currency += line['amount_currency'] or 0.0
            account_id = line['account_id']['id']
            partner_id = (line['partner_id'] and line['partner_id']['id']) or False
        writeoff = debit - credit

        # Ifdate_p in context => take this date
        if context.has_key('date_p') and context['date_p']:
            date=context['date_p']
        else:
            date = time.strftime('%Y-%m-%d')

        cr.execute('SELECT account_id, reconcile_id '\
                   'FROM account_move_line '\
                   'WHERE id IN %s '\
                   'GROUP BY account_id,reconcile_id',
                   (tuple(ids), ))
        r = cr.fetchall()
        #TODO: move this check to a constraint in the account_move_reconcile object
        #Comentado para poder conciliar facturas con cuentas diferentes, Ramses W. Pena-o2s
        # if len(r) != 1:
        #     raise osv.except_osv(_('Error'), _('Entries are not of the same account or already reconciled ! '))
        # if not unrec_lines:
        #     raise osv.except_osv(_('Error!'), _('Entry is already reconciled.'))
        account = account_obj.browse(cr, uid, account_id, context=context)
        if not account.reconcile:
            raise except_orm(_('Error'), _('The account is not defined to be reconciled !'))
        if r[0][1] != None:
            raise except_orm(_('Error!'), _('Some entries are already reconciled.'))

        if (not currency_obj.is_zero(cr, uid, account.company_id.currency_id, writeoff)) or \
           (account.currency_id and (not currency_obj.is_zero(cr, uid, account.currency_id, currency))):
            if not writeoff_acc_id:
                raise except_orm(_('Warning!'), _('You have to provide an account for the write off/exchange difference entry.'))
            if writeoff > 0:
                debit = writeoff
                credit = 0.0
                self_credit = writeoff
                self_debit = 0.0
            else:
                debit = 0.0
                credit = -writeoff
                self_credit = 0.0
                self_debit = -writeoff
            # If comment exist in context, take it
            if 'comment' in context and context['comment']:
                libelle = context['comment']
            else:
                libelle = _('Write-Off')

            cur_obj = self.pool.get('res.currency')
            cur_id = False
            amount_currency_writeoff = 0.0
            if context.get('company_currency_id',False) != context.get('currency_id',False):
                cur_id = context.get('currency_id',False)
                for line in unrec_lines:
                    if line.currency_id and line.currency_id.id == context.get('currency_id',False):
                        amount_currency_writeoff += line.amount_currency
                    else:
                        tmp_amount = cur_obj.compute(cr, uid, line.account_id.company_id.currency_id.id, context.get('currency_id',False), abs(line.debit-line.credit), context={'date': line.date})
                        amount_currency_writeoff += (line.debit > 0) and tmp_amount or -tmp_amount

            writeoff_lines = [
                (0, 0, {
                    'name': libelle,
                    'debit': self_debit,
                    'credit': self_credit,
                    'account_id': account_id,
                    'date': date,
                    'partner_id': partner_id,
                    'currency_id': cur_id or (account.currency_id.id or False),
                    'amount_currency': amount_currency_writeoff and -1 * amount_currency_writeoff or (account.currency_id.id and -1 * currency or 0.0)
                }),
                (0, 0, {
                    'name': libelle,
                    'debit': debit,
                    'credit': credit,
                    'account_id': writeoff_acc_id,
                    'analytic_account_id': context.get('analytic_id', False),
                    'date': date,
                    'partner_id': partner_id,
                    'currency_id': cur_id or (account.currency_id.id or False),
                    'amount_currency': amount_currency_writeoff and amount_currency_writeoff or (account.currency_id.id and currency or 0.0)
                })
            ]

            writeoff_move_id = move_obj.create(cr, uid, {
                'period_id': writeoff_period_id,
                'journal_id': writeoff_journal_id,
                'date':date,
                'state': 'draft',
                'line_id': writeoff_lines
            })

            writeoff_line_ids = self.search(cr, uid, [('move_id', '=', writeoff_move_id), ('account_id', '=', account_id)])
            if account_id == writeoff_acc_id:
                writeoff_line_ids = [writeoff_line_ids[1]]
            ids += writeoff_line_ids

        # marking the lines as reconciled does not change their validity, so there is no need
        # to revalidate their moves completely.
        reconcile_context = dict(context, novalidate=True)
        r_id = move_rec_obj.create(cr, uid, {
            'type': type,
            'line_id': map(lambda x: (4, x, False), ids),
            'line_partial_ids': map(lambda x: (3, x, False), ids)
        }, context=reconcile_context)
        # the id of the move.reconcile is written in the move.line (self) by the create method above
        # because of the way the line_id are defined: (4, x, False)
        for id in ids:
            workflow.trg_trigger(uid, 'account.move.line', id, cr)

        if lines and lines[0]:
            partner_id = lines[0].partner_id and lines[0].partner_id.id or False
            if partner_id and not partner_obj.has_something_to_reconcile(cr, uid, partner_id, context=context):
                partner_obj.mark_as_reconciled(cr, uid, [partner_id], context=context)
        return r_id
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
