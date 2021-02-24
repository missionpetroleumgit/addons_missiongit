##########################
# -*- coding: utf-8 -*- ##
##########################


from openerp import models, fields, api
from openerp.exceptions import except_orm, Warning


class account_invoice(models.Model):
    _inherit = 'account.invoice'

    purchaorden_id = fields.Many2one('purchase.importation', 'Importacion', domain=[('state','not in',['done','cancel'])])
