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

class statement_load_voucher(models.TransientModel):
    _name = "statement.load.voucher"
    _description = "Load Voucher into Statement"

    line_ids = fields.Many2many('account.voucher', 'voucher_line_rel', 'voucher_id', 'line_id', 'Vouchers', \
                                domain="[('state', '=', 'posted'), ('bank_statement_line_ids', '=', False)]"
    )
    
    def get_statement_line_new(self, cr, uid, voucher, statement, context=None):
        # Override thi method to modifiy the new statement line to create
        ctx = context.copy()
        ctx['date'] = voucher.date
        amount = self.pool.get('res.currency').compute(cr, uid, voucher.currency_id.id,
                                                       statement.currency.id, voucher.amount, context=ctx)
 
        sign = voucher.type == 'payment' and -1.0 or 1.0
        type = voucher.type == 'payment' and 'supplier' or 'customer'
        account_id = voucher.type == 'payment' and voucher.partner_id.property_account_payable.id or voucher.partner_id.property_account_receivable.id
        return {
            'name': voucher.reference or voucher.number or '?',
            'amount': sign * amount,
            'type': type,
            'partner_id': voucher.partner_id.id,
#             'account_id': account_id,
            'statement_id': statement.id,
            'ref': voucher.name,
            'voucher_id': voucher.id,
#             'journal_entry_id': voucher.move_id.id,
        }
 
    def add_statement_lines(self, cr, uid, ids, context=None):
        statement_obj = self.pool.get('account.bank.statement')
        statement_line_obj = self.pool.get('account.bank.statement.line')
        voucher_obj = self.pool.get('account.voucher')
 
        if context is None:
            context = {}
        data = self.read(cr, uid, ids, [], context=context)[0]
        voucher_ids = data['line_ids']
        if not voucher_ids:
            return {'type': 'ir.actions.act_window_close'}
        statement = statement_obj.browse(
            cr, uid, context['active_id'], context=context)
        for voucher in voucher_obj.browse(cr, uid, voucher_ids, context=context):
            statement_line_obj.create(cr, uid,
                                      self.get_statement_line_new(cr, uid, voucher, statement, context=context), context=context)
        return {'type': 'ir.actions.act_window_close'}

statement_load_voucher()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: