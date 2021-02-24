##########################
# -*- coding: utf-8 -*- ##
##########################


from openerp import models, fields, api, _
from openerp.exceptions import except_orm, ValidationError
import openerp.addons.decimal_precision as dp
from openerp.tools.float_utils import float_compare
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
from datetime import datetime
import time


def is_float(s):
    try:
        float(s)
        return True
    except ValueError:
        return False


def convert_couma_to_point(s):
    index = s.index(',')
    if index:
        count = s.count(',')
        if count != 1:
            raise except_orm('Error!!', 'Formato equivocado')
        _str = s.replace(',', '.')
        return _str
    return s


class purchase_quotes(models.Model):
    _name = 'purchase.quotes'
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    # def print_quotes(self, cr, uid, ids, context=None):
    #     if not ids:
    #         raise except_orm('Error!!', 'Formato equivocado')
    #
    #     data = {
    #         'id': ids and ids[0],
    #         'ids': ids,
    #     }
    #
    #     return self.pool['report'].get_action(
    #         cr, uid, [], 'purchase.report_purchaseorder', data=data, context=context
    #     )

    @api.multi
    def button_dummy(self):
        return True

    def print_quotes(self, cr, uid, ids, context=None):
        '''
        This function prints the request for quotation and mark it as sent, so that we can see more easily the next step of the workflow
        '''
        # assert len(ids) == 1, 'This option should only be used for a single id at a time'
        return self.pool['report'].get_action(cr, uid, ids[0], 'purchase.report_purchasequotation', context=context)

    @api.one
    def _amount_all(self):
        cur_obj=self.pool['res.currency']
        val = val1 = 0.0
        cur = self.env.user.company_id.currency_id
        for line in self.quotes_lines:
            if line.discount:
                amount_discount = float(line.discount)/line.product_qty
            else:
                amount_discount = 0.00
            if line.state == 'cancel':
                continue
            val1 += line.price_subtotal
            # print "precio unitario", line.price_unit - (float(line.discount)/line.product_qty)
            print "precio unitario", line.price_unit
            for c in self.pool['account.tax'].compute_all(self._cr, self._uid, line.taxes_id, line.price_unit - amount_discount, line.product_qty, line.product_id, self.partner_id)['taxes']:
                val += c.get('amount', 0.0)
        self.amount_tax = cur_obj.round(self._cr, self._uid, cur, val)
        self.amount_total = self.amount_tax + val1
        self.amount_subtotal = val1

    @api.one
    def _calculate_new(self):
        total = 0.0
        for line in self.quotes_lines:
            if line.percent:
                total += (line.product_qty * line.price_unit) - line.price_subtotal

        self.total_discount = total

    name = fields.Char('Numero', readonly=True)
    partner_id = fields.Many2one('res.partner', 'Proveedor', required=True, domain=[('supplier', '=', True)])
    date_request = fields.Date('Fecha de la cotizacion')
    company_id = fields.Many2one('res.company', 'Compania')
    quotes_lines = fields.One2many('quotes.line', 'quote_id', 'Lineas de cotizacion', delete='cascade')
    purchase_order_id = fields.Many2one('purchase.order', 'Orden de compra')
    # pricelist_id = fields.Many2one('product.pricelist', 'Lista de Precio')
    state = fields.Selection([('draft', 'Solicitud'), ('done', 'Aprobada'), ('cancel', 'Cancelada')], 'Estado')
    amount_tax = fields.Float('Total impuestos', compute=_amount_all)
    amount_total = fields.Float('Total', compute=_amount_all)
    amount_subtotal = fields.Float('Subtotal', compute=_amount_all)
    total_discount = fields.Float('Descuento Total', compute=_calculate_new)
    payment_term_id = fields.Many2one('account.payment.term', string="Termino de Pago")
    time_delivery = fields.Date('Tiempo de Entrega')
    attachment_ids = fields.Many2many(
        comodel_name='ir.attachment',
        relation='attachments_rel',
        column1='account_id',
        column2='attachment_id',
        string='Archivo Adjunto(s)'
    )

    # @api.onchange('partner_id')
    # def onchange_partner_id(self):
    #     self.pricelist_id = self.partner_id.property_product_pricelist.id

    @api.model
    def default_get(self, fields_list):
        res = dict()
        if 'order_id' in self._context and self._context['order_id']:
            if not self.quotes_lines:
                order = self.env['purchase.order'].browse(self._context['order_id'])
                items = list()
                for req in order.request_products:
                    taxes = list()
                    taxes.append([6, False, [tax.id for tax in req.product_id.supplier_taxes_id]])
                    items.append((0, 0, {'name': req.description, 'analytics_id':req.analytics_id.id, 'date_planned': req.date_requested, 'price_unit': 0.00, 'product_id': req.product_id.id,
                                         'product_qty': req.qty, 'product_uom': req.product_uom.id, 'company_id': self.env.user.company_id.id,
                                         'taxes_id': taxes, 'quote_sequence': req.req_sequence}))
                res['quotes_lines'] = items
        elif 'importation_id' in self._context and self._context['importation_id']:
            if not self.quotes_lines:
                order = self.env['importation.order'].browse(self._context['importation_id'])
                items = list()
                for req in order.request_ids:
                    taxes = list()
                    # DA/27.11.2018 Comento lo de importaciones para que no se refleje en las cotizaciones
                    # taxes.append([6, False, [tax.id for tax in req.product_id.supplier_taxes_id]])
                    items.append((0, 0, {'name': req.description, 'analytics_id':req.analytics_id.id, 'date_planned': req.date_requested, 'price_unit': 0.00, 'product_id': req.product_id.id,
                                         'product_qty': req.qty, 'product_uom': req.product_uom.id, 'company_id': self.env.user.company_id.id}))
                res['quotes_lines'] = items
        user = self.env['res.users'].browse(self._uid)
        res['company_id'] = user.company_id.id
        res['state'] = 'draft'
        res['name'] = '/'
        res['date_request'] = time.strftime('%Y-%m-%d')
        return res

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].get('purchase.quotes', context=self._context)
        return super(purchase_quotes, self).create(vals)

    @api.multi
    def action_done(self):
        for record in self:
            #if not record.purchase_order_id.is_procura and not record.importation_id.is_imp_procura:
            for line in record.quotes_lines:
                if line.state in ('draft', 'cancel'):
                    if not line.date_planned:
                        raise except_orm('Error!', 'La fecha programada es requerida en cada linea')
                    line.state = 'done'
            record.state = 'done'
            # Comento lo de requisiciones hasta que se apruebe 06.03.2019 DA
            # for requests in record.purchase_order_id.requisition_order_id.request_line_ids:
            #     if requests.qty > 0:
            #         new_qty = 0
            #         for line in record.quotes_lines:
            #             if line.state in ('draft', 'cancel'):
            #                 if not line.date_planned:
            #                     raise except_orm('Error!', 'La fecha programada es requerida en cada linea')
            #                 if line.product_id.id == requests.product_id.id and line.product_qty <= requests.qty:
            #                     new_qty = requests.qty - line.product_qty
            #                     requests.qty = new_qty
            #                     for req in record.purchase_order_id.request_products:
            #                         if line.product_id.id == req.product_id.id:
            #                             req.qty = new_qty
            #                             if new_qty == 0:
            #                                 req.line_fill = True
            #                     if new_qty == 0:
            #                         requests.line_fill = True
            #                     line.state = 'done'
            # if record.importation_id.is_imp_procura or record.purchase_order_id.is_procura:
            #     for line in record.quotes_lines:
            #         if line.state in ('draft', 'cancel'):
            #             if not line.date_planned:
            #                 raise except_orm('Error!', 'La fecha programada es requerida en cada linea')
            #         line.state = 'done'

    @api.multi
    def action_cancel(self):
        for record in self:
            for line in record.quotes_lines:
                if line.state in ('done', 'draft'):
                    line.state = 'cancel'
                else:
                    raise except_orm('Error!', 'La cotizacion ya se encuentra cancelada')
            record.state = 'cancel'
            # Comento lo de requisiciones hasta que se apruebe 06.03.2019 DA
            # if not record.purchase_order_id.is_procura:
            #     for requests in record.purchase_order_id.requisition_order_id.request_line_ids:
            #         new_qty = 0
            #         for line in record.quotes_lines:
            #             if line.state == 'done':
            #                 if line.product_id.id == requests.product_id.id:
            #                     original_qty = requests.qty + line.product_qty
            #                     requests.qty = original_qty
            #                     for req in record.purchase_order_id.request_products:
            #                         if line.product_id.id == req.product_id.id:
            #                             req.qty = original_qty
            #                             if requests.line_fill:
            #                                 req.line_fill = False
            #                     if requests.line_fill:
            #                         requests.line_fill = False
            #                     line.state = 'cancel'
            #             elif line.state == 'draft':
            #                 line.state = 'cancel'
            # if record.importation_id.is_imp_procura or record.purchase_order_id.is_procura:
            #     for line in record.quotes_lines:
            #         if line.state in ('done', 'draft'):
            #             line.state = 'cancel'
            #         else:
            #             raise except_orm('Error!', 'La cotizacion ya se encuentra cancelada')
            #
            # record.state = 'cancel'

    @api.v7
    def send_mymail(self, cr, uid, ids, context=None):
        '''
        This function opens a window to compose an email, with the edi sale template message loaded by default
        '''
        assert len(ids) == 1, 'This option should only be used for a single id at a time.'
        ir_model_data = self.pool.get('ir.model.data')
        try:
            template_id = ir_model_data.get_object_reference(cr, uid, 'purchase_tiw', 'email_template_purchase_quotes')[1]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data.get_object_reference(cr, uid, 'mail', 'email_compose_message_wizard_form')[
                1]
        except ValueError:
            compose_form_id = False
        ctx = dict()
        ctx.update({
            'default_model': 'purchase.quotes',
            'default_res_id': ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'mark_so_as_sent': True
        })
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }

