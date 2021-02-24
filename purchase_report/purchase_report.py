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
from datetime import datetime
import locale
from openerp import models, fields, api
from openerp.exceptions import except_orm
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT as DSTF


class PurchaseReportF4(models.TransientModel):
    _name = 'purchase.report.ffour'
    _description = 'Purchase Report'

    date_from = fields.Date('Fecha Desde', required=True)
    date_to = fields.Date('Fecha Hasta', required=True)
    type_export = fields.Selection([('xls', 'EXCEL')], 'Tipo de archivo', required=True, default='xls')
    data = fields.Binary('Archivo', filters=None)
    path = fields.Char('Ruta')
    company_id = fields.Many2one('res.company', 'Compania', readonly=True)
    partner_ids = fields.Many2many('res.partner', string='Proveedor', domain=[('supplier', '=', True)])
    type = fields.Selection([('product', 'Productos'), ('service', 'Servicios'),
                             ('prod_consu', 'Consumibles/Productos')], 'Tipo de compra')
    d_type = fields.Selection([('internal', 'Nacional'), ('importation', 'Importacion')], 'Tipo', required=True)
    region = fields.Selection([('coast', 'Costa'), ('sierra', 'Sierra'),
                               ('east', 'Oriente'), ('inter', 'Internacional')], 'Region', required=True)

    @api.multi
    def set_header(self, ws, xi, style_header):
        ws.write(xi, 1, 'Secuencia', style_header)
        ws.write(xi, 2, 'Nombre Proveedor', style_header)
        ws.write(xi, 3, 'RUC', style_header)
        ws.write(xi, 4, 'Telefono', style_header)
        ws.write(xi, 5, 'Servicio Prestado', style_header)
        ws.write(xi, 6, 'Categorizacion del servicio', style_header)
        ws.write(xi, 7, 'Fecha Inicio', style_header)
        ws.write(xi, 8, 'Status Prestacion', style_header)
        ws.write(xi, 9, 'Fecha Fin Servicio', style_header)
        ws.write(xi, 10, 'Monto Mensual Facturado', style_header)
        ws.write(xi, 11, 'Region', style_header)
        ws.write(xi, 12, 'Parroquia', style_header)
        ws.write(xi, 13, 'Provincia', style_header)
        ws.write(xi, 14, 'Canton', style_header)
        ws.write(xi, 15, 'Direccion', style_header)
        ws.write(xi, 16, 'Proyecto', style_header)
        col = 15
        return col

    @api.multi
    def get_total_amount_by_partner(self, partner):
        if partner:
            date_from = self.date_from
            date_to = self.date_to
            amount = 0
            purchase_order = self.env['purchase.order']
            domain = [('date_order', '>=', date_from), ('date_order', '<=', date_to),
                      ('state', 'in', ('approved', 'done')), ('partner_id', '=', partner)]
            purchase_order_data = purchase_order.search(domain)
            if purchase_order_data:
                for orders in purchase_order_data:
                    amount += orders.amount_total
            return amount

    @api.multi
    def set_body(self, orders, ws, xi, linea_der, linea_izq, seq, linea_izq_n, view_style):
        locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
        for order in orders:
            ws.write(xi, 1, seq, linea_der)
            ws.write(xi, 2, order.partner_id.name, linea_izq)
            ws.write(xi, 3, order.partner_id.part_number or '-', linea_izq)
            ws.write(xi, 4, order.partner_id.phone, linea_izq)
            ws.write(xi, 5, order.partner_id.service_type, linea_der)
            ws.write(xi, 6, order.partner_id.service_categ or '-', linea_izq_n)
            ws.write(xi, 7, '-', linea_izq_n)
            ws.write(xi, 8, 'FINALIZADO', linea_izq_n)
            ws.write(xi, 9, '-', view_style)
            ws.write(xi, 10, locale.currency(self.get_total_amount_by_partner(order.partner_id.id),
                                             grouping=True), view_style)
            ws.write(xi, 11, order.partner_id.region or '-', linea_izq_n)
            ws.write(xi, 12, order.partner_id.parish_id.name or '-', linea_izq_n)
            ws.write(xi, 13, order.partner_id.canton_id.name or '-', linea_izq_n)
            ws.write(xi, 14, order.partner_id.parish_id.name or '-', linea_izq_n)
            if order.partner_id.street and order.partner_id.street2:
                ws.write(xi, 15, order.partner_id.street + ' ' + order.partner_id.street2, linea_izq_n)
            elif order.partner_id.street and not order.partner_id.street2:
                ws.write(xi, 15, order.partner_id.street, linea_izq_n)
            else:
                ws.write(xi, 15, '-', linea_izq_n)
            ws.write(xi, 16, 'PETROAMAZONAS', linea_izq_n)

    @api.multi
    def get_partners_type(self):
        self._cr.execute('SELECT DISTINCT(p.id) as id\
                    FROM res_partner p\
                    JOIN purchase_order po ON (po.partner_id=p.id)\
                    WHERE po.state IN (\'approved\', \'done\')\
                    AND (p.region=%s)\
                    AND (po.destination=%s)\
                    AND (po.type_purchase IN (\'service\', \'consu\', \'product\'))\
                    AND (po.date_order between %s and %s)\
                    ORDER BY id', (self.region, self.d_type, self.date_from, self.date_to))
        partners = self._cr.dictfetchall()
        partner_ids = [x['id'] for x in partners]
        return partner_ids

    @api.multi
    def get_partners_prod(self):
        self._cr.execute('SELECT DISTINCT(p.id) as id\
                    FROM res_partner p\
                    JOIN purchase_order po ON (po.partner_id=p.id)\
                    WHERE po.state IN (\'approved\', \'done\')\
                    AND (p.region=%s)\
                    AND (po.destination=%s)\
                    AND (po.type_purchase IN (\'consu\', \'product\'))\
                    AND (po.date_order between %s and %s)\
                    ORDER BY id', (self.region, self.d_type, self.date_from, self.date_to))
        partners = self._cr.dictfetchall()
        partner_ids = [x['id'] for x in partners]
        return partner_ids

    @api.multi
    def get_partners(self):
        self._cr.execute('SELECT DISTINCT(p.id) as id\
                    FROM res_partner p\
                    JOIN purchase_order po ON (po.partner_id=p.id)\
                    WHERE po.state IN (\'approved\', \'done\')\
                    AND (p.region=%s)\
                    AND (po.destination=%s)\
                    AND (po.type_purchase=%s)\
                    AND (po.date_order between %s and %s)\
                    ORDER BY id', (self.region, self.d_type, self.type, self.date_from, self.date_to))
        partners = self._cr.dictfetchall()
        partner_ids = [x['id'] for x in partners]
        return partner_ids

    @api.multi
    def get_orders(self):

        date_from = self.date_from
        date_to = self.date_to
        purchase_order = self.env['purchase.order']
        partner_ids = []

        if self.date_from > self.date_to:
            raise except_orm('Error !', 'Revise las fechas, la primera fecha no debe ser mayor a la segunda fecha !')

        domain = [('date_order', '>=', date_from), ('date_order', '<=', date_to),
                  ('state', 'in', ('approved', 'done'))]
        if self.company_id:
            domain.append(('company_id', '=', self.company_id.id))
        if self.d_type:
            domain.append(('destination', '=', self.d_type))
        if self.type in ('product', 'service'):
            domain.append(('type_purchase', '=', self.type))
        if self.type == 'consu_prod':
            domain.append(('type_purchase', 'in', ('product', 'consu')))
        if self.partner_ids:
            domain.append(('partner_id', 'in', [part.id for part in self.partner_ids]))
        if not self.partner_ids and self.type in ('product', 'service'):
            partner_ids = self.get_partners()
        if not self.partner_ids and not self.type:
            partner_ids = self.get_partners_type()
        if not self.partner_ids and self.type == 'prod_consu':
            partner_ids = self.get_partners_prod()
        domain.append(('partner_id', 'in', partner_ids))
        purchase_order_data = purchase_order.search(domain, order='partner_id')

        return purchase_order_data

    @api.one
    def excel_action(self):
        wb = pycel.Workbook(encoding='utf-8')

        style_cabecera = pycel.easyxf('font: colour black, bold True;'
                                      'align: vertical center, horizontal center;'
                                      )

        style_header = pycel.easyxf('font: bold True;'
                                    'align: vertical center, horizontal center, wrap on;'
                                    'borders: left 1, right 1, top 1, bottom 1;')

        view_style = pycel.easyxf('font: colour blue, bold true, height 170;'
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
        linea_der = pycel.easyxf('font: colour black, height 150;'
                                 'align: vertical center, horizontal right;'
                                 'borders: left 1, right 1, top 1, bottom 1;'
                                 )

        ws = wb.add_sheet('REPORTE F4')

        ws.show_grid = False
        ws.header_str = u"&LFecha de Impresion: &D Hora: &T&RPagina &P de &N"
        ws.footer_str = u""
        company = self.env['res.users'].browse(self._uid).company_id
        ws.write_merge(1, 1, 1, 5, company.name, style_cabecera)
        ws.write_merge(2, 2, 1, 5, 'Direccion: ' + company.partner_id.street, style_cabecera)
        ws.write_merge(3, 3, 1, 5, 'Ruc: ' + company.partner_id.part_number, style_cabecera)
        ws.write_merge(5, 5, 1, 5, 'Fecha:' + ' ' + datetime.today().strftime('%Y-%m-%d'), style_cabecera)
        ws.write_merge(6, 6, 1, 5, 'Reporte', style_cabecera)

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

        xi = 8  # Cabecera de Cliente
        self.set_header(ws, xi, style_header)
        xi += 1
        data_file_name = "formularioF4_%s.xls" % datetime.now().strftime(DSTF)
        orders = self.get_orders()
        seq = 0
        partners = []
        for order in orders:
            if order.partner_id.id:
                if seq == 0:
                    partners.append(order.partner_id.id)
                    seq = 1
                if order.partner_id.id not in partners:
                    partners.append(order.partner_id.id)
                    self.set_body(order, ws, xi, linea_der, linea_izq, seq, linea_izq_n, view_style)
                    seq += 1
                    xi += 1
        if len(partners) == 1:
            self.set_body(orders[0], ws, xi, linea_der, linea_izq, seq, linea_izq_n, view_style)

        ws.col(0).width = 500
        ws.col(1).width = 2500
        ws.col(2).width = 9900
        ws.col(3).width = 7000
        ws.col(4).width = 8000
        ws.col(5).width = 5000
        ws.col(6).width = 5000
        ws.col(7).width = 5000
        ws.col(8).width = 5000
        ws.col(9).width = 5500
        ws.col(10).width = 6500
        ws.col(11).width = 6500
        ws.col(12).width = 5000
        ws.col(13).width = 4500
        ws.col(14).width = 9000
        ws.col(15).width = 6500
        ws.col(16).width = 5500
        ws.col(17).width = 3500
        ws.row(8).height = 750

        try:
            buf = cStringIO.StringIO()

            wb.save(buf)
            out = base64.encodestring(buf.getvalue())
            buf.close()
            res_model = 'purchase.report.ffour'
            self.load_doc(out, data_file_name, res_model)

            return self.write({'data': out, 'txt_filename': data_file_name, 'name': 'reportef4.xls'})

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

PurchaseReportF4()
