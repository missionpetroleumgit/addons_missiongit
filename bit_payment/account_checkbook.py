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

from openerp.osv import fields, osv
from openerp.tools.translate import _
from datetime import datetime
from number_to_text import Numero_a_Texto
from openerp.tools import float_is_zero


class account_checkbook(osv.osv):

    _name = 'account.checkbook'
    _description = 'Manage Checkbook'

    def _get_type(self, cr, uid, context=None):
        if context is None:
            context = {}
        return context.get('is_supplier')

    def _default_company_get(self, cr, uid, context=None):
        user = self.pool.get('res.users').browse(cr, uid, uid)
        return user.company_id.id

    _columns = {
        'name':fields.char('CheckBook Name', size=30, readonly=True,select=True,required=True,states={'draft': [('readonly', False)]}),
        'range_desde': fields.integer('Check Number Desde', size=8, readonly=True,required=True,states={'draft': [('readonly', False)]}),
        'range_hasta': fields.integer('Check Number Hasta', size=8,readonly=True, required=True,states={'draft': [('readonly', False)]}),
        'actual_number':fields.char('Next Check Number', size=8,readonly=False, required=True,states={'draft': [('readonly', False)]}),
        'account_bank_id': fields.many2one('res.partner.bank','Account Bank',readonly=True,required=True,states={'draft': [('readonly', False)]}),
        'journal_id': fields.many2one('account.journal', 'Journal', required=True, domain=[('is_allow_check','=',True)]),
        'user_id' : fields.many2one('res.users','User'),
        'change_date': fields.date('Change Date'),
        'company_id': fields.many2one('res.company', 'Compania'),
        'state':fields.selection([('draft','Draft'),('active','In Use'),('used','Used')],string='State',readonly=True),
        'filling': fields.integer('Relleno')

    }

    _order = "name"
    _defaults = {
        'state': 'draft',
        'is_supplier': _get_type,
        'company_id': _default_company_get
    }

    def default_filling(self, filling, value):
        str_value = str(value)
        while len(str_value) < filling:
            str_value = '0' + str_value
        return str_value

    def create(self, cr, uid, vals, context=None):
        if context is None:
            context = {}
        res = {}
        if 'range_desde' in vals and int(vals.get('range_desde')) == 0:
            raise osv.except_osv(_('Error !'), _('The field "Number From" must be greater than 0.!'))
        if 'range_hasta' in vals and int(vals.get('range_hasta')) == 0:
            raise osv.except_osv(_('Error !'), _('The field "Number Until" must be greater than 0.!'))
        if 'actual_number' in vals and int(vals.get('actual_number')) == 0:
            raise osv.except_osv(_('Error !'), _('The field "Next Check Number" must be greater than 0.!'))
        elif 'actual_number' in vals and int(vals.get('range_desde')) > int(vals.get('actual_number')) \
                or int(vals.get('actual_number')) > int(vals.get('range_hasta')):
            raise osv.except_osv(_('Error !'), _('The field "Next Check Number" must be greater than "Number From" and less than "Number Until".!'))
        return super(account_checkbook, self).create(cr, uid, vals, context)

    def unlink(self, cr, uid, ids, context=None):
        res= {}
        for order in self.browse(cr,uid,ids,context=context):
            if  order.state not in ('draft'):
                raise osv.except_osv(_('Error !'), _('You can drop the checkbook(s) only in  draft state !'))
                return False
        res = super(account_checkbook, self).unlink(cr, uid, ids, context)
        return res

    def actualizar_consecutivo(self, cr, uid, cb_id, context=None):
        brw_chequera = self.browse(cr, uid, cb_id)
        consecutivo = brw_chequera.actual_number
        self.write(cr, uid, cb_id, {'actual_number': int(consecutivo) + 1}, context=context)
        return consecutivo

    def onchange_hasta(self, cr, uid, ids,range_desde,range_hasta, context=None):
        res = {}
        if int(range_hasta) == 0 or int(range_hasta) < int(range_desde):
            res = {'value':{'range_hasta': 0}}
            res.update({'warning': {'title': _('Error !'),
                                    'message': _('Range hasta  must be greater than range desde')}})
        return res

    def wkf_active(self, cr, uid, ids,context=None):
        if context is None:
            context = {}
        self.write(cr, uid, ids, { 'state' : 'active' })
        return True

    def wkf_used(self, cr, uid, ids,context=None):
        self.write(cr, uid, ids, { 'state' : 'used' })
        return True

account_checkbook()


