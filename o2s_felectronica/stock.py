# -*- coding: utf-8 -*-
#####
#  Facturación electrónica
#####

from openerp import models, fields, api, _
from openerp import netsvc
import tempfile
import base64
from openerp.exceptions import except_orm, Warning
import openerp.addons.decimal_precision as dp
import time

class stock_picking(models.Model):
    _inherit = 'stock.picking'

    @api.multi
    def _get_ticket(self):
        print "NAME TICK", self.name
        print "NAME TICK***********", self.ticket_id
        array = []
        tic_li = self.env['service.ticket'].search([('id','=',self.ticket_id)])
        if tic_li:
            for mov in tic_li:
                array.append(mov.id)
            self.moves_ids = array
            # Para guia remision electronica
    gremision_id = fields.One2many('stock.picking.electronica', 'gremielect_id', 'Guia Remision Electronica')
    num_autoremi = fields.Char('Autorizacion Guia', size=49)
    date_aut_remi = fields.Datetime('Fecha Autorizacion', readonly=1)
    state_remielectro = fields.Selection([('pendiente', 'Pendiente'), ('autorizado', 'Autorizado'),
                                          ('firmado', 'Firmado')], 'Estado FE')
    d_partida = fields.Char('Direccion Partida', size=100)
    date_it = fields.Date('Fecha Inicio Transporte')
    date_ft = fields.Date('Fecha Fin Transporte')
    destinatario = fields.Many2one('res.partner', 'Destinatario', domain=[('active', '=', True)], ondelete='cascade')
    transportista = fields.Many2one('res.partner', 'Transportista', domain=[('active', '=', True)], ondelete='cascade')
    motivo = fields.Char('Motivo Traslado', size=100)
    doc_adu = fields.Char('Doc Aduana Unico', size=100)
    cod_ed = fields.Char('Codigo Establecimiento Destino', size=4)
    ruta = fields.Char('Ruta', size=100)
    doc_sustento = fields.Many2one('account.invoice', 'Documento Sustento')
    prefactura = fields.Char('Documento Sustento', size=9)
    emission_series = fields.Char('Serie Emision', size=3)
    emission_point = fields.Char('Punto Emision', size=3)
    contrato = fields.Char('Contrato', size=100)
    marca = fields.Char('Marca', size=100)
    modelo = fields.Char('Modelo', size=16)
    chasis = fields.Char('Chasis', size=24)
    ntrasp = fields.Char('Nombre Transportista', size=100)
    placat = fields.Char('Placa', size=16)
    posting = fields.Char('Destino', size=128)
    applicant = fields.Char('Solicita', size=64)
    dest_identification = fields.Char('Identificacion Destinatario', size=16)
    # transportista = fields.Char('Transportista', size=64)
    identt = fields.Char('Identificacion Transportista', size=16)
    carrier_id_type = fields.Selection([('ruc', 'RUC'), ('ced', 'Cedula'), ('pass', 'Pasaporte'),
                                        ('inter', 'Internacional')], 'Tipo Identificacion')
    solicited_by = fields.Char('Solicita', size=64)
    carrier_by = fields.Char('Transportado por', size=64)
    #services_ids = fields.One2many('service.ticket', 'tik_id', string="Tickets asociados", compute='_get_ticket')
    #CSV:28-12-2017:Aumento para guardar info electronica offline
    #inf_electronica = fields.Text('Info Electronica')

    _defaults = {
        'date_aut_remi': lambda *a: time.strftime('%Y-%m-%d %H:%M:%S'),
        'state_remielectro': lambda * a: 'pendiente',
        #         'doc_sustento': _get_invoice,
    }

class stock_picking_electronica(models.Model):
    _name = 'stock.picking.electronica'
    _description = 'Guia Remision Electronica Electronica'

    name = fields.Char('Nombre', size=64, translate=True)
    clave_acceso = fields.Char('Clave Acceso', size=64, translate=True)
    clave_contingencia = fields.Char('Clave Contingencia', size=64, translate=True)
    contingencia = fields.Boolean('Contingencia', help="Indica si la clave de acceso del comprobante es de contingencia")
    cod_comprobante = fields.Char('Codigo Comprobante', size=64, translate=True)
    gremielect_id = fields.Many2one('stock.picking', 'Guia Remision Electronica')
    note = fields.Text('Historial', translate=True)

    _defaults = {
        'name': lambda * a: 'Guia Remision Electronico',
    }

