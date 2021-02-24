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


class MoveRevisionStockReport(models.TransientModel):
    _name = 'move.revision.stock.report'
    _description = 'Reporte Stock'

    @api.onchange('select_mode')
    def control_purchase(self):
        if self.select_mode in ('purchase', 'import'):
            self.type = 'incoming'
        if self.select_mode == 'product':
            self.type = None

    date_from = fields.Date('Fecha Desde')
    date_to = fields.Date('Fecha Hasta')
    type_export = fields.Selection([('xls', 'EXCEL')], 'Tipo de archivo', required=True, default='xls')
    data = fields.Binary('Archivo', filters=None)
    path = fields.Char('Ruta')
    select_mode = fields.Selection([('purchase', 'Orden de compra'), ('import', 'Importacion'), ('product', 'Producto'),
                                    ('none', 'Ninguno')], 'Tipo', default='none')
    purchase_id = fields.Many2one('purchase.order', 'Orden de Compra',
                                  domain="[('type_purchase','=', 'product'), ('state', 'in', ('approved', 'done')),"
                                         "('picking_ids', '!=', False)]")
    importation_id = fields.Many2one('purchase.importation', 'Importacion',
                                     domain="[('state', 'in', ('transit', 'done')),"
                                            "('picking_ids', '!=', False)]")
    company_id = fields.Many2one('res.company', 'Compania')
    type = fields.Selection([('incoming', 'Ingresos'), ('outgoing', 'Salidas'), ('internal', 'Internos')],
                            'Tipo de Movimiento')
    state = fields.Selection([('pending', 'Pendiente'), ('done', 'Transferido')], 'Estado')
    product_id = fields.Many2one('product.product', 'Producto')

    @api.multi
    def set_header(self, ws, xi, style_header):

        ws.write(xi, 1, 'FECHA', style_header)
        ws.write(xi, 2, 'ORDEN', style_header)
        ws.write(xi, 3, 'EMPRESA', style_header)
        ws.write(xi, 4, 'CODIGO', style_header)
        ws.write(xi, 5, 'PRODUCTO', style_header)
        ws.write(xi, 6, 'DESCRIPCION', style_header)
        ws.write(xi, 7, 'ORIGEN', style_header)
        ws.write(xi, 8, 'DESTINO', style_header)
        ws.write(xi, 9, 'CANTIDAD', style_header)
        ws.write(xi, 10, 'STOCK', style_header)
        ws.write(xi, 11, 'REFERENCIA', style_header)
        ws.write(xi, 12, 'OBSERVACIONES', style_header)
        ws.write(xi, 13, 'ESTADO', style_header)
        col = 20
        return col

    @api.multi
    def get_state(self, state):
        estado = ''
        if state:
            if state == 'draft':
                estado = 'Borrador'
            if state == 'assigned':
                estado = 'Disponible'
            if state == 'confirmed':
                estado = 'Esperando disponibilidad'
            if state == 'waiting':
                estado = 'Esperando otro movimiento'
            if state == 'done':
                estado = 'Transferido'
            return estado

    @api.multi
    def set_body(self, orders, ws, xi, linea_izq, linea_izq_n):

        for order in orders:
            ws.write(xi, 1, order.date or '-', linea_izq)
            ws.write(xi, 2, order.picking_id.name or '-', linea_izq)
            ws.write(xi, 3, order.picking_id.partner_id.name or '-', linea_izq)
            ws.write(xi, 4, order.product_id.default_code or '-', linea_izq_n)
            ws.write(xi, 5, order.product_id.name or '-', linea_izq_n)
            ws.write(xi, 6, order.name or '-', linea_izq_n)
            ws.write(xi, 7, order.location_id.name or '-', linea_izq_n)
            ws.write(xi, 8, order.location_dest_id.name or '-', linea_izq_n)
            ws.write(xi, 9, order.product_qty or '0', linea_izq_n)
            ws.write(xi, 10, order.product_id.qty_available or '0', linea_izq_n)
            ws.write(xi, 11, order.picking_id.origin or '-', linea_izq_n)
            ws.write(xi, 12, order.picking_id.note or '-', linea_izq_n)
            ws.write(xi, 13, self.get_state(order.state) or '-', linea_izq_n)

    @api.multi
    def get_orders(self):

        date_from = self.date_from
        date_to = self.date_to
        stock_move = self.env['stock.move']
        domain = []

        if self.date_from > self.date_to:
            raise except_orm('Error !', 'Revise las fechas, la primera fecha no debe ser mayor a la segunda fecha !')
        if not self.select_mode == 'none':
            domain = []
        if self.select_mode == 'none':
            domain = [('date', '>=', date_from), ('date', '<=', date_to)]
        if self.select_mode == 'product':
            domain = [('product_id', '=', self.product_id.id)]
        if self.company_id:
            domain.append(('company_id', '=', self.company_id.id))
        if self.state == 'pending':
            domain.append(('state', 'in', ('draft', 'assigned', 'confirmed')))
        if not self.state:
            domain.append(('state', 'in', ('confirmed', 'assigned', 'draft', 'done')))
        if self.type == 'incoming':
            domain.append(('picking_id.picking_type_id', '=', 1))
        if self.type == 'outgoing':
            domain.append(('picking_id.picking_type_id', '=', 2))
        if self.type == 'internal':
            domain.append(('picking_id.picking_type_id', '=', 3))

        stock_move_data = stock_move.search(domain, order='date,picking_id')
        print "Lista", stock_move_data
        return stock_move_data

    @api.one
    def excel_action(self):
        wb = pycel.Workbook(encoding='utf-8')

        style_cabecera = pycel.easyxf('font: colour black, bold True;'
                                      'align: vertical center, horizontal center;')
        style_header = pycel.easyxf('font: bold True;'
                                    'align: vertical center, horizontal center, wrap on;'
                                    'borders: left 1, right 1, top 1, bottom 1;')
        linea_izq = pycel.easyxf('font: colour black, height 150;'
                                 'align: vertical center, horizontal left, wrap on;'
                                 'borders: left 1, right 1, top 1, bottom 1;')
        linea_izq_n = pycel.easyxf('font: colour black, height 140;'
                                   'align: vertical center, horizontal center, wrap on;'
                                   'borders: left 1, right 1, top 1, bottom 1;')

        ws = wb.add_sheet('Revision Stock')

        ws.show_grid = False
        ws.header_str = u"&LFecha de Impresion: &D Hora: &T&RPagina &P de &N"
        ws.footer_str = u""
        company = self.env['res.users'].browse(self._uid).company_id
        ws.write_merge(1, 1, 1, 5, company.name, style_cabecera)
        if self.select_mode == 'none':
            ws.write_merge(2, 2, 1, 5, 'Fecha desde: ' + self.date_from + ' - ' + 'Fecha hasta: ' +
                           self.date_to + ' ', style_cabecera)
        ws.write_merge(3, 3, 1, 5, 'REPORTE REVISION MOVIMIENTOS', style_cabecera)

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
        data_file_name = "revision_stock_report.xls"
        orders = self.get_orders()
        if self.select_mode == 'none':
            for order in orders:
                self.set_body(order, ws, xi, linea_izq, linea_izq_n)
                xi += 1
            if not orders:
                raise except_orm('Error!', 'No existe información a generar con este requerimiento')
        elif self.select_mode == 'purchase':
            if not self.purchase_id.picking_ids:
                raise except_orm('Error!', 'No existe información a generar con este requerimiento')
            for orders in self.purchase_id.picking_ids:
                for record in orders.move_lines:
                    self.set_body(record, ws, xi, linea_izq, linea_izq_n)
                    xi += 1
        elif self.select_mode == 'import':
            if not self.importation_id.picking_ids:
                raise except_orm('Error!', 'No existe información a generar con este requerimiento')
            for orders in self.importation_id.picking_ids:
                for record in orders.move_lines:
                    self.set_body(record, ws, xi, linea_izq, linea_izq_n)
                    xi += 1
        elif self.select_mode == 'product':
            for order in orders:
                self.set_body(order, ws, xi, linea_izq, linea_izq_n)
                xi += 1
            if not orders:
                raise except_orm('Error!', 'No existe información a generar con este requerimiento')

        ws.col(0).width = 500
        ws.col(1).width = 4000
        ws.col(2).width = 3800
        ws.col(3).width = 9000
        ws.col(4).width = 3200
        ws.col(5).width = 14000
        ws.col(6).width = 14000
        ws.col(7).width = 6000
        ws.col(8).width = 3500
        ws.col(9).width = 3000
        ws.col(10).width = 2000
        ws.col(11).width = 7000
        ws.col(12).width = 7000
        ws.col(13).width = 5000
        ws.row(5).height = 750

        try:
            buf = cStringIO.StringIO()
            wb.save(buf)
            out = base64.encodestring(buf.getvalue())
            buf.close()
            res_model = 'move.revision.stock.report'
            self.load_doc(out, data_file_name, res_model)
            return self.write({'data': out, 'txt_filename': data_file_name, 'name': 'reporte_revision_stock.xls'})
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


MoveRevisionStockReport()
