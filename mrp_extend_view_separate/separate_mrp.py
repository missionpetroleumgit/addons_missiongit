# -*- coding: utf-8 -*-
from openerp import api, models, fields
import smtplib
from urlparse import urljoin
from openerp.exceptions import except_orm


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    type = fields.Selection([('service', 'Servicio'), ('mrp', 'Manofacturing'), ('assy', 'Ensamble')],
                            'Tipo')
    picking_ids = fields.One2many('stock.picking', 'internal_picking_customer_id', 'Ingreso',
                                  domain=[('picking_type_id', '=', 3)])
    sale_order_id = fields.Many2one('sale.order', 'Orden de venta')
    customer_pick_ids = fields.One2many('stock.picking', 'customer_picking_customer_id', 'Ing. Cliente',
                                        domain=[('picking_type_id', '=', 1)])

    @api.model
    def create(self, vals):
        name = '/'
        print vals
        if vals.get('type') == 'assy':
            name = self.env['ir.sequence'].next_by_code('assembly.mrp.orders')
        elif vals.get('type') == 'mrp':
            name = self.env['ir.sequence'].next_by_code('manufacturing.mrp.orders')
        elif vals.get('type') == 'service':
            name = self.env['ir.sequence'].next_by_code('manufacturing.service.mrp.orders')
        vals.update({'name': name})
        print vals.get('type')
        return super(MrpProduction, self).create(vals)


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    internal_picking_customer_id = fields.Many2one('mrp.production', 'Orden Produccion')
    customer_picking_customer_id = fields.Many2one('mrp.production', 'Manufacturing')
