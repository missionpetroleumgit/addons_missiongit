# -*- coding: utf-8 -*-
#####
#  Sales for restaurants
#####

from openerp import models, fields, api
from openerp.exceptions import except_orm, Warning
import openerp.addons.decimal_precision as dp


class mrp_bom(models.Model):
    _inherit = 'mrp.bom'

    vigencia = fields.Integer('Vigencia', help="Cantidad de días de vigencia del producto a partir de la fecha de producido.")


    _defaults = {
        'company_id': lambda self, cr, uid, c: self.pool.get('res.company')._company_default_get(cr, uid, 'mrp.bom', context=c),
    }

    def onchange_product_prod_id(self, cr, uid, ids, product_id, context=None):
        """ Changes UoM and name if product_id changes.
        @param product_id: Changed product_id
        @return:  Dictionary of changed values
        """
        res = {}
        if product_id:
            pro_pro = self.pool.get("product.product").search(cr, uid, [('id', '=', product_id)], context=context)
            prod_obj = self.pool.get('product.product').browse(cr, uid, pro_pro, context=context)
            print "OJO", prod_obj.product_tmpl_id.id
            prod = self.pool.get('product.template').browse(cr, uid, prod_obj.product_tmpl_id.id, context=context)
            res['value'] = {
                'name': '['+str(prod_obj.default_code)+']'+str(prod.name.encode('UTF-8')),
                'product_tmpl_id': prod.id,
            }
        return res

    def onchange_product_tmpl_id(self, cr, uid, ids, product_tmpl_id, product_qty=0, context=None):
        """ Changes UoM and name if product_id changes.
        @param product_id: Changed product_id
        @return:  Dictionary of changed values
        """
        res = {}
        if product_tmpl_id:
            prod = self.pool.get('product.template').browse(cr, uid, product_tmpl_id, context=context)
            res['value'] = {
                #'name': prod.name,
                'product_uom': prod.uom_id.id,
            }
        return res

class mrp_production(models.Model):
    _inherit = 'mrp.production'

    # def _get_move(self, cr, uid, ids, context={}):
    #     result = {}
    #     print "SELF", self
    #     for mrp in self.browse(cr, uid, ids, context=None):
    #         print "mrp.name", 'PROD:'+" "+mrp.name
    #         moves_ids = self.pool.get('account.move').search(cr, uid, [('name','=','PROD'+" "+mrp.name)])
    #         print "MOVES*******", moves_ids
    #         if len(moves_ids):
    #             print "entro", len(moves_ids)
    #             result[mrp.id]=moves_ids
    #     return result
    @api.multi
    def _get_move(self):
        # tratar que solo entre una vez.. cuando ya debe tener lineas de asiento state...
        if self.name and not self.moves_ids and self.state=='done':
            print "NAME PROD", self.name
            move_li = self.env['account.move.line'].search([('ref','=',str(self.name))])
            if move_li:
                array = []
                for mov in move_li:
                    array.append(mov.id)
                self.moves_ids = array

    vigencia = fields.Integer('Vigencia', help="Cantidad de días de vigencia del producto a partir de la fecha de producido.")
    observacion = fields.Text('Observaciones', help="Registrar alguna observacion propia de la produccion")
    peso_prod = fields.Float('Peso Producto', help="Ingrese el peso de producto, esto me sirve para calcular la eficiencia de la produccion")
    peso_total = fields.Float('Peso Total Producción', help="Ingrese el peso total de la producción, esto sirve para calcular la eficiencia de la produccion")
    uni_real = fields.Float('Unidades Real', help="Ingrese las unidades reales de la producción, esto sirve para calcular la eficiencia de la produccion")
    efic_produccion = fields.Char('Eficiencia Producción', help="Eficiencia de la producción finalizada")
    #moves_ids = fields.Many2one('account.move', string="Asientos asociados", compute='_get_move')
    moves_ids = fields.One2many('account.move.line', 'move_id', string="Asientos asociados", compute='_get_move')
    costo_tprod = fields.Float('Costo Total Producción', help="Aqui puede ver el costo total de la producción")
    costo_unid = fields.Float('Costo Unidad Producida', help="Aqui puede ver el costo de la unidad de la producción")

    _defaults = {
        'company_id': lambda self, cr, uid, c: self.pool.get('res.company')._company_default_get(cr, uid, 'mrp.production', context=c),
    }

    def product_id_change(self, cr, uid, ids, product_id, product_qty=0, context=None):
        """ Finds UoM of changed product.
        @param product_id: Id of changed product.
        @return: Dictionary of values.
        """
        result = {}
        vigen = 0
        ub_dest = 0
        if not product_id:
            return {'value': {
                'product_uom': False,
                'bom_id': False,
                'routing_id': False,
                'product_uos_qty': 0,
                'vigencia':0,
                'product_uos': False
            }}
        bom_obj = self.pool.get('mrp.bom')
        product = self.pool.get('product.product').browse(cr, uid, product_id, context=context)
        #CSV:14-05-2018: AUMENTO PARA CARGAR AUTOMATICAMENTE LA UBICACIÓN DEFAULT DEL PRODUCTO
        if product.property_default_location_dest.id:
            ub_dest = product.property_default_location_dest.id
        else:
            raise Warning(('Aviso'), ('Revise la configuracion de la ubicacion por defecto del producto %s' % (str(product.name))))
        bom_id = bom_obj._bom_find(cr, uid, product_id=product.id, properties=[], context=context)
        routing_id = False
        if bom_id:
            bom_point = bom_obj.browse(cr, uid, bom_id, context=context)
            routing_id = bom_point.routing_id.id or False
            vigen = bom_point.vigencia or 0
        product_uom_id = product.uom_id and product.uom_id.id or False
        result['value'] = {'product_uos_qty': 0, 'product_uos': False, 'product_uom': product_uom_id, 'bom_id': bom_id, 'routing_id': routing_id, 'vigencia':vigen, 'peso_prod':product.peso_prod, 'location_dest_id':product.property_default_location_dest.id}
        if product.uos_id.id:
            result['value']['product_uos_qty'] = product_qty * product.uos_coeff
            result['value']['product_uos'] = product.uos_id.id
        return result

    def eficiencia_change(self, cr, uid, ids, product_qty ,peso_prod, peso_total, context=None):
        """ Finds UoM of changed product.
        @param product_id: Id of changed product.
        @return: Dictionary of values.
        """
        result = {}
        efic = 0.00
        cant_real = 0.00
        if peso_total<=0:
            return {'value': {
                'efic_produccion': '%',
                'uni_real': 0.00
            }}
        else:
            cant_real = round(peso_total/peso_prod, 2)
            efic = round((cant_real*100)/product_qty, 2)
            result['value'] = {'efic_produccion': str(efic)+'%',
                               'uni_real': cant_real}

        return result

    def eficiencia_uni_change(self, cr, uid, ids, product_qty ,peso_prod, uni_real, context=None):
        """ Finds UoM of changed product.
        @param product_id: Id of changed product.
        @return: Dictionary of values.
        """
        result = {}
        efic = 0.00
        peso_real = 0.00
        if uni_real<=0:
            return {'value': {
                'efic_produccion': '%'
            }}
        else:
            peso_real = round(uni_real*peso_prod, 2)
            efic = round((uni_real*100)/product_qty, 2)
            result['value'] = {'efic_produccion': str(efic)+'%',
                               'peso_total': peso_real}

        return result


    def _make_production_produce_line(self, cr, uid, production, context=None):
        stock_move = self.pool.get('stock.move')
        proc_obj = self.pool.get('procurement.order')
        source_location_id = production.product_id.property_stock_production.id
        destination_location_id = production.location_dest_id.id
        procs = proc_obj.search(cr, uid, [('production_id', '=', production.id)], context=context)
        procurement = procs and\
            proc_obj.browse(cr, uid, procs[0], context=context) or False
        data = {
            'name': production.name,
            'date': production.date_planned,
            'product_id': production.product_id.id,
            'product_uom': production.product_uom.id,
            'product_uom_qty': production.product_qty,
            'product_uos_qty': production.product_uos and production.product_uos_qty or False,
            'product_uos': production.product_uos and production.product_uos.id or False,
            'location_id': source_location_id,
            'location_dest_id': destination_location_id,
            'move_dest_id': production.move_prod_id.id,
            'procurement_id': procurement and procurement.id,
            'company_id': production.company_id.id,
            'production_id': production.id,
            'origin': production.name,
            'days_vig': production.vigencia,
            'group_id': procurement and procurement.group_id.id,
        }
        move_id = stock_move.create(cr, uid, data, context=context)
        #a phantom bom cannot be used in mrp order so it's ok to assume the list returned by action_confirm
        #is 1 element long, so we can take the first.
        return stock_move.action_confirm(cr, uid, [move_id], context=context)[0]

