# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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
from openerp.tools import float_is_zero
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
from openerp.report import report_sxw
from openerp.tools import float_compare, float_round

import time

class account_conciliation_statement(osv.osv):

    _order = "date desc, id desc"
    _name = "account.conciliation.statement"
    _description = "Conciliation Statement"
#    _inherit = ['mail.thread']
    _columns = {
        'name': fields.char(
            'Reference', states={'draft': [('readonly', False)]},
            readonly=True, # readonly for account_cash_statement
            copy=False,
            help='if you give the Name other then /, its created Accounting Entries Move '
                 'will be with same name as statement name. '
                 'This allows the statement entries to have the same references than the '
                 'statement itself'),
        'date': fields.date('Fecha Conciliacion', required=True, states={'confirm': [('readonly', True)]},
                            select=True, copy=False),
        'date_cierre': fields.date('Fecha Cierre', required=True, states={'confirm': [('readonly', True)]},
                            select=True, copy=False),
        'journal_id': fields.many2one('account.journal', 'Journal',
            readonly=True, states={'draft':[('readonly',False)]}),
        'period_id': fields.many2one('account.period', 'Period', required=True,
            states={'confirm':[('readonly', True)]}),
        'user_id': fields.many2one('res.users', 'P.Venta', required=True,
            states={'confirm':[('readonly', True)]}),
        'poss_id': fields.many2one('pos.session', 'Sesion', required=True,
            states={'confirm':[('readonly', True)]}),
        'valor_bruto': fields.float('Valor Bruto', digits_compute=dp.get_precision('Account'),
            states={'confirm':[('readonly',True)]}),
        'comision': fields.float('Comision', digits_compute=dp.get_precision('Account'),
            states={'confirm': [('readonly', True)]}, help="Computed using the cash control lines"),
        'iva_retenido': fields.float('Iva Retenido', digits_compute=dp.get_precision('Account'),
            states={'confirm':[('readonly',True)]}),
        'irf_retenido': fields.float('Irf Retenido', digits_compute=dp.get_precision('Account'),
            states={'confirm':[('readonly',True)]}),
        'valor_neto': fields.float('Neto Pagar', digits_compute=dp.get_precision('Account'),
            states={'confirm':[('readonly',True)]}),
        'valor_pendiente': fields.float('Valor Pendiente', digits_compute=dp.get_precision('Account'),
            states={'confirm':[('readonly',True)]}),
        'valor_conciliar': fields.float('Valor Conciliar', digits_compute=dp.get_precision('Account'),
            states={'confirm':[('readonly',True)]}),
        'valor_comision': fields.float('Valor Comision', digits_compute=dp.get_precision('Account'),
            states={'confirm':[('readonly',True)]}),
        'valor_iva': fields.float('Valor Iva', digits_compute=dp.get_precision('Account'),
            states={'confirm':[('readonly',True)]}),
        'valor_irf': fields.float('Valor Irf', digits_compute=dp.get_precision('Account'),
            states={'confirm':[('readonly',True)]}),
        'company_id': fields.related('journal_id', 'company_id', type='many2one', relation='res.company', string='Company', store=True, readonly=True),
        'line_ids': fields.one2many('account.conciliation.statement.line',
                                    'conciliation_id', 'Conciliation lines',
                                    states={'confirm':[('readonly', True)]}, copy=True),
        'move_line_ids': fields.one2many('account.move.line', 'statement_id',
                                         'Entry lines', states={'confirm':[('readonly',True)]}),
        'state': fields.selection([('draft', 'New'),
                                   ('open','Open'), # CSV:2016-04-21 used by cash statements
                                   ('pending','Pendiente'), # CSV:2016-04-21 used by pay partial
                                   ('confirm', 'Closed')],
                                   'Status', required=True, readonly="1",
                                   copy=False,
                                   help='When new statement is created the status will be \'Draft\'.\n'
                                        'And after getting confirmation from the bank it will be in \'Confirmed\' status.'),
        'type': fields.selection([('individual', 'Individual'),
                                   ('grupal','Grupal')],
                                   'Status', required=True, readonly="1",
                                   copy=False,
                                   help='Tipo de conciliacion para realizar individual o grupal'),
        'lote':fields.char('Lote', size=64, required=False, readonly=False),
        'is_con_dif': fields.boolean('Cuentas Conciliacion', help="Marcar esta opcion si se quiere realizar la conciliacion con cuentas diferentes a las configuradas en los diarios"),
        'default_bancocon_account_id': fields.many2one('account.account', 'Cuenta Banco', domain="[('type','!=','view')]", help="Escoger la cuenta para banco de la concialion de tarjetas"),
        'default_comision_account_id': fields.many2one('account.account', 'Cuenta Comision', domain="[('type','!=','view')]", help="Escoger la cuenta para comision de la concialion de tarjetas"),
        #'type_target': fields.many2one('o2s.target.type', 'Tipo Tarjeta'),
    }

    _defaults = {
        'name': '/',
        'date': fields.date.context_today,
        'state': 'draft',
        'type': 'individual',
#         'journal_id': _default_journal_id,
#         'period_id': _get_period,
        'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'account.conciliation.statement',context=c),
    }

    def _check_company_id(self, cr, uid, ids, context=None):
        for statement in self.browse(cr, uid, ids, context=context):
            if statement.company_id.id != statement.period_id.company_id.id:
                return False
        return True

    _constraints = [
        (_check_company_id, 'The journal and period chosen have to belong to the same company.', ['journal_id','period_id']),
    ]

    def button_conci_tarj(self, cr, uid, ids, context=None):
        print "IDS***", ids
        move_obj = self.pool.get('account.move')
        move_lin_obj = self.pool.get('account.move.line')
        for st in self.browse(cr, uid, ids, context=context):
            #****Creacion de conciliaciones parciales si existe pagos parciales
            if st.is_con_dif:
                cuen_banco = st.default_bancocon_account_id.id
                cuen_comi = st.default_comision_account_id.id
            else:
                cuen_banco = st.journal_id.default_bancocon_account_id.id
                cuen_comi = st.journal_id.default_comision_account_id.id

            res = []
            band = 0
            conci_obj = self.pool.get('account.conciliation.statement')
            conci_lin_obj = self.pool.get('account.conciliation.statement.line')
            stat_conc_line_ids = conci_lin_obj.search(cr, uid, [('conciliation_id', '=', st.id)])
            stat_conc_line_obj =  conci_lin_obj.browse(cr, uid, stat_conc_line_ids, context=context)
            vals_pend = {
                'name': st.name,
                  'journal_id': st.journal_id.id,
                  'period_id': st.period_id.id,
                  'user_id': st.user_id.id,
                  'poss_id' : st.poss_id.id,
                  'company_id' : st.company_id.id,
                  'comision': st.comision,
                  'iva_retenido': st.iva_retenido,
                  'irf_retenido': st.irf_retenido,
                  'lote': st.lote,
                  'type': st.type,
                  'is_con_dif': True,
                  'date_cierre': st.date_cierre,
                  'default_comision_account_id': st.default_comision_account_id.id,
                  'state': 'open'
            }
            print "***vals conciliation pend***: ", vals_pend
            for conci_line in stat_conc_line_obj:
                if conci_line.is_conci:
                    print "TARJETA CONCILIA", conci_line.journal_id.name
                    cuen_tarj = conci_line.journal_id.default_credit_account_id.id
                    diario = conci_line.journal_id.id
                # else:
                #     cuen_tarj = st.journal_id.default_credit_account_id.id
                #     diario = st.journal_id.id
                if conci_line.amount_pendiente > 0:
                    vals_pend_line = {
                             'name': conci_line.name,
                             'amount': conci_line.amount_pendiente,
                             'amount_conc': conci_line.amount_pendiente,
                             'amount_pendiente': conci_line.amount_pendiente,
                             'partner_id': conci_line.partner_id.id,
                             'account_id': conci_line.account_id.id,
                             'journal_id': conci_line.journal_id.id,
                             'ref': conci_line.ref,
                             'user_id': conci_line.user_id.id,
                             'lote': conci_line.lote,
                             'company_id': conci_line.company_id.id,
                             'amount_comision': round((conci_line.amount_pendiente*conci_line.journal_id.comision)/100,2),
                             'amount_iva_retenido': round(((conci_line.amount_pendiente-(conci_line.amount_pendiente/1.14))*conci_line.journal_id.iva_ret)/100,2),
                             'amount_irf_retenido': round(((conci_line.amount_pendiente/1.14)*conci_line.journal_id.irf_ret)/100,2),
                             'amount_neto': round(conci_line.amount_pendiente-((conci_line.amount_pendiente*conci_line.journal_id.comision)/100)-(((conci_line.amount_pendiente-(conci_line.amount_pendiente/1.14))*conci_line.journal_id.iva_ret)/100)-(((conci_line.amount_pendiente/1.14)*conci_line.journal_id.irf_ret)/100),2)
                    }
                    print "***vals conciliation pendiente line***: ", vals_pend_line
                    res.append(vals_pend_line)
                    band = 1
                    if not conci_line.is_conci:
                        conci_line.unlink()

            if band == 1:
                concil_id = conci_obj.create(cr, uid, vals_pend)
                for con_line in res:
                    vals_pen_lin = {
                             'name': con_line.get('name'),
                             'amount': con_line.get('amount'),
                             'amount_conc': con_line.get('amount_conc'),
                             'amount_pendiente': con_line.get('amount_pendiente'),
                             'partner_id': con_line.get('partner_id'),
                             'account_id': con_line.get('account_id'),
                             'conciliation_id': concil_id,
                             'journal_id': con_line.get('journal_id'),
                             'ref': con_line.get('ref'),
                             'user_id': con_line.get('user_id'),
                             'lote': con_line.get('lote'),
                             'company_id': con_line.get('company_id'),
                             'amount_comision': con_line.get('amount_comision'),
                             'amount_iva_retenido': con_line.get('amount_iva_retenido'),
                             'amount_irf_retenido': con_line.get('amount_irf_retenido'),
                             'amount_neto': con_line.get('amount_neto'),
                    }
                    concil_line_id = conci_lin_obj.create(cr, uid, vals_pen_lin)             

