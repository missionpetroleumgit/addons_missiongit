##########################
# -*- coding: utf-8 -*- ##
##########################


from openerp import models, fields, api
from openerp.exceptions import except_orm, Warning
import openerp.addons.decimal_precision as dp


class account_invoice_line_transit(models.TransientModel):
    _name = 'account.invoice.line.transit'

    product_id = fields.Many2one('product.product', 'Product', domain=[('purchase_ok', '=', True)], change_default=True)
    name = fields.Text('Description', required=True)
    quantity = fields.Float('Quantity', digits_compute=dp.get_precision('Product Unit of Measure'), required=True)
    uos_id = fields.Many2one('product.uom', 'Product Unit of Measure', required=True)
    price_unit = fields.Float('Unit Price', required=True, digits_compute=dp.get_precision('Product Price'))
    account_id = fields.Many2one('account.account', 'Cuenta Contable')
    transit_invoice_id = fields.Many2one('generate.partial.invoice.imp', 'ID transitorio')
    invoice_id = fields.Many2one('account.invoice', 'Factura')
    to_generate = fields.Boolean('Item')
    importation_id = fields.Many2one('importation.order', 'Importacion')
    subtotal_importation = fields.Float('Subtotal')
    factured = fields.Boolean('Linea Facturada')


# CSV: 15-09-2017 Creo wizard para crear factura desde orden importación
class generate_partial_invoice_imp(models.TransientModel):
    _name = 'generate.partial.invoice.imp'

    date_start = fields.Date('Fecha de Factura', required=True)
    invoice_line_ids = fields.One2many('account.invoice.line.transit', 'transit_invoice_id', 'Lineas de Importacion')
    group_bills = fields.Boolean('Agrupar facturas')

    @api.multi
    def check_same_partner(self):
        cont = 0
        orders = self.env['importation.order'].browse(self._context['active_ids'])
        p1 = orders.partner_id[0]
        for record in orders:
            if p1 != record.partner_id:
                return False
                break
            if p1 == record.partner_id:
                cont += 1
            if cont > 1:
                return True

    @api.onchange('invoice_line_ids')
    def onchange_requisition_order_id(self):
        line_ids = []
        for order in self.env['importation.order'].browse(self._context['active_ids']):
            for line in order.order_lines:
                if not line.factured:
                    taxes = list()
                    taxes.append([6, False, [tax.id for tax in line.taxes_id]])
                    vals = (0, 0, {'product_id': line.product_id.id, 'company_id': line.company_id.id,
                                   'importation_id': line.importation_id.id, 'quantity': line.product_qty,
                                   'uos_id': line.product_uom.id, 'subtotal_importation': line.subtotal_importation,
                                   'name': line.name, 'taxes_id': taxes, 'analytics_id': line.analytics_id.id,
                                   'price_unit': line.price_unit, 'imported': line.imported,
                                   'date_planned': line.date_planned, 'factured': line.factured
                                   })
                    line_ids.append(vals)
            self.update({'invoice_line_ids': line_ids})

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
                fact = 0
                if order.state != 'done':
                    raise except_orm('Error!', 'No puede generar una factura de una '
                                               'orden que no este confirmada, orden %s' % order.name)
                for line in order.order_lines:
                    if line.factured:
                        fact += 1
                    if len(order.order_lines) == fact:
                        raise except_orm('Error!', 'Ya fueron facturadas las líneas seleccionadas, '
                                                   'Importacion' % order.name)
                if not order.partner_id.property_account_payable:
                    raise except_orm('Error!', 'Configure las cuentas en el proveedor %s' % order.partner_id.name)
                inv = invoice.create({'date_invoice': rec.date_start, 'partner_id': order.partner_id.id,
                                      'account_id': order.partner_id.property_account_payable.id,
                                      'document_type': order.partner_id.document_type.id,
                                      'tax_support': order.partner_id.tax_support.id, 'type': 'in_invoice',
                                      'origin': order.name, 'journal_id': ijournal.id, 'account_id': iaccount.id})
                for line in self.invoice_line_ids:
                    if line.importation_id.id == order.id:
                        if line.to_generate and not line.factured:
                            description = line.product_id.description if line.product_id.description else line.product_id.name
                            if line.product_id.type in ('product','consu') and line.product_id.transit_account_id:
                                cuenta_f = line.product_id.transit_account_id.id
                            elif line.product_id.type in ('product','consu') and not line.product_id.transit_account_id:
                                raise except_orm('Error!', 'Configure las cuentas de transito '
                                                           'en el producto %s' % line.product_id.name)
                            if line.product_id.type in ('service') and line.product_id.property_account_expense:
                                cuenta_f = line.product_id.property_account_expense.id
                            elif line.product_id.type in ('service') and not line.product_id.property_account_expense:
                                raise except_orm('Error!', 'Configure las cuentas de gasto '
                                                           'en el producto %s' % line.product_id.name)
                            res = {'product_id': line.product_id.id,
                                   'name': description,
                                   'account_id': cuenta_f,
                                   'quantity': line.quantity,
                                   'uos_id': line.uos_id.id,
                                   'price_unit': line.price_unit,
                                   'invoice_id': inv.id
                                   }
                            invoice_line.create(res)
                            line.update({'factured': True})
        return True
