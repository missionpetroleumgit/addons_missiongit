# -*- coding: utf-8 -*-
from openerp import models, fields, api
import base64
import StringIO
from datetime import datetime
from openerp.exceptions import except_orm


class service_percent(models.TransientModel):
    _name = 'service.percent'

    company_id = fields.Many2one('res.company', 'Compañia', required=True)
    amount = fields.Float('Monto a distribuir')
    date_reg = fields.Date('Fecha de Registro', required=True)
    employe_days_ids = fields.One2many('employee.days.rel', 'service_percent_id', 'Empleados')

    @api.onchange('company_id')
    def onchange_company_id(self):
        if self.company_id:
            employee_ids = [employee.id for employee in self.env['hr.employee'].search([('company_id', '=', self.company_id.id)])]
            sql = "SELECT employee_id FROM company_employee_relation WHERE company_id=%s" % self.company_id.id
            self._cr.execute(sql)
            res = self._cr.dictfetchall()
            if res:
                employee_ids += [item['employee_id'] for item in res]
            employee_days = list()
            for rec in employee_ids:
                employee_days.append((0, 0, {'employee_id': rec, 'nu_days': 30}))
            self.employe_days_ids = employee_days

    @api.multi
    def percent_distribution(self):
        days_total = 0.00
        for emp in self.employe_days_ids:
            days_total += emp.nu_days

        if days_total <= 0:
            raise except_orm('Error!', 'El total de dias debe ser mayor a 0.00')

        factor = self.amount/days_total

        add_incomes = self.env['hr.adm.incomes'].search([('code', '=', 'ING10PERC')])
        if not add_incomes:
            add_incomes = self.env['hr.adm.incomes'].create({'name': 'ING. SERVICIOS', 'code': 'ING10PERC', 'payroll_label': 'ING. SERVICIOS'})

        for item in self.employe_days_ids:
            self.env['hr.income'].create({
                'adm_id': add_incomes.id,
                'company_id': item.employee_id.company_id.id,
                'employee_id': item.employee_id.id,
                'value': item.nu_days * factor,
                'date': self.date_reg,
                'state': 'draft'
            })

        return {'type': 'ir.actions.act_window_close'}


class employee_days_rel(models.TransientModel):
    _name = 'employee.days.rel'

    employee_id = fields.Many2one('hr.employee', 'Empleados', required=True)
    nu_days = fields.Integer('Dias Trabajados')
    service_percent_id = fields.Many2one('service.percent', 'Servicio')


