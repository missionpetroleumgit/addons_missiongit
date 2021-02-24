##########################
# -*- coding: utf-8 -*- ##
##########################


from openerp import models, fields, api
from openerp.exceptions import except_orm, Warning
import openerp.addons.decimal_precision as dp
from openerp.tools.float_utils import float_compare
from datetime import datetime
import time

################################################
# Importacion de varias ordenes de importacion #
################################################
################################################
################################################
################################################
################################################


class purchase_importation(models.Model):
    _name = 'purchase.importation'

    STATE_SELECTION = [
        ('draft', 'Borrador'),
        ('confirmed', 'Inicial'),
        ('transit', 'Transito'),
        ('done', 'Done'),
        ('cancel', 'Cancelled')
    ]

    @api.one
    def _amount_total(self):
        total = 0.00
        for line in self.order_lines:
            total += line.subtotal_importation
        self.amount_total = total

    @api.one
    def _count_all(self):
        self.invoice_count = len(self.invoice_ids)
        self.shipment_count = len(self.picking_ids)

    @api.model
    def _default_company(self):
        return self.env.user.company_id.id

    @api.model
    def _get_journal(self):
        company_id = self.env.user.company_id.id
        journal_obj = self.env['account.journal']
        res = journal_obj.search([('code', '=', 'DIMP'), ('company_id', '=', company_id)], limit=1)
        return res and res[0] or False

    @api.model
    def _get_default_currency(self):
        return self.env.user.company_id.currency_id.id

    @api.model
    def _get_picking_in(self):
        obj_data = self.env['ir.model.data']
        type_obj = self.env['stock.picking.type']
        company_id = self.env.user.company_id.id
        types = type_obj.search([('code', '=', 'incoming'), ('warehouse_id.company_id', '=', company_id)])
        if not types:
            types = type_obj.search([('code', '=', 'incoming'), ('warehouse_id', '=', False)])
            if not types:
                raise except_orm('Error!', "Make sure you have at least an incoming picking type defined")
        return types.id

    @api.one
    def _get_picking_ids(self):
        if isinstance(self.id, int):
            res = [self.id, ]
            picking_ids = list()
            query = """
            SELECT picking_id, pi.id FROM stock_picking p, stock_move m, importation_order_line iol, purchase_importation pi
                WHERE pi.id in %s and pi.id = iol.importation_id and iol.id = m.importation_line_id and m.picking_id = p.id
                GROUP BY picking_id, pi.id

            """
            self._cr.execute(query, (tuple(res), ))
            picks = self._cr.fetchall()
            for pick_id, po_id in picks:
                picking_ids.append(pick_id)
            self.picking_ids = picking_ids
        else:
            pass

    @api.one
    def _importation_amount(self):
        amount = 0.00
        for expense in self.expenses_ids:
            amount += expense.amount
        self.amount_importation = amount

    @api.model
    def _get_default_location(self):
        picktype_id = self._get_picking_in()
        picktype = self.env['stock.picking.type']
        picktype_obj = picktype.browse(picktype_id)
        return picktype_obj.default_location_dest_id.id

    name = fields.Char('Referencia')
    date_order = fields.Date('Inicio Importacion')
    partner_id = fields.Many2one('res.partner', 'Proveedor', domain=[('supplier', '=', True)])
    picking_type_id = fields.Many2one('stock.picking.type', 'Entregar a', default=_get_picking_in)
    company_id = fields.Many2one('res.company', 'Company', default=_default_company)
    order_lines = fields.One2many('importation.order.line', 'importation_id', 'Lineas de Importacion')
    # request_ids = fields.One2many('request.product', 'importation_id','Productos solicitados', ondelete='cascade')
    # quotes = fields.One2many('purchase.quotes', 'importation_id', 'Cotizaciones', ondelete='cascade')
    state = fields.Selection(STATE_SELECTION, 'Estado', default='draft')
    expenses_ids = fields.One2many('importation.expenses', 'importation_id', 'Costos de Importacion', ondelete='cascade')
    amount_ct = fields.Float('Credito Tributario')
    amount_total = fields.Float('Total', compute=_amount_total)
    amount_nct = fields.Float('Monto no aplica CT')
    invoice_ids = fields.Many2many('account.invoice', 'purchase_importation_invoice_rel', 'importation_id',
                                   'invoice_id', 'Facturas', copy=False, help="Facturadas generadas desde la importacion")
    location_id = fields.Many2one('stock.location', 'Ubicacion', default=_get_default_location)
    invoice_count = fields.Float('Invoices', compute=_count_all)
    comment = fields.Text('Info. Adicional')
    currency_id = fields.Many2one('res.currency', 'Currency', required=True, default=_get_default_currency)
    shipment_count = fields.Float('Shipments', compute=_count_all)
    picking_ids = fields.One2many('stock.picking', compute=_get_picking_ids, string='Picking List')
    amount_importation = fields.Float('Costo de Importacion', compute=_importation_amount)
    journal_id = fields.Many2one('account.journal', 'Diario de Importaciones', default=_get_journal)
    origin = fields.Char('Origen')
    is_importation = fields.Boolean('Is importation')
    att_ids = fields.Many2many(comodel_name='ir.attachment', relation='attachment_impor_rel', column1='importation_id',
                                      column2='attachment_id', string='Archivo Adjunto(s)')

    _defaults = {
        is_importation: True
    }

    # @api.multi
    # def write(self, vals):
    #     return super(purchase_importation, self).write(vals)

    @api.onchange('picking_type_id')
    def onchange_picking_type_id(self):
        self.location_id = self.picking_type_id.default_location_dest_id.id

    @api.model
    def create(self, vals):
        obj = super(purchase_importation, self).create(vals)
        if not obj.journal_id:
            raise except_orm('Error!', 'No existe un diario de importaciones definido, el mismo debe tener como codigo: DIMP')
        return obj

    @api.multi
    def imp_start(self):
        for rec in self:
            rec.state = 'confirmed'

    @api.multi
    def imp_cancel(self):
        for rec in self:
            for invoice in rec.invoice_ids:
                if invoice.state not in ('draft', 'open'):
                    raise except_orm('Error!', 'No puede cancelar una importacion con facturas pagadas: Factura %s' % invoice.number)
                invoice.action_cancel()
            for pick in rec.picking_ids:
                if pick.state == 'done':
                    raise except_orm('Error!', 'No puede cancelar una importacion con productos recibidos: Recepcion %s' % pick.name)
                pick.action_cancel()
            rec.state = 'cancel'

    @api.multi
    def imp_set_transit(self):
        for rec in self:
            for line in rec.order_lines:
                line.subtotal_importation = line.price_unit * line.product_qty
            rec.amount_ct = 0.00
            rec.amount_nct = 0.00
            rec.state = 'transit'
            move = self.env['account.move'].search([('ref', '=', rec.name)])
            if move:
                move.button_cancel()
                move.unlink()

    @api.multi
    def invoice_open(self):
        mod_obj = self.env['ir.model.data']
        act_obj = self.env['ir.actions.act_window']

        result = mod_obj.get_object_reference('account', 'action_invoice_tree2')
        id = result and result[1] or False
        result = act_obj.search_read([('id', '=', id)])[0]
        inv_ids = []
        for po in self:
            inv_ids += [invoice.id for invoice in po.invoice_ids]
        if not inv_ids:
            raise except_orm('Error!', 'Please create Invoices.')
         #choose the view_mode accordingly
        if len(inv_ids) > 1:
            result['domain'] = "[('id','in',["+','.join(map(str, inv_ids))+"])]"
        else:
            res = mod_obj.get_object_reference('account', 'invoice_supplier_form')
            result['views'] = [(res and res[1] or False, 'form')]
            result['res_id'] = inv_ids and inv_ids[0] or False
        return result

    @api.multi
    def view_picking(self):
        mod_obj = self.env['ir.model.data']
        act_obj = self.env['ir.actions.act_window']
        dummy, action_id = tuple(mod_obj.get_object_reference('stock', 'action_picking_tree'))
        action = act_obj.search_read([('id', '=', action_id)])[0]

        pick_ids = []
        for po in self:
            pick_ids += [picking.id for picking in po.picking_ids]

        #override the context to get rid of the default filtering on picking type
        action['context'] = {}
        #choose the view_mode accordingly
        if len(pick_ids) > 1:
            action['domain'] = "[('id','in',[" + ','.join(map(str, pick_ids)) + "])]"
        else:
            res = mod_obj.get_object_reference('stock', 'view_picking_form')
            action['views'] = [(res and res[1] or False, 'form')]
            action['res_id'] = pick_ids and pick_ids[0] or False
        return action

    @api.multi
    def action_prorated(self):
        for rec in self:
            if self.env.user.company_id.percent == 0.00:
                raise except_orm('Error!', 'Configure el porcentaje del ISD en la compania')
            amount_product = 0.00
            amount_inv = 0.00
            amount_service = 0.00
            items_service = list()
            amount_expense = 0.00
            amount_ise = 0.00
            for line in rec.order_lines:
                if line.product_id.type != 'service':
                    amount_product += line.subtotal_importation
                else:
                    amount_service += line.subtotal_importation
                    items_service.append(line)
            for expense in rec.expenses_ids:
                amount_expense += expense.amount
            move = rec.lq_account_move_create()
            move_line = self.env['account.move.line']
            dict_lines = dict()
            amount_ise = rec.amount_total * self.env.user.company_id.percent
	    nofiles = 0
            for line in rec.order_lines:
                item_cimport = 0.00
                subtotal = line.subtotal_importation
                if line.product_id.type != 'service':
                    # move_ft = self.env['stock.move'].search([('picking_id', 'in', (rec.picking_ids.id, )),
                    #                                         ('product_id', '=', line.product_id.id)])
                    factor = line.subtotal_importation/amount_product
                    line.subtotal_importation += amount_expense*factor
                    pack = self.env['stock.pack.operation'].search(
                        [('picking_id', 'in', rec.picking_ids.ids), ('product_id', '=', line.product_id.id)])
                    lots_to_write = self.env['stock.production.lot']
                    for p in pack:
                        if p.lot_id:
                            lots_to_write += p.lot_id
                            nofiles += 1
                    lots_to_write.write({'amount_cost': line.price_unit,
                                         'importation_amount': round(((line.subtotal_importation - (
                                             line.price_unit * line.product_qty)) / line.product_qty), 2)})

                    # for stm in move_ft:
                    #    item = self.env['stock.production.lot'].search([('id', '=', stm.serial_item_id.id)])
                    #    #item = self.env['serial.item'].search([('id', '=', stm.serial_item_id.id)])
                    #    if item:
                    #        item.write({'amount_cost': line.price_unit,
                    #                    'importation_amount': round(((line.subtotal_importation
                    # - (line.price_unit * line.product_qty))/ line.product_qty),2)})
                    #        nofiles += 1
                    if not line.product_id.tariff_item_id:
                        raise except_orm('Error!', 'El producto %s no tiene configurado la Partida Arancelaria' % line.product_id.name)
                    if line.product_id.tariff_item_id.apply:
                        rec.amount_ct += amount_ise*factor
                        item_cimport = amount_ise*factor
                        if move.journal_id.isd_cc_account_id.id not in dict_lines:
                            dict_lines[move.journal_id.isd_cc_account_id.id] = {'debit': amount_ise*factor, 'credit': 0.00}
                        else:
                            dict_lines[move.journal_id.isd_cc_account_id.id]['debit'] += amount_ise*factor
                    else:
                        line.subtotal_importation += amount_ise*factor
                        rec.amount_nct += amount_ise*factor
                        if not line.product_id.property_stock_account_output:
                            pass
                        else:
                            if line.product_id.property_stock_account_output.id not in dict_lines:
                                dict_lines[line.product_id.property_stock_account_output.id] = {'debit': amount_ise*factor, 'credit': 0.00}
                            else:
                                dict_lines[line.product_id.property_stock_account_output.id]['debit'] += amount_ise*factor

                    for serial_item in line.product_id.serial_items:
			for picking_ids in rec.picking_ids:
                            if serial_item.origin == picking_ids.name: #rec.name:
                                serial_item.amount_cost = line.price_unit #subtotal_importation/line.product_qty
                                serial_item.importation_amount = round((( line.subtotal_importation - (line.price_unit * line.product_qty))/ line.product_qty),2) # item_cimport/line.product_qty

                    if line.product_id.cost_method == 'average':
                        line.product_id.standard_price = (line.product_id.standard_price + (line.subtotal_importation/line.product_qty))/2

                    if not line.product_id.property_stock_account_output:
                        if line.product_id.property_stock_account_input.id not in dict_lines:
                            dict_lines[line.product_id.property_stock_account_input.id] = {'debit': line.subtotal_importation, 'credit': 0.00}
                        else:
                            dict_lines[line.product_id.property_stock_account_input.id]['debit'] += line.subtotal_importation
                    else:
                        if line.product_id.property_stock_account_output.id not in dict_lines:
                            dict_lines[line.product_id.property_stock_account_output.id] = {'debit': amount_expense*factor, 'credit': 0.00}
                        else:
                            dict_lines[line.product_id.property_stock_account_output.id]['debit'] += (amount_expense*factor)
                        if line.product_id.property_stock_account_input.id not in dict_lines:
                            dict_lines[line.product_id.property_stock_account_input.id] = {'debit': line.product_qty * line.price_unit, 'credit': 0.00}
                        else:
                            dict_lines[line.product_id.property_stock_account_input.id]['debit'] += line.product_qty * line.price_unit
                    if not line.product_id.transit_account_id:
                        raise except_orm('Error!', 'Configure la cuenta de transito para el producto %s' % line.product_id.name)
                    if line.product_id.transit_account_id.id not in dict_lines:
                        dict_lines[line.product_id.transit_account_id.id] = {'debit': 0.00, 'credit': subtotal}
                    else:
                        dict_lines[line.product_id.transit_account_id.id]['credit'] += subtotal

            if not items_service:
                dict_lines[move.journal_id.cost_account_id.id] = {'debit': 0.00, 'credit': rec.amount_importation}
            else:
                dict_lines[move.journal_id.cost_account_id.id] = {'debit': 0.00, 'credit': rec.amount_importation - amount_service}
                for item in items_service:
                    if not item.product_id.property_account_expense:
                        raise except_orm('Error!', 'Configure la cuenta de gasto del servicio %s' % item.product_id.name)
                    if item.product_id.property_account_expense.id not in dict_lines:
                        dict_lines[item.product_id.property_account_expense.id] = {'debit': 0.00, 'credit': item.subtotal_importation}
                    else:
                        dict_lines[item.product_id.property_account_expense.id]['credit'] += item.subtotal_importation
            dict_lines[move.journal_id.isd_cp_account_id.id] = {'debit': 0.00, 'credit': amount_ise}
            for key, val in dict_lines.items():
                move_line.create({
                    'name': move.ref,
                    'quantity': 0,
                    'date': datetime.today().strftime('%Y-%m-%d'), #move.date,
                    'debit': val['debit'],
                    'credit': val['credit'],
                    'account_id': key,
                    'move_id': move.id,
                    'partner_id': rec.partner_id.id if val['debit'] > 0 else False})
            rec.state = 'done'

    # Cron actualiza los costos de productos
    @api.multi
    def cron_action_prorated(self):
        purchase_importation = self.env['purchase.importation'].search([('state', '=', 'done')])
        nofiles = 0
        for rec in purchase_importation:
            for line in rec.order_lines:
                if line.product_id.type != 'service':
                    pack = self.env['stock.pack.operation'].search([('picking_id','=',rec.picking_ids.id),('product_id', '=', line.product_id.id)])
                    if pack.lot_id:
                        pack.lot_id.write({'amount_cost': line.price_unit,
                                           'importation_amount': round(((line.subtotal_importation - (line.price_unit * line.product_qty))/ line.product_qty),2)})
                        nofiles += 1
        print 'Numero de series afectdas ', nofiles

    def lq_account_move_create(self):
        move = self.env['account.move']
        period = self.env['account.period']
        period_obj = period.search([('date_start', '<=', datetime.today().strftime('%Y-%m-%d')), ('date_stop', '>=', datetime.today().strftime('%Y-%m-%d'))], limit=1)
        if not period_obj:
            raise except_orm('Error!', 'No existe un periodo contable definido para la fecha de la importacion')
        move_obj = move.create({'ref': self.name, 'journal_id': self.journal_id.id, 'date': datetime.today().strftime('%Y-%m-%d'), 'period_id': period_obj.id})
        return move_obj

    @api.multi
    def action_invoice(self):
        invoice = self.env['account.invoice']
        invoice_line = self.env['account.invoice.line']
        for rec in self:
            if not rec.partner_id.property_account_payable:
                raise except_orm('Error!', 'Configure las cuentas en el proveedor %s' % rec.partner_id.name)
            inv = invoice.create({'partner_id': rec.partner_id.id, 'account_id': rec.partner_id.property_account_payable.id,
                                  'document_type': rec.partner_id.document_type.id, 'tax_support': rec.partner_id.tax_support.id,
                                  'type': 'in_invoice', 'origin': rec.origin})
            for line in rec.order_lines:
                res = line._prepare_inv_line(inv)
                invoice_line.create(res)

            rec.write({'invoice_ids': [(4, inv.id)]})

    # def _get_approbe_qty(self, quotes):
    #     app_cont = 0
    #     for quote in quotes:
    #         if quote.state == 'done':
    #             app_cont += 1
    #     return app_cont

    # def create_lines(self, importation_id, line):
    #     taxes = list()
    #     taxes.append([6, False, [tax.id for tax in line.taxes_id]])
    #     self.env['importation.order.line'].create({'importation_id': importation_id, 'name': line.name,
    #                                                'product_qty': line.product_qty, 'date_planned': line.date_planned,
    #                                                'product_id': line.product_id.id, 'taxes_id': taxes, 'product_uom': line.product_uom.id,
    #                                                'price_unit': line.price_unit, 'subtotal_importation': line.price_unit*line.product_qty})
    #
    # def create_simple_order(self, quotes):
    #     for quot in quotes:
    #         if quot.state in ('draft', 'cancel'):
    #             continue
    #
    #         for line in quot.quotes_lines:
    #             if line.state in ('draft', 'cancel'):
    #                 continue
    #             if line.price_subtotal < 0.00:
    #                 raise except_orm('Error!', 'Una linea de la cotizacion %s esta aprobada y su valor es menor o igual a 0.00' % quot.name)
    #             self.create_lines(quot.importation_id.id, line)
    #
    #         return quot
    #
    # def create_multi_order(self, quote, quotes):
    #     for q in quotes:
    #         if q.id != quote.id:
    #             pick_type = self.env['stock.picking.type'].search([('code', '=', 'incoming')])
    #             if not pick_type:
    #                 raise except_orm('Error!', 'No hay definido un tipo de operacion de entrada')
    #             importation = self.create({'partner_id': q.partner_id.id, 'date_order': q.date_request, 'picking_type_id': pick_type.id,
    #                                        'location_id': pick_type.default_location_dest_id.id, 'user_id': quote.importation_id.user_id.id})
    #
    #             q.write({'importation_id': importation.id})
    #             importation.manager_approved()
    #             #Falta transitar por los estados
    #     return True

    # @api.multi
    # def imp_manager(self):
    #     for rec in self:
    #         rec.state = 'execute'

    def _prepare_order_line_move(self, order, order_line, picking_id, group_id):
        product_uom = self.env['product.uom']
        price_unit = order_line.price_unit
        if order_line.product_uom.id != order_line.product_id.uom_id.id:
            price_unit *= order_line.product_uom.factor / order_line.product_id.uom_id.factor
        if order.currency_id.id != order.company_id.currency_id.id:
            #we don't round the price_unit, as we may want to store the standard price with more digits than allowed by the currency
            price_unit = order.currency_id.compute(price_unit, order.company_id.currency_id.id, round=False)
        res = []
        move_template = {
            'name': order_line.name or '',
            'product_id': order_line.product_id.id,
            'product_uom': order_line.product_uom.id,
            'product_uos': order_line.product_uom.id,
            'date': order.date_order,
            'date_expected': order_line.date_planned,
            'location_id': order.partner_id.property_stock_supplier.id,
            'location_dest_id': order.location_id.id,
            'picking_id': picking_id,
            'partner_id': order.partner_id.id,
            'move_dest_id': False,
            'state': 'draft',
            'importation_line_id': order_line.id,
            'company_id': order.company_id.id,
            'price_unit': price_unit,
            'picking_type_id': order.picking_type_id.id,
            'group_id': group_id,
            'procurement_id': False,
            'origin': order.name,
            'route_ids': order.picking_type_id.warehouse_id and [(6, 0, [x.id for x in order.picking_type_id.warehouse_id.route_ids])] or [],
            'warehouse_id':order.picking_type_id.warehouse_id.id,
            'invoice_state': 'none',
        }

        diff_quantity = order_line.product_qty
        #if the order line has a bigger quantity than the procurement it was for (manually changed or minimal quantity), then
        #split the future stock move in two because the route followed may be different.
        if float_compare(diff_quantity, 0.0, precision_rounding=order_line.product_uom.rounding) > 0:
            move_template['product_uom_qty'] = diff_quantity
            move_template['product_uos_qty'] = diff_quantity
            res.append(move_template)
        return res

    def _create_stock_moves(self, order, order_lines, picking=False, context=None):
        stock_move = self.env['stock.move']
        todo_moves = []
        # new_group = self.env["procurement.group"].create({'name': order.name, 'partner_id': order.partner_id.id})

        for order_line in order_lines:
            if not order_line.product_id:
                continue

            if order_line.product_id.type in ('product', 'consu'):
                for vals in self._prepare_order_line_move(order, order_line, picking, False):
                    move = stock_move.create(vals)
                    move.action_confirm()
                    move.force_assign()

    @api.multi
    def action_picking_create(self):
        for order in self:
            picking_vals = {
                'picking_type_id': order.picking_type_id.id,
                'partner_id': order.partner_id.id,
                'date': order.date_order,
                'origin': order.name,
            }
            picking = self.env['stock.picking'].create(picking_vals)
            order._create_stock_moves(order, order.order_lines, picking.id)
            picking_ids = [p.id for p in order.picking_ids]
            picking_ids.append(picking.id)
            order.picking_ids = [[6, False, picking_ids]]
            order.write({'picking_ids': [(4, picking.id)]})
        return picking

    @api.multi
    def purchase_confirm(self):
        #  CSV: 15-09-2017 AUMENTO PARA CONTROLAR LA GENERACION DE LA FACTURA SI YA SE GENERO DESDE LA ORDEN
        invoice = self.env['account.invoice']

        days = 0
        orig = self.origin.split(',')
        for record in self:
            val = {
                'tracing_id': [(0, 0, {
                    'purchase_order_id': record.id,
                    'user_id': record.env.user.id,
                    'date_tracing': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'state': 'approved_gert'
                })]
            }
            record.write(val)
            if not record.order_lines:
                raise except_orm('Error!', 'La orden no tiene lineas de compras, posiblemente debido a que no se ha aprobado ninguna de las cotizaciones')
            for line in record.order_lines:
                line.origin.imported = True
            #  CSV: 15-09-2017 AUMENTO PARA CONTROLAR LA GENERACION DE LA FACTURA SI YA SE GENERO DESDE LA ORDEN
            for imp in self.env['purchase.importation'].browse(self.ids):
                orig = imp.origin.split(',')
                num_fact = 0
                for odim in orig:
                    inv_exist = invoice.search([('origin', '=', odim.strip())])
                    if len(inv_exist)>0:
                        record.write({'invoice_ids': [(4, inv_exist.id)]})
                        num_fact += 1
            if num_fact == 0:
                record.action_invoice()
            #  *************************************************************************************************
            record.state = 'transit'
            record.name = self.env['ir.sequence'].get('purchase.importation', context=self._context)
            record.action_picking_create()
    #
    # @api.multi
    # def send_mymail(self):
    #     mtp = self.env['email.template']
    #     mail = self.env['mail.mail']
    #     for record in self:
    #         tmp = mtp.search([('model_id.model', '=', self._name), ('name', '=', 'Importation Order - Send by Email')])
    #         mail_id = tmp.send_mail(record.id)
    #         mail_obj = mail.browse(mail_id)
    #         mail_obj.send()
    #     return True


