# -*- coding: utf-8 -*-
#############################
#  Purchase for restaurants #
#############################

from openerp import models, fields, api, SUPERUSER_ID
from openerp.exceptions import except_orm


class res_company(models.Model):
    _inherit = 'res.company'

    advance_account_id = fields.Many2one('account.account', 'Cuenta de Anticipo')
