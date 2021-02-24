# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.exceptions import except_orm, Warning
from datetime import datetime


class stock_picking(models.Model):
    _inherit = 'stock.picking'

    @api.one
    @api.depends('picking_type_id')
    def _compute_picking_type(self):
        if self.picking_type_id:
            self.picking_ty = self.picking_type_id.code

    @api.multi
    def picking_to_draft(self):
        for record in self:
            if record.state == 'cancel':
                record.state = 'draft'
                for lines in self.move_lines:
                    lines.state = 'draft'
            elif record.state == 'done':
                if record.returns:
                    record.state = 'draft'
                    for lines in self.move_lines:
                        lines.state = 'draft'
        return True

    type_reception = fields.Selection([('tools', 'Herramientas'), ('materials', 'Materiales'),('order','Pedido de venta')],'Tipo Recepción')
    picking_ty = fields.Char(string="Tipo de stock", compute='_compute_picking_type')
    electronic_guide = fields.Boolean(string="Guia Electronica")
    returns = fields.Boolean('Retorno')
    reception_date = fields.Datetime('Fecha de recepcion')

    @api.model
    def default_get(self, fields_list):
        res = super(stock_picking, self).default_get(fields_list)
        if 'work' in self._context:
            work = self.env['work.product.rel'].browse(self._context['work'])
            items = []
            default_location_src_id = False
            default_location_dest_id = False
            picktype = self.env['stock.picking.type'].search([('code', '=', 'outgoing')])
            if picktype:
                default_location_src_id = picktype.default_location_src_id and picktype.default_location_src_id.id or False
                default_location_dest_id = picktype.default_location_dest_id and picktype.default_location_dest_id.id or False
            for item in work.items:
                if item.product_id.type == 'product':
                    items.append([0, 0, {'product_id': item.product_id.id, 'name': item.product_id.name, 'product_uom_qty': item.qty,
                                         'product_uom': item.product_id.uom_id.id, 'state': 'draft', 'procure_method': 'make_to_stock',
                                         'location_id': default_location_src_id, 'location_dest_id': default_location_dest_id,
                                         'picking_type_id': picktype.id}])
            res['move_lines'] = items
            res['picking_type_id'] = picktype and picktype.id or False

        return res

class stock_transfer_details_items(models.Model):
    _inherit = 'stock.transfer_details_items'

    serial_item_id = fields.Many2one('serial.item', 'No. Serie')

class stock_return_picking_line(models.Model):
    _inherit = 'stock.return.picking.line'

    serial_item_id = fields.Many2one('serial.item', 'No. Serie')

class stock_transfer_details(models.Model):
    _inherit = 'stock.transfer_details'

    def default_get(self, cr, uid, fields, context=None):
        if context is None: context = {}
        res = super(stock_transfer_details, self).default_get(cr, uid, fields, context=context)
        picking_ids = context.get('active_ids', [])
        active_model = context.get('active_model')

        if not picking_ids or len(picking_ids) != 1:
            # Partial Picking Processing may only be done for one picking at a time
            return res
        assert active_model in ('stock.picking'), 'Bad context propagation'
        picking_id, = picking_ids
        picking = self.pool.get('stock.picking').browse(cr, uid, picking_id, context=context)
        items = []
        packs = []
        if not picking.pack_operation_ids:
            picking.do_prepare_partial()
        for op in picking.pack_operation_ids:
            item = {
                'packop_id': op.id,
                'product_id': op.product_id.id,
                'product_uom_id': op.product_uom_id.id,
                'quantity': op.product_qty,
                'package_id': op.package_id.id,
                'lot_id': op.lot_id.id,
                'sourceloc_id': op.location_id.id,
                'destinationloc_id': op.location_dest_id.id,
                'result_package_id': op.result_package_id.id,
                'date': op.date,
                'owner_id': op.owner_id.id,
                'serial_item_id': self.return_serial(cr, uid, op.picking_id.id, context=context),
            }
            if op.product_id:
                items.append(item)
            elif op.package_id:
                packs.append(item)
        res.update(item_ids=items)
        res.update(packop_ids=packs)
        return res

    def return_serial(self,cr, uid, picking_id, context=None ):
        move_obj = self.pool.get('stock.move')
        move = self.pool.get('stock.move').search(cr, uid,[('picking_id','=',picking_id),('select','=',False)], context=context, order='id')
        movebrows = self.pool.get('stock.move').browse(cr, uid,move, context=context)
        serial_item_id = False

        for stm in movebrows:
            serial_item_id = stm.serial_item_id.id
            move_obj.write(cr, uid, stm.id, {'select': True}, context=context)
            break
        return serial_item_id

    @api.one
    def do_detailed_transfer(self):
        res = super(stock_transfer_details, self).do_detailed_transfer()
        today = datetime.now()
	quant = 0
        quant_obj = self.env['stock.quant']
        if not self.picking_id.reception_date:
            self.picking_id.reception_date = today
        for record in self.picking_id.pack_operation_ids:
            for moves in self.picking_id.move_lines:
                if record.product_id.id == moves.product_id.id:
                    record.motive = moves.motive
                    record.name = moves.name
	#for item in self.item_ids:
        #    location = item.sourceloc_id.id
        #    if item.lot_id:
        #        quant = quant_obj.search([('product_id', '=', item.product_id.id), ('lot_id', '=', item.lot_id.id),
        #                                  ('location_id', '=', location), ('qty', '>', 0)])
        #        if not quant:
        #            raise Warning('No puedes transferir %s, no tienes el stock suficiente con este Lote/Serie %s, '
        #                          'por favor comprueba el stock.' % (item.quantity, item.lot_id.name))
        #        if quant:
        #            if item.quantity <= quant.qty:
        #                continue
        #            else:
        #                raise Warning('No puede transferir %s, solo tiene %s en la %s' % (item.quantity, quant.qty,
        #                                                                                  item.sourceloc_id.name))

        return res


