# -*- coding: utf-8 -*-
from openerp import models, fields, api
import base64
import StringIO
from datetime import datetime


class tenth_file(models.TransientModel):
    _name = 'tenth.file'

    name = fields.Char('Nombre')
    txt_binary = fields.Binary()

    @api.multi
    def generate_file(self):
        for record in self:
            file_txt = StringIO.StringIO()
            ids = self._context['active_ids']
            file_txt.write(self.header_string())
            for remuneration in self.env['hr.remuneration.employee'].browse(ids):
                file_txt.write(self.set_string(self.get_data(remuneration)))
            out = base64.encodestring(file_txt.getvalue().encode('utf-8'))
            file_txt.close()
            record.txt_binary = out
            record.name = 'Archivo Decimos(%s).csv' % datetime.now().strftime('%Y%m%d%H%M%S')
            return {
                'name': 'Archivo Generado',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'tenth.file',
                'res_id': record.id,
                'view_id': False,
                'type': 'ir.actions.act_window',
                'domain': [],
                'target': 'new',
                'context': self._context,
            }

    def get_data(self, obj):
        data = self.get_data_contract(obj.employee_id.id)
        data = data[0]
        vals = {
            'column1': obj.employee_id.identification_id,
            'column2': obj.employee_id.emp_nombres.encode('utf-8'),
            'column3': obj.employee_id.emp_apellidos.encode('utf-8'),
            'column4': self.return_gender(obj.employee_id.gender),
            'column5': obj.otherid or '',
            'column6': str(obj.worked_time),
            'column7': self.return_payment(obj.forma_pago),
            ##
            'column8': data['jpperm'],
            'column9': data['hours'],
            'column10': data['discap'],
            'column11': data['retirement_date'],
            'column12': data['reten_value'],
            'column13': data['monthly_payment'],
        }
        return vals

    @api.one
    def get_data_contract(self, employee):
        data = {
            'jpperm': 'False',
            'hours': 'False',
            'discap': 'False',
            'retirement_date': '',
            'reten_value': '',
            'monthly_payment': 'False',
        }
        contract = self.pool.get('hr.contract')
        contract_id = contract.search(self._cr, self._uid, [('employee_id', '=', employee)])
        if contract_id:
            contract_id = contract_id[0]
            obj_contract = contract.browse(self._cr, self._uid, contract_id)
            if obj_contract.working_hours.name == 'Horario Normal 240 H/M':
                data['jpperm'] = ''
                data['hours'] = ''
            else:
                data['jpperm'] = 'X'
                data['hours'] = str(5*obj_contract.horas_x_dia)
            if obj_contract.employee_id.emp_discapacidad:
                data['discap'] = 'X'
            else:
                data['discap'] = ''
            if obj_contract.employee_id.emp_dec_cuarto:
                data['monthly_payment'] = 'X'
            else:
                data['monthly_payment'] = ''
        return data

    def header_string(self):
        string = "Cedula" + "," + "Nombres" + "," + "Apellidos" + "," + "Genero" + "," + "Ocupacion" + "," + "Dias Laborados" + "," + "Tipo de Pago" + "," + \
                 "Jornada Parcial Permanente" + "," + "Horas Estipuladas Jornada Parcial" + "," + "Discapacidad" + "," + "Fecha Jubilacion" + "," + \
                 "Valor Retencion" + "," + "Mensualiza Pago" + chr(13) + chr(10)
        return string

    def set_string(self, values):
        return values['column1'] + ',' + values['column2'].decode('utf-8') + ',' + values['column3'].decode('utf-8') + ',' + values['column4'] + ',' + \
               values['column5'] + ',' + values['column6'] + ',' + values['column7'] + ',' + values['column8'] + ',' + values['column9'] + ',' + values['column10'] + ',' + \
               values['column11'] + ',' + values['column12'] + ',' + values['column13'] + chr(13) + chr(10)

    def return_gender(self, gender):
        letter = ''
        if gender == 'female':
            letter = 'M'
        if gender == 'male':
            letter = 'H'
        return letter

    def return_payment(self, payment):
        letter = ''
        if payment == 'transferencia':
            letter = 'A'
        if payment == 'cheque':
            letter = 'P'
        return letter