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
import xlwt
import xlwt as pycel
import base64
import cStringIO
from openerp.exceptions import except_orm
import re
import locale


class sale_order_states_report(models.TransientModel):
    _name = 'sale.order.states.report'
    _description = 'Reporte Orden'

    date_from = fields.Date('Fecha Desde')
    date_to = fields.Date('Fecha Hasta')
    type_export = fields.Selection([('xls', 'EXCEL')], 'Tipo de archivo', required=True, default='xls')
    data = fields.Binary('Archivo', filters=None)
    path = fields.Char('Ruta')
    company_id = fields.Many2one('res.company', 'Compania')
    partner_id = fields.Many2one('res.partner', 'Cliente', domain=[('customer', '=', True)])
    state = fields.Selection([('draft_manual', 'Cotización / Venta a Facturar'), ('progress', 'Facturada')
                              ], 'Estado Orden', required=True)
    out_ship = fields.Boolean('Incluir Salidas', default=False)

    @api.multi
    def set_header(self, ws, xi, style_header):

        ws.write(xi, 1, 'FECHA', style_header)
        ws.write(xi, 2, 'ORDEN', style_header)
        ws.write(xi, 3, 'COTIZACIÓN', style_header)
        ws.write(xi, 4, 'RUC', style_header)
        ws.write(xi, 5, 'CLIENTE', style_header)
        ws.write(xi, 6, 'FACTURA', style_header)
        ws.write(xi, 7, 'FECHA FACTURA', style_header)
        ws.write(xi, 8, 'ESTADO FACTURA', style_header)
        ws.write(xi, 9, 'BASE IVA', style_header)
        ws.write(xi, 10, 'IVA', style_header)
        ws.write(xi, 11, 'TOTAL', style_header)
        ws.write(xi, 12, 'ESTADO', style_header)
        ws.write(xi, 13, 'RESPONSABLE', style_header)
        if self.out_ship:
            ws.write(xi, 14, 'GUIA DE REMISION', style_header)
        col = 20
        return col

    @api.multi
    def get_state(self, state):
        estado = ''
        if state:
            if state == 'manual':
                estado = 'POR FACTURAR'
            if state in ('draft', 'sent'):
                estado = 'COTIZACIÓN'
            elif state in ('progress', 'done'):
                estado = 'FACTURADO'
            return estado

    @api.multi
    def get_invoice_state(self, state):
        estado = ''
        if state:
            if state == 'open':
                estado = 'CONTABILIZADA'
            if state == 'paid':
                estado = 'PAGADA'
            return estado

    @api.multi
    def set_body(self, orders, invoice, pick_name, ws, xi, linea_der, linea_izq, seq, linea_izq_n, linea_izq_neg, view_style, linea_der_bold
                 ,view_style_out):

        for order in orders:
            ws.write(xi, 1, order.date_order[:10], linea_izq)
            ws.write(xi, 2, order.name, linea_izq)
            ws.write(xi, 3, order.number_req, linea_izq)
            if not order.partner_id.part_number:
                raise except_orm('Error !',
                                 'Debe colocar el RUC para el cliente %s !' % order.partner_id.name)
            else:
                ws.write(xi, 4, '[' + order.partner_id.part_number + ']', linea_izq)
            ws.write(xi, 5, order.partner_id.name, linea_izq_n)
            if invoice:
                ws.write(xi, 6, invoice.number_reem, linea_izq_n)
                ws.write(xi, 7, invoice.date_invoice, linea_izq_n)
                ws.write(xi, 8, self.get_invoice_state(invoice.state), linea_izq_n)
                ws.write(xi, 9, float(round(order.amount_untaxed, 2)), linea_izq_n)
                ws.write(xi, 10, float(round(order.amount_tax, 2)), linea_izq_n)
                ws.write(xi, 11, float(round(order.amount_total, 2)), linea_izq_n)
            else:
                ws.write(xi, 6, '---', linea_izq_n)
                ws.write(xi, 7, '---', linea_izq_n)
                ws.write(xi, 8, '---', linea_izq_n)
                ws.write(xi, 9, float(round(order.amount_untaxed, 2)), linea_izq_n)
                ws.write(xi, 10, float(round(order.amount_tax, 2)), linea_izq_n)
                ws.write(xi, 11, float(round(order.amount_total, 2)), linea_izq_n)
            ws.write(xi, 12, self.get_state(order.state), linea_izq_n)
            ws.write(xi, 13, order.user_id.partner_id.name, linea_izq_n)
            if self.out_ship:
                ws.write(xi, 14, pick_name, linea_izq_n)

    @api.multi
    def get_orders(self):

        date_from = self.date_from
        date_to = self.date_to
        sale_order = self.env['sale.order']

        if self.date_from > self.date_to:
            raise except_orm('Error !', 'Revise las fechas, la primera fecha no debe ser mayor a la segunda fecha !')

        domain = [('date_order', '>=', date_from), ('date_order', '<=', date_to)]

        if self.company_id:
            domain.append(('company_id', '=', self.company_id.id))
        if self.partner_id:
            domain.append(('partner_id', '=', self.partner_id.id))
        if self.state == 'draft_manual':
            domain.append(('state', 'in', ('draft', 'sent', 'manual')))
        if self.state == 'progress':
            domain.append(('state', 'in', ('progress', 'done')))

        sale_order_data = sale_order.search(domain, order='partner_id,date_order')

        return sale_order_data

    @api.multi
    def get_state_name(self, state):
        pick_state = ''
        if state == 'done':
            pick_state = 'Realizado'
        else:
            pick_state = 'No realizado'
        return pick_state


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

        xi = 5  # Cabecera de Cliente
        self.set_header(ws, xi, style_header)
        xi += 1
        columns = [8, 9, 10]
        cell_formula = []
        formated_cell_formula = []
        cell_formula = ['SUBTOTAL(9,I%s:I{0})', 'SUBTOTAL(9,J%s:J{0})', 'SUBTOTAL(9,K%s:K{0})']
        total_formula = ['SUBTOTAL(9,I7:I{0})', 'SUBTOTAL(9,J7:J{0})', 'SUBTOTAL(9,K7:K{0})']
        data_file_name = "reporte_ventas.xls"
        seq = 0
        part_id = False
        orders = self.get_orders()
        invoice = False
        for item in cell_formula:
            formated_cell_formula.append(item % xi)
        for order in orders:
            pick_name = ''
            if self.out_ship:
                for pick in order.picking_ids:
                    if len(pick) > 1:
                        pick_name += pick.name + ' - ' + self.get_state_name(pick.state) + '/ '
                    else:
                        pick_name = pick.name + ' - ' + self.get_state_name(pick.state)
            if order and self.state == 'draft_manual' and order.date_confirm:
                if part_id != order.partner_id.id and part_id:
                    ws.write(xi, 7, 'SUBTOTAL', view_style)
                    ws.write(xi, columns[0], xlwt.Formula(formated_cell_formula[0].format(xi)), linea_der_bold)
                    ws.write(xi, columns[1], xlwt.Formula(formated_cell_formula[1].format(xi)), linea_der_bold)
                    ws.write(xi, columns[2], xlwt.Formula(formated_cell_formula[2].format(xi)), linea_der_bold)
                    xi += 1
                    part_id = order.partner_id.id
                    formated_cell_formula = []
                    for item in cell_formula:
                        formated_cell_formula.append(item % xi)
                elif part_id != order.partner_id.id and not part_id:
                    part_id = order.partner_id.id
                self.set_body(order, invoice, pick_name, ws, xi, linea_der, linea_izq, seq, linea_izq_n, linea_izq_neg, view_style,
                              linea_der_bold, view_style_out)
                xi += 1

            if order and self.state == 'progress':
                for invoice in order.invoice_ids:
                    if invoice.state not in ('cancel', 'invalidate'):
                        if part_id != order.partner_id.id and part_id:
                            ws.write(xi, 7, 'SUBTOTAL', view_style)
                            ws.write(xi, columns[0], xlwt.Formula(formated_cell_formula[0].format(xi)), linea_der_bold)
                            ws.write(xi, columns[1], xlwt.Formula(formated_cell_formula[1].format(xi)), linea_der_bold)
                            ws.write(xi, columns[2], xlwt.Formula(formated_cell_formula[2].format(xi)), linea_der_bold)
                            xi += 1
                            part_id = order.partner_id.id
                            formated_cell_formula = []
                            for item in cell_formula:
                                formated_cell_formula.append(item % xi)
                        elif part_id != order.partner_id.id and not part_id:
                            part_id = order.partner_id.id
                        self.set_body(order, invoice, pick_name, ws, xi, linea_der, linea_izq, seq, linea_izq_n, linea_izq_neg,
                                      view_style, linea_der_bold, view_style_out)
                        xi += 1

        ws.write(xi, 7, 'SUBTOTAL', view_style)
        ws.write(xi, columns[0], xlwt.Formula(formated_cell_formula[0].format(xi)), linea_der_bold)
        ws.write(xi, columns[1], xlwt.Formula(formated_cell_formula[1].format(xi)), linea_der_bold)
        ws.write(xi, columns[2], xlwt.Formula(formated_cell_formula[2].format(xi)), linea_der_bold)
        xi += 1

        ws.write(xi, 7, 'TOTAL', view_style)
        ws.write(xi, columns[0], xlwt.Formula(total_formula[0].format(xi)), linea_der_bold)
        ws.write(xi, columns[1], xlwt.Formula(total_formula[1].format(xi)), linea_der_bold)
        ws.write(xi, columns[2], xlwt.Formula(total_formula[2].format(xi)), linea_der_bold)

        ws.col(0).width = 500
        ws.col(1).width = 2700
        ws.col(2).width = 3800
        ws.col(3).width = 3800
        ws.col(4).width = 3200
        ws.col(5).width = 14000
        ws.col(6).width = 3500
        ws.col(7).width = 3500
        ws.col(8).width = 3500
        ws.col(9).width = 2000
        ws.col(10).width = 2000
        ws.col(11).width = 2000
        ws.col(12).width = 5000
        ws.col(13).width = 8000
        ws.col(14).width = 3000
        ws.col(15).width = 3000
        ws.col(16).width = 3000
        ws.row(5).height = 750

        try:
            buf = cStringIO.StringIO()

            wb.save(buf)
            out = base64.encodestring(buf.getvalue())
            buf.close()
            res_model = 'sale.order.states.report'
            self.load_doc(out, data_file_name, res_model)

            return self.write({'data': out, 'txt_filename': data_file_name, 'name': 'reporte_ventas.xls'})

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

sale_order_states_report()
