# -*- coding: utf-8 -*-
##############################################################################
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
##############################################################################

from openerp.osv import fields, osv


class traceability_report_wizard(osv.osv_memory):
    _name = 'traceability.report.wizard'
    _description = 'Traceability Report'

    _columns = {
        'purchase_importation_id': fields.many2one('purchase.importation', 'Importacion', required=True),
        'product_ids': fields.many2many('stock.move', 'stock_move_name', 'stock_move_line_id', 'stock_move_print_id', 'Productos', required=True),
    }

    def get_traceability_report(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        data = self.read(cr, uid, ids)[0]
        datas = {
            'ids': context.get('active_ids', []),
            'model': 'traceability.material.report',
            'form': data
        }

        datas['form']['active_ids'] = context.get('active_ids', False)
        return self.pool['report'].get_action(cr, uid, [], 'mp_traceability.traceability_material_report', data=datas, context=context)


traceability_report_wizard()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
