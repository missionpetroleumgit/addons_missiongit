__author__ = 'guillermo'
from openerp import models, fields, api
from dateutil import parser
from dateutil.relativedelta import relativedelta
from openerp.exceptions import except_orm
from datetime import datetime


# class hr_period(models.Model):
#     _name = 'hr.period'
#
#     @api.one
#     def _compute_name(self):
#         if self.init_date:
#             aux_date = parser.parse(self.init_date)
#             self.name = str(aux_date.month.real) + '/' + str(aux_date.year.real)
#
#     name = fields.Char('Periodo', compute='_compute_name')
#     init_date = fields.Date('Fecha inicial del Periodo')
#     end_date = fields.Date('Fecha final del Periodo')
#
#     @api.onchange('init_date')
#     def onchenge_init_date(self):
#         res = dict()
#         if self.end_date:
#             if self.init_date >= self.end_date:
#                 self.init_date = None
#                 res['warning'] = {'title': 'Alerta', 'message': 'La fecha inicial no puede mayor o igual a la final'}
#                 return res
#
#     @api.onchange('end_date')
#     def onchenge_end_date(self):
#         res = dict()
#         if self.init_date:
#             if self.end_date <= self.init_date:
#                 self.end_date = None
#                 res['warning'] = {'title': 'Alerta', 'message': 'La fecha final no puede menor o igual a la inicial'}
#                 return res


class tenth_wizard(models.TransientModel):
    _name = 'tenth.wizard'

    decimo_type = fields.Selection([('dc3', 'Decimo 3ro'), ('dc4', 'Decimo 4to')], 'Tipo de Decimo', required=True)
    period_id = fields.Many2one('hr.period.period', 'Periodo', domain="[('code', '=', period_code)]")
    company_id = fields.Many2one('res.company', 'Empresa', default=lambda self: self.env['res.company']._company_default_get('tenth.wizard'))
    employee_ids = fields.Many2many(comodel_name='hr.employee', string='Empleados', required=True, domain="[('state_emp', '=', 'active')]")
    period_code = fields.Char('Periodo Empresa', related='company_id.period_decimo3_pay.code')

    @api.one
    def generate_tenth(self):
        tenth_env = self.env['hr.remuneration.employee']
        if self.decimo_type == 'dc3':
            date_period = parser.parse(self.period_id.date_start)
            initial_search_date = date_period - relativedelta(months=11)
            payslip = self.env['hr.payslip']
            for employee in self.employee_ids:
                if employee.state_emp == 'active':
                    periodo_inicio = initial_search_date.strftime('%Y-%m-%d')
                    a, b = tenth_env.tenth_amount_calculate(self.decimo_type, employee.id, periodo_inicio, self.period_id.date_stop)
                    values = {
                        'employee_id': employee.id,
                        'decimo_type': self.decimo_type,
                        'periodo_inicio': periodo_inicio,
                        'periodo_final': self.period_id.date_stop,
                        'worked_time': b,
                        'pay_amount': a,
                        'pay_amountbackup': a

                    }
                    tenth_env.create(values)
        elif self.decimo_type == 'dc4':
            user = self.env['res.users'].browse(self._uid)
            company = self.env['res.company'].browse(user.company_id.id)
            for employee in self.employee_ids:
                if employee.state_emp == 'active':
                    if employee.region == 'sierra' and (company.region == 'sierra' or company.region == 'both'):
                        fecha_inicio = company.fecha_init_sierra
                        fecha_fin = company.fecha_fin_sierra
                    elif employee.region == 'costa' and (company.region == 'costa' or company.region == 'both'):
                        fecha_inicio = company.fecha_init_costa
                        fecha_fin = company.fecha_fin_costa
                    else:
                        raise except_orm('Error', ("La region asociada al empleado %s no existe en la configuracion de la "
                                                  "compania")%employee.name)
                    a, b = tenth_env.tenth_amount_calculate(self.decimo_type, employee.id, fecha_inicio, fecha_fin)
                    if a > 0.00:
                        values = {
                            'employee_id': employee.id,
                            'decimo_type': self.decimo_type,
                            'periodo_inicio': fecha_inicio,
                            'periodo_final': fecha_fin,
                            'worked_time': b,
                            'pay_amount': a,
                            'pay_amountbackup':a
                        }
                        tenth_env.create(values)
            return True

