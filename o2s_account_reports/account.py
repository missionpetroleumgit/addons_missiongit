##########################
# -*- coding: utf-8 -*- ##
##########################


from openerp import models, fields, api
from openerp.exceptions import except_orm, Warning


class account_account(models.Model):
    _inherit = 'account.account'

    code_tiw = fields.Char('Codigo Tiw')
    name_tiw = fields.Char('Nombre Tiw')

