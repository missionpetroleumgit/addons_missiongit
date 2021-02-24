# -*- coding: utf-8 -*-
from openerp import api, models, fields
import smtplib
from urlparse import urljoin
from openerp.exceptions import except_orm


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    @api.one
    def _get_production_orders(self):
        if isinstance(self.id, int):
            res = [self.id, ]
            mrp_production_ids = list()
            query = """ SELECT id, name FROM mrp_production mrp
                WHERE mrp.mrp_production_id in %s
                GROUP BY id """
            self._cr.execute(query, (tuple(res),))
            mrp = self._cr.fetchall()
            for mrp_id, mrp_name in mrp:
                mrp_production_ids.append(mrp_id)
            self.mrp_ids = mrp_production_ids
        else:
            pass

    @api.one
    def _get_shipping(self):
        if isinstance(self.id, int):
            res = [self.id, ]
            mrp_shipping_ids = list()
            query = """SELECT pick.id, pick.name FROM stock_picking pick, stock_move moves, mrp_production prod 
            WHERE moves.production_id=prod.id and moves.picking_id=pick.id and prod.id IN %s"""
            self._cr.execute(query, (tuple(res),))
            mrp1 = self._cr.fetchall()
            query = """SELECT pick.id, pick.name FROM stock_picking pick, stock_move moves, mrp_production prod 
                        WHERE moves.raw_material_production_id=prod.id and moves.picking_id=pick.id and prod.id IN %s"""
            self._cr.execute(query, (tuple(res),))
            mrp2 = self._cr.fetchall()
            query = """SELECT pick.id, pick.name FROM stock_picking pick, stock_move moves, mrp_production prod 
                                    WHERE moves.post_consum_raw_move_id=prod.id and moves.picking_id=pick.id and prod.id IN %s"""
            self._cr.execute(query, (tuple(res),))
            mrp3 = self._cr.fetchall()
            for ship_id, ship_name in mrp1:
                mrp_shipping_ids.append(ship_id)
            for ship_id, ship_name in mrp2:
                mrp_shipping_ids.append(ship_id)
            for ship_id, ship_name in mrp3:
                mrp_shipping_ids.append(ship_id)
            self.ship_ids = mrp_shipping_ids
        else:
            pass

    @api.multi
    def view_importations(self):
        mod_obj = self.env['ir.model.data']
        act_obj = self.env['ir.actions.act_window']
        dummy, action_id = tuple(mod_obj.get_object_reference('mrp', 'mrp_production_action'))
        action = act_obj.search_read([('id', '=', action_id)])[0]

        mrp_ids = []
        for mp in self:
            mrp_ids += [prod.id for prod in mp.mrp_ids]

        # override the context to get rid of the default filtering on picking type
        action['context'] = {}
        # choose the view_mode accordingly
        if len(mrp_ids) > 1:
            action['domain'] = "[('id','in',[" + ','.join(map(str, mrp_ids)) + "])]"
        else:
            res = mod_obj.get_object_reference('mrp', 'mrp_production_form_view')
            action['views'] = [(res and res[1] or False, 'form')]
            action['res_id'] = mrp_ids and mrp_ids[0] or False
        return action

    @api.multi
    def view_shipping(self):
        mod_obj = self.env['ir.model.data']
        act_obj = self.env['ir.actions.act_window']
        dummy, action_id = tuple(mod_obj.get_object_reference('stock', 'action_picking_tree_all'))
        action = act_obj.search_read([('id', '=', action_id)])[0]

        shipping_ids = []
        for mp in self:
            shipping_ids += [ship.id for ship in mp.ship_ids]
        # override the context to get rid of the default filtering on picking type
        action['context'] = {}
        # choose the view_mode accordingly
        if len(shipping_ids) > 1:
            action['domain'] = "[('id','in',[" + ','.join(map(str, shipping_ids)) + "])]"
        else:
            res = mod_obj.get_object_reference('stock', 'view_picking_form')
            action['views'] = [(res and res[1] or False, 'form')]
            action['res_id'] = shipping_ids and shipping_ids[0] or False
        return action

    @api.one
    def _count(self):
        self.mrp_count = len(self.mrp_ids)
        self.ship_count = len(self.ship_ids)
        if not len(self.mrp_ids):
            self.mrp_count = 0

    move_lines = fields.One2many('stock.move', 'raw_material_production_id', 'Products to Consume',
                                 domain=[('state', 'not in', ('done', 'cancel'))], states={'draft': [('readonly', False)], 'confirmed': [('readonly', False)]})
    order_line_id = fields.Many2one('sale.order.line', 'Linea de Venta')
    sale_id = fields.Many2one('sale.order', 'Venta', related='order_line_id.order_id', store=True)
    mrp_ids = fields.One2many('mrp.production', compute='_get_production_orders', string='Ordenes hijas')
    mrp_children = fields.Boolean('Orden hija', default=False)
    mrp_production_id = fields.Many2one('mrp.production', 'production_id')
    mrp_count = fields.Float('Ordenes Hijas', compute=_count)
    ship_count = fields.Float('Albaranes', compute=_count)
    ship_ids = fields.One2many('stock.picking', compute='_get_shipping', string='Albaranes')
    requisition_ids = fields.One2many('mrp.purchase.order', 'mrp_id', 'Requisiciones')
    not_bom = fields.Boolean('Sin BoM')
    stock_moves = fields.One2many('stock.move', 'post_consum_raw_move_id', 'Products to Consume',
                                 domain=[('state', '!=', 'cancel')], states={'draft': [('readonly', False)], 'confirmed': [('readonly', False)]})
    # stock_moves2 = fields.One2many('stock.move', 'post_to_consum_raw_move_id', 'Products to Consume',
    #                              domain=[('state', 'not in', ('draft', 'cancel'))], readonly=True)
    post_consum = fields.Boolean('Post-consumo', invisible=True)
    type = fields.Selection([('assy', 'Ensamble'), ('service', 'Servicio'), ('mrp', 'Manofacturacion')], 'Tipo')

    @api.multi
    def items_check(self, transit_moves):
        if self.stock_moves:
            check = 0
            all_charged = []
            print " SI entro"
            for record in transit_moves:
                for item in self.stock_moves:
                    if record.move_id.id == item.id and item.id not in all_charged:
                        all_charged.append(item.id)
            for record in transit_moves:
                if record.move_id.id in all_charged:
                    check += 1
                    print "conteo", check
                    if check == len(transit_moves):
                        return True

    @api.multi
    def create_products_post_consume(self):
        stock_move_transit = self.env['stock.move.transit'].search([('production_id', '=', self.id)])
        pos_stock_moves = []
        if stock_move_transit:
            items_check = self.items_check(stock_move_transit)
            if items_check:
                raise except_orm('Advertencia!', 'Ya se han cargado todos los items con exito. !')
        if stock_move_transit:
            for moves in stock_move_transit:
                pos_stock_moves.append(moves.move_id.id)
            self.write({'stock_moves': [(6, 0, pos_stock_moves or [])]})
        else:
            raise except_orm('Advertencia!', 'No hay nada que cargar. !')
        return True

    @api.multi
    def action_set_new_product(self):
        self.ensure_one()
        action = self.env.ref('mrp_extend.action_view_transient_move_create').read()[0]
        return action

    @api.multi
    def check_stock_post_consum(self):
        for record in self:
            for moves in record.stock_moves:
                if moves.state != 'done':
                    raise except_orm('Error', 'Aun no puede continuar con el proceso, debe cerrar primero posconsumo')
                else:
                    record.post_consum = False
        return True

    @api.multi
    def button_produce_start(self):
        self.ensure_one()
        action = self.env.ref('mrp.act_mrp_product_produce').read()[0]
        action['context'] = {'default_mode': 'consume'}
        return action

    @api.model
    def _default_warehouse(self):
        warehouse = self.env['stock.warehouse'].search([('company_id', '=', self.env.user.id)], limit=1)
        return warehouse

    def action_confirm(self, cr, uid, ids, context=None):
        """ Confirms production order.
        @return: Newly generated Shipment Id.
        """
        user_lang = self.pool.get('res.users').browse(cr, uid, [uid]).partner_id.lang
        picking_type_obj = self.pool.get('stock.picking.type')
        mrp_bom = self.pool.get('mrp.bom')
        int_type = picking_type_obj.search(cr, uid, [('code', '=', 'internal')], context=context)
        type_internal = picking_type_obj.browse(cr, uid, int_type[0], context=context) or False
        context = dict(context, lang=user_lang)
        uncompute_ids = filter(lambda x: x, [not x.product_lines and x.id or False for x in self.browse(cr, uid, ids, context=context)])
        for production in self.browse(cr, uid, ids, context=context):
            if production.not_bom:
                bom = mrp_bom.search(cr, uid, [('product_id', '=', production.product_id.id)], context=context)
                old_bom_id = mrp_bom.browse(cr, uid, bom, context=context)
                if not old_bom_id:
                    bom_id = self.pool.get('mrp.bom').create(cr, uid, {'product_id': production.product_id.id,
                                                                       'product_tmpl_id': production.product_id.product_tmpl_id.id,
                                                                       'standard_price': production.product_id.standard_price,
                                                                       'product_uom': production.product_id.uom_id.id,
                                                                       'product_qty': '1', 'type': 'normal',
                                                                       'company_id': production.company_id.id,
                                                                       'name': production.product_id.name},
                                                             context=context)
                if old_bom_id:
                    production.write({'bom_id': old_bom_id[0].id})
                else:
                    production.write({'bom_id': bom_id})
            self.action_compute(cr, uid, uncompute_ids, context=context)
            self._make_production_produce_line(cr, uid, production, context=context)

            stock_moves = []
            picking = []
            for line in production.product_lines:
                if line.product_id.type != 'service':
                    stock_move_id = self._make_production_consume_line(cr, uid, line, context=context)
                    stock_moves.append(stock_move_id)
                else:
                    self._make_service_procurement(cr, uid, line, context=context)
            if picking:
                production._send_warehouse_mail(production.id, picking)
            if stock_moves:
                # self.pool.get('stock.move').action_confirm(cr, uid, stock_moves, context=context)
                warehouse = self._default_warehouse(cr, uid, context=context)
                picking_id = self.pool.get('stock.picking').create(cr, uid, {'origin': production.name, 'picking_type_id': type_internal.id}, context=context)
                self.pool.get('stock.move').write(cr, uid, stock_moves, {'picking_id': picking_id,
                                                                         'raw_material_production_id': production.id}, context)
                self.pool.get('stock.picking').action_assign(cr, uid, [picking_id], context=context)
            production.write({'state': 'confirmed'})
        return 0

    @api.multi
    def _send_warehouse_mail(self, prod, picking):
        mrp_production = self.env['mrp.production'].search([('id', '=', prod)])
        stock_picking = self.env['stock.picking'].search([('id', '=', picking)])
        if mrp_production and stock_picking:
            remitente = "<daldaz@mission-petroleum.com>"
            destinatario = "<daldaz@mission-petroleum.com>"
            url = self._get_stock_url(stock_picking.id)
            mensaje = """
            Estimados,

            Se ha generado un albaran interno %s, desde la orden de produccion %s.

            Link del albaran interno, %s


            Saludos Cordiales,

            PRODUCCION
            MISSIONPETROLEUM S.A.
            Av. de Los Shyris N36-188 y Naciones Unidas
            Edif. Shyris Park Piso 4, Of. 401- 402 - 403 - 404
            Telf.: (593) 23949380 Ext.: 225 - 226
            www.mission-petroleum.com

                       """ % (stock_picking.name, mrp_production.name, url)
            username = 'daldaz@mission-petroleum.com'
            password = 'N4nd0MpM1ss10n2018!$!'
            email = """From: %s
                        To: %s
                        Subject: %s
                        %s
                        """ % (remitente, destinatario, stock_picking.name, mensaje)
            try:
                smtp = smtplib.SMTP('mail.mission-petroleum.com')
                smtp.starttls()
                smtp.login(username, password)
                smtp.sendmail(remitente, destinatario, email)
                smtp.quit()
            except:
                print """Error: el mensaje no pudo enviarse.
                            Compruebe que sendmail se encuentra instalado en su sistema"""

    @api.multi
    def _get_stock_url(self, pid):
        link = ''
        picking = self.env['stock.picking'].search([('id', '=', pid)])
        base_url = self.pool['ir.config_parameter'].get_param(self._cr, self._uid, 'web.base.url')
        for order in self:
            link = urljoin(
                base_url + '/web?=#id=' + str(picking.id) + '&view_type=form&model=mrp.production&action=633', '')
        return link

    def _make_production_produce_line(self, cr, uid, production, context=None):
        stock_move = self.pool.get('stock.move')
        proc_obj = self.pool.get('procurement.order')
        picking_type_obj = self.pool.get('stock.picking.type')
        source_location_id = production.product_id.property_stock_production.id
        destination_location_id = production.location_dest_id.id
        procs = proc_obj.search(cr, uid, [('production_id', '=', production.id)], context=context)
        int_type = picking_type_obj.search(cr, uid, [('code', '=', 'internal')], context=context)
        procurement = procs and \
                      proc_obj.browse(cr, uid, procs[0], context=context) or False
        type_internal = picking_type_obj.browse(cr, uid, int_type[0], context=context) or False
        warehouse = self._default_warehouse(cr, uid, context=context)
        picking_id = self.pool.get('stock.picking').create(cr, uid, {'origin': production.name, 'picking_type_id': type_internal.id}, context=context)
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
            'group_id': procurement and procurement.group_id.id,
            'picking_id': picking_id,
        }
        move_id = stock_move.create(cr, uid, data, context=context)
        self.pool.get('stock.picking').action_assign(cr, uid, [picking_id], context=context)
        #a phantom bom cannot be used in mrp order so it's ok to assume the list returned by action_confirm
        #is 1 element long, so we can take the first.
        return move_id


class MrpProductionWorkCenterLine(models.Model):
    _inherit = 'mrp.production.workcenter.line'

    service_product_id = fields.Many2one('product.product', 'Servicio asociado')


class MprPurchaseOrder(models.Model):
    _name = 'mrp.purchase.order'

    description = fields.Char('Nombre', size=32)
    mrp_id = fields.Many2one('mrp.production', 'Produccion')
    order_id = fields.Many2one('purchase.order', 'Requisiciones', domain=[('state', 'in', ('draft', 'sent', 'bid'))])
    date_req = fields.Datetime('Fecha Requisicion')

    @api.onchange('order_id')
    def date_onchange(self):
        if self.order_id:
            self.date_req = self.order_id.date_order


class StockMove(models.Model):
    _inherit = 'stock.move'

    post_consum_raw_move_id = fields.Many2one('mrp.production', 'Productos Post-consumo')
    transit_move_id = fields.Many2one('stock.move.transit', 'Movimientos temporales')

    @api.multi
    def search_check_quant(self):
        sum = 0
        if self:
            stock_quant = self.env['stock.quant'].search([('product_id', '=', self.product_id.id),
                                                          ('location_id', '=', 12),
                                                          ('qty', '>', 0)])
            for item in stock_quant:
                # if item.reservation_id:
                #     raise except_orm('Error', 'Existe una reservacion, comuniquese con bodega'
                #                               ' para quitar la reservacion y pueda sacar la cantidad'
                #                               ' deseada, producto. %s' % item.product_id.name_template)
                sum += item.qty
            if sum >= self.product_qty:
                return True
            else:
                return False

    @api.one
    def action_postconsume(self):
        if self.search_check_quant():
            raise except_orm('Error', 'No puede pasar a posconsumo un item que si tiene stock en BG.')
        for record in self:
            if record.state in ('draft', 'confirmed', 'assigned'):
                picking = False
                mrp_production = self.env['mrp.production'].search([('id', '=', record.raw_material_production_id.id)])
                type_id = self.env['stock.picking.type'].search([('code', '=', 'internal')])
                picking_obj = self.env['stock.picking']
                move_id = self.search([('post_consum_raw_move_id', '=', mrp_production.id)], limit=1)
                if move_id:
                    picking = picking_obj.search([('id', '=', move_id.picking_id.id)])
                stock_move_transit = self.env['stock.move.transit']
                new_moves = []
                if not picking:
                    vals = {
                        'origin': ' ' + record.picking_id.origin,
                        'picking_type_id': type_id.id
                    }
                    picking = self.env['stock.picking'].create(vals)
                values = {
                    'description': record.name,
                    'move_id': record.id,
                    'production_id': mrp_production.id
                }
                transit_move = stock_move_transit.create(values)
                x = record.id
                print "moves", mrp_production.move_lines
                for moves in mrp_production.move_lines:
                    new_moves.append(moves.id)
                    if moves.id == record.id and moves.state not in ('done', 'cancel'):
                        new_moves.remove(x)
                for moves in mrp_production.move_lines2:
                    new_moves.append(moves.id)
                mrp_production.update({'move_lines': [(6, 0, new_moves)]})
                mrp_production.post_consum = True
                record.update({'picking_id': picking, 'post_consum_raw_move_id': mrp_production.id})
            return True


class StockMoveTransit(models.Model):
    _name = 'stock.move.transit'

    production_id = fields.Many2one('mrp.production', 'Orden de produccion')
    description = fields.Char('Nombre', size=256)
    move_id = fields.Many2one('stock.move', 'Movimientos')


StockMoveTransit()
