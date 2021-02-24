# -*- coding: utf-8 -*-
from openerp.report import report_sxw
from openerp.osv import osv


class report_invoice_disaggregated_class(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(report_invoice_disaggregated_class, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'disaggregated_lines': self._disaggregated_lines
        })

    def _disaggregated_lines(self, invoice):
        lines = list()
        if not invoice.invoice_line:
            raise osv.except_orm('Error!', 'La factura %s no tiene lineas' % invoice.name)
        for line in invoice.invoice_line:
            if line.product_id.is_lumpsum:
                lines.append({'name': line.name, 'quantity': line.quantity, 'uos_id': line.uos_id.name, 'price_unit': line.price_unit,
                              'invoice_line_tax_id': line.invoice_line_tax_id, 'price_subtotal': line.price_subtotal, 'prod': ''})
                for lump in line.product_id.components:
                    lines.append({'name': self.get_description(lump, invoice)[0], 'quantity': lump.qty, 'uos_id': lump.uom_id.name,
                                  'price_unit': '', 'invoice_line_tax_id': '',
                                  'price_subtotal': '', 'prod': self.get_description(lump, invoice)[2]})
                continue
            lines.append({'name': line.name, 'quantity': line.quantity, 'uos_id': line.uos_id.name, 'price_unit': line.price_unit,
                          'invoice_line_tax_id': line.invoice_line_tax_id, 'price_subtotal': line.price_subtotal, 'prod': line.custom_identificator})
        return lines

    def get_description(self, lump, invoice):
        description = lump.product_id.name
        id_cliente = False
        amount = 0.00
        if invoice.contract:
            for var in invoice.contract.pricelist_id.version_id:
                if var.active:
                    for item in var.items_id:
                        if lump.product_id.id == item.product_id.id:
                            description = item.partner_desc
                            id_cliente = item.product_partner_ident
                            amount = item.fixed_price
                            break
                    break
        return description, amount, id_cliente


class report_invoice_disaggregated(osv.AbstractModel):
    _name = 'report.o2s_account_reports.report_invoice_disaggregated'
    _inherit = 'report.abstract_report'
    _template = 'o2s_account_reports.report_invoice_disaggregated'
    _wrapped_report_class = report_invoice_disaggregated_class
