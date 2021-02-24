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
import datetime
from openerp.exceptions import Warning
import xlwt
import xlwt as pycel

ACTION_DICT = {
    'view_type': 'form',
    'view_mode': 'form',
    'res_model': 'base.module.upgrade',
    'target': 'new',
    'type': 'ir.actions.act_window',
    'nodestroy': True,
}


class stock_margin_inventory(osv.Model):
    _name = "stock.margin.inventory"
    _description = 'Margen de contribucion'

    def check_state(self, state):
        if state:
            if state == 'done':
                estado = 'REALIZADO'
            elif state == 'draft':
                estado = 'NUEVO'
            elif state == 'waiting':
                estado = 'ESPERANDO MOV'
            elif state == 'confirmed':
                estado = 'ESPERANDO DISP'
            elif state == 'assigned':
                estado = 'DISPONIBLE'
            elif state == 'cancel':
                estado = 'CANCELADO'
        return estado

    def get_invoice_number(self, cr, uid, move_obj):
        order = ''
        price = 0
        name = ''
        print move_obj.picking_id
        if move_obj:
            sale_order_obj = self.pool.get('sale.order')
            sale_order_line_obj = self.pool.get('sale.order.line')
            procurement_obj = self.pool.get('procurement.order')
            procurement_order = procurement_obj.search(cr, uid, [('id', '=', move_obj.procurement_id.id)])
            if procurement_order:
                procurement_id = procurement_obj.browse(cr, uid, procurement_order)
                sale_order_line = sale_order_line_obj.browse(cr, uid, procurement_id.sale_line_id.id)
                print "sale_line_id", sale_order_line
                order = sale_order_obj.search(cr, uid, [('id', '=', sale_order_line.order_id.id)])
                if order:
                    sale_order = sale_order_obj.browse(cr, uid, order)
                    if sale_order.invoice_ids:
                        for invoice in sale_order.invoice_ids:
                            if invoice.state in ('open', 'paid'):
                                name = invoice.number_reem
                                for lines in invoice.invoice_line:
                                    if lines.product_id.id == move_obj.product_id.id:
                                        price = lines.price_unit
            elif move_obj.picking_id and not procurement_order:
                order = sale_order_obj.search(cr, uid, [('name', '=', move_obj.picking_id.origin[:11])])
                if not order:
                    order = sale_order_obj.search(cr, uid, [('name', '=', move_obj.picking_id.origin[:12])])
                    if order:
                        sale_order = sale_order_obj.browse(cr, uid, order)
                        if sale_order.invoice_ids:
                            for invoice in sale_order.invoice_ids:
                                if invoice.state in ('open', 'paid'):
                                    name = invoice.number_reem
                                    for lines in invoice.invoice_line:
                                        if lines.product_id.id == move_obj.product_id.id:
                                            price = lines.price_unit
        return order, price, name

    def get_lines_report_wage(self, cr, uid, form):
        res = []
        prod_prod_data = []
        date_from = form.get('date_from', False)
        date_to = form.get('date_to', False)
        company = form.get('company_id', False)
        prod_id = form.get('product_id', False)
        category = form.get('category_id', False)
        prod_obj = self.pool.get('product.product')
        category_obj = self.pool.get('product.category')
        stoc_mov_obj = self.pool.get('stock.move')
        type = form.get('type', False)
        tot = 0.00
        tot_sald_ant = 0.00
        tot_c_ant = 0.00
        tot_cantidad = 0.00
        tot_cantxrecep = 0.00
        tot_cantxdesp = 0.00
        tot_costo = 0.00
        tot_costo_mov = 0.00
        tot_saldo_stock = 0.00
        tot_valor_total = 0.00
        tot_promedio = 0.00
        move_state = 'done'
        product_type = 'product'
        rep_products = '%rpr-%'
        products_ids = []
        if type == 'category':
            if not category:
                raise Warning('No ha seleccionado ninguna categoria, ingrese una.')
            categ = category[0]
            cr.execute('SELECT DISTINCT p.id AS id \
                        FROM product_product AS p, stock_move AS s, product_template AS t \
                        WHERE (p.id=s.product_id) \
                            AND (p.product_tmpl_id = t.id) \
                            AND (t.categ_id = %s) \
                            AND (t.type = %s) \
                            AND (p.active = True) \
                            AND (s.state = %s) \
                            AND (s.date >= %s)\
                            AND (s.date <= %s)\
                            ORDER BY p.id',
                       (categ, product_type, move_state, date_from, date_to))
            products = cr.dictfetchall()
            products_ids = [x['id'] for x in products]
            if not products_ids:
                raise Warning('No existe informacion que mostrar con esa categoria y en las fechas ingresadas.')
            prod_prod_data = prod_obj.browse(cr, uid, products_ids)

        if type == 'product':
            if not prod_id:
                cr.execute('SELECT DISTINCT p.id AS id \
                            FROM product_product p, stock_move AS s, product_template t \
                            WHERE (p.id=s.product_id) \
                                AND (p.product_tmpl_id = t.id) \
                                AND (t.type = %s) \
                                AND (p.default_code not ilike %s) \
                                AND (p.active = True) \
                                AND (s.state = %s) \
                                AND (s.date >= %s)\
                                AND (s.date <= %s)\
                                ORDER BY p.id',
                           (product_type, rep_products, move_state, date_from, date_to,))
                products = cr.dictfetchall()
                products_ids = [x['id'] for x in products]
                if not products_ids:
                    raise Warning('No existe informacion que mostrar en las fechas ingresadas.')
                prod_prod_data = prod_obj.browse(cr, uid, products_ids)
            if prod_id:
                prod_prod_data = prod_obj.browse(cr, uid, [prod_id[0]])
        sec = 1
        cont = 0
        for prod in prod_prod_data:
            old_qty = 0.00
            old_value = 0.00
            qty_val = False
            ingresos_ant = 0
            egresos_ant = 0
            tipo = ''
            saldo_ant = 0.00
            cantxdesp = 0.00
            qty_sum = 0.00
            sum_value = 0.00
            cantxrecep = 0.00
            saldo_stock = 0.00
            valor_total = 0.00
            promedio = 0.00
            estado = ''
            cost = 0.00
            old_cost = 0.00
            cond = False
            buy_cond = False
            last_cost = 0.00
            prom_cost = 0.00
            order = ''
            sale_price = 0
            invoice_name = ''
            price_cost = 0
            costo_compra = 0

            # CSV:11-04-2018:AUMENTO PARA SACAR SALDO ANTERIOR A LA FECHA DEL REPORTE
            if cont == 0:
                cost_ant = 0
                stock_ing_ant = stoc_mov_obj.search(cr, uid, [('product_id', '=', prod.id),
                                                              ('location_dest_id.usage', '=', 'internal'),
                                                              ('date', '<', date_from), ('state', '=', 'done'),
                                                              ('company_id', '=', company[0])])
                stock_egre_ant = stoc_mov_obj.search(cr, uid, [('product_id', '=', prod.id),
                                                               ('location_id.usage', '=', 'internal'),
                                                               ('date', '<', date_from), ('state', '=', 'done'),
                                                               ('company_id', '=', company[0])])
                if len(stock_ing_ant) > 0 or len(stock_egre_ant) > 0:
                    stock_ing_ant_data = stoc_mov_obj.browse(cr, uid, stock_ing_ant)
                    stock_egr_ant_data = stoc_mov_obj.browse(cr, uid, stock_egre_ant)
                    for moves_ant in stock_ing_ant_data:
                        ingresos_ant += moves_ant.product_qty
                        cost_ant = cost_ant + (moves_ant.product_qty * moves_ant.price_unit)
                    for mov_egr_ant in stock_egr_ant_data:
                        egresos_ant += mov_egr_ant.product_qty
                        cost_ant = cost_ant - (mov_egr_ant.product_qty * mov_egr_ant.price_unit)
                    saldo_ant = ingresos_ant - egresos_ant
                    cont = 1
            # CSV:11-04-2018:CARGO LOS MOVIMIENTOS ENTRE LAS FECHAS A SACAR
            if not prod_id:
                stock_mov_ids = stoc_mov_obj.search(cr, uid, [('product_id', '=', prod.id), ('date', '>=', date_from),
                                                              ('date', '<=', date_to), ('company_id', '=', company[0]),
                                                              ('state', '=', 'done')],
                                                    order='date')
            if prod_id:
                stock_mov_ids = stoc_mov_obj.search(cr, uid,
                                                    [('product_id', '=', prod_id[0]), ('date', '>=', date_from),
                                                     ('date', '<=', date_to), ('company_id', '=', company[0]),
                                                     ('state', '=', 'done')],
                                                    order='date')
            if len(stock_mov_ids) > 0:
                stock_mov_data = stoc_mov_obj.browse(cr, uid, stock_mov_ids)
                for moves in stock_mov_data:
                    costo = 0.00
                    costo_mov = 0.00
                    if prod.id == moves.product_id.id and moves.product_id.type == 'product' and moves.product_id.active:
                        # CSV:CASOS MOVIMIENTOS
                        data = {}
                        cantidad = 0.00
                        origin = moves.location_id.usage
                        destiny = moves.location_dest_id.usage
                        fecha = moves.date[:10] or ''
                        ref = moves.origin or ''
                        origen = moves.picking_id.origin or ''
                        albaran = moves.picking_id.name or ''
                        destino = moves.location_dest_id.name or ''
                        empresa = moves.picking_id.partner_id.name or ''
                        notas = moves.picking_id.note or ''
                        prod_name = moves.product_id.name or ''
                        qty_available = moves.product_id.qty_available
                        print moves

                        if moves.product_id.default_code:
                            cod_name = '[' + moves.product_id.default_code + ']'
                        else:
                            cod_name = ''
                        sald_ant = saldo_ant
                        c_ant = cost_ant
                        # costo = moves.price_unit
                        # costo_mov = moves.product_qty * moves.price_unit
                        uom = moves.product_id.uom_id.name

                        if moves.state:
                            estado = self.check_state(moves.state)

                        if origin == 'supplier' and destiny == 'internal':
                            tipo = 'COMPRA'
                            if moves.state == 'done':
                                if prom_cost == 0:
                                    costo_compra = moves.price_unit
                                else:
                                    costo_compra = (prom_cost + moves.price_unit) / 2
                                prom_cost = costo_compra

                        if origin == 'internal' and destiny == 'customer':
                            tipo = 'VENTA'
                            order = self.get_invoice_number(cr, uid, moves)[0]
                            sale_price = self.get_invoice_number(cr, uid, moves)[1]
                            invoice_name = self.get_invoice_number(cr, uid, moves)[2]
                            if moves.state == 'done' and invoice_name:
                                ref = invoice_name
                                cantidad = moves.product_qty
                                cantxdesp = 0
                                cantxrecep = moves.product_qty
                                qty_sum = round(old_qty - moves.product_qty, 2)
                                costo = round(sale_price, 2)
                                sum_value = round(old_value - (costo * moves.product_qty), 2)
                                costo_mov = round(costo * moves.product_qty, 2)
                                if qty_sum == 0:
                                    sum_value = 0
                                if prom_cost == 0:
                                    prom_cost = moves.product_id.standard_price
                                price_cost = prom_cost * moves.product_qty
                                last_cost = costo

                        elif origin == 'inventory' and destiny == 'internal':
                            tipo = 'AJUSTE INVENTARIO +'
                            if moves.state == 'done':
                                if prom_cost == 0:
                                    costo_compra = moves.price_unit
                                else:
                                    costo_compra = (prom_cost + moves.price_unit) / 2
                                prom_cost = costo_compra

                        elif origin == 'production' and destiny == 'internal':
                            tipo = 'PRODUCCION'
                            if moves.state == 'done':
                                if prom_cost == 0:
                                    costo_compra = moves.price_unit
                                else:
                                    costo_compra = (prom_cost + moves.price_unit) / 2
                                prom_cost = costo_compra

                        elif origin == 'production' and destiny == 'customer':
                            tipo = 'VENTA'
                            if moves.state == 'done':
                                cantidad = moves.product_qty
                                cantxdesp = 0
                                cantxrecep = moves.product_qty
                                qty_sum = round(old_qty - moves.product_qty, 2)
                                costo = round(sale_price, 2)
                                sum_value = round(old_value - (costo * moves.product_qty), 2)
                                costo_mov = round(costo * moves.product_qty, 2)
                                if qty_sum == 0:
                                    sum_value = 0
                                price_cost = prom_cost * moves.product_qty

                        if not qty_val:
                            old_qty = qty_sum
                            old_value = prom_cost
                            qty_val = True
                        else:
                            old_qty = qty_sum
                            old_value = prom_cost
                        product = moves.product_id.id

                        if invoice_name and destiny == 'customer':
                            data['sec'] = sec
                            data['qty_sum'] = qty_sum
                            data['sum_value'] = sum_value
                            data['prod_name'] = prod_name
                            data['cod_name'] = cod_name
                            data['fecha'] = fecha
                            data['tipo'] = tipo
                            data['ref'] = ref
                            data['origen'] = origen.upper()
                            data['albaran'] = albaran
                            data['destino'] = destino.upper()
                            data['empresa'] = empresa
                            data['notas'] = notas.upper()
                            data['sald_ant'] = sald_ant
                            data['c_ant'] = c_ant
                            data['cantidad'] = cantidad
                            data['cantxrecep'] = cantxrecep
                            data['cantxdesp'] = cantxdesp
                            data['costo'] = costo
                            data['costo_mov'] = costo_mov
                            data['saldo_stock'] = saldo_stock
                            data['valor_total'] = valor_total
                            data['promedio'] = promedio
                            data['estado'] = estado
                            data['qty'] = qty_available
                            data['uom'] = uom
                            tot_sald_ant += sald_ant
                            tot_c_ant += c_ant
                            tot_cantidad += cantidad
                            tot_cantxrecep += cantxrecep
                            tot_cantxdesp += cantxdesp
                            tot_costo = costo
                            tot_costo_mov = costo_mov
                            tot_saldo_stock += saldo_stock
                            tot_valor_total += valor_total
                            tot_promedio += promedio
                            data['t_sald_ant'] = tot_sald_ant
                            data['t_c_ant'] = tot_c_ant
                            data['t_cantidad'] = tot_cantidad
                            data['t_cantxrecep'] = tot_cantxrecep
                            data['t_cantxdesp'] = tot_cantxdesp
                            data['t_costo'] = tot_costo
                            data['t_costo_mov'] = tot_costo_mov
                            data['t_saldo_stock'] = tot_saldo_stock
                            data['t_valor_total'] = tot_valor_total
                            data['t_promedio'] = tot_promedio
                            data['order'] = order
                            data['sale_price'] = sale_price
                            data['name'] = invoice_name
                            data['price_cost'] = price_cost
                            saldo_ant = 0
                            cost_ant = 0
                            sec += 1
                            res.append(data)
            if not stock_mov_ids:
                raise Warning('No existe informacion que mostrar en las fechas ingresadas')
        return res

    def _format_date(self, date):
        if date:
            campos = date.split('-')
            date = datetime.date(int(campos[0]), int(campos[1]), int(campos[2]))
            return date

    def get_days(self, cr, uid, date_start, date_now):
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
        date_to = form.get('date_to')
        categ = form.get('category_id')
        tipo = form.get('type', False)
        categ_obj = self.pool.get('product.category')
        if tipo == 'category':
            if not categ:
                raise Warning('No ha seleccionado ninguna categoria, ingrese una.')
            category = categ_obj.search(cr, uid, [('id', '=', categ[0])], context=context)
            categ = categ_obj.browse(cr, uid, category, context=None)
        type_pv = form.get('company_id')
        path = form.get('path')
        # Formato de la Hoja de Excel
        wb = pycel.Workbook(encoding='utf-8')

        style_cabecera = pycel.easyxf('font: colour black, bold True;' 'align: vertical center, horizontal center;')

        style_cabecerader = pycel.easyxf('font: bold True;' 'align: vertical center, horizontal right;')

        style_cabeceraizq = pycel.easyxf('font: bold True;' 'align: vertical center, horizontal left;')

        style_header = pycel.easyxf('font: bold True;' 'align: vertical center, horizontal center, wrap on;'
                                    'borders: left 1, right 1, top 1, bottom 1;')

        linea = pycel.easyxf('borders:bottom 1;')

        linea_center = pycel.easyxf('font: colour black, height 140;' 'align: vertical center, horizontal center, wrap on;'
                                    'borders: left 1, right 1, top 1, bottom 1;')

        linea_izq = pycel.easyxf('font: colour black, height 140;' 'align: vertical center, horizontal left, wrap on;'
                                 'borders: left 1, right 1, top 1, bottom 1;')
        linea_izq_n = pycel.easyxf('font: colour black, height 140;' 'align: vertical center, horizontal left, wrap on;'
                                   )
        linea_der = pycel.easyxf('font: colour black, height 140;' 'align: vertical center, horizontal right;'
                                 'borders: left 1, right 1, top 1, bottom 1;')
        title = type_pv[1]
        title1 = ''

        ws = wb.add_sheet(title)
        direccion = ''
        ws.show_grid = False
        ws.header_str = u"&LFecha de Impresion: &D Hora: &T&RPagina &P de &N"
        ws.footer_str = u""
        compania = self.pool.get('res.users').browse(cr, uid, uid).company_id
        calle1 = compania.partner_id.street
        calle2 = compania.partner_id.street2
        ruc = compania.partner_id.part_number or ''
        if calle1 and calle2:
            direccion = str(calle1.encode('UTF-8')) + " " + str(calle2.encode('UTF-8'))
        elif calle1 and not calle2:
            direccion = str(calle1.encode('UTF-8')) or ''
        elif calle2 and not calle1:
            direccion = str(calle2.encode('UTF-8')) or ''
        x0 = 8
        totales = self.get_lines_report_wage(cr, uid, form)
        ws.write_merge(1, 1, 1, x0, compania.name, style_cabecera)
        ws.write_merge(2, 2, 1, x0, 'Direccion: ' + str(direccion), style_cabecera)
        ws.write_merge(3, 3, 1, x0, 'Ruc: ' + str(ruc), style_cabecera)
        ws.write_merge(5, 5, 1, x0, title1 + " " +
                       time.strftime('%d/%m/%Y', time.strptime(date_from,'%Y-%m-%d')).upper() + " AL " +
                       time.strftime('%d/%m/%Y', time.strptime(date_to, '%Y-%m-%d')).upper(), style_cabecera)
        if tipo == 'category':
            ws.write_merge(7, 7, 1, x0, 'CATEGORIA: ' + categ.name.upper(), style_cabecera)

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

        xi = 11  # Cabecera de Cliente
        xe = 12
        sec = 1

        ws.write(xi, 1, 'ITEM', style_header)
        ws.write(xi, 2, 'CODIGO', style_header)
        ws.write(xi, 3, 'PRODUCTO', style_header)
        ws.write(xi, 4, 'EMPRESA', style_header)
        ws.write(xi, 5, 'FECHA', style_header)
        ws.write(xi, 6, 'ORDEN', style_header)
        ws.write(xi, 7, 'QTY', style_header)
        ws.write(xi, 8, 'P. VENTA', style_header)
        ws.write(xi, 9, 'COSTO', style_header)
        tot_sald_ant = 0
        tot_c_ant = 0
        tot_cantidad = 0
        tot_cantxrecep = 0
        tot_cantxdesp = 0
        tot_costo = 0
        tot_costo_mov = 0
        tot_saldo_stock = 0
        tot_valor_total = 0
        tot_promedio = 0
        for tot in totales:
            tot_sald_ant = tot.get('t_sald_ant', '')
            tot_c_ant = tot.get('t_c_ant', '')
            tot_cantidad = tot.get('t_cantidad', '')
            tot_cantxrecep = tot.get('t_cantxrecep', '')
            tot_cantxdesp = tot.get('t_cantxdesp', '')
            tot_costo = tot.get('t_costo', '')
            tot_costo_mov = tot.get('t_costo_mov', '')
            tot_saldo_stock = tot.get('t_saldo_stock', '')
            tot_valor_total = tot.get('t_valor_total', '')
            tot_promedio = tot.get('t_promedio', '')

        ws.write(xe, 1, '', style_header)
        ws.write(xe, 2, '', style_header)
        ws.write(xe, 3, '', style_header)
        ws.write(xe, 4, '', style_header)
        ws.write(xe, 5, '', style_header)
        ws.write(xe, 6, '', style_header)
        ws.write(xe, 7, '', style_header)
        ws.write(xe, 8, '', style_header)
        ws.write(xe, 9, '', style_header)

        xi = xe + 1
        # rf = rr = ri = 0
        # amount_base = amount_calculate = 0.00
        product = False
        columns = [11]
        data_rev = []
        prod = False
        for linea in totales:
            if linea.get('estado') not in ('CANCELADO', 'NUEVO'):
                # detalle
                #if not prod:
                #    data_rev.append(linea.get('cod_name'))
                #    prod = True
                #    product_sumary = linea.get('sum_value', '')
                #    product_qty = linea.get('qty_sum', '')
                #if linea.get('cod_name') not in data_rev:
                #    data_rev.append(linea.get('cod_name'))
                #    ws.write(xi, 10, 'STOCK', style_header)
                #    ws.write(xi, columns[0], product_qty, style_header)
                #    xi += 1

                ws.write(xi, 1, linea['sec'], linea_center)
                ws.write(xi, 2, linea['cod_name'], linea_center)
                ws.write(xi, 3, linea['prod_name'], linea_center)
                ws.write(xi, 4, linea.get('empresa', ''), linea_izq)
                ws.write(xi, 5, linea.get('fecha', ''), linea_izq)
                ws.write(xi, 6, linea.get('ref', ''), linea_izq)
                ws.write(xi, 7, linea.get('cantxrecep', ''), linea_der)
                ws.write(xi, 8, linea.get('costo_mov', ''), linea_der)
                ws.write(xi, 9, linea.get('price_cost', ''), linea_der)
                product_sumary = linea.get('sum_value', '')
                product_qty = linea.get('qty_sum', '')
                xi += 1

        ws.col(0).width = 500
        ws.col(1).width = 1200
        ws.col(2).width = 3000
        ws.col(3).width = 10000
        ws.col(4).width = 10000
        ws.col(5).width = 2000
        ws.col(6).width = 3500
        ws.col(7).width = 1200
        ws.col(8).width = 1500
        ws.col(9).width = 2500

        ws.row(11).height = 750

        buf = cStringIO.StringIO()

        wb.save(buf)
        out = base64.encodestring(buf.getvalue())
        buf.close()
        name = "%s.xls" % ("Reporte_margen_contribucion")
        archivo = '/opt/temp/' + name
        res_model = 'stock.margin.inventory'
        id = ids and type(ids) == type([]) and ids[0] or ids
        self.load_doc(cr, uid, out, id, name, archivo, res_model)

        return {
            'type': 'ir.actions.client',
            'tag': 'reload'
        }

    def load_doc(self, cr, uid, out, id, data_fname, archivo, res_model):
        attach_vals = {'name': data_fname, 'datas_fname': data_fname, 'res_model': res_model, 'datas': out,
                       'type': 'binary', 'file_type': 'file_type'}
        if id:
            attach_vals.update({'res_id': id})
        self.pool.get('ir.attachment').create(cr, uid, attach_vals)

    _columns = {
        'name': fields.char('', size=64, required=False, readonly=False),
        'data': fields.binary('', filters=None),
        'date_from': fields.date('Fecha Desde'),
        'date_to': fields.date('Fecha Hasta'),
        'company_id': fields.many2one('res.company', 'Compania', required=True),
        'product_id': fields.many2one('product.product', 'Producto'),
        'category_id': fields.many2one('product.category', 'Categoria'),
        'type': fields.selection([('product', 'Producto'), ('category', 'Categoria')], 'Tipo')
    }
    _defaults = {
        'date_from': lambda *a: time.strftime('2018-01-01'),
        'company_id': lambda s, cr, uid, c: s.pool.get('res.company')._company_default_get(cr, uid,
                                                                                           'stock.inventory.report',
                                                                                           context=c),
        'type': 'product'
    }


stock_margin_inventory()