class account_check(osv.osv):
    _name = 'account.check'
    _description = 'Accounting check'
    _order = "date desc, id desc"

    def _get_currency(self, cr, uid, context=None):
        if context is None:
            context = {}
        if not context.get('is_supplier'):
            return 3
        return

    _columns = {

        'number' : fields.char('Number', required=True),
        'partner_id' : fields.many2one('res.partner', 'Partner', required=True),
        'checkbook_id' : fields.many2one('account.checkbook', 'Checkbook'),
        'amount' : fields.float('Total', required=True ),
        'currency_id' : fields.many2one('res.currency', 'Currency', required=True),
        'date' : fields.date('Date', select=True, required=True),
        'is_check' : fields.boolean('Es Cheque ?'),
        'statement_id': fields.many2one('account.bank.statement', 'Bank statement', select=True),
        'is_supplier': fields.boolean('Is supplier'),

    }

    _defaults = {
        'is_check' : False,
        'currency_id' : _get_currency
    }

    def get_number_in_letters(self, amount):
        return Numero_a_Texto(amount)

account_check()


class account_bank_statement(osv.osv):
    _inherit = 'account.bank.statement'

    def _exist_some_pay(self, cr, uid, ids, name, args, context=None):
        res = {}
        for st in self.browse(cr, uid, ids, context=context):
            some_pay = False
            for st_line in st.line_ids:
                some_pay = some_pay or st_line.amount < 0
            res[st.id] = some_pay
        return res

    def _get_valor_cheque(self, cr, uid, ids, name, args, context=None):
        val_cheque = 0.00
        res = {}
        for st in self.browse(cr, uid, ids, context=context):
            print "st.journal_id.name", st.journal_id.name
            print "st.company_id.id", st.company_id.id
            if st.journal_id.name == 'EFECTIVO':
                journal = self.pool.get('account.journal').search(cr, uid, [('name', '=', 'CHEQUE'),('company_id','=',st.company_id.id)])
                print "JOURNAL***", journal[0]
                if journal:
                    sta_che = self.pool.get('account.bank.statement').search(cr, uid, [('pos_session_id', '=', st.pos_session_id.id),('journal_id','=',journal[0])])
                    if sta_che:
                        sta_che_obj = self.pool.get('account.bank.statement').browse(cr, uid, sta_che, context)
                        val_cheque = sta_che_obj.balance_end
            res[st.id] = val_cheque
            print "val_cheque", val_cheque
        return res

    def _get_valor_deposito(self, cr, uid, ids, name, args, context=None):
        val_dep = 0.00
        res = {}
        for st in self.browse(cr, uid, ids, context=context):
            print "st.journal_id.name", st.journal_id.name
            print "st.company_id.id", st.company_id.id
            if st.journal_id.name == 'EFECTIVO':
                journal = self.pool.get('account.journal').search(cr, uid, [('name', '=', 'CHEQUE'),('company_id','=',st.company_id.id)])
                print "JOURNAL***", journal[0]
                if journal:
                    sta_che = self.pool.get('account.bank.statement').search(cr, uid, [('pos_session_id', '=', st.pos_session_id.id),('journal_id','=',journal[0])])
                    if sta_che:
                        sta_che_obj = self.pool.get('account.bank.statement').browse(cr, uid, sta_che, context)
                        val_dep = sta_che_obj.balance_end+st.balance_end
            res[st.id] = val_dep
            print "val_dep", val_dep
        return res

    def _get_one_partner(self, cr, uid, context=None):
        if context is None:
            context = {}
        one_partner = True
        aux_partner = False
        if hasattr(self, 'line_ids'):
            is_first = True
            for l in self.line_ids:
                if is_first:
                    aux_partner = l.partner_id.id
                elif aux_partner != l.partner_id.id:
                    one_partner = False
                is_first = False
        return one_partner and aux_partner or False

    _columns = {
        'bank_account': fields.many2one('res.partner.bank', 'Cuenta Bancaria Proveedor'),
        'is_check' : fields.boolean('Pago por cheque?'),
        'check_ids': fields.one2many('account.check', 'statement_id', 'Checks'),
        'some_pay': fields.function(_exist_some_pay, type='boolean', string='Exists some pay ?'),
        'partner_id' : fields.many2one('res.partner', 'Partner'),
        'concept' : fields.char('Concept', size=255),
        'to_partner': fields.boolean('pagar al beneficiario?'),
        'check_book_id': fields.many2one('account.checkbook', 'Talonario de cheques'),
        'no_cheque': fields.char('No. Cheque', size=16),
        #CSV:29-11-2017: AUMENTO PARA QUE VERIFIQUEN EL VALOR TOTAL DEL DEPOSITO EFECTIVO + CHEQUE
        'valor_cheque' : fields.function(_get_valor_cheque, type='float', string='Valor Cheque'),
        'tot_dep' : fields.function(_get_valor_deposito, type='float', string='Total Deposito'),
        'state': fields.selection([('draft', 'Borrador'),
                                   ('open','Open'), # used by cash statements
                                   ('cancel', 'Cancelado'),
                                   ('confirm', 'Closed')],
                                  'Status', required=True, readonly="1",
                                  copy=False,
                                  help='When new statement is created the status will be \'Draft\'.\n'
                                       'And after getting confirmation from the bank it will be in \'Confirmed\' status.'),


    }

    _defaults = {
        'partner_id' : _get_one_partner
    }

    def onchange_journal_id(self, cr, uid, ids, journal_id, context=None):
        result = super(account_bank_statement, self).onchange_journal_id(cr, uid, ids, journal_id)
        if journal_id:
            journal = self.pool.get('account.journal').browse(cr, uid, journal_id, context)
            if 'value' in result:
                result['value']['is_check'] = journal.is_allow_check
            else:
                result = { 'value' : { 'is_check' : journal.is_allow_check }}
        return result

    def _prepare_move_line_vals(self, cr, uid, st_line, move_id, debit, credit, currency_id=False,
                                amount_currency=False, account_id=False, partner_id=False, context=None):
        res = super(account_bank_statement, self)._prepare_move_line_vals(cr, uid, st_line, move_id, debit, credit, currency_id, amount_currency, account_id, partner_id, context)
        if st_line.statement_id.to_partner:
            res.update({'partner_id': st_line.statement_id.partner_id.id})
        return res

    def button_confirm_bank(self, cr, uid, ids, context=None):
        checkbook = self.pool.get('account.checkbook')
        res = super(account_bank_statement, self).button_confirm_bank(cr, uid, ids, context)
        for rec in self.browse(cr, uid, ids):
	# Comento por que no se requiere que cada extracto tiene diferente nombre no puede tener un mismo nombre
            #if rec.name:
            #   seq_id = self.pool.get('ir.sequence').search(cr, uid, [('code', '=', 'banco.secuencia')])
            #    name = self.pool.get('ir.sequence')._next(cr, uid, seq_id, context)
            #rec.update({'name': name})
            self.write(cr, uid, rec.id, {'no_cheque': checkbook.default_filling(rec.check_book_id.filling, rec.check_book_id.actual_number)})
            checkbook.actualizar_consecutivo(cr, uid, rec.check_book_id.id, context=None)
            voucher_ids = []
            for st_line in rec.line_ids:
                voucher_ids.append(st_line.voucher_id.id)
        self.pool.get('account.voucher').write(cr, uid, voucher_ids, {'state': 'reconcile'}, context)
        return res

    def button_cancel(self, cr, uid, ids, context=None):
        res = super(account_bank_statement, self).button_cancel(cr, uid, ids, context)
        for record in self.browse(cr, uid, ids):
            for line in record.line_ids:
                if line.voucher_id:
                    self.pool.get('account.voucher').action_back_posted(cr, uid, [line.voucher_id.id], context)
        return self.write(cr, uid, ids, {'state': 'cancel'}, context=context)

    def action_cancel_draft(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state': 'draft'}, context=context)

    def to_string(self, value):

        convert = str(round(-value, 2))
        decimales = convert[convert.index('.'):len(convert)]
        if len(decimales) == 2:
            convert += '0'
        return convert

    def get_amount_in_letters(self, amount):
        in_letters = self.env['account.check'].get_number_in_letters(amount)
        return in_letters

    def get_format(self, date):
        def_date = datetime.strptime(date, "%Y-%m-%d")
        return def_date.strftime("%Y / %m / %d")

account_bank_statement()


class account_bank_statement_line(osv.osv):
    _inherit = 'account.bank.statement.line'

    _columns = {
        'voucher_id': fields.many2one('account.voucher', 'Voucher', readonly=True),
    }

    def process_reconciliation(self, cr, uid, id, mv_line_dicts, context=None):
        """ Creates a move line for each item of mv_line_dicts and for the statement line. Reconcile a new move line with its counterpart_move_line_id if specified. Finally, mark the statement line as reconciled by putting the newly created move id in the column journal_entry_id.

            :param int id: id of the bank statement line
            :param list of dicts mv_line_dicts: move lines to create. If counterpart_move_line_id is specified, reconcile with it
        """
        if context is None:
            context = {}
        st_line = self.browse(cr, uid, id, context=context)
        company_currency = st_line.journal_id.company_id.currency_id
        statement_currency = st_line.journal_id.currency or company_currency
        bs_obj = self.pool.get('account.bank.statement')
        am_obj = self.pool.get('account.move')
        aml_obj = self.pool.get('account.move.line')
        currency_obj = self.pool.get('res.currency')

        # Checks
        if st_line.journal_entry_id.id:
            raise osv.except_osv(_('Error!'), _('The bank statement line was already reconciled.'))
        for mv_line_dict in mv_line_dicts:
            for field in ['debit', 'credit', 'amount_currency']:
                if field not in mv_line_dict:
                    mv_line_dict[field] = 0.0
            if mv_line_dict.get('counterpart_move_line_id'):
                mv_line = aml_obj.browse(cr, uid, mv_line_dict.get('counterpart_move_line_id'), context=context)
                if mv_line.reconcile_id:
                    raise osv.except_osv(_('Error!'), _('A selected move line was already reconciled.'))

        # Create the move
        move_name = (st_line.statement_id.name or st_line.name) + "/" + str(st_line.sequence)
        move_vals = bs_obj._prepare_move(cr, uid, st_line, move_name, context=context)
        move_id = am_obj.create(cr, uid, move_vals, context=context)

        # Create the move line for the statement line
        if st_line.statement_id.currency.id != company_currency.id:
            if st_line.currency_id == company_currency:
                amount = st_line.amount_currency
            else:
                ctx = context.copy()
                ctx['date'] = st_line.date
                amount = currency_obj.compute(cr, uid, st_line.statement_id.currency.id, company_currency.id, st_line.amount, context=ctx)
        else:
            amount = st_line.amount
        bank_st_move_vals = bs_obj._prepare_bank_move_line(cr, uid, st_line, move_id, amount, company_currency.id, context=context)
        aml_obj.create(cr, uid, bank_st_move_vals, context=context)
        # Complete the dicts
        st_line_currency = st_line.currency_id or statement_currency
        st_line_currency_rate = st_line.currency_id and (st_line.amount_currency / st_line.amount) or False
        to_create = []
        for mv_line_dict in mv_line_dicts:
            if mv_line_dict.get('is_tax_line'):
                continue
            mv_line_dict['ref'] = move_name
            mv_line_dict['move_id'] = move_id
            mv_line_dict['period_id'] = st_line.statement_id.period_id.id
            mv_line_dict['journal_id'] = st_line.journal_id.id
            mv_line_dict['company_id'] = st_line.company_id.id
            mv_line_dict['statement_id'] = st_line.statement_id.id
            if mv_line_dict.get('counterpart_move_line_id'):
                mv_line = aml_obj.browse(cr, uid, mv_line_dict['counterpart_move_line_id'], context=context)
                mv_line_dict['partner_id'] = mv_line.partner_id.id or st_line.partner_id.id
                mv_line_dict['account_id'] = mv_line.account_id.id
            if st_line_currency.id != company_currency.id:
                ctx = context.copy()
                ctx['date'] = st_line.date
                mv_line_dict['amount_currency'] = mv_line_dict['debit'] - mv_line_dict['credit']
                mv_line_dict['currency_id'] = st_line_currency.id
                if st_line.currency_id and statement_currency.id == company_currency.id and st_line_currency_rate:
                    debit_at_current_rate = self.pool.get('res.currency').round(cr, uid, company_currency, mv_line_dict['debit'] / st_line_currency_rate)
                    credit_at_current_rate = self.pool.get('res.currency').round(cr, uid, company_currency, mv_line_dict['credit'] / st_line_currency_rate)
                elif st_line.currency_id and st_line_currency_rate:
                    debit_at_current_rate = currency_obj.compute(cr, uid, statement_currency.id, company_currency.id, mv_line_dict['debit'] / st_line_currency_rate, context=ctx)
                    credit_at_current_rate = currency_obj.compute(cr, uid, statement_currency.id, company_currency.id, mv_line_dict['credit'] / st_line_currency_rate, context=ctx)
                else:
                    debit_at_current_rate = currency_obj.compute(cr, uid, st_line_currency.id, company_currency.id, mv_line_dict['debit'], context=ctx)
                    credit_at_current_rate = currency_obj.compute(cr, uid, st_line_currency.id, company_currency.id, mv_line_dict['credit'], context=ctx)
                if mv_line_dict.get('counterpart_move_line_id'):
                    #post an account line that use the same currency rate than the counterpart (to balance the account) and post the difference in another line
                    ctx['date'] = mv_line.date
                    if mv_line.currency_id.id == mv_line_dict['currency_id'] \
                            and float_is_zero(abs(mv_line.amount_currency) - abs(mv_line_dict['amount_currency']), precision_rounding=mv_line.currency_id.rounding):
                        debit_at_old_rate = mv_line.credit
                        credit_at_old_rate = mv_line.debit
                    else:
                        debit_at_old_rate = currency_obj.compute(cr, uid, st_line_currency.id, company_currency.id, mv_line_dict['debit'], context=ctx)
                        credit_at_old_rate = currency_obj.compute(cr, uid, st_line_currency.id, company_currency.id, mv_line_dict['credit'], context=ctx)
                    mv_line_dict['credit'] = credit_at_old_rate
                    mv_line_dict['debit'] = debit_at_old_rate
                    if debit_at_old_rate - debit_at_current_rate:
                        currency_diff = debit_at_current_rate - debit_at_old_rate
                        to_create.append(self.get_currency_rate_line(cr, uid, st_line, -currency_diff, move_id, context=context))
                    if credit_at_old_rate - credit_at_current_rate:
                        currency_diff = credit_at_current_rate - credit_at_old_rate
                        to_create.append(self.get_currency_rate_line(cr, uid, st_line, currency_diff, move_id, context=context))
                    if mv_line.currency_id and mv_line_dict['currency_id'] == mv_line.currency_id.id:
                        amount_unreconciled = mv_line.amount_residual_currency
                    else:
                        amount_unreconciled = currency_obj.compute(cr, uid, company_currency.id, mv_line_dict['currency_id'] , mv_line.amount_residual, context=ctx)
                    if float_is_zero(mv_line_dict['amount_currency'] + amount_unreconciled, precision_rounding=mv_line.currency_id.rounding):
                        amount = mv_line_dict['debit'] or mv_line_dict['credit']
                        sign = -1 if mv_line_dict['debit'] else 1
                        currency_rate_difference = sign * (mv_line.amount_residual - amount)
                        if not company_currency.is_zero(currency_rate_difference):
                            exchange_lines = self._get_exchange_lines(cr, uid, st_line, mv_line, currency_rate_difference, mv_line_dict['currency_id'], move_id, context=context)
                            for exchange_line in exchange_lines:
                                to_create.append(exchange_line)

                else:
                    mv_line_dict['debit'] = debit_at_current_rate
                    mv_line_dict['credit'] = credit_at_current_rate
            elif statement_currency.id != company_currency.id:
                #statement is in foreign currency but the transaction is in company currency
                prorata_factor = (mv_line_dict['debit'] - mv_line_dict['credit']) / st_line.amount_currency
                mv_line_dict['amount_currency'] = prorata_factor * st_line.amount
            to_create.append(mv_line_dict)
        # If the reconciliation is performed in another currency than the company currency, the amounts are converted to get the right debit/credit.
        # If there is more than 1 debit and 1 credit, this can induce a rounding error, which we put in the foreign exchane gain/loss account.
        if st_line_currency.id != company_currency.id:
            diff_amount = bank_st_move_vals['debit'] - bank_st_move_vals['credit'] \
                          + sum(aml['debit'] for aml in to_create) - sum(aml['credit'] for aml in to_create)
            if not company_currency.is_zero(diff_amount):
                diff_aml = self.get_currency_rate_line(cr, uid, st_line, diff_amount, move_id, context=context)
                diff_aml['name'] = _('Rounding error from currency conversion')
                to_create.append(diff_aml)
        # Create move lines
        move_line_pairs_to_reconcile = []
        for mv_line_dict in to_create:
            counterpart_move_line_id = None # NB : this attribute is irrelevant for aml_obj.create() and needs to be removed from the dict
            if mv_line_dict.get('counterpart_move_line_id'):
                counterpart_move_line_id = mv_line_dict['counterpart_move_line_id']
                del mv_line_dict['counterpart_move_line_id']
            new_aml_id = aml_obj.create(cr, uid, mv_line_dict, context=context)
            if counterpart_move_line_id != None:
                move_line_pairs_to_reconcile.append([new_aml_id, counterpart_move_line_id])
        # Reconcile
        for pair in move_line_pairs_to_reconcile:
            aml_obj.reconcile_partial(cr, uid, pair, context=context)
        # Mark the statement line as reconciled
        self.write(cr, uid, id, {'journal_entry_id': move_id}, context=context)
        if st_line.statement_id.to_partner:
            self.pool.get('account.move').write(cr, uid, move_id, {'partner_id': st_line.statement_id.partner_id.id}, context)


class account_journal(osv.osv):
    _inherit = "account.journal"

    _columns = {
        'is_allow_check': fields.boolean('Allow Check writing', help='Check this if the journal is to be used for writing checks.'),
    }

    def get_number_in_letters(self, amount):
        return Numero_a_Texto(amount)

account_journal()

