# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution - Ecuador
#    Copyright (C) 2019 MissionPetroleum Daniel Aldaz (<daldaz@mission-petroleum.com>).
#
##############################################################################

import base64
import cStringIO
from openerp import models, fields, api
from openerp.exceptions import except_orm
import xlwt
import xlwt as pycel


class purchase_importation_operations_report(models.TransientModel):
    _name = 'purchase.importation.operations.report'
    _description = 'Reporte Importaciones'

    date_from = fields.Date('Fecha Desde')
    date_to = fields.Date('Fecha Hasta')
    type_export = fields.Selection([('xls', 'EXCEL')], 'Tipo de archivo', required=True, default='xls')
    data = fields.Binary('Archivo', filters=None)
    path = fields.Char('Ruta')
    company_id = fields.Many2one('res.company', 'Compania')
    partner_id = fields.Many2one('res.partner', 'Proveedor', domain=[('supplier', '=', True)])
    type = fields.Selection([('draft', 'Borrador'), ('confirmed', 'Produccion'), ('international', 'Internacional'),
                             ('customs', 'Aduana'), ('transit', 'Transito'), ('cancel', 'Cancelado'),
                             ('done', 'Cerradas')], 'Estado')
    transport = fields.Selection([('marine', 'Maritimo'), ('earth', 'Terrestre'), ('plane', 'Aereo')],
                                 'Transporte' )
    destination = fields.Selection([('stock', 'Stock'), ('procura', 'Procura')])

    @api.multi
    def set_header(self, ws, xi, style_header):

        ws.write(xi, 1, 'FECHA', style_header)
        ws.write(xi, 2, 'REQUISICION', style_header)
        ws.write(xi, 3, 'REFERENCIA', style_header)
        ws.write(xi, 4, 'TIPO DE COMPRA', style_header)
        ws.write(xi, 5, 'CATEGORIA', style_header)
        ws.write(xi, 6, 'ORDEN DE COMPRA', style_header)
        ws.write(xi, 7, 'FECHA IMPORTACION', style_header)
        ws.write(xi, 8, 'IMPORTACION', style_header)
        ws.write(xi, 9, 'PROVEEDOR', style_header)
        ws.write(xi, 10, 'ESTADO', style_header)
        ws.write(xi, 11, 'TRANSPORTE', style_header)
        ws.write(xi, 12, 'PAGO', style_header)
        ws.write(xi, 13, 'ETD', style_header)
        ws.write(xi, 14, 'ETA', style_header)
        ws.write(xi, 15, 'ETBASE', style_header)
        col = 15
        return col

    @api.multi
    def get_states(self, state):
        estado = ''
        if state:
            if state == 'confirmed':
                estado = 'IMP. PRODUCCION'
            if state == 'customs':
                estado = 'ADUANA'
            if state == 'international':
                estado = 'T. INTERNACIONAL'
            if state == 'transit':
                estado = 'T. NACIONAL'
            if state == 'done':
                estado = 'CERRADA'
            if state == 'draft':
                estado = 'BORRADOR'
        return estado

    @api.multi
    def set_body(self, imports, purchase, category, imp, pick_date, invoice, ws, xi, linea_der, linea_izq, seq, linea_izq_n,
                 linea_izq_neg, view_style, linea_der_bold, view_style_out):

        for importation in imports:
            if purchase:
                ws.write(xi, 1, purchase.date_order[:10] or '', linea_izq)
                ws.write(xi, 2, purchase.number_req or '', linea_izq)
                ws.write(xi, 3, purchase.origin or '', linea_izq)
            else:
                ws.write(xi, 1, imp.date_order or '', linea_izq)
                ws.write(xi, 2, imp.name or '', linea_izq)
                ws.write(xi, 3, imp.name or '', linea_izq)
            ws.write(xi, 4, 'STOCK', linea_izq)
            ws.write(xi, 5, category or '', linea_izq)
            if purchase:
                ws.write(xi, 6, purchase.name or '', linea_izq)
            else:
                ws.write(xi, 6, imp.name or '', linea_izq)
            ws.write(xi, 7, importation.date_order or '', linea_izq)
            ws.write(xi, 8, importation.name or '', linea_izq)
            ws.write(xi, 9, importation.partner_id.name or '', linea_izq_n)
            ws.write(xi, 10, self.get_states(importation.state).upper() or '', linea_izq_n)
            ws.write(xi, 11, '', linea_izq_n)
            if invoice.state == 'paid' or invoice.residual == '0' and invoice.state == 'open':
                ws.write(xi, 12, 'Pagado', linea_izq_n)
            if invoice.residual < invoice.amount_total and invoice.state == 'open':
                ws.write(xi, 12, 'Pago Parcial', linea_izq_n)
            if invoice.residual == invoice.amount_total and invoice.state == 'open':
                ws.write(xi, 12, 'Ningún Pago', linea_izq_n)
            if invoice.state in ('invalidate', 'cancel'):
                ws.write(xi, 12, 'Factura Anulada', linea_izq_n)
            ws.write(xi, 13, importation.eta_date or '', linea_izq_n)
            ws.write(xi, 14, importation.etd_date or '', linea_izq_n)
            if pick_date:
                ws.write(xi, 15, pick_date[:10], linea_izq_n)
            else:
                ws.write(xi, 15, '', linea_izq_n)

    @api.multi
    def get_data(self):

        date_from = self.date_from
        date_to = self.date_to
        purchase_importation = self.env['purchase.importation']

        if self.date_from > self.date_to:
            raise except_orm('Error !',
                             'Revise las fechas, la primera fecha no debe ser mayor a la segunda fecha !')

        domain = [('date_order', '>=', date_from), ('date_order', '<=', date_to)]

        if self.company_id:
            domain.append(('company_id', '=', self.company_id.id))
        if self.partner_id:
            domain.append(('partner_id', '=', self.partner_id.id))
        if not self.type:
            domain.append(('state', '!=', 'cancel'))
        if self.type == 'transit':
            domain.append(('state', '=', 'transit'))
        if self.type == 'customs':
            domain.append(('state', '=', 'customs'))
        if self.type == 'international':
            domain.append(('state', '=', 'international'))
        if self.type == 'confirmed':
            domain.append(('state', '=', 'confirmed'))
        if self.type == 'done':
            domain.append(('state', '=', 'done'))
        if self.type == 'cancel':
            domain.append(('state', '=', 'cancel'))
        if self.type == 'draft':
            domain.append(('state', '=', 'draft'))
        importation_data = purchase_importation.search(domain, order='partner_id')

        return importation_data

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

        ws = wb.add_sheet('Reporte Importaciones')

        ws.show_grid = False
        ws.header_str = u"&LFecha de Impresion: &D Hora: &T&RPagina &P de &N"
        ws.footer_str = u""
        company = self.env['res.users'].browse(self._uid).company_id
        ws.write_merge(1, 1, 1, 5, company.name, style_cabecera)
        ws.write_merge(2, 2, 1, 5, 'Fecha desde: ' + self.date_from + ' - ' + 'Fecha hasta: ' + self.date_to + ' ',
                       style_cabecera)
        ws.write_merge(3, 3, 1, 5, 'REPORTE IMPORTACIONES', style_cabecera)

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

        xi = 6  # Cabecera de Cliente
        self.set_header(ws, xi, style_header)
        xi += 1
        data_file_name = "reporte_importaciones.xls"
        seq = 0
        orders = self.get_data()
        columns = [8, 9]
        total_formula = ['SUBTOTAL(9,I10:I{0})', 'SUBTOTAL(9,J10:J{0})']
        purchase_order_obj = self.env['purchase.order']
        purchase_order_line_obj = self.env['purchase.order.line']
        importation_order_obj = self.env['importation.order']
        importation_order_line_obj = self.env['importation.order.line']
        stock_move_obj = self.env['stock.move']
        stock_picking_obj = self.env['stock.picking']
        imp_invoice_id = False
        for importation in orders:
            for invoice in importation.invoice_ids:
                if invoice.partner_id.id == importation.partner_id.id:
                    imp_invoice_id = invoice[0]

            purchase_order = []
            purchase_order_line = []
            importation_order = []
            category = ''
            picking = ''
            data = []
            if not self.type:
                purchase_order = purchase_order_obj.search([('name', '=', importation.origin),
                                                            ('partner_id', '=', importation.id),
                                                            ('state', '!=', 'cancel')],
                                                           order='id')
            if self.type == 'transit':
                purchase_order = purchase_order_obj.search([('name', '=', importation.origin),
                                                            ('partner_id', '=', importation.id),
                                                            ('state', '=', 'transit')],
                                                           order='id')
            if self.type == 'customs':
                purchase_order = purchase_order_obj.search([('name', '=', importation.origin),
                                                            ('partner_id', '=', importation.id),
                                                            ('state', '=', 'customs')],
                                                           order='id')
            if self.type == 'international':
                purchase_order = purchase_order_obj.search([('name', '=', importation.origin),
                                                            ('partner_id', '=', importation.id),
                                                            ('state', '=', 'international')],
                                                           order='id')
            if self.type == 'confirmed':
                purchase_order = purchase_order_obj.search([('name', '=', importation.origin),
                                                            ('partner_id', '=', importation.id),
                                                            ('state', '=', 'confirmed')],
                                                           order='id')
            if self.type == 'done':
                purchase_order = purchase_order_obj.search([('name', '=', importation.origin),
                                                            ('partner_id', '=', importation.id),
                                                            ('state', '=', 'done')],
                                                           order='id')
            if self.type == 'cancel':
                purchase_order = purchase_order_obj.search([('name', '=', importation.origin),
                                                            ('partner_id', '=', importation.id),
                                                            ('state', '=', 'cancel')],
                                                           order='id')
            if not purchase_order:
                purchase_order = purchase_order_obj.search([('name', '=', importation.origin[:11])])
            if not purchase_order:
                purchase_order = purchase_order_obj.search([('name', '=', importation.origin[:15])])
            if not purchase_order:
                importation_order = importation_order_obj.search([('name', '=', importation.origin)])
            if purchase_order:
                purchase_order_line = purchase_order_line_obj.search([('order_id', '=', purchase_order.id)])
                if purchase_order_line:
                    category = purchase_order_line[0].product_id.categ_id.name
            if purchase_order:
                importation_order_line = importation_order_line_obj.search([('importation_id', '=', importation.id)])
                if importation_order_line:
                    stock_move = stock_move_obj.search([('importation_line_id', '=', importation_order_line[0].id)])
                    if stock_move:
                        picking = stock_move[0].picking_id.reception_date
            if imp_invoice_id:
                imp_invoice_id
            self.set_body(importation, purchase_order, category, importation_order, picking, imp_invoice_id, ws, xi, linea_der,
                          linea_izq, seq, linea_izq_n, linea_izq_neg, view_style, linea_der_bold, view_style_out)
            xi += 1

        ws.col(0).width = 1000
        ws.col(1).width = 2500
        ws.col(2).width = 4000
        ws.col(3).width = 9000
        ws.col(4).width = 2500
        ws.col(5).width = 9000
        ws.col(6).width = 4000
        ws.col(7).width = 4000
        ws.col(8).width = 9000
        ws.col(9).width = 11000
        ws.col(10).width = 4000
        ws.col(11).width = 4000
        ws.col(12).width = 2000
        ws.col(13).width = 2000
        ws.col(14).width = 2000
        ws.col(15).width = 2500
        ws.col(16).width = 2500
        ws.col(17).width = 2500
        ws.col(18).width = 2500
        ws.col(19).width = 2500
        ws.col(20).width = 2500
        ws.row(6).height = 600

        try:
            buf = cStringIO.StringIO()

            wb.save(buf)
            out = base64.encodestring(buf.getvalue())
            buf.close()
            res_model = 'purchase.importation.operations.report'
            self.load_doc(out, data_file_name, res_model)

            return self.write({'data': out, 'txt_filename': data_file_name, 'name': 'reporte_importacion.xls'})

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

purchase_importation_operations_report()
