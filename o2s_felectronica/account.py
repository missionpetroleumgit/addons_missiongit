# -*- coding: utf-8 -*-
#####
#  Sales for restaurants
#####

from openerp import models, fields, api
from openerp.exceptions import except_orm, Warning
import openerp.addons.decimal_precision as dp
import time


class account_tax_code(models.Model):
    _inherit = 'account.tax.code'
    # Para facturacion electronica
    cod_imp_fe = fields.Selection([('1', 'Renta 1'),
                                   ('2', 'IVA 2'),
                                   ('3', 'ICE 3'),
                                   ('5', 'IRBPNR 5'),
                                   ('6', 'ISD 6')], 'C Factura Electronica', help="Codigo impuesto facturacion electronica")
    cod_tarifa = fields.Selection([('0', '0%'),
                                   ('9', '10%'),
                                   ('10', '20%'),
                                   ('1', '30%'),
                                   ('2', '12%'),
                                   ('3', '14%'),
                                   ('2', '70%'),
                                   ('3', '100%'),
                                   ('6', 'No Objeto Impuestos'),
                                   ('7', 'Exento IVA'),
                                   ('4580', 'ISD 5%')], 'Codigo %', help="Codigo impuesto tarifa % facturacion electronica")
    tarifa = fields.Float('Tarifa %', size=8, help="Porcentaje de Impuesto 12%..")