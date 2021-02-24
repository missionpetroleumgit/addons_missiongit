from openerp.osv import osv, fields
import openerp.addons.decimal_precision as dp

class product_template_wizard(osv.osv_memory):
    _name = 'product.template.wizard'
    _columns = {
        'name_template': fields.char('Name'),
        'type': fields.selection([('product', 'Stockable Product'), ('consu', 'Consumable'), ('service', 'Service')], 'Product Type', required=True),
        'attribute_value_ids': fields.many2many('product.attribute.value', id1='prod_id', id2='att_id', string='Attributes'),
        'template_id': fields.many2one('product.wizard', 'Template'),
        'lst_price': fields.float('Public Price', digits_compute=dp.get_precision('Product Price')),
        'default_code': fields.char('Referencia Interna')
    }
product_template_wizard()

class product_wizard(osv.osv_memory):
    _name = 'product.wizard'
    _columns = {
        'name': fields.char('Name'),
        'product_template_ids': fields.one2many('product.template.wizard',
                                                'template_id', 'Products')
    }

    def get_existing_variants(self, cr, uid, product_tmp_id, context=None):
        list_variants = []
        x = []
        product_pool = self.pool.get('product.product')
        product_ids = product_pool.search(cr, uid, [('product_tmpl_id', '=', product_tmp_id)])
        for product in product_pool.browse(cr, uid, product_ids):
            for value in product.attribute_value_ids:
                x.append(value.id)
                x.sort()
            vals = {
                'name_template': product.name_template,
                'attribute_value_ids': [[6, False, x]],
                'type': 'product',
                'lst_price': product.lst_price or 0.00
            }
            list_variants.append(vals)
            x = []
        return list_variants

    
    def _get_variants(self, cr, uid, context=None):
        if context is None:
            context = {}
        attribute_ids =[]
        product_tmp_id = context.get('product_tmp_id')
        res = []
        result = []
        default_code = 0
        tmpl_ids = self.pool.get('product.template').browse(cr, uid, [product_tmp_id])
        for tmpl_id in tmpl_ids:
            # list of values combination
            variant_alone = []
            all_variants = [[]]
            for variant_id in tmpl_id.attribute_line_ids:
                if len(variant_id.value_ids) == 1:
                    variant_alone.append(variant_id.value_ids[0])
                temp_variants = []
                for variant in all_variants:
                    for value_id in variant_id.value_ids:
                        temp_variants.append(sorted(variant + [int(value_id)]))
                if temp_variants:
                    all_variants = temp_variants
                    
            for list_variant in all_variants:
                default_code += 1
                vals = {
                    'name_template': tmpl_id.name,
                    'attribute_value_ids': [[6, False, list_variant]],
                    'type':'product',
                    'lst_price': tmpl_id.lst_price or 0.00
                }
                res.append(vals)
        existing_variants = self.get_existing_variants(cr, uid, product_tmp_id, context=None)
        for element in res:
            if element in existing_variants:
                pass
            else:
                result.append(element)

        return result

    _defaults = {
        'product_template_ids': _get_variants,         
    }
    
    def create_var(self, cr, uid, ids, context=None):
        product_tmp_id = context.get('product_tmp_id')
        product_product_template = self.pool.get('product.template').read(cr, uid, [product_tmp_id], ['default_code', 'name'])
        if product_product_template:
            product_product_template = product_product_template[0]
        product_product = self.pool.get('product.product')
        wizard_obl = self.browse(cr, uid, ids[0], context=None)
        for product_template in wizard_obl.product_template_ids:
            list_values_ids = []
            for record in product_template.attribute_value_ids:
                list_values_ids.append(record.id)
            vals = {
                    'attribute_value_ids': [(6, False, list_values_ids)],
                    'active': True,
                    'product_tmpl_id':product_tmp_id,
                    'default_code': product_template.default_code,
                    'type':'product',
                    'name_template': product_product_template['name']
                    }
            product_product.create(cr, uid, vals, context=None)
        return True
    
product_wizard()
