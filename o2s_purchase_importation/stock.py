from openerp import models, fields, api


class stock_move(models.Model):
    _inherit = 'stock.move'
    importation_line_id = fields.Many2one('importation.order.line', 'Purchase Importation Line', ondelete='set null',
                                          select=True, readonly=True)

stock_move()


class stock_picking(models.Model):
    _inherit = 'stock.picking'
    #
    #     # @api.model
    #     # def _get_type(self):
    #     #    return self._context.get('change_state_imp')
    #
    #     is_importation = fields.Boolean('De Importacion')
    #     picking_ready = fields.Boolean('Todo Dividido', change_default=True)

    # @api.multi
    # def do_transfer(self):
    #     for record in self:
    #         for move in record.move_lines:
    #             if move.importation_line_id and move.importation_line_id.importation_id.state == 'transit':
    #                 move.importation_line_id.importation_id.action_prorated()
    #
    #     return super(stock_picking, self).do_transfer()


stock_picking()
