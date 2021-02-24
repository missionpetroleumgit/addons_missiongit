import itertools
from lxml import etree

from openerp import models, fields, api, _
from openerp.exceptions import except_orm, Warning, RedirectWarning
from openerp.tools import float_compare
import openerp.addons.decimal_precision as dp


class account_invoice_line(models.Model):
    _inherit = "account.invoice.line"

    reemb_product = fields.Boolean('Reem', default=False)
    third_partner_id = fields.Many2one('res.partner', 'Tercero', domain=[('is_third_partner', '=', True)])

    @api.multi
    def product_id_change(self, product, uom_id, qty=0, name='', type='out_invoice',
            partner_id=False, fposition_id=False, price_unit=False, currency_id=False,
            company_id=None):
        if product:
            res = super(account_invoice_line, self).product_id_change(product, uom_id, qty, name, type,
                                                                      partner_id, fposition_id, price_unit, currency_id, company_id)
            prod_obj = self.env['product.product'].browse(product)
            if prod_obj.product_tmpl_id.is_reemb:
                res['value'].update({'reemb_product': True})
            else:
                res['value'].update({'reemb_product': False})
            return res
        return super(account_invoice_line, self).product_id_change(product, uom_id, qty, name, type,
            partner_id, fposition_id, price_unit, currency_id, company_id)

#     @api.multi
#     def product_id_change(self, product, uom_id, qty=0, name='', type='out_invoice',
#             partner_id=False, fposition_id=False, price_unit=False, currency_id=False,
#             company_id=None):
# 
#         if product:
#             res = super(account_invoice_line, self).product_id_change(product, uom_id, 0, '', 'out_invoice',
#                                                                       partner_id, fposition_id, price_unit, currency_id, company_id)
#             prod_obj = self.env['product.product'].browse(product)
#             if prod_obj.product_tmpl_id.is_reemb:
#                 res['value'].update({'reemb_product': True})
#             else:
#                 res['value'].update({'reemb_product': False})
#             return res
#         return super(account_invoice_line, self).product_id_change(product, uom_id, 0, '', 'out_invoice',
#                                                                    partner_id, fposition_id, price_unit, currency_id, company_id)

    @api.model
    def move_line_get_item(self, line):
        return {
            'type': 'src',
            'name': line.name.split('\n')[0][:64],
            'price_unit': line.price_unit,
            'quantity': line.quantity,
            'price': line.price_subtotal,
            'account_id': line.account_id.id,
            'product_id': line.product_id.id,
            'uos_id': line.uos_id.id,
            'account_analytic_id': line.account_analytic_id.id,
            'taxes': line.invoice_line_tax_id,
            'third_partner_id': line.third_partner_id.id,
            'reemb_product': line.reemb_product
        }
