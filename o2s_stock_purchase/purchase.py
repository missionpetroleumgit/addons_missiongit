from openerp.osv import fields, osv
import openerp.addons.decimal_precision as dp


class purchase_order(osv.osv):
    _inherit = 'purchase.order'

purchase_order()


class purchase_order_line(osv.osv):
    _inherit = 'purchase.order.line'

    _columns = {
        'number': fields.char('No. parte')
    }
purchase_order_line()

