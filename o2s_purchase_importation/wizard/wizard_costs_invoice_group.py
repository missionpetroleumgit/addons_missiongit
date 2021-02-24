##########################
# -*- coding: utf-8 -*- ##
##########################

from openerp import models, fields, api
from openerp.exceptions import except_orm, Warning


# DHA -- 26-11-2018 Wizard para crear una sola factura desde importaciones y borro las creadas
class transit_importation_expenses(models.TransientModel):
    _name = 'transit.importation.expenses'

    partner_id = fields.Many2one('res.partner', 'Proveedor', domain=[('supplier', '=', True)])
    product_id = fields.Many2one('product.product', 'Producto', domain=[('is_imported', '=', True)])
    amount = fields.Float('Valor')
    invoiced = fields.Boolean('Facturado')
    transit_importation_id = fields.Many2one(comodel_name='generate.expenses.grouping.invoice',
                                             string='ID Modelo transitorio')
    importation_id = fields.Many2one(comodel_name='purchase.importation', string='Importacion')
    company_id = fields.Many2one('res.company', string='Compania', related='importation_id.company_id')
    invoice_number = fields.Char('No. Factura')


class generate_expenses_grouping_invoice(models.TransientModel):
    _name = 'generate.expenses.grouping.invoice'

    date = fields.Date('Fecha de Factura', required=True)
    cost_ids = fields.One2many('transit.importation.expenses', 'transit_importation_id', 'Costos de Importacion',
                               ondelete='cascade')

    @api.multi
    def button_generate_expenses_grouping_invoice(self):
        importation = self.env['importation.order']
        invoice = self.env['account.invoice']
        journal = self.env['account.journal']
        account = self.env['account.account']
        product = self.env['product.product']
        partner = self.env['res.partner']

        expense = list()
        invoice_lines = list()
        for rec in self:
            ijournal = journal.search([('code', '=', 'DIMP')])
            iaccount = account.search([('code', '=', '2010102')])
            inv = ''
            for order in self.env['purchase.importation'].browse(self._context['active_ids']):
                if order.state not in ('aduana', 'transit'):
                    raise except_orm('Error!',
                                     'No puede agrupar facturas o generar costos de una orden que no este en '
                                     'transito o confirmada, orden %s' % order.name)
            for cost in rec.cost_ids:
                if cost.product_id.type == 'product' and not cost.product_id.property_account_expense:
                    raise except_orm('Error!',
                                     'Configure las cuentas gasto en el producto %s' % cost.product_id.name)

                res = {'product_id': cost.product_id.id,
                       'partner_id': cost.partner_id.id,
                       'invoiced': True,
                       'amount': cost.amount,
                       'importation_id': cost.importation_id.id,
                       'invoice': cost.invoice_number
                       }

                expense.append(res)
            for item in expense:
                c_amount = 0
                no_invoice = ''
                self.env['importation.expenses'].create(item)
                partner1 = item.get('partner_id')
                if not cost.partner_id.property_account_payable:
                    raise except_orm('Error!', 'Configure las cuentas en el proveedor %s' % cost.partner_id.name)
                for partners in expense:
                    imp_partner_id = partners.get('partner_id')
                    imp_id = partners.get('importation_id')
                    prod_id = partners.get('product_id')
                    productid = product.search([('id', '=', prod_id)])
                    importation_id = importation.search([('id', '=', imp_id)])
                    if productid:
                        if productid.property_account_expense.id and productid.type in ('consu', 'product', 'service'):
                            account_id = productid.property_account_expense.id
                        else:
                            raise except_orm('Error!',
                                             'Configure las cuentas gasto en el producto %s' % productid.name)
                    if partners.get('partner_id') == partner1:
                        c_amount += partners.get('amount')
                        no_invoice = partners.get('invoice')
                    res1 = {'product_id': productid.id,
                            'name': productid.name,
                            'uos_id': productid.uos_id.id,
                            'price_unit': c_amount,
                            'quantity': 1,
                            'account_id': account_id,
                            'partner_id': imp_partner_id,
                            'origin': importation_id.id,
                            }
                    invoice_lines.append(res1)

            for invoice_items in invoice_lines:
                self.env['account.invoice.line'].create(invoice_items)
                imp_order_id = invoice_items.get('origin')
                importation = importation.search([('id', '=', imp_order_id)])
                partner_id = partner.search([('id', '=', invoice_items.get('partner_id'))])

                inv = invoice.create({'date_invoice': rec.date,
                                      'partner_id': partner_id.id,
                                      'account_id': iaccount.id,
                                      'document_type': partner_id.document_type.id,
                                      'tax_support': partner_id.tax_support.id,
                                      'type': 'in_invoice',
                                      'origin': importation.name,
                                      'journal_id': ijournal.id,
                                      'account_id': iaccount.id})
                invoice_items.update({'invoice_id': inv.id})
            for order in self.env['purchase.importation'].browse(self._context['active_ids']):
                invoice_ids = [i.id for i in order.invoice_ids]
                for invoices in inv:
                    invoice_ids.append(invoices.id)
                order.invoice_ids = [[6, False, invoice_ids]]

        return True
