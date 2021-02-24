##########################
# -*- coding: utf-8 -*- ##
##########################


from openerp import models, fields, api
from openerp.exceptions import except_orm, Warning
import openerp.addons.decimal_precision as dp
from openerp.tools.float_utils import float_compare
from datetime import datetime, date
import datetime
import time

################################################
################################################


class purchase_importation(models.Model):
    _name = 'purchase.importation'

    STATE_SELECTION = [
        ('draft', 'Borrador'),
        ('confirmed', 'Imp. en Produccion'),
        ('international', 'Transito Internacional'),
        ('customs', 'Aduana'),
        ('transit', 'Transito Nacional'),
        ('done', 'Base MP'),
        ('cancel', 'Cancelled')
    ]

    @api.multi
    def pass_international(self):
        days = 0
        for record in self:
            record.end_production_date = date.today()
            record.international_date = date.today()
            days = record.recompute_days(record.production_date, record.end_production_date)
        self.prod_days = days
        self.state = 'international'

    @api.multi
    def recompute_days(self, f1, f2):
        days = 0
        for record in self:
            if not f1 or not f2:
                f1 = str(date.today())
                ini_d = datetime.datetime.strptime(f1, '%Y-%M-%d').date()
                f2 = str(date.today())
                end_d = datetime.datetime.strptime(f2, '%Y-%M-%d').date()
                days = (end_d - ini_d).days + 1
            else:
                ini_d = datetime.datetime.strptime(f1, '%Y-%M-%d').date()
                end_d = datetime.datetime.strptime(f2, '%Y-%M-%d').date()
                days = (end_d - ini_d).days + 1

        return days

    @api.multi
    def pass_customs(self):
        days = 0
        for line in self.order_lines:
            if not line.product_id.tariff_item_id:
                raise except_orm('Error!', 'Por favor ingrese la partida '
                                           'arancelaria para el producto '
                                           '%s' % '['+line.product_id.default_code + '] ' + line.product_id.name)
        for record in self:
            record.end_international_date = date.today()
            record.customs_date = date.today()
            days = record.recompute_days(record.international_date, record.end_international_date)
        self.international_days = days
        self.state = 'customs'

    @api.one
    def _amount_total(self):
        total = 0.00
        for line in self.order_lines:
            total += line.subtotal_importation
        self.amount_total = total
        self.fob_value = total

    @api.one
    def _count_all(self):
        self.invoice_count = len(self.invoice_ids)
        self.shipment_count = len(self.picking_ids)
        self.pays_count = len(self.some_payment_ids)

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
    picking_created = fields.Boolean('Albaran creado', default=False)
    sec_generated = fields.Boolean('Secuencial')

    production_date = fields.Date('Fecha Inicio')
    end_production_date = fields.Date('Fecha Fin')
    prod_days = fields.Integer('# Dias')
    international_date = fields.Date('Fecha Inicio')
    end_international_date = fields.Date('Fecha Fin')
    international_days = fields.Integer('# Dias')
    customs_date = fields.Date('Fecha Inicio')
    end_customs_date = fields.Date('Fecha Fin')
    customs_days = fields.Integer('# Dias')
    local_date = fields.Date('Fecha Inicio')
    end_local_date = fields.Date('Fecha Fin')
    local_days = fields.Integer('# Dias')
    base_date = fields.Date('Fecha Inicio')
    days_f = fields.Char('Dias', default='DIAS')
    days_i = fields.Char('Dias', default='DIAS')
    days_t = fields.Char('Dias', default='DIAS')
    days_l = fields.Char('Dias', default='DIAS')
    # Añado tabla pagos
    payments_ids = fields.One2many('importation.payments', 'importation_id', 'Pagos', ondelete='cascade')
    some_payment_ids = fields.Many2many('account.voucher', 'purchase_importation_payment_rel', 'importation_id',
                                        'payment_id', 'Egresos', copy=False,
                                        help="Egresos generados desde la importacion")
    pays_count = fields.Float('Invoices', compute=_count_all)
    fob_value = fields.Float('Valor FOB', compute=_amount_total, store=True)
    total_liq = fields.Float('Total Importacion')
    inter_cost = fields.Float('Costo Internacion')
    eta_date = fields.Date('Fecha ETD')
    etd_date = fields.Date('Fecha ETA')
    pn_date = fields.Date('Proceso nacionalización')
    _defaults = {
        is_importation: True,
        sec_generated: False
    }

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
            self.production_date = date.today()
            if not rec.sec_generated:
                rec.sec_generated = True
                rec.name = self.env['ir.sequence'].get('purchase.importation', context=self._context) + ' ' + \
                           '(' + rec.origin + ')'
            rec.state = 'confirmed'

    @api.multi
    def button_reset_line(self):
        #CSV: 15-09-2017 AUMENTO PARA CONTROLAR LA GENERACION DE LA FACTURA SI YA SE GENERO DESDE LA ORDEN
        invoice = self.env['account.invoice']
        for record in self:
            for imp in self.env['purchase.importation'].browse(self.ids):
                inv_exist = invoice.search([('purchaorden_id', '=', imp.id)])
                for fact in inv_exist:
                    if len(fact)>0 and fact.state not in('cancel'):
                        record.write({'invoice_ids': [(4, fact.id)]})
            record.state = 'transit'
            return True

    @api.multi
    def imp_cancel(self):
        if self.state == 'done':
            raise Warning('Advertencia !', 'Estos registros ya fueron costeados')
        for rec in self:
            for invoice in rec.invoice_ids:
                if invoice.state not in ('draft', 'open'):
                    raise except_orm('Error!', 'No puede cancelar una importacion con facturas pagadas: Factura %s'
                                     % invoice.number)
                invoice.action_cancel()
            for pick in rec.picking_ids:
                if pick.state == 'done':
                    raise except_orm('Error!', 'No puede cancelar una importacion con productos recibidos: Recepcion '
                                               '%s' % pick.name)
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
    def pay_open(self):
        mod_obj = self.env['ir.model.data']
        act_obj = self.env['ir.actions.act_window']

        dummy, action_id = tuple(mod_obj.get_object_reference('o2s_account_advances', 'action_voucher_list_somepays'))
        action = act_obj.search_read([('id', '=', action_id)])[0]
        pays_ids = []
        for po in self:
            pays_ids += [pay.id for pay in po.some_payment_ids]
        action['context'] = {}
        # choose the view_mode accordingly
        if len(pays_ids) > 1:
            action['domain'] = "[('id','in',[" + ','.join(map(str, pays_ids)) + "])]"
        else:
            res = mod_obj.get_object_reference('o2s_account_advances', 'account_voucher_form_view_somepays')
            action['views'] = [(res and res[1] or False, 'form')]
            action['res_id'] = pays_ids and pays_ids[0] or False

        return action

    @api.multi
    def view_picking(self):
        mod_obj = self.env['ir.model.data']
        act_obj = self.env['ir.actions.act_window']
        dummy, action_id = tuple(mod_obj.get_object_reference('stock', 'action_picking_tree'))
        action = act_obj.search_read([('id', '=', action_id)])[0]

        pick_ids = []
        for po in self:
            pick_ids += [picking.id for picking in po.picking_ids]

        # override the context to get rid of the default filtering on picking type
        action['context'] = {}
        # choose the view_mode accordingly
        if len(pick_ids) > 1:
            action['domain'] = "[('id','in',[" + ','.join(map(str, pick_ids)) + "])]"
        else:
            res = mod_obj.get_object_reference('stock', 'view_picking_form')
            action['views'] = [(res and res[1] or False, 'form')]
            action['res_id'] = pick_ids and pick_ids[0] or False
        return action

    @api.multi
    def create_credit_account_move(self, line_id, move, new_price):
        move_id = ()
        if line_id:
            move_line = self.env['account.move.line']
            today = date.today().strftime('%Y-%m-%d')
            period_obj = self.env['account.period']
            period = period_obj.search([('date_start', '<=', today), ('date_stop', '>=', today)], limit=1)
            if not period:
                raise except_orm('Error!', 'No existe un periodo contable definido para la fecha de la importacion')
            partner = line_id.importation_id.partner_id
            transit_acc = line_id.product_id.transit_account_id
            journal = self.env['account.journal'].search([('code', '=', 'DIMP')])
            if move:
                move_id = move
            move_line.create({'name': '[' + line_id.product_id.default_code + '] ' + line_id.product_id.name,
                              'partner_id': partner.id, 'account_id': transit_acc.id, 'credit': new_price,
                              'debit': 0.00, 'move_id': move_id.id, 'journal_id': journal.id, 'period_id': period.id})
        return True

    @api.multi
    def create_debit_account_move(self, line_id, move, new_price):
        move_id = ()
        if line_id:
            move_line = self.env['account.move.line']
            partner = line_id.importation_id.partner_id
            inv_acc = line_id.product_id.property_account_expense
            journal = self.env['account.journal'].search([('code', '=', 'DIMP')])
            today = date.today().strftime('%Y-%m-%d')
            period_obj = self.env['account.period']
            period = period_obj.search([('date_start', '<=', today), ('date_stop', '>=', today)], limit=1)
            if not period:
                raise except_orm('Error!', 'No existe un periodo contable definido para la fecha de la importacion')
            if move:
                move_id = move
            move_line.create({'name': '[' + line_id.product_id.default_code + '] ' + line_id.product_id.name,
                              'partner_id': partner.id, 'account_id': inv_acc.id, 'credit': 0.00,
                              'debit': new_price, 'move_id': move_id.id, 'journal_id': journal.id,
                              'period_id': period.id})
        return True

    @api.multi
    def action_prorated(self):
        move = ()
        sum_line_price = 0
        total_expenses = 0
        stock_move = self.env['stock.move']
        move_created = False
        for pick in self.picking_ids:
            if pick.state == 'cancel':
                raise except_orm('Error!', 'El ingreso de esta importacion es cancelada, por favor '
                                           'comuniquese con bodega.')
            if pick.state != 'done':
                raise except_orm('Error!', 'No puede liquidar una importacion que no haya sido ingresada por bodega')
        if self.env.user.company_id.percent == 0.00:
            raise except_orm('Error!', 'Configure el porcentaje del ISD en la compania')
        for line in self.order_lines:
            sum_line_price += line.price_unit * line.product_qty
        total_value = sum_line_price
        for line in self.order_lines:
            if not line.already_costed:
                if len(self.expenses_ids) <= 1:
                    raise except_orm('Error!', 'No puede liquidar una importacion si no hay costos de internacion asociados.')
                for expense in self.expenses_ids:
                    if not expense.already_costed:
                        total_expenses += expense.amount
                        expense.already_costed = True
                total_internment = total_expenses
                if line.product_id.type in ('consu', 'service'):
                    raise except_orm('Error!', 'El siguiente producto no se ha configurado correctamente el tipo de'
                                               ' producto, por favor '
                                               'contactese con bodega para corregir este '
                                               'error, %s ' % '[' + line.product_id.default_code + '] ' +
                                     line.product_id.name)
                if not line.product_id.transit_account_id:
                    raise except_orm('Error !', 'El siguiente producto no tiene configurado'
                                                ' la cuenta de importaciones en transito. %s'
                                     % line.product_id.name)
                if not line.product_id.property_account_expense:
                    raise except_orm('Error !', 'El siguiente producto no tiene configurado'
                                                ' la cuenta de inventario. %s'
                                     % line.product_id.name)
                if not line.already_costed and line.product_id.type == 'product':
                    if not move_created:
                        move = self.lq_account_move_create()
                        move_created = True
                    move_line = stock_move.search([('importation_line_id', '=', line.id)])
                    if line.price_unit < total_value:
                        line_value = line.price_unit * line.product_qty
                        line_percent = (line_value * 100) / total_value
                        internment_line_percent = (line_percent * total_internment) / 100
                        price_line = line.price_unit * line.product_qty
                        total_line = price_line + internment_line_percent
                        new_line_price = total_line / line.product_qty
                        line.already_costed = True
                        if line.product_id.standard_price == 0:
                            line.product_id.standard_price = new_line_price
                            self.create_credit_account_move(line, move, total_line)
                            self.create_debit_account_move(line, move, total_line)
                        else:
                            new_line_price = (line.product_id.standard_price + new_line_price) / 2
                            line.product_id.standard_price = new_line_price
                            self.create_credit_account_move(line, move, total_line)
                            self.create_debit_account_move(line, move, total_line)
                        if move_line:
                            move_line.price_unit = new_line_price
        self.state = 'done'

    # # Cron actualiza los costos de productos
    # @api.multi
    # def cron_action_prorated(self):
    #     purchase_importation = self.env['purchase.importation'].search([('state', '=', 'done')])
    #     nofiles = 0
    #     for rec in purchase_importation:
    #         for line in rec.order_lines:
    #             if line.product_id.type != 'service':
    #                 pack = self.env['stock.pack.operation'].search([('picking_id','=',rec.picking_ids.id),('product_id', '=', line.product_id.id)])
    #                 if pack.lot_id:
    #                     pack.lot_id.write({'amount_cost': line.price_unit,
    #                                        'importation_amount': round(((line.subtotal_importation - (line.price_unit * line.product_qty))/ line.product_qty),2)})
    #                     nofiles += 1
    #     print 'Numero de series afectdas ', nofiles

    @api.multi
    def lq_account_move_create(self):
        move = self.env['account.move']
        period = self.env['account.period']
        journal = self.env['account.journal'].search([('code', '=', 'DIMP')])
        today = date.today().strftime('%Y-%m-%d')
        period_obj = period.search([('date_start', '<=', today), ('date_stop', '>=', today)], limit=1)
        if not period_obj:
            raise except_orm('Error!', 'No existe un periodo contable definido para la fecha de la importacion')
        move_obj = move.create({'ref': self.name, 'journal_id': journal.id, 'date': today,
                                'period_id': period_obj.id})
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
        if order_lines[0].importation_id.picking_ids:
            raise except_orm('Error', 'Ya se encuentra creado un albaran por esta importacion.')
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
        customs_imp = 0
        if len(self.expenses_ids) == 0:
            raise except_orm('Error!', 'Por favor primero asigne la liquidacion aduanera a la importacion.')
        else:
            for record in self.expenses_ids:
                if record.product_id.default_code == 'IMPORT-02':
                    customs_imp += 1
            if customs_imp == 0:
                raise except_orm('Error!', 'Por favor primero asigne la liquidacion aduanera a la importacion.')
        for record in self:
            record.end_customs_date = date.today()
            record.local_date = date.today()
            days = record.recompute_days(record.customs_date, record.end_customs_date)
        self.customs_days = days
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
            record.state = 'transit'
            #
            # @api.multi
            # def send_mymail(self):
            #     mtp = self.env['email.template']
            #     mail = self.env['mail.mail']
            #     for record in self:
            #         tmp = mtp.search([('model_id.model', '=', self._name),
            #  ('name', '=', 'Importation Order - Send by Email')])
            #         mail_id = tmp.send_mail(record.id)
            #         mail_obj = mail.browse(mail_id)
            #         mail_obj.send()
            #     return True

    @api.multi
    def create_stock_picking(self):
        for record in self:
            record.action_picking_create()
            self.picking_created = True


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
    already_costed = fields.Boolean('Linea costeada', default=False)

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
    invoice = fields.Char('Factura')
    already_costed = fields.Boolean('Costo utilizado')

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

    # Asiento para el producto que tenga marcado que es impuesto aduanero

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
        move_obj = move.create({'ref': 'Imp. Aduaneros', 'journal_id': journal_obj.id, 'date': date.today().strftime('%Y-%m-%d'), 'period_id': period_obj.id})
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


