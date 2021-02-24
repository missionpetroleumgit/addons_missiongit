# -*- coding: utf-8 -*-
###############################
#  Lista de precios para petroleras  #
###############################
from openerp import tools
from openerp import models, fields, api
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp.exceptions import except_orm
import time


class product_pricelist_item(osv.osv):
    _inherit = 'product.pricelist.item'

    def _price_field_get(self, cr, uid, context=None):
        pt = self.pool.get('product.price.type')
        ids = pt.search(cr, uid, [], context=context)
        result = []
        for line in pt.browse(cr, uid, ids, context=context):
            result.append((line.id, line.name))

        result.append((-1, _('Other Pricelist')))
        result.append((-2, _('Supplier Prices on the product form')))
        result.append((-3, _('Precio fijo')))
        return result

    _columns = {
        'base': fields.selection(_price_field_get, 'Based on', required=True, size=-1, help="Base price for computation."),
        'fixed_price': fields.float('Precio Fijo', digits=(9, 2)),
        'product_partner_ident': fields.char('Identificacion Cliente', required=True),
        'partner_desc': fields.char('Descripcion del Cliente', required=True),
        # 'o2s_id': fields.integer('O2s sequence'),
    }

    def product_id_change(self, cr, uid, ids, product_id, context=None):
        res = super(product_pricelist_item, self).product_id_change(cr, uid, ids, product_id, context)
        if 'value' in res and product_id:
            product = self.pool.get('product.product').browse(cr, uid, product_id)
            res['value']['partner_desc'] = product.name
        return res


class product_pricelist_version(osv.osv):
    _inherit = "product.pricelist.version"

    _columns = {

        'code': fields.char('Codigo de Contrato', required=True)

            }




