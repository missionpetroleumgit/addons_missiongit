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
            
        'pay_mode_id':fields.many2one('payment.mode', 'Payment mode', required=True, readonly=True, states={'draft':[('readonly',False)]}),
                        
    }
    
    def onchange_pay_mode(self, cr, uid, ids, pay_mode_id, partner_id, amount, type, date, context):
        res = {}
        for obj_payment_mode in self.pool.get('payment.mode').browse(cr, uid, [pay_mode_id], context):
            journal_id = obj_payment_mode.journal
            currency_id = journal_id.company_id.currency_id.id
        if partner_id:
            res = self.onchange_partner_id(cr, uid, ids, partner_id, journal_id.id, amount, currency_id, type, date, context)
        if journal_id:
            res['value']['journal_id'] = journal_id.id
        return res
        
        
    def to_string(self, value):
        return str(round(value, 2))
        
    def proforma_voucher(self, cr, uid, ids, context=None):
        res = super(account_voucher, self).proforma_voucher(cr, uid, ids, context)
#     We come back proform the voucher.
#        for voucher in self.browse(cr, uid, ids, context=context): 
 #           self.write(cr, uid, [voucher.id], {'state': 'proforma'})
#            self.write(cr, uid, [voucher.id], {'state': 'posted'})
        return True

    def button_proforma_voucher(self, cr, uid, ids, context=None):
        obj_acc = self.pool.get('account.invoice')
        invoice_id = context.get('invoice_id')

#        self.proforma_voucher(cr, uid, ids, context)
        
    # Cambio de estado a parcial
        brw_acc = obj_acc.browse(cr, uid, invoice_id, context)
        if brw_acc.residual != 0 and brw_acc.state != 'partially':    
            obj_acc.write(cr, uid, invoice_id, {'state' : 'partially'}, context=context)
        return {'type': 'ir.actions.act_window_close'}
    
account_voucher()