#****Creacion de asiento conciliacion        
            vals = {
                'name': '/',
                'ref': st.name,
                'journal_id': diario,
                'period_id': st.period_id.id,
                'date': st.date,
                'state': 'draft'
            }
            print "***vals move***: ", vals
            move_id = move_obj.create(cr, uid, vals)
            vals_line = {
                'name': st.name,
                'ref': 'NCB',
                'journal_id': st.journal_id.id,
                'period_id': st.period_id.id,
                'date': st.date,
                'move_id': move_id,
                'debit': st.valor_neto,
                'credit': 0.00,
                'account_id': cuen_banco,
                'state': 'draft'
            }
            print "***vals move line***: ", vals_line
            move_line_id = move_lin_obj.create(cr, uid, vals_line) 
            vals_line1 = {
                'name': st.name,
                'ref': 'BANCO',
                'journal_id': st.journal_id.id,
                'period_id': st.period_id.id,
                'date': st.date,
                'move_id': move_id,
                'debit': 0.00,
                'credit': st.valor_conciliar,
                'account_id': cuen_tarj,
                'state': 'draft'
            }
            print "***vals move line***: ", vals_line1
            move_line_id1 = move_lin_obj.create(cr, uid, vals_line1)
            vals_line2 = {
                'name': st.name,
                'ref': 'NCB',
                'journal_id': st.journal_id.id,
                'period_id': st.period_id.id,
                'date': st.date,
                'move_id': move_id,
                'debit': st.valor_irf,
                'credit': 0.00,
                'account_id': st.journal_id.default_irf_ret_account_id.id,
                'state': 'draft'
            }
            print "***vals move line***: ", vals_line2
            move_line_id2 = move_lin_obj.create(cr, uid, vals_line2)
            vals_line3 = {
                'name': st.name,
                'ref': 'NCB',
                'journal_id': st.journal_id.id,
                'period_id': st.period_id.id,
                'date': st.date,
                'move_id': move_id,
                'debit': st.valor_iva,
                'credit': 0.00,
                'account_id': st.journal_id.default_iva_ret_account_id.id,
                'state': 'draft'
            }
            print "***vals move line***: ", vals_line3
            move_line_id3 = move_lin_obj.create(cr, uid, vals_line3)
            vals_line4 = {
                'name': st.name,
                'ref': 'NCB',
                'journal_id': st.journal_id.id,
                'period_id': st.period_id.id,
                'date': st.date,
                'move_id': move_id,
                'debit': st.valor_comision,
                'credit': 0.00,
                'account_id': cuen_comi,
                'state': 'draft'
            }
            print "***vals move line***: ", vals_line4
            move_line_id4 = move_lin_obj.create(cr, uid, vals_line4)            
        return self.write(cr, uid, ids, {'state': 'confirm'}, context=context)
    
    def button_dummy(self, cr, uid, ids, context=None):
        print "IDS***", ids
        conci_obj = self.pool.get('account.conciliation.statement')
        conci_lin_obj = self.pool.get('account.conciliation.statement.line')
        stat_conc_line_ids = conci_lin_obj.search(cr, uid, [('conciliation_id', '=', ids), ('is_conci', '=', True)])
        stat_conc_line_obj =  conci_lin_obj.browse(cr, uid, stat_conc_line_ids, context=context)
        valor_bruto = 0.00
        valor_concil = 0.00
        valor_neto = 0.00
        valor_comi = 0.00
        valor_iva = 0.00
        valor_irf = 0.00
        for st_lin in stat_conc_line_obj:
            valor_bruto += round(st_lin.amount, 2)
            valor_concil += round(st_lin.amount_conc, 2)
            valor_neto += round(st_lin.amount_neto, 2)
            valor_comi += round(st_lin.amount_comision, 2)
            valor_iva += round(st_lin.amount_iva_retenido, 2)
            valor_irf += round(st_lin.amount_irf_retenido, 2)
        vals_stat = {'valor_bruto' : valor_bruto,
                  'valor_conciliar' : valor_concil,
                  'valor_neto' : valor_neto,
                  'valor_comision' : valor_comi,
                  'valor_iva' : valor_iva,
                  'valor_irf' : valor_irf}
        conci_obj.write(cr,uid,ids,vals_stat)            
        return self.write(cr, uid, ids, {'state': 'open'}, context=context)

    def button_cancel(self, cr, uid, ids, context=None):
        bnk_st_line_ids = []
        for st in self.browse(cr, uid, ids, context=context):
            bnk_st_line_ids += [line.id for line in st.line_ids]
        self.pool.get('account.conciliation.statement.line').cancel(cr, uid, bnk_st_line_ids, context=context)
        return self.write(cr, uid, ids, {'state': 'open'}, context=context)


