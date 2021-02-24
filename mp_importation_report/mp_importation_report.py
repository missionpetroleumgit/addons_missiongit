# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution - Ecuador
#    Copyright (C) 2019 MissionPetroleum Daniel Aldaz (<daldaz@mission-petroleum.com>).
#
##############################################################################

import base64
import cStringIO
import xlwt as pycel
from openerp import models, fields, api
from openerp.exceptions import except_orm
import xlwt
import xlwt as pycel


class purchase_importation_order_report(models.TransientModel):
    _name = 'purchase.importation.order.report'
    _description = 'Reporte Importaciones'

    date_from = fields.Date('Fecha Desde')
    date_to = fields.Date('Fecha Hasta')
    type_export = fields.Selection([('xls', 'EXCEL')], 'Tipo de archivo', required=True, default='xls')
    data = fields.Binary('Archivo', filters=None)
    path = fields.Char('Ruta')
    company_id = fields.Many2one('res.company', 'Compania')
    partner_id = fields.Many2one('res.partner', 'Proveedor', domain=[('supplier', '=', True)])
    type = fields.Selection([('assigned', 'Transito'), ('done', 'Cerradas')], 'Tipo')

    @api.multi
    def set_header(self, ws, xi, style_header):

        ws.write(xi, 1, 'FECHA INGRESO', style_header)
        ws.write(xi, 2, 'FECHA IMPORTACION', style_header)
        ws.write(xi, 3, 'IMPORTACION', style_header)
        ws.write(xi, 4, 'PROVEEDOR', style_header)
        ws.write(xi, 5, 'CODIGO', style_header)
        ws.write(xi, 6, 'PRODUCTO', style_header)
        ws.write(xi, 7, 'UdM', style_header)
        ws.write(xi, 8, 'QTY', style_header)
        ws.write(xi, 9, 'COSTO', style_header)
        ws.write(xi, 10, 'TOTAL', style_header)
        ws.write(xi, 11, 'COSTO (+) INT', style_header)
        ws.write(xi, 12, 'TOTAL', style_header)
        ws.write(xi, 13, 'ESTADO', style_header)
        ws.write(xi, 14, 'INGRESO', style_header)
        col = 13
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
    def get_pick(self, line_id):
        importation_line_obj = self.env['importation.order.line']
        importation_line = importation_line_obj.search([('id', '=', line_id)])
        picking_name = ''
        if importation_line:
            for pick in importation_line.importation_id.picking_ids:
                if pick.state not in ('cancel', 'done'):
                    picking_name = pick.name
            if importation_line.importation_id.state != 'done' and importation_line.importation_id.picking_ids:
                for pick in importation_line.importation_id.picking_ids:
                    if pick.state not in ('cancel', 'done'):
                        picking_name = 'Abierta, ingreso aún no generado'
            elif importation_line.importation_id.state != 'done' and not importation_line.importation_id.picking_ids:
                picking_name = 'Abierta, ingreso aún no generado'
            #elif importation_line.importation_id.state == 'done' and importation_line.importation_id.picking_ids:
            #    for pick in importation_line.importation_id.picking_ids:
            #        if pick.state in ('cancel', 'done'):
            #           picking_name = 'Cerrada y no ingresada'
        return picking_name

    @api.multi
    def set_body(self, imports, lineas, moves, new_qty, ws, xi, linea_der, linea_izq, seq, linea_izq_n,
                 linea_izq_neg, view_style, linea_der_bold, view_style_out):
        if moves:
            ws.write(xi, 1, moves.date[:11], linea_izq)
            ws.write(xi, 2, imports.date_order, linea_izq)
            ws.write(xi, 3, imports.name, linea_izq)
            ws.write(xi, 4, imports.partner_id.name, linea_izq)
            ws.write(xi, 5, '[' + moves.product_id.default_code + ']', linea_izq)
            ws.write(xi, 6, moves.product_id.name, linea_izq)
            ws.write(xi, 7, moves.product_uom.name, linea_izq)
            ws.write(xi, 8, moves.product_qty, linea_izq)
            ws.write(xi, 9, moves.price_unit, linea_izq_n)
            ws.write(xi, 10, moves.product_qty * moves.price_unit, linea_izq_n)
            ws.write(xi, 11, moves.price_unit, linea_izq_n)
            ws.write(xi, 12, moves.product_qty * moves.price_unit, linea_izq_n)
            ws.write(xi, 13, self.get_states(imports.state).upper(), linea_izq_n)
            ws.write(xi, 14, moves.picking_id.name, linea_izq_n)
        else:
            ws.write(xi, 1, '', linea_izq)
            ws.write(xi, 2, imports.date_order, linea_izq)
            ws.write(xi, 3, imports.name, linea_izq)
            ws.write(xi, 4, imports.partner_id.name, linea_izq)
            ws.write(xi, 5, '[' + lineas.product_id.default_code + ']', linea_izq)
            ws.write(xi, 6, lineas.product_id.name, linea_izq)
            ws.write(xi, 7, lineas.product_uom.name, linea_izq)
            ws.write(xi, 8, new_qty, linea_izq)
            ws.write(xi, 9, lineas.price_unit, linea_izq_n)
            ws.write(xi, 10, new_qty * lineas.price_unit, linea_izq_n)
            ws.write(xi, 11, lineas.price_unit, linea_izq_n)
            ws.write(xi, 12, new_qty * lineas.price_unit, linea_izq_n)
            ws.write(xi, 13, self.get_states(imports.state).upper(), linea_izq_n)
            ws.write(xi, 14, self.get_pick(lineas.id), linea_izq_n)

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
            domain.append(('state', 'in', ('transit', 'customs', 'international', 'confirmed', 'done')))
        if self.type == 'done':
            domain.append(('state', '=', 'done'))
        if not self.type:
            domain.append(('state', 'in', ('transit', 'customs', 'international', 'confirmed', 'done')))
        importation_data = purchase_importation.search(domain, order='id')

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
        columns = [9, 10, 11, 12]
        total_formula = ['SUBTOTAL(9,J10:J{0})', 'SUBTOTAL(9,K10:K{0})', 'SUBTOTAL(9,L10:L{0})', 'SUBTOTAL(9,M10:M{0})']
        stock_move_obj = self.env['stock.move']
        importation_order_line = self.env['importation.order.line']
        for importation in orders:
            no_data = []
            prod_value = 0
            move_ids = ()
            moves = ()
            lines = ()
            if self.type == 'assigned':
                for lines in importation.order_lines:
                    data = []
                    new_lines = ()
                    prod_value = 0
                    tot_value = 0
                    sum_move = lines.product_qty
                    stock_move = ()
                    move = ()
                    move_ids = stock_move_obj.search([('importation_line_id', '=', lines.id),
                                                      ('product_id', '=', lines.product_id.id),
                                                      ('state', 'in', ('done', 'assigned', 'draft', 'confirmed'))],
                                                     order='importation_line_id')
                    for move in move_ids:
                        if move.importation_line_id.id == lines.id and move.product_id.id == lines.product_id.id:
                            if move.state == 'done':
                                tot_value += move.product_qty
                                print "Valor", tot_value
                                print "id", move.id
                                print "imp id", move.importation_line_id.id
                                print "total", sum_move
                            if tot_value == lines.product_qty:
                                no_data.append(lines.id)
                            else:
                                prod_value = sum_move - tot_value
                    if lines.id not in data and lines.id not in no_data and lines.product_id.type == 'product':
                        if importation.picking_ids:
                            if not importation.picking_ids[0].state == 'cancel':
                                data.append(lines.id)
                        else:
                            data.append(lines.id)
                        if prod_value == 0:
                            prod_value = lines.product_qty
                    if data and prod_value > 0:
                        new_lines = importation_order_line.search([('id', 'in', data)])
                        self.set_body(importation, new_lines, stock_move, prod_value, ws, xi, linea_der, linea_izq, seq,
                                      linea_izq_n, linea_izq_neg, view_style, linea_der_bold, view_style_out)
                        xi += 1
            if self.type == 'done':
                if importation.picking_ids:
                    for pick in importation.picking_ids:
                        for moves in pick.move_lines:
                            if moves.state == 'done':
                                self.set_body(importation, lines, moves, prod_value, ws, xi, linea_der, linea_izq, seq,
                                              linea_izq_n, linea_izq_neg, view_style, linea_der_bold, view_style_out)
                                xi += 1
            if not self.type:
                if importation.picking_ids:
                    for pick in importation.picking_ids:
                        for moves in pick.move_lines:
                            self.set_body(importation, lines, moves, prod_value, ws, xi, linea_der, linea_izq, seq,
                                          linea_izq_n, linea_izq_neg, view_style, linea_der_bold, view_style_out)
                            xi += 1
                for lines in importation.order_lines:
                    data = []
                    new_lines = ()
                    prod_value = 0
                    tot_value = 0
                    sum_move = lines.product_qty
                    stock_move = ()
                    move = ()
                    move_ids = stock_move_obj.search([('importation_line_id', '=', lines.id),
                                                      ('product_id', '=', lines.product_id.id),
                                                      ('state', 'in', ('done', 'assigned', 'draft', 'confirmed'))],
                                                     order='importation_line_id')
                    for move in move_ids:
                        if move.importation_line_id.id == lines.id and move.product_id.id == lines.product_id.id:
                            if move.state == 'done':
                                tot_value += move.product_qty
                                print "Valor", tot_value
                                print "id", move.id
                                print "imp id", move.importation_line_id.id
                                print "total", sum_move
                            if tot_value == lines.product_qty:
                                no_data.append(lines.id)
                            else:
                                prod_value = sum_move - tot_value
                    if lines.id not in data and lines.id not in no_data and lines.product_id.type == 'product':
                        if importation.picking_ids:
                            if not importation.picking_ids[0].state == 'cancel':
                                data.append(lines.id)
                        else:
                            data.append(lines.id)
                        if prod_value == 0:
                            prod_value = lines.product_qty
                    if data and prod_value > 0:
                        new_lines = importation_order_line.search([('id', 'in', data)])
                        self.set_body(importation, new_lines, stock_move, prod_value, ws, xi, linea_der, linea_izq, seq,
                                      linea_izq_n, linea_izq_neg, view_style, linea_der_bold, view_style_out)
                        xi += 1

        ws.write(xi, 7, 'TOTAL', view_style)
        ws.write(xi, columns[0], xlwt.Formula(total_formula[0].format(xi)), linea_der_bold)
        ws.write(xi, columns[1], xlwt.Formula(total_formula[1].format(xi)), linea_der_bold)
        ws.write(xi, columns[2], xlwt.Formula(total_formula[2].format(xi)), linea_der_bold)
        ws.write(xi, columns[3], xlwt.Formula(total_formula[3].format(xi)), linea_der_bold)

        ws.col(0).width = 1000
        ws.col(1).width = 2500
        ws.col(2).width = 4000
        ws.col(3).width = 11000
        ws.col(4).width = 11000
        ws.col(5).width = 3000
        ws.col(6).width = 14000
        ws.col(7).width = 3000
        ws.col(8).width = 1500
        ws.col(9).width = 3000
        ws.col(10).width = 3000
        ws.col(11).width = 3000
        ws.col(12).width = 3000
        ws.col(13).width = 3500
        ws.col(14).width = 6000
        ws.col(15).width = 1500
        ws.col(16).width = 2500
        ws.row(9).height = 750

        try:
            buf = cStringIO.StringIO()

            wb.save(buf)
            out = base64.encodestring(buf.getvalue())
            buf.close()
            res_model = 'purchase.importation.order.report'
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

purchase_importation_order_report()
