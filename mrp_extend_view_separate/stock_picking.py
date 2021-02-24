# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.exceptions import except_orm, Warning
from datetime import datetime


class stockTransferDetails(models.Model):
    _inherit = 'stock.transfer_details'

    @api.one
    def do_detailed_transfer(self):
        res = super(stockTransferDetails, self).do_detailed_transfer()
        today = datetime.now()
        mrp_production = self.env['mrp.production']
        mrp_true = 0
        stock_move = self.env['stock.move']
        if self.picking_id and self.picking_id.picking_type_id.code == 'internal':
            for moves in self.picking_id.move_lines:
                if moves.production_id and moves.location_dest_id.id == 12:
                    mrp_true += 1
                if mrp_true > 0:
                    production_id = mrp_production.search([('id', '=', moves.production_id[0].id)])
                    move_id = stock_move.search([('raw_material_production_id', '=', moves.production_id[0].id)])
                    if not move_id:
                        raise Warning('Error!', 'La orden de produccion no tiene asignada ninguna materia prima')
                    if production_id:
                        if production_id.state in ('draft', 'confirmed', 'ready'):
                            raise Warning('No puedes transferir un albaran de ingreso de un producto de produccion'
                                          ' en el estado. %s'
                                          % production_id.state)
                        if move_id[0].picking_id.state not in ('done', 'cancel'):
                            raise Warning('No puedes transferir un albaran de ingreso de un producto de produccion,'
                                          ' si aun no ha tranferido la materia prima solicitada '
                                          '# de movimiento. %s' % move_id[0].picking_id.name)
        return res
