# -*- coding: utf-8 -*-
#############################
#  Purchase for restaurants #
#############################
from openerp import models, fields, api, _
from openerp.exceptions import except_orm
import openerp.addons.decimal_precision as dp


class account_voucher(models.Model):
    _inherit = 'account.voucher'

    @api.model
    def _set_advance_account(self):
        acc = self.env['account.account'].search([('name', 'ilike', 'anticipo'), ('type', '=', 'receivable')])
        if self.env.user.company_id.advance_account_id:
            acc = self.env.user.company_id.advance_account_id.id
        return acc

    @api.onchange('check_book_id')
    def onchange_check_secuencial(self):
        if self.check_book_id:
            self.no_cheque = self.check_book_id.actual_number

    @api.onchange('account_bank_id')
    def onchange_account_bank(self):
        if self.account_bank_id and self.type == 'payment':
            if self.account_bank_id.journal_id:
                self.journal_id = self.account_bank_id.journal_id

    advance_account_id = fields.Many2one('account.account', 'Cuenta de Anticipo', default=_set_advance_account)
    type = fields.Selection(selection_add=[('advance', 'Anticipo'), ('some_pays', 'Pago Varios')])
    crossing_accounts = fields.Boolean('Es cruce de cuentas?')
    crossing_account_id = fields.Many2one('account.account', 'Cuenta a cruzar')
    purchase_id = fields.Many2one('purchase.order', 'Orden de compra')
    no_cheque = fields.Char('No. Cheque')
    account_pays = fields.One2many('account.pay.some', 'voucher_id', 'Pagos')
    grouped_report = fields.Boolean('Agrupar reporte por cuenta')

    @api.v7
    def onchange_line_ids(self, cr, uid, ids, line_dr_ids, line_cr_ids, amount, voucher_currency, type, context=None):
        res = super(account_voucher, self).onchange_line_ids(cr, uid, ids, line_dr_ids, line_cr_ids, amount, voucher_currency, type, context)
        line_dr_ids = self.resolve_2many_commands(cr, uid, 'line_dr_ids', line_dr_ids, ['amount'], context)
        voucher_line = ()
        move_line = self.pool.get('account.move.line')
        amount = 0
        if type == 'payment':
            for v_line in line_dr_ids:
                if not v_line.get('id'):
                    line_id = self.pool.get('account.voucher.line').browse(cr, uid, v_line['move_line_id'], context=context)
                    for voucher_line in self.browse(cr, uid, line_id, context=context).ids:
                            amount += v_line.get('amount')
                    if v_line.get('amount') == v_line.get('amount_unreconciled'):
                        v_line.setdefault('amount_reconcile', True)
                    if v_line.get('amount') > v_line.get('amount_unreconciled'):
                        raise except_orm('ERROR DE USUARIO!', 'El valor a pagar no puede ser mayor al de la factura')
                if not v_line.get('move_line_id'):
                    line_id = self.pool.get('account.voucher.line').browse(cr, uid, v_line['id'], context=context)
                    for voucher_line in self.browse(cr, uid, line_id, context=context).ids:
                            amount += v_line.get('amount')
                    if v_line.get('amount') == voucher_line.amount_unreconciled:
                        v_line.setdefault('amount_reconcile', True)
                    if v_line.get('amount') > voucher_line.amount_unreconciled:
                        raise except_orm('ERROR DE USUARIO!', 'El valor a pagar no puede ser mayor al de la factura')
            res['value'].update({'amount': amount})
        return res

    @api.model
    def default_get(self, fields_list):
        res = super(account_voucher, self).default_get(fields_list)
        if 'type' in self._context and self._context['type'] == 'advance':
            res.update({'type': self._context['type']})
        return res

    # CSV:24-04-2018: AUMENTO PARA PAGO VARIAS CUENTAS
    @api.one
    def validate_advance_some(self):
        # no = self.env['ir.sequence'].search([('code', '=', 'advances'), ('company_id', '=', self.company_id.id)])
        # no = self.env['ir.sequence'].get('advances', context=self._context)
        if not self.number:
            no = self.env['ir.sequence'].next_by_id(self.journal_id.sequence_id.id)
            if not no:
                raise except_orm('Error!', 'Defina una secuencia de anticipo para la compania %s, el codigo debe ser advances' % self.company_id.name)
            self.number = no
        move = self.create_move_some()
        checkbook = self.env['account.checkbook']
        self.no_cheque = checkbook.default_filling(self.check_book_id.filling, self.check_book_id.actual_number)
        checkbook.actualizar_consecutivo(self.check_book_id.id, context=None)

        self.move_id = move
        self.state = 'posted'

    def create_move_some(self):
        total = 0
        move = self.env['account.move']
        line = self.env['account.move.line']
        journal = self.env['account.journal'].search([('code', '=', 'DANT'), ('company_id', '=', self.company_id.id)])
        if not journal:
            raise except_orm('Error!', 'No existe un diario de anticipo con el codigo DANT')
        number = str(self.journal_id.code + '/' + self.number)
        move_obj = move.create({'journal_id': journal.id, 'period_id': self.period_id.id, 'date': self.date,
                                'company_id': self.company_id.id, 'ref': number})
        for pagos in self.account_pays:
            total += pagos.amount
            if self.is_check:
                line.create({'name': number, 'partner_id': self.partner_id.id, 'account_id': pagos.account_id.id,
                             'credit': 0.00, 'debit': pagos.amount, 'move_id': move_obj.id,'no_cheque':self.no_cheque,'benef':self.benef})
                line.write({'ref': self.reference})
                line2 = line.create({'name': number, 'account_id': self.journal_id.default_credit_account_id.id,
                                     'credit': pagos.amount, 'debit': 0.00, 'move_id': move_obj.id,'no_cheque':self.no_cheque,'benef':self.benef})
                line2.write({'ref': self.reference})
            elif self.is_etransfer:
                line.create({'name': number, 'partner_id': self.partner_id.id, 'account_id': pagos.account_id.id,
                             'credit': 0.00, 'debit': pagos.amount, 'move_id': move_obj.id, 'no_cheque': self.electronic_transfer_ref,
                             'benef': self.benef})
                line.write({'ref': self.reference})
                line2 = line.create({'name': number, 'account_id': self.journal_id.default_credit_account_id.id,
                                     'credit': pagos.amount, 'debit': 0.00, 'move_id': move_obj.id,
                                     'no_cheque': self.electronic_transfer_ref, 'benef': self.benef})
                line2.write({'ref': self.reference})
        self.amount = total
        return move_obj.id

    # @api.multi
    # def action_voucher_sent(self):
    #     ir_model_data = self.pool.get('ir.model.data')
    #     try:
    #         template_id = self.env.ref('purchase', 'email_template_edi_purchase_done', False)
    #     except ValueError:
    #         template_id = False
    #     try:
    #         compose_form_id = self.env.ref('mail.email_compose_message_wizard_form', False)
    #     except ValueError:
    #         compose_form_id = False
    #     ctx = dict(
    #             default_model='account.voucher',
    #             default_res_id=self.id,
    #             default_use_template=bool(template_id),
    #             default_template_id=template_id,
    #             default_composition_mode='comment',
    #         )
    #
    #     return {
    #         'name': _('Compose Email'),
    #         'type': 'ir.actions.act_window',
    #         'view_type': 'form',
    #         'view_mode': 'form',
    #         'res_model': 'mail.compose.message',
    #         'views': [(compose_form_id, 'form')],
    #         'view_id': compose_form_id,
    #         'target': 'new',
    #         'context': ctx,
    #     }

    def print_pay(self, cr, uid, ids, context=None):
        assert len(ids) == 1, 'This option should only be used for a single id at a time'
        return self.pool['report'].get_action(cr, uid, ids, 'bit_payment.report_check_egreso', context=context)

    @api.one
    def validate_advance(self):
        # no = self.env['ir.sequence'].search([('code', '=', 'advances'), ('company_id', '=', self.company_id.id)])
        # no = self.env['ir.sequence'].get('advances', context=self._context)
        reg_number = ''
        if not self.number:
            no = self.env['ir.sequence'].next_by_id(self.journal_id.sequence_id.id)
            if not no:
                raise except_orm('Error!', 'Defina una secuencia de anticipo para la compania %s, el codigo debe ser advances' % self.company_id.name)
            self.number = no
        if self.no_cheque:
            reg_number = self.no_cheque
        if self.electronic_transfer_ref:
            reg_number = self.electronic_transfer_ref
        move = self.create_move(reg_number)
        checkbook = self.env['account.checkbook']
        self.no_cheque = checkbook.default_filling(self.check_book_id.filling, self.check_book_id.actual_number)
        checkbook.actualizar_consecutivo(self.check_book_id.id, context=None)

        self.move_id = move
        self.state = 'posted'

    def create_move(self, no_number):
        move = self.env['account.move']
        line = self.env['account.move.line']
        journal = self.env['account.journal'].search([('code', '=', 'DANT'), ('company_id', '=', self.company_id.id)])
        if not journal:
            raise except_orm('Error!', 'No existe un diario de anticipo con el codigo DANT')
        number = str(self.journal_id.code + '/' + self.number)
        move_obj = move.create({'journal_id': journal.id, 'period_id': self.period_id.id, 'date': self.date,
                                'company_id': self.company_id.id, 'ref': number})
        line.create({'name': number, 'ref': self.reference, 'partner_id': self.partner_id.id, 'account_id': self.advance_account_id.id,
                     'credit': 0.00, 'debit': self.amount, 'move_id': move_obj.id, 'no_cheque': no_number})
        line.write({'ref': self.reference})
        line2 = line.create({'partner_id': self.partner_id.id, 'name': number, 'ref': self.reference, 'account_id': self.journal_id.default_credit_account_id.id,
                             'credit': self.amount, 'debit': 0.00, 'move_id': move_obj.id, 'no_cheque': no_number})
        line2.write({'ref': self.reference})
        return move_obj.id

    @api.one
    def cancel_advance(self):
        return self.cancel_voucher()

    @api.one
    def action_advance_draft(self):
        return self.action_cancel_draft()

    @api.v7
    def onchange_amount(self, cr, uid, ids, amount, rate, partner_id, journal_id, currency_id, ttype, date, payment_rate_currency_id, company_id,
                        crossing_accounts=False, crossing_account_id=False, context=None):
        if context is None:
            context = {}
        ctx = context.copy()
        ctx.update({'date': date})
        #read the voucher rate with the right date in the context
        currency_id = currency_id or self.pool.get('res.company').browse(cr, uid, company_id, context=ctx).currency_id.id
        voucher_rate = self.pool.get('res.currency').read(cr, uid, [currency_id], ['rate'], context=ctx)[0]['rate']
        ctx.update({
            'voucher_special_currency': payment_rate_currency_id,
            'voucher_special_currency_rate': rate * voucher_rate})
        res = self.recompute_voucher_lines(cr, uid, ids, partner_id, journal_id, amount, currency_id, ttype, date, crossing_accounts, crossing_account_id, context=ctx)
        vals = self.onchange_rate(cr, uid, ids, rate, amount, currency_id, payment_rate_currency_id, company_id, context=ctx)
        for key in vals.keys():
            res[key].update(vals[key])
        return res

    @api.v7
    def onchange_partner_id(self, cr, uid, ids, partner_id, journal_id, amount, currency_id, ttype, date, crossing_accounts=False, crossing_account_id=False, context=None):
        if not journal_id:
            return {}
        if context is None:
            context = {}
        #TODO: comment me and use me directly in the sales/purchases views
        res = self.basic_onchange_partner(cr, uid, ids, partner_id, journal_id, ttype, context=context)
        if ttype in ['sale', 'purchase']:
            return res
        ctx = context.copy()
        # not passing the payment_rate currency and the payment_rate in the context but it's ok because they are reset in recompute_payment_rate
        ctx.update({'date': date})
        vals = self.recompute_voucher_lines(cr, uid, ids, partner_id, journal_id, amount, currency_id, ttype, date, crossing_accounts, crossing_account_id, context=ctx)
        vals2 = self.recompute_payment_rate(cr, uid, ids, vals, currency_id, date, ttype, journal_id, amount, context=context)
        for key in vals.keys():
            res[key].update(vals[key])
        for key in vals2.keys():
            res[key].update(vals2[key])
        #TODO: can probably be removed now
        #TODO: onchange_partner_id() should not returns [pre_line, line_dr_ids, payment_rate...] for type sale, and not
        # [pre_line, line_cr_ids, payment_rate...] for type purchase.
        # We should definitively split account.voucher object in two and make distinct on_change functions. In the
        # meanwhile, bellow lines must be there because the fields aren't present in the view, what crashes if the
        # onchange returns a value for them
        if ttype == 'sale':
            del(res['value']['line_dr_ids'])
            del(res['value']['pre_line'])
            del(res['value']['payment_rate'])
        elif ttype == 'purchase':
            del(res['value']['line_cr_ids'])
            del(res['value']['pre_line'])
            del(res['value']['payment_rate'])
        return res

    @api.v7
    def recompute_voucher_lines(self, cr, uid, ids, partner_id, journal_id, price, currency_id, ttype, date, crossing_accounts=False, crossing_account_id=False, context=None):
        """
        Returns a dict that contains new values and context

        @param partner_id: latest value from user input for field partner_id
        @param args: other arguments
        @param context: context arguments, like lang, time zone

        @return: Returns a dict which contains new values, and context
        """
        def _remove_noise_in_o2m():
            """if the line is partially reconciled, then we must pay attention to display it only once and
                in the good o2m.
                This function returns True if the line is considered as noise and should not be displayed
            """
            if line.reconcile_partial_id:
                if currency_id == line.currency_id.id:
                    if line.amount_residual_currency <= 0:
                        return True
                else:
                    if line.amount_residual <= 0:
                        return True
            return False

        if context is None:
            context = {}
        context_multi_currency = context.copy()

        currency_pool = self.pool.get('res.currency')
        move_line_pool = self.pool.get('account.move.line')
        partner_pool = self.pool.get('res.partner')
        journal_pool = self.pool.get('account.journal')
        line_pool = self.pool.get('account.voucher.line')

        #set default values
        default = {
            'value': {'line_dr_ids': [], 'line_cr_ids': [], 'pre_line': False},
        }

        # drop existing lines
        line_ids = ids and line_pool.search(cr, uid, [('voucher_id', '=', ids[0])])
        for line in line_pool.browse(cr, uid, line_ids, context=context):
            if line.type == 'cr':
                default['value']['line_cr_ids'].append((2, line.id))
            else:
                default['value']['line_dr_ids'].append((2, line.id))

        if not partner_id or not journal_id:
            return default

        journal = journal_pool.browse(cr, uid, journal_id, context=context)
        partner = partner_pool.browse(cr, uid, partner_id, context=context)
        currency_id = currency_id or journal.company_id.currency_id.id

        total_credit = 0.0
        total_debit = 0.0
        account_type = None
        if context.get('account_id'):
            account_type = self.pool['account.account'].browse(cr, uid, context['account_id'], context=context).type
        if ttype == 'payment':
            if not account_type:
                account_type = 'payable'
            total_debit = price or 0.0
        else:
            total_credit = price or 0.0
            if not account_type:
                account_type = 'receivable'

        if not context.get('move_line_ids', False):
            if ttype == 'payment':
                ids = move_line_pool.search(cr, uid, [('state','=','valid'), ('account_id.type', '=', account_type), ('reconcile_id', '=', False), ('partner_id', '=', partner_id)], context=context, order='date')
            else:
                ids = move_line_pool.search(cr, uid, [('state','=','valid'), ('account_id.type', '=', account_type), ('journal_id.code', 'in', ['DV', 'DSIN']), ('reconcile_id', '=', False), ('partner_id', '=', partner_id)], context=context, order='date')
            # if ids and account_type == 'payable':
            #     ids += move_line_pool.search(cr, uid, [('state','=','valid'), ('account_id', '=', journal.company_id.advance_account_id.id),
            #                                            ('reconcile_id', '=', False), ('partner_id', '=', partner_id)], context=context)
            # elif not ids and account_type == 'payable':
            #     ids = move_line_pool.search(cr, uid, [('state','=','valid'), ('account_id', '=', journal.company_id.advance_account_id.id),
            #                                           ('reconcile_id', '=', False), ('partner_id', '=', partner_id)], context=context)
        else:
            ids = context['move_line_ids']

        if crossing_accounts and ids:
            ids.extend(move_line_pool.search(cr, uid, [('state', '=', 'valid'), ('account_id', '=', crossing_account_id),
                                                       ('reconcile_id', '=', False), ('partner_id', '=', partner_id)], context=context))
        invoice_id = context.get('invoice_id', False)
        company_currency = journal.company_id.currency_id.id
        move_lines_found = []

        # order the lines by most old first
        # ids.reverse()
        account_move_lines = move_line_pool.browse(cr, uid, ids, context=context)

        #compute the total debit/credit and look for a matching open amount or invoice
        for line in account_move_lines:
            if _remove_noise_in_o2m():
                continue

            if invoice_id:
                if line.invoice.id == invoice_id:
                    #if the invoice linked to the voucher line is equal to the invoice_id in context
                    #then we assign the amount on that line, whatever the other voucher lines
                    move_lines_found.append(line.id)
            elif currency_id == company_currency:
                #otherwise treatments is the same but with other field names
                if line.amount_residual == price:
                    #if the amount residual is equal the amount voucher, we assign it to that voucher
                    #line, whatever the other voucher lines
                    move_lines_found.append(line.id)
                    break
                #otherwise we will split the voucher amount on each line (by most old first)
                total_credit += line.credit or 0.0
                total_debit += line.debit or 0.0
            elif currency_id == line.currency_id.id:
                if line.amount_residual_currency == price:
                    move_lines_found.append(line.id)
                    break
                total_credit += line.credit and line.amount_currency or 0.0
                total_debit += line.debit and line.amount_currency or 0.0

        remaining_amount = price
        #voucher line creation
        for line in account_move_lines:

            if _remove_noise_in_o2m():
                continue

            if line.currency_id and currency_id == line.currency_id.id:
                amount_original = abs(line.amount_currency)
                amount_unreconciled = abs(line.amount_residual_currency)
            else:
                #always use the amount booked in the company currency as the basis of the conversion into the voucher currency
                amount_original = currency_pool.compute(cr, uid, company_currency, currency_id, line.credit or line.debit or 0.0, context=context_multi_currency)
                amount_unreconciled = currency_pool.compute(cr, uid, company_currency, currency_id, abs(line.amount_residual), context=context_multi_currency)
            line_currency_id = line.currency_id and line.currency_id.id or company_currency
            rs = {
                'name':line.move_id.name,
                'type': line.credit and 'dr' or 'cr',
                'move_line_id':line.id,
                'account_id':line.account_id.id,
                'amount_original': amount_original,
                'amount': (line.id in move_lines_found) and min(abs(remaining_amount), amount_unreconciled) or 0.0,
                'date_original':line.date,
                'date_due':line.date_maturity,
                'amount_unreconciled': amount_unreconciled,
                'currency_id': line_currency_id,
            }
            remaining_amount -= rs['amount']
            #in case a corresponding move_line hasn't been found, we now try to assign the voucher amount
            #on existing invoices: we split voucher amount by most old first, but only for lines in the same currency
            if not move_lines_found:
                if currency_id == line_currency_id:
                    if line.credit:
                        amount = min(amount_unreconciled, abs(total_debit))
                        rs['amount'] = amount
                        total_debit -= amount
                    else:
                        amount = min(amount_unreconciled, abs(total_credit))
                        rs['amount'] = amount
                        total_credit -= amount

            if rs['amount_unreconciled'] == rs['amount']:
                rs['reconcile'] = True

            if rs['type'] == 'cr':
                default['value']['line_cr_ids'].append(rs)
            else:
                default['value']['line_dr_ids'].append(rs)

            if len(default['value']['line_cr_ids']) > 0:
                default['value']['pre_line'] = 1
            elif len(default['value']['line_dr_ids']) > 0:
                default['value']['pre_line'] = 1
            default['value']['writeoff_amount'] = self._compute_writeoff_amount(cr, uid, default['value']['line_dr_ids'], default['value']['line_cr_ids'], price, ttype)
        return default


    def default_filling(self, filling, value):
        str_value = str(value)
        while len(str_value) < filling:
            str_value = '0' + str_value
        return str_value

    @api.model
    def create(self, vals):
        name = '/'
        journal_pool = self.env['account.journal']
        journal = journal_pool.search([('name', '=', 'Diario General')])
        if vals.get('type') == 'receipt':
            name = self.env['ir.sequence'].next_by_code('receipt_voucher')
        else:
            if journal.id == vals.get('journal_id'):
                name = self.env['ir.sequence'].next_by_code('pay_voucher')
            else:
                name = self.env['ir.sequence'].next_by_code('bank_pay_voucher')
        vals.update({'number': name})
        return super(account_voucher, self).create(vals)


