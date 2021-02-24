# -*- coding: utf-8 -*-
from openerp.osv import fields, osv
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp

class account_payment_order_wizard(osv.osv_memory):
    _name ="account.payment.order.wizard"
    _inherit ='payment.document'
    _columns = {

                }
    
    def fields_view_get(self, cr, uid, view_id=None, view_type='form',
                        context=None, toolbar=False, submenu=False):
        """
         Changes the view dynamically
         @param self: The object pointer.
         @param cr: A database cursor
         @param uid: ID of the user currently logged in
         @param context: A standard dictionary
         @return: New arch of view.
        """
        if context is None:
            context={}
        if 'active_ids' in context and len(context.get('active_ids')) > 1:
            self.pool.get('account.voucher').validate_transaction(cr, uid, context.get('active_ids'), context)
            
        res = super(account_payment_order_wizard, self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar,submenu=False)
        return res

    
    def default_get(self, cr, uid, fields, context=None):
        if context is None:
            context = {}
        res = super(account_payment_order_wizard, self).default_get(cr, uid, fields, context=context)
        
        if 'active_ids' in context:
            band_first = True
            amount = 0.0
            my_checkbook = ''
            line_ids = []
            aux = []
            for voucher_id in self.pool.get('account.voucher').browse(cr, uid, context.get('active_ids'), context):
                if band_first:
                    type = voucher_id.type
                    res.update({'date': voucher_id.date })
                    res.update({'partner_id': voucher_id.partner_id.id })
                    if not type == 'payment':
                        account_id = voucher_id.pay_mode_id.journal.default_credit_account_id.id
                    else:
                        account_id = voucher_id.pay_mode_id.journal.default_debit_account_id.id
                    res.update({'account_id': account_id })
                    res.update({'pay_mode_id': voucher_id.pay_mode_id.id })
                    res.update({'type': voucher_id.type })
                    res.update({'company_id': self.pool.get('res.users').browse(cr, uid, uid, context).company_id.id })
                    res.update({'is_check': voucher_id.pay_mode_id.is_check })
                    if voucher_id.pay_mode_id.is_check:
                        # Obtengo la cuenta bancaria asociada al modo de pago
                        mp_bank_id = voucher_id.pay_mode_id.bank_id.id
                        list_checkb = self.pool.get('account.checkbook').search(cr, uid, [('account_bank_id', '=', mp_bank_id)])
                        for check_b in list_checkb:
                            my_checkbook = self.pool.get('account.checkbook').browse(cr, uid, check_b, context).actual_number
                        res.update({'check_number': my_checkbook })
                    band_first = False
                res.update({'number': voucher_id.number })
                res.update({'reference': voucher_id.reference })
                res.update({'journal_id': voucher_id.journal_id.id })
                res.update({'state': voucher_id.state })
                amount += voucher_id.amount
                res.update({'amount': voucher_id.amount })
                res.update({'date': voucher_id.date })
            #    aux.append((0, 0, var_temp))
                if type == 'payment':
                    for line in voucher_id.line_dr_ids:
                        line_ids.append(line.id)
                if type == 'receipt':
                    for line in voucher_id.line_cr_ids:
                        line_ids.append(line.id)
#            res.update({'voucher_ids' : aux })
            res.update({'amount': amount })
            
            if type == 'payment':
                res.update({'line_dr_ids': line_ids })
            if type == 'receipt':
                res.update({'line_cr_ids': line_ids })
        return res

# Aquí tengo que registrar el cheque
# Aumentar la secuencia del cheque
# Cambiar a estado "Posted" los Voucher seleccionados 


    def save_transaction(self, cr, uid, ids, context):
        vals = {}
        for form in self.browse(cr, uid, ids):            
        # Conformando los valores a salvar el pay_doc
            if form.check_number:
                vals['check_number'] = form.check_number
            vals['partner_id'] = form.partner_id.id
            vals['pay_mode_id'] = form.pay_mode_id.id
            vals['amount'] = form.amount
            vals['date'] = form.date
            vals['res_partner_id'] = form.res_partner_id.id
            vals['pay_reason'] = form.pay_reason
            vals['type'] = form.type
            vals['company_id'] = 1
            vals['state'] = 'open'

 #           obj_pay_doc = self.pool.get('payment.document')
 #           id = obj_pay_doc.create(cr, uid, vals, context=context)
            
        

        return {'type': 'ir.actions.act_window_close'}
    

        
account_payment_order_wizard()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: