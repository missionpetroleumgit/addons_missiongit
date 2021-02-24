# -*- encoding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################

from openerp import models, api, exceptions, _
from openerp import models, fields, api, _
from openerp.exceptions import except_orm

class SaleOrder(models.Model):
    _inherit = "sale.order"

    editbolean = fields.Boolean('Cambio a Borrador')

    @api.multi
    def button_draft(self):
        # go from canceled state to draft state
        for order in self:
            if order.state == 'cancel':
                order.order_line.write({'state': 'draft'})
                order.procurement_group_id.sudo().unlink()
                for line in order.order_line:
                    line.procurement_ids.sudo().unlink()
		    line.write({'state': 'draft'})
                order.write({'state': 'draft', 'editbolean': True})
                order.delete_workflow()
                order.create_workflow()
            # else:
            #    raise except_orm('Error !', 'Para cambiar a borrador debe estar cancelada la orden.')
        return True
