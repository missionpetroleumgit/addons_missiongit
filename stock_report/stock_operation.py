# # -*- coding: utf-8 -*-
#
# from openerp import api, fields, models
#
#
# class StockPicking(models.Model):
#     _inherit = 'stock.picking'
#
#     @api.multi
#     def do_enter_transfer_details(self):
#         res = super(StockPicking, self).do_enter_transfer_details()
#         for record in self:
#             if record.move_lines:
#                 for moves in record.move_lines:
#