class importation_order_line(models.Model):
    _name = 'importation.order.line'

    importation_id = fields.Many2one('purchase.importation', 'Importacion')
    subtotal_importation = fields.Float('Subtotal')
    name = fields.Text('Description', required=True)
    product_qty = fields.Float('Quantity', digits_compute=dp.get_precision('Product Unit of Measure'), required=True)
    date_planned = fields.Date('Scheduled Date', required=True, select=True)
    taxes_id = fields.Many2many('account.tax', 'importation_order_taxe', 'imp_id', 'tax_id', 'Taxes')
    product_uom = fields.Many2one('product.uom', 'Product Unit of Measure', required=True)
    product_id = fields.Many2one('product.product', 'Product', domain=[('purchase_ok','=',True)], change_default=True)
    move_ids = fields.One2many('stock.move', 'purchase_line_id', 'Reservation', readonly=True, ondelete='set null')
    price_unit = fields.Float('Unit Price', required=True, digits_compute= dp.get_precision('Product Price'))
    account_analytic_id = fields.Many2one('account.analytic.account', 'Analytic Account',)
    company_id = fields.Many2one('res.company',string='Company', related='importation_id.company_id', store=True, readonly=True)
    number = fields.Char('No. parte')
    origin = fields.Many2one('importation.line', 'Origen')
    order = fields.Char('Orden', related='origin.importation_id.name')

    def _prepare_inv_line(self, inv):

        description = self.product_id.description if self.product_id.description else self.product_id.name
        if not self.product_id.property_stock_account_input:
            raise except_orm('Error!', 'Configure las cuentas en el producto %s' % self.product_id.name.encode('utf-8'))
        return {'product_id': self.product_id.id, 'name': description, 'account_id': self.product_id.property_stock_account_input.id, 'quantity': self.product_qty,
                'uos_id': self.product_uom.id, 'price_unit': self.price_unit, 'invoice_id': inv.id}


class request_product(models.Model):
    _inherit = 'request.product'

    importation_id = fields.Many2one('importation.order', 'Orden de Importacion')


class purchase_quotes(models.Model):
    _inherit = 'purchase.quotes'

    importation_id = fields.Many2one('importation.order', 'Importacion')


class importation_expenses(models.Model):
    _name = 'importation.expenses'

    partner_id = fields.Many2one('res.partner', 'Proveedor', domain=[('supplier', '=', True)])
    product_id = fields.Many2one('product.product', 'Producto', domain=[('is_imported', '=', True)])
    amount = fields.Float('Valor')
    invoiced = fields.Boolean('Facturado')
    importation_id = fields.Many2one('purchase.importation', 'Importacion')
    company_id = fields.Many2one('res.company', string='Compania', related='importation_id.company_id')

    @api.one
    def action_invoice(self):
        if not self.product_id.is_tax:
            invoice = self.env['account.invoice']
            invoice_line = self.env['account.invoice.line']
            try:
                inv = invoice.create({'partner_id': self.partner_id.id, 'account_id': self.partner_id.property_account_payable.id,
                                      'document_type': self.partner_id.document_type.id, 'tax_support': self.partner_id.tax_support.id,
                                      'type': 'in_invoice', 'origin': self.importation_id.name})
                description = self.product_id.description if self.product_id.description else self.product_id.name
                taxes = []
                for tax in self.product_id.supplier_taxes_id:
                    tax_to_add = tax.id
                    if tax.description in ('1', '2'):
                        fiscal = self.env['account.fiscal.position.tax'].search([('position_id', '=', self.partner_id.property_account_position.id),
                                                                                 ('tax_src_id.description', '=', tax.description)])
			if not fiscal:
                            raise except_orm('Error de configuración !', 'Debe configurar la posición fiscal del proveedor')
                        tax_to_add = fiscal.tax_dest_id.id
                    taxes.append(tax_to_add)
                invoice_line.create({'product_id': self.product_id.id, 'name': description, 'account_id': self.product_id.property_account_expense.id, 'quantity': 1,
                                     'uos_id': self.product_id.uom_id.id, 'price_unit': self.amount, 'invoice_id': inv.id,
                                     'invoice_line_tax_id': [[6, 0, taxes]]})
            except ValueError:
                raise except_orm('Error!', 'Error al generar la factura, revise las configuraciones')
            self.invoiced = True
            invoice_ids = [i.id for i in self.importation_id.invoice_ids]
            invoice_ids.append(inv.id)
            self.importation_id.invoice_ids = [[6, False, invoice_ids]]
        else:
            self.ipa_account_move_create()
            self.invoiced = True

    #Asiento para el producto que tenga marcado que es impuesto aduanero

    def ipa_account_move_create(self):
        move = self.env['account.move']
        period = self.env['account.period']
        journal = self.env['account.journal']
        move_line = self.env['account.move.line']
        period_obj = period.search([('date_start', '<=', self.importation_id.date_order), ('date_stop', '>=', self.importation_id.date_order)], limit=1)
        if not period_obj:
            raise except_orm('Error!', 'No existe un periodo contable definido para la fecha de la importacion')
        journal_obj = journal.search([('code', '=', 'DIPA'), ('company_id', '=', self.company_id.id)], limit=1)
        if not journal_obj:
            raise except_orm('Error!', 'No existe un diario con el codigo DIPA')
        move_obj = move.create({'ref': 'Imp. Aduaneros', 'journal_id': journal_obj.id, 'date': datetime.now().strftime('%Y-%m-%d'), 'period_id': period_obj.id})
        move_line.create(self.get_line_vals(move_obj, self.product_id.property_account_expense.id, self.amount, 0.00))
        move_line.create(self.get_line_vals(move_obj, self.partner_id.property_account_payable.id, 0.00, self.amount, self.partner_id.id))
        return move_obj

    def get_line_vals(self, move, account, debit, credit,partner=False):
        return {
            'name': self.product_id.name,
            'quantity': 0,
            'date': move.date,
            'debit': debit,
            'credit': credit,
            'account_id': account,
            'move_id': move.id,
            'partner_id': partner
        }


