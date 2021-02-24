# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution - Ecuador
#    Copyright (C) 2019 MissionPetroleum Daniel Aldaz (<daldaz@mission-petroleum.com>).
#
##############################################################################

from openerp import models, fields, api
import xlwt as pycel
import base64
import cStringIO
from openerp.exceptions import except_orm


class sale_order_invoice_report(models.TransientModel):
    _name = 'sale.order.invoice.report'
    _description = 'Reporte Ventas Facturas'

    date_from = fields.Date('Fecha Desde')
    date_to = fields.Date('Fecha Hasta')
    type_export = fields.Selection([('xls', 'EXCEL')], 'Tipo de archivo', required=True, default='xls')
    data = fields.Binary('Archivo', filters=None)
    path = fields.Char('Ruta')
    company_id = fields.Many2one('res.company', 'Compania')
    partner_id = fields.Many2one('res.partner', 'Cliente', domain=[('customer', '=', True)])
    pit_id = fields.Many2one('service.well.line', 'Pozo')
    fields_id = fields.Many2one('service.field', 'Campo')
    business_unit_id = fields.Many2one('service.line', 'Unidad de negocio')
    account_analytic_id = fields.Many2one('account.analytic.plan.instance', 'Cuenta analitica')

    @api.multi
    def set_header(self, ws, xi, style_header):

        ws.write(xi, 2, 'ORDEN', style_header)
        ws.write(xi, 3, 'FECHA', style_header)
        ws.write(xi, 4, 'TIPO', style_header)
        ws.write(xi, 5, 'RUC', style_header)
        ws.write(xi, 6, 'NOMBRE', style_header)
        ws.write(xi, 7, 'POZO', style_header)
        ws.write(xi, 8, 'CAMPO', style_header)
        ws.write(xi, 9, 'L. NEGOCIO', style_header)
        if self.account_analytic_id:
            ws.write(xi, 10, 'CUENTA COSTO', style_header)
            ws.write(xi, 11, 'FACTURA', style_header)
            ws.write(xi, 12, 'AUTORIZACION', style_header)
            ws.write(xi, 13, 'FECHA FACT.', style_header)
            ws.write(xi, 14, 'DOC', style_header)
            ws.write(xi, 15, 'EST.', style_header)
            ws.write(xi, 16, 'BASE 0', style_header)
            ws.write(xi, 17, 'BASE IVA', style_header)
            ws.write(xi, 18, 'IVA', style_header)
            ws.write(xi, 19, 'TOTAL', style_header)
        else:
            ws.write(xi, 10, 'FACTURA', style_header)
            ws.write(xi, 11, 'AUTORIZACION', style_header)
            ws.write(xi, 12, 'FECHA FACT.', style_header)
            ws.write(xi, 13, 'DOC', style_header)
            ws.write(xi, 14, 'EST.', style_header)
            ws.write(xi, 15, 'BASE 0', style_header)
            ws.write(xi, 16, 'BASE IVA', style_header)
            ws.write(xi, 17, 'IVA', style_header)
            ws.write(xi, 18, 'TOTAL', style_header)
        col = 19
        return col

    @api.multi
    def set_body(self, invoices, sale, account, refund, ws, xi, linea_der, linea_izq, seq, linea_izq_n, linea_izq_neg, view_style, linea_der_bold
                 ,view_style_out):

        for order in invoices:
            if not refund:
                ws.write(xi, 1, '', linea_izq)
                if sale:
                    ws.write(xi, 2, sale.name, linea_izq)
                    ws.write(xi, 3, sale.date_order, linea_izq)
                else:
                    ws.write(xi, 2, '-----', linea_izq)
                    ws.write(xi, 3, '-----', linea_izq)
                ws.write(xi, 4, 'DV', linea_izq)
                ws.write(xi, 5, '[' + order.partner_id.part_number + ']', linea_izq)
                ws.write(xi, 6, order.partner_id.name, linea_izq_n)
                if order.pit_id:
                    ws.write(xi, 7, order.pit_id.name, linea_der)
                else:
                    ws.write(xi, 7, '-----', linea_izq)
                if order.fields_id:
                    ws.write(xi, 8, order.fields_id.name, linea_der)
                else:
                    ws.write(xi, 8, '-----', linea_izq)
                if order.business_unit_id:
                    ws.write(xi, 9, order.business_unit_id.name, linea_der)
                else:
                    ws.write(xi, 9, '-----', linea_der)
                if self.account_analytic_id:
                    ws.write(xi, 10, account, linea_der)
                    ws.write(xi, 11, order.number_reem, linea_der)
                    ws.write(xi, 12, order.authorization_id.name, linea_izq_n)
                    ws.write(xi, 13, order.date_invoice, linea_izq_n)
                    ws.write(xi, 14, order.document_type.code, linea_izq_n)
                    ws.write(xi, 15, order.authorization_id.serie_emission, linea_izq_n)
                    if order.amount_iva == 0:
                        if order.state == 'invalidate':
                            ws.write(xi, 15, '0', linea_izq_n)
                            ws.write(xi, 16, '0', linea_izq_n)
                            ws.write(xi, 17, '0', linea_izq_n)
                            ws.write(xi, 18, '0', linea_izq_n)
                        else:
                            ws.write(xi, 15, order.amount_untaxed, linea_izq_n)
                            ws.write(xi, 16, '0', linea_izq_n)
                            ws.write(xi, 17, '0', linea_izq_n)
                            ws.write(xi, 18, order.amount_total, linea_izq_n)
                    else:
                        ws.write(xi, 15, '0', linea_izq_n)
                        if order.state == 'invalidate':
                            ws.write(xi, 16, '0', linea_izq_n)
                            ws.write(xi, 17, '0', linea_izq_n)
                            ws.write(xi, 18, '0', linea_izq_n)
                        else:
                            ws.write(xi, 16, order.amount_untaxed, linea_izq_n)
                            ws.write(xi, 17, order.amount_iva, linea_izq_n)
                            ws.write(xi, 18, order.amount_total, linea_izq_n)
                else:
                    ws.write(xi, 10, order.number_reem, linea_der)
                    ws.write(xi, 11, order.authorization_id.name, linea_izq_n)
                    ws.write(xi, 12, order.date_invoice, linea_izq_n)
                    ws.write(xi, 13, order.document_type.code, linea_izq_n)
                    ws.write(xi, 14, order.authorization_id.serie_emission, linea_izq_n)
                    if order.amount_iva == 0:
                        if order.state == 'invalidate':
                            ws.write(xi, 15, '0', linea_izq_n)
                            ws.write(xi, 16, '0', linea_izq_n)
                            ws.write(xi, 17, '0', linea_izq_n)
                            ws.write(xi, 18, '0', linea_izq_n)
                        else:
                            ws.write(xi, 15, order.amount_untaxed, linea_izq_n)
                            ws.write(xi, 16, '0', linea_izq_n)
                            ws.write(xi, 17, '0', linea_izq_n)
                            ws.write(xi, 18, order.amount_total, linea_izq_n)
                    else:
                        ws.write(xi, 15, '0', linea_izq_n)
                        if order.state == 'invalidate':
                            ws.write(xi, 16, '0', linea_izq_n)
                            ws.write(xi, 17, '0', linea_izq_n)
                            ws.write(xi, 18, '0', linea_izq_n)
                        else:
                            ws.write(xi, 16, order.amount_untaxed, linea_izq_n)
                            ws.write(xi, 17, order.amount_iva, linea_izq_n)
                            ws.write(xi, 18, order.amount_total, linea_izq_n)
            else:
                ws.write(xi, 1, '', linea_izq)
                ws.write(xi, 2, '-----', linea_izq)
                ws.write(xi, 3, '-----', linea_izq)
                ws.write(xi, 4, 'DRV', linea_izq)
                ws.write(xi, 5, '[' + refund.partner_id.part_number + ']', linea_izq)
                ws.write(xi, 6, refund.partner_id.name, linea_izq_n)
                ws.write(xi, 7, '-----', linea_der)
                ws.write(xi, 8, '-----', linea_izq)
                if order.business_unit_id:
                    ws.write(xi, 9, order.business_unit_id.name, linea_der)
                else:
                    ws.write(xi, 9, '-----', linea_der)
                ws.write(xi, 10, refund.number_reem, linea_der)
                ws.write(xi, 11, refund.authorization_id.name, linea_izq_n)
                ws.write(xi, 12, refund.date_invoice, linea_izq_n)
                ws.write(xi, 13, refund.document_type.code, linea_izq_n)
                ws.write(xi, 14, refund.authorization_id.serie_emission, linea_izq_n)
                ws.write(xi, 15, '0', linea_izq_n)
                ws.write(xi, 16, refund.amount_untaxed * -1, linea_izq_n)
                ws.write(xi, 17, refund.amount_iva * -1, linea_izq_n)
                ws.write(xi, 18, refund.amount_total * -1, linea_izq_n)

    @api.multi
    def get_invoices(self):

        date_from = self.date_from
        date_to = self.date_to
        account_invoice = self.env['account.invoice']
        account_invoice_line = self.env['account.invoice.line']

        if self.account_analytic_id:

            if self.date_from > self.date_to:
                raise except_orm('Error !',
                                 'Revise las fechas, la primera fecha no debe ser mayor a la segunda fecha !')

            domain = [('invoice_id.date_invoice', '>=', date_from), ('invoice_id.date_invoice', '<=', date_to),
                      ('state', 'in', ('open', 'paid', 'invalidate', 'cancel')),
                      ('type', 'in', ('out_invoice', 'out_refund'))]

            if self.company_id:
                domain.append(('company_id', '=', self.company_id.id))
            if self.partner_id:
                domain.append(('partner_id', '=', self.partner_id.id))
            if self.pit_id:
                domain.append(('invoice_id.pit_id', '=', self.pit_id.id))
            if self.fields_id:
                domain.append(('invoice_id.fields_id', '=', self.fields_id.id))
            if self.business_unit_id:
                domain.append(('invoice_id.business_unit_id', '=', self.business_unit_id.id))
            if self.account_analytic_id:
                domain.append(('analytics_id', '=', self.account_analytic_id.id))

            account_invoice_data = account_invoice_line.search(domain, order='partner_id')

        else:
            if self.date_from > self.date_to:
                raise except_orm('Error !', 'Revise las fechas, la primera fecha no debe ser mayor a la segunda fecha !')

            domain = [('date_invoice', '>=', date_from), ('date_invoice', '<=', date_to),
                      ('state', 'in', ('open', 'paid', 'invalidate', 'cancel')),
                      ('type', 'in', ('out_invoice', 'out_refund'))]

            if self.company_id:
                domain.append(('company_id', '=', self.company_id.id))
            if self.partner_id:
                domain.append(('partner_id', '=', self.partner_id.id))
            if self.pit_id:
                domain.append(('pit_id', '=', self.pit_id.id))
            if self.fields_id:
                domain.append(('fields_id', '=', self.fields_id.id))
            if self.business_unit_id:
                domain.append(('business_unit_id', '=', self.business_unit_id.id))

            account_invoice_data = account_invoice.search(domain, order='number_reem')

        return account_invoice_data

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
        ws.write_merge(3, 3, 1, 5, 'REPORTE FACTURAS VENTAS', style_cabecera)

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
        data_file_name = "reporte_ventas_facturas.xls"
        seq = 0
        orders = self.get_invoices()
        order = False
        refund = False
        sale_order_obj = self.env['sale.order']
        account_invoice_obj = self.env['account.invoice']
        invoice_ids = account_invoice_obj.search([('type', '=', 'out_refund'),
                                                  ('date_invoice', '>=', self.date_from),
                                                  ('date_invoice', '<=', self.date_to)])
        data = []
        if not self.account_analytic_id:
            for invoice in orders:
                if len(invoice.origin) >= 14:
                    sale_id = sale_order_obj.search([('name', '=', invoice.origin[:11])])
                    if not sale_id:
                        sale_id = sale_order_obj.search([('name', '=', invoice.origin[:13])])
                else:
                    sale_id = sale_order_obj.search([('name', '=', invoice.origin)])

                if sale_id:
                    self.set_body(invoice, sale_id, order, refund, ws, xi, linea_der, linea_izq, seq, linea_izq_n,
                                  linea_izq_neg, view_style, linea_der_bold, view_style_out)
                    xi += 1

                for refund_id in invoice_ids:
                    if refund_id.id not in data:
                        data.append(refund_id.id)
                        self.set_body(invoice, sale_id, order, refund_id, ws, xi, linea_der, linea_izq, seq,
                                      linea_izq_n, linea_izq_neg, view_style, linea_der_bold, view_style_out)
                        xi += 1

        if self.account_analytic_id:
            invoice = False
            for lines in orders:
                if len(invoice.origin) >= 14:
                    sale_id = sale_order_obj.search([('name', '=', invoice.origin[:13])])
                else:
                    sale_id = sale_order_obj.search([('name', '=', invoice.origin)])
                if sale_id and invoice != lines.invoice_id.id:
                    self.set_body(lines.invoice_id, sale_id, lines.analytics_id[0].name, refund, ws, xi, linea_der,
                                  linea_izq, seq, linea_izq_n, linea_izq_neg, view_style, linea_der_bold,
                                  view_style_out)
                    invoice = lines.invoice_id.id
                    xi += 1
                if invoice_ids:
                    self.set_body(invoice, sale_id, order, invoice_ids, ws, xi, linea_der, linea_izq, seq,
                                  linea_izq_n, linea_izq_neg, view_style, linea_der_bold, view_style_out)
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
        ws.col(10).width = 4200
        if self.account_analytic_id:
            ws.col(11).width = 6000
        else:
            ws.col(11).width = 4200
        ws.col(12).width = 3500
        if self.account_analytic_id:
            ws.col(13).width = 4000
            ws.col(14).width = 1500
            ws.col(15).width = 1500
        else:
            ws.col(13).width = 1500
            ws.col(14).width = 1500
            ws.col(15).width = 2500
        ws.col(16).width = 2500
        ws.col(17).width = 2500
        ws.col(18).width = 2500
        ws.col(19).width = 2500

        try:
            buf = cStringIO.StringIO()

            wb.save(buf)
            out = base64.encodestring(buf.getvalue())
            buf.close()
            res_model = 'sale.order.invoice.report'
            self.load_doc(out, data_file_name, res_model)

            return self.write({'data': out, 'txt_filename': data_file_name, 'name': 'ventas_facturas.xls'})

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

sale_order_invoice_report()