class account_pay_some(models.Model):
    _name = "account.pay.some"
    _description = "Pagos Varias Cuentas"
    _order = "id desc"

    @api.model
    def _set_advance_account(self):
        acc = self.env['account.account'].search([('name', 'ilike', 'anticipo'), ('type', '=', 'receivable')])
        if self.env.user.company_id.advance_account_id:
            acc = self.env.user.company_id.advance_account_id.id
        return acc

    account_id = fields.Many2one('account.account', 'Cuenta de Pago', default=_set_advance_account)
    amount = fields.Float('Monto', digits_compute=dp.get_precision('Account'))
    voucher_id = fields.Many2one('account.voucher', 'Pagos')


class account_voucher_line(models.Model):
    _inherit = 'account.voucher.line'

    @api.multi
    def _check_invoice_number(self):
        for record in self:
            ref = record.move_line_id.ref
            if not record.invoice:
                if record.move_line_id.invoice:
                    record.invoice = record.move_line_id.invoice.number_reem
                    break
                else:
                    if record.voucher_id.type == 'receipt':
                        if ref:
                            record.invoice = record.move_line_id.ref[39:]
                        break
                    if record.voucher_id.type == 'payment':
                        if ref:
                            record.invoice = record.move_line_id.ref[58:]
                        break

    invoice = fields.Char('Factura', compute=_check_invoice_number, readonly=False, store=True)

account_voucher_line()
