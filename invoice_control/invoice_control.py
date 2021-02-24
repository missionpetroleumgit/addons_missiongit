# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution - Ecuador
#    Copyright (C) 2019 MissionPetroleum Daniel Aldaz (<daldaz@mission-petroleum.com>).
#
##############################################################################

from openerp import api, fields, models
from datetime import datetime, timedelta
from openerp.exceptions import except_orm
from openerp.tools.translate import _


class account_invoice(models.Model):
    _inherit = 'account.invoice'

    invoice_validated = fields.Datetime('Validacion Factura')
    invoice_paid = fields.Datetime('Factura Pagada')
    # field date create for invoice control D.A. 23.05.19
    date_invoice_control = fields.Datetime('Fecha pago factura')

    @api.multi
    def action_cancel(self):
        res = super(account_invoice, self).action_cancel()
        sale_order_obj = self.env['sale.order']
        for record in self:
            sale_id = sale_order_obj.search([('name', '=', record.origin)])
            if sale_id:
                for sale in sale_id:
                    record.invoice_validated = ''
                    record.invoice_paid = ''
                    record.date_invoice_control = ''
        return res

    @api.multi
    def invoice_validate(self):
        res = super(account_invoice, self).invoice_validate()
        sale_order_obj = self.env['sale.order']
        for record in self:
            record.invoice_validated = datetime.now()
            sale_id = sale_order_obj.search([('name', '=', record.origin)])
            if sale_id:
                if not sale_id.invoice_valid and sale_id.state == 'progress':
                    sale_id.invoice_valid = sale_id.get_invoice_date()
                if sale_id.invoice_created and sale_id.invoice_valid:
                    sale_id.val_days = sale_id.calculate_date(sale_id.invoice_valid, sale_id.invoice_created)

        return res

account_invoice()


