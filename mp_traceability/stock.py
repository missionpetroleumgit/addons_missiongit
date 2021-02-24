# -*- coding: utf-8 -*-
from openerp import api, models, fields
from openerp.exceptions import except_orm
import openerp.addons.decimal_precision as dp
from openerp.exceptions import except_orm, Warning


class StockProductionLot(models.Model):
    _inherit = 'stock.production.lot'

    @api.multi
    def get_id(self):
        traceability = ()
        for record in self:
            traceability = record.id
            self.traceability = traceability
        return traceability

    heat_ids = fields.One2many('stock.product.heat', 'lot_id', 'Colada')
    date_expiry = fields.Date('Fecha Caducidad')
    traceability = fields.Integer('Codigo Trazabilidad', compute=get_id, size=256)
    trace_ref = fields.Text('Observaciones')
    location_type = fields.Selection([('internal', 'Interno'), ('production', 'Produccion'), ('customer', 'Cliente'),
                                      ('supplier', 'Proveedor'), ('warehouse', 'Bodega')], 'Tipo')
    location_id = fields.Many2one('stock.location', 'Ubicacion Stock')


class Importation(models.Model):
    _inherit = 'purchase.importation'

    stock_traceability_ids = fields.One2many('stock.traceability', 'traceability_id', 'Trazabilidad')


class StockProductHeat(models.Model):
    _name = 'stock.product.heat'

    lot_id = fields.Many2one('stock.production.lot', 'Lote')
    name = fields.Char('HEAT NUMBER', size=32)
    heat_treat_lot = fields.Char('HEAT TREAT LOT No', size=32)
    heat_treat_furnace = fields.Char('HEAT TREATMENT FURNACE No', size=32)


class StockTraceability(models.Model):
    _name = 'stock.traceability'

    traceability_id = fields.Many2one('purchase.importation', 'Trazabilidad')
    transfer_id = fields.Many2one('stock.transfer_details', 'Transfer')
    packop_id = fields.Many2one('stock.pack.operation', 'Operation')
    product_id = fields.Many2one('product.product', 'Product')
    product_uom_id = fields.Many2one('product.uom', 'Product Unit of Measure')
    quantity = fields.Float('Quantity', digits=dp.get_precision('Product Unit of Measure'), default=1.0)
    package_id = fields.Many2one('stock.quant.package', 'Source package',
                                 domain="['|', ('location_id', 'child_of', sourceloc_id), ('location_id','=',False)]")
    lot_id = fields.Many2one('stock.production.lot', 'Lot/Serial Number')
    sourceloc_id = fields.Many2one('stock.location', 'Source Location', required=True)
    destinationloc_id = fields.Many2one('stock.location', 'Destination Location', required=True)
    result_package_id = fields.Many2one('stock.quant.package', 'Destination package',
                                        domain="['|', ('location_id', 'child_of', destinationloc_id), "
                                               "('location_id','=',False)]")
    date = fields.Datetime('Date')
    owner_id = fields.Many2one('res.partner', 'Owner', help="Owner of the quants")


class stock_transfer_details_items(models.Model):
    _inherit = 'stock.transfer_details_items'

    # @api.onchange('sourceloc_id')
    # def onchange_usage(self):
    #     usage = ''
    #     pick_id = self._context['active_ids']
    #     move_id = self.env['stock.move'].search([('picking_id', 'in', pick_id)], limit=1)
    #     if pick_id and move_id:
    #         print "pick y move", pick_id, move_id, self._context, move_id.location_id.usage
    #         self.write({'usage': move_id.location_id.usage})
    #     return True

    usage = fields.Selection([('internal', 'Interno'), ('customer', 'Cliente'), ('supplier', 'Proveedor'),
                              ('production', 'Produccion'), ('transit', 'Transito'), ('view', 'Vista'),
                              ('inventory', 'Inventario'), ('procurement', 'Obtencion')], 'Uso')


stock_transfer_details_items()


class stock_transfer_details(models.Model):
    _inherit = 'stock.transfer_details'

    @api.one
    def do_detailed_transfer(self):
        res = super(stock_transfer_details, self).do_detailed_transfer()
        origin1 = self.picking_id.origin[:2]
        origin2 = self.picking_id.origin[:3]
        incoming = self.picking_id.picking_type_id.code == 'incoming'
        internal = self.picking_id.picking_type_id.code == 'internal'
        importation_order_line = self.env['importation.order.line']
        importation_order = self.env['purchase.importation']
        for item in self.item_ids:
            print "Context", self._context
            print "Context", self.item_ids
            if item.quantity < 0:
                raise except_orm('Error !',
                                 'La cantidad a transferir debe ser mayor a 0. !')
            for move in self.picking_id.move_lines:
                if move.location_id.id != item.sourceloc_id.id:
                    raise except_orm('Error !',
                                     'La ubicacion de origen debe ser la misma que la del movimiento. !')
                if move.location_dest_id.id != item.destinationloc_id.id:
                    raise except_orm('Error !',
                                     'La ubicacion de destino debe ser la misma que la del movimiento. !')
        if self.picking_id and self.picking_id.picking_type_id.code == 'incoming':
            for moves in self.picking_id.move_lines:
                importation_line_obj = importation_order_line.search([('id', '=', moves.importation_line_id.id)])
                if importation_line_obj:
                    importation_obj = importation_order.search([('id', '=', importation_line_obj[0].importation_id.id)])
                    moves.importation_id = importation_obj.id
        if incoming or internal and origin1 in ('AO', 'MO') or origin2 == 'MSO':
            if self.picking_id.pick_selection not in ('return', 'outgoing', 'incoming'):
                if not self.picking_id.wh_revision:
                    raise except_orm('Error !',
                                     'Debe colocar los datos de revisión por bodega de este ingreso.!!')
                if self.picking_id.revision_required:
                    if not self.picking_id.quality_revision or not self.picking_id.wh_revision:
                        raise except_orm('Error !',
                                         'Debe colocar los datos de revisión por calidad y bodega de este ingreso.!!')
                else:
                    if not self.picking_id.wh_revision:
                        raise except_orm('Error de revisión !',
                                         'Debe colocar los datos de revisión por bodega de este ingreso.!!')
        return res


class stock_move(models.Model):
    _inherit = 'stock.move'

    importation_id = fields.Many2one('purchase.importation', 'Importacion')

stock_move()


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    pick_selection = fields.Selection([('incoming', 'Ingreso'), ('outgoing', 'Entregas'),  ('internal', 'Interno'),
                                       ('return', 'Devolucion')], 'Tipo Movimiento')

    @api.onchange('pick_selection')
    def onchange_picking_type(self):
        if self.pick_selection == 'internal':
            self.update({'picking_type_id': 3})
        elif self.pick_selection in ('incoming', 'return'):
            self.update({'picking_type_id': 1})
        elif self.pick_selection == 'outgoing':
            self.update({'picking_type_id': 2})


StockPicking()
