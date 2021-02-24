# -*- coding: utf-8 -*-
from openerp import models, fields, api
from string import upper
from openerp.exceptions import except_orm, Warning
import base64
import os
import StringIO
from datetime import datetime


class payment_file(models.TransientModel):
    _name = 'payment.file'

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
            out = base64.encodestring(file_txt.getvalue().encode('latin-1'))
            file_txt.close()
            record.txt_binary = out
            record.txt_filename = 'Pago_Proveedor(%s).txt' % datetime.now().strftime('%Y%m%d%H%M%S')
            return {
                'name': 'Archivo Generado',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'payment.file',
                'res_id': record.id,
                'view_id': False,
                'type': 'ir.actions.act_window',
                'domain': [],
                'target': 'new',
                'context': self._context,
            }

    def set_string(self, value):
        space = str()
        return value['column1'] + '\t' + value['column2'] + '\t' + value['column3'] + '\t' + value['column4'] + '\t' + \
               value['column5'] + '\t' + value['column6'] + '\t' + value['column7'] + '\t' + value['column8'][0: 41] + '\t' + value['column9'] + '\t' + value['column10'] + '\t' + \
               value['column11'] + '\t' + value['column12'] + chr(13) + chr(10)

    @api.one
    def _get_data(self):
        context = dict(self._context)
        ids = context['active_ids']
        company = self.env['res.users'].browse(self._uid).company_id
        values = list()
        cont = 1
        for voucher in self.env['account.voucher'].browse(ids):
            if not voucher.is_etransfer:
                raise except_orm('Error!!', 'El documento con referencia: %s no es de pago electronico' % voucher.reference)
            for line in voucher.line_dr_ids:
                if line.amount > 0.00:
                    vals = {
                        'column1': 'PA',
                        'column2': line.partner_id.part_number if not line.partner_id.use_another_id else line.partner_id.second_identification,
                        'column3': company.currency_id.name,
                        'column4': self.round_complete(line.amount),
                        'column5': self.get_bank_data(voucher, voucher.bank_account_id)[0],
                        'column6': self.get_bank_data(voucher, voucher.bank_account_id)[1],
                        'column7': self.get_bank_data(voucher, voucher.bank_account_id)[2],
                        'column8': self.get_description(voucher),
                        'column9': self.get_identification(line.partner_id)[0],
                        'column10': self.get_identification(line.partner_id)[1],
                        'column11': line.partner_id.name,
                        'column12': voucher.bank_account_id.bank_bic
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

    def get_description(self, voucher):
        return voucher.reference

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

    def value_complete(self, value):
        if value < 0.00:
            value *= -1
        value = round(value, 2)
        value *= 100
        if len(str(value)) < 13:
            string_value = str(int(value))
            #while len(string_value) < 13:
            #    string_value = '0' + string_value
            return string_value
        return str(int(value))

    def get_bank_data(self, voucher, bank_account):
        if not bank_account:
            raise except_orm('Error!!', 'El pago %s no tiene selccionada la cuenta bancaria de proveedor' % voucher.number)
        type = 'CTA'
        type_account = str()
        if bank_account.state == 'AHO':
            type_account = 'AHO'
        elif bank_account.state == 'CTE':
            type_account = 'CTE'
        number = bank_account.acc_number
        return type, type_account, number
