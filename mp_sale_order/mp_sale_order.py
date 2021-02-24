##########################
# -*- coding: utf-8 -*- ##
##########################

from openerp import models, fields, api
from openerp.exceptions import except_orm
from datetime import datetime, timedelta


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.onchange('days_to_close')
    def onchange_control(self):
        days = self.days_to_close
        if days > 30:
            print "pass", self.pass_order
            raise except_orm('Error!', 'Los dias de expiracion de una cotizacion no pueden superar los 30 dias.')
        elif 30 > days > 1:
            self.pass_order = True

    @api.multi
    def get_quotation_count(self):
        if self.days_to_close > 1 and self.id is not False:
            if self.state in ('draft', 'sent'):
                date_from = self.date_order
                if type(date_from) is str:
                    date_from = datetime.strptime(date_from, '%Y-%m-%d %H:%M:%S')
                days = self.days_to_close
                if days > 30:
                    "Noo hace nada"
                else:
                    date_to = date_from + timedelta(days=days)
                    count_days = self.calculate_expiry_date(date_to, date_from)
                    check_days = self.check_days(count_days)
                    self.check_control = True
                    self.days_count = count_days
                    return count_days
            elif self.state not in ('draft', 'sent'):
                self.days_count = self.days_count

    @api.multi
    def calculate_expiry_date(self, second_date, first_date):
        dias = 0
        if self.state in ('draft', 'sent'):
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

    @api.multi
    def check_days(self, days):
        if days == '0' and self.state in ('draft', 'sent'):
            self.verify_days = True
            if self.verify_days:
                self.update({'quotation_state': 'close'})
            return True
        else:
            return False

    quotation_state = fields.Selection([('open', 'Abierta'), ('close', 'Expirada')], 'Estado Cotizacion',
                                       default='open')
    days_to_close = fields.Integer(default='1')
    days_count = fields.Char('Dias restantes', compute=get_quotation_count)
    check_control = fields.Boolean('Para guardar o imprimir debe registrar dias de expiracion validos')
    pass_order = fields.Boolean('Pass', default=False)
    verify_days = fields.Boolean('Expired', compute=check_days)

    @api.multi
    def create_new_invoice(self):
        order_id = self
        if not order_id.invoice_ids and order_id.state == 'manual':
            raise except_orm('Error !', 'No puede refacturar una orden de venta que no tenga facturas asociadas.!')
        for invoice in order_id.invoice_ids:
            if invoice.state not in ('cancel', 'invalidate'):
                raise except_orm('Error !', 'No puede refacturar si tiene una factura que no este cancelada o anulada!')
            if invoice.state in ('cancel', 'invalidate'):
                invoice.update({'state': 'cancel'})
        if order_id.state in ('progress', 'done'):
            self.update({'state': 'manual'})
            for line in order_id.order_line:
                line.update({'state': 'confirmed', 'invoiced': False})
        else:
            raise except_orm('Error !', 'No puede volver a refacturar una orden que no este facturada.')
        return True

    @api.multi
    def action_button_confirm(self):
        res = super(SaleOrder, self).action_button_confirm()
        if self.state == 'manual':
            print "dias", self.days_to_close
            if self.days_to_close <= 1:
                raise except_orm('Error!', 'Primero debe colocar los dias de expiracion antes de generar '
                                           'la orden de venta.')
            for line in self.order_line:
                if line.product_id.type in ('product', 'consu'):
                    quantity_check = self.search_check_quant(line)
                    if not quantity_check:
                        raise except_orm('Error', 'No existe disponibilidad en bodega general para realizar la venta del'
                                                  ' producto o si va a generar una orden de servicios debe asegurarse de '
                                                  'que sean items configurados como tipo - SERVICIO - '
                                                  ' %s.' % line.product_id.name_template)
                    if not quantity_check:
                        check_orders = self.search_mrp_productions(line.product_id, line.order_id)
                        if not check_orders:
                            raise except_orm('Error', 'No puede crear una orden de venta que no tiene asociada o creada una'
                                                      ' orden de produccion al siguiente '
                                                      'producto %s.' % line.product_id.name_template)
        return res

    @api.multi
    def search_mrp_productions(self, product_id, sale_order):
        if product_id:
            mrp_production = self.env['mrp.production'].search([('product_id', '=', product_id.id),
                                                                ('state', 'not in', ('done', 'cancel'))])
            sale_mrp = self.env['mrp.production'].search([('product_id', '=', product_id.id),
                                                          ('sale_order_id', '=', sale_order.id),
                                                          ('state', 'not in', ('done', 'cancel'))])
            if not mrp_production or not sale_mrp:
                return False
            else:
                return True

    @api.multi
    def search_check_quant(self, sale_line_id):
        sum = 0
        if sale_line_id.product_id:
            stock_quant = self.env['stock.quant'].search([('product_id', '=', sale_line_id.product_id.id),
                                                          ('location_id', '=', 12),
                                                          ('qty', '>', 0)])
            for item in stock_quant:
                # if item.reservation_id:
                #     raise except_orm('Error', 'Existe una reservacion, comuniquese con bodega'
                #                               ' para quitar la reservacion y pueda sacar la cantidad'
                #                               ' deseada, producto. %s' % item.product_id.name_template)
                sum += item.qty
            if sum >= sale_line_id.product_uom_qty:
                return True
            else:
                return False


SaleOrder()
