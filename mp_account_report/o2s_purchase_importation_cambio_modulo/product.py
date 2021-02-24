##########################
# -*- coding: utf-8 -*- ##
##########################


from openerp import models, fields, api
from openerp.exceptions import except_orm, Warning
from openerp.osv import expression


class product_template(models.Model):
    _inherit = 'product.template'

    is_imported = fields.Boolean('es costo de importacion?')
    tariff_item_id = fields.Many2one('tariff.item', 'Partida arancelaria')
    transit_account_id = fields.Many2one('account.account', 'Cuenta de Transito')
    is_tax = fields.Boolean('es imp. aduanero?')


class tariff_item(models.Model):
    _name = 'tariff.item'

    code = fields.Char('Codigo')
    name = fields.Char('Nombre')
    apply = fields.Boolean('aplica credito?')
