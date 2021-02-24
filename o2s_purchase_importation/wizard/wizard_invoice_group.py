##########################
# -*- coding: utf-8 -*- ##
##########################

from openerp import models, fields, api
from openerp.exceptions import except_orm, Warning


# DHA -- 26-11-2018 Wizard para crear una sola factura desde importaciones y borro las creadas
class bundling_invoices_imp(models.TransientModel):
    _name = 'bundling.invoices.imp'

    date = fields.Date('Fecha de Factura', required=True)

    # @api.multi
    # def unlink(self):
    #     for record in self:
    #         if record.state not in ('draft', 'process'):
    #             raise Warning('No se puede eliminar una conciliacion que no este en los estados nueva o en proceso.')
    #         for line in record.reconcile_lines:
    #             line.unlink()
    #     return super(account_invoice, self).unlink()

    @api.multi
    def button_gruping_invoices(self):
        invoice = self.env['account.invoice']
        journal = self.env['account.journal']
        account = self.env['account.account']
        invoice_lines = list()
        for rec in self:
            inv = ''
            for order in self.env['purchase.importation'].browse(self._context['active_ids']):
                ijournal = journal.search([('code', '=', 'DIMP')])
                iaccount = account.search([('code', '=', '2010102')])
                origin = ''
                if order.state not in ('done', 'transit'):
                    raise except_orm('Error!',
                                     'No puede generar una factura de una orden que no este confirmada, orden %s' % order.name)
                inv_exist = invoice.search([('origin', '=', str(order.origin)), ('state', '=', 'draft')])
                if len(inv_exist) > 0:
                    for invoice_del in inv_exist:
                        invoice_del.unlink()
                if not order.partner_id.property_account_payable:
                    raise except_orm('Error!', 'Configure las cuentas en el proveedor %s' % order.partner_id.name)
                if order.name:
                    for oname in order:
                        origin += ', ' + oname.name
                for line in order.order_lines:
                    description = line.product_id.description if line.product_id.description else line.product_id.name
                    if line.product_id.type in ('product','consu') and line.product_id.transit_account_id:
                        cuenta_f = line.product_id.transit_account_id.id
                    elif line.product_id.type in ('product','consu') and not line.product_id.transit_account_id:
                        raise except_orm('Error!', 'Configure las cuentas transito en el producto %s' % line.product_id.name)
                    if line.product_id.type in ('service') and line.product_id.property_account_expense:
                        cuenta_f = line.product_id.property_account_expense.id
                    elif line.product_id.type in ('service') and not line.product_id.property_account_expense:
                        raise except_orm('Error!', 'Configure las cuentas gasto en el producto %s' % line.product_id.name)
                    res = {'product_id': line.product_id.id, 'name': description, 'account_id': cuenta_f, 'quantity': line.product_qty,
                           'uos_id': line.product_uom.id, 'price_unit': line.price_unit}
                    invoice_lines.append(res)
            inv = invoice.create({'date_invoice': rec.date, 'partner_id': order.partner_id.id,
                                  'account_id': order.partner_id.property_account_payable.id,
                                  'document_type': order.partner_id.document_type.id,
                                  'tax_support': order.partner_id.tax_support.id,
                                  'type': 'in_invoice', 'origin': origin, 'journal_id': ijournal.id,
                                  'account_id': iaccount.id})

            for item in invoice_lines:
                item.update({'invoice_id': inv.id})
                self.env['account.invoice.line'].create(item)
            for order in self.env['purchase.importation'].browse(self._context['active_ids']):
                invoice_ids = [i.id for i in order.invoice_ids]
                invoice_ids.append(inv.id)
                order.invoice_ids = [[6, False, invoice_ids]]

        return True
