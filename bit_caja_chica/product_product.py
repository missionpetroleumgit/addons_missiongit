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

    is_pcchica = fields.Boolean('Producto caja chica', help="Marqué esta opción si el producto puede ser utilizado en caja chica")