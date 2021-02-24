# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution - Ecuador
#    Copyright (C) 2019 MissionPetroleum Daniel Aldaz (<daldaz@mission-petroleum.com>).
#
##############################################################################

from openerp import models, fields, api
import xlwt
import xlwt as pycel
import base64
import cStringIO
from openerp.exceptions import except_orm


class purchase_order_detail_report(models.TransientModel):
    _name = 'purchase.order.detail.report'
    _description = 'Reporte Compras Facturas'

    date_from = fields.Date('Fecha Desde')
    date_to = fields.Date('Fecha Hasta')
    type_export = fields.Selection([('xls', 'EXCEL')], 'Tipo de archivo', required=True, default='xls')
    data = fields.Binary('Archivo', filters=None)
    path = fields.Char('Ruta')
    company_id = fields.Many2one('res.company', 'Compania')
    partner_id = fields.Many2one('res.partner', 'Proveedor', domain=[('supplier', '=', True)])

    @api.multi
    def set_header(self, ws, xi, style_header):

        ws.write(xi, 1, 'ID FACTURA', style_header)
        ws.write(xi, 2, 'FECHA FACT.', style_header)
        ws.write(xi, 3, 'RUC', style_header)
        ws.write(xi, 4, 'NOMBRE', style_header)
        ws.write(xi, 5, 'TIPO', style_header)
        ws.write(xi, 6, 'FACTURA', style_header)
        ws.write(xi, 7, 'DOC', style_header)
        ws.write(xi, 8, 'EST.', style_header)
        ws.write(xi, 9, 'BASE 0', style_header)
        ws.write(xi, 10, 'BASE IVA', style_header)
        ws.write(xi, 11, 'IVA', style_header)
        ws.write(xi, 12, 'TOTAL', style_header)
        ws.write(xi, 13, '303', style_header)
        ws.write(xi, 14, '310', style_header)
        ws.write(xi, 15, '312', style_header)
        ws.write(xi, 16, '320', style_header)
        ws.write(xi, 17, '322', style_header)
        ws.write(xi, 18, '3440', style_header)
        ws.write(xi, 19, '332', style_header)
        ws.write(xi, 20, '721', style_header)
        ws.write(xi, 21, '723', style_header)
        ws.write(xi, 22, '725', style_header)
        ws.write(xi, 23, '729', style_header)
        ws.write(xi, 24, '731', style_header)
        ws.write(xi, 25, 'ESTADO', style_header)
        col = 13
        return col

    @api.multi
    def set_body(self, invoices, refund, code, ws, xi, linea_der, linea_izq,
                 seq, linea_izq_n, linea_izq_neg, view_style, linea_der_bold, view_style_out):

        for order in invoices:
            if not refund:
                ws.write(xi, 1, order.id, linea_izq)
                ws.write(xi, 2, order.date_invoice, linea_izq)
                ws.write(xi, 3, '[' + order.partner_id.part_number + ']', linea_izq)
                ws.write(xi, 4, order.partner_id.name, linea_izq_n)
                ws.write(xi, 5, 'DC', linea_izq)
                ws.write(xi, 6, order.number_reem, linea_der)
                ws.write(xi, 7, order.document_type.code, linea_izq_n)
                ws.write(xi, 8, order.authorization_id.serie_emission, linea_izq_n)
                if order.amount_iva == 0:
                    if order.state == 'invalidate':
                        ws.write(xi, 9, float(0), linea_izq_n)
                        ws.write(xi, 10, float(0), linea_izq_n)
                        ws.write(xi, 11, float(0), linea_izq_n)
                        ws.write(xi, 12, float(0), linea_izq_n)
                    else:
                        ws.write(xi, 9, float(order.amount_untaxed), linea_izq_n)
                        ws.write(xi, 10, float(0), linea_izq_n)
                        ws.write(xi, 11, float(0), linea_izq_n)
                        ws.write(xi, 12, float(order.amount_total), linea_izq_n)
                else:
                    ws.write(xi, 9, float(0), linea_izq_n)
                    if order.state == 'invalidate':
                        ws.write(xi, 10, float(0), linea_izq_n)
                        ws.write(xi, 11, float(0), linea_izq_n)
                        ws.write(xi, 12, float(0), linea_izq_n)
                    else:
                        ws.write(xi, 10, float(order.amount_untaxed), linea_izq_n)
                        ws.write(xi, 11, float(order.amount_iva), linea_izq_n)
                        ws.write(xi, 12, float(order.amount_total), linea_izq_n)
                ws.write(xi, 13, float(self.get_taxes(order)[0]) or float(0), linea_izq_n)
                ws.write(xi, 14, float(self.get_taxes(order)[1]) or float(0), linea_izq_n)
                ws.write(xi, 15, float(self.get_taxes(order)[2]) or float(0), linea_izq_n)
                ws.write(xi, 16, float(self.get_taxes(order)[3]) or float(0), linea_izq_n)
                ws.write(xi, 17, float(self.get_taxes(order)[4]) or float(0), linea_izq_n)
                ws.write(xi, 18, float(self.get_taxes(order)[5]) or float(0), linea_izq_n)
                ws.write(xi, 19, float(self.get_taxes(order)[6]) or float(0), linea_izq_n)
                ws.write(xi, 20, float(self.get_taxes(order)[7]) or float(0), linea_izq_n)
                ws.write(xi, 21, float(self.get_taxes(order)[8]) or float(0), linea_izq_n)
                ws.write(xi, 22, float(self.get_taxes(order)[9]) or float(0), linea_izq_n)
                ws.write(xi, 23, float(self.get_taxes(order)[10]) or float(0), linea_izq_n)
                ws.write(xi, 24, float(self.get_taxes(order)[11]) or float(0), linea_izq_n)
                ws.write(xi, 25, order.state_factelectro.upper(), linea_izq_n)
            else:
                ws.write(xi, 1, refund.id, linea_izq)
                ws.write(xi, 2, refund.date_invoice, linea_izq)
                ws.write(xi, 3, '[' + refund.partner_id.part_number + ']', linea_izq)
                ws.write(xi, 4, refund.partner_id.name, linea_izq_n)
                ws.write(xi, 5, 'DRC', linea_izq)
                ws.write(xi, 6, refund.number_reem, linea_der)
                ws.write(xi, 7, refund.document_type.code, linea_izq_n)
                ws.write(xi, 8, refund.authorization_id.serie_emission, linea_izq_n)
                if refund.amount_iva == 0:
                    ws.write(xi, 9, float(refund.amount_untaxed), linea_izq_n)
                    ws.write(xi, 10, float(0), linea_izq_n)
                    ws.write(xi, 11, float(0), linea_izq_n)
                    ws.write(xi, 12, float(refund.amount_total), linea_izq_n)
                else:
                    ws.write(xi, 9, float(0), linea_izq_n)
                    ws.write(xi, 10, float(refund.amount_untaxed), linea_izq_n)
                    ws.write(xi, 11, float(refund.amount_iva), linea_izq_n)
                    ws.write(xi, 12, float(refund.amount_total), linea_izq_n)
                ws.write(xi, 13, float(0), linea_izq_n)
                ws.write(xi, 14, float(0), linea_izq_n)
                ws.write(xi, 15, float(0), linea_izq_n)
                ws.write(xi, 16, float(0), linea_izq_n)
                ws.write(xi, 17, float(0), linea_izq_n)
                ws.write(xi, 18, float(0), linea_izq_n)
                ws.write(xi, 19, float(0), linea_izq_n)
                ws.write(xi, 20, float(0), linea_izq_n)
                ws.write(xi, 21, float(0), linea_izq_n)
                ws.write(xi, 22, float(0), linea_izq_n)
                ws.write(xi, 23, float(0), linea_izq_n)
                ws.write(xi, 24, float(0), linea_izq_n)
                ws.write(xi, 25, order.state_factelectro.upper(), linea_izq_n)

    @api.multi
    def get_invoices(self):

        date_from = self.date_from
        date_to = self.date_to
        account_invoice = self.env['account.invoice']
        if self.date_from > self.date_to:
            raise except_orm('Error !', 'Revise las fechas, la primera fecha no debe ser mayor a la segunda fecha !')

        domain = [('date_invoice', '>=', date_from), ('date_invoice', '<=', date_to),
                  ('state', 'in', ('open', 'paid')), ('type', '=', 'in_invoice'), ('is_importa', '=', False)]

        if self.company_id:
            domain.append(('company_id', '=', self.company_id.id))
        if self.partner_id:
            domain.append(('partner_id', '=', self.partner_id.id))

        account_invoice_data = account_invoice.search(domain, order='number_reem')

        return account_invoice_data

    @api.multi
    def get_taxes(self, invoice):
        v303 = v310 = v312 = v320 = v322 = v3440 = v332 = 0
        i721 = i723 = i725 = i729 = i731 = 0
        if invoice.deduction_id:
            for ret in invoice.deduction_id.tax_ids:
                if ret.tax_code_id.code == '303':
                    v303 = ret.amount * -1
                elif ret.tax_code_id.code == '310':
                    v310 = ret.amount * -1
                elif ret.tax_code_id.code == '312':
                    v312 = ret.amount * -1
                elif ret.tax_code_id.code == '320':
                    v320 = ret.amount * -1
                elif ret.tax_code_id.code == '322':
                    v322 = ret.amount * -1
                elif ret.tax_code_id.code in ('3440', '394'):
                    v3440 = ret.amount * -1
                elif ret.tax_code_id.code in ('332', '332G', '332I'):
                    v332 = ret.amount * -1
                elif ret.tax_code_id.code == '721':
                    i721 = ret.amount * -1
                elif ret.tax_code_id.code == '723':
                    i723 = ret.amount * -1
                elif ret.tax_code_id.code == '725':
                    i725 = ret.amount * -1
                elif ret.tax_code_id.code == '729':
                    i729 = ret.amount * -1
                elif ret.tax_code_id.code == '731':
                    i731 = ret.amount * -1
        return v303, v310, v312, v320, v322, v3440, v332, i721, i723, i725, i729, i731


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

        ws = wb.add_sheet('Reporte Compras')

        ws.show_grid = False
        ws.header_str = u"&LFecha de Impresion: &D Hora: &T&RPagina &P de &N"
        ws.footer_str = u""
        company = self.env['res.users'].browse(self._uid).company_id
        ws.write_merge(1, 1, 1, 5, company.name, style_cabecera)
        ws.write_merge(2, 2, 1, 5, 'Fecha desde: ' + self.date_from + ' - ' + 'Fecha hasta: ' + self.date_to + ' ', style_cabecera)
        ws.write_merge(3, 3, 1, 5, 'REPORTE FACTURAS COMPRAS', style_cabecera)

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

        columns = [9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24]
        total_formula = ['SUBTOTAL(9,J11:J{0})', 'SUBTOTAL(9,K11:K{0})', 'SUBTOTAL(9,L11:L{0})',
                         'SUBTOTAL(9,M11:M{0})', 'SUBTOTAL(9,N11:N{0})', 'SUBTOTAL(9,O11:O{0})',
                         'SUBTOTAL(9,P11:P{0})', 'SUBTOTAL(9,Q11:Q{0})', 'SUBTOTAL(9,R11:R{0})',
                         'SUBTOTAL(9,S11:S{0})', 'SUBTOTAL(9,T11:T{0})', 'SUBTOTAL(9,U11:U{0})',
                         'SUBTOTAL(9,V11:V{0})', 'SUBTOTAL(9,W11:W{0})', 'SUBTOTAL(9,X11:X{0})',
                         'SUBTOTAL(9,Y11:Y{0})']
        xi = 9  # Cabecera de Cliente
        self.set_header(ws, xi, style_header)
        xi += 1
        data_file_name = "reporte_compras_facturas.xls"
        seq = 0
        orders = self.get_invoices()
        refund = False
        account_invoice_obj = self.env['account.invoice']
        invoice_ids = account_invoice_obj.search([('type', '=', 'in_refund'),
                                                  ('date_invoice', '>=', self.date_from),
                                                  ('date_invoice', '<=', self.date_to)])
        data = []
        for invoice in orders:
            code =''
            if invoice.deduction_id:
                for ret in invoice.deduction_id.tax_ids:
                    code = ret.tax_code_id.code
            self.set_body(invoice, refund, code, ws, xi, linea_der,
                          linea_izq, seq, linea_izq_n, linea_izq_neg, view_style, linea_der_bold,
                          view_style_out)

            xi += 1
            for refund_id in invoice_ids:
                if refund_id.id not in data:
                    data.append(refund_id.id)
                    self.set_body(invoice, refund_id, ws, xi, linea_der, linea_izq, seq,
                                  linea_izq_n, linea_izq_neg, view_style, linea_der_bold, view_style_out)
                    xi += 1

        # LINE TOTAL GENERAL
        ws.write(xi, 8, 'TOTAL', view_style)
        ws.write(xi, columns[0], xlwt.Formula(total_formula[0].format(xi)), linea_der_bold)
        ws.write(xi, columns[1], xlwt.Formula(total_formula[1].format(xi)), linea_der_bold)
        ws.write(xi, columns[2], xlwt.Formula(total_formula[2].format(xi)), linea_der_bold)
        ws.write(xi, columns[3], xlwt.Formula(total_formula[3].format(xi)), linea_der_bold)
        ws.write(xi, columns[4], xlwt.Formula(total_formula[4].format(xi)), linea_der_bold)
        ws.write(xi, columns[5], xlwt.Formula(total_formula[5].format(xi)), linea_der_bold)
        ws.write(xi, columns[6], xlwt.Formula(total_formula[6].format(xi)), linea_der_bold)
        ws.write(xi, columns[7], xlwt.Formula(total_formula[7].format(xi)), linea_der_bold)
        ws.write(xi, columns[8], xlwt.Formula(total_formula[8].format(xi)), linea_der_bold)
        ws.write(xi, columns[9], xlwt.Formula(total_formula[9].format(xi)), linea_der_bold)
        ws.write(xi, columns[10], xlwt.Formula(total_formula[10].format(xi)), linea_der_bold)
        ws.write(xi, columns[11], xlwt.Formula(total_formula[11].format(xi)), linea_der_bold)
        ws.write(xi, columns[12], xlwt.Formula(total_formula[12].format(xi)), linea_der_bold)
        ws.write(xi, columns[13], xlwt.Formula(total_formula[13].format(xi)), linea_der_bold)
        ws.write(xi, columns[14], xlwt.Formula(total_formula[14].format(xi)), linea_der_bold)
        ws.write(xi, columns[15], xlwt.Formula(total_formula[15].format(xi)), linea_der_bold)

        ws.col(0).width = 100
        ws.col(1).width = 3500
        ws.col(2).width = 3500
        ws.col(3).width = 3500
        ws.col(4).width = 10000
        ws.col(5).width = 2000
        ws.col(6).width = 4500
        ws.col(7).width = 2000
        ws.col(8).width = 2000
        ws.col(9).width = 2000
        ws.col(10).width = 2500
        ws.col(11).width = 2500
        ws.col(12).width = 2500
        ws.col(13).width = 2500
        ws.col(14).width = 2500
        ws.col(15).width = 2500
        ws.col(16).width = 2500
        ws.col(17).width = 2500
        ws.col(18).width = 2500
        ws.col(19).width = 2500
        ws.col(20).width = 2500
        ws.col(21).width = 2500
        ws.col(22).width = 2500
        ws.col(23).width = 2500
        ws.col(24).width = 2500
        ws.col(25).width = 4000

        try:
            buf = cStringIO.StringIO()

            wb.save(buf)
            out = base64.encodestring(buf.getvalue())
            buf.close()
            res_model = 'purchase.order.detail.report'
            self.load_doc(out, data_file_name, res_model)

            return self.write({'data': out, 'txt_filename': data_file_name, 'name': 'ventas_facturas.xls'})

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

purchase_order_detail_report()
