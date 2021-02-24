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
from docutils.utils.math.latex2mathml import mover

from openerp import tools
from openerp.osv import fields, osv
from openerp.report import report_sxw
from openerp.addons.decimal_precision import decimal_precision as dp
from string import upper
from time import strftime
import base64
import StringIO
import cStringIO
import time
from psycopg2.errorcodes import SUBSTRING_ERROR
from decimal import Decimal
from unicodedata import decimal
import csv
#import mx.DateTime
#from mx.DateTime import RelativeDateTime
import datetime
from openerp.exceptions import Warning
import xlwt as pycel  # Libreria que Exporta a Excel

ACTION_DICT = {'view_type': 'form',
               'view_mode': 'form',
               'res_model': 'base.module.upgrade',
               'target': 'new',
               'type': 'ir.actions.act_window',
               'nodestroy': True}


class stock_inventory_report(osv.Model):
    _name = "stock.inventory.report"
    _description = 'Reporte Inventario'

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
        date_from = form.get('date_from', False)
        date_to = form.get('date_to', False)
        company = form.get('company_id', False)
        prod_id = form.get('product_id', False)

        prod_obj = self.pool.get('product.product')
        stoc_mov_obj = self.pool.get('stock.move')
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

        if prod_id:
            prod_prod_data = prod_obj.browse(cr, uid, [prod_id[0]])
            sec = 1
            cont = 0
            for prod in prod_prod_data:
                ingresos_ant = 0
                egresos_ant = 0
                tipo = ''
                saldo_ant = 0.00
                cantxdesp = 0.00
                cantxrecep = 0.00
                saldo_stock = 0.00
                valor_total = 0.00
                promedio = 0.00
                estado = ''
                data = {}
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
                stock_mov_ids = stoc_mov_obj.search(cr, uid, [('product_id', '=', prod.id), ('date', '>=', date_from),
                                                              ('date', '<=', date_to), ('company_id', '=', company[0])],
                                                    order='date')
                if len(stock_mov_ids) > 0:
                    stock_mov_data = stoc_mov_obj.browse(cr, uid, stock_mov_ids)
                    for moves in stock_mov_data:
                        # CSV:CASOS MOVIMIENTOS
                        data = {}
                        origin = moves.location_id.usage
                        destiny = moves.location_dest_id.usage
                        fecha = moves.date or ''
                        ref = moves.origin or ''
                        origen = moves.location_id.name or ''
                        albaran = moves.picking_id.name or ''
                        destino = moves.location_dest_id.name or ''
                        empresa = moves.picking_id.partner_id.name or ''
                        notas = moves.picking_id.note or ''
                        prod_name = moves.product_id.name or ''
                        sald_ant = saldo_ant
                        c_ant = cost_ant
                        costo = moves.price_unit
                        costo_mov = moves.product_qty * moves.price_unit

                        if moves.state:
                            estado = self.check_state(moves.state)

                        if moves.state == 'done':
                            cantidad = moves.product_qty
                            saldo_stock = (saldo_stock + saldo_ant) - moves.product_qty
                            valor_total = (valor_total + c_ant) - (moves.product_qty * moves.price_unit)
                            if saldo_stock > 0:
                                promedio = valor_total / saldo_stock
                        else:
                            cantidad = 0.00
                            saldo_stock = saldo_stock
                            valor_total = valor_total
                            promedio = promedio

                        if origin == 'supplier' and destiny == 'internal':
                            tipo = 'COMPRA'
                            if moves.state == 'done':
                                cantidad = moves.product_qty
                                cantxdesp = 0.00
                                cantxrecep = 0.00
                            else:
                                cantidad = 0.00
                                cantxdesp = 0.00
                                cantxrecep = moves.product_qty
                        elif origin == 'internal' and destiny == 'customer':
                            tipo = 'VENTA'
                            if moves.state == 'done':
                                cantidad = moves.product_qty
                                cantxdesp = 0.00
                                cantxrecep = 0.00
                            else:
                                cantidad = 0.00
                                cantxdesp = moves.product_qty
                                cantxrecep = 0.00
                                promedio = promedio
                            if moves.state == 'done':
                                saldo_stock = (saldo_stock + saldo_ant) - moves.product_qty
                                valor_total = (valor_total+c_ant) - (moves.product_qty * moves.price_unit)
                                if saldo_stock >0:
                                    promedio = valor_total/saldo_stock
                                else:
                                    promedio = promedio
                            else:
                                saldo_stock = saldo_stock
                                valor_total = valor_total

                        elif origin == 'inventory' and destiny == 'internal':
                            tipo = 'AJUSTE INVENTARIO +'
                            if moves.state == 'done':
                                cantidad = moves.product_qty
                                cantxdesp = 0.00
                                cantxrecep = 0.00
                            else:
                                cantidad = 0.00
                                cantxdesp = 0.00
                                cantxrecep = moves.product_qty
                            if moves.state == 'done':
                                saldo_stock = (saldo_stock + saldo_ant) + moves.product_qty
                                valor_total = (valor_total+c_ant) + (moves.product_qty * moves.price_unit)
                                promedio = valor_total/saldo_stock
                            else:
                                saldo_stock = saldo_stock
                                valor_total = valor_total
                                promedio = promedio

                        elif origin == 'internal' and destiny == 'inventory':
                            tipo = 'AJUSTE INVENTARIO -'
                            if moves.state == 'done':
                                cantidad = moves.product_qty
                                cantxdesp = 0.00
                                cantxrecep = 0.00
                            else:
                                cantidad = 0.00
                                cantxdesp = moves.product_qty
                                cantxrecep = 0.00
                            if moves.state == 'done':
                                saldo_stock = (saldo_stock + saldo_ant) - moves.product_qty
                                valor_total = (valor_total+c_ant) - (moves.product_qty * moves.price_unit)
                                promedio = valor_total/saldo_stock
                            else:
                                saldo_stock = saldo_stock
                                valor_total = valor_total
                                promedio = promedio

                        elif origin == 'production' and destiny == 'internal':
                            tipo = 'PRODUCCION'
                            if moves.state == 'done':
                                cantidad = moves.product_qty
                                cantxdesp = 0.00
                                cantxrecep = 0.00
                            else:
                                cantidad = 0.00
                                cantxdesp = 0.00
                                cantxrecep = moves.product_qty
                            if moves.state == 'done':
                                saldo_stock = (saldo_stock + saldo_ant) + moves.product_qty
                                valor_total = (valor_total+c_ant) + (moves.product_qty * moves.price_unit)
                                promedio = valor_total/saldo_stock
                            else:
                                saldo_stock = saldo_stock
                                valor_total = valor_total
                                promedio = promedio

                        elif origin == 'internal' and destiny == 'production':
                            tipo = 'PRODUCCION CONSUMO'
                            if moves.state == 'done':
                                cantidad = moves.product_qty
                                cantxdesp = 0.00
                                cantxrecep = 0.00
                            else:
                                cantidad = 0.00
                                cantxdesp = moves.product_qty
                                cantxrecep = 0.00
                            if moves.state == 'done':
                                saldo_stock = (saldo_stock + saldo_ant) - moves.product_qty
                                valor_total = (valor_total+c_ant) - (moves.product_qty * moves.price_unit)
                                if saldo_stock >0:
                                    promedio = valor_total/saldo_stock
                                else:
                                    promedio = promedio
                            else:
                                saldo_stock = saldo_stock
                                valor_total = valor_total
                                promedio = promedio

                        elif origin == 'internal' and destiny == 'internal':
                            tipo = 'INTERNO'
                            if moves.state == 'done':
                                cantidad = moves.product_qty
                                cantxdesp = 0.00
                                cantxrecep = 0.00
                            else:
                                cantidad = 0.00
                                cantxdesp = moves.product_qty
                                cantxrecep = 0.00
                            if moves.state == 'done':
                                saldo_stock = (saldo_stock + saldo_ant)
                                valor_total = (valor_total+c_ant)
                                if saldo_stock >0:
                                    promedio = valor_total/saldo_stock
                                else:
                                    promedio = promedio
                            else:
                                saldo_stock = saldo_stock
                                valor_total = valor_total
                                promedio = promedio

                        elif origin == 'transit' and destiny == 'internal':
                            tipo = 'TRANSITO +'
                            if moves.state == 'done':
                                cantxdesp = 0.00
                                cantxrecep = 0.00
                            else:
                                cantxdesp = 0.00
                                cantxrecep = moves.product_qty

                        elif origin == 'internal' and destiny == 'transit':
                            tipo = 'TRANSITO -'
                            if moves.state == 'done':
                                cantidad = moves.product_qty
                                cantxdesp = 0.00
                                cantxrecep = 0.00
                            else:
                                cantidad = 0.00
                                cantxdesp = 0.00
                                cantxrecep = moves.product_qty
                            if moves.state == 'done':
                                saldo_stock = (saldo_stock + saldo_ant) + moves.product_qty
                                valor_total = (valor_total+c_ant) + (moves.product_qty * moves.price_unit)
                                promedio = valor_total/saldo_stock
                            else:
                                saldo_stock = saldo_stock
                                valor_total = valor_total
                                promedio = promedio


                        data['sec'] = sec
                        data['prod_name'] = prod_name
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
                        tot_sald_ant += sald_ant
                        tot_c_ant += c_ant
                        tot_cantidad += cantidad
                        tot_cantxrecep += cantxrecep
                        tot_cantxdesp += cantxdesp
                        tot_costo += costo
                        tot_costo_mov += costo_mov
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
                        res.append(data)
                else:
                    raise Warning('No existe informacion que mostrar en las fechas ingresadas')
        else:
            prod_prod = prod_obj.search(cr, uid,
                                        [('active', '=', True), ('product_tmpl_id.company_id', '=', company[0]),
                                         ('product_tmpl_id.sale_ok', '=', True)], order='default_code,name_template')
            prod_prod_data = prod_obj.browse(cr, uid, prod_prod)
            sec = 1
            for prod in prod_prod_data:
                tot_puini = 0
                tot_inv = 0
                tot_tot = 0
                tot_fis = 0
                tot_pend = 0
                ingresos = 0
                egresos = 0
                ingresos_ant = 0
                egresos_ant = 0
                saldo_ant = 0
                pendient = 0
                data = {}
                # CSV:11-04-2018:CARGO LOS MOVIMIENTOS ENTRE LAS FECHAS A SACAR
                stock_ing_ids = stoc_mov_obj.search(cr, uid, [('product_id', '=', prod.id),
                                                              ('picking_id.picking_type_id.code', '=', 'incoming'),
                                                              ('date', '>=', date_from), ('date', '<=', date_to),
                                                              ('state', '=', 'done'), ('company_id', '=', company[0])])
                stock_egre_ids = stoc_mov_obj.search(cr, uid, [('product_id', '=', prod.id),
                                                               ('picking_id.picking_type_id.code', '=', 'outgoing'),
                                                               ('date', '>=', date_from), ('date', '<=', date_to),
                                                               ('state', '=', 'done'), ('company_id', '=', company[0])])
                if len(stock_ing_ids) > 0 or len(stock_egre_ids) > 0:
                    stock_ing_data = stoc_mov_obj.browse(cr, uid, stock_ing_ids)
                    stock_egr_data = stoc_mov_obj.browse(cr, uid, stock_egre_ids)
                    for moves in stock_ing_data:
                        ingresos += moves.product_uom_qty
                    for mov_egr in stock_egr_data:
                        egresos += mov_egr.product_uom_qty
                # CSV:11-04-2018:AUMENTO PARA SACAR SALDO ANTERIOR A LA FECHA DEL REPORTE
                stock_ing_ant = stoc_mov_obj.search(cr, uid, [('product_id', '=', prod.id),
                                                              ('picking_id.picking_type_id.code', '=', 'incoming'),
                                                              ('date', '<', date_from), ('state', '=', 'done'),
                                                              ('company_id', '=', company[0])])
                stock_egre_ant = stoc_mov_obj.search(cr, uid, [('product_id', '=', prod.id),
                                                               ('picking_id.picking_type_id.code', '=', 'outgoing'),
                                                               ('date', '<', date_from), ('state', '=', 'done'),
                                                               ('company_id', '=', company[0])])
                if len(stock_ing_ant) > 0 or len(stock_egre_ant) > 0:
                    stock_ing_ant_data = stoc_mov_obj.browse(cr, uid, stock_ing_ant)
                    stock_egr_ant_data = stoc_mov_obj.browse(cr, uid, stock_egre_ant)
                    for moves_ant in stock_ing_ant_data:
                        ingresos_ant += moves_ant.product_uom_qty
                    for mov_egr_ant in stock_egr_ant_data:
                        egresos_ant += mov_egr_ant.product_uom_qty

                if ingresos - egresos >= 0:
                    data['sec'] = sec
                    data['prod'] = prod.default_code + ' ' + prod.name
                    data['fecha'] = prod.create_date
                    data['pre_uni'] = prod.product_tmpl_id.list_price
                    data['inv_real'] = ingresos - egresos
                    data['inv_fis'] = ingresos_ant - egresos_ant
                    data['pendt'] = (ingresos_ant - egresos_ant) + (ingresos - egresos)
                    data['valor_total'] = round(
                        ((ingresos_ant - egresos_ant) + (ingresos - egresos)) * prod.product_tmpl_id.list_price, 2)
                    tot_puini += prod.product_tmpl_id.list_price
                    tot_inv += ingresos - egresos
                    tot_tot += round(
                        ((ingresos_ant - egresos_ant) + (ingresos - egresos)) * prod.product_tmpl_id.list_price, 2)
                    tot_fis += ingresos_ant - egresos_ant
                    tot_pend += (ingresos_ant - egresos_ant) + (ingresos - egresos)
                    data['t_invr'] = tot_inv
                    data['t_puni'] = tot_puini
                    data['t_tot'] = tot_tot
                    data['t_fis'] = tot_fis
                    data['t_pend'] = tot_pend
                    sec += 1
                    res.append(data)
                else:
                    continue
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
        title1 = 'INVENTARIO KARDEX DE'

        ws = wb.add_sheet(title)

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
        ws.write_merge(1, 1, 1, x0, compania.name, style_cabecera)
        ws.write_merge(2, 2, 1, x0, 'Direccion: ' + str(direccion), style_cabecera)
        ws.write_merge(3, 3, 1, x0, 'Ruc: ' + str(ruc), style_cabecera)
        ws.write_merge(5, 5, 1, x0, title1 + " " +
                       time.strftime('%d/%m/%Y', time.strptime(date_from,'%Y-%m-%d')).upper() + " AL " +
                       time.strftime('%d/%m/%Y', time.strptime(date_to, '%Y-%m-%d')).upper(), style_cabecera)

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
        xe = 9
        sec = 1

        ws.write(xi, 1, 'ITEM', style_header)
        ws.write(xi, 2, 'PRODUCTO', style_header)
        ws.write(xi, 3, 'EMPRESA', style_header)
        ws.write(xi, 4, 'ALBARAN', style_header)
        ws.write(xi, 5, 'FECHA INGRESO/SALIDA', style_header)
        ws.write(xi, 6, 'TIPO', style_header)
        ws.write(xi, 7, 'ORDEN DE TRABAJO', style_header)
        ws.write(xi, 8, 'ORIGEN', style_header)
        ws.write(xi, 9, 'DESTINO', style_header)
        ws.write(xi, 10, 'CANTIDAD', style_header)
        ws.write(xi, 11, 'INGRESOS', style_header)
        ws.write(xi, 12, 'SALIDAS', style_header)
        # ws.write(xi, 11, 'SALDO STOCK', style_header)
        ws.write(xi, 13, 'ESTADO', style_header)
        ws.write(xi, 14, 'OBSERVACIONES', style_header)
        totales = self.get_lines_report_wage(cr, uid, form)
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
        ws.write(xe, 9, 'TOTAL', style_header)
        ws.write(xe, 10, tot_cantidad, linea_der)
        ws.write(xe, 11, tot_cantxrecep, linea_der)
        ws.write(xe, 12, tot_cantxdesp, linea_der)
        # ws.write(xe, 11, tot_saldo_stock, linea_der)
        ws.write(xe, 13, '', style_header)

        ws.write(xe, 14, '', style_header)

        xi = xe + 1
        rf = rr = ri = 0
        amount_base = amount_calculate = 0.00
        for linea in totales:
            # detalle
            ws.write(xi, 1, linea['sec'], linea_center)
            ws.write(xi, 2, linea.get('prod_name', ''), linea_izq)
            ws.write(xi, 3, linea.get('empresa', ''), linea_izq)
            ws.write(xi, 4, linea.get('albaran', ''), linea_izq)
            ws.write(xi, 5, linea.get('fecha', ''), linea_izq)
            ws.write(xi, 6, linea.get('tipo', ''), linea_izq)
            ws.write(xi, 7, linea.get('ref', ''), linea_izq)
            ws.write(xi, 8, linea.get('origen', ''), linea_izq)
            ws.write(xi, 9, linea.get('destino', ''), linea_izq)
            ws.write(xi, 10, linea.get('cantidad', ''), linea_der)
            ws.write(xi, 11, linea.get('cantxrecep', ''), linea_der)
            ws.write(xi, 12, linea.get('cantxdesp', ''), linea_der)
            # ws.write(xi, 11, linea.get('saldo_stock', ''), linea_der)
            ws.write(xi, 13, linea.get('estado', ''), linea_izq)

            ws.write(xi, 14, linea.get('notas', ''), linea_izq)
            xi += 1

        ws.col(0).width = 500
        ws.col(1).width = 1500
        ws.col(2).width = 9900
        ws.col(3).width = 10800
        ws.col(4).width = 3250
        ws.col(5).width = 3250
        ws.col(6).width = 4200
        ws.col(7).width = 3250
        ws.col(8).width = 7000
        ws.col(9).width = 7000
        ws.col(14).width = 10000

        ws.row(8).height = 750

        buf = cStringIO.StringIO()

        wb.save(buf)
        out = base64.encodestring(buf.getvalue())
        buf.close()
        name = "%s.xls" % ("Reporte_stock")
        archivo = '/opt/temp/' + name
        res_model = 'stock.inventory.report'
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
    }
    _defaults = {
        'date_from': lambda *a: time.strftime('2018-01-01'),
        'company_id': lambda s, cr, uid, c: s.pool.get('res.company')._company_default_get(cr, uid,
                                                                                           'stock.inventory.report',
                                                                                           context=c),
    }

stock_inventory_report()
