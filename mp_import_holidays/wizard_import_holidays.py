# -*- coding: utf-8 -*-
import base64
from openerp import models, fields, api
from openerp.exceptions import except_orm
from datetime import datetime


def calculate_days(date_from, date_to):
    date_1 = ''
    date_2 = ''
    if date_from and date_to:
        date_1 = datetime.strptime(date_from, "%Y-%m-%d")
        date_2 = datetime.strptime(date_to, "%Y-%m-%d")
    days = abs((date_2 - date_1).days)
    return days + 1


class HolidaysImport(models.Model):
    _name = 'holidays.import'

    file = fields.Binary('Archivo', required=True)
    type = fields.Many2one('hr.holidays.status', 'Tipo')
    company_id = fields.Many2one('res.company', 'Compañía', required=True)

    @api.multi
    def button_import(self):
        holiday_status_env = self.env['hr.holidays.status']
        holiday_env = self.env['hr.holidays']
        for record in self:
            buf = base64.decodestring(record.file).split('\n')
            buf = buf[1:len(buf) - 1]
            for item in buf:
                item = item.split(',')
                employee = self.env['hr.employee'].search([('identification_id', '=', item[0]),
                                                           ('company_id', '=', record.company_id.id)])
                if not employee:
                    raise except_orm('Error', 'La cedula %s no está asociada a ningún empleado' % item[0])
                if item[1] > item[2]:
                    raise except_orm('Error', 'La fecha de inicio es mayor a la fecha fin el el registro con numero de '
                                              'cedula %s' % item[0])
                days = calculate_days(item[1], item[2])
                if days > 0:
                    holiday_env.create({
                        'holiday_status_id': self.type.id, 'employee_id': employee.id, 'number_of_days_temp': float(days),
                        'date_from': item[1], 'date_to': item[2], 'name': item[3], 'company_id': record.company_id.id,
                        'holiday_type': 'employee', 'number_of_days': float(days)
                    })
                holiday_env.holidays_confirm()
                holiday_env.holidays_first_validate()
                holiday_env.holidays_validate()

        return True