purchase_quotes()


class quotes_line(models.Model):
    _name = 'quotes.line'

    @api.multi
    def _amount_line(self):
        cur_obj=self.pool['res.currency']
        tax_obj = self.pool['account.tax']
        for line in self:
            taxes = tax_obj.compute_all(self._cr, self._uid, line.taxes_id, line.price_unit, line.product_qty, line.product_id, line.quote_id.partner_id)
            cur = self.env.user.company_id.currency_id
            line.price_subtotal = cur_obj.round(self._cr, self._uid, cur, taxes['total'])
            if line.discount:
                discount, ignore = self.calculate_discount(line.discount, line.price_subtotal)
                line.price_subtotal -= discount

    @api.one
    def _percent_line(self):
        cur_obj=self.pool('res.currency')
        tax_obj = self.pool('account.tax')
        if self.discount:
            taxes = tax_obj.compute_all(self._cr, self._uid, self.taxes_id, self.price_unit, self.product_qty, self.product_id, self.quote_id.partner_id)
            cur = self.quote_id.company_id.currency_id
            price_subtotal = cur_obj.round(self._cr, self._uid, cur, taxes['total'])
            discount, percent = self.calculate_discount(self.discount, price_subtotal)
            self.percent = percent
        else:
            self.percent = 0.00

    quote_id = fields.Many2one('purchase.quotes', 'Cotizacion')
    product_id = fields.Many2one('product.product', 'Producto', domain=[('purchase_ok','=',True)], change_default=True)
    company_id = fields.Many2one('res.company', 'Compania')
    product_qty = fields.Float('Cantidad', digits_compute=dp.get_precision('Product Unit of Measure'), required=True)
    product_uom = fields.Many2one('product.uom', 'Unidad de medida', required=True)
    price_unit = fields.Float('Precio unitario', required=True, digits_compute= dp.get_precision('Product Price'))
    price_subtotal = fields.Float('Subtotal', compute=_amount_line, digits_compute= dp.get_precision('Account'))
    state = fields.Selection([('draft', 'Solicitud'), ('done', 'Aprobada'), ('cancel', 'Cancelada')], 'Estado', default='draft', readonly=True)
    name = fields.Char('Descripcion')
    taxes_id = fields.Many2many('account.tax', 'quotes_order_taxe', 'line_id', 'tax_id', 'Impuestos')
    date_planned = fields.Date('Fecha programada', required=True)
    discount = fields.Char('Descuento', help='El descuento se aplica en % o en el monto relativo al mismo, por ejemplo: \n'
                                             'a)12% disminuiria el 12% del monto \n'
                                             'b)12 disminuiria 12 dolares al monto.')
    percent = fields.Float('Porciento', compute=_percent_line)
    analytics_id = fields.Many2one('account.analytic.plan.instance', string='Distribución Analitica')
    req_value = fields.Integer('Restante', help='Este valor sera el resultado de el valor de la requisicion contra '
                                                'el valor actual registrado en la cotizacion')
    quote_sequence = fields.Char('Secuencia', readonly=True)

    def calculate_discount(self, discount, price_subtotal):
        percent = 0.00
        if ',' in discount:
            discount = convert_couma_to_point(discount)
        if is_float(discount):
            percent = float(discount) *100/price_subtotal if price_subtotal > 0 else 0.00
            return float(discount), percent
        else:
            if '%' in discount:
                index = discount.index('%')
                number = discount[0: index]
                # amount = 0.00
                if not is_float(number):
                    raise except_orm('Error!!', 'El valor no corresponde con el formato')
                amount = (price_subtotal*float(number)/100)
                percent = float(number)
            else:
                raise except_orm('Error!!', 'El valor no corresponde con el formato')
        return amount, percent

    @api.onchange('discount')
    def onchange_discount(self):
        res = {'value': {}}
        if self.discount and self.discount != '0':
            if ',' in self.discount:
                res['warning'] = {'title': 'Error!', 'message': 'Formato equivocado'}
            return res
        return True

    @api.model
    def create(self, vals):
        return super(quotes_line, self).create(vals)

    @api.multi
    def action_cancel(self):
        for record in self:
            if record.state in ('draft', 'cancel'):
                record.state = 'cancel'
            # for requests in record.quote_id.purchase_order_id.requisition_order_id.request_line_ids:
            #     if record.state == 'done':
            #         if record.product_id.id == requests.product_id.id:
            #             original_qty = requests.qty + record.product_qty
            #             requests.qty = original_qty
            #             record.product_qty = original_qty
            #             for req in record.quote_id.purchase_order_id.request_products:
            #                 if record.product_id.id == req.product_id.id:
            #                     req.qty = original_qty
            #                     if requests.line_fill:
            #                         req.line_fill = False
            #             if requests.line_fill:
            #                 requests.line_fill = False
            #             record.state = 'cancel'
            #     elif record.state == 'draft':
            #         record.state = 'cancel'

    @api.v7
    def onchange_product_uom(self, cr, uid, ids, pricelist_id, product_id, qty, uom_id,
                             partner_id, date_order=False, fiscal_position_id=False,
                             name=False, price_unit=False, state='draft', context=None):
        """
        onchange handler of product_uom.
        """
        if context is None:
            context = {}
        if not uom_id:
            return {'value': {'price_unit': price_unit or 0.0, 'name': name or '', 'product_uom' : uom_id or False}}
        context = dict(context, purchase_uom_check=True)
        return self.onchange_product_id(cr, uid, ids, pricelist_id, product_id, qty, uom_id,
                                        partner_id, date_order=date_order, fiscal_position_id=fiscal_position_id,
                                        name=name, price_unit=price_unit, state=state, context=context)

    @api.v7
    def onchange_product_id(self, cr, uid, ids, pricelist_id, product_id, qty, uom_id,
                            partner_id, date_order=False, fiscal_position_id=False,
                            name=False, price_unit=False, state='draft', context=None):
        """
        onchange handler of product_id.
        """
        if context is None:
            context = {}

        res = {'value': {'price_unit': price_unit or 0.0, 'name': name or '', 'product_uom': uom_id or False}}
        if not product_id:
            return res

        product_product = self.pool.get('product.product')
        product_uom = self.pool.get('product.uom')
        res_partner = self.pool.get('res.partner')
        product_pricelist = self.pool.get('product.pricelist')
        account_fiscal_position = self.pool.get('account.fiscal.position')
        account_tax = self.pool.get('account.tax')

        # - check for the presence of partner_id and pricelist_id
        #if not partner_id:
        #    raise osv.except_osv(_('No Partner!'), _('Select a partner in purchase order to choose a product.'))
        #if not pricelist_id:
        #    raise osv.except_osv(_('No Pricelist !'), _('Select a price list in the purchase order form before choosing a product.'))

        # - determine name and notes based on product in partner lang.
        context_partner = context.copy()
        if partner_id:
            lang = res_partner.browse(cr, uid, partner_id).lang
            context_partner.update( {'lang': lang, 'partner_id': partner_id} )
        product = product_product.browse(cr, uid, product_id, context=context_partner)
        #call name_get() with partner in the context to eventually match name and description in the seller_ids field
        if not name or not uom_id:
            # The 'or not uom_id' part of the above condition can be removed in master. See commit message of the rev. introducing this line.
            dummy, name = product_product.name_get(cr, uid, product_id, context=context_partner)[0]
            if product.description_purchase:
                name += '\n' + product.description_purchase
            res['value'].update({'name': name})

        # - set a domain on product_uom
        res['domain'] = {'product_uom': [('category_id','=',product.uom_id.category_id.id)]}

        # - check that uom and product uom belong to the same category
        product_uom_po_id = product.uom_po_id.id
        if not uom_id:
            uom_id = product_uom_po_id

        if product.uom_id.category_id.id != product_uom.browse(cr, uid, uom_id, context=context).category_id.id:
            if context.get('purchase_uom_check') and self._check_product_uom_group(cr, uid, context=context):
                res['warning'] = {'title': _('Warning!'), 'message': _('Selected Unit of Measure does not belong to the same category as the product Unit of Measure.')}
            uom_id = product_uom_po_id

        res['value'].update({'product_uom': uom_id})

        # - determine product_qty and date_planned based on seller info
        if not date_order:
            date_order = fields.datetime.now().strftime('%Y-%m-%d')

        supplierinfo = False
        precision = self.pool.get('decimal.precision').precision_get(cr, uid, 'Product Unit of Measure')
        for supplier in product.seller_ids:
            if partner_id and (supplier.name.id == partner_id):
                supplierinfo = supplier
                if supplierinfo.product_uom.id != uom_id:
                    res['warning'] = {'title': _('Warning!'), 'message': _('The selected supplier only sells this product by %s') % supplierinfo.product_uom.name }
                min_qty = product_uom._compute_qty(cr, uid, supplierinfo.product_uom.id, supplierinfo.min_qty, to_uom_id=uom_id)
                if float_compare(min_qty , qty, precision_digits=precision) == 1: # If the supplier quantity is greater than entered from user, set minimal.
                    if qty:
                        res['warning'] = {'title': _('Warning!'), 'message': _('The selected supplier has a minimal quantity set to %s %s, you should not purchase less.') % (supplierinfo.min_qty, supplierinfo.product_uom.name)}
                    qty = min_qty
        # dt = self._get_date_planned(cr, uid, supplierinfo, date_order, context=context).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        qty = qty or 1.0
        # res['value'].update({'date_planned': date_planned or dt})
        if qty:
            res['value'].update({'product_qty': qty})

        price = 0.00
        if price_unit is False or price_unit is None:
            # - determine price_unit and taxes_id
            if pricelist_id:
                date_order_str = datetime.strptime(date_order, '%Y-%m-%d').strftime('%Y-%m-%d')
                price = product_pricelist.price_get(cr, uid, [pricelist_id],
                                                    product.id, qty or 1.0, partner_id or False, {'uom': uom_id, 'date': date_order_str})[pricelist_id]
            else:
                price = 0.00

        taxes = account_tax.browse(cr, uid, map(lambda x: x.id, product.supplier_taxes_id))
        fpos = fiscal_position_id and account_fiscal_position.browse(cr, uid, fiscal_position_id, context=context) or False
        taxes_ids = account_fiscal_position.map_tax(cr, uid, fpos, taxes)
        res['value'].update({'price_unit': price, 'taxes_id': taxes_ids})

        return res

