# -*- coding: utf-8 -*-
###############################
# ##########################  #
###############################

from openerp import models, fields, api
from openerp.exceptions import except_orm, Warning


class bonus_distribution(models.Model):
    _name = 'bonus.distribution'

    name = fields.Char('Nombre', required=True)
    period_id = fields.Many2one('hr.period.period', 'Periodo', required=True)
    bonus_ids = fields.One2many('bonus_payment', 'bdist_id', 'Distribucion de horas por bono')
    state = fields.Selection([('draft', 'Nuevo'), ('done', 'Generado')], 'Estado', default='draft')
    # service_line = fields.Selection([('liner', 'Liner Hanger'), ('power', 'Power Tong')], 'Linea de Negocio', required=True)
    business_unit_id = fields.Many2one('hr.business.unit', 'Unidad de Negocio')

    @api.onchange('business_unit_id')
    def onchange_business_unit_id(self):
        if self.business_unit_id:
            bonus = list()
            employees = self.env['hr.employee'].search([('business_unit_id', '=', self.business_unit_id.id), ('state_emp', '=', 'active')])
            for employee in employees:
                bonus.append((0, 0, {'employee_id': employee.id, 'hours_workshop': 0.00, 'hours_well': 0.00, 'hours_international': 0.00}))
            self.bonus_ids = bonus

    @api.multi
    def action_confirm(self):
        for record in self:
            for line in record.bonus_ids:
                dict_bonus = dict()
                for bon in line.employee_id.contract_id.bonus_ids:
                    dict_bonus[bon.related_field] = {'type': bon.type.id, 'amount': bon.amount, 'convert': bon.convert, 'type_convert': bon.type_convert.id, 'limit': bon.limit}

                if record.business_unit_id.codigo in ('LNH', 'PWT'):
                    adm = self.env['hr.adm.incomes']
                    #BONO 1
                    if 'hours_international' in dict_bonus and dict_bonus['hours_international']['convert'] and dict_bonus['hours_international']['limit'] > 0 and line.hours_international > 0.00:
                        amount_total = line.hours_international * dict_bonus['hours_international']['amount']
                        amount_he = line.employee_id.contract_id.wage/240 * dict_bonus['hours_international']['limit'] * adm.browse(dict_bonus['hours_international']['type_convert']).default_value
                        amount_bon = amount_total - amount_he
                        self.create_income(dict_bonus['hours_international']['type'], line.employee_id.id, amount_bon)
                        self.create_income(dict_bonus['hours_international']['type_convert'], line.employee_id.id, amount_he)
                    else:
                        if 'hours_international' in dict_bonus and line.hours_international > 0.00:
                            self.create_income(dict_bonus['hours_international']['type'], line.employee_id.id,
                                               line.hours_international * dict_bonus['hours_international']['amount'])
                    #BONO 2
                    if 'hours_workshop' in dict_bonus and dict_bonus['hours_workshop']['convert'] and dict_bonus['hours_workshop']['limit'] > 0 and line.hours_workshop > 0.00:
                        amount_total = line.hours_workshop * dict_bonus['hours_workshop']['amount']
                        amount_he = line.employee_id.contract_id.wage/240 * dict_bonus['hours_workshop']['limit'] * adm.browse(dict_bonus['hours_workshop']['type_convert']).default_value
                        amount_bon = amount_total - amount_he

                        self.create_income(dict_bonus['hours_workshop']['type'], line.employee_id.id, amount_bon)
                        self.create_income(dict_bonus['hours_workshop']['type_convert'], line.employee_id.id, amount_he)
                    else:
                        if 'hours_workshop' in dict_bonus and line.hours_workshop > 0.00:
                            self.create_income(dict_bonus['hours_workshop']['type'], line.employee_id.id,
                                               line.hours_workshop * dict_bonus['hours_workshop']['amount'])
                    #BONO 3
                    if 'hours_well' in dict_bonus and dict_bonus['hours_well']['convert'] and dict_bonus['hours_well']['limit'] > 0 and line.hours_well > 0.00:
                        amount_total = line.hours_well * dict_bonus['hours_well']['amount']
                        amount_he = line.employee_id.contract_id.wage/240 * dict_bonus['hours_well']['limit'] * adm.browse(dict_bonus['hours_well']['type_convert']).default_value
                        amount_bon = amount_total - amount_he
                        self.create_income(dict_bonus['hours_well']['type'], line.employee_id.id, amount_bon)
                        self.create_income(dict_bonus['hours_well']['type_convert'], line.employee_id.id, amount_he)
                    else:
                        if 'hours_well' in dict_bonus and line.hours_well > 0.00:
                            self.create_income(dict_bonus['hours_well']['type'], line.employee_id.id,
                                               line.hours_well * dict_bonus['hours_well']['amount'])
                else:
                    if 'hours_international' in dict_bonus:
                        self.create_income(dict_bonus['hours_international']['type'], line.employee_id.id, line.hours_international * dict_bonus['hours_international']['amount'])
                    if 'hours_workshop' in dict_bonus:
                        self.create_income(dict_bonus['hours_workshop']['type'], line.employee_id.id, line.hours_workshop * dict_bonus['hours_workshop']['amount'])
                    if 'hours_well' in dict_bonus:
                        self.create_income(dict_bonus['hours_well']['type'], line.employee_id.id, line.hours_well * dict_bonus['hours_well']['amount'])
            record.state = 'done'
        return True

    def create_income(self, adm, employee, value):
        income = self.env['hr.income']
        income.create({'adm_id': adm, 'employee_id': employee, 'value': value, 'date': self.period_id.date_start})
        return True


    @api.multi
    def action_draft(self):
        for rec in self:
            rec.state = 'draft'


class bonus_payment(models.Model):
    _name = 'bonus_payment'
    _rec_name = 'employee_id'

    employee_id = fields.Many2one('hr.employee', 'Empleado', required=True)
    hours_international = fields.Float('Internacional')
    hours_workshop = fields.Float('Taller')
    hours_well = fields.Float('Pozo')
    bdist_id = fields.Many2one('bonus.distribution', 'Distribucion de bonos')
