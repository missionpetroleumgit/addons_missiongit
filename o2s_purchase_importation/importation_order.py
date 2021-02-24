from openerp import models, fields, api
from openerp.exceptions import except_orm, Warning
import openerp.addons.decimal_precision as dp
from openerp.tools.float_utils import float_compare
import dateutil.parser
import datetime
import time
from time import strftime

###################################################################
#################### Orden de importacion #########################
###################################################################


class importation_order(models.Model):
    _name = 'importation.order'

    @api.one
    def _amount_total(self):
        total = 0.00
        for line in self.order_lines:
            total += line.subtotal_importation
        self.amount_total = total

    @api.multi
    def approve_imp_procura(self):
        for record in self:
            record.state = 'execute'

    STATE_SELECTION = [
        ('draft', 'Borrador'),
        ('sent', 'RFQ'),
        ('bid', 'Controller'),
        # ('confirmed', 'Presupuestada'),
        # ('approved', 'Aprobacion Gerencia'),
        ('execute', 'G. General'),
        ('done', 'Orden Confirmada'),
        ('cancel', 'Cancelled')
    ]

    IMPORTATION_STATE = [
        ('new', 'No Generado aun'),
        ('confirm', 'Generada'),
    ]

    # @api.model
    # def create(self, vals):
    #     if not self._context.get('is_imp_procura'):
    #         vals['name'] = self.env['ir.sequence'].get('importation.requisition', context=self._context)
    #     else:
    #         vals['name'] = self.env['ir.sequence'].get('importation.requisition.procura', context=self._context)
    #     return super(importation_order, self).create(vals)

    @api.model
    def _get_default_currency(self):
        return self.env.user.company_id.currency_id.id

    @api.model
    def _default_company(self):
        return self.env.user.company_id.id

    @api.model
    def _get_user_employee(self):
        return self.env.user.partner_id.employee_id.id

    @api.one
    def _importationState(self):
        state = ''
        if self.state == 'done':
            order_lines = self.order_lines[0]
            if len(order_lines):
                already_imported = order_lines.imported
                if already_imported:
                    state = 'Importacion Generada'
                if not already_imported:
                    state = 'Importacion No Generada'
            self.importation_state = state

    name = fields.Char('Referencia')
    employee_id = fields.Many2one('hr.employee', 'Solicitado por?', default=_get_user_employee)
    user_id = fields.Many2one('res.users', 'Aprueba')
    date_order = fields.Date('Fecha del pedido')
    partner_id = fields.Many2one('res.partner', 'Proveedor', domain=[('supplier', '=', True)])
    company_id = fields.Many2one('res.company', 'Company', default=_default_company)
    order_lines = fields.One2many('importation.line', 'importation_id', 'Lineas de Importacion')
    request_ids = fields.One2many('request.product', 'importation_id','Productos solicitados', ondelete='cascade')
    quotes = fields.One2many('purchase.quotes', 'importation_id', 'Cotizaciones', ondelete='cascade')
    state = fields.Selection(STATE_SELECTION, 'Estado', default='draft')
    amount_total = fields.Float('Total', compute=_amount_total)
    comment = fields.Text('Info. Adicional')
    currency_id = fields.Many2one('res.currency', 'Currency', required=True, default=_get_default_currency)
    with_copy = fields.Char('CC', size=64)
    attn = fields.Char('ATTN', size=64)
    register_id = fields.Many2one('hr.employee', 'FROM')
    importation_state = fields.Char('Estado Imp.', compute=_importationState, size=32)
    approve_date = fields.Datetime('Fecha de Aprobacion')
    control_approve = fields.Boolean('Aprobacion Controller')
    control_comment = fields.Text('Comentario')
    imp_sent = fields.Boolean('Imp. Enviado')
    is_imp_procura = fields.Boolean('Es importacion de procura')
    imp_origin = fields.Char('Origen Importacion')
    shipment_terms = fields.Char('Shipment terms')
    payment_terms_id = fields.Many2one('account.payment.term', 'Terminos de pago')
    imp_delivery_date = fields.Date('Tiempo de entrega')
    analytics_id = fields.Many2one('account.analytic.plan.instance', 'Distribucion Analitica')
    importation_req_number = fields.Char('No. Requisicion', readonly=True)

    @api.multi
    def rqimportation_sent(self):
        if len(self.request_ids) == 0:
            raise except_orm('Error!', 'No existen lineas de pedido')
        if self.is_imp_procura:
            if len(self.quotes) == 0:
                raise except_orm('Error!', 'Debe ingresar la cotizacion correspondiente')
            validate = 0
            for quotes in self.quotes:
                if not quotes.attachment_ids and quotes.state != 'cancel':
                    raise except_orm('Error!', 'Por favor adjunte el/los documentos necesarios al documento %s' % quotes.name)
                if quotes.state == 'done':
                    validate += 1
            if validate < 1:
                raise except_orm('Error!',
                                 'Por favor, debe aprobar una o mas cotizaciones para proceder con la compra')

        return self.write({'imp_sent': 'True'})

    @api.onchange('employee_id')
    def onchange_employee_id(self):
        self.user_id = self.employee_id.parent_id.user_id.id

    @api.multi
    def imp_received(self):
        for record in self:
            if self._uid != record.user_id.id:# and not record.multi:
                raise except_orm('Error!', 'Usted no esta autorizado a aprobar la requisicion')
            record.state = 'sent'
        return True

    @api.multi
    def imp_manager(self):
        for rec in self:
            if rec.state == 'approved':
                date_app = rec.approve_date
                date_app = time.strftime("%Y-%m-%d %H:%M:%S")
                dateutil.parser.parse(date_app).date()
                date1 = datetime.datetime.strptime(date_app, '%Y-%m-%d %H:%M:%S')
                datenow = date1.date()
                rec.approve_date = date_app
                rec.state = 'execute'

    @api.multi
    def imp_bid(self):
        for rec in self:
            valida = 0
            if not rec.quotes:
                raise except_orm('Error!', 'Por favor al menos cree una o varias cotizaciones')
            for quotes in rec.quotes:
                if quotes.state == 'done':
                    if len(quotes.attachment_ids) == 0:
                        raise except_orm('Error!', 'Por favor debe adjuntar los documentos necesarios')
                    valida += 1
                if valida == 0:
                    raise except_orm('Alerta !!', 'Se debe definir las cotizaciones y aprobar al menos una !')
            if valida >= 1:
                rec.state = 'bid'

    # @api.multi
    # def imp_presp(self):
    #     valida = 0
    #     for rec in self:
    #         for quote in rec.quotes:
    #             if quote.state == 'done':
    #                 valida = 1
    #         if valida == 1:
    #             if rec.control_approve:
    #                 rec.state = 'confirmed'
    #             else:
    #                 raise except_orm('Alerta !!', 'Primero se debe revisar las cotizaciones y tener la aprobacion del Comite.')

    @api.multi
    def imp_approve(self):
        for rec in self:
            rec.state = 'done'

    @api.multi
    def imp_cancel(self):
        for rec in self:
            rec.state = 'cancel'

    def create_lines(self, importation_id, line):
        taxes = list()
        taxes.append([6, False, [tax.id for tax in line.taxes_id]])
        self.env['importation.line'].create({'importation_id': importation_id, 'name': line.name,
                                             'product_qty': line.product_qty, 'date_planned': line.date_planned,
                                             'product_id': line.product_id.id, 'taxes_id': taxes, 'product_uom': line.product_uom.id,
                                             'price_unit': line.price_unit, 'subtotal_importation': line.price_unit*line.product_qty,
                                             'analytics_id': line.analytics_id.id})
        self.payment_terms_id = line.quote_id.payment_term_id or ''
        self.imp_delivery_date = line.quote_id.time_delivery or ''

    def create_simple_order(self, quotes):
        for quot in quotes:
            if quot.state in ('draft', 'cancel'):
                continue

            for line in quot.quotes_lines:
                if line.state in ('draft', 'cancel'):
                    continue
                if line.price_subtotal < 0.00:
                    raise except_orm('Error!', 'Una linea de la cotizacion %s esta aprobada y su valor es menor o igual a 0.00' % quot.name)
                self.create_lines(quot.importation_id.id, line)

            return quot

    def create_multi_order(self, quote, quotes):
        for q in quotes:
            if q.id != quote.id:
                pick_type = self.env['stock.picking.type'].search([('code', '=', 'incoming')])
                if not pick_type:
                    raise except_orm('Error!', 'No hay definido un tipo de operacion de entrada')
                importation = self.create({'partner_id': q.partner_id.id, 'date_order': q.date_request,
                                           'location_id': pick_type.default_location_dest_id.id,
                                           'user_id': quote.importation_id.user_id.id,
                                           'state':'done',
                                           'name':self.env['ir.sequence'].get('importation.order', context=self._context)
                                           })
                for line in q.quotes_lines:
                    if line.state in ('draft', 'cancel'):
                        continue
                    if line.price_subtotal < 0.00:
                        raise except_orm('Error!',
                                         'Una linea de la cotizacion %s esta aprobada y su valor es menor o igual a 0.00' % line.name)
                    importation.create_lines(importation.id, line)
                q.write({'importation_id': importation.id})

                #importation.manager_approved()
                #Falta transitar por los estados
        return True

    def _get_approbe_qty(self, quotes):
        app_cont = 0
        for quote in quotes:
            if quote.state == 'done':
                app_cont += 1
        return app_cont

    @api.multi
    def purchase_confirm(self):
        for record in self:
            if not record.control_approve and not record.is_imp_procura:
                raise except_orm('Alerta !!', 'Primero se debe revisar las cotizaciones y tener la aprobacion del Comite.')
            val = {

                'tracing_id': [(0, 0, {
                    'purchase_order_id': record.id,
                    'user_id': record.env.user.id,
                    'date_tracing': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'state': 'done'
                })]
            }
            record.write(val)
            quot = self.create_simple_order(record.quotes)
            if self._get_approbe_qty(record.quotes) > 1:
                self.create_multi_order(quot, record.quotes)
            if not record.order_lines:
                raise except_orm('Error!', 'La orden no tiene lineas de compras, posiblemente debido a que no se ha aprobado ninguna de las cotizaciones')
            record.partner_id = quot.partner_id.id
            # record.send_mymail()

            record.importation_req_number = record.name
            if record.is_imp_procura:
                record.state = 'done'
                record.name = self.env['ir.sequence'].get('importation.order.procura', context=self._context) or '/'
            else:
                record.state = 'execute'
                record.name = self.env['ir.sequence'].get('importation.order', context=self._context)

    @api.multi
    def send_mymail(self):
        mtp = self.env['email.template']
        mail = self.env['mail.mail']
        for record in self:
            tmp = mtp.search([('model_id.model', '=', self._name), ('name', '=', 'Importation Order - Send by Email')])
            mail_id = tmp.send_mail(record.id)
            mail_obj = mail.browse(mail_id)
            mail_obj.send()
        return True