#CSV:15-05-2018: AÑADO PARA QUE LOS MOVIMIENTOS DE LOS PRODUCTOS CONSUMIDOS DESCARGUE LA LA UBICACIÓN POR DEFECTO.
    def _make_consume_line_from_data(self, cr, uid, production, product, uom_id, qty, uos_id, uos_qty, context=None):
        stock_move = self.pool.get('stock.move')
        loc_obj = self.pool.get('stock.location')
        # Internal shipment is created for Stockable and Consumer Products
        if product.type not in ('product', 'consu'):
            return False
        # Take routing location as a Source Location.
        #source_location_id = production.location_src_id.id
        if product.property_default_location_dest:
            source_location_id = product.property_default_location_dest.id
        else:
            raise Warning(('Aviso'), ('Revise la configuracion de la ubicacion por defecto del producto %s' % (str(product.name))))
        prod_location_id = source_location_id
        prev_move = False
        if production.bom_id.routing_id and production.bom_id.routing_id.location_id and production.bom_id.routing_id.location_id.id != source_location_id:
            source_location_id = production.bom_id.routing_id.location_id.id
            prev_move = True

        destination_location_id = production.product_id.property_stock_production.id
        move_id = stock_move.create(cr, uid, {
            'name': production.name,
            'date': production.date_planned,
            'product_id': product.id,
            'product_uom_qty': qty,
            'product_uom': uom_id,
            'product_uos_qty': uos_id and uos_qty or False,
            'product_uos': uos_id or False,
            'location_id': source_location_id,
            'location_dest_id': destination_location_id,
            'company_id': production.company_id.id,
            'procure_method': prev_move and 'make_to_stock' or self._get_raw_material_procure_method(cr, uid, product,
                                                                                                     location_id=source_location_id,
                                                                                                     location_dest_id=destination_location_id,
                                                                                                     context=context),
        # Make_to_stock avoids creating procurement
            'raw_material_production_id': production.id,
            # this saves us a browse in create()
            'price_unit': product.standard_price,
            'origin': production.name,
            'warehouse_id': loc_obj.get_warehouse(cr, uid, production.location_src_id, context=context),
            'group_id': production.move_prod_id.group_id.id,
        }, context=context)

        if prev_move:
            prev_move = self._create_previous_move(cr, uid, move_id, product, prod_location_id, source_location_id,
                                                   context=context)
            stock_move.action_confirm(cr, uid, [prev_move], context=context)
        return move_id