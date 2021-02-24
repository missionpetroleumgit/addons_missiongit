# -*- coding: utf-8 -*-
###############################
# ##########################  #
###############################

from openerp import models, fields, api
from openerp.exceptions import except_orm, Warning


class hr_adm_incomes(models.Model):
    _inherit = 'hr.adm.incomes'

    type = fields.Selection([('hours', 'Horas Extras'), ('bonus', 'Bonos'), ('income', 'Ingresos')], 'Tipo', required=True)
