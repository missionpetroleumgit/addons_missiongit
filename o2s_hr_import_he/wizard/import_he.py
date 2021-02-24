# -*- coding: utf-8 -*-
import base64
from openerp import models, fields, api
from openerp.exceptions import except_orm


def calculate_value(adm_income_env, type_hd_income, valor_hora, value_column):
    adm_income = adm_income_env.search([('code', '=', type_hd_income)])
    if not adm_income:
        raise except_orm('Atencion !', 'Tipo de Ingreso %s no existe' % type_hd_income)
    amount = float(adm_income.default_value) * float(valor_hora) * float(value_column)
    return amount, adm_income.id


class import_he(models.Model):
    _name = 'import.he'

    file = fields.Binary('Archivo', required=True)
    date_reg = fields.Date('Fecha de Registro', required=True)
    company_id = fields.Many2one('res.company', 'Compañía', required=True)

    @api.multi
    def button_import(self):
        adm_income_env = self.env['hr.adm.incomes']
        income_env = self.env['hr.income']
        for record in self:
            buf = base64.decodestring(record.file).split('\n')
            buf = buf[1:len(buf) - 1]
            for item in buf:
                item = item.split(',')
                employee = self.env['hr.employee'].search([('identification_id', '=', item[0]), ('company_id', '=', record.company_id.id)])
                if not employee:
                    raise except_orm('Error', 'La cédula %s no está asociada a ningún empleado' % item[0])
                if (employee.contract_id.horas_x_dia * 30.00) == 0:
                    raise except_orm('Error',
                                     'El empleado %s tiene en 0 el campo horas por dia, revise por favor' % employee.emp_apellidos)
                valor_hora = employee.contract_id.wage/240*2
                amount_50, adm_id = calculate_value(adm_income_env, 'INGHSUP', valor_hora, item[2])
                if amount_50:
                    income_env.create({
                        'adm_id': adm_id, 'employee_id': employee.id, 'value': amount_50, 'date': record.date_reg,
                        'horas': item[2], 'h_registro': True, 'company_id': record.company_id.id
                    })
                # amount_fest, adm_id = calculate_value(adm_income_env, 'INGHRF', valor_hora, item[2])
                # if amount_fest:
                #     income_env.create({
                #         'adm_id': adm_id, 'employee_id': employee.id, 'value': amount_fest, 'date': record.date_reg,
                #         'horas': item[0], 'h_registro': True, 'company_id': record.company_id.id
                #     })
                # amount_25, adm_id = calculate_value(adm_income_env, 'INGHEXT', valor_hora, item[3])
                # if amount_25:
                #     income_env.create({
                #         'adm_id': adm_id, 'employee_id': employee.id, 'value': amount_25, 'date': record.date_reg,
                #         'horas': item[3], 'h_registro': True, 'company_id': record.company_id.id
                #     })
                # amount_100, adm_id = calculate_value(adm_income_env, 'INGHNOC', valor_hora, item[5])
                # if amount_100:
                #     income_env.create({
                #         'adm_id': adm_id, 'employee_id': employee.id, 'value': amount_100, 'date': record.date_reg,
                #         'horas': item[5], 'h_registro': True, 'company_id': record.company_id.id
                #     })

        return True

