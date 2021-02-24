# -*- coding: utf-8 -*-
from openerp import models, fields, api
from openerp.exceptions import except_orm, Warning


TIPOS_NOMINA = {
    'rol': 'NOMINA',
    'quincena': 'QUINCENA',
    'liquidation': 'LIQUIDACION',
    'serv10': 'SERVICIO'
}


class hr_payslip_run(models.Model):
    _name = 'hr.payslip.run'
    _inherit = 'hr.payslip.run'

    company_id = fields.Many2one('res.company', 'Compania', required=True)

    @api.v7
    def company_id_change(self, cr, uid, ids, company_id=False, context=False):
        res = {'value': {}}
        if company_id and 'type' in context:
            struct_id = self.pool.get('hr.payroll.structure').search(cr, uid, [('company_id', '=', company_id), ('name', '=', TIPOS_NOMINA[context['type']])])
            if not struct_id:
                message = 'No existe una estructura salarial definida para el tipo %s' % context['type']
                res['warning'] = {'title': 'Alerta', 'message': message}
                return res
            res['value'].update({'struct_id': struct_id[0]})
        return res

hr_payslip_run()


class hr_holidays(models.Model):
    _inherit = 'hr.holidays'

    company_id = fields.Many2one('res.company', 'Compania')

    @api.model
    def default_get(self, fields_list):
        res = super(hr_holidays, self).default_get(fields_list)
        user = self.env['res.users'].browse(self._uid)
        res['company_id'] = user.company_id.id
        return res

hr_holidays()


class hr_contract(models.Model):
    _inherit = 'hr.contract'

    company_id = fields.Many2one('res.company', 'Compania')

    @api.model
    def default_get(self, fields_list):
        res = super(hr_contract, self).default_get(fields_list)
        user = self.env['res.users'].browse(self._uid)
        res['company_id'] = user.company_id.id
        return res

    _sql_constraints = [
            ('unique_active', 'unique(employee_id,company_id,activo)', 'El empleado ya tiene ACTIVO un contrato')
            ]

hr_contract()


class hr_employee(models.Model):
    _inherit = 'hr.employee'

    company_id = fields.Many2one('res.company', 'Compania')

    @api.model
    def default_get(self, fields_list):
        res = super(hr_employee, self).default_get(fields_list)
        user = self.env['res.users'].browse(self._uid)
        res['company_id'] = user.company_id.id
        return res

    @api.model
    def update_employee(self, employee):
        job = self.env['hr.job'].search([('name', '=', employee.job_id.name), ('company_id', '=', employee.company_id.id)])
        if employee.job_id and job:
           employee.write({'job_id': job.id})
        return True

    @api.model
    def update_partner(self, employee):
        partner = self.env['res.partner'].search([('employee_id', '=', employee.id)])
        if employee.company_id and partner:
            partner.write({'company_id': employee.company_id.id})
        return True

    _sql_constraints = [('name_unique', 'unique(identification_id,company_id)', 'La cedula debe ser unica!')]

hr_employee()

class hr_loan(models.Model):
    _inherit = 'hr.loan'

    company_id = fields.Many2one('res.company', 'Compania')

hr_loan()