class account_conciliation_statement_line(osv.osv):

    def cancel(self, cr, uid, ids, context=None):
        account_move_obj = self.pool.get('account.move')
        move_ids = []
        for line in self.browse(cr, uid, ids, context=context):
            if line.journal_entry_id:
                move_ids.append(line.journal_entry_id.id)
                for aml in line.journal_entry_id.line_id:
                    if aml.reconcile_id:
                        move_lines = [l.id for l in aml.reconcile_id.line_id]
                        move_lines.remove(aml.id)
                        self.pool.get('account.move.reconcile').unlink(cr, uid, [aml.reconcile_id.id], context=context)
                        if len(move_lines) >= 2:
                            self.pool.get('account.move.line').reconcile_partial(cr, uid, move_lines, 'auto', context=context)
        if move_ids:
            account_move_obj.button_cancel(cr, uid, move_ids, context=context)
            account_move_obj.unlink(cr, uid, move_ids, context)

    _order = "conciliation_id desc, sequence"
    _name = "account.conciliation.statement.line"
    _description = "Conciliation Statement Line"
#    _inherit = ['ir.needaction_mixin']
    _columns = {
        'name': fields.char('Concepto', required=True),
        'date': fields.date('Date', required=True),
        'amount': fields.float('Valor Bruto', digits_compute=dp.get_precision('Account')),
        'partner_id': fields.many2one('res.partner', 'Partner'),
        'bank_account_id': fields.many2one('res.partner.bank','Bank Account'),
        'account_id': fields.many2one('account.account', 'Account', help="This technical field can be used at the statement line creation/import time in order to avoid the reconciliation process on it later on. The statement line will simply create a counterpart on this account"),
        'conciliation_id': fields.many2one('account.conciliation.statement', 'Conciliation', select=True, required=True, ondelete='restrict'),
#        'journal_id': fields.related('conciliation_id', 'journal_id', type='many2one', relation='account.journal', string='F.Pago', store=True, readonly=True),
        'journal_id': fields.many2one('account.journal', 'F.Pago', readonly=True),
        'partner_name': fields.char('Partner Name', help="This field is used to record the third party name when importing bank statement in electronic format, when the partner doesn't exist yet in the database (or cannot be found)."),
        'ref': fields.char('Reference'),
        'note': fields.text('Notes'),
        'sequence': fields.integer('Sequence', select=True, help="Gives the sequence order when displaying a list of bank statement lines."),
        'company_id': fields.related('conciliation_id', 'company_id', type='many2one', relation='res.company', string='Company', store=True, readonly=True),
        'journal_entry_id': fields.many2one('account.move', 'Journal Entry', copy=False),
        'amount_conc': fields.float('Valor Con/Par', help="The amount expressed in an optional other currency if it is a multi-currency entry.", digits_compute=dp.get_precision('Account')),
        'amount_comision': fields.float('Comision', help="The amount expressed in an optional other currency if it is a multi-currency entry.", digits_compute=dp.get_precision('Account')),
        'amount_iva_retenido': fields.float('Iva Retenido', help="The amount expressed in an optional other currency if it is a multi-currency entry.", digits_compute=dp.get_precision('Account')),
        'amount_irf_retenido': fields.float('Irf Retenido', help="The amount expressed in an optional other currency if it is a multi-currency entry.", digits_compute=dp.get_precision('Account')),
        'amount_neto': fields.float('Valor Neto', help="The amount expressed in an optional other currency if it is a multi-currency entry.", digits_compute=dp.get_precision('Account')),
        'amount_pendiente': fields.float('Valor Pendiente', help="The amount expressed in an optional other currency if it is a multi-currency entry.", digits_compute=dp.get_precision('Account')),    
        'currency_id': fields.many2one('res.currency', 'Currency', help="The optional other currency if it is a multi-currency entry."),
        'is_conci': fields.boolean('Conciliar', help="Marcar si se va a conciliar la linea"),
        'lote':fields.char('Lote', size=64, required=False, readonly=False),
        'user_id': fields.many2one('res.users', 'P.Venta', required=False),
    }
    _defaults = {
        'name': lambda self,cr,uid,context={}: self.pool.get('ir.sequence').get(cr, uid, 'account.conciliation.statement.line'),
        'date': lambda self,cr,uid,context={}: context.get('date', fields.date.context_today(self,cr,uid,context=context)),
    }
    
    def onchange_valor_pendiente(self, cr, uid, ids, amount_conc, amount, journal_id, context=None):
        print "amount", amount
        print "amount_conc", amount_conc 
        print "Journal", journal_id
        accout_jour_obj = self.pool.get('account.journal')
        accout_jour_ids = accout_jour_obj.search(cr, uid, [('id', '=', journal_id)])
        accout_jour_obj =  accout_jour_obj.browse(cr, uid, accout_jour_ids, context=context)
        for journal in accout_jour_obj:
            por_comision = journal.comision
            por_iva = journal.iva_ret
            por_irf = journal.irf_ret
             
        if amount_conc == amount:
            result = { 'value' : { 'amount_pendiente' : 0.00 }}
        elif amount > amount_conc:
            result = { 'value' : { 'amount_pendiente' : amount - amount_conc,
                                   'amount_comision' : round((amount_conc*por_comision)/100,2),
                                   'amount_iva_retenido' : round(((amount_conc-(amount_conc/1.14))*por_iva)/100,2),
                                   'amount_irf_retenido' : round(((amount_conc/1.14)*por_irf)/100,2),
                                   'amount_neto' : round(amount_conc-((amount_conc*por_comision)/100)-(((amount_conc-(amount_conc/1.14))*por_iva)/100)-(((amount_conc/1.14)*por_irf)/100),2) }}
        elif  amount < amount_conc:
            raise osv.except_osv(_('Advertencia !'), _('El valor a conciliar no puede ser mayor que el valor bruto.!'))

        return result

    def onchange_valor_conciliar(self, cr, uid, ids, is_conci, amount_conc, amount, journal_id, context=None):
        result = {}
        print "amount", amount
        amount_conc = amount
        print "amount_conc", amount_conc
        print "Journal", journal_id
        accout_jour_obj = self.pool.get('account.journal')
        accout_jour_ids = accout_jour_obj.search(cr, uid, [('id', '=', journal_id)])
        accout_jour_obj =  accout_jour_obj.browse(cr, uid, accout_jour_ids, context=context)
        for journal in accout_jour_obj:
            por_comision = journal.comision
            por_iva = journal.iva_ret
            por_irf = journal.irf_ret

        if is_conci:
            result = { 'value' : { 'amount_pendiente' : amount - amount_conc,
                                   'amount_conc' : amount_conc,
                                   'amount_comision' : round((amount_conc*por_comision)/100,2),
                                   'amount_iva_retenido' : round(((amount_conc-(amount_conc/1.14))*por_iva)/100,2),
                                   'amount_irf_retenido' : round(((amount_conc/1.14)*por_irf)/100,2),
                                   'amount_neto' : round(amount_conc-((amount_conc*por_comision)/100)-(((amount_conc-(amount_conc/1.14))*por_iva)/100)-(((amount_conc/1.14)*por_irf)/100),2) }}
        return result