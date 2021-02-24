# -*- coding: utf-8 -*-
#####
#  Facturacion Electronica
#####
from passlib.handlers.misc import plaintext

from openerp import models, fields, api
from openerp.exceptions import except_orm, Warning
import openerp.addons.decimal_precision as dp
import time


class res_partner(models.Model):
    _inherit = 'res.partner'

    @api.one
    def _cod_type(self):
        cod = ''
        if self.part_type=='c':
            cod = '05'
        elif self.part_type=='r':
            cod = '04'
        elif self.part_type=='s':
            cod = '07'
        elif self.part_type=='p':
            cod = '06'
        elif self.part_type=='pla':
            cod = '09'
        else:
            raise Warning(('Aviso'), ('Tipo de Identificacion desconocida'))
        self.cod_type_ident = cod

    cod_type_ident = fields.Char('Cod. Tipo Identificacion', compute=_cod_type, size=20, help='Codigo de Identificacion')
    cod_posfis = fields.Char('Cod. Posicion Fiscal', size=20, help='Codigo Posicion Fiscal')
    obli_contab = fields.Selection([('SI','SI'),('NO','NO')], "Obligado a llevar contabilidad")
    ident1 = fields.Char('Identificacion1', size=20, help='Codigo de Identificacion')
    ident2 = fields.Char('Identificacion2', size=20, help='Codigo de Identificacion')
    sucursal1 = fields.Char('Sucursal1', size=128)
    sucursal2 = fields.Char('Sucursal2', size=128)
    unid_t = fields.Selection([('dias','Dias'),('semanas','Semanas'),('meses','Meses'),('anios','Años')], "Unidad Tiempo")
    plazo = fields.Float('Plazo', size=8, help="Plazo de pago cliente emision electronica..")
    f_pago = fields.Selection([('01', 'SIN UTILIZACION DEL SISTEMA FINANCIERO'),
                                        ('19', 'TARJETA DE CRÉDITO'),
                                        ('20', 'OTROS CON UTILIZACION DEL SISTEMA FINANCIERO')], 'Formas de Pago', help="Seleccionar la forma de pago para emision electronica")
    _defaults = {
        'f_pago': lambda * a: '20',
        'plazo': lambda * a: 30.00,
        'unid_t': lambda * a: 'dias',
        'obli_contab': lambda * a: 'NO',
        'cod_posfis': lambda * a: '000',
    }
    _sql_constraints = [
        ('partner_uniq', 'unique (ident_num,ref)', 'Ya existe otro cliente/proveedor igual!')
    ]

    # f_pago = fields.Selection([('01', 'SIN UTILIZACION DEL SISTEMA FINANCIERO'),
    #                                     ('02', 'CHEQUE PROPIO'),
    #                                     ('03', 'CHEQUE CERTIFICADO'),
    #                                     ('04', 'CHEQUE DE GERENCIA'),
    #                                     ('05', 'CHEQUE DEL EXTERIOR'),
    #                                     ('06', 'DÉBITO DE CUENTA'),
    #                                     ('07', 'TRANSFERENCIA PROPIO BANCO'),
    #                                     ('08', 'TRANSFERENCIA OTRO BANCO NACIONAL'),
    #                                     ('09', 'TRANSFERENCIA BANCO EXTERIOR'),
    #                                     ('10', 'TARJETA DE CRÉDITO NACIONAL'),
    #                                     ('11', 'TARJETA DE CRÉDITO INTERNACIONAL'),
    #                                     ('12', 'GIRO'),
    #                                     ('13', 'DEPOSITO EN CUENTA(CORRIENTE/AHORROS)'),
    #                                     ('14', 'ENDOSO DE INVERSIÓN'),
    #                                     ('15', 'COMPENSACIÓN DE DEUDAS'),
    #                                     ('16', 'TARJETA DE DÉBITO'),
    #                                     ('17', 'DINERO ELECTRÓNICO'),
    #                                     ('18', 'TARJETA PREPAGO'),
    #                                     ('19', 'TARJETA DE CRÉDITO'),
    #                                     ('20', 'OTROS CON UTILIZACION DEL SISTEMA FINANCIERO'),
    #                                     ('21', 'ENDOSO DE TÍTULOS')], 'Formas de Pago', help="Seleccionar la forma de pago para emision electronica")