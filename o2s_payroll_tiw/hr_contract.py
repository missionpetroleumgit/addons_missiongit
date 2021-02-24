# -*- coding: utf-8 -*-
###############################
# ##########################  #
###############################

from openerp import models, fields, api
from openerp.exceptions import except_orm, Warning


class hr_contract(models.Model):
    _inherit = 'hr.contract'

    bonus_ids = fields.One2many('hr.type.of.bonus', 'contract_id', 'Bonos a percibir')

    # @api.multi
    # def write(self, vals):
    #     users = self.env['res.users'].search([])
    #     for record in users:
    #         self.pool['hr.employee'].write(self._cr, self._uid, [record.partner_id.employee_id.id], {'user_id': record.id})
    #     return super(hr_contract, self).write(vals)


class hr_type_of_bonus(models.Model):
    _name = 'hr.type.of.bonus'
    _rec_name = 'type'

    type = fields.Many2one('hr.adm.incomes', 'Bono')
    related_field = fields.Selection([('hours_international', 'Bono Internacional'), ('hours_workshop', 'Bono Taller'),
                                      ('hours_well', 'Bono Pozo')], 'Campo a pagar', required=True)
    amount = fields.Float('Valor/dia')
    convert = fields.Boolean('convertir?')
    type_convert = fields.Many2one('hr.adm.incomes', 'Convertir a:')
    limit = fields.Float('Horas a pagar')
    contract_id = fields.Many2one('hr.contract', 'Contrato')

    @api.onchange('type')
    def onchage_type(self):
        self.amount = self.type.default_value

hr_type_of_bonus()


class hr_employee(models.Model):
    _inherit = 'hr.employee'

    service_line = fields.Selection([('liner', 'Liner Hanger'), ('power', 'Power Tong')], 'Linea de Negocio', required=True)

