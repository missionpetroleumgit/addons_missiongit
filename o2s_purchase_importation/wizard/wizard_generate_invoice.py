##########################
# -*- coding: utf-8 -*- ##
##########################


from openerp import models, fields, api
from openerp.exceptions import except_orm, Warning

# CSV: 15-09-2017 Creo wizard para crear factura desde orden importación

class generate_invoice_imp(models.TransientModel):
    _name = 'generate.invoice.imp'

    date_start = fields.Date('Fecha de Factura', required=True)

    @api.multi
    def button_gen_invoice(self):
        invoice = self.env['account.invoice']
        invoice_line = self.env['account.invoice.line']
        journal = self.env['account.journal']
        account = self.env['account.account']
        for rec in self:
            for order in self.env['importation.order'].browse(self._context['active_ids']):
                ijournal = journal.search([('code', '=', 'DIMP')])
                iaccount = account.search([('code', '=', '2010102')])
                print "id diario", ijournal.id
                print "id diario", ijournal.name
                print "order", order
                if order.state != 'done':
                    raise except_orm('Error!', 'No puede generar una factura de una orden que no este confirmada, orden %s' % order.name)
                inv_exist = invoice.search([('origin', '=', order.name)])
                if len(inv_exist) > 0:
                    raise except_orm('Advertencia!', 'Ya existe una factura creada desde la orden %s, primero borrela para generar nuevamente' % order.name)
                if not order.partner_id.property_account_payable:
                    raise except_orm('Error!', 'Configure las cuentas en el proveedor %s' % order.partner_id.name)
                inv = invoice.create({'date_invoice': rec.date_start, 'partner_id': order.partner_id.id, 'account_id': order.partner_id.property_account_payable.id,
                                      'document_type': order.partner_id.document_type.id, 'tax_support': order.partner_id.tax_support.id,
                                      'type': 'in_invoice', 'origin': order.name, 'journal_id': ijournal.id, 'account_id': iaccount.id})
                for line in order.order_lines:
                    description = line.product_id.description if line.product_id.description else line.product_id.name
                    print "line.product_id.property_stock_account_input", line.product_id.property_stock_account_input
                    print "line.product_id", line.product_id.id
                    if line.product_id.type in ('product','consu') and line.product_id.transit_account_id:
                        cuenta_f = line.product_id.transit_account_id.id
                    elif line.product_id.type in ('product','consu') and not line.product_id.transit_account_id:
                        raise except_orm('Error!', 'Configure las cuentas transito en el producto %s' % line.product_id.name)
                    if line.product_id.type in ('service') and line.product_id.property_account_expense:
                        cuenta_f = line.product_id.property_account_expense.id
                    elif line.product_id.type in ('service') and not line.product_id.property_account_expense:
                        raise except_orm('Error!', 'Configure las cuentas gasto en el producto %s' % line.product_id.name)
                    res = {'product_id': line.product_id.id, 'name': description, 'account_id': cuenta_f, 'quantity': line.product_qty,
                           'uos_id': line.product_uom.id, 'price_unit': line.price_unit, 'invoice_id': inv.id}
                    invoice_line.create(res)

        return True