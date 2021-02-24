# -*- coding: utf-8 -*-
###############################
#  Objetos de Servicio para petroleras  #
###############################

from openerp import models, fields, api
from openerp.exceptions import except_orm, Warning
from openerp.tools.translate import _
from datetime import datetime, date, timedelta


class service_block_field(models.Model):
    _name = 'service.block.field'

    name = fields.Char('Bloque', size=8)
    description = fields.Char('Nombre', size=128)
    operator = fields.Char('Operadora', size=128)


class service_block(models.Model):
    _name = 'service.block'

    name = fields.Char('Nombre')
    block_field_id = fields.Many2one('service.block.field', 'Bloque')
    block_description = fields.Char('Descripcion')
    block_operator = fields.Char(related='block_field_id.operator')
    field_ids = fields.One2many('service.field', 'block_id', 'Campos')

    @api.onchange('block_field_id')
    def onchange_block_field_id(self):
        for record in self:
            if record.block_field_id:
                record.name = self.block_field_id.description + ' ' + record.block_field_id.name


class service_field(models.Model):
    _name = 'service.field'

    name = fields.Char('Campo')
    block_id = fields.Many2one('service.block', 'Bloque')
    block_field_id = fields.Many2one('service.block.field', 'Nombre Bloque')


class service_well(models.Model):
    _name = 'service.well'

    name = fields.Char('Nombre')
    field_id = fields.Many2one('service.field', 'Campo')
    well_line_ids = fields.One2many('service.well.line', 'well_id', 'Campos')

    @api.onchange('field_id')
    def onchange_name(self):
        if self.field_id:
            self.name = self.field_id.name


class service_well_line(models.Model):
    _name = 'service.well.line'

    name = fields.Char('Nombre')
    well_type = fields.Selection([('location', 'Locacion'), ('pool', 'Pozo')], 'Estado', default='pool')
    rig_ids = fields.Many2many(comodel_name='service.rig', string='Taladros')
    well_id = fields.Many2one('service.well', 'Campo')
    field_id = fields.Many2one('service.field', 'Campos')

    @api.onchange('well_id')
    def onchange_field_id(self):
        if self.well_id:
            self.field_id = self.well_id.field_id.id


class service_rig(models.Model):
    _name = 'service.rig'

    name = fields.Char('Nombre')
    code = fields.Char('Codigo')
    service_well_id = fields.Many2one('service.well.line')


class service_land(models.Model):
    _name = 'service.land'

    name = fields.Char('Nombre', size=32)


class service_line(models.Model):
    _name = 'service.line'

    name = fields.Char('Linea de Negocio')
    sequence_id = fields.Many2one('ir.sequence', 'Secuencia')
    location_id = fields.Many2one('stock.location', 'Localizacion')