class stock_return_picking(models.Model):
    _inherit = 'stock.return.picking'

    def default_get(self, cr, uid, fields, context=None):
        """
         To get default values for the object.
         @param self: The object pointer.
         @param cr: A database cursor
         @param uid: ID of the user currently logged in
         @param fields: List of fields for which we want default values
         @param context: A standard dictionary
         @return: A dictionary with default values for all field in ``fields``
        """
        result1 = []
        if context is None:
            context = {}
        if context and context.get('active_ids', False):
            if len(context.get('active_ids')) > 1:
                raise Warning('You may only return one picking at a time!')
        res = super(stock_return_picking, self).default_get(cr, uid, fields, context=context)
        record_id = context and context.get('active_id', False) or False
        uom_obj = self.pool.get('product.uom')
        pick_obj = self.pool.get('stock.picking')
        pick = pick_obj.browse(cr, uid, record_id, context=context)
        quant_obj = self.pool.get("stock.quant")
        chained_move_exist = False
        if pick:
            if pick.state != 'done':
                raise Warning('You may only return pickings that are Done!')

            for move in pick.move_lines:
                if move.move_dest_id:
                    chained_move_exist = True
                #Sum the quants in that location that can be returned (they should have been moved by the moves that were included in the returned picking)
                qty = 0
                quant_search = quant_obj.search(cr, uid, [('history_ids', 'in', move.id), ('qty', '>', 0.0), ('location_id', 'child_of', move.location_dest_id.id)], context=context)
                for quant in quant_obj.browse(cr, uid, quant_search, context=context):
                    if not quant.reservation_id or quant.reservation_id.origin_returned_move_id.id != move.id:
                        qty += quant.qty
                qty = uom_obj._compute_qty(cr, uid, move.product_id.uom_id.id, qty, move.product_uom.id)
                result1.append({'product_id': move.product_id.id, 'quantity': qty, 'move_id': move.id, 'serial_item_id':move.serial_item_id.id})

            if len(result1) == 0:
                raise Warning('No products to return (only lines in Done state and not fully returned yet can be returned)!')
            if 'product_return_moves' in fields:
                res.update({'product_return_moves': result1})
            if 'move_dest_exists' in fields:
                res.update({'move_dest_exists': chained_move_exist})
        return res


class StockPackOperations(models.Model):
    _inherit = 'stock.pack.operation'

    name = fields.Char('Nombre', size=2048)
    motive = fields.Selection([('prestamo', 'Prestamo'), ('devolucion', 'Devolucion'), ('reparacion', 'Reparacion'),
                                    ('venta', 'Venta'), ('fabricacion', 'Fabricacion'), ('modificacion', 'Modificación'),
                                    ('otros', 'Otros'), ('no_operativo', 'No Operativo'),
                                    ('mantenimiento', 'Mantenimiento'), ('compra', 'Compra'),
                                    ('rent', 'Renta'), ('consign', 'Consignacion')], 'Motivo')
    # lot_id = fields.Many2one('stock.production.lot', 'Lote / No. Serie', readonly=True, select=True, ondelete="restrict")
