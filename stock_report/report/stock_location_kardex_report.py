# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp.osv import fields, osv
import base64
import cStringIO
import time
import xlwt
import datetime
import xlwt as pycel


class stock_location_real_inventory(osv.Model):
    _name = "stock.location.real.inventory"
    _description = 'Reporte Inventario Bodegas'

    def get_lines_report_wage(self, cr, uid, form):
        res = []
        date_from = form.get('date_from', False)
        company = form.get('company_id', False)
        location = form.get('location_id', False)
        prod_obj = self.pool.get('product.product')
        stoc_mov_obj = self.pool.get('stock.move')
        prod_qty_obj = self.pool.get('stock.quant')
        location_obj = self.pool.get('stock.location')
        move_state = ['done']
        product_type = 'product'
        rep_products = 'rpr'
        if not location:
            location = location_obj.search(cr, uid, [('usage', '=', 'internal'), ('id', '!=', 12)], order='id asc',
                                           context=None)
            print "locks", location
            location_ids = location_obj.browse(cr, uid, location, context=None)
            cr.execute('SELECT DISTINCT p.id AS id \
                        FROM product_product p, stock_move AS s, product_template t, stock_location l \
                        WHERE (p.id=s.product_id) \
                            AND (p.product_tmpl_id = t.id) \
                            AND (l.id = s.location_id) \
                            AND (s.location_id IN %s) \
                            AND (t.type = %s) \
                            AND (p.default_code not ilike %s) \
                            AND (p.active = True) \
                            AND (s.state IN %s) \
                            AND (s.date <= %s) \
                            ORDER BY p.id',
                       (tuple(location), product_type, rep_products, tuple(move_state), date_from))
            products = cr.dictfetchall()
            print "primer grupo", products
            products_ids = [x['id'] for x in products]
            cr.execute('SELECT DISTINCT p.id AS id \
                        FROM product_product p, stock_move AS s, product_template t, stock_location l \
                        WHERE (p.id=s.product_id) \
                            AND (p.product_tmpl_id = t.id) \
                            AND (l.id = s.location_dest_id) \
                            AND (s.location_dest_id IN %s) \
                            AND (t.type = %s) \
                            AND (p.default_code not ilike %s) \
                            AND (p.active = True) \
                            AND (s.state IN %s) \
                            AND (s.date <= %s) \
                            ',
                       (tuple(location), product_type, rep_products, tuple(move_state), date_from))
            products = cr.dictfetchall()
            print "segundo grupo", products
            products_ids = [x['id'] for x in products]
            if not products_ids:
                return []
            prod_prod_data = prod_obj.browse(cr, uid, products_ids)
        else:
            warehouse = location[0]
            cr.execute('SELECT DISTINCT p.id AS id \
                        FROM product_product p, stock_move AS s, product_template t, stock_location l \
                        WHERE (p.id=s.product_id) \
                            AND (p.product_tmpl_id = t.id) \
                            AND (l.id = s.location_id) \
                            AND (l.id = %s) \
                            AND (t.type = %s) \
                            AND (p.default_code not ilike %s) \
                            AND (p.active = True) \
                            AND (s.state IN %s) \
                            AND (s.date <= %s)\
                            ',
                       (warehouse, product_type, rep_products, tuple(move_state), date_from))
            products = cr.dictfetchall()
            products_ids = [x['id'] for x in products]
            if not products_ids:
                return []
            prod_prod_data = prod_obj.browse(cr, uid, products_ids)
        sec = 1
        sec_0 = 1
        sec_n = 1
        product = False
        location = location_obj.search(cr, uid, [('usage', '=', 'internal'), ('id', '!=', 12)], order='id asc',
                                       context=None)
        location_ids = location_obj.browse(cr, uid, location, context=None)
        for prod in prod_prod_data:
            old_qty = 0.00
            old_value = 0.00
            qty_val = False
            move_qty = 0.00
            stock_mov_ids = stoc_mov_obj.search(cr, uid,
                                                [('product_id', '=', prod.id),
                                                 ('date', '<=', date_from), ('company_id', '=', company[0]),
                                                 ('state', '=', 'done')],
                                                order='location_id asc')
            if len(stock_mov_ids) > 0:
                stock_mov_data = stoc_mov_obj.browse(cr, uid, stock_mov_ids)
                data_rev = []
                for warehouse in location_ids:
                    for moves in stock_mov_data:
                        costo = 0.00
                        if warehouse.id == moves.location_id.id or warehouse.id == moves.location_dest_id.id:
                            if product and product != moves.product_id.id:
                                data_rev.append(moves.product_id.id)
                                data['sec'] = sec
                                data['qty_sum'] = qty_sum
                                data['sum_value'] = sum_value
                                data['prod_name'] = name
                                data['cod_name'] = '[' + code + ']'
                                data['uom'] = udm
                                data['ident'] = ident
                                data['bodega'] = bodega
                                data['origin'] = origin
                                data['ref'] = ref
                                data['date'] = date
                                if qty_sum > 0:
                                    data['prom'] = round(sum_value / qty_sum, 2)
                                else:
                                    data['prom'] = sum_value
                                sec += 1
                                res.append(data)

                            if prod.id == moves.product_id.id and moves.product_id.type == 'product' and moves.product_id.active:
                                product = True
                                # CSV:CASOS MOVIMIENTOS
                                data = {}
                                origin = moves.location_id.usage
                                destiny = moves.location_dest_id.usage
                                prod_name = moves.product_id.name or ''
                                internal = moves.location_id.usage == 'internal'
                                dest_internal = moves.location_dest_id.usage == 'internal'
                                if moves.product_id.default_code:
                                    cod_name = '[' + moves.product_id.default_code + ']'
                                else:
                                    cod_name = ''
                                uom = moves.product_id.uom_id.name

                                if origin == 'internal' and destiny == 'customer' and moves.location_id.id != 12 and internal:
                                    tipo = 'VENTA'
                                    if moves.state == 'done':
                                        qty_sum = round(old_qty - moves.product_qty, 2)
                                        #  costo = round(prom_cost, 2)
                                        sum_value = round(old_value - (costo * moves.product_qty), 2)
                                        if qty_sum == 0:
                                            sum_value = 0
                                        last_cost = costo
                                        move_qty = move_qty - moves.product_qty

                                if origin == 'customer' and destiny == 'internal' and moves.location_dest_id.id != 12 and dest_internal:
                                    tipo = 'RETORNO'
                                    if moves.state == 'done':
                                        qty_sum = round(old_qty + moves.product_qty, 2)
                                        #  costo = round(last_cost, 2)
                                        sum_value = round(old_value + (costo * moves.product_qty), 2)
                                        move_qty += moves.product_qty

                                elif origin == 'internal' and moves.location_id.id == 12 and destiny == 'internal' and dest_internal:
                                    tipo = 'INTERNO'
                                    if moves.state == 'done':
                                        qty_sum = round(old_qty + moves.product_qty, 2)
                                        # costo = round(prom_cost, 2)
                                        sum_value = round(old_value - (costo * moves.product_qty), 2)
                                        last_cost = costo
                                        if qty_sum == 0:
                                            sum_value = 0
                                        move_qty += moves.product_qty

                                elif origin == 'internal' and destiny == 'internal' and moves.location_dest_id.id == 12 and internal:
                                    tipo = 'RETORNO'
                                    if moves.state == 'done':
                                        qty_sum = round(old_qty - moves.product_qty, 2)
                                        #  costo = round(last_cost, 2)
                                        sum_value = round(old_value - (costo * moves.product_qty), 2)
                                        move_qty = move_qty - moves.product_qty

                                if not qty_val:
                                    old_qty = qty_sum
                                    old_value = sum_value
                                    qty_val = True
                                else:
                                    old_qty = qty_sum
                                    old_value = sum_value
                                product = moves.product_id.id
                                name = moves.product_id.name_template
                                code = moves.product_id.default_code
                                udm = moves.product_id.uom_id.name
                                ident = moves.product_id.id
                                bodega = warehouse.name
                                origin = moves.picking_id.note
                                ref = moves.picking_id.origin
                                date = moves.date
                    # move_qty = move_qty
                    # data['move_qty'] = move_qty
        return res

    def _format_date(self, date):
        if date:
            campos = date.split('-')
            date = datetime.date(int(campos[0]), int(campos[1]), int(campos[2]))
            return date

    def get_days(self, cr, uid, date_start, date_now):
        # date_now = time.strftime("%Y-%m-%d")
        days = (self._format_date(date_now) - self._format_date(date_start)).days
        return days

    def get_days_before(self, cr, uid, date_start, date_stop):
        days = (self._format_date(date_stop) - self._format_date(date_start)).days
        return days

    def action_excel(self, cr, uid, ids, context=None):
        if not ids:
            return {'type_pv': 'ir.actions.act_window_close'}
        if context is None:
            context = {}
        form = self.read(cr, uid, ids)[0]
        date_from = form.get('date_from')
        type_stock = form.get('type_stock')
        type_pv = form.get('company_id')
        # Formato de la Hoja de Excel
        wb = pycel.Workbook(encoding='utf-8')

        style_cabecera = pycel.easyxf('font: colour black, bold True;'
                                      'align: vertical center, horizontal center;'
                                      )

        style_header = pycel.easyxf('font: bold True;'
                                    'align: vertical center, horizontal center, wrap on;'
                                    'borders: left 1, right 1, top 1, bottom 1;')

        linea = pycel.easyxf('borders:bottom 1;')

        linea_center = pycel.easyxf('font: colour black, height 140;'
                                    'align: vertical center, horizontal center, wrap on;'
                                    'borders: left 1, right 1, top 1, bottom 1;')
        linea_der_bold = pycel.easyxf('font: colour black, bold true, height 200;'
                                      'align: vertical center, horizontal right, wrap on;'
                                      'borders: left 1, right 1, top 1, bottom 1;'
                                      )
        view_style = pycel.easyxf('font: colour green, bold true, height 200;'
                                  'align: vertical center, horizontal center, wrap on;'
                                  'borders: left 1, right 1, top 1, bottom 1;'
                                  )
        linea_izq = pycel.easyxf('font: colour black, height 140;'
                                 'align: vertical center, horizontal left, wrap on;'
                                 'borders: left 1, right 1, top 1, bottom 1;')
        linea_izq_n = pycel.easyxf('font: colour black, height 140;'
                                   'align: vertical center, horizontal left, wrap on;'
                                   )
        linea_der = pycel.easyxf('font: colour black, height 140;'
                                 'align: vertical center, horizontal right;'
                                 'borders: left 1, right 1, top 1, bottom 1;')

        style_cabeceraizq = pycel.easyxf('font: bold True;' 'align: vertical center, horizontal left;')
        title = type_pv[1]
        title1 = 'INVENTARIO REAL'

        ws = wb.add_sheet(title)

        ws.show_grid = False
        ws.header_str = u"&LFecha de Impresion: &D Hora: &T&RPagina &P de &N"
        ws.footer_str = u""
        compania = self.pool.get('res.users').browse(cr, uid, uid).company_id
        calle1 = compania.partner_id.street
        calle2 = compania.partner_id.street2
        ruc = compania.partner_id.part_number
        if calle1 and calle2:
            direccion = str(calle1.encode('UTF-8')) + " " + str(calle2.encode('UTF-8'))
        elif calle1 and not calle2:
            direccion = str(calle1.encode('UTF-8'))
        elif calle2 and not calle1:
            direccion = str(calle2.encode('UTF-8'))
        else:
            direccion = ''
        if ruc:
            ruc_part = ruc
        else:
            ruc_part = ''
        x0 = 6

        ws.write_merge(1, 1, 1, x0, compania.name, style_cabecera)
        ws.write_merge(2, 2, 1, x0, 'Direccion: ' + str(direccion), style_cabecera)
        ws.write_merge(3, 3, 1, x0, 'Ruc: ' + str(ruc_part), style_cabecera)
        ws.write_merge(5, 5, 1, x0, title1 + " AL " +
                       time.strftime('%d/%m/%Y', time.strptime(date_from, '%Y-%m-%d')).upper(), style_cabecera)

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

        #Formato de Numero
        style = pycel.XFStyle()
        style.num_format_str = '#,##0.00'
        style.alignment = align
        style.font = font1

        #Formato de Numero Saldo
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
        xe = 9

        ws.write(xi, 1, 'ITEM', style_header)
        ws.write(xi, 2, 'CODIGO', style_header)
        ws.write(xi, 3, 'PRODUCTO', style_header)
        ws.write(xi, 4, 'U.M.', style_header)
        ws.write(xi, 5, 'STOCK', style_header)
        ws.write(xi, 6, 'COSTO', style_header)
        ws.write(xi, 7, 'TOTAL', style_header)
        totales = self.get_lines_report_wage(cr, uid, form)
        xi = xe + 1
        columns = [5, 6, 7]
        total_formula = ['SUBTOTAL(9,F9:F{0})', 'SUBTOTAL(9,G9:G{0})', 'SUBTOTAL(9,H9:H{0})']
        seq = 1
        prod = False
        data_rev = []
        lock = False
        if type_stock == 'stock':
            for linea in totales:
                if linea.get('qty_sum', '') > 0:
                    #if not lock:
                    #    data_rev.append(linea.get('bodega'))
                    #    lock = True
                    #    product_sumary = linea.get('sum_value', '')
                    #    product_qty = linea.get('qty_sum', '')
                    #if linea.get('bodega') not in data_rev:
                    #    data_rev.append(linea.get('bodega'))
                    #    ws.write(xi, 4, 'STOCK', style_header)
                    #    ws.write(xi, columns[0], product_qty, style_header)
                    #    if not product_sumary < 1:
                    #        ws.write(xi, columns[1], product_sumary, style_header)
                    #    else:
                    #        ws.write(xi, columns[1], '0', style_header)
                    #    xi += 1
                    if lock != linea.get('bodega'):
                        ws.write(xi, 2, linea.get('bodega', ''), style_cabeceraizq)
                        xi += 1
                        lock = linea.get('bodega')
                    # detalle
                    ws.write(xi, 1, seq, linea_izq)
                    ws.write(xi, 2, linea.get('cod_name', ''), linea_izq)
                    ws.write(xi, 3, linea.get('prod_name', ''), linea_izq)
                    ws.write(xi, 4, linea.get('uom', ''), linea_izq)
                    ws.write(xi, 5, linea.get('qty_sum', ''), linea_der)
                    ws.write(xi, 6, linea.get('prom', ''), linea_der)
                    ws.write(xi, 7, linea.get('sum_value', ''), linea_der)
                    ws.write(xi, 8, linea.get('origin', ''), linea_der)
                    ws.write(xi, 9, linea.get('ref', ''), linea_der)
                    ws.write(xi, 10, linea.get('date', ''), linea_der)

                    xi += 1
                    seq += 1

        # ws.write(xi, 4, 'TOTAL', view_style)
        # ws.write(xi, columns[0], xlwt.Formula(total_formula[0].format(xi)), linea_der_bold)
        # ws.write(xi, columns[1], xlwt.Formula(total_formula[1].format(xi)), linea_der_bold)
        # ws.write(xi, columns[2], xlwt.Formula(total_formula[2].format(xi)), linea_der_bold)

        ws.col(0).width = 1000
        ws.col(1).width = 2250
        ws.col(2).width = 3000
        ws.col(3).width = 14900
        ws.col(4).width = 2500
        ws.col(5).width = 2500
        ws.col(6).width = 2500
        ws.row(8).height = 750

        buf = cStringIO.StringIO()

        wb.save(buf)
        out = base64.encodestring(buf.getvalue())
        buf.close()
        name = "%s.xls" % ("Reporte_inventario")
        archivo = '/opt/temp/' + name
        res_model = 'stock.location.real.inventory'
        id = ids and type(ids) == type([]) and ids[0] or ids
        self.write(cr, uid, ids, {'data':out, 'name':'Reporte_inventario_bodega.xls'})

        self.load_doc(cr, uid, out, id, name, archivo, res_model)
        return {
            'type': 'ir.actions.client',
            'tag': 'reload'
        }

    def load_doc(self, cr, uid, out, id, data_fname, archivo, res_model):

        attach_vals = {
            'name': data_fname,
            'datas_fname': data_fname,
            'res_model': res_model,
            'datas': out,
            'type': 'binary',
            'file_type': 'file_type',
        }
        if id:
            attach_vals.update({'res_id': id})
        self.pool.get('ir.attachment').create(cr, uid, attach_vals)

    _columns = {
        'name':fields.char('Nombre', size=64, required=False, readonly=False),
        'data':fields.binary('Archivo', filters=None),
        'date_from': fields.date('Fecha Corte'),
        'company_id': fields.many2one('res.company', 'Compania', required=True),
        'location_id': fields.many2one('stock.location', 'Bodega'),
        'type_stock': fields.selection([('stock', 'Existencias')], 'Tipo')
    }
    _defaults = {
        'company_id': lambda s, cr, uid, c: s.pool.get('res.company')._company_default_get(cr, uid, 'stock.inventary.real', context=c),
        'location': 'stock'
    }

stock_location_real_inventory()
