# -*- coding: utf-8 -*-
from openerp import api, models, fields
from openerp.addons.decimal_precision import decimal_precision as dp


class TransientMoveCreate(models.TransientModel):
    _name = 'transient.move.create'

    transient_lines = fields.One2many('transient.line.create', 'transient_model_id', 'Productos', required=True)

    @api.multi
    def button_create(self):
        self.ensure_one()
        picking_id = ()
        picking = False
        stock_move = self.env['stock.move']
        picking_obj = self.env['stock.picking']
        production = self.env['mrp.production'].browse(self._context['active_id'])
        virtual_location = self.env.ref('stock.location_production')
        move_id = stock_move.search([('raw_material_production_id', '=', production.id),
                                     ('state', 'not in', ('cancel', 'done'))], limit=1)
        if move_id:
            picking = picking_obj.search([('id', '=', move_id.picking_id.id)], limit=1)
	    picking = picking.id
        if production.not_bom and not picking:
            picking_type_obj = self.env['stock.picking.type']
            int_type = picking_type_obj.search([('code', '=', 'internal')])
            value = {'origin': production.name,
                     'picking_type_id': int_type.id}
            picking_id = picking_obj.create(value)
            print "pick2", picking_id
        for line in self.transient_lines:
            vals = {
                'product_id': line.product_id.id,
                'name': line.product_id.name,
                'origin': production.name,
                'product_uom_qty': line.product_qty,
                'product_uom': line.product_uom.id,
                'procure_method': 'make_to_stock',
                'location_id': line.src_location_id.id,
                'location_dest_id': virtual_location.id,
                'date_expected': production.date_planned,
                'company_id': production.company_id.id,
                'price_unit': line.product_id.standard_price,
                'raw_material_production_id': production.id,
                'production_id': production.id,
                'warehouse_id': line.src_location_id.get_warehouse(production.location_src_id),
                'picking_id': picking or picking_id.id or False,
                'state': 'confirmed'
            }
            move = stock_move.create(vals)
            production.product_lines.create({'name': line.product_id.name, 'product_id': line.product_id.id,
                                             'product_qty': line.product_qty, 'product_uom': line.product_uom.id, 'production_id': production.id})


class TransientLinesCreate(models.TransientModel):
    _name = 'transient.line.create'

    @api.multi
    def get_src_location(self):
        src_location = self.env['stock.location']
        location = src_location.search([('name', '=', 'Bodega General')])
        return location

    product_id = fields.Many2one('product.product', 'Producto', required=True)
    product_qty = fields.Float('Cantidad', digits_compute=dp.get_precision('Product Price'), default=1.0)
    product_uom = fields.Many2one('product.uom', 'UdM')
    src_location_id = fields.Many2one('stock.location', 'Ubicacion de Stock', required=True, default=get_src_location)
    transient_model_id = fields.Many2one('transient.move.create', 'Transient')

    @api.onchange('product_id')
    def product_id_change(self):
        self.product_uom = self.product_id.uom_id.id
