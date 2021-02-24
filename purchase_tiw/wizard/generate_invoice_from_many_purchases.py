##########################
# -*- coding: utf-8 -*- ##
##########################


from openerp import models, fields, api
from openerp.exceptions import except_orm, Warning


class generate_invoice(models.TransientModel):
    _name = 'generate.invoice'

    name = fields.Char('description')

    def check_partner(self, orders):
        partners = list()
        for order in self.pool.get['purchase.order'].browse(orders):
            if order.partner_id.id not in partners:
                partners.append(order.partner_id.id)
            else:
                raise except_orm('Error!', 'No puede generar ordenes de compra de distintos proveedores')
        return True

    @api.multi
    def generate_invoice(self):
        ids = self._context['active_ids']
        invoice_lines = list()
        for rec in self:
            origin = ''
            #self.check_partner(self.env['purchase.order'].browse(ids))
            for po in self.env['purchase.order'].browse(ids):
                if po.state != 'approved' and po.state_manager != 'approved':
                    raise except_orm('Error!', 'Solo se puede generar factura de compras confirmadas y aprobadas, compra %s no cumple requisitos' % po.name)
                origin += po.name + ','
                for line in po.order_line:
                    if line.product_id.type != 'service':
                        raise except_orm('Error!', 'Solo se puede generar factura desde compras de servicios, producto %s no es de servicio' % line.product_id.name)
                    lines = {
                        'product_id': line.product_id.id,
                        'name': line.name,
                        'account_id': line.product_id.property_account_expense.id,
                        'quantity': line.product_qty,
                        'uos_id': line.product_uom.id,
                        'price_unit': line.price_unit,
                        'discount': line.percent,
                        'invoice_line_tax_id': [[6, 0, [tax.id for tax in line.taxes_id]]],
                    }
                    invoice_lines.append(lines)
            inv = self.env['account.invoice'].create({'partner_id': po.partner_id.id, 'origin': origin, 'account_id': po.partner_id.property_account_payable.id,
                                                      'document_type': po.partner_id.document_type.id, 'tax_support': po.partner_id.tax_support.id, 'type': 'in_invoice'})
            for item in invoice_lines:
                item.update({'invoice_id': inv.id})
                self.env['account.invoice.line'].create(item)

        return True
