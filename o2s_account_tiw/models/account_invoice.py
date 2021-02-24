# -*- coding: utf-8 -*-
###############################
#  Objetos de Servicio para petroleras  #
###############################

from openerp import models, fields, api
from openerp.exceptions import except_orm, Warning
import openerp.addons.decimal_precision as dp


class account_invoice(models.Model):
    _inherit = 'account.invoice'

    ticket = fields.Many2one('service.ticket', 'No. Pedido')
    contract = fields.Many2one('account.analytic.account', 'Contrato')
    project = fields.Many2one('account.analytic.account', 'Proyecto')
    field = fields.Many2one('service.field', 'Campo')
    well = fields.Many2one('service.well', 'Pozo')
    rig = fields.Many2one('service.rig', 'Taladro')
    oc = fields.Char('OC')
    oet = fields.Char('OET')
    pre_invoice = fields.Char('Pre-factura')
    guiaremision_ref = fields.Char('Guia Remision')
    ticket_ids = fields.Many2many('service.ticket', 'service_ticket_invoice_rel', 'invoice_id', 'ticket_id', string='Tickets Agrupados')

class account_invoice_line(models.Model):
    _inherit = 'account.invoice.line'

    custom_identificator = fields.Char('Id Cliente')

    @api.model
    def move_line_get(self, invoice_id):
        inv = self.env['account.invoice'].browse(invoice_id)
        currency = inv.currency_id.with_context(date=inv.date_invoice)
        company_currency = inv.company_id.currency_id
        res = []
        #Validacion ticket del mismo contrato
        contract_id = False
        for tick in inv.ticket_ids:
            if contract_id != tick.contract_id and contract_id != False:
                raise except_orm('Error!', 'Tickets no pertenecen al mismo contrato')
            contract_id = tick.contract_id

        for line in inv.invoice_line:
            if line.invoice_id.type in ('out_invoice', 'out_refund'):
                if line.product_id.is_lumpsum:
                    ticket_obj = self.env['service.ticket'].search([('id','in',inv.ticket_ids.ids)], limit = 1)
                    if not ticket_obj.contract_id:
                        raise except_orm('Error!', 'No puede facturar un lumpsum sin definir contrato en la factura')
                    pricelist_item = self.env['product.pricelist.item']
                    amount_lumpsum = 0.00
                    for cmp in line.product_id.components:
                        pricelist = pricelist_item.search([('price_version_id.pricelist_id', '=', ticket_obj.contract_id.pricelist_id.id), ('price_version_id.active', '=', True),
                                                           ('product_id', '=', cmp.product_id.id)])
                        if not pricelist:
                            raise except_orm('Error!', 'El componente %s no se encuentra definido en la lista de precios' % cmp.product_id.name)
                        if len(pricelist) > 1:
                            raise except_orm('Error!', 'Existen dos items en la variante de lista de precios con el mismo producto: %s' % cmp.product_id.name)
                        amount_lumpsum += pricelist.fixed_price * cmp.qty
                    for cmp2 in line.product_id.components:
                        pricelist = pricelist_item.search([('price_version_id.pricelist_id', '=', ticket_obj.contract_id.pricelist_id.id), ('price_version_id.active', '=', True),
                                                           ('product_id', '=', cmp2.product_id.id)])
                        mres = self.move_line_get_item_lumpsum(line, cmp2, (cmp2.qty*pricelist.fixed_price)/amount_lumpsum)
                        res.append(mres)
                else:
                    mres = self.move_line_get_item(line)
                    mres['invl_id'] = line.id
                    res.append(mres)
            else:
                mres = self.move_line_get_item(line)
                mres['invl_id'] = line.id
                res.append(mres)
            tax_code_found = False
            taxes = line.invoice_line_tax_id.compute_all(
                (line.price_unit * (1.0 - (line.discount or 0.0) / 100.0)),
                line.quantity, line.product_id, inv.partner_id)['taxes']
            for tax in taxes:
                if inv.type in ('out_invoice', 'in_invoice'):
                    tax_code_id = tax['base_code_id']
                    tax_amount = tax['price_unit'] * line.quantity * tax['base_sign']
                else:
                    tax_code_id = tax['ref_base_code_id']
                    tax_amount = tax['price_unit'] * line.quantity * tax['ref_base_sign']

                if tax_code_found:
                    if not tax_code_id:
                        continue
                    res.append(dict(mres))
                    res[-1]['price'] = 0.0
                    res[-1]['account_analytic_id'] = False
                elif not tax_code_id:
                    continue
                tax_code_found = True

                res[-1]['tax_code_id'] = tax_code_id
                res[-1]['tax_amount'] = currency.compute(tax_amount, company_currency)
        return res

    @api.model
    def move_line_get_item_lumpsum(self, line, cmp, factor):
        precision = self.env['decimal.precision'].search([('name', '=', 'Account')]).digits
        return {
            'type': 'src',
            'name': cmp.product_id.name.split('\n')[0][:64],
            'price_unit': round(line.price_unit * factor, precision),
            'quantity': cmp.qty,
            'price': round(line.price_subtotal * factor, precision),
            'account_id': cmp.product_id.property_account_income.id,
            'product_id': cmp.product_id.id,
            'uos_id': cmp.product_id.uos_id.id,
            'account_analytic_id': line.account_analytic_id.id,
            'taxes': cmp.product_id.taxes_id,
        }

