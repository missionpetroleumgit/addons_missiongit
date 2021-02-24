__author__ = 'guillermo'
from openerp import models, fields, api


class decimos_report_wizard(models.TransientModel):
    _name = 'decimos.report.wizard'

    date_from = fields.Date('Desde', required=True)
    date_to = fields.Date('Hasta', required=True)
    type = fields.Selection([('dc3', 'Decimo 3ro'), ('dc4', 'Decimo 4to')], 'Tipo de Decimo', required=True)

    @api.onchange('date_from')
    def onchenge_date_from(self):
        res = dict()
        if self.date_to:
            if self.date_from >= self.date_to:
                self.date_from = None
                res['warning'] = {'title': 'Alerta', 'message': 'La fecha inicial no puede mayor o igual a la final'}
                return res

    @api.onchange('date_to')
    def onchenge_date_to(self):
        res = dict()
        if self.date_from:
            if self.date_to <= self.date_from:
                self.date_to = None
                res['warning'] = {'title': 'Alerta', 'message': 'La fecha final no puede menor o igual a la inicial'}
                return res

    @api.multi
    def print_report(self):
        data = {'type': self.type, 'date_from': self.date_from, 'date_to': self.date_to}
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'bit_hr_payroll_ec.decimo_report',
            'datas': data,
            }
