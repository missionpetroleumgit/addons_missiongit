# -*- coding: utf-8 -*-
###############################
#  Productos para petroleras  #
###############################

from openerp import models, fields, api
from openerp.exceptions import except_orm, Warning


class product_template(models.Model):
    _inherit = 'product.template'

    is_lumpsum = fields.Boolean('es Lump-Sum?')
    components = fields.One2many('lumpsum.component', 'product_tmpl_id', string='Productos del Lump-Sum')
    part_number = fields.Char(streing='Part Number')


class lumpsum_component(models.Model):
    _name = 'lumpsum.component'

    product_id = fields.Many2one('product.product', 'Producto', required=True)
    uom_id = fields.Many2one('product.uom', 'UoM', required=True)
    qty = fields.Float('Cantidad', required=True)
    product_tmpl_id = fields.Many2one('product.template', 'Plantilla Producto')

    @api.onchange('product_id')
    def onchange_product_id(self):
        self.uom_id = self.product_id.uom_id.id


