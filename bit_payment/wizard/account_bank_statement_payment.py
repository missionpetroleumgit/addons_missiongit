# -*- coding: utf-8 -*-
from openerp import models, fields, api
from string import upper
from openerp.exceptions import except_orm, Warning
import base64
import os
import StringIO
from datetime import datetime


class payment_file_acc_voucher(models.TransientModel):
    _name = 'payment.file.acc.voucher'

    bank_id = fields.Many2one('res.bank', 'Banco', required=True)
    txt_binary = fields.Binary()
    txt_filename = fields.Char()

    @api.multi
    def generate_file(self):
        for record in self:
            file_txt = StringIO.StringIO()
            items = self._get_data()[0]
            for item in items:
                string = self.set_string(item)
                file_txt.write(upper(string))
            out = base64.encodestring(file_txt.getvalue())
            file_txt.close()
            record.txt_binary = out
            record.txt_filename = 'Pago_Proveedor(%s).txt' % datetime.now().strftime('%Y%m%d%H%M%S')
            return {
                'name': 'Archivo Generado',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'payment.file.acc.voucher',
                'res_id': record.id,
                'view_id': False,
                'type': 'ir.actions.act_window',
                'domain': [],
                'target': 'new',
                'context': self._context,
            }

    def set_string(self, value):
        space = str()
        if self.bank_id.bic == '10':
            return value['column1'] + '\t' + value['column2'] + '\t' + value['column3'] + '\t' + value['column4'] + '\t' + \
               value['column5'] + '\t' + value['column6'] + '\t' + value['column7'] + '\t' + value['column8'][0: 41] + '\t' + value['column9'] + '\t' + value['column10'] + '\t' + \
               value['column11'] + '\t' + value['column12'] + chr(13) + chr(10)
        elif self.bank_id.bic == '32':
            return value['column1'] + '\t' + value['column2'] + '\t' + value['column3'] + '\t' + value['column4'] + '\t' + \
               value['column5'] + '\t' + value['column6'] + '\t' + value['column7'] + '\t' + value['column8'][0: 41] + '\t' + value['column9'] + '\t' + value['column10'] + '\t' + \
               value['column11'] + '\t' + value['column12'] + chr(13) + chr(10)

    @api.one
    def _get_data(self):
        context = dict(self._context)
        ids = context['active_ids']
        company = self.env['res.users'].browse(self._uid).company_id
        values = list()
        for statement in self.env['account.bank.statement'].browse(ids):
            if statement.to_partner:
                vals = {
                    'column1': 'PA',
                    'column2': statement.partner_id.part_number if not statement.partner_id.use_another_id else statement.partner_id.second_identification,
                    'column3': company.currency_id.name,
                    'column4': self.round_complete(statement.balance_start),
                    'column5': self.get_bank_data(statement, statement.bank_account)[0],
                    'column6': self.get_bank_data(statement, statement.bank_account)[1],
                    'column7': self.get_bank_data(statement, statement.bank_account)[2],
                    'column8': self.get_description(statement.name),
                    'column9': self.get_identification(statement.partner_id)[0],
                    'column10': self.get_identification(statement.partner_id)[1],
                    'column11': statement.partner_id.name,
                    'column12': statement.bank_account.bank_bic
                }
                values.append(vals)
            else:
                for line in statement.line_ids:
                    if line.amount > 0.00:
                        vals = {
                            'column1': 'PA',
                            'column2': line.partner_id.part_number if not line.partner_id.use_another_id else line.partner_id.second_identification,
                            'column3': company.currency_id.name,
                            'column4': self.round_complete(line.amount),
                            'column5': self.get_bank_data(statement, line.bank_account_id)[0],
                            'column6': self.get_bank_data(statement, line.bank_account_id)[1],
                            'column7': self.get_bank_data(statement, line.bank_account_id)[2],
                            'column8': self.get_description(line.ref),
                            'column9': self.get_identification(line.partner_id)[0],
                            'column10': self.get_identification(line.partner_id)[1],
                            'column11': line.partner_id.name,
                            'column12': line.bank_account_id.bank_bic
                        }
                        values.append(vals)
        return values

    def get_identification(self, partner):
        part_type = str()
        if partner.part_type == 'c':
            part_type = 'C'
        elif partner.part_type == 'r':
            part_type = 'R'
        return part_type, partner.part_number

    def get_description(self, ref):
        return ref

    def round_complete(self, value):
        if value < 0.00:
            value *= -1
        value = round(value, 2)
        value *= 100
        if len(str(value)) < 13:
            string_value = str(int(value))
            while len(string_value) < 13:
                string_value = '0' + string_value
            return string_value
        return str(int(value))

    def get_bank_data(self, statement, bank_account):
        if not statement.bank_account and statement.to_partner:
            raise except_orm('Error!!', 'El pago %s no tiene selccionada la cuenta bancaria de proveedor' % statement.name)
        type = 'CTA'
        type_account = str()
        if bank_account.state == 'AHO':
            type_account = 'AHO'
        elif bank_account.state == 'CTE':
            type_account = 'CTE'
        number = bank_account.acc_number
        return type, type_account, number