class sale_order(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def action_cancel(self):
        res = super(sale_order, self).action_cancel()
        for record in self:
            for inv in record.invoice_ids:
                if inv.state not in ('draft', 'cancel', 'invalidate'):
                    raise except_orm(
                        _('Cannot cancel this sales order!'),
                        _('First cancel all invoices attached to this sales order.'))
            record.invoice_created = ''
            record.cr_days = ''
        return res

    @api.multi
    def _compute_days(self):
        today = datetime.now()
        days = ''
        for record in self:
            days = self.calculate_date(today, record.invoice_created)
            if record.invoice_created:
                record.invoiced_days_count = days
            if record.state in ('done', 'progress'):
                record.calc_paid_days()

    @api.multi
    def calc_paid_days(self):
        for invoice in self.invoice_ids:
            if invoice.state == 'paid':
                if invoice.date_invoice_control:
                    date = invoice.date_invoice_control
                    t_days = self.calculate_date(date, self.invoice_created)
                    days = self.calculate_date(date, self.invoice_valid)
                    self.invoiced_days_count = t_days
                    self.invoice_paid_date = date
                    self.invoice_paid_days = days

    docs_sent = fields.Datetime('Documentacion Enviada')
    docs_received = fields.Datetime('Documentacion Recibida')
    docs_days = fields.Char('Dias Documentacion Recibida', default=0)
    invoice_created = fields.Datetime('Creacion Factura')
    cr_days = fields.Char('Dias creacion factura', default=0)
    invoice_valid = fields.Datetime('Validacion Factura')
    val_days = fields.Char('Dias validacion factura', default=0)
    invoiced_days_count = fields.Char('Dias a partir Pre-Factura', compute=_compute_days)
    invoice_paid_date = fields.Datetime('Pago Factura', compute=_compute_days)
    invoice_paid_days = fields.Char('Dias pago factura', default=0, compute=_compute_days)
    attach_sale_ids = fields.Many2many(
        comodel_name='ir.attachment',
        relation='attachments_sale_rel',
        column1='sale_id',
        column2='attachment_id',
        string='Archivo Adjunto(s)'
    )

    @api.multi
    def get_invoice_date(self):
        date = ''
        for record in self.invoice_ids:
            if record.state == 'open':
                date = record.invoice_validated
        return date

    @api.multi
    def invoice_control(self, date):
        for r in self:
            if r.docs_sent:
                # if len(r.attach_sale_ids) == 0:
                #    raise except_orm('Error de Usuario !', 'Debe adjuntar los documentos relacionados al bien/servicio'
                #                                            ' entregado')
                if date:
                    r.docs_received = date
                else:
                    r.docs_received = datetime.now()
            if not r.docs_sent:
                if date:
                    r.docs_sent = date
                else:
                    r.docs_sent = datetime.now()
            if r.docs_sent and r.docs_received:
                r.docs_days = self.calculate_date(r.docs_received, r.docs_sent)

    @api.multi
    def calculate_date(self, second_date, first_date):
        days = 0
        if type(second_date) is str:
            second_date = datetime.strptime(second_date, '%Y-%m-%d %H:%M:%S')
        if type(first_date) is str:
            first_date = datetime.strptime(first_date, '%Y-%m-%d %H:%M:%S')
        if first_date and second_date:
            if second_date < first_date:
                return False
            if str(second_date)[:10] == str(first_date)[:10]:
                dias = '1 Día'
                return dias
            else:
                days = second_date - first_date
            if days.days.real == 0:
                dias = str(days.days.real + 1) + ' ' + 'Día'
            elif days.days.real == 1:
                dias = str(days.days.real) + ' ' + 'Día'
            elif days.days.real > 1:
                dias = str(days.days.real) + ' ' + 'Días'
            return dias

sale_order()


class sale_advance_payment_inv(models.TransientModel):
    _inherit = 'sale.advance.payment.inv'

    @api.v7
    def create_invoices(self, cr, uid, ids, context=None):
        res = super(sale_advance_payment_inv, self).create_invoices(cr, uid, ids, context=context)
        sale_ids = context.get('active_ids', [])
        sale_obj = self.pool.get('sale.order')
        for sale_ids in sale_obj.browse(cr, uid, sale_ids, context=context):
            sale_ids.update({'state': 'progress', 'invoice_created': datetime.now()})
            for sale_w in self.browse(cr, uid, ids, context=context):
                if sale_w.advance_payment_method == 'lines' and not sale_ids.docs_sent or \
                                        sale_w.advance_payment_method == 'lines' and not sale_ids.docs_received:
                    raise except_orm('Error !', 'Por favor primero debe registrar en el sistema la fecha de '
                                                'documentacion enviada y recibida, con los botones "Documentos '
                                                'recibidos o enviados", esto sirve para tener un mejor control '
                                                'de las facturas.')
            if not sale_ids.docs_sent:
                raise except_orm('Error !', 'Por favor primero debe registrar en el sistema la fecha de documentacion'
                                            ' enviada, con el boton "Bien/Servicio Entregado", esto sirve para tener un '
                                            'mejor control de las facturas.')
            if not sale_ids.docs_received:
                raise except_orm('Error !', 'Por favor primero debe registrar en el sistema la fecha del servicio '
                                            'entregado, con el boton "Documentos enviados", esto sirve para tener'
                                            ' un mejor control de las facturas.')

            if sale_ids.invoice_created and sale_ids.docs_received:
                sale_ids.cr_days = sale_ids.calculate_date(sale_ids.invoice_created, sale_ids.docs_received)
        return res

sale_advance_payment_inv()


class account_voucher(models.Model):
    _inherit = 'account.voucher'

    @api.v7
    def voucher_move_line_create(self, cr, uid, voucher_id, line_total, move_id, company_currency, current_currency,
                                 context=None):
        res = super(account_voucher, self).voucher_move_line_create(cr, uid, voucher_id, line_total, move_id,
                                                                    company_currency, current_currency,
                                                                    context=None)
        if context is None:
            context = {}
        voucher_obj = self.pool.get('account.voucher')
        invoice_obj = self.pool.get('account.invoice')

        date = self.read(cr, uid, [voucher_id], ['date'], context=context)[0]['date']
        ctx = context.copy()
        ctx.update({'date': date})
        voucher = voucher_obj.browse(cr, uid, voucher_id, context=ctx)
        if voucher.type == 'receipt':
            if voucher.line_dr_ids:
                for line in voucher.line_dr_ids:
                    inv = invoice_obj.search(cr, uid, ([('number_reem', '=', line.invoice), ('type', '=', 'out_invoice')]))
                    if inv:
                        invoice = invoice_obj.browse(cr, uid, inv)
                        if line.reconcile:
                            invoice.date_invoice_control = datetime.now()
            if voucher.line_cr_ids:
                for line in voucher.line_cr_ids:
                    inv = invoice_obj.search(cr, uid, ([('number_reem', '=', line.invoice), ('type', '=', 'out_invoice')]))
                    if inv:
                        invoice = invoice_obj.browse(cr, uid, inv)
                        if line.reconcile:
                            invoice.date_invoice_control = datetime.now()
        return res

account_voucher()


class SaleMakeInvoice(models.TransientModel):
    _inherit = 'sale.make.invoice'

    # date = fields.Datetime('Fecha', required=True)
    # date_docs = fields.Datetime('Fecha Documentos', required=True)
    # date_ok = fields.Boolean('OK', default=False)

    @api.multi
    def make_invoices(self):
        res = super(SaleMakeInvoice, self).make_invoices()
        sale_order = self.env['sale.order']
        for order in sale_order.browse(self._context['active_ids']):
            if not order.docs_sent:
                raise except_orm('Error !', 'No puede facturar ventas que aun no este asignada la fecha '
                                            'de entrega de servicio o bien en todas las ordenes que se desea facturar')
            if not order.docs_received:
                raise except_orm('Error !', 'No puede facturar ventas que aun no este asignada la fecha '
                                            'de entrega de recepción de documentos en todas las ordenes que '
                                            'se desea facturar')
        return res

SaleMakeInvoice()
