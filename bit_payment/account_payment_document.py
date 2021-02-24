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
import openerp.addons.decimal_precision as dp


class account_voucher(osv.osv):
    _inherit = 'account.voucher'
    _description= 'Accounting Voucher'

    _columns = {

        # 'payment_id': fields.many2one('payment.document', 'Voucher'),
        'is_etransfer': fields.boolean('es Transf. Elect.?'),
        'bank_account_id': fields.many2one('res.partner.bank', 'Cuenta Bancaria Proveedor'),
        'is_check': fields.boolean("Es cheque ?")
    }

   # _defaults = {
        # pongo por defecto True para missionpetroleum
   #     'is_etransfer': True,
   # }
    # _defaults = {
    #     # pongo por defecto True para missionpetroleum
    #     'is_etransfer': True,
    # }

    # def validate_transaction(self, cr, uid, ids, context=None):
    # # Validate unique partner and pay_mode
    #     pay_mode_unico = partner_unico = band_first = True
    #     for voucher in self.browse(cr, uid, ids, context):
    #         if partner_unico and pay_mode_unico:
    #             if band_first:  # Obtengo los valores del primer registro
    #                 first_partner = voucher.partner_id.id
    #                 first_pay_mode = voucher.pay_mode_id.id
    #                 band_first = False
    #             else:   # Comparo que coincida el primero con todos los demás
    #                 if first_partner != voucher.partner_id.id:
    #                     partner_unico = False
    #                 if first_pay_mode != voucher.pay_mode_id.id:
    #                     pay_mode_unico = False
    #     if not partner_unico or not pay_mode_unico:
    #         message = ''
    #         if pay_mode_unico:
    #             message = _('Records selected must be from the same supplier.')
    #         else:
    #             message = _('Records selected should be the same mode of payment.')
    #         raise osv.except_osv(_('Warning!'), message)
    #     return True

account_voucher()


