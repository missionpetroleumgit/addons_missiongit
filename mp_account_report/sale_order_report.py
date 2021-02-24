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


class sale_order_detail_report(models.TransientModel):
    _name = 'sale.order.detail.report'
    _description = 'Reporte Orden'

    date_from = fields.Date('Fecha Desde')
    date_to = fields.Date('Fecha Hasta')
    type_export = fields.Selection([('xls', 'EXCEL')], 'Tipo de archivo', required=True, default='xls')
    data = fields.Binary('Archivo', filters=None)
    path = fields.Char('Ruta')
    company_id = fields.Many2one('res.company', 'Compania')
    partner_id = fields.Many2one('res.partner', 'Cliente', domain=[('customer', '=', True)])
    state = fields.Selection([('all', 'Todas'), ('order', 'Venta a Facturar'), ('invoiced', 'Facturada'),
                              ('done', 'Realizada')], 'Estado Orden', default='all')
    importation_id = fields.Many2one('purchase.importation', 'Importacion')

    @api.multi
    def set_header(self, ws, xi, style_header):

        ws.write(xi, 2, 'ORDEN', style_header)
        ws.write(xi, 3, 'FECHA', style_header)
        ws.write(xi, 4, 'TIPO', style_header)
        ws.write(xi, 5, 'RUC', style_header)
        ws.write(xi, 6, 'NOMBRE', style_header)
        ws.write(xi, 7, 'FACTURA', style_header)
        ws.write(xi, 8, 'PREFACTURA', style_header)
        ws.write(xi, 9, 'VALIDACION', style_header)
        ws.write(xi, 10, 'DIAS', style_header)
        ws.write(xi, 11, 'PAGO', style_header)
        ws.write(xi, 12, 'DIAS', style_header)
        ws.write(xi, 13, 'AUTORIZACION', style_header)
        ws.write(xi, 14, 'FECHA FACT.', style_header)
        ws.write(xi, 15, 'DOC', style_header)
        ws.write(xi, 16, 'EST.', style_header)
        ws.write(xi, 17, 'BASE 0', style_header)
        ws.write(xi, 18, 'BASE IVA', style_header)
        ws.write(xi, 19, 'IVA', style_header)
        ws.write(xi, 20, 'TOTAL', style_header)

        col = 20
        return col

    @api.multi
    def set_body(self, orders, invoice, ws, xi, linea_der, linea_izq, seq, linea_izq_n, linea_izq_neg, view_style, linea_der_bold
                 ,view_style_out):

        for order in orders:

            ws.write(xi, 1, '', linea_izq)
            ws.write(xi, 2, order.name, linea_izq)
            ws.write(xi, 3, order.date_order, linea_izq)
            ws.write(xi, 4, 'DV', linea_izq)
            ws.write(xi, 5, '[' + order.partner_id.part_number + ']', linea_izq)
            ws.write(xi, 6, order.partner_id.name, linea_izq_n)
            ws.write(xi, 8, order.invoice_created, linea_der)
            ws.write(xi, 9, order.invoice_valid, linea_der)
            ws.write(xi, 10, order.val_days, linea_der)
            ws.write(xi, 11, order.invoice_paid_date, linea_der)
            ws.write(xi, 12, order.invoice_paid_days, linea_der)
            if invoice:
                ws.write(xi, 7, invoice.number_reem, linea_der)
                ws.write(xi, 13, invoice.authorization_id.name, linea_izq_n)
                ws.write(xi, 14, invoice.date_invoice, linea_izq_n)
                ws.write(xi, 15, invoice.document_type.code, linea_izq_n)
                ws.write(xi, 16, invoice.authorization_id.serie_emission, linea_izq_n)
                ws.write(xi, 17, invoice.base_sin_iva, linea_izq_n)
                ws.write(xi, 18, invoice.base_iva, linea_izq_n)
                ws.write(xi, 19, invoice.amount_iva, linea_izq_n)
                ws.write(xi, 20, invoice.amount_total, linea_izq_n)
            else:
                ws.write(xi, 7, '-----', linea_der)
                ws.write(xi, 13, '-----', linea_izq_n)
                ws.write(xi, 14, '-----', linea_izq_n)
                ws.write(xi, 15, '-----', linea_izq_n)
                ws.write(xi, 16, '-----', linea_izq_n)
                ws.write(xi, 17, '0', linea_izq_n)
                ws.write(xi, 18, '0', linea_izq_n)
                ws.write(xi, 19, '0', linea_izq_n)
                ws.write(xi, 20, '0', linea_izq_n)

    @api.multi
    def get_orders(self):

        date_from = self.date_from
        date_to = self.date_to
        sale_order = self.env['sale.order']

        if self.date_from > self.date_to:
            raise except_orm('Error !', 'Revise las fechas, la primera fecha no debe ser mayor a la segunda fecha !')

        domain = [('date_order', '>=', date_from), ('date_order', '<=', date_to),
                  ('state', 'in', ('manual', 'progress', 'done'))]

        if self.company_id:
            domain.append(('company_id', '=', self.company_id.id))
        if self.partner_id:
            domain.append(('partner_id', '=', self.partner_id.id))

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
                                     'align: vertical center, horizontal left, wrap on;'
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

        ws = wb.add_sheet('Reporte Ventas')

        ws.show_grid = False
        ws.header_str = u"&LFecha de Impresion: &D Hora: &T&RPagina &P de &N"
        ws.footer_str = u""
        company = self.env['res.users'].browse(self._uid).company_id
        ws.write_merge(1, 1, 1, 5, company.name, style_cabecera)
        ws.write_merge(2, 2, 1, 5, 'Fecha desde: ' + self.date_from + ' - ' + 'Fecha hasta: ' + self.date_to + ' ', style_cabecera)
        ws.write_merge(3, 3, 1, 5, 'REPORTE VENTAS', style_cabecera)

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

        xi = 9  # Cabecera de Cliente
        self.set_header(ws, xi, style_header)
        xi += 1
        data_file_name = "reporte_ventas.xls"
        seq = 0
        orders = self.get_orders()
        invoice = False
        for order in orders:

            # self.set_body(order, invoice, ws, xi, linea_der, linea_izq, seq, linea_izq_n, linea_izq_neg, view_style,
            #           linea_der_bold, view_style_out)
            # xi += 1

            if order:
                for invoice in order.invoice_ids:
                    if invoice.state in ('open', 'paid'):
                        self.set_body(order, invoice, ws, xi, linea_der, linea_izq, seq, linea_izq_n, linea_izq_neg,
                                      view_style,
                                      linea_der_bold, view_style_out)
                        xi += 1

        ws.col(0).width = 100
        ws.col(1).width = 100
        ws.col(2).width = 3500
        ws.col(3).width = 4000
        ws.col(4).width = 2000
        ws.col(5).width = 3500
        ws.col(6).width = 10000
        ws.col(7).width = 5000
        ws.col(8).width = 4000
        ws.col(9).width = 4000
        ws.col(10).width = 2000
        ws.col(11).width = 2000
        ws.col(12).width = 3000
        ws.col(13).width = 3000
        ws.col(14).width = 3000
        ws.col(15).width = 3000

        try:
            buf = cStringIO.StringIO()

            wb.save(buf)
            out = base64.encodestring(buf.getvalue())
            buf.close()
            res_model = 'sale.order.detail.report'
            self.load_doc(out, data_file_name, res_model)

            return self.write({'data': out, 'txt_filename': data_file_name, 'name': 'control_facturas.xls'})

        except ValueError:
            raise Warning('Error a la hora de salvar el archivo')
        ws.col(6).width = 3000
        ws.col(7).width = 3000

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

sale_order_detail_report()