quotes_line()


class purchase_order(models.Model):
    _inherit = 'purchase.order'

    @api.model
    def _get_user_employee(self):
        return self.env.user.partner_id.employee_id.id

    @api.model
    def control_default(self):
        control = self.env['control.sheet.report'].search([('model_id.model', '=', self._name)])
        return [(0, 0, {'control_id': i.id, 'report':i.report, 'code':i.code,'review':i.review,'issue':i.issue}) for i in control]

    quotes_ids = fields.One2many('purchase.quotes', 'purchase_order_id', 'Cotizaciones', ondelete='cascade')
    multi = fields.Boolean('multiple?')
    request_products = fields.One2many('request.product', 'order_id', 'Solicitud de Productos', ondelete='cascade')
    req_user_id = fields.Many2one('hr.employee', 'Solicitado por', default=_get_user_employee)
    app_user_id = fields.Many2one('res.users', 'Aprueba')
    type_purchase = fields.Selection([('product', 'Producto(s)'), ('service', 'Servicio(s)'), ('consu', 'Consumible(s)')
                                      ], 'Tipos de Productos')
    obs_ids = fields.One2many('purchase.observations', 'obs_id', 'Observacion')
    # JJM agrego booleano para saber si ya pasó por aprobacion presupuestaria
    # y pueden hacer control previo
    is_approve_quotes = fields.Boolean('Cotizacion aprobada')
    employee_id = fields.Many2one('hr.employee', string="Responsable", domain=[('business_unit_id.codigo', '=', 'COMPRAS')])
    tracing_id = fields.One2many('purchase.order.tracing', 'purchase_order_id', string='Seguimiento')
    control_sheet_ids = fields.One2many('purchase.control.sheet', 'order_purchase_id', string="Gestion de Calidad", default=control_default)
    place_delivery = fields.Char(string='Lugar de Entrega')
    state = fields.Selection([('draft', 'Requisicion'),
                              ('sent', 'Revision'),
                              # ('order_cotrol','Orden de Compra'),
                              ('bid', 'Orden de Compra'),
                              ('confirmed', 'Esperando Aprovacion'),
                              ('approved', 'Compra Confirmada'),
                              ('except_picking', 'Exception Albaran'),
                              ('except_invoice', 'Exception Albaran'),
                              ('done', 'Realizado'),
                              ('cancel', 'Cancelled')
                              ], 'Estado')
    is_procura = fields.Boolean('Es procura?', default=False)
    cancel_controller = fields.Boolean("Cancelado por controller")

    @api.multi
    def controller_order(self):
        for record in self:
            record.number_req = record.name
            if record.type_purchase in ('product', 'consu'):
                record.name = self.env['ir.sequence'].get('purchase.order.product') or '/'
            elif record.type_purchase == 'service':
                record.name = self.env['ir.sequence'].get('purchase.order.service') or '/'
            record.write({'state': 'bid', 'state_manager': 'except'})
            # for requisition in record.requisition_order_id:
            #     requisition.purchase_order_ids.append(record.id)

    @api.multi
    def action_confirm(self):
        res = super(purchase_order, self).wkf_confirm_order()
        return res

    @api.multi
    def check_approve_quotes(self):
        for record in self:
            for quotes in record.quotes_ids:
                if not quotes.attachment_ids:
                    raise ValidationError('Debe agregar archivo adjunto de cotizacion en el proveedor')
            # verifico si tiene almenos una cotizacion aprobada
            if not any([q.state == 'done' for q in record.quotes_ids]):
                raise ValidationError('El registro no tiene ninguna cotizacion aprobada')
            record.is_approve_quotes = True
            record.control = False
            val = {

                'tracing_id': [(0, 0, {
                    'purchase_order_id': self.id,
                    'user_id': self.env.user.id,
                    'date_tracing': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'state': 'bid'
                })]
            }
            record.write(val)

        return True

    @api.onchange('req_user_id')
    def onchange_req_user_id(self):
        self.app_user_id = self.req_user_id.parent_id.user_id.id

    @api.onchange('type_purchase')
    def onchange_type_purchase(self):
        if self.type_purchase in ('consu', 'service'):
            self.invoice_method = 'manual'
        elif self.type_purchase == 'product':
            self.invoice_method = 'picking'

    def _get_approbe_qty(self, quotes):
        app_cont = 0
        for quote in quotes:
            if quote.state == 'done':
                app_cont += 1
        return app_cont

    def create_lines(self, purchase_order_id, line):
        taxes = list()
        taxes.append([6, False, [tax.id for tax in line.taxes_id]])
        self.env['purchase.order.line'].create({'order_id': purchase_order_id, 'name': line.name,
                                                'product_qty': line.product_qty, 'date_planned': line.date_planned,
                                                'product_id': line.product_id.id, 'taxes_id': taxes,
                                                'price_unit': line.price_unit, 'percent': line.percent,
                                                'discount': line.discount, 'product_uom': line.product_id.uom_id.id,
                                                'analytics_id': line.analytics_id.id, 'line_sequence': line.quote_sequence})
        self.minimum_planned_date = line.quote_id.time_delivery
        self.payment_term_id = line.quote_id.payment_term_id.id

    def create_simple_order(self, quotes):
        for quot in quotes:
            if quot.state in ('draft', 'cancel'):
                continue

            for line in quot.quotes_lines:
                if line.state in ('draft', 'cancel'):
                    continue
                if line.price_subtotal < 0.00:
                    raise except_orm('Error!', 'Una linea de la cotizacion %s esta aprobada y su valor es menor o igual a 0.00' % quot.name)
                self.create_lines(quot.purchase_order_id.id, line)

            return quot

    def create_multi_order(self, quote, quotes, procura, req, responsable, app_user_id, dest):
        objs = list()
        for q in quotes:
            if q.id != quote.id:
                pick_type = self.env['stock.picking.type'].search([('code', '=', 'incoming')])
                if not pick_type:
                    raise except_orm('Error!', 'No hay definido un tipo de operacion de entrada')
                purchase = self.create({'origin': quote.purchase_order_id.name, 'partner_id': q.partner_id.id,
                                        'date_order': q.date_request, 'picking_type_id': pick_type.id,
                                        'location_id': pick_type.default_location_dest_id.id,
                                        'req_user_id': quote.purchase_order_id.req_user_id.id, 'multi': True,
                                        'invoice_method': self.invoice_method, 'type_purchase': self.type_purchase,
                                        'minimum_planned_date': quote.time_delivery, 'employee_id': responsable,
                                        'payment_term_id': quote.payment_term_id.id, 'is_procura': procura,
                                        # 'requisition_order_id': quote.purchase_order_id.requisition_order_id.id,
                                        'sale_order_id': quote.purchase_order_id.sale_order_id.id,
                                        'customer_id': quote.purchase_order_id.customer_id.id,
                                        'not_apply': quote.purchase_order_id.not_apply, 'app_user_id': app_user_id,
                                        'destination': dest
                                        })

                q.write({'purchase_order_id': purchase.id})
                purchase.wkf_send_rfq()
                purchase.signal_workflow('bid_received')
                purchase.controller_order()
                purchase.manager_approved()
                purchase.wkf_bid_received()
                purchase.signal_workflow('purchase_confirm')
                purchase.number_req = req

        return True

    @api.multi
    def wkf_confirm_order(self):
        purchase = []
        if self.quotes_ids:
            for obj in self.quotes_ids:
                if obj.state == 'done':
                    purchase.append(obj.id)
        cot = self.env['purchase.quotes'].search([('id', 'in', purchase)])
        for record in self:
            procura = record.is_procura
            dest = record.destination
            req = record.number_req
            responsable = record.employee_id.id
            app_user_id = record.app_user_id.id
            quot = self.create_simple_order(cot)
            if self._get_approbe_qty(cot) > 1:
                self.create_multi_order(quot, cot, procura, req, responsable, app_user_id, dest)
            if not record.order_line:
                raise except_orm('Error!', 'La orden no tiene lineas de compras, posiblemente debido a que no se ha aprobado ninguna de las cotizaciones')
            if quot:
                record.partner_id = quot.partner_id.id
            import_lines = []
            if self.destination == 'importation':
                for quotes in record.quotes_ids:
                    if quotes.state == 'done':
                        for po_line in record.order_line:
                            if po_line.state == 'cancel':
                                continue
                            line_vals = {
                                'name': po_line.name,
                                'product_qty': po_line.product_qty,
                                'product_id': po_line.product_id.id,
                                'product_uom': po_line.product_uom.id,
                                'price_unit': po_line.price_unit,
                                'imported': False,
                                'account_analytic_id': po_line.account_analytic_id.id,
                                'date_planned': po_line.date_planned,
                                'taxes_id': [(6, 0, [t.id for t in po_line.taxes_id])],
                            }
                            import_lines.append((0, 0, line_vals))
                        import_vals = {
                            'name': record.name,
                            'employee_id': record.req_user_id.id,
                            'user_id': record.app_user_id.id,
                            'date_order': record.date_order,
                            'partner_id': record.partner_id.id,
                            'company_id': record.company_id.id,
                            'order_lines': import_lines,
                            'state': 'done',
                            'comment': record.notes,
                        }
                        importation = self.env['importation.order'].create(import_vals)
                        record.order_line.action_confirm()
                        record.write({'state': 'done', 'validator': self.env.uid})
            if record.is_procura:
                record.update({'name': self.env['ir.sequence'].get('procura.order') or '/', 'number_req': record.name})
        res = super(purchase_order, self).wkf_confirm_order()
        return res

    @api.multi
    def wkf_send_rfq(self):
        res = super(purchase_order, self).wkf_send_rfq()
        seq = 0
        for line in self.request_products:
            seq += 1
            line.write({'req_sequence': seq})
        for record in self:
            if self.state == 'draft':
                if self.cancel_controller:
                    record.signal_workflow('send_rfq')
                    if not record.control:
                        val = {

                            'tracing_id': [(0, 0, {
                                'purchase_order_id': self.id,
                                'user_id': self.env.user.id,
                                'date_tracing': time.strftime('%Y-%m-%d %H:%M:%S'),
                                'state': 'approved'
                            })]
                        }
                        record.write(val)
                elif self._uid != record.app_user_id.id and not record.multi:
                    raise except_orm('Error!', 'Usted no esta autorizado a aprobar la requisicion %s' % record.name)
                record.signal_workflow('send_rfq')
                if not record.control:
                    val = {

                        'tracing_id': [(0, 0, {
                            'purchase_order_id': self.id,
                            'user_id': self.env.user.id,
                            'date_tracing': time.strftime('%Y-%m-%d %H:%M:%S'),
                            'state': 'approved'
                        })]
                    }
                    record.write(val)
            else:

                return res
        return True

    @api.multi
    def wkf_bid_received(self):

        val = {

            'tracing_id': [(0, 0, {
                'purchase_order_id': self.id,
                'user_id': self.env.user.id,
                'date_tracing': time.strftime('%Y-%m-%d %H:%M:%S'),
                'state': 'approved_finc'
            })]
        }
        self.write(val)
        return super(purchase_order, self).wkf_bid_received()

    @api.multi
    def send_mymail(self, name):
        mtp = self.env['email.template']
        mail = self.env['mail.mail']
        for record in self:
            tmp = mtp.search([('model_id.model', '=', self._name), ('name', '=', name)])
            mail_id = tmp.send_mail(record.id)
            mail_obj = mail.browse(mail_id)
            mail_obj.send()
        return True

    @api.model
    def create(self, vals):
        if not self._context.get('is_procura'):
            # Comento requicisiones temporalmente DA
            # requisition = self.env['requisition.purchase']
            # requisition_id = requisition.search([('id', '=', vals['requisition_order_id'])])
            # if requisition_id:
            #     name = requisition_id.name
            #     vals.update({'name': name, 'state': 'sent'})
            # else:
            if vals['type_purchase'] in ('product', 'consu'):
                vals['name'] = self.env['ir.sequence'].get('purc.order.req.prod') or '/'
            elif vals['type_purchase'] == 'service':
                vals['name'] = self.env['ir.sequence'].get('pur.order.req.serv') or '/'
            else:
                vals['name'] = '/'
        else:
            vals['name'] = self.env['ir.sequence'].get('procura.requisition.order') or '/'
        obj = super(purchase_order, self).create(vals)

        # obj.write(vals)
        # obj.send_mymail('Aviso de Aprobacion')
        val = {

            'tracing_id': [(0, 0, {
                'purchase_order_id': self.id,
                'user_id': self.env.user.id,
                'date_tracing': time.strftime('%Y-%m-%d %H:%M:%S'),
                'state': 'draft'
            })]
        }
        obj.write(val)

        return obj

    @api.multi
    def tracing_order(self, vals):
        if self:
            val = {

                'tracing_id': [(0, 0, {
                    'purchase_order_id': self.id,
                    'user_id': self.env.user.id,
                    'date_tracing': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'state': self.state
                })]
            }
        self.write(val)

    @api.multi
    def action_cancel(self):
        res = super(purchase_order, self).action_cancel()
        val = {

            'tracing_id': [(0, 0, {
                'purchase_order_id': self.id,
                'user_id': self.env.user.id,
                'date_tracing': time.strftime('%Y-%m-%d %H:%M:%S'),
                'state': 'cancel'
            })]
        }
        self.write(val)

    @api.multi
    def action_cancel_draft(self):
        res = super(purchase_order, self).action_cancel_draft()
        val = {

            'tracing_id': [(0, 0, {
                'purchase_order_id': self.id,
                'user_id': self.env.user.id,
                'date_tracing': time.strftime('%Y-%m-%d %H:%M:%S'),
                'state': 'borrador'
            })]
        }
        self.write(val)


