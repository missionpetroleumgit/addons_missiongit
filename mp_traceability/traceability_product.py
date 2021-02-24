# -*- coding: utf-8 -*-
##############################################################################
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import time
from openerp.osv import osv
from openerp.report import report_sxw


class traceability_material(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(traceability_material, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
            'pack_records': self.pack_records,
            'get_lines': self.get_lines,
            'heat_numbers': self.heat_numbers,
        })

    def get_lines(self, importation_id):
        purchase_order = self.pool.get('purchase.order')
        purchase_importation = self.pool.get('purchase.importation')
        imp_obj = purchase_importation.search(self.cr, self.uid, [('id', '=', importation_id)])
        imp_id = purchase_importation.browse(self.cr, self.uid, imp_obj)
        if imp_id:
            purchase_id = purchase_order.search(self.cr, self.uid, [('name', '=', imp_id.order_lines[0].order)])
            if not purchase_id:
                purchase_id = purchase_order.search(self.cr, self.uid, [('number_req', '=', imp_id.order_lines[0].order)])
            if purchase_id:
                purchase_obj = purchase_order.browse(self.cr, self.uid, purchase_id)
                order = purchase_obj.name
                req = purchase_obj.number_req
                return order, req

    def pack_records(self, importation_id, line_ids):
        pack_obj = ()
        stock_move = self.pool.get('stock.move')
        stock_pack_operation = self.pool.get('stock.pack.operation')
        data = []
        datas = []
        if importation_id:
            stock_move_obj = stock_move.search(self.cr, self.uid, [('importation_id', '=', importation_id)])
            if stock_move_obj:
                move_ids = stock_move.browse(self.cr, self.uid, stock_move_obj)
                for record in move_ids:
                    if record.picking_id.id not in data and record.state == 'done':
                        data.append(record.picking_id.id)
                if len(data) > 1:
                    data = tuple(data)
                    pack_obj = stock_pack_operation.search(self.cr, self.uid, [('picking_id', 'in', data)])
                elif len(data) == 1:
                    pack_obj = stock_pack_operation.search(self.cr, self.uid, [('picking_id', '=', data[0])],
                                                           order="product_id")
                pack_records = stock_pack_operation.browse(self.cr, self.uid, pack_obj)
                for item in pack_records:
                    for lines in line_ids:
                        if item.product_id.id == lines.product_id.id:
                            datas.append(item.id)
                print datas
                pack_records = stock_pack_operation.browse(self.cr, self.uid, datas)
                return pack_records

    def heat_numbers(self, lot_id):
        data = ''
        if lot_id:
            stock_production_lot = self.pool.get('stock.production.lot')
            stock_prod_obj = stock_production_lot.search(self.cr, self.uid, [('id', '=', lot_id)])
            stock_prod_ids = stock_production_lot.browse(self.cr, self.uid, stock_prod_obj)
            for item in stock_prod_ids.heat_ids:
                if len(stock_prod_ids.heat_ids) > 1:
                    data += item.name + ' / '
                else:
                    data = item.name
            return data


class traceability_material_report(osv.AbstractModel):
    _name = 'report.mp_traceability.traceability_material_report'
    _inherit = 'report.abstract_report'
    _template = 'mp_traceability.traceability_material_report'
    _wrapped_report_class = traceability_material

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