class product_pricelist(osv.osv):
    _inherit = 'product.pricelist'

    _columns = {
        'pricelist_state': fields.selection([('draft', 'Borrador'), ('confirm', 'Confirmada')], 'Estado'),
    }

    _defaults = {
        'pricelist_state': 'draft'
    }

    @api.multi
    def pricelist_confirm(self):
        for rec in self:
            rec.pricelist_state = 'confirm'
        # return estado

    @api.multi
    def pricelist_to_draft(self):
        for rec in self:
            rec.pricelist_state = 'draft'
        # return estado

    def _price_rule_get_multi(self, cr, uid, pricelist, products_by_qty_by_partner, context=None):
        context = context or {}
        date = context.get('date') or time.strftime('%Y-%m-%d')
        date = date[0:10]

        products = map(lambda x: x[0], products_by_qty_by_partner)
        currency_obj = self.pool.get('res.currency')
        product_obj = self.pool.get('product.template')
        product_uom_obj = self.pool.get('product.uom')
        price_type_obj = self.pool.get('product.price.type')

        if not products:
            return {}

        version = False
        for v in pricelist.version_id:
            if ((v.date_start is False) or (v.date_start <= date)) and ((v.date_end is False) or (v.date_end >= date)):
                version = v
                break
        if not version:
            raise osv.except_osv(_('Warning!'), _("At least one pricelist has no active version !\nPlease create or activate one."))
        categ_ids = {}
        for p in products:
            categ = p.categ_id
            while categ:
                categ_ids[categ.id] = True
                categ = categ.parent_id
        categ_ids = categ_ids.keys()

        is_product_template = products[0]._name == "product.template"
        if is_product_template:
            prod_tmpl_ids = [tmpl.id for tmpl in products]
            # all variants of all products
            prod_ids = [p.id for p in
                        list(chain.from_iterable([t.product_variant_ids for t in products]))]
        else:
            prod_ids = [product.id for product in products]
            prod_tmpl_ids = [product.product_tmpl_id.id for product in products]

        # Load all rules
        cr.execute(
            'SELECT i.id '
            'FROM product_pricelist_item AS i '
            'WHERE (product_tmpl_id IS NULL OR product_tmpl_id = any(%s)) '
            'AND (product_id IS NULL OR (product_id = any(%s))) '
            'AND ((categ_id IS NULL) OR (categ_id = any(%s))) '
            'AND (price_version_id = %s) '
            'ORDER BY sequence, min_quantity desc',
            (prod_tmpl_ids, prod_ids, categ_ids, version.id))

        item_ids = [x[0] for x in cr.fetchall()]
        items = self.pool.get('product.pricelist.item').browse(cr, uid, item_ids, context=context)

        price_types = {}

        results = {}
        for product, qty, partner in products_by_qty_by_partner:
            results[product.id] = 0.0
            rule_id = False
            price = False

            # Final unit price is computed according to `qty` in the `qty_uom_id` UoM.
            # An intermediary unit price may be computed according to a different UoM, in
            # which case the price_uom_id contains that UoM.
            # The final price will be converted to match `qty_uom_id`.
            qty_uom_id = context.get('uom') or product.uom_id.id
            price_uom_id = product.uom_id.id
            qty_in_product_uom = qty
            if qty_uom_id != product.uom_id.id:
                try:
                    qty_in_product_uom = product_uom_obj._compute_qty(
                        cr, uid, context['uom'], qty, product.uom_id.id or product.uos_id.id)
                except except_orm:
                    # Ignored - incompatible UoM in context, use default product UoM
                    pass

            for rule in items:
                if rule.min_quantity and qty_in_product_uom < rule.min_quantity:
                    continue
                if is_product_template:
                    if rule.product_tmpl_id and product.id != rule.product_tmpl_id.id:
                        continue
                    if rule.product_id and \
                            (product.product_variant_count > 1 or product.product_variant_ids[0].id != rule.product_id.id):
                        # product rule acceptable on template if has only one variant
                        continue
                else:
                    if rule.product_tmpl_id and product.product_tmpl_id.id != rule.product_tmpl_id.id:
                        continue
                    if rule.product_id and product.id != rule.product_id.id:
                        continue

                if rule.categ_id:
                    cat = product.categ_id
                    while cat:
                        if cat.id == rule.categ_id.id:
                            break
                        cat = cat.parent_id
                    if not cat:
                        continue

                if rule.base == -1:
                    if rule.base_pricelist_id:
                        price_tmp = self._price_get_multi(cr, uid,
                                                          rule.base_pricelist_id, [(product,
                                                                                    qty, partner)], context=context)[product.id]
                        ptype_src = rule.base_pricelist_id.currency_id.id
                        price_uom_id = qty_uom_id
                        price = currency_obj.compute(cr, uid,
                                                     ptype_src, pricelist.currency_id.id,
                                                     price_tmp, round=False,
                                                     context=context)
                elif rule.base == -2:
                    seller = False
                    for seller_id in product.seller_ids:
                        if (not partner) or (seller_id.name.id != partner):
                            continue
                        seller = seller_id
                    if not seller and product.seller_ids:
                        seller = product.seller_ids[0]
                    if seller:
                        qty_in_seller_uom = qty
                        seller_uom = seller.product_uom.id
                        if qty_uom_id != seller_uom:
                            qty_in_seller_uom = product_uom_obj._compute_qty(cr, uid, qty_uom_id, qty, to_uom_id=seller_uom)
                        price_uom_id = seller_uom
                        for line in seller.pricelist_ids:
                            if line.min_quantity <= qty_in_seller_uom:
                                price = line.price
                elif rule.base == -3:
                    price = currency_obj.compute(cr, uid, rule.base_pricelist_id.currency_id.id, pricelist.currency_id.id,
                                                 rule.fixed_price, round=False, context=context)
                else:
                    if rule.base not in price_types:
                        price_types[rule.base] = price_type_obj.browse(cr, uid, int(rule.base))
                    price_type = price_types[rule.base]

                    # price_get returns the price in the context UoM, i.e. qty_uom_id
                    price_uom_id = qty_uom_id
                    price = currency_obj.compute(
                        cr, uid,
                        price_type.currency_id.id, pricelist.currency_id.id,
                        product_obj._price_get(cr, uid, [product], price_type.field, context=context)[product.id],
                        round=False, context=context)

                if price is not False:
                    price_limit = price
                    price = price * (1.0+(rule.price_discount or 0.0))
                    if rule.price_round:
                        price = tools.float_round(price, precision_rounding=rule.price_round)

                    convert_to_price_uom = (lambda price: product_uom_obj._compute_price(
                        cr, uid, product.uom_id.id,
                        price, price_uom_id))
                    if rule.price_surcharge:
                        price_surcharge = convert_to_price_uom(rule.price_surcharge)
                        price += price_surcharge

                    if rule.price_min_margin:
                        price_min_margin = convert_to_price_uom(rule.price_min_margin)
                        price = max(price, price_limit + price_min_margin)

                    if rule.price_max_margin:
                        price_max_margin = convert_to_price_uom(rule.price_max_margin)
                        price = min(price, price_limit + price_max_margin)

                    rule_id = rule.id
                break

            # Final price conversion to target UoM
            price = product_uom_obj._compute_price(cr, uid, price_uom_id, price, qty_uom_id)

            results[product.id] = (price, rule_id)
        return results


# class product_product(osv.osv):
#     _inherit = 'product.product'
#
#     def write(self, cr, uid, ids, vals, context=None):
#         items = self.pool.get('product.pricelist.item').search(cr, uid, [('id', '!=', 4)])
#         for item in self.pool.get('product.pricelist.item').browse(cr, uid, items):
#             product_ids = self.pool.get('product.product').search(cr, uid, [('o2s_id', '=', item.o2s_id)])
#             if product_ids:
#                 product_id = product_ids[0]
#                 product = self.pool.get('product.product').browse(cr, uid, product_id)
#                 item.write({'product_id': product.id, 'product_tmpl_id': product.product_tmpl_id.id})
#         return super(product_product, self).write(cr, uid, ids, vals, context)
