# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
from openerp.tools import float_compare, float_is_zero
from openerp import api, models, fields, _
from openerp.exceptions import except_orm


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    invoice_move_cost_ids = fields.One2many('account.move', 'move_cost_id', 'Asientos de costo')

    @api.multi
    def invoice_validate(self):
        res = super(AccountInvoice, self).invoice_validate()
        AccountMove = self.env['account.move']
        AccountJournal = self.env['account.journal']
        AccountMoveLine = self.env['account.move.line']
        debit = 0
        credit = 0
        lines_values = {}
        for lines in self.invoice_line:
            cost_acc_id = lines.product_id.property_stock_account_input
            if lines.product_id.type not in ('service', 'consu') and lines.invoice_id.type == 'out_invoice':
                journal = AccountJournal.search([('code', '=', 'DI')])
                if not cost_acc_id:
                    raise except_orm('Error !', 'No se encuentra configurada la cuenta de inventario del producto %s'
                                     % lines.product_id.default_code + ' ' + lines.product_id.name)
                if lines.product_id.standard_price == '0' and lines.product_id.type not in ('product', 'consu'):
                    raise except_orm('Error !', 'El producto %s no tiene precio de costo por ende el asiento no se '
                                                'puede generar con valor 0, asigne el costo del producto '
                                                'con producción antes de validar la factura por favor. att tu Papi'
                                     % lines.product_id.default_code + ' ' + lines.product_id.name)
                if cost_acc_id.code[:1] != '1':
                    raise except_orm('Error !', 'El producto %s no tiene configurada una cuenta de inventario, '
                                                'la cuenta %s, no es la correcta, revise por favor'
                                     % (lines.product_id.default_code + ' ' + lines.product_id.name, cost_acc_id.code))

                move = AccountMove.create({'journal_id': journal.id,
                                           'ref': lines.product_id.name + ' / ' + lines.invoice_id.number_reem})

                if lines.id not in lines_values:
                    lines_values[lines.product_id.property_stock_account_input.id] = {
                        'account_id': lines.product_id.property_stock_account_input.id,
                        'name': self.number_reem,
                        'credit': lines.product_id.standard_price,
                        'move_id': move.id,
                        'debit': 0.0,
                    }
                else:
                    lines_values[lines.product_id.property_stock_account_input.id]['credit'] += lines.product_id.standard_price
                for key, val in lines_values.iteritems():
                    AccountMoveLine.create(val)
                if not lines.product_id.property_account_cost_id:
                    raise except_orm('Error', 'Configure la cuenta de costo para el producto %s.'
                                     % '[' + lines.product_id.default_code + '] ' + lines.product_id.name)
                if lines.product_id.property_account_cost_id.code[:1] != '5':
                    raise except_orm('Error !', 'El producto %s no tiene configurada una cuenta de costo, '
                                                'la cuenta %s, no es la correcta, revise por favor'
                                     % (lines.product_id.default_code + ' ' + lines.product_id.name, cost_acc_id.code))
                AccountMoveLine.create({
                    'account_id': lines.product_id.property_account_cost_id.id,
                    'name': self.number_reem,
                    'debit': lines.product_id.standard_price,
                    'credit': 0.0,
                    'move_id': move.id

                })

                self.write({'invoice_move_cost_ids': [(4, move.id)]})

        return res

    @api.multi
    def action_cancel(self):
        res = super(AccountInvoice, self).action_cancel()
        moves = []
        for move in self.invoice_move_cost_ids:
            if move:
                for line in move.line_id:
                    line.unlink()
            move.button_cancel()
            move.unlink()

        return res


class AccountMove(models.Model):
    _inherit = 'account.move'

    move_cost_id = fields.Many2one('account.invoice', 'Asientos de Costo')

