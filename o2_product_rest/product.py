# -*- coding: utf-8 -*-
############################
#  Product for restaurants #
############################

from openerp import models, fields, api
from openerp.exceptions import except_orm, Warning
import openerp.addons.decimal_precision as dp


class product_product(models.Model):
    _inherit = 'product.product'

    property_default_location_dest = fields.Many2one('stock.location', 'Ubicacion destino por defecto')
    # o2_id = fields.Integer('Internal Id for Open 2S')

    @api.v7
    def _check_o2_id(self, cr, uid, ids, context=None):
        # rec = self.browse(cr, uid, ids[0])
        # product = self.search(cr, uid, [('o2_id', '=', rec.o2_id),
        #                                 ('company_id', '=', rec.company_id.id)])
        # if product:
        #     return False
        return False

    @api.v7
    def _check_default_code(self, cr, uid, ids, context=None):
        rec = self.browse(cr, uid, ids[0])
        product = self.search(cr, uid, [('default_code', '=', rec.default_code),
                                        ('company_id', '=', rec.company_id.id), ('id', '!=', ids[0])])
        if product:
            return False
        return True

    # _sql_constraints = [
    #     ('o2s_id_uniq', 'unique(company_id, o2_id)', 'Ya existe un producto con el código interno insertado para la compañía seleccionada!'),
    # ]

    _constraints = [
        # (_check_o2_id, 'Ya existe un producto con el código interno insertado para la compañía seleccionada', ['o2_id']),
        (_check_default_code, 'Ya existe un producto con esa referencia interna para la compañia', ['default_code'])
    ]

product_product()


class product_supplierinfo(models.Model):
    _inherit = 'product.supplierinfo'

    supplier_taxes_id = fields.Many2many('account.tax', 'account_tax_supplier_rel', 'supp_id', 'tax_id', 'Impuestos de Proveedor')

    @api.model
    def default_get(self, fields_list):
        res = super(product_supplierinfo, self).default_get(fields_list)
        if 'company_id' in self._context:
            res.update({'company_id': self._context['company_id']})
        return res