class service_ticket(models.Model):

    _name = 'service.ticket'
    _order = "create_date"

    st = {'prov': 'Si', 'invoice': 'No', 'rever':'No'}

    SALE_TYPES = [('rentOrder', 'Orden de Renta'),
                  ('repairOrder', 'Orden de Reparacion'),
                  ]

    @api.one
    def _invoice_state(self):
        state = ''
        for order in self.order_ids:
            for invoice in order.invoice_ids:
                state = self.st[invoice.state_provision]
                break
        if len(state) <= 1:
            state = 'S/F'
        self.state_invoice = state
        self.write({'st_store': state})

    @api.model
    def _default_company(self):
        user = self.env['res.users'].browse(self._uid)
        return user.company_id.id


    @api.model
    def control_default(self):
        control = self.env['control.sheet.report'].search([('model_id.model', '=', self._name)])
        return [(0, 0, {'control_id': i.id, 'report':i.report, 'code':i.code,'review':i.review,'issue':i.issue}) for i in control]

    @api.one
    @api.depends('name_pedido','number_req')
    def name_service_ticket(self):

        for o in self:
            if o.order_ids:
                self.name_pedido = o.order_ids.name
                self.number_req= o.order_ids.number_req

    name = fields.Char('Nombre')  # readonly=True
    line_id = fields.Many2one('service.line', 'Linea de Negocio', required=True)
    partner_id = fields.Many2one('res.partner', 'Cliente', required=True)
    contract_id = fields.Many2one('account.analytic.account', 'Contrato')
    project_id = fields.Many2one('account.analytic.account', 'Proyecto')
    field_id = fields.Many2one('service.field', 'Campo')
    service_well_id = fields.Many2one('service.well.line', 'Pozo')
    block_field_id = fields.Many2one('service.block.field', 'Nombre Bloque')
    well_id = fields.Many2one('service.well', 'Pozo')
    drill_id = fields.Many2one('service.rig', 'Taladro')
    date_start = fields.Datetime('Fecha Inicio')
    date_end = fields.Datetime('Fecha Final')
    responsible_id = fields.Many2one('hr.employee', 'Responsable', required=True)
    event = fields.Selection([('drill', 'Drilling'), ('work', 'Workover'), ('facilities', 'Facilities'),
                              ('w_line', 'Wire Line'), ('m_shop', 'Machine Shop'),
                              ('tubing', 'Coiled Tubing'), ('repair', 'Repair Services'),
                              ('less', 'Rig Less'), ('tubular', 'Tubular Services'),
                              ('cement', 'Cementing'), ('rental', 'Rental Services'),
                              ('lift', 'Artificial Lift'), ('liner', 'Liner Hanger'),
                              ('well', 'Wellhead'), ('bop', 'B.O.P. Services'), ('completation', 'Completacion'),
                              ('another', 'Otros')
                              ], 'Evento', required=True)
    company_man = fields.Char('Company Man')
    company_jun = fields.Char('Company Junior')
    description = fields.Text('Descripcion')
    done_description = fields.Text('Trabajo')
    employee_ids = fields.One2many('service.employee.asigned', 'ticket_id', 'Empleados Asignados', required=True)
    order_ids = fields.One2many('sale.order', 'ticket_id', 'Pedidos')
    picking_ids = fields.One2many('stock.picking', 'ticket_id', 'Movimientos de Inventario')
    state = fields.Selection([('order', 'Orden'), ('progress', 'En Proceso'),
                              ('toinv', 'Por Facturar'), ('prov', 'Provisionado'),
                              ('done', 'Facturado'), ('cancel', 'Anulado')], 'Estado', default='order')
    work_id = fields.Many2one('work.product.rel', 'Trabajo')
    state_invoice = fields.Char('Provisionado', compute=_invoice_state)
    st_store = fields.Char('Provisionado')
    company_id = fields.Many2one('res.company', 'Compania', default=_default_company)
    is_rent = fields.Boolean('Es Renta')
    is_repair = fields.Boolean('Es Reparacion')
    sale_type = fields.Selection(SALE_TYPES, 'Sale order types')
    product_detail_ids =fields.One2many('product.customer.ticke', 'service_ticket_id', string="Producto")
    control_sheet_ids = fields.One2many('service.control.sheet', 'service_control_id', string="Gestion de Calidad", default=control_default)
    service_opetation_ids = fields.One2many('service.ticket.opetation', 'service_id', 'Operacion')
    name_pedido = fields.Char('Periodo', compute=name_service_ticket)
    number_req = fields.Char('Pedido Qeq',compute=name_service_ticket)
    super_int = fields.Char('Superintendente', size=32)

    @api.model
    def create(self, vals):
        super(stock_picking, self).create(vals)
        for ml in vals.get('move_lines'):
            if ml.product_id:
                if vals.get('type_reception') == 'order' and ml.qty_available == 0:
                    raise except_orm('Error!', 'No posee Cantidad disponible para el producto %s' % ml.product_id.name)

    @api.multi
    def action_confirm(self):
        for record in self:
            # record.name = self.env['ir.sequence'].get_id(record.line_id.sequence_id.id)
            if not record.order_ids:
                raise except_orm('Error!', 'No hay pedidos de ventas generados')
            for order in record.order_ids:
                if order.state != 'cancel':
                    repair_order = order.is_repair
                    sp = self.create_stock_picking(order, repair_order)
                    for line in order.order_line:
                        self.create_stock_move(sp, line)

            record.state = 'progress'
            for picking in record.picking_ids:
                if not picking.type_reception:
                    raise except_orm(_('Error!'),
                                     _('El albaran "%s" no tiene configurado Tipo Recepcion') % (picking.origin))

    def create_stock_picking(self, order, repair):
        pick = self.env['stock.picking']
        if repair:
            picktype = self.env['stock.picking.type'].search(
                [('code', '=', 'incoming'), ('warehouse_id', '=', order.warehouse_id.id)])
        else:
            picktype = self.env['stock.picking.type'].search(
                [('code', '=', 'outgoing'), ('warehouse_id', '=', order.warehouse_id.id)])
        if picktype:
            picktype = picktype.id
        if repair:
            return pick.create({'origin': order.name, 'partner_id': order.partner_id.id, 'picking_type_id': 3,
                                'ticket_id': order.ticket_id.id, 'type_reception': 'order'})
        return pick.create({'origin': order.name, 'partner_id': order.partner_id.id, 'picking_type_id': picktype, 'ticket_id': order.ticket_id.id, 'type_reception':'order'})

    def create_stock_move(self, picking, line):
        move = self.env['stock.move']
        default_location_src_id = False
        default_location_dest_id = False
        if not picking.picking_type_id or not picking.picking_type_id.default_location_src_id or not picking.picking_type_id.default_location_dest_id:
            raise except_orm('Error!', 'Configure las ubicaciones por defecto en los tipos de operacion')
        default_location_src_id = picking.picking_type_id.default_location_src_id.id
        default_location_dest_id = picking.picking_type_id.default_location_dest_id.id
        if not line.product_id.is_lumpsum:
            move.create({'picking_id': picking.id, 'product_id': line.product_id.id, 'name': line.name, 'product_uom_qty': line.product_uom_qty,
                         'product_uom': line.product_id.uom_id.id, 'state': 'draft', 'procure_method': 'make_to_stock',
                         'location_id': default_location_src_id, 'location_dest_id': default_location_dest_id,
                         'picking_type_id': picking.picking_type_id.id})
        else:
            if line.product_id.components:
                for cmp in line.product_id.components:
                    move.create({'picking_id': picking.id, 'product_id': cmp.product_id.id, 'name': cmp.product_id.name, 'product_uom_qty': cmp.qty,
                                 'product_uom': cmp.uom_id.id, 'state': 'draft', 'procure_method': 'make_to_stock',
                                 'location_id': default_location_src_id, 'location_dest_id': default_location_dest_id,
                                 'picking_type_id': picking.picking_type_id.id})

    @api.multi
    def set_draft(self):
        for record in self:
            record.state = 'order'

    @api.multi
    def action_cancel(self):
        for record in self:
            record.state = 'cancel'

    @api.multi
    def action_closed(self):
        pick_ids = []
        for record in self:
            if record.is_repair:
                if not (record.employee_ids and record.company_man and record.picking_ids):
                    raise except_orm('Error!', 'No se puede cerrar el ticket porque faltan datos')
            record.state = 'toinv'
            # if record.picking_ids.origin in record.ticket_id.order_ids.name or record:
            # comento para pasar el control de asientos contables y poder confirmar el ticket
            # pick_ids += [picking.id for picking in record.picking_ids]
            # self.create_account_move(pick_ids)

    @api.multi
    def action_invoiced(self):
        for record in self:
            for order in record.order_ids:
                if order.state != 'cancel':
                    order.action_button_confirm()
                    self.pool['sale.order'].signal_workflow(self._cr, self._uid, [order.id], 'manual_invoice')
                    order.action_done()
            record.state = 'done'

    def create_account_move(self, pickings):

        stockpicking = self.env['stock.picking'].search([('id','in', pickings),('type_reception','in',['order','materials'])])

        for picking in stockpicking:
            stockmove = self.env['stock.move'].search([('picking_id','=',picking.id)])
            period = self.env['account.period'].search([('date_start', '<=', picking.date), ('date_stop', '>=', picking.date)], limit=1)
            for move in stockmove:
                move_obj = self.env['account.move']
                if move.picking_id.type_reception == 'order':
                    move_lines = self.create_account_move_lines_so(move)
                elif move.picking_id.type_reception == 'materials':
                    move_lines = self.create_account_move_lines_default(move)
                else:
                    raise except_orm('Error!', 'Albaran no tiene especificado campo Tipo Recepcion')

                if move_lines:
                    move_obj.create( {'journal_id': move.product_id.product_tmpl_id.categ_id.property_stock_journal.id,
                                      'line_id': move_lines,
                                      'period_id': period.id,
                                      'date': move.date,
                                      'ref': move.picking_id.name})

    def create_account_move_lines_so(self, move_stock):
        for move in move_stock:
            partner_id = (move.picking_id.partner_id and self.pool.get('res.partner')._find_accounting_partner(move.picking_id.partner_id).id) or False
            if move.product_id.property_account_expense.id:
                debit_line_vals_gasto = {
                    'name': move.name,
                    'product_id': move.product_id.id,
                    'quantity': move.product_qty,
                    'product_uom_id': move.product_id.uom_id.id,
                    'ref': move.picking_id and move.picking_id.name or False,
                    'date': move.date,
                    'partner_id': partner_id,
                    'debit': move.product_qty * self.sum_series(move.product_id, move.serial_item_id)[2],
                    'credit': 0.00,
                    'account_id': move.product_id.property_account_expense.id,
                }
            else:
                raise except_orm('Error!', 'El producto: ' + move.product_id.name + ' No tiene configurado cuenta de gasto')

            if move.product_id.property_stock_account_input.id:
                credit_line_vals_inventario = {
                    'name': move.name,
                    'product_id': move.product_id.id,
                    'quantity': move.product_qty,
                    'product_uom_id': move.product_id.uom_id.id,
                    'ref': move.picking_id and move.picking_id.name or False,
                    'date': move.date,
                    'partner_id': partner_id,
                    'debit': 0.00,
                    'credit': move.product_qty * self.sum_series(move.product_id, move.serial_item_id)[0],
                    'account_id': move.product_id.property_stock_account_input.id,
                }
            else:
                raise except_orm('Error!', 'El producto: ' + move.product_id.name + ' No tiene configurado cuenta de inventario')

            if move.product_id.property_stock_account_output.id:
                credit_line_vals_costo = {
                    'name': move.name,
                    'product_id': move.product_id.id,
                    'quantity': move.product_qty,
                    'product_uom_id': move.product_id.uom_id.id,
                    'ref': move.picking_id and move.picking_id.name or False,
                    'date': move.date,
                    'partner_id': partner_id,
                    'debit': 0.00,
                    'credit': move.product_qty * self.sum_series(move.product_id, move.serial_item_id)[1],
                    'account_id': move.product_id.property_stock_account_output.id,
                }
            else:
                raise except_orm('Error!', 'El producto: ' + move.product_id.name + ' No tiene configurado cuenta de costo de inventario')

        return [(0, 0, debit_line_vals_gasto), (0, 0, credit_line_vals_inventario), (0, 0, credit_line_vals_costo)]

    def create_account_move_lines_default(self, move_stock):
        for move in move_stock:
            partner_id = (move.picking_id.partner_id and self.pool.get('res.partner')._find_accounting_partner(move.picking_id.partner_id).id) or False
            if move.product_id.property_account_expense.id:
                debit_line_vals_gasto = {
                    'name': move.name,
                    'product_id': move.product_id.id,
                    'quantity': move.product_qty,
                    'product_uom_id': move.product_id.uom_id.id,
                    'ref': move.picking_id and move.picking_id.name or False,
                    'date': move.date,
                    'partner_id': partner_id,
                    'debit': move.product_id.standard_price * move.product_qty,
                    'credit': 0.00,
                    'account_id': move.product_id.property_account_expense.id,
                }
            else:
                raise except_orm('Error!', 'El producto: ' + move.product_id.name + ' No tiene configurado cuenta de gasto')


            if move.product_id.property_stock_account_input.id:
                credit_line_vals_inventario = {
                    'name': move.name,
                    'product_id': move.product_id.id,
                    'quantity': move.product_qty,
                    'product_uom_id': move.product_id.uom_id.id,
                    'ref': move.picking_id and move.picking_id.name or False,
                    'date': move.date,
                    'partner_id': partner_id,
                    'debit': 0.00,
                    'credit': move.product_id.standard_price * move.product_qty,
                    'account_id': move.product_id.property_stock_account_input.id,
                }
            else:
                raise except_orm('Error!', 'El producto: ' + move.product_id.name + ' No tiene configurado cuenta de inventario')

        return [(0, 0, debit_line_vals_gasto), (0, 0, credit_line_vals_inventario)]

    def sum_series(self, product_id, serial_id):

        if serial_id:
            series = self.env['serial.item'].search([('product_id','=', product_id.id),('id','=',serial_id.id )])
            list = []
            if series:
                importation_amount = 0
                amount_cost = 0
                total = 0
                for ser in series:
                    importation_amount += round(ser.importation_amount,2)
                    amount_cost += round(ser.amount_cost,2)
                    total += importation_amount + amount_cost
                    list.append(amount_cost)
                    list.append(importation_amount)
                    list.append(total)
        else:
            raise except_orm('Error!', 'El producto: ' + product_id.name + ' No tiene series creadas')
        return list

    @api.model
    def create(self, vals):
        # print "vals: ", vals
        if vals.get('order_ids'):
            if len(vals.get('order_ids')) > 1:
                raise except_orm('Error!', 'Debe crear solo una linea de pedido')
        name = '/'
        if (not vals.get('is_rent') and not vals.get('is_repair')):
            name = self.env['ir.sequence'].next_by_code('service.ticket.sale.sequence')
        elif vals.get('is_rent'):
            name =self.env['ir.sequence'].next_by_code('service.ticket.rent.sequence')
        elif vals.get('is_repair'):
            name = self.env['ir.sequence'].next_by_code('service.ticket.repair.sequence')
        vals.update({'name':name})
        return super(service_ticket, self).create(vals)


