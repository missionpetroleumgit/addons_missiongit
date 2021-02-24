# -*- coding: utf-8 -*-
#############################
#  Purchase for restaurants #
#############################
from openerp import models, fields, api


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    delivered_to = fields.Many2one('hr.employee', 'Entregado a')

    def print_out(self, cr, uid, ids, context=None):
        assert len(ids) == 1, 'This option should only be used for a single id at a time'
        return self.pool['report'].get_action(cr, uid, ids, 'purchase_adjustment.report_print_picking_out',
                                              context=context)
StockPicking()
