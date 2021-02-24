# -*- coding: utf-8 -*-
from openerp.report import report_sxw
from openerp.osv import osv


class report_service_disaggregated_class(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(report_service_disaggregated_class, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'get_description': self._get_description
        })

    def _get_description(self, cmpt, order):
        item_pool = self.pool.get('product.pricelist.item')
        item_ids = item_pool.search(self.cr, self.uid, [('product_id', '=', cmpt.product_id.id), ('price_version_id.pricelist_id', '=', order.pricelist_id.id)])
        if item_ids:
            item = item_pool.browse(self.cr, self.uid, item_ids[0])
            return item.partner_desc, item.product_partner_ident
        return cmpt.product_id.name, cmpt.product_id.default_code


class service_ticket_non_grouping_report(osv.AbstractModel):
    _name = 'report.o2s_sale_contract.service_ticket_non_grouping_report'
    _inherit = 'report.abstract_report'
    _template = 'o2s_sale_contract.service_ticket_non_grouping_report'
    _wrapped_report_class = report_service_disaggregated_class

