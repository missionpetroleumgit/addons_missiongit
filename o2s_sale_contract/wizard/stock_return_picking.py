from openerp.osv import osv, fields
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp


class stock_return_picking(osv.osv_memory):
    _inherit = 'stock.return.picking'

    def create_returns(self, cr, uid, ids, context=None):
        res = super(stock_return_picking, self).create_returns(cr, uid, ids, context)
        pick_object = self.pool.get('stock.picking')
        pick = pick_object.browse(cr, uid, context['active_id'])
        if pick.ticket_id:
            sale_object = self.pool.get('sale.order')
            sale_id = sale_object.search(cr, uid, [('ticket_id', '=', pick.ticket_id.id), ('name', '=', pick.origin)])
            # if sale_id:
                # sale_object.action_cancel(cr, uid, sale_id, context)
	pick.update({'returns': True})
        return res

stock_return_picking()

