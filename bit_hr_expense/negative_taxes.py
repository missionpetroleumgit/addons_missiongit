# -*- coding: utf-8 -*-
###############################
# ##########################  #
###############################

from openerp import models, fields, api


class negative_taxes(models.Model):
    _name = 'negative.taxes'

    employee_id = fields.Many2one('hr.employee', 'Empleado')
    amount = fields.Float('Monto')
    user_id = fields.Many2one('res.users', 'Creado por')

negative_taxes()