class importation_line(models.Model):
    _name = 'importation.line'

    @api.one
    def amount_subtotal(self):
        self.subtotal_importation = self.price_unit * self.product_qty

    importation_id = fields.Many2one('importation.order', 'Orden de Importacion')
    subtotal_importation = fields.Float('Subtotal', compute=amount_subtotal)
    name = fields.Text('Description', required=True)
    product_qty = fields.Float('Quantity', digits_compute=dp.get_precision('Product Unit of Measure'), required=True)
    date_planned = fields.Date('Scheduled Date', required=True, select=True)
    taxes_id = fields.Many2many('account.tax', 'importation_order_taxe2', 'imp_id', 'tax_id', 'Taxes')
    product_uom = fields.Many2one('product.uom', 'Product Unit of Measure', required=True)
    product_id = fields.Many2one('product.product', 'Product', domain=[('purchase_ok','=',True)], change_default=True)
    price_unit = fields.Float('Unit Price', required=True, digits_compute= dp.get_precision('Product Price'))
    account_analytic_id = fields.Many2one('account.analytic.account', 'Analytic Account',)
    company_id = fields.Many2one('res.company',string='Company', related='importation_id.company_id', store=True, readonly=True)
    number = fields.Char('No. parte')
    imported = fields.Boolean('Importada')
    analytics_id = fields.Many2one('account.analytic.plan.instance', 'Distribucion Analitica')
    factured = fields.Boolean('Linea facturada')

    @api.onchange('product_id')
    def onchange_product_id(self):
        self.name = self.product_id.name
        self.product_uom = self.product_id.uom_id


class serial_product_desc(models.Model):
    _name = 'serial.product.desc'

    part_number = fields.Char('No.Parte', size=32, required="1")
    description = fields.Char('Descripcion', size=200, required="1")
    name = fields.Char('Nombre', size=200)

    @api.onchange('part_number', 'description')
    def name_onchange(self):
        if self.part_number:
            self.name = '[' + str(self.part_number) + ']' + ' ' + str(self.description)


