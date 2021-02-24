# -*- coding: utf-8 -*-
#####
#  Product Product for restaurants
#####
from datetime import datetime, date, time, timedelta
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
import calendar
from openerp import models, fields, api
from openerp.exceptions import except_orm, Warning
import openerp.addons.decimal_precision as dp


class product_product(models.Model):
    _inherit = 'product.product'

    peso_prod = fields.Float('Peso Producto', help="Ingrese el peso de producto, esto me sirve para calcular la eficiencia de la produccion")
    is_production = fields.Boolean('Puede ser fabricado', help="Marqué esta opción si el producto puede ser fabricado")
    is_insumo = fields.Boolean('Insumo Fabricación', help="Marqué esta opción si el producto es insumo para fabricación")
    with_process = fields.Boolean('Asientos Proceso', help="Marqué esta opción si desea manejar asientos con proceso")
    account_stock_prod = fields.Many2one('account.account', 'Cuenta Stock', domain="[('type','!=','view')]", help="Escoger la cuenta de stock del local")
    account_trasi_prod = fields.Many2one('account.account', 'Cuenta Transicion', domain="[('type','!=','view')]", help="Escoger la cuenta de stock del local")
    account_final_prod = fields.Many2one('account.account', 'Cuenta Terminados', domain="[('type','!=','view')]", help="Escoger la cuenta de stock del local")

    _defaults = {
        'with_process': False,
    }