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

    _columns = {
        'name':fields.char('CheckBook Name', size=30, readonly=True,select=True,required=True,states={'draft': [('readonly', False)]}),
        'range_desde': fields.integer('Check Number Desde', size=8, readonly=True,required=True,states={'draft': [('readonly', False)]}),
        'range_hasta': fields.integer('Check Number Hasta', size=8,readonly=True, required=True,states={'draft': [('readonly', False)]}),
        'actual_number':fields.char('Next Check Number', size=8,readonly=True, required=True,states={'draft': [('readonly', False)]}),
        'account_bank_id': fields.many2one('res.partner.bank','Account Bank',readonly=True,required=True,states={'draft': [('readonly', False)]}),
        'journal_id': fields.many2one('account.journal', 'Journal', required=True, domain=[('is_allow_check','=',True)]),
        'user_id' : fields.many2one('res.users','User'),  
        'change_date': fields.date('Change Date'),
        'state':fields.selection([('draft','Draft'),('active','In Use'),('used','Used')],string='State',readonly=True),
                    
    }
    
    _order = "name"
    _defaults = {
        'state': 'draft',
        'is_supplier': _get_type
    }
    
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
        'is_check' : fields.boolean('Is check ?'),
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
        'is_check' : fields.boolean('Is check ?'),
        'check_ids': fields.one2many('account.check', 'statement_id', 'Checks'),
        'some_pay': fields.function(_exist_some_pay, type='boolean', string='Exists some pay ?'),
        'partner_id' : fields.many2one('res.partner', 'Partner'),
        'concept' : fields.char('Concept', size=255),
        'to_partner': fields.boolean('pagar al beneficiario?'),
	'no_cheque': fields.char('No. Cheque', size=16),
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
    
    def generated_check(self, cr, uid, ids, context=None):
        partner_list = []
        first = True
        dicc = {}
        partner = consecutivo = False
        exist_parent_in_statement = False
        for st in self.browse(cr, uid, ids, context=context):
            if st.partner_id:
                partner = st.partner_id.id
                exist_parent_in_statement = True
            for st_line in st.line_ids:
                if not exist_parent_in_statement:
                    partner = st_line.partner_id.id
                is_pay = st_line.amount < 0
                
            # Buscar mi journal en las chequeras
                obj_chequera = self.pool.get('account.checkbook')
                list_checkb = obj_chequera.search(cr, uid, [('state','=','active'), ('journal_id', '=', st.journal_id.id)])
            # Valido el caso de que no exista chequera activa
                if not list_checkb:
                    raise osv.except_osv(   _('¡¡ Alerta !!'), 
                                            _('No existe chequera activa para el diario indicado.')
                                        ) 
            # Obtener el primer elemento
                chequera_id = list_checkb and list_checkb[0]
                        
                if partner and is_pay:
                # Buscar el número actual
                    if not exist_parent_in_statement and partner not in partner_list or first:
                        consecutivo = obj_chequera.actualizar_consecutivo(cr, uid, chequera_id, context)   
                    new_number = partner in dicc and 'number' in dicc.get(partner) \
                                and dicc.get(partner).get('number') or consecutivo
                    new_amount = partner in dicc and 'amount' in dicc.get(partner) \
                                and dicc.get(partner).get('amount') and \
                                dicc.get(partner).get('amount') + abs(st_line.amount) or abs(st_line.amount)
                    dicc[partner] = {
                                        'number' : new_number,
                                        'partner_id' : partner,
                                        'amount' : new_amount,
                                        'date' : st.date,
                                        'is_check' : st.is_check,
                                        'statement_id' : st.id,
                                        'checkbook_id' : chequera_id,
                                        'is_supplier': True
                                    }
                    partner_list.append(partner)
                first = False

            if partner_list:
                for p in list(set(partner_list)):
                    check_id = self.pool.get('account.check').create(cr, uid, dicc.get(p), context=context)
            else:
                if st.some_pay:
                    raise osv.except_osv(_('¡¡ Alerta !!'),
                                         _('Debe asociar al menos a un cliente / proveedor en las líneas.')
                                         )
        self.pool.get('account.voucher').action_reconcile(cr, uid, ids, context)            
        return

    def _prepare_move_line_vals(self, cr, uid, st_line, move_id, debit, credit, currency_id=False,
                amount_currency=False, account_id=False, partner_id=False, context=None):
        res = super(account_bank_statement, self)._prepare_move_line_vals(cr, uid, st_line, move_id, debit, credit, currency_id, amount_currency, account_id, partner_id, context)
        if st_line.statement_id.to_partner:
            res.update({'partner_id': st_line.statement_id.partner_id.id})
        return res

account_bank_statement()


class account_bank_statement_line(osv.osv):
    _inherit = 'account.bank.statement.line'

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

