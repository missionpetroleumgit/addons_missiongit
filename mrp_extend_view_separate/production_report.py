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


class mrp_production_order_report(models.TransientModel):
    _name = 'mrp.production.order.report'
    _description = 'Reporte Produccion'

    date_from = fields.Date('Fecha Desde')
    date_to = fields.Date('Fecha Hasta')
    type_export = fields.Selection([('xls', 'EXCEL')], 'Tipo de archivo', required=True, default='xls')
    data = fields.Binary('Archivo', filters=None)
    path = fields.Char('Ruta')
    company_id = fields.Many2one('res.company', 'Compania')
    partner_id = fields.Many2one('res.partner', 'Cliente', domain=[('customer', '=', True)])
    type = fields.Selection([('process', 'Proceso'), ('finish', 'Terminadas')], 'Estado')
    production_id = fields.Many2one('mrp.production', 'Orden de Produccion')

    @api.multi
    def set_header(self, ws, xi, style_header):

        ws.write(xi, 1, 'PRODUCTO', style_header)
        ws.write(xi, 2, 'SERIE/LOTE', style_header)
        ws.write(xi, 3, 'ESTADO', style_header)
        col = 5
        return col

    @api.multi
    def get_states(self, state):
        mpr_state = ''
        if state:
            if state in ('draft', 'confirmed', 'ready', 'in_production'):
                mpr_state = 'PRODUCCION EN PROCESO'
            if state == 'done':
                mpr_state = 'TERMINADA'
        return mpr_state

    @api.multi
    def get_tracability(self, move_id):
        stock_pack_obj = self.env['stock.pack.operation'].search([('picking_id', '=', move_id.picking_id.id),
                                                                  ('product_id', '=', move_id.product_id.id)])
        no_serial = '---'
        if stock_pack_obj:
            return stock_pack_obj.lot_id.name
        else:
            return no_serial

    @api.multi
    def set_body(self, assy_moves, moves, count, ws, xi, linea_der, linea_izq, seq, linea_izq_n,
                 linea_izq_neg, view_style, linea_der_bold, view_style_out):
        if count == 1:
            ws.write(xi, 1, 'PRODUCTO: [' + assy_moves.product_id.default_code + '] ' + assy_moves.product_id.name_template, linea_izq_neg)
            xi += 1
            ws.write(xi, 1, 'CANTIDAD: ' + str(assy_moves.product_qty) + ' ' + assy_moves.product_id.uom_id.name, linea_izq_neg)
            xi += 1
            ws.write(xi, 1, 'SERIE: ' + str(self.get_tracability(assy_moves)), linea_izq_neg)
            xi += 1
            ws.write(xi, 1, 'ESTADO: ' + str(self.get_states(assy_moves.state)), linea_izq_neg)
            xi += 1
        for move in moves:
            ws.write(xi, 1, str(move.product_qty) + ' ' + str(move.product_id.uom_id.name) +
                     ' [' + move.product_id.default_code + '] '
                     + str(move.product_id.name_template), linea_izq)
            ws.write(xi, 2, self.get_tracability(move) or '-', linea_izq)
            ws.write(xi, 3, self.get_states(move.state), linea_izq)
            xi += 1

    @api.multi
    def get_data(self):
        date_from = self.date_from
        date_to = self.date_to
        mrp_production = self.env['mrp.production']
        domain = []
        if not self.production_id:
            if self.date_from > self.date_to:
                raise except_orm('Error !',
                                 'Revise las fechas, la primera fecha no debe ser mayor a la segunda fecha !')
            domain = [('date_planned', '>=', date_from, 'date_planned', '<=', date_to)]

        if self.production_id:
            domain.append(('id', '=', self.production_id.id))
        if self.partner_id and not self.production_id:
            domain.append(('partner_id', '=', self.partner_id.id))
        if self.type == 'type' and not self.production_id:
            domain.append(('state', 'in', ('draft', 'confirmed', 'ready', 'in_production')))
        if self.type == 'finish' and not self.production_id:
            domain.append(('state', '=', 'done'))
        if not self.type and not self.production_id:
            domain.append(('state', 'in', ('draft', 'confirmed', 'ready', 'in_production', 'done')))
        production_data = mrp_production.search(domain, order='id')
        return production_data

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

        ws = wb.add_sheet('Reporte Produccion')

        ws.show_grid = False
        ws.header_str = u"&LFecha de Impresion: &D Hora: &T&RPagina &P de &N"
        ws.footer_str = u""
        company = self.env['res.users'].browse(self._uid).company_id
        ws.write_merge(1, 1, 1, 5, company.name, style_cabecera)
        if not self.production_id:
            ws.write_merge(2, 2, 1, 5, 'Fecha desde: ' + self.date_from + ' - ' + 'Fecha hasta: ' + self.date_to + ' ',
                       style_cabecera)
        ws.write_merge(3, 3, 1, 5, 'REPORTE PRODUCCION', style_cabecera)

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
        data_file_name = "reporte_produccion.xls"
        seq = 0
        orders = self.get_data()
        # columns = [9, 10, 11, 12]
        # total_formula = ['SUBTOTAL(9,J10:J{0})', 'SUBTOTAL(9,K10:K{0})', 'SUBTOTAL(9,L10:L{0})', 'SUBTOTAL(9,M10:M{0})']
        stock_move_obj = self.env['stock.move']
        stock_pack_obj = self.env['stock.pack.operation']
        for mrp in orders:
            count = 0
            moves = ()
            if not self.type:
                moves_ids = stock_move_obj.search([('production_id', '=', mrp.id),
                                                   ('product_id', '=', mrp.product_id.id)],
                                                  order='id')
                assy_moves_ids = stock_move_obj.search([('production_id', '=', mrp.id),
                                                        ('product_id', '=', mrp.product_id.id)],
                                                       order='id', limit=1)
                count += 1
                if assy_moves_ids:
                    self.set_body(assy_moves_ids, moves, count, ws, xi, linea_der, linea_izq, seq,
                                  linea_izq_n, linea_izq_neg, view_style, linea_der_bold, view_style_out)
                    count += 1
                    xi += 4
                    if assy_moves_ids:
                        move_ids = []
                        pend_moves_ids = stock_move_obj.search([('raw_material_production_id', '=', mrp.id)],
                                                               order='id')
                        posconsume_moves_ids = stock_move_obj.search(
                            [('post_consum_raw_move_id', '=', mrp.id),
                             ], order='id')
                        for moves in pend_moves_ids:
                            if moves.id not in move_ids:
                                move_ids.append(moves.id)
                        for moves in posconsume_moves_ids:
                            if moves.id not in move_ids:
                                move_ids.append(moves.id)
                        print "moves", move_ids
                        stock_move_ids = stock_move_obj.search([('id', 'in', move_ids)])
                        self.set_body(assy_moves_ids, stock_move_ids, count, ws, xi, linea_der, linea_izq, seq,
                                      linea_izq_n, linea_izq_neg, view_style, linea_der_bold, view_style_out)
                        xi += 1
            if self.type == 'process':
                moves_ids = stock_move_obj.search([('production_id', '=', mrp.id),
                                                   ('state', 'in', ('assigned', 'draft', 'confirmed', 'waiting')),
                                                   ('product_id', '=', mrp.product_id.id)],
                                                  order='id')
                print "moves", moves_ids
                assy_moves_ids = stock_move_obj.search([('production_id', '=', mrp.id),
                                                        ('state', 'in', ('assigned', 'draft', 'confirmed', 'waiting')),
                                                        ('product_id', '=', mrp.product_id.id)],
                                                       order='id', limit=1)
                if assy_moves_ids:
                    self.set_body(assy_moves_ids, moves, ws, xi, linea_der, linea_izq, seq,
                                  linea_izq_n, linea_izq_neg, view_style, linea_der_bold, view_style_out)
                    xi += 1
                    print "xi", xi
                    if assy_moves_ids:
                        move_ids = []
                        pend_moves_ids = stock_move_obj.search([('raw_material_production_id', '=', assy_moves_ids.id),
                                                                ('state', 'in', ('assigned', 'draft', 'confirmed', 'waiting'))],
                                                               order='id')
                        ready_moves_ids = stock_move_obj.search([('raw_material_production_id', '=', assy_moves_ids.id),
                                                                 ('state', '=', 'done')], order='id')
                        posconsume_moves_ids = stock_move_obj.search([('post_consum_raw_move_id', '=', assy_moves_ids.id),
                                                                      ('state', 'in', ('assigned', 'draft', 'confirmed', 'waiting'))], order='id')
                        for moves in pend_moves_ids:
                            if moves.id not in move_ids:
                                move_ids.append(moves.id)
                        for moves in ready_moves_ids:
                            if moves.id not in move_ids:
                                move_ids.append(moves.id)
                        for moves in posconsume_moves_ids:
                            if moves.id not in move_ids:
                                move_ids.append(moves.id)

                        move_ids = tuple(move_ids)
                        stock_move_ids = stock_move_obj.search([('id', 'in', move_ids)])
                        self.set_body(assy_moves_ids, stock_move_ids, ws, xi, linea_der, linea_izq, seq,
                                      linea_izq_n, linea_izq_neg, view_style, linea_der_bold, view_style_out)
                        xi += 1
                        print "xi aqui", xi
            if self.type == 'finish':
                assy_moves_ids = stock_move_obj.search([('production_id', '=', mrp.id),
                                                        ('state', '=', 'done')],
                                                       order='id', limit=1)
                print "move end", assy_moves_ids
                self.set_body(assy_moves_ids, moves, ws, xi, linea_der, linea_izq, seq,
                              linea_izq_n, linea_izq_neg, view_style, linea_der_bold, view_style_out)
                prod_value = 0
                xi += 1
                if assy_moves_ids:
                    move_ids = []
                    pend_moves_ids = stock_move_obj.search([('raw_material_production_id', '=', assy_moves_ids.id),
                                                            ('state', '=', 'done')],
                                                           order='id')
                    ready_moves_ids = stock_move_obj.search([('raw_material_production_id', '=', assy_moves_ids.id),
                                                             ('state', '=', 'done')], order='id')
                    posconsume_moves_ids = stock_move_obj.search([('post_consum_raw_move_id', '=', assy_moves_ids.id),
                                                                  ('state', '=', 'done')], order='id')
                    for moves in pend_moves_ids:
                        if moves.id not in move_ids:
                            move_ids.append(moves.id)
                    for moves in ready_moves_ids:
                        if moves.id not in move_ids:
                            move_ids.append(moves.id)
                    for moves in posconsume_moves_ids:
                        if moves.id not in move_ids:
                            move_ids.append(moves.id)

                    move_ids = tuple(move_ids)
                    print "moves", move_ids
                    stock_move_ids = stock_move_obj.search([('id', 'in', move_ids)])

                    self.set_body(assy_moves_ids, stock_move_ids, ws, xi, linea_der, linea_izq, seq,
                                  linea_izq_n, linea_izq_neg, view_style, linea_der_bold, view_style_out)
                    xi += 1

        # ws.write(xi, 7, 'TOTAL', view_style)
        # ws.write(xi, columns[0], xlwt.Formula(total_formula[0].format(xi)), linea_der_bold)
        # ws.write(xi, columns[1], xlwt.Formula(total_formula[1].format(xi)), linea_der_bold)
        # ws.write(xi, columns[2], xlwt.Formula(total_formula[2].format(xi)), linea_der_bold)
        # ws.write(xi, columns[3], xlwt.Formula(total_formula[3].format(xi)), linea_der_bold)

        ws.col(0).width = 1000
        ws.col(1).width = 30500
        ws.col(2).width = 4000
        ws.col(3).width = 3000
        ws.col(4).width = 3000
        ws.col(5).width = 3000
        ws.col(6).width = 3000
        ws.col(7).width = 3000
        ws.col(8).width = 3000
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
            res_model = 'mrp.production.order.report'
            self.load_doc(out, data_file_name, res_model)

            return self.write({'data': out, 'txt_filename': data_file_name, 'name': 'reporte_produccion.xls'})

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


mrp_production_order_report()
