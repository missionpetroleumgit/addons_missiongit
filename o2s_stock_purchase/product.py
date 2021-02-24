from openerp.osv import fields, osv
import openerp.addons.decimal_precision as dp


class product_product(osv.osv):
    _inherit = 'product.product'

    _columns = {
        'serial_items': fields.one2many('serial.item', 'product_id', 'Items de producto', delete='cascade'),
    }

product_product()


class serial_item(osv.osv):
    _name = 'serial.item'

    _columns = {
        'name': fields.char('No. Serie'),
        'amount_cost': fields.float('Costo de producto'),
        'importation_amount': fields.float('Costo de importacion'),
        'assigned': fields.boolean('Asignado'),
        'product_id': fields.many2one('product.product', 'Producto'),
        'origin': fields.char('Origen', help='Orden de la que proviene')
    }
serial_item()
