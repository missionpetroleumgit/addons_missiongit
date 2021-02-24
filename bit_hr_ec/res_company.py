__author__ = 'guillermo'
from openerp import models, fields, api
from dateutil.relativedelta import relativedelta
from datetime import datetime, date
from dateutil import parser


class res_company(models.Model):

    _inherit = 'res.company'

    @api.multi
    def _compute_fecha_init_sierra(self):
        for record in self:
            fys = self.env['hr.fiscalyear'].search([('state', '=', 'draft')])
            for fy in fys:
                fiscal_date = parser.parse(fy.date_start)
                fiscal_year = fiscal_date.year.real
                current_year = date.today().year.real
                if fiscal_year == current_year:
                    new_date = parser.parse(fy.date_start) - relativedelta(months=5)
                    record.fecha_init_sierra = new_date.strftime('%Y-%m-%d')
                else:
                    record.fecha_init_sierra = None

    @api.multi
    def _compute_fecha_fin_sierra(self):
        for record in self:
            fys = self.env['hr.fiscalyear'].search([('state', '=', 'draft')])
            for fy in fys:
                fiscal_date = parser.parse(fy.date_start)
                fiscal_year = fiscal_date.year.real
                current_year = date.today().year.real
                if fiscal_year == current_year:
                    new_date = parser.parse(fy.date_start) + relativedelta(months=6, days=30)
                    record.fecha_fin_sierra = new_date.strftime('%Y-%m-%d')
                else:
                    record.fecha_fin_sierra = None

    @api.multi
    def _compute_fecha_init_costa(self):
        for record in self:
            fys = self.env['hr.fiscalyear'].search([('state', '=', 'draft')])
            for fy in fys:
                fiscal_date = parser.parse(fy.date_start)
                fiscal_year = fiscal_date.year.real
                current_year = date.today().year.real
                if fiscal_year == current_year:
                    new_date = parser.parse(fy.date_start) - relativedelta(months=10)
                    record.fecha_init_costa = new_date.strftime('%Y-%m-%d')
                else:
                    record.fecha_init_costa = None

    @api.multi
    def _computefecha_fin_costa(self):
        for record in self:
            fys = self.env['hr.fiscalyear'].search([('state', '=', 'draft')])
            for fy in fys:
                fiscal_date = parser.parse(fy.date_start)
                fiscal_year = fiscal_date.year.real
                current_year = date.today().year.real
                if fiscal_year == current_year:
                    formato2 = "%Y-%m-%d %H:%M:%S"
                    today = datetime.today()
                    cadena = str(today.year.real) + '-01-01' + ' 00:00:00'
                    datetime_jan = datetime.strptime(cadena, formato2)
                    datetime_march = datetime_jan + relativedelta(months=2)
                    date_feb = datetime_march - datetime_jan
                    days_add = date_feb.days.real
                    new_date = parser.parse(fy.date_start) + relativedelta(days=(days_add-1))
                    record.fecha_fin_costa = new_date.strftime('%Y-%m-%d')
                else:
                    record.fecha_fin_costa = None

    region = fields.Selection([('sierra', 'Sierra'), ('costa', 'Costa'), ('both', 'Ambas')], 'Region', required=True)
    fecha_init_sierra = fields.Date(string='Fecha Inicial', compute=_compute_fecha_init_sierra)
    fecha_fin_sierra = fields.Date('Fecha Final', compute=_compute_fecha_fin_sierra)
    fecha_init_costa = fields.Date('Fecha Inicial', compute=_compute_fecha_init_costa)
    fecha_fin_costa = fields.Date('Fecha Final', compute=_computefecha_fin_costa)
    period_decimo3_pay = fields.Many2one('hr.period.period', 'Periodo a pagar Decimo')
    decimo3_journal_id = fields.Many2one('account.journal', 'Diario de Decimos 3ros', required=True)
    decimo4_journal_id = fields.Many2one('account.journal', 'Diario de Decimos 4tos', required=True)
    start_counting = fields.Integer('Inicio Incremento de Vacaciones', required=True)
    limit = fields.Integer('Limite de Incremento', required=True)
    increase = fields.Float('Incremento', required=True, digits=(1, 9))
    base = fields.Float('Base', required=True)
    vacation_entry = fields.Boolean('Generar Asiento Vacaciones')

