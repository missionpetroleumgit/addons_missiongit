# -*- coding: utf-8 -*-
##############################################################################

from openerp.osv import fields, osv
import base64
import cStringIO
import time
import datetime
from openerp.exceptions import Warning
import xlwt
import xlwt as pycel
import xlsxwriter

ACTION_DICT = {
    'view_type': 'form',
    'view_mode': 'form',
    'res_model': 'base.module.upgrade',
    'target': 'new',
    'type': 'ir.actions.act_window',
    'nodestroy': True,
}


class stock_inventary_detallado(osv.Model):
    _name = "stock.inventary.detallado"
    _description = 'Reporte Inventario Detallado'

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

    def get_lines_report_wage(self, cr, uid, form):
        res = []
        prod_prod_data = []
        date_start = '01-08-2018'
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
                       (categ, product_type, move_state, date_start, date_to))
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
                           (product_type, rep_products, move_state, date_start, date_to,))
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

            # CSV:11-04-2018:AUMENTO PARA SACAR SALDO ANTERIOR A LA FECHA DEL REPORTE
            if cont == 0:
                cost_ant = 0
                stock_ing_ant = stoc_mov_obj.search(cr, uid, [('product_id', '=', prod.id),
                                                              ('location_dest_id.usage', '=', 'internal'),
                                                              ('date', '<', date_start), ('state', '=', 'done'),
                                                              ('company_id', '=', company[0])])
                stock_egre_ant = stoc_mov_obj.search(cr, uid, [('product_id', '=', prod.id),
                                                               ('location_id.usage', '=', 'internal'),
                                                               ('date', '<', date_start), ('state', '=', 'done'),
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
                stock_mov_ids = stoc_mov_obj.search(cr, uid, [('product_id', '=', prod.id), ('date', '>=', date_start),
                                                              ('date', '<=', date_to), ('company_id', '=', company[0]),
                                                              ('state', '=', 'done')],
                                                    order='date')
            if prod_id:
                stock_mov_ids = stoc_mov_obj.search(cr, uid,
                                                    [('product_id', '=', prod_id[0]), ('date', '>=', date_start),
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
                        fecha = moves.date or ''
                        ref = moves.origin or ''
                        origen = moves.picking_id.origin or ''
                        albaran = moves.picking_id.name or ''
                        destino = moves.location_dest_id.name or ''
                        empresa = moves.picking_id.partner_id.name or ''
                        notas = moves.picking_id.note or ''
                        prod_name = moves.product_id.name or ''
                        qty_available = moves.product_id.qty_available

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
                                cantidad = moves.product_qty
                                cantxdesp = 0.00
                                cantxrecep = moves.product_qty
                                qty_sum = round(old_qty + moves.product_qty, 2)
                                sum_value = round(old_value + (moves.price_unit * moves.product_qty), 2)
                                costo = moves.price_unit
                                costo_mov = round(costo * moves.product_qty)
                                if qty_sum <= 0:
                                    prom_cost = sum_value
                                else:
                                    prom_cost = sum_value / qty_sum

                        if origin == 'internal' and destiny == 'supplier':
                            tipo = 'DEVOLUCION'
                            if moves.state == 'done':
                                cantidad = moves.product_qty
                                cantxdesp = moves.product_qty
                                cantxrecep = 0.00
                                qty_sum = round(old_qty - moves.product_qty, 2)
                                costo = round(prom_cost, 2)
                                sum_value = round(old_value - (costo * moves.product_qty), 2)
                                costo_mov = round(costo * moves.product_qty, 2)
                                # moves.price_unit = round(last_cost, 2)

                        if origin == 'internal' and destiny == 'customer':
                            tipo = 'VENTA'
                            if moves.state == 'done':
                                cantidad = moves.product_qty
                                cantxdesp = moves.product_qty
                                cantxrecep = 0.00
                                qty_sum = round(old_qty - moves.product_qty, 2)
                                costo = round(prom_cost, 2)
                                sum_value = round(old_value - (costo * moves.product_qty), 2)
                                costo_mov = round(costo * moves.product_qty, 2)
                                if qty_sum == 0:
                                    sum_value = 0
                                # moves.price_unit = round(prom_cost, 2)
                                # last_cost = moves.price_unit
                                last_cost = costo

                        if origin == 'customer' and destiny == 'internal':
                            tipo = 'RETORNO'
                            if moves.state == 'done':
                                cantidad = moves.product_qty
                                cantxdesp = 0.00
                                cantxrecep = moves.product_qty
                                qty_sum = round(old_qty + moves.product_qty, 2)
                                costo = round(last_cost, 2)
                                sum_value = round(old_value + (costo * moves.product_qty), 2)
                                costo_mov = round(costo * moves.product_qty, 2)
                                # moves.price_unit = round(last_cost, 2)

                        elif origin == 'inventory' and destiny == 'internal':
                            tipo = 'AJUSTE INVENTARIO +'
                            if moves.state == 'done':
                                cantidad = moves.product_qty
                                cantxdesp = 0.00
                                cantxrecep = moves.product_qty
                                qty_sum = round(old_qty + moves.product_qty, 2)
                                sum_value = round(old_value + (moves.price_unit * moves.product_qty), 2)
                                costo = moves.price_unit
                                costo_mov = round(costo * moves.product_qty, 2)
                                if qty_sum <= 0:
                                    prom_cost = sum_value
                                else:
                                    prom_cost = sum_value / qty_sum

                        elif origin == 'internal' and destiny == 'inventory':
                            tipo = 'AJUSTE INVENTARIO -'
                            if moves.state == 'done':
                                cantidad = moves.product_qty
                                cantxdesp = moves.product_qty
                                cantxrecep = 0.00
                                qty_sum = round(old_qty - moves.product_qty, 2)
                                costo = round(last_cost, 2)
                                sum_value = round(old_value - (costo * moves.product_qty), 2)
                                costo_mov = round(costo * moves.product_qty, 2)
                                if qty_sum == 0:
                                    sum_value = 0
                                # moves.price_unit = round(last_cost, 2)

                        elif origin == 'production' and destiny == 'internal':
                            tipo = 'PRODUCCION'
                            if moves.state == 'done':
                                cantidad = moves.product_qty
                                cantxdesp = 0.00
                                cantxrecep = moves.product_qty
                                qty_sum = round(old_qty + moves.product_qty, 2)
                                costo = moves.price_unit
                                sum_value = round(old_value + (costo * moves.product_qty), 2)
                                costo_mov = round(costo * moves.product_qty, 2)
                                if qty_sum <= 0:
                                    prom_cost = sum_value
                                else:
                                    prom_cost = sum_value / qty_sum

                        elif origin == 'internal' and destiny == 'production':
                            tipo = 'PRODUCCION CONSUMO'
                            if moves.state == 'done':
                                cantidad = moves.product_qty
                                cantxdesp = moves.product_qty
                                cantxrecep = 0.00
                                qty_sum = round(old_qty - moves.product_qty, 2)
                                costo = round(prom_cost, 2)
                                sum_value = round(old_value - (costo * moves.product_qty), 2)
                                costo_mov = round(costo * moves.product_qty, 2)
                                if qty_sum == 0:
                                    sum_value = 0
                                last_cost = costo
                                # moves.price_unit = round(prom_cost, 2)
                                # last_cost = moves.price_unit

                        elif origin == 'production' and destiny == 'customer':
                            tipo = 'PRODUCCION CONSUMO'
                            if moves.state == 'done':
                                cantidad = moves.product_qty
                                cantxdesp = moves.product_qty
                                cantxrecep = 0.00
                                qty_sum = round(old_qty - moves.product_qty, 2)
                                costo = round(prom_cost, 2)
                                sum_value = round(old_value - (costo * moves.product_qty), 2)
                                costo_mov = round(costo * moves.product_qty, 2)
                                if qty_sum == 0:
                                    sum_value = 0
                                # moves.price_unit = round(prom_cost, 2)

                        elif origin == 'internal' and moves.location_id.id == 12 and destiny == 'internal':
                            tipo = 'INTERNO'
                            if moves.state == 'done':
                                cantidad = moves.product_qty
                                cantxdesp = moves.product_qty
                                cantxrecep = 0.00
                                qty_sum = round(old_qty - moves.product_qty, 2)
                                costo = round(prom_cost, 2)
                                sum_value = round(old_value - (costo * moves.product_qty), 2)
                                costo_mov = round(costo * moves.product_qty, 2)
                                if qty_sum == 0:
                                    sum_value = 0
                                last_cost = costo

                                # moves.price_unit = round(prom_cost, 2)
                                # last_cost = moves.price_unit

                        elif origin == 'internal' and destiny == 'internal' and moves.location_dest_id.id == 12:
                            tipo = 'RETORNO'
                            if moves.state == 'done':
                                cantidad = moves.product_qty
                                cantxdesp = 0.00
                                cantxrecep = moves.product_qty
                                qty_sum = round(old_qty + moves.product_qty, 2)
                                costo = round(last_cost, 2)
                                sum_value = round(old_value + (costo * moves.product_qty), 2)
                                costo_mov = round(costo * moves.product_qty, 2)
                                # moves.price_unit = round(last_cost, 2)

                        elif origin == 'transit' and destiny == 'internal':
                            tipo = 'TRANSITO +'
                            if moves.state == 'done':
                                cantxdesp = 0.00
                                cantxrecep = 0.00
                                qty_sum = round(old_qty + moves.product_qty, 2)
                                sum_value = round(old_value + (moves.price_unit * moves.product_qty), 2)
                                costo = round(prom_cost, 2)
                                costo_mov = round(costo * moves.product_qty, 2)

                        elif origin == 'internal' and destiny == 'transit':
                            tipo = 'TRANSITO -'
                            if moves.state == 'done':
                                cantidad = moves.product_qty
                                cantxdesp = 0.00
                                cantxrecep = 0.00
                                qty_sum = round(old_qty - moves.product_qty, 2)
                                sum_value = round(old_value - (moves.price_unit * moves.product_qty), 2)
                                costo = round(last_cost, 2)
                                costo_mov = round(costo * moves.product_qty, 2)
                                # moves.price_unit = round(last_cost, 2)

                        if not qty_val:
                            old_qty = qty_sum
                            old_value = sum_value
                            qty_val = True
                        else:
                            old_qty = qty_sum
                            old_value = sum_value
                        product = moves.product_id.id

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
                        saldo_ant = 0
                        cost_ant = 0
                        sec += 1
                        if data['fecha'] >= date_from:
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
        date_start = '01-08-2018'
        date_to = form.get('date_to')
        categ = form.get('category_id')
        categ_obj = self.pool.get('product.category')
        tipo = form.get('type', False)
        if tipo == 'category':
            if not categ:
                raise Warning('No ha seleccionado ninguna categoria, ingrese una.')
            category = categ_obj.search(cr, uid, [('id', '=', categ[0])], context=context)
            categ = categ_obj.browse(cr, uid, category, context=None)
        type_pv = form.get('company_id')
        path = form.get('path')
        # Formato de la Hoja de Excel

        wb = xlsxwriter.Workbook('/opt/temp/Kardex_detallado.xlsx')
        style_cabecera = wb.add_format({
            'bold': 1,
            'align': 'center',
            'valign': 'vcenter'})
        style_cabecera.set_font_name('Calibri')
        style_cabecera.set_font_size(14)

        style_cabeceraizq = wb.add_format({
            'bold': 1,
            'align': 'left',
            'valign': 'vertical'})
        style_cabeceraizq.set_font_name('Calibri')
        style_cabeceraizq.set_font_size(10)

        style_header = wb.add_format({
            'bold': 1,
            'border': 1,
            'align': 'center',
            'valign': 'vcenter'
            })
        style_header.set_font_name('Calibri')
        style_header.set_font_size(7.5)

        linea_center = wb.add_format({
            'bold': 1,
            'border': 1,
            'align': 'center',
            'valign': 'rigth'})
        linea_center.set_font_name('Calibri')
        linea_center.set_font_size(12)

        linea_izq = wb.add_format({
            'border': 1,
            'align': 'left',
            'valign': 'rigth'})
        linea_izq.set_font_name('Calibri')
        linea_izq.set_font_size(7.5)

        linea_izq_n = wb.add_format({
            'bold': 1,
            'border': 1,
            'align': 'left',
            'valign': 'rigth'})
        linea_izq_n.set_font_name('Calibri')
        linea_izq_n.set_font_size(12)

        linea_der = wb.add_format({
            'border': 1,
            'align': 'rigth',
            'valign': 'rigth'})
        linea_der.set_font_name('Calibri')
        linea_der.set_font_size(7.5)

        ws = wb.add_worksheet('Kardex Detallado')

        linea = pycel.easyxf('borders:bottom 1;')

        title = type_pv[1]
        title1 = 'INVENTARIO KARDEX DE'

        direccion = ''
        ws.show_grid = False
        ws.hide_gridlines(2)
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
        ws.merge_range(1, 1, 1, x0, compania.name, style_cabecera)
        ws.merge_range(2, 1, 2, x0, 'Direccion: ' + str(direccion), style_cabecera)
        ws.merge_range(3, 1, 3, x0, 'Ruc: ' + str(ruc), style_cabecera)
        ws.merge_range(5, 1, 5, x0, title1 + " " +
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

        xi = 7  # Cabecera de Cliente
        xe = 8
        sec = 1

        ws.write(xi, 1, 'ITEM', style_header)
        ws.write(xi, 2, 'EMPRESA', style_header)
        ws.write(xi, 3, 'MOVIMIENTO', style_header)
        ws.write(xi, 4, 'FECHA', style_header)
        ws.write(xi, 5, 'TIPO', style_header)
        ws.write(xi, 6, 'ORDEN', style_header)
        ws.write(xi, 7, 'ORIGEN', style_header)
        ws.write(xi, 8, 'DESTINO', style_header)
        ws.write(xi, 9, 'ENTRADAS', style_header)
        ws.write(xi, 10, 'P. UNITARIO', style_header)
        ws.write(xi, 11, 'TOTAL', style_header)
        ws.write(xi, 12, 'SALIDAS', style_header)
        ws.write(xi, 13, 'P. UNITARIO', style_header)
        ws.write(xi, 14, 'TOTAL', style_header)
        ws.write(xi, 15, 'SALDO', style_header)
        ws.write(xi, 16, 'VALOR', style_header)
        ws.write(xi, 17, 'OBSERVACIONES', style_header)

        xi = xe + 1
        product = False
        columns = [15, 16]
        data_rev = []
        prod = False
        for linea in totales:
            if linea.get('estado') not in ('CANCELADO', 'NUEVO'):
                # detalle
                if not prod:
                    data_rev.append(linea.get('cod_name'))
                    prod = True
                    product_sumary = linea.get('sum_value', '')
                    product_qty = linea.get('qty_sum', '')
                if linea.get('cod_name') not in data_rev:
                    data_rev.append(linea.get('cod_name'))
                    ws.write(xi, 14, 'STOCK', style_header)
                    ws.write(xi, columns[0], product_qty, style_header)
                    if not product_sumary < 1:
                        ws.write(xi, columns[1], product_sumary, style_header)
                    else:
                        ws.write(xi, columns[1], int(0), style_header)

                    xi += 1
                if product != linea.get('cod_name'):
                    ws.write(xi, 2, linea.get('cod_name', '') + ' ' + linea.get('prod_name', ''), style_cabeceraizq)
                    xi += 1
                    product = linea.get('cod_name')
                    if date_from > date_start:
                        ws.write(xi, 13, 'Saldo Anterior : ', style_header)
                        recep1 = linea.get('qty_sum', '') + linea.get('cantxdesp', '')
                        recep2 = linea.get('costo_mov', '') + linea.get('sum_value', '')
                        desp1 = linea.get('qty_sum', '') - linea.get('cantxrecep', '')
                        desp2 = linea.get('sum_value', '') - linea.get('costo_mov', '')
                        if recep1 == 0 or desp1 == 0:
                            recep2 = 0
                            desp2 = 0
                        if linea.get('cantxdesp') == 0:
                            ws.write(xi, 15, desp1, style_header)
                            ws.write(xi, 16, desp2, linea_der)
                        xi += 1

                    elif date_from <= date_start:
                        continue

                ws.write(xi, 1, linea['sec'], linea_center)
                ws.write(xi, 2, linea.get('empresa', ''), linea_izq)
                ws.write(xi, 3, linea.get('albaran', ''), linea_izq)
                ws.write(xi, 4, linea.get('fecha', ''), linea_izq)
                ws.write(xi, 5, linea.get('tipo', ''), linea_izq)
                ws.write(xi, 6, linea.get('ref', ''), linea_izq)
                ws.write(xi, 7, linea.get('origen', ''), linea_izq)
                ws.write(xi, 8, linea.get('destino', ''), linea_izq)
                ws.write(xi, 9, linea.get('cantxrecep', ''), linea_der)
                if linea.get('cantxrecep') == 0:
                    ws.write(xi, 10, int(0), linea_der)
                    ws.write(xi, 11, int(0), linea_der)
                else:
                    ws.write(xi, 10, linea.get('costo', ''), linea_der)
                    ws.write(xi, 11, linea.get('costo_mov', ''), linea_der)
                ws.write(xi, 12, linea.get('cantxdesp', ''), linea_der)
                if linea.get('cantxdesp') == 0:
                    ws.write(xi, 13, int(0), linea_der)
                    ws.write(xi, 14, int(0), linea_der)
                else:
                    ws.write(xi, 13, linea.get('costo', ''), linea_der)
                    ws.write(xi, 14, linea.get('costo_mov', ''), linea_der)
                ws.write(xi, 15, linea.get('qty_sum', ''), style_header)
                ws.write(xi, 16, linea.get('sum_value', ''), linea_der)
                ws.write(xi, 17, linea.get('notas', ''), linea_izq)
                product_sumary = linea.get('sum_value', '')
                product_qty = linea.get('qty_sum', '')
                xi += 1
        if totales:
            if linea.get('cod_name') == totales[-1].get('cod_name'):
                data_rev.append(linea.get('cod_name'))
                ws.write(xi, 14, 'STOCK', style_header)
                ws.write(xi, columns[0], linea.get('qty_sum', ''), style_header)
                if not linea.get('sum_value', '') < 0.1:
                    ws.write(xi, columns[1], linea.get('sum_value', ''), style_header)
                else:
                    ws.write(xi, columns[1], int(0), style_header)
                xi += 1

        ws.set_column(0, 0, 1)
        ws.set_column(1, 1, 4)
        ws.set_column(2, 2, 50)
        ws.set_column(3, 3, 10)
        ws.set_column(4, 4, 13)
        ws.set_column(5, 5, 13)
        ws.set_column(6, 6, 15)
        ws.set_column(7, 7, 15)
        ws.set_column(8, 8, 15)
        ws.set_column(9, 9)
        ws.set_column(10, 10)
        ws.set_column(11, 11)
        ws.set_column(12, 12)
        ws.set_column(13, 13)
        ws.set_column(14, 14)
        ws.set_column(15, 15, 4)
        ws.set_column(16, 16)
        ws.set_column(17, 17, 40)

        ws.set_row(11)  # 750

        try:
            wb.close()
            var = open('/opt/temp/Kardex_detallado.xlsx', 'r')
            buf = cStringIO.StringIO(var.read())
            out = base64.encodestring(buf.getvalue())
            data_fname = "Kardex_detallado.xlsx"
            archivo = '/opt/temp/' + data_fname
            res_model = 'stock.inventary.detallado'
            id = ids and type(ids) == type([]) and ids[0] or ids
            self.load_doc(cr, uid, out, id, data_fname, archivo, res_model)
            var.close()
        except ValueError:
            raise Warning('Error a la hora de salvar el archivo')

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


stock_inventary_detallado()
