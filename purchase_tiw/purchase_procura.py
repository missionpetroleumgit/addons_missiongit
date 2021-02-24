from openerp import models, fields, api
from openerp.exceptions import except_orm, Warning
import openerp.addons.decimal_precision as dp
from openerp.tools.float_utils import float_compare
import dateutil.parser
import datetime
import time
from time import strftime


class purchase_order(models.Model):
    _inherit = 'purchase.order'

    @api.multi
    def wkf_confirm_order(self):
        res = super(purchase_order, self).wkf_confirm_order()
        return res

    @api.multi
    def approve_manager_procura(self):
        for record in self:
            record.state = 'sent'

    # @api.model
    # def create(self, vals):
    #     vals.update({'is_procura': True})
    #     obj = super(purchase_order, self).create(vals)
    #
    #     return obj

purchase_order()

