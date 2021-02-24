# -*- coding: utf-8 -*-
from openerp import models, fields, api
from openerp.exceptions import except_orm, Warning
from datetime import datetime


class provision_entries(models.TransientModel):
    _inherit = 'provision.entries'

    def convert_lines(self, line, type, move_obj):
        res = []
        precision = self.env['decimal.precision'].search([('name', '=', 'Account')]).digits
        if type == 'out_invoice':
            pricelist_item = self.env['product.pricelist.item']
            count = 0
            for ticket in line.invoice_id.ticket_ids:
                if count == 0:
                    contract = ticket.contract_id
                    count = 1

            if 'is_lumpsum' in line.product_id._fields and line.product_id.is_lumpsum:
                total = 0.00
                if not contract:
                    raise except_orm('Error!', 'No puede provisionar el lumpsum %s sin un contrato definido en la factura' % line.product_id.name)
                for item in line.product_id.components:
                    pricelist = pricelist_item.search([('price_version_id.pricelist_id', '=', contract.pricelist_id.id), ('price_version_id.active', '=', True),
                                                       ('product_id', '=', item.product_id.id)])
                    if not pricelist:
                        raise except_orm('Error!', 'El componente %s no se encuentra definido en la lista de precios' % item.product_id.name)
                    if len(pricelist) > 1:
                        raise except_orm('Error!', 'Existen dos items en la variante de lista de precios con el mismo producto: %s' % item.product_id.name)
                    total += pricelist.fixed_price * item.qty
                for item2 in line.product_id.components:
                    if not item2.product_id.property_account_income:
                        raise except_orm('Error!', 'Configure la cuenta de ingreso del producto %s' % item2.product_id.name)
                    pricelist = pricelist_item.search([('price_version_id.pricelist_id', '=', contract.pricelist_id.id), ('price_version_id.active', '=', True),
                                                       ('product_id', '=', item2.product_id.id)])
                    res.append({'name': 'Prov.:' + line.invoice_id.origin if line.invoice_id.origin else '', 'partner_id': line.invoice_id.partner_id.id,
                                'account_id': item2.product_id.property_account_income.id, 'debit': 0.00, 'credit': round(item2.qty*pricelist.fixed_price/total * line.price_subtotal, precision),
                                'move_id': move_obj.id})
            else:
                if not line.product_id.property_account_income:
                        raise except_orm('Error!', 'Configure la cuenta de ingreso del producto %s' % line.product_id.name)
                if contract:
                    pricelist = pricelist_item.search([('price_version_id.pricelist_id', '=', contract.pricelist_id.id), ('price_version_id.active', '=', True),
                                                       ('product_id', '=', line.product_id.id)])
                    if not pricelist:
                        raise except_orm('Error!', 'El producto %s no se encuentra definido en la lista de precios correspondiente al contrato seleccionado en la factura' % line.product_id.name)
                    credit = pricelist.fixed_price * line.quantity
                    if line.discount:
                        discount = credit * line.discount/100
                        credit -= discount
                else:
                    credit = line.price_subtotal
                res.append({'name': 'Prov.:' + line.invoice_id.origin if line.invoice_id.origin else '', 'partner_id': line.invoice_id.partner_id.id,
                            'account_id': line.product_id.property_account_income.id, 'debit': 0.00, 'credit': credit,
                            'move_id': move_obj.id})
        elif type == 'in_invoice':
            res.append({'name': 'Prov.:' + line.invoice_id.origin if line.invoice_id.origin else '', 'partner_id': line.invoice_id.partner_id.id,
                        'account_id': line.product_id.property_account_expense.id, 'debit': line.price_subtotal, 'credit': 0.00,
                        'move_id': move_obj.id})
        return res



