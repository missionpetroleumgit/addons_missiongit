# -*- coding: utf-8 -*-

from openerp.osv import fields, osv
import openerp.addons.decimal_precision as dp
from openerp import api
from openerp.exceptions import except_orm, ValidationError


class stock_move(osv.osv):
    _inherit = 'stock.move'

    _columns = {
        'serial_item_id': fields.many2one('serial.item', 'No. Serie'), # Readonly if selection True
        'select': fields.boolean('selection invisible'), # True if product have any serial
        'qty_available': fields.float('Cantidad disponible', related='product_id.qty_available', readonly=True),
        'motive': fields.selection([('prestamo', 'Prestamo'), ('devolucion', 'Devolucion'), ('reparacion', 'Reparacion'),
                                    ('venta', 'Venta'), ('fabricacion', 'Fabricacion'), ('modificacion', 'Modificación'),
                                    ('otros', 'Otros'), ('no_operativo', 'No Operativo'),
                                    ('mantenimiento', 'Mantenimiento'), ('compra', 'Compra')], 'Motivo')}

    # def onchange_product_id(self, cr, uid, ids, prod_id=False, loc_id=False, loc_dest_id=False, partner_id=False):
    #     res = super(stock_move, self).onchange_product_id(cr, uid, ids, prod_id, loc_id, loc_dest_id, partner_id)
    #     if prod_id:
    #         prod = self.pool.get('product.product').browse(cr, uid, prod_id)
    #         serials = [serial.id for serial in prod.serial_items if not serial.assigned]
    #         res.setdefault('domain', {})
    #         res['domain']['serial_item_id'] = repr([('id', 'in', serials)])
    #         res['value'].update({'select': True})
    #     return res

    def action_done(self, cr, uid, ids, context=None):
        for item in self.browse(cr, uid, ids):
            if not item.serial_item_id.assigned and item.picking_type_id.code == 'outgoing':
                self.pool.get('serial.item').write(cr, uid, [item.serial_item_id.id], {'assigned': True})
            elif item.serial_item_id.assigned and item.picking_type_id.code == 'incoming':
                self.pool.get('serial.item').write(cr, uid, [item.serial_item_id.id], {'assigned': False})
        return super(stock_move, self).action_done(cr, uid, ids, context)