class purchase_order(models.Model):
    _inherit = 'purchase.order'

    @api.one
    def _get_importation_ids(self):
        if isinstance(self.id, int):
            res = [self.id, ]
            importation_ids = list()
            query = """ SELECT i.id, o.id FROM purchase_importation i, purchase_order o
                WHERE o.id in %s and i.origin = o.name
                GROUP BY i.id, o.id """
            self._cr.execute(query, (tuple(res),))
            imp = self._cr.fetchall()
            for imps_id, po_id in imp:
                importation_ids.append(imps_id)
            self.imp_ids = importation_ids
        else:
            pass

    @api.multi
    def view_importations(self):
        mod_obj = self.env['ir.model.data']
        act_obj = self.env['ir.actions.act_window']
        dummy, action_id = tuple(mod_obj.get_object_reference('o2s_purchase_importation', 'action_purchase_importation'))
        action = act_obj.search_read([('id', '=', action_id)])[0]

        imp_ids = []
        for po in self:
            imp_ids += [importation.id for importation in po.imp_ids]

        # override the context to get rid of the default filtering on picking type
        action['context'] = {}
        # choose the view_mode accordingly
        if len(imp_ids) > 1:
            action['domain'] = "[('id','in',[" + ','.join(map(str, imp_ids)) + "])]"
        else:
            res = mod_obj.get_object_reference('o2s_purchase_importation', 'form_purchase_importation')
            action['views'] = [(res and res[1] or False, 'form')]
            action['res_id'] = imp_ids and imp_ids[0] or False
        return action

    @api.one
    def _count(self):
        self.imp_count = len(self.imp_ids)
        if not len(self.imp_ids):
            self.imp_count = 0

    destination = fields.Selection([('importation', 'Importacion'), ('internal', 'Proveedor Nacional')],
                                   'Origen de Compra', default='internal')
    imp_ids = fields.One2many('purchase.importation', compute=_get_importation_ids, string='Importation List')
    imp_count = fields.Float('Shipments', compute=_count)

    # @api.multi
    # def wkf_confirm_order(self):
    #     orders = self.env['purchase.order']
    #     for po in self:
    #         if po.destination == 'importation':
    #             # creo lineas de pedido
    #             for quot in po.quotes_ids:
    #                 if quot.state == 'done':
    #                     for line in quot.quotes_lines:
    #                         if line.state =='done':
    #                             if line.price_subtotal < 0.00:
    #                                 raise except_orm('Error!',
    #                                                  'Una linea de la cotizacion %s esta aprobada y su valor es menor o igual a 0.00' % quot.name)
    #                             po.wkf_confirm_order()
    #             #quot = self.create_simple_order(po.quotes_ids)
    #             # if not po.order_line:
    #             #     raise except_orm('Error!',
    #             #                      'La orden no tiene lineas de compras, posiblemente debido a que no se ha aprobado ninguna de las cotizaciones')
    #             po.partner_id = quot.partner_id.id
    #             import_lines = []
    #             for po_line in po.order_line:
    #                 if po_line.state == 'cancel':
    #                     continue
    #                 line_vals = {
    #                     'name': po_line.name,
    #                     'product_qty': po_line.product_qty,
    #                     'product_id': po_line.product_id.id,
    #                     'product_uom': po_line.product_uom.id,
    #                     'price_unit': po_line.price_unit,
    #                     'imported': False,
    #                     'account_analytic_id': po_line.account_analytic_id.id,
    #                     'date_planned': po_line.date_planned,
    #                     'taxes_id': [(6, 0, [t.id for t in po_line.taxes_id])],
    #                 }
    #                 import_lines.append((0, 0, line_vals))
    #             import_vals = {
    #                 'name': po.name,
    #                 'employee_id': po.req_user_id.id,
    #                 'user_id' : po.app_user_id.id,
    #                 'date_order': po.date_order,
    #                 'partner_id': po.partner_id.id,
    #                 'company_id': po.company_id.id,
    #                 'order_lines': import_lines,
    #                 'state': 'done',
    #                 'comment': po.notes,
    #             }
    #             importation = self.env['importation.order'].create(import_vals)
    #             po.order_line.action_confirm()
    #             po.write({'state': 'done', 'validator': self.env.uid})
    #             print "linea"
    #         else:
    #             orders += po
    #             #ids_to_continue.append(po.id)
    #     print "orders to super", orders
    #     if orders:
    #         return super(purchase_order, orders).wkf_confirm_order()
    #     return True

    def action_picking_create(self, cr, uid, ids, context=None):
        picking_id = self.pool.get('stock.picking')
        for order in self.browse(cr, uid, ids):
            if order.destination == 'importation':
                print "create picking importation", order.state
                self.pool.get('purchase.order.line').action_confirm(cr, uid, order.order_line.ids, context)
                self.write(cr, uid, [order.id], {'state': 'done', 'validator': uid})
            else:
                picking_vals = {
                    'picking_type_id': order.picking_type_id.id,
                    'partner_id': order.partner_id.id,
                    'date': order.date_order,
                    'origin': order.name
                }
                picking_id = self.pool.get('stock.picking').create(cr, uid, picking_vals, context=context)
                self._create_stock_moves(cr, uid, order, order.order_line, picking_id, context=context)
                #return picking_id
                print "create picking importation"
        return picking_id