purchase_order()


class request_product(models.Model):
    _name = 'request.product'

    product_id = fields.Many2one('product.product', 'Producto', required=True)
    qty = fields.Float('Cantidad', required=True)
    product_uom = fields.Many2one('product.uom', 'Unidad de Medida', related='product_id.uom_id', readonly=True)
    qty_available = fields.Float('Cantidad disponible', related='product_id.qty_available', readonly=True)
    date_requested = fields.Date('Fecha Planificada', required=True)
    order_id = fields.Many2one('purchase.order', 'Orden')
    importation_id = fields.Many2one('purchase.importation', 'Importacion')
    description = fields.Char('Detalle', required=True)
    virtual_available = fields.Float('Cantidad Virtual', related='product_id.virtual_available', readonly=True)
    analytics_id = fields.Many2one('account.analytic.plan.instance', string='Distribución Analitica', domain=[('journal_id.type', '=', 'purchase')])
    line_fill = fields.Boolean('ID Ya ocupado')
    req_sequence = fields.Char('Secuencia', readonly=True)
    solicited_qty = fields.Float('Cantidad solicitada')

    @api.onchange('product_id')
    def onchange_product_id(self):
        res = {}
        self.description = self.product_id.name
        domain = [('purchase_ok', '=', True)]
        if self.order_id:
            if self.order_id.type_purchase:
                if self.order_id.type_purchase in ('product', 'service', 'consu'):
                    domain.append(('type', '=', self.order_id.type_purchase))
        res['domain'] = {'product_id': domain}
        return res

