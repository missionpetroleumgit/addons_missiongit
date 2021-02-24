# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution - Ecuador
#    Copyright (C) 2019 MissionPetroleum Daniel Aldaz (<daldaz@mission-petroleum.com>).
#
##############################################################################

from datetime import datetime
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT as DSTF
from openerp import models, fields, api
import xlwt as pycel
import base64
import cStringIO
from openerp.exceptions import except_orm
import re
import locale


class invoice_control(models.TransientModel):
    _name = 'invoice.control'
    _description = 'Control Facturas'

    date_from = fields.Date('Fecha Desde')
    date_to = fields.Date('Fecha Hasta')
    type_export = fields.Selection([('xls', 'EXCEL')], 'Tipo de archivo', required=True, default='xls')
    data = fields.Binary('Archivo', filters=None)
    path = fields.Char('Ruta')
    company_id = fields.Many2one('res.company', 'Compania')
    partner_id = fields.Many2one('res.partner', 'Cliente', domain=[('customer', '=', True)])
    state = fields.Selection([('all', 'Todas'), ('order', 'Venta a Facturar'), ('invoiced', 'Facturada'),
                              ('done', 'Realizada')], 'Estado Orden', default='all')

    @api.multi
    def set_header(self, ws, xi, style_header):
        ws.write(xi, 1, 'Sec.', style_header)
        ws.write(xi, 2, 'Cliente', style_header)
        ws.write(xi, 3, 'Contrato', style_header)
        ws.write(xi, 4, 'Lista de Precios', style_header)
        ws.write(xi, 5, 'Fecha Servicio', style_header)
        ws.write(xi, 6, 'Fecha Pre-Factura', style_header)
        ws.write(xi, 7, 'Fecha Factura', style_header)
        ws.write(xi, 8, 'Fecha Cobro', style_header)
        ws.write(xi, 9, 'F.S(-)F. P-Ft.', style_header)
        ws.write(xi, 10, 'F.S(-)F. Ft.', style_header)
        ws.write(xi, 11, 'F.C(-)F. Ft.', style_header)
        ws.write(xi, 12, 'Dias por Cobro', style_header)
        ws.write(xi, 13, 'Orden No.', style_header)
        ws.write(xi, 14, 'Subtotal', style_header)
        ws.write(xi, 15, 'IVA', style_header)
        ws.write(xi, 16, 'Total', style_header)
        ws.write(xi, 17, 'Estado orden', style_header)
        ws.write(xi, 18, 'Orden Ref.', style_header)
        ws.write(xi, 19, 'No. Ticket', style_header)
        ws.write(xi, 20, 'No. Factura', style_header)
        # ws.write(xi, 18, 'Fecha Fact.', style_header)
        col = 19
        return col

    @api.multi
    def get_state(self, state):
        name_state = '-'
        if state:
            if state == 'manual':
                name_state = 'Venta a Facturar'
            if state == 'progress':
                name_state = 'Facturada'
            if state == 'done':
                name_state = 'Realizada'
        return name_state

    @api.multi
    def set_body(self, orders, ws, xi, linea_der, linea_izq, seq, linea_izq_n, linea_izq_neg, view_style, linea_der_bold
                 ,view_style_out):

        for order in orders:
            terms = order.partner_id.property_payment_term
            if terms:
                term = order.partner_id.property_payment_term.name
                days_term = re.sub("\D", "", term)

            invoice_created = False
            invoice_valid = False
            invoice_paid_date = False
            invoiced_days_count = False
            d_invoice = '-'
            if order.date_invoice:
                d_invoice = datetime.strptime(order.date_invoice, '%Y-%m-%d').strftime('%Y-%m-%d %H:%M:%S')
                invoice_created = order.calculate_date(d_invoice, order.docs_sent)
                invoice_valid = order.calculate_date(d_invoice, order.docs_sent)
                invoice_paid_date = order.calculate_date(order.invoice_paid_date, d_invoice)
                if not invoice_paid_date:
                    invoiced_days_count = order.calculate_date(datetime.now(), d_invoice)
                else:
                    invoiced_days_count = order.calculate_date(order.invoice_paid_date, d_invoice)
            if invoice_created:
                invcrt = int(re.sub("\D", "", invoice_created)) - 1
            else:
                invcrt = '-'
            if invoice_valid:
                invval = int(re.sub("\D", "", invoice_valid)) - 1
            else:
                invval = '-'
            if invoice_paid_date:
                invpaid = int(re.sub("\D", "", invoice_paid_date)) - 1
            else:
                invpaid = '-'
            if invoiced_days_count:
                invdcnt = int(re.sub("\D", "", invoiced_days_count)) - 1
            else:
                invdcnt = '-'
            ws.write(xi, 1, seq, linea_der)
            ws.write(xi, 2, order.partner_id.name, linea_izq)
            ws.write(xi, 3, order.ticket_id.contract_id.name or '-', linea_izq)
            ws.write(xi, 4, order.pricelist_id.name, linea_izq)
            if order.docs_sent:
                ws.write(xi, 5, order.docs_sent[:10], linea_izq_n)
            else:
                ws.write(xi, 5, '-', linea_izq_n)
            if d_invoice:
                ws.write(xi, 6, d_invoice[:10], linea_izq_n)
            else:
                ws.write(xi, 6, '-', linea_izq_n)
            if d_invoice:
                ws.write(xi, 7, d_invoice[:10], linea_izq_n)
            else:
                ws.write(xi, 7, '-', linea_izq_n)
            if order.invoice_paid_date:
                ws.write(xi, 8, order.invoice_paid_date[:10], linea_izq_n)
            else:
                ws.write(xi, 8, '-', linea_izq_n)
            ws.write(xi, 9, invcrt or '-', linea_izq_neg)
            ws.write(xi, 10, invval or '-', linea_izq_neg)
            ws.write(xi, 11, invpaid or '-', linea_izq_neg)
            if terms:
                if type(invdcnt) is int:
                    if int(invdcnt) > int(days_term):
                        ws.write(xi, 12, invdcnt or '-', view_style_out)
                    else:
                        ws.write(xi, 12, invdcnt or '-', view_style)
                else:
                    ws.write(xi, 12, '-', view_style)
            else:
                ws.write(xi, 12, invdcnt or '-', view_style)
            ws.write(xi, 13, order.name, linea_izq_n)
            ws.write(xi, 14, locale.currency(order.amount_untaxed, grouping=True), linea_der_bold)
            ws.write(xi, 15, locale.currency(order.amount_tax, grouping=True), linea_der_bold)
            ws.write(xi, 16, locale.currency(order.amount_total, grouping=True), linea_der_bold)
            ws.write(xi, 17, self.get_state(order.state), linea_izq_n)
            ws.write(xi, 18, order.client_order_ref, linea_izq)
            ws.write(xi, 19, order.ticket_id.name, linea_izq_n)
            ws.write(xi, 20, order.invoice_number or '-', linea_izq_n)
            # ws.write(xi, 18, order.date_invoice or '-', linea_izq_n)

    @api.multi
    def get_orders(self):

        date_from = self.date_from
        date_to = self.date_to
        sale_order = self.env['sale.order']

        if self.date_from > self.date_to:
            raise except_orm('Error !', 'Revise las fechas, la primera fecha no debe ser mayor a la segunda fecha !')

        domain = [('date_order', '>=', date_from), ('date_order', '<=', date_to), ('docs_sent', '>=', date_from),
                  ('docs_sent', '<=', date_to)]
        if self.company_id:
            domain.append(('company_id', '=', self.company_id.id))
        if self.partner_id:
            domain.append(('partner_id', '=', self.partner_id.id))
        if self.state == 'all':
            domain.append(('state', 'in', ('manual', 'progress', 'done')))
        if self.state == 'order':
            domain.append(('state', '=', 'manual'))
        if self.state == 'invoiced':
            domain.append(('state', '=', 'progress'))
        if self.state == 'done':
            domain.append(('state', '=', 'done'))

        sale_order_data = sale_order.search(domain, order='partner_id')

        return sale_order_data

    @api.one
    def excel_action(self):
        wb = pycel.Workbook(encoding='utf-8')

        style_cabecera = pycel.easyxf('font: colour black, bold True;'
                                      'align: vertical center, horizontal center;'
                                      )

        style_header = pycel.easyxf('font: bold True;'
                                    'align: vertical center, horizontal center, wrap on;'
                                    'borders: left 1, right 1, top 1, bottom 1;')

        view_style = pycel.easyxf('font: colour green, bold true, height 200;'
                                  'align: vertical center, horizontal center, wrap on;'
                                  'borders: left 1, right 1, top 1, bottom 1;'
                                  )

        linea_izq = pycel.easyxf('font: colour black, height 150;'
                                 'align: vertical center, horizontal left, wrap on;'
                                 'borders: left 1, right 1, top 1, bottom 1;'
                                 )
        linea_izq_n = pycel.easyxf('font: colour black, height 140;'
                                   'align: vertical center, horizontal center, wrap on;'
                                   'borders: left 1, right 1, top 1, bottom 1;'
                                   )
        linea_izq_neg = pycel.easyxf('font: colour black, bold true, height 200;'
                                     'align: vertical center, horizontal center, wrap on;'
                                     'borders: left 1, right 1, top 1, bottom 1;'
                                     )
        linea_der = pycel.easyxf('font: colour black, height 150;'
                                 'align: vertical center, horizontal right;'
                                 'borders: left 1, right 1, top 1, bottom 1;'
                                 )
        linea_der_bold = pycel.easyxf('font: colour black, bold true, height 200;'
                                      'align: vertical center, horizontal right, wrap on;'
                                      'borders: left 1, right 1, top 1, bottom 1;'
                                      )
        view_style_out = pycel.easyxf('font: colour red, bold true, height 200;'
                                      'align: vertical center, horizontal center, wrap on;'
                                      'borders: left 1, right 1, top 1, bottom 1;'
                                      )
        view_style_red = pycel.easyxf('font: colour red, height 200;'
                                      'align: vertical center, horizontal left, wrap on;'
                                      'borders: left 1, right 1, top 1, bottom 1;'
                                      )
        view_style_green = pycel.easyxf('font: colour green, height 200;'
                                      'align: vertical center, horizontal left, wrap on;'
                                      'borders: left 1, right 1, top 1, bottom 1;'
                                      )

        ws = wb.add_sheet('CONTROL DE ORDENES DE VENTA')

        ws.show_grid = False
        ws.header_str = u"&LFecha de Impresion: &D Hora: &T&RPagina &P de &N"
        ws.footer_str = u""
        company = self.env['res.users'].browse(self._uid).company_id
        ws.write_merge(1, 1, 1, 5, company.name, style_cabecera)
        # ws.write_merge(2, 2, 1, 5, 'Dirección: ' + company.partner_id.street, style_cabecera)
        ws.write_merge(3, 3, 1, 5, 'Ruc: ' + company.partner_id.part_number, style_cabecera)
        ws.write_merge(4, 4, 1, 5, 'Fecha:' + ' ' + datetime.today().strftime('%Y-%m-%d'), style_cabecera)
        ws.write_merge(5, 5, 1, 5, 'CONTROL DE FACTURAS', style_cabecera)
        ws.write_merge(7, 7, 1, 5, 'Días por Cobro', linea_izq)
        ws.write_merge(8, 8, 1, 5, '████ Rojo:', view_style_red)
        ws.write_merge(9, 9, 1, 5, 'Los días por cobrar sean mayor a los días en el terminos de pago del cliente'
                       , linea_izq)
        ws.write_merge(10, 10, 1, 5, '████ Verde:', view_style_green)
        ws.write_merge(11, 11, 1, 5, 'Los días por cobrar están en el rango del termino de pago con el cliente'
                       , linea_izq)
        ws.write_merge(12, 12, 1, 5, 'F.S: Fecha de Servicio  |  F. P-Ft.: Fecha de la Pre-factura  |  '
                                     'F. Ft.: Fecha de la Factura  |  F.C: Fecha de Cobro', linea_izq)

        ws.fit_num_pages = 1
        ws.fit_height_to_pages = 0
        ws.fit_width_to_pages = 1
        ws.portrait = 1

        align = pycel.Alignment()
        align.horz = pycel.Alignment.HORZ_RIGHT
        align.vert = pycel.Alignment.VERT_CENTER

        font1 = pycel.Font()
        font1.colour_index = 0x0
        font1.height = 140

        linea_izq_n.width = 150

        # Formato de Numero
        style = pycel.XFStyle()
        style.num_format_str = '#,##0.00'
        style.alignment = align
        style.font = font1

        # Formato de Numero Saldo
        font = pycel.Font()
        font.bold = True
        font.colour_index = 0x27

        style1 = pycel.XFStyle()
        style1.num_format_str = '#,##0.00'
        style1.alignment = align
        style1.font = font

        font2 = pycel.Font()
        font2.bold = True
        font2.colour_index = 0x0

        style2 = pycel.XFStyle()
        style2.num_format_str = '#,##0.00'
        style2.alignment = align
        style2.font = font2

        style3 = pycel.XFStyle()
        style3.num_format_str = '0'
        style3.alignment = align
        style3.font = font1

        xi = 13  # Cabecera de Cliente
        self.set_header(ws, xi, style_header)
        xi += 1
        data_file_name = "control_ordenes_venta_al_%s.xls" % datetime.now().strftime(DSTF)
        orders = self.get_orders()
        seq = 0
        for order in orders:
            seq += 1
            self.set_body(order, ws, xi, linea_der, linea_izq, seq, linea_izq_n, linea_izq_neg, view_style,
                          linea_der_bold, view_style_out)
            xi += 1

        ws.col(0).width = 500
        ws.col(1).width = 1500
        ws.col(2).width = 15900
        ws.col(3).width = 10000
        ws.col(4).width = 11000
        ws.col(5).width = 2500
        ws.col(6).width = 2500
        ws.col(7).width = 2500
        ws.col(8).width = 2500
        ws.col(9).width = 3000
        ws.col(10).width = 2500
        ws.col(11).width = 2500
        ws.col(12).width = 2500
        ws.col(13).width = 3500
        ws.col(14).width = 3000
        ws.col(15).width = 3000
        ws.col(16).width = 3000
        ws.col(17).width = 3000
        ws.col(18).width = 10500
        ws.col(19).width = 5500
        ws.col(20).width = 3500
        ws.row(5).height = 750
        ws.row(13).height = 750

        try:
            buf = cStringIO.StringIO()

            wb.save(buf)
            out = base64.encodestring(buf.getvalue())
            buf.close()
            res_model = 'invoice.control'
            self.load_doc(out, data_file_name, res_model)

            return self.write({'data': out, 'txt_filename': data_file_name, 'name': 'control_facturas.xls'})

        except ValueError:
            raise Warning('Error a la hora de salvar el archivo')

    @api.one
    def load_doc(self, out, data_file_name, res_model):
        attach_vals = {
            'name': data_file_name,
            'datas_fname': data_file_name,
            'res_model': res_model,
            'datas': out,
            'type': 'binary',
            'file_type': 'file_type',
        }
        if self.id:
            attach_vals.update({'res_id': self.id})
        self.env['ir.attachment'].create(attach_vals)

invoice_control()
