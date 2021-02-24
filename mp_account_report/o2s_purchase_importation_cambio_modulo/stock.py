from openerp import models, fields, api
from openerp.exceptions import except_orm


class stock_move(models.Model):
    _inherit = 'stock.move'
    importation_line_id = fields.Many2one('importation.order.line', 'Purchase Importation Line', ondelete='set null',
 select=True, readonly=True)


class stock_picking(models.Model):
    _inherit = 'stock.picking'
#
#     # @api.model
#     # def _get_type(self):
#     #    return self._context.get('change_state_imp')
#
#     is_importation = fields.Boolean('De Importacion')
#     picking_ready = fields.Boolean('Todo Dividido', change_default=True)

    @api.multi
    def do_transfer(self):
        for record in self:
            for move in record.move_lines:
                if move.importation_line_id and move.importation_line_id.importation_id.state == 'transit':
                    move.importation_line_id.importation_id.action_prorated()
        return super(stock_picking, self).do_transfer()

#    @api.multi
#    def picking_to_draft(self):
#        for record in self:
#            if record.state == 'cancel':
#                record.state = 'draft'
#                for lines in self.move_lines:
#                    lines.state = 'draft'
#        return True


#     @api.onchange('picking_ready')
#     def change_state_imp(self):
#         self.is_importation = False