class importation_payments(models.Model):
    _name = 'importation.payments'

    partner_id = fields.Many2one('res.partner', 'Proveedor', domain=[('supplier', '=', True)])
    amount = fields.Float('Valor')
    done = fields.Boolean('Realizado')
    importation_id = fields.Many2one('purchase.importation', 'Importacion')
    company_id = fields.Many2one('res.company', string='Compania', related='importation_id.company_id')

    @api.one
    def action_payment(self):
        payment = self.env['account.voucher']
        payment_line = self.env['account.pay.some']
        account_account_obj = self.env['account.account']
        pay_account = account_account_obj.search([('code', '=', '1010402')])
        try:
            pay = payment.create(
                {  # 'partner_id': self.partner_id.id,
                    'benef': self.partner_id.name,
                    'account_id': self.partner_id.property_account_payable.id,
                    'type': 'some_pays',
                    'reference': self.importation_id.name})
            payment_line.create({'account_id': pay_account.id,
                                 'amount': self.amount,
                                 'voucher_id': pay.id})
        except ValueError:
            raise except_orm('Error!', 'Error al generar el egreso, revise las configuraciones')
        self.done = True

        pays_ids = [i.id for i in self.importation_id.some_payment_ids]
        pays_ids.append(pay.id)
        self.importation_id.some_payment_ids = [[6, False, pays_ids]]


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