# class payment_document(osv.osv):
#     _name = 'payment.document'
#     _description= 'Payment document'
#
#     _columns = {
#
#         'voucher_ids': fields.one2many('account.voucher', 'payment_id', 'Vouchers'),
# #        'voucher_id':fields.many2one('account.voucher', 'Voucher'),
#         'check_number':fields.char('Check number', size=25),
#         'partner_id':fields.many2one('res.partner', 'Supplier'),
#         'pay_mode_id':fields.many2one('payment.mode', 'Payment mode'),
#         'pay_reason':fields.char('Payment reason', size=256),
#         'res_partner_id':fields.many2one('res.partner', 'Delivered to'),
#         'date':fields.date('Date', select=True, required=True, help="Effective date for accounting entries"),
#         'company_id': fields.many2one('res.company', 'Company', required=True),
#         'amount': fields.float('Total', digits_compute=dp.get_precision('Account'), required=True),
#         'type':fields.selection([
#             ('sale','Sale'),
#             ('purchase','Purchase'),
#             ('payment','Payment'),
#             ('receipt','Receipt'),
#         ],'Default Type'),
#         'state':fields.selection(
#             [('draft','Draft'),
#              ('cancel_null','Cancelled Null'),
#              ('cancel','Cancelled'),
#              ('open','Open'),
#              ('received','Received'),
#              ('commited','Commited'),
#              ('in_bank','Delivered to the bank')
#             ], 'Status', readonly=True, size=32, track_visibility='onchange',
#             help=' * The \'Draft\' status is used when a user created the new check. \
#                         \n* The \'Open\' when check is Ready to delivered to Supplier or receiving Customer. \
#                         \n* The \'Received\' status is used when the user receives the check \
#                         \n* The \'Commited\' status is used when the user delivery the check \
#                         \n* The \'Delivered to the bank\' status is used when the check has been received by the bank. \
#                         \    This is the final state \
#                         \n* The \'Cancelled Null\' status is used when the user cancels the check Supplier \
#                         \n* The \'Cancelled\' status is used when the user cancels the check Customer.'),
#
#     }
#
#     _defaults = {
#                     'state': 'draft',
#                 }
#
#     def fields_view_get(self, cr, uid, view_id=None, view_type='form',
#                         context=None, toolbar=False, submenu=False):
#         """
#          Changes the view dynamically
#          @param self: The object pointer.
#          @param cr: A database cursor
#          @param uid: ID of the user currently logged in
#          @param context: A standard dictionary
#          @return: New arch of view.
#         """
#         if context is None:
#             context={}
#         if 'active_ids' in context and len(context.get('active_ids')) > 1:
#             self.pool.get('account.voucher').validate_transaction(cr, uid, context.get('active_ids'), context)
#
#         res = super(payment_document, self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar,submenu=False)
#         return res
#
#
#     def default_get(self, cr, uid, fields, context=None):
#         if context is None:
#             context = {}
#         res = super(payment_document, self).default_get(cr, uid, fields, context=context)
#
#         if 'active_ids' in context:
#             band_first = True
#             amount = 0.0
#             my_checkbook = ''
#             line_ids = []
#             aux = []
#             temp = {}
#             for voucher_id in self.pool.get('account.voucher').browse(cr, uid, context.get('active_ids'), context):
#                 var_temp = {}
#                 if band_first:
#                     type = voucher_id.type
#                     temp.update({'date': voucher_id.date })
#                     temp.update({'partner_id': voucher_id.partner_id.id })
#                     if not type == 'payment':
#                         account_id = voucher_id.pay_mode_id.journal.default_credit_account_id.id
#                     else:
#                         account_id = voucher_id.pay_mode_id.journal.default_debit_account_id.id
#                     temp.update({'account_id': account_id })
#                     temp.update({'pay_mode_id': voucher_id.pay_mode_id.id })
#                     temp.update({'type': voucher_id.type })
#                     temp.update({'company_id': self.pool.get('res.users').browse(cr, uid, uid, context).company_id.id })
#                     temp.update({'is_check': voucher_id.pay_mode_id.is_check })
#                     if voucher_id.pay_mode_id.is_check:
#                         # Obtengo la cuenta bancaria asociada al modo de pago
#                         mp_bank_id = voucher_id.pay_mode_id.bank_id.id
#                         list_checkb = self.pool.get('account.checkbook').search(cr, uid, [('account_bank_id', '=', mp_bank_id)])
#                         for check_b in list_checkb:
#                             my_checkbook = self.pool.get('account.checkbook').browse(cr, uid, check_b, context).actual_number
#                         temp.update({'check_number': my_checkbook })
#                     band_first = False
#                     res.update(temp)
#                 var_temp.update({'number': voucher_id.number })
#                 var_temp.update({'reference': voucher_id.reference })
#                 var_temp.update({'journal_id': voucher_id.journal_id.id })
#                 var_temp.update({'state': voucher_id.state })
#                 amount += voucher_id.amount
#                 var_temp.update({'amount': voucher_id.amount })
#                 var_temp.update(temp)
#                 var_temp.update({'date': voucher_id.date })
#                 if type == 'payment':
#                     for line in voucher_id.line_dr_ids:
#                         line_ids.append(line.id)
#                 if type == 'receipt':
#                     for line in voucher_id.line_cr_ids:
#                         line_ids.append(line.id)
#             res.update({'voucher_ids' : context.get('active_ids') })
#             res.update({'amount': amount })
#
#             if type == 'payment':
#                 res.update({'line_dr_ids': line_ids })
#             if type == 'receipt':
#                 res.update({'line_cr_ids': line_ids })
#         return res
#
# # Aquí tengo que registrar el cheque
# # Aumentar la secuencia del cheque
# # Cambiar a estado "Posted" los Voucher seleccionados
#
#
#     def save_transaction(self, cr, uid, ids, context):
#
#         obj_pay_doc = self.pool.get('payment.document')
#         obj_acc_vou = self.pool.get('account.voucher')
#         obj_bank_statem = self.pool.get('account.bank.statement')
#         obj_bank_st_lin = self.pool.get('account.bank.statement.line')
#
#         vals = {}
#         bs_vals = {}
#         bs_l_vals = {}
#         for form in self.browse(cr, uid, ids):
#         # Conformando los valores a salvar el pay_doc
#             if form.check_number:
#                 vals['check_number'] = form.check_number
#             vals['partner_id'] = form.partner_id.id
#             vals['pay_mode_id'] = form.pay_mode_id.id
#             vals['amount'] = form.amount
#             vals['date'] = form.date
#             vals['res_partner_id'] = form.res_partner_id.id
#             vals['pay_reason'] = form.pay_reason
#             vals['type'] = form.type
#             vals['company_id'] = 1
#             vals['state'] = 'open'
#
#             voucher_id = obj_acc_vou.browse(cr, uid, context.get('active_ids'))[0]
#
#             bs_vals['journal_id'] = form.pay_mode_id.journal.id
#             bs_vals['period_id'] = voucher_id.period_id.id
# #=======================================================================
# # # Buscar el último balance de este journal
# #=======================================================================
#             bs_vals['balance_start'] = 0.0
#             bs_vals['state'] = 'draft'
#             bs_vals['date'] = form.date
#             bs_vals['total_entry_encoding'] = form.amount
#
#             bs_l_vals['name'] = form.pay_reason
#             bs_l_vals['date'] = form.date
#             bs_l_vals['partner_id'] = form.partner_id.id
#             bs_l_vals['journal_id'] = form.pay_mode_id.journal.id
#
#         # Update the pay_document
#             obj_pay_doc.write(cr, uid, ids, vals, context=context)
#         # Update the relation in voucher with payment
#             obj_acc_vou.write(cr, uid, context.get('active_ids'), { 'payment_id' : form.id }, context=context)
#         # Change the state in the voucher to "posted"
#             obj_acc_vou.proforma_voucher(cr, uid, context.get('active_ids'), context)
#         # Insert the bank statement
#             st_id = obj_bank_statem.create(cr, uid, bs_vals, context=context)
#         # Insert the line in the bank statement to reconcile
#             bs_l_vals['statement_id'] = st_id
#             obj_bank_st_lin.create(cr, uid, bs_l_vals, context=context)
#
#         return {'type': 'ir.actions.act_window_close'}
#
#     def action_draft(self, cr, uid, ids, context={}):
#         return self.write(cr, uid, ids, {'state': 'draft'}, context=context)
#
#     def action_open(self, cr, uid, ids, context=None):
#         self.write(cr, uid, ids, {'state' : 'open'}, context=context)
#
#     def action_received(self, cr, uid, ids, context={}):
#         return self.write(cr, uid, ids, {'state': 'received'}, context=context)
#
#     def action_commited(self, cr, uid, ids, context={}):
#         return self.write(cr, uid, ids, {'state': 'commited'}, context=context)
#
#     def action_in_bank(self, cr, uid, ids, context=None):
#         self.write(cr, uid, ids, {'state' : 'in_bank'}, context=context)
#
#     def action_cancel_null(self, cr, uid, ids, context={}):
#         return self.write(cr, uid, ids, {'state': 'cancel_null'}, context=context)
#
#     def action_cancel(self, cr, uid, ids, context=None):
#         return self.write(cr, uid, ids, {'state': 'cancel'}, context=context)
#
# payment_document()
#