request_product()


class purchase_observations(models.Model):
    _name = 'purchase.observations'

    #@api.model
    #def _get_user(self):
    #   return self.env.user.id

    user_obs_id = fields.Many2one('res.users', 'Nombre', readonly=True)
    obs_id = fields.Many2one('purchase.order')
    comment = fields.Char('Observacion')


purchase_observations()


class purchase_order_tracing(models.Model):

    _name = 'purchase.order.tracing'

    purchase_order_id = fields.Many2one('purchase.order')
    user_id = fields.Many2one('res.users', string='Usuario')
    date_tracing = fields.Datetime('Fecha')
    state = fields.Selection([('draft', 'Creación de Requisicion'),
                              ('approved', 'Aprobación Jefe Inmediato'),
                              ('bid', 'Gestión Area de Compra'),
                              ('control', 'Revisión Controller'),
                              ('approved_finc', 'Aprobación Financiera'),
                              ('approved_ger','Aprobación Gerencia General'),
                              ('approved_gert', 'Aprobación Gerencia Tecnica'),
                              ('confirmation', 'Confirmación Orden de Compra'),
                              ('purchase','Orden Regresada a Gestión Area de Compra '),
                              ('cancel','Orden Cancelada'),
                              ('borrador','Orden Cambiado a Borrador')
                              ], 'Estado')
    # requisition_id = fields.Many2one('requisition.purchase')

purchase_order_tracing()

class purchase_control_sheet(models.Model):

    _name = 'purchase.control.sheet'

    order_purchase_id = fields.Many2one('purchase.order', string="Orden de Compra")
    control_id = fields.Many2one('control.sheet.report', string="Control de Hoja")
    report = fields.Char(relation='control_id.report',string="Nombre del Reporte")
    code = fields.Char(relation='control_id.code',string="Codigo")
    review = fields.Char(relation='control_id.review',string="Revision")
    issue = fields.Date(relation='control_id.issue',string="Emision")


purchase_control_sheet()


