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


class purchase_importation_warehouse_report(models.TransientModel):
    _name = 'purchase.importation.warehouse.report'
    _description = 'Reporte Importaciones'

    date_from = fields.Date('Fecha Desde')
    date_to = fields.Date('Fecha Hasta')
    type_export = fields.Selection([('xls', 'EXCEL')], 'Tipo de archivo', required=True, default='xls')
    data = fields.Binary('Archivo', filters=None)
    path = fields.Char('Ruta')
    company_id = fields.Many2one('res.company', 'Compania')
    partner_id = fields.Many2one('res.partner', 'Proveedor', domain=[('supplier', '=', True)])
    type = fields.Selection([('draft', 'Borrador'), ('assigned', 'Transito'),
                             ('cancel', 'Cancelado'), ('done', 'Cerradas')], 'Tipo', required=True)

    @api.multi
    def set_header(self, ws, xi, style_header):

        ws.write(xi, 1, 'FECHA', style_header)
        ws.write(xi, 2, 'IMPORTACION', style_header)
        ws.write(xi, 3, 'PROVEEDOR', style_header)
        ws.write(xi, 4, 'CODIGO', style_header)
        ws.write(xi, 5, 'PRODUCTO', style_header)
        ws.write(xi, 6, 'UdM', style_header)
        ws.write(xi, 7, 'CANTIDAD', style_header)
        ws.write(xi, 8, 'PRECIO UNITARIO', style_header)
        ws.write(xi, 9, 'TOTAL', style_header)
        ws.write(xi, 10, 'ESTADO', style_header)
        ws.write(xi, 11, 'INGRESO', style_header)
        col = 7
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
    def set_body(self, imports, lineas, move, prod_cost, ws, xi, linea_der, linea_izq, seq, linea_izq_n, linea_izq_neg,
                 view_style, linea_der_bold, view_style_out):

        for importation in imports:
            ws.write(xi, 1, importation.date_order, linea_izq)
            ws.write(xi, 2, importation.name, linea_izq)
            ws.write(xi, 3, importation.partner_id.name, linea_izq)
            ws.write(xi, 4, '[' + lineas.product_id.default_code + ']', linea_izq)
            ws.write(xi, 5, lineas.product_id.name, linea_izq)
            ws.write(xi, 6, lineas.product_uom.name, linea_izq)
            ws.write(xi, 7, move.product_qty, linea_izq)
            ws.write(xi, 8, lineas.price_unit, linea_izq_n)
            # if moves.price_unit and qty:
            ws.write(xi, 9, (move.product_qty * lineas.price_unit), linea_izq_n)
            ws.write(xi, 10, self.get_states(lineas.importation_id.state).upper(), linea_izq_n)
            ws.write(xi, 11, move.picking_id.name, linea_izq_n)

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
        if self.type == 'assigned':
            domain.append(('state', 'in', ('transit', 'customs', 'international', 'confirmed')))
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

        xi = 9  # Cabecera de Cliente
        self.set_header(ws, xi, style_header)
        xi += 1
        data_file_name = "reporte_importaciones.xls"
        seq = 0
        orders = self.get_data()
        columns = [8, 9]
        total_formula = ['SUBTOTAL(9,I10:I{0})', 'SUBTOTAL(9,J10:J{0})']
        stock_move_obj = self.env['stock.move']
        for importation in orders:
            data = []
            for lines in importation.order_lines:
                prod_value = 0
                move_ids = ()
                if self.type in ('assigned', 'confirmed'):
                    move_ids = stock_move_obj.search([('importation_line_id', '=', lines.id),
                                                      ('product_id', '=', lines.product_id.id),
                                                      ('state', 'in', ('assigned', 'draft', 'confirmed'))], order='importation_line_id')
                if self.type == 'done':
                    move_ids = stock_move_obj.search([('importation_line_id', '=', lines.id),
                                                      ('product_id', '=', lines.product_id.id),
                                                      ('state', '=', 'done')],
                                                     order='importation_line_id')
                if self.type == 'cancel':
                    move_ids = stock_move_obj.search([('importation_line_id', '=', lines.id),
                                                      ('product_id', '=', lines.product_id.id),
                                                      ('state', '=', 'cancel')],
                                                     order='importation_line_id')

                for move in move_ids:
                    if move.importation_line_id.id == lines.id and lines.id not in data:
                        data.append(lines.id)
                        prod_value = move.product_qty
                        if move.importation_line_id == lines.id and lines.id in data:
                            prod_value += move.product_qty
                        self.set_body(importation, lines, move, prod_value, ws, xi, linea_der, linea_izq, seq,
                                      linea_izq_n, linea_izq_neg, view_style, linea_der_bold, view_style_out)
                        xi += 1
        ws.write(xi, 7, 'TOTAL', view_style)
        ws.write(xi, columns[0], xlwt.Formula(total_formula[0].format(xi)), linea_der_bold)
        ws.write(xi, columns[1], xlwt.Formula(total_formula[1].format(xi)), linea_der_bold)

        ws.col(0).width = 1000
        ws.col(1).width = 2500
        ws.col(2).width = 11000
        ws.col(3).width = 11000
        ws.col(4).width = 3000
        ws.col(5).width = 14000
        ws.col(6).width = 3000
        ws.col(7).width = 3000
        ws.col(8).width = 5000
        ws.col(9).width = 4000
        ws.col(10).width = 4200
        ws.col(11).width = 4200
        ws.col(12).width = 3500
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
            res_model = 'purchase.importation.warehouse.report'
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

purchase_importation_warehouse_report()
