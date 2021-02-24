# -*- coding: utf-8 -*-
from openerp import models, fields, api
from openerp.exceptions import except_orm, Warning
from datetime import datetime


class provision_entries(models.TransientModel):
    _name = 'provision.entries'

    @api.one
    def _pro_amount(self):
        inv = self.env['account.invoice'].browse(self._context['active_id'])
        self.amount = inv.amount_untaxed
        self.ref = inv.id

    journal_id = fields.Many2one('account.journal', 'Diario de Provision', required=True)
    date_entry = fields.Date('Fecha de asiento', required=True)
    amount = fields.Float('Monto a provisionar', compute=_pro_amount)
    ref = fields.Many2one('account.invoice', 'Referencia', compute=_pro_amount)
    period_id = fields.Many2one('account.period', 'Periodo', required=True)

    @api.one
    def generate_provision(self):
        move = self.env['account.move']
        line = self.env['account.move.line']
        try:
            move_obj = move.create({'ref': self.ref.origin, 'period_id': self.period_id.id, 'date': self.date_entry, 'journal_id': self.journal_id.id})
            debit_account_id, credit_account_id = False, False
            if self.ref.type == 'out_invoice':
                res = self.get_lines(self.ref, move_obj, self.amount, 0.00)
            elif self.ref.type == 'in_invoice':
                res = self.get_lines(self.ref, move_obj, 0.00, self.amount)
            for item in res:
                line.create(item)
        except ValueError:
            raise except_orm('Error!', 'No se pudo generar el asiento')
        self.ref.prov_id = move_obj.id
        self.ref.state_provision = 'prov'

        return True

    def get_lines(self, invoice, move_obj, debit, credit):
        res = list()
        res.append({'name': 'Prov.:' + invoice.origin, 'partner_id': invoice.partner_id.id, 'account_id': invoice.account_id.id, 'debit': debit, 'credit': credit,
                    'move_id': move_obj.id})
        for inv_line in invoice.invoice_line:
            res += self.convert_lines(inv_line, invoice.type, move_obj)
        return res

    def convert_lines(self, line, type, move_obj):
        res = []
        if type == 'out_invoice':
            if not line.product_id.property_account_income:
                        raise except_orm('Error!', 'Configure la cuenta de ingreso del producto %s' % line.product_id.name)
            res.append({'name': 'Prov.:' + line.invoice_id.origin, 'partner_id': line.invoice_id.partner_id.id,
                        'account_id': line.product_id.property_account_income.id, 'debit': 0.00, 'credit': line.price_subtotal,
                        'move_id': move_obj.id})
        elif type == 'in_invoice':
            if not line.product_id.property_account_expense:
                        raise except_orm('Error!', 'Configure la cuenta de gasto del producto %s' % line.product_id.name)
            res.append({'name': 'Prov.:' + line.invoice_id.origin, 'partner_id': line.invoice_id.partner_id.id,
                        'account_id': line.product_id.property_account_expense.id, 'debit': line.price_subtotal, 'credit': 0.00,
                        'move_id': move_obj.id})
        return res



