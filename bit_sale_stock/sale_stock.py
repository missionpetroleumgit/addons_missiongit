# -*- coding: utf-8 -*-

from openerp import api, fields, models
from openerp.tools.translate import _
from openerp.exceptions import except_orm, Warning, RedirectWarning

class product_template(models.Model):
    _inherit = 'product.template'
    
    is_reemb = fields.Boolean(string='Reembolsable')
    property_account_cost_id = fields.Many2one('account.account', company_dependent=True,
        string="Cost Account", oldname="property_account_income",
        help="This account will be used for invoices instead of the default one to value sales for the current product.")    


class product_product(models.Model):
    _inherit = 'product.product'

    # @api.model
    # def search(self, args=[], offset=0, limit=None, order=None, context=None, count=False):
    #     prod_list = []
    #     pricelist_id = False
    #     if 'tarifa' in self._context and self._context.get('tarifa'):
    #         if 'pricelist' in self._context and self._context.get('pricelist'):
    #             pricelist_id = self._context.get('pricelist')
    #             for pricelist in self.env['product.pricelist'].browse(pricelist_id):
    #                 for pl_version in pricelist.version_id:
    #                     for pl_item in pl_version.items_id:
    #                         if pl_item.product_id:
    #                             prod_list.append(pl_item.product_id.id)
    #         if prod_list:
    #             args += [('id', 'in', prod_list)]
    #     res = super(product_product, self).search(args)
    #     return res
    
class sale_order(models.Model):
    _inherit = 'sale.order'
    
    payment_term = fields.Many2one('account.payment.term', store=True, readonly=True,
                                      related='partner_id.property_payment_term')
    fiscal_position = fields.Many2one('account.fiscal.position', store=True, readonly=True,
                                      related='partner_id.property_account_position')
    
    @api.v7
    def onchange_pricelist_id(self, cr, uid, ids, pricelist_id, order_lines, context=None):
#         res = super(sale_order, self).onchange_pricelist_id(cr, uid, ids, pricelist_id, order_lines, context)
        curr_id = self.pool.get('product.pricelist').browse(cr, uid, pricelist_id, context=context).currency_id.id
        res = { 'value' : { 'currency_id' : curr_id, 'order_line' : [] } }
        return res


class sale_order_line(models.Model):
    _inherit = 'sale.order.line'
    
    is_reemb = fields.Boolean(string='Reembolsable')

    @api.v7    
    def product_id_change_with_wh(self, cr, uid, ids, pricelist, product, qty=0, uom=False, qty_uos=0, \
                                  uos=False, name='', partner_id=False, lang=False, update_tax=True, \
                                  date_order=False, packaging=False, fiscal_position=False, flag=False, \
                                  warehouse_id=False, context=None):
        res = super(sale_order_line, self).product_id_change_with_wh(cr, uid, ids, pricelist, product, qty, \
                            uom, qty_uos, uos, name, partner_id, lang, update_tax, date_order, packaging, \
                            fiscal_position, flag, warehouse_id, context)
        if product:
            brw_prod = self.pool.get('product.product').browse(cr, uid, product, context)
            res.get('value').update( { 'is_reemb': brw_prod.product_tmpl_id.is_reemb } )
        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