class service_employee_asigned(models.Model):

    _name = 'service.employee.asigned'

    employee_id = fields.Many2one('hr.employee', 'Empleado', required=True)
    date_start = fields.Datetime('Inicio')
    date_end = fields.Datetime('Fin')
    ticket_id = fields.Many2one('service.ticket', 'Ticket')


class sale_order(models.Model):
    _inherit = 'sale.order'

    @api.v7
    def action_cancel(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        sale_order_line_obj = self.pool.get('sale.order.line')
        account_invoice_obj = self.pool.get('account.invoice')
        for sale in self.browse(cr, uid, ids, context=context):
            for inv in sale.invoice_ids:
                if inv.state not in ('draft', 'cancel', 'invalidate'):
                    raise except_orm(
                        _('Cannot cancel this sales order!'),
                        _('First cancel all invoices attached to this sales order.'))
                inv.signal_workflow('invoice_cancel')
            line_ids = [l.id for l in sale.order_line if l.state != 'cancel']
            sale_order_line_obj.button_cancel(cr, uid, line_ids, context=context)
        self.write(cr, uid, ids, {'state': 'cancel'})
        return True

    @api.multi
    def _sale_state_invoice(self):
        for sale_order in self:
            state = ''
            dinvoice = ''
            ninvoice = ''
            if sale_order.state in ('manual', 'progress', 'done'):
                if not len(sale_order.invoice_ids):
                    state = 'anyone'
                    dinvoice = ''
                for inv in sale_order.invoice_ids:
                    if inv.state == 'draft':
                        state = 'draft'
                        dinvoice = inv.date_invoice
                    if inv.state == 'open':
                        state = 'open'
                        dinvoice = inv.date_invoice
                        ninvoice = inv.number_reem
                    if inv.state == 'paid':
                        state = 'paid'
                        dinvoice = inv.date_invoice
                        ninvoice = inv.number_reem
                    if inv.state not in ('draft', 'paid', 'open'):
                        state = 'invalidate'
                        dinvoice = inv.date_invoice
            sale_order.date_invoice = dinvoice
            sale_order.inv_state = state
            sale_order.invoice_number = ninvoice

    @api.multi
    def state_invoice(self):
        for order in self:
            order.istate = order.inv_state

    SALE_TYPES = [('rentOrder', 'Orden de Renta'),
                  ('repairOrder', 'Orden de Reparacion'),
                  ]

    @api.one
    def _total_discount(self):
        discount = 0.00
        for line in self.order_line:
            if line.discount:
                discount += ((line.price_unit * line.product_uom_qty) - line.price_subtotal)
                self.total_discount = discount

    ticket_id = fields.Many2one('service.ticket', 'Ticket')
    sale_type = fields.Selection(SALE_TYPES, 'Sale order types')
    is_rent = fields.Boolean('Es Renta')
    is_repair = fields.Boolean('Es Reparacion')
    number_req = fields.Char('No. Cotizacion')
    total_discount = fields.Float(compute=_total_discount, string="Descuento Total")
    sale_note = fields.Char('Asunto', size=128)
    inv_state = fields.Char('Estado Factura', compute=_sale_state_invoice)
    istate = fields.Selection([('draft', 'Borrador'), ('open', 'Factura Validada'),
                               ('paid', 'Factura Pagada'), ('invalidate', 'Anulada'), ('anyone', 'No generada')],
                              'Estado', compute=state_invoice, help='Indica el estado de la factura adjunta a esta orden')
    date_invoice = fields.Date('Fecha Factura', compute=_sale_state_invoice,
                               help='Indica la fecha de la factura adjunta a esta orden')
    invoice_number = fields.Char('Numero Factura', compute=_sale_state_invoice, help='Indica el numero de la factura')

    @api.model
    def default_get(self, fields_list):
        res = super(sale_order, self).default_get(fields_list)
        print "self._context: ", self._context
        if 'contract_id' in self._context and 'partner_id' in self._context:
            res['partner_id'] = self._context['partner_id']
            #res['client_order_ref'] = self._context['default_name']
            res['name'] = '/'

            contract = self.env['account.analytic.account'].browse(self._context['contract_id'])
            res['pricelist_id'] = contract.pricelist_id.id
        return res

    def _prepare_line(self, work_item, pricelist, partner):
        res = self.pool('sale.order.line').product_id_change(self._cr, self._uid, False, pricelist, work_item.product_id.id, work_item.qty, partner_id=partner)
        res['value'].update({'product_id': work_item.product_id.id, 'product_uom_qty': work_item.qty,
                             'delay': 0, 'is_reemb': False, 'state': 'draft'})
        return res['value']

    @api.v7
    def onchange_fiscal_position(self, cr, uid, ids, fiscal_position, order_lines, context=None):
        res = super(sale_order, self).onchange_fiscal_position(cr, uid, ids, fiscal_position, order_lines, context)
        if order_lines:
            return res
        pass

    @api.v7
    def onchange_partner_id(self, cr, uid, ids, part, context=None):
        if not part:
            return {'value': {'partner_invoice_id': False, 'partner_shipping_id': False,  'payment_term': False, 'fiscal_position': False}}

        part = self.pool.get('res.partner').browse(cr, uid, part, context=context)
        addr = self.pool.get('res.partner').address_get(cr, uid, [part.id], ['delivery', 'invoice', 'contact'])
        # pricelist = part.property_product_pricelist and part.property_product_pricelist.id or False
        invoice_part = self.pool.get('res.partner').browse(cr, uid, addr['invoice'], context=context)
        payment_term = invoice_part.property_payment_term and invoice_part.property_payment_term.id or False
        dedicated_salesman = part.user_id and part.user_id.id or uid
        val = {
            'partner_invoice_id': addr['invoice'],
            'partner_shipping_id': addr['delivery'],
            'payment_term': payment_term,
            'user_id': dedicated_salesman,
        }
        delivery_onchange = self.onchange_delivery_id(cr, uid, ids, False, part.id, addr['delivery'], False,  context=context)
        val.update(delivery_onchange['value'])
        # if pricelist:
        #     val['pricelist_id'] = pricelist
        if not self._get_default_section_id(cr, uid, context=context) and part.section_id:
            val['section_id'] = part.section_id.id
        sale_note = self.get_salenote(cr, uid, ids, part.id, context=context)
        if sale_note: val.update({'note': sale_note})
        return {'value': val}

    @api.v7
    def _prepare_invoice(self, cr, uid, order, lines, context=None):
        """Prepare the dict of values to create the new invoice for a
           sales order. This method may be overridden to implement custom
           invoice generation (making sure to call super() to establish
           a clean extension chain).

           :param browse_record order: sale.order record to invoice
           :param list(int) line: list of invoice line IDs that must be
                                  attached to the invoice
           :return: dict of value to create() the invoice
        """
        if context is None:
            context = {}
        journal_ids = self.pool.get('account.journal').search(cr, uid,
                                                              [('type', '=', 'sale'), ('company_id', '=', order.company_id.id)],
                                                              limit=1)
        if not journal_ids:
            raise except_orm(_('Error!'),
                             _('Please define sales journal for this company: "%s" (id:%d).') % (order.company_id.name, order.company_id.id))
        invoice_vals = {
            'name': order.client_order_ref or '',
            'origin': order.name,
            'type': 'out_invoice',
            'reference': order.client_order_ref or order.name,
            'account_id': order.partner_invoice_id.property_account_receivable.id,
            'partner_id': order.partner_invoice_id.id,
            'journal_id': journal_ids[0],
            'invoice_line': [(6, 0, lines)],
            'currency_id': order.pricelist_id.currency_id.id,
            'comment': order.note,
            'payment_term': order.payment_term and order.payment_term.id or False,
            'fiscal_position': order.fiscal_position.id or order.partner_invoice_id.property_account_position.id,
            'date_invoice': context.get('date_invoice', False),
            'company_id': order.company_id.id,
            'user_id': order.user_id and order.user_id.id or False,
            'section_id': order.section_id.id,
            # 'ticket_ids': [[6, 0, [order.ticket_id.id]]],
        }

        # Care for deprecated _inv_get() hook - FIXME: to be removed after 6.1
        invoice_vals.update(self._inv_get(cr, uid, order, context=context))
        return invoice_vals

    @api.model
    def create(self, vals):
        # print "vals: ", vals
        name = '/'
        if (not vals.get('is_rent') and not vals.get('is_repair')):
            name = self.env['ir.sequence'].next_by_code('cotizacion.ven.sequence')
        elif vals.get('is_rent'):
            name = self.env['ir.sequence'].next_by_code('cotizacion.rent.sequence')
        elif vals.get('is_repair'):
            name = self.env['ir.sequence'].next_by_code('cotizacion.repar.sequence')

        vals.update({'name': name, 'number_req':name})

        return super(sale_order, self).create(vals)


    @api.multi
    def action_button_confirm(self):
        super(sale_order, self).action_button_confirm()
        if self.editbolean:
            name= self.name
        elif (not self.is_rent and not self.is_repair):
            name = self.env['ir.sequence'].next_by_code('orden.ven.sequence')
        elif self.is_rent:
            name = self.env['ir.sequence'].next_by_code('orden.rent.sequence')
        elif self.is_repair:
            name = self.env['ir.sequence'].next_by_code('orden.repar.sequence')
        self.update({'name': name})


class sale_order_line(models.Model):
    _inherit = 'sale.order.line'

    @api.model
    def control_default(self):
        control = self.env['control.sheet.report'].search([('model_id.model', '=', self._name)])
        return [(0, 0, {'control_id': i.id, 'report':i.report, 'code':i.code,'review':i.review,'issue':i.issue}) for i in control]

    custom_identificator = fields.Char('Id Cliente')
    date_rent_from = fields.Date('F. Desde', default=date.today())
    date_rent_to = fields.Date('F. Hasta', default=date.today() + timedelta(days=1))
    # es_renta = fields.Boolean('Es Renta', related='order_id.is_rent')
    rent_days = fields.Integer('Dias Renta')
    price_subtotal = fields.Float(compute='_amount_lines', string='Subtotal', )
    control_sheet_ids = fields.One2many('sale.control.sheet', 'sale_control_id', string="Gestion de Calidad",default=control_default)
    item_price_list = fields.Integer('Item lista de precio')
    delivery_date = fields.Date('Fecha entrega')

    @api.onchange('date_rent_from', 'date_rent_to')
    def _onchange_date_rent_from(self):
        if not self.order_id.is_rent:
            return
        date_from = fields.Date.from_string(self.date_rent_from)
        date_to = fields.Date.from_string(self.date_rent_to)
        if date_to < date_from:
            self.date_rent_to = fields.Datetime.to_string(date_from + timedelta(days=1))
            return {'warning': {
                'title': _('Configuration Error!'),
                'message': 'La fecha de inicio no puede ser mayor a la fecha fin'
            }}
        self.rent_days = (date_to - date_from).days + 1
        # self.product_id_change(self.order_id.pricelist_id,self.product_id,self.product_uom_qty,self.product_uom,self.product_uos_qty,self.product_uos,self.name,self.order_id.partner_id,date_order=self.order_id.date_order)

        self.price_subtotal = self.price_unit * self.product_uom_qty
        #self._amount_line(None,None)

    @api.v7
    def product_id_change(self, cr, uid, ids,pricelist, product, qty=0, uom=False, qty_uos=0, uos=False, name='', partner_id=False,
                          lang=False, update_tax=True, date_order=False, packaging=False, fiscal_position=False, flag=False, context=None):
        description = False
        seq = 0
        res = super(sale_order_line, self).product_id_change(cr, uid, ids, pricelist, product, qty, uom, qty_uos, uos, name, partner_id,
                                                             lang, update_tax, date_order, packaging, fiscal_position, flag, context)

        if pricelist:
            domain = list()
            pricelist_obj = self.pool.get('product.pricelist').browse(cr, uid, pricelist, context)
            for var in pricelist_obj.version_id:
                if var.active:
                    for item in var.items_id:
                        domain.append(item.product_id.id)
                        if product and product == item.product_id.id:
                            description = item.partner_desc
                            id_cliente = item.product_partner_ident
                            seq = item.sequence

                            break
                    break
            if domain:
                res['domain'].update({'product_id': repr([('id', 'in', domain)])})
        if description:
            res['value'].update({'name': description, 'custom_identificator': id_cliente, 'item_price_list': seq})
        return res

    @api.v7
    def _prepare_order_line_invoice_line(self, cr, uid, line, account_id=False, context=None):
        res = super(sale_order_line, self)._prepare_order_line_invoice_line(cr, uid, line, account_id, context)
        if res:
            res.update({'custom_identificator': line.custom_identificator})
        return res

    @api.one
    @api.depends('product_uom_qty','rent_days','price_unit','discount','tax_id')
    def _amount_lines(self,):

        print "amount line"
        # res = super(sale_order_line, self)._amount_line(field_name, arg)
        # for line in self:
        #     if line.order_id.is_rent:
        #         res[line.id] = res[line.id] * line.rent_days

        res = {}
        for line in self:
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            if line.order_id.is_rent:
                line.product_uom_qty = line.rent_days
            print price
            taxes = line.tax_id.compute_all(price, line.product_uom_qty, line.product_id, line.order_id.partner_id)
            cur = line.order_id.pricelist_id.currency_id
            line.price_subtotal = cur.round(taxes['total'])
        return res


class stock_picking(models.Model):
    _inherit = 'stock.picking'

    @api.model
    def control_default(self):
        control = self.env['control.sheet.report'].search([('model_id.model', '=', self._name)])
        return [(0, 0, {'control_id': i.id, 'report':i.report, 'code':i.code,'review':i.review,'issue':i.issue}) for i in control]

    ticket_id = fields.Many2one('service.ticket', 'Ticket')
    reception_guide = fields.Char(string="Guia de Recepcion")
    control_sheet_ids = fields.One2many('stock.control.sheet', 'stock_control_id', string="Gestion de Calidad", default=control_default)

    @api.model
    def default_get(self, fields_list):
        res = super(stock_picking, self).default_get(fields_list)
        if 'partner_id' in self._context:
            res['partner_id'] = self._context['partner_id']
        return res


class work(models.Model):
    _name = 'work'

    name = fields.Char('Nombre')


class work_product_rel(models.Model):
    _name = 'work.product.rel'
    _rec_name = 'work_id'

    work_id = fields.Many2one('work', 'Etiqueta de Trabajo', required=True)
    items = fields.One2many('work.product.rel.item', 'rel_id', 'Productos a utilizar')
    lang = fields.Char('lenguaje', default='es_EC')


class work_product_rel_item(models.Model):
    _name = 'work.product.rel.item'

    product_id = fields.Many2one('product.product', 'Producto', required=True, domain=[('sale_ok', '=', True)])
    qty = fields.Float('Cantidad')
    rel_id = fields.Many2one('work.product.rel', 'Work Rel')


class product_category(models.Model):
    _inherit = "product.category"

    generate_accounting = fields.Boolean('No Generar Contabilidad')


class product_detail_ticke(models.Model):

    _name = "product.detail.ticke"
    _rec_name = 'name'

    def name_get(self, cr, uid, ids, context=None):
        res = []
        i = self.browse(cr, uid, ids, context)
        for obj in i:
            res.append((obj.id,obj.code + ' ' + obj.name))
        return res

    def search(self, cr, uid, args, offset=0, limit=80, order=None, context=None, count=False):
        auxiliar = list()
        for arg in args:
            if arg[0] == 'name':
                auxiliar.append(['code', 'ilike', arg[2]])
                break
        res = super(product_detail_ticke, self).search(cr, uid, args, offset, limit, order, context, count)
        if not res and auxiliar:
            res = super(product_detail_ticke, self).search(cr, uid, auxiliar, offset, limit, order, context, count)
        return res

    name = fields.Char(string="Nombre")
    code = fields.Char(string= "Codigo")
    observation =fields.Char(string="Observación")


class product_customer_ticke(models.Model):

    _name = "product.customer.ticke"

    @api.depends('name')
    def onchange_proeduct(self):
        for obj in self:
            if obj.name:
                obj.code = obj.name.code
                obj.observation = obj.name.observation

    service_ticket_id = fields.Many2one('service.ticket', string="Servicio Ticket")
    name = fields.Many2one('product.detail.ticke', string="Nombre")
    code = fields.Char(relation='name.code',string="Codigo", compute=onchange_proeduct)
    observation = fields.Char(relation='name.code',string="Observación", readonly="True")
    product_qty = fields.Float(string="Cantidad")
    motive = fields.Selection([('prestamo', 'Prestamo'),
                               ('devolucion', 'Devolucion'),
                               ('reparacion', 'Reparación'),
                               ('venta', 'Venta'),
                               ('fabricacion', 'Fabricación'),
                               ('modificacion', 'Modificación'),
                               ('otros', 'Otros'),
                               ('no_operativo', 'No Operativo'),
                               ('mantenimiento', 'Mantenimiento'),
                               ('compra', 'Compra'),
                               ],
                              'Motivo')


class service_control_sheet(models.Model):

    _name="service.control.sheet"

    service_control_id = fields.Many2one('service.ticket', string="Service Ticket")
    control_id = fields.Many2one('control.sheet.report', string="Control de Hoja")
    report = fields.Char(string="Nombre del Reporte")
    code = fields.Char(string="Codigo")
    review = fields.Char(string="Revision")
    issue = fields.Date(string="Emision")


class sale_control_sheet(models.Model):

    _name="sale.control.sheet"

    sale_control_id = fields.Many2one('sale.order', string="Orden de Venta")
    control_id = fields.Many2one('control.sheet.report', string="Control de Hoja")
    report = fields.Char(string="Nombre del Reporte")
    code = fields.Char(string="Codigo")
    review = fields.Char(string="Revision")
    issue = fields.Date(string="Emision")


class service_ticket_opetation(models.Model):

    _name ='service.ticket.opetation'

    service_id = fields.Many2one('service.ticket','Servicios')
    name = fields.Char(string="Operacion")
    repair_elemenet_id = fields.Many2one('product.customer.ticke',string='Elemento a Reparar')
    product_oum_qty = fields.Float(string="Cantidad")
    product_oum = fields.Float(string="Unidad")
    duration = fields.Float(string='Duracion')
    workcenter = fields.Char(string="Centro de Reparacion")


class stock_control_sheet(models.Model):

    _name="stock.control.sheet"

    stock_control_id = fields.Many2one('stock.pickig', string="Moviminto en Almacen")
    control_id = fields.Many2one('control.sheet.report', string="Control de Hoja")
    report = fields.Char(string="Nombre del Reporte")
    code = fields.Char(string="Codigo")
    review = fields.Char(string="Revision")
    issue = fields.Date(string="Emision")


class sale_advance_payment_inv(models.TransientModel):
    _inherit = 'sale.advance.payment.inv'

    @api.v7
    def create_invoices(self, cr, uid, ids, context=None):
        res = super(sale_advance_payment_inv, self).create_invoices(cr, uid, ids, context=context)
        sale_ids = context.get('active_ids', [])
        sale_obj = self.pool.get('sale.order')
        for sale_ids in sale_obj.browse(cr, uid, sale_ids, context=context):
            sale_ids.update({'state': 'progress'})
        return res

