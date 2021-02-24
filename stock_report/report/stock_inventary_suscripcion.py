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
import mx.DateTime
from mx.DateTime import RelativeDateTime
import datetime
import xlwt as pycel #Libreria que Exporta a Excel


class stock_inventary_suscripcion(osv.Model):
    _name = "stock.inventary.suscripcion"
    _description = 'Reporte Inventario Suscripcion'
    
        
    
    def get_lines_report_wage(self, cr, uid, form):
        res = []
        date_from = form.get('date_from', False)
        date_to = form.get('date_to', False)
        tipo = form.get('type_pv', False)
        
        prod_obj = self.pool.get('product.product')
        prod_tem_obj = self.pool.get('product.template')
        stoc_mov_obj = self.pool.get('stock.move')
        prod_qty_obj = self.pool.get('stock.quant')
        prod_sus_obj = self.pool.get('product.subscription')
        prod_suslot_obj = self.pool.get('product.subscription.lot')
        tot_inv = 0.00
        tot_puini = 0.00
        tot_tot = 0.00
        tot_entreg = 0.00
        tot_pend = 0.00
        
        if tipo == 'matriz':
            prod_prod = prod_obj.search(cr, uid, [('active', '=', True)], order='name')
            prod_prod_data = prod_obj.browse(cr, uid, prod_prod)
            sec = 1
            for prod in prod_prod_data:
                ingresos = 0
                egresos = 0
                entreg = 0
                pendient = 0
                vendidos = 0
                data = {}
                stock_ing_ids = stoc_mov_obj.search(cr, uid, [('product_id', '=', prod.id), ('location_dest_id', '=', 12), ('date', '>=', date_from), ('date', '<=', date_to), ('state', '=', 'done')])
                stock_egre_ids = stoc_mov_obj.search(cr, uid, [('product_id', '=', prod.id), ('location_id', '=', 12), ('date', '>=', date_from), ('date', '<=', date_to), ('state', '=', 'done')])
                if len(stock_ing_ids) > 0 or len(stock_egre_ids) > 0:
                    stock_ing_data = stoc_mov_obj.browse(cr, uid, stock_ing_ids)
                    stock_egr_data = stoc_mov_obj.browse(cr, uid, stock_egre_ids)
                    for moves in stock_ing_data:
                        ingresos += moves.product_uom_qty
                    for mov_egr in stock_egr_data:
                        egresos += mov_egr.product_uom_qty
                        pr_sus = prod_sus_obj.search(cr, uid, [('move_id', '=', mov_egr.id)])
                        if len(pr_sus) == 0:
                            vendidos = mov_egr.product_uom_qty
                        elif len(pr_sus) == 1:
                            pr_sus_obj =  prod_sus_obj.browse(cr, uid, pr_sus)
                            for susc in pr_sus_obj:
                                entregado = susc.get_deliver
                            if  entregado == True:
                                entreg += mov_egr.product_uom_qty
                            elif entregado == False:
                                pendient += mov_egr.product_uom_qty
                        else:
                            raise osv.except_osv("Error", 'Existen mas de dos lineas de suscripcion asociadas al movimiento')
                    pro_temp_ids = prod_tem_obj.search(cr, uid, [('id', '=', prod.product_tmpl_id.id), ('sale_ok', '=', True), ('pos_categ_id', '!=', 6)])
                    if len(pro_temp_ids) > 0: 
                        pro_temp_data = prod_tem_obj.browse(cr, uid, pro_temp_ids)
                        for prod_temp in pro_temp_data:
                            data['sec'] = sec
                            data['prod'] = prod_temp.name
                            data['fecha'] = prod_temp.date_ing
                            data['pre_uni'] = prod_temp.list_price
                            data['inv_real'] = ingresos - egresos
                            data['entreg'] = entreg
                            data['pendt'] = pendient
                            data['valor_total'] = round((ingresos - egresos) * prod_temp.list_price,2)
                            tot_puini += prod_temp.list_price
                            tot_inv += ingresos - egresos
                            tot_tot += round((ingresos - egresos) * prod_temp.list_price,2)
                            tot_entreg += entreg
                            tot_pend += pendient
                        data['t_invr'] = tot_inv
                        data['t_puni'] = tot_puini
                        data['t_tot'] = tot_tot
                        data['t_entreg'] = tot_entreg
                        data['t_pend'] = tot_pend
                        sec += 1
                        res.append(data)
                    else:
                        continue
                else:
                    continue
        elif tipo == '12oct':
            prod_prod = prod_obj.search(cr, uid, [('active', '=', True)], order='name')
            prod_prod_data = prod_obj.browse(cr, uid, prod_prod)
            sec = 1
            for prod in prod_prod_data:
                ingresos = 0
                egresos = 0
                entreg = 0
                pendient = 0
                vendidos = 0
                data = {}
                stock_ing_ids = stoc_mov_obj.search(cr, uid, [('product_id', '=', prod.id), ('location_dest_id', '=', 19), ('date', '>=', date_from), ('date', '<=', date_to), ('state', '=', 'done')])
                stock_egre_ids = stoc_mov_obj.search(cr, uid, [('product_id', '=', prod.id), ('location_id', '=', 19), ('date', '>=', date_from), ('date', '<=', date_to), ('state', '=', 'done')])
                if len(stock_ing_ids) > 0 or len(stock_egre_ids) > 0:
                    stock_ing_data = stoc_mov_obj.browse(cr, uid, stock_ing_ids)
                    stock_egr_data = stoc_mov_obj.browse(cr, uid, stock_egre_ids)
                    for moves in stock_ing_data:
                        ingresos += moves.product_uom_qty
                    for mov_egr in stock_egr_data:
                        egresos += mov_egr.product_uom_qty
                        pr_sus = prod_sus_obj.search(cr, uid, [('move_id', '=', mov_egr.id)])
                        if len(pr_sus) == 0:
                            vendidos = mov_egr.product_uom_qty
                        elif len(pr_sus) == 1:
                            pr_sus_obj =  prod_sus_obj.browse(cr, uid, pr_sus)
                            for susc in pr_sus_obj:
                                entregado = susc.get_deliver
                            if  entregado == True:
                                entreg += mov_egr.product_uom_qty
                            elif entregado == False:
                                pendient += mov_egr.product_uom_qty
                        else:
                            raise osv.except_osv("Error", 'Existen mas de dos lineas de suscripcion asociadas al movimiento')
                    pro_temp_ids = prod_tem_obj.search(cr, uid, [('id', '=', prod.product_tmpl_id.id), ('sale_ok', '=', True), ('pos_categ_id', '!=', 6)])
                    if len(pro_temp_ids) > 0: 
                        pro_temp_data = prod_tem_obj.browse(cr, uid, pro_temp_ids)
                        for prod_temp in pro_temp_data:
                            data['sec'] = sec
                            data['prod'] = prod_temp.name
                            data['fecha'] = prod_temp.date_ing
                            data['pre_uni'] = prod_temp.list_price
                            data['inv_real'] = ingresos - egresos
                            data['entreg'] = entreg
                            data['pendt'] = pendient
                            data['valor_total'] = round((ingresos - egresos) * prod_temp.list_price,2)
                            tot_puini += prod_temp.list_price
                            tot_inv += ingresos - egresos
                            tot_tot += round((ingresos - egresos) * prod_temp.list_price,2)
                            tot_entreg += entreg
                            tot_pend += pendient
                        data['t_invr'] = tot_inv
                        data['t_puni'] = tot_puini
                        data['t_tot'] = tot_tot
                        data['t_entreg'] = tot_entreg
                        data['t_pend'] = tot_pend
                        sec += 1
                        res.append(data)
                    else:
                        continue
                else:
                    continue
        elif tipo == 'guayaquil':
            prod_prod = prod_obj.search(cr, uid, [('active', '=', True)], order='name')
            prod_prod_data = prod_obj.browse(cr, uid, prod_prod)
            sec = 1
            for prod in prod_prod_data:
                ingresos = 0
                egresos = 0
                entreg = 0
                pendient = 0
                vendidos = 0
                data = {}
                stock_ing_ids = stoc_mov_obj.search(cr, uid, [('product_id', '=', prod.id), ('location_dest_id', '=', 20), ('date', '>=', date_from), ('date', '<=', date_to), ('state', '=', 'done')])
                stock_egre_ids = stoc_mov_obj.search(cr, uid, [('product_id', '=', prod.id), ('location_id', '=', 20), ('date', '>=', date_from), ('date', '<=', date_to), ('state', '=', 'done')])
                if len(stock_ing_ids) > 0 or len(stock_egre_ids) > 0:
                    stock_ing_data = stoc_mov_obj.browse(cr, uid, stock_ing_ids)
                    stock_egr_data = stoc_mov_obj.browse(cr, uid, stock_egre_ids)
                    for moves in stock_ing_data:
                        ingresos += moves.product_uom_qty
                    for mov_egr in stock_egr_data:
                        egresos += mov_egr.product_uom_qty
                        pr_sus = prod_sus_obj.search(cr, uid, [('move_id', '=', mov_egr.id)])
                        if len(pr_sus) == 0:
                            vendidos = mov_egr.product_uom_qty
                        elif len(pr_sus) == 1:
                            pr_sus_obj =  prod_sus_obj.browse(cr, uid, pr_sus)
                            for susc in pr_sus_obj:
                                entregado = susc.get_deliver
                            if  entregado == True:
                                entreg += mov_egr.product_uom_qty
                            elif entregado == False:
                                pendient += mov_egr.product_uom_qty
                        else:
                            raise osv.except_osv("Error", 'Existen mas de dos lineas de suscripcion asociadas al movimiento')
                    pro_temp_ids = prod_tem_obj.search(cr, uid, [('id', '=', prod.product_tmpl_id.id), ('sale_ok', '=', True), ('pos_categ_id', '!=', 6)])
                    if len(pro_temp_ids) > 0: 
                        pro_temp_data = prod_tem_obj.browse(cr, uid, pro_temp_ids)
                        for prod_temp in pro_temp_data:
                            data['sec'] = sec
                            data['prod'] = prod_temp.name
                            data['fecha'] = prod_temp.date_ing
                            data['pre_uni'] = prod_temp.list_price
                            data['inv_real'] = ingresos - egresos
                            data['entreg'] = entreg
                            data['pendt'] = pendient
                            data['valor_total'] = round((ingresos - egresos) * prod_temp.list_price,2)
                            tot_puini += prod_temp.list_price
                            tot_inv += ingresos - egresos
                            tot_tot += round((ingresos - egresos) * prod_temp.list_price,2)
                            tot_entreg += entreg
                            tot_pend += pendient
                        data['t_invr'] = tot_inv
                        data['t_puni'] = tot_puini
                        data['t_tot'] = tot_tot
                        data['t_entreg'] = tot_entreg
                        data['t_pend'] = tot_pend
                        sec += 1
                        res.append(data)
                    else:
                        continue
                else:
                    continue
        return res
    

        
    
    def _format_date(self, date):
        if date:
            campos = date.split('-')
            date = datetime.date(int(campos[0]), int(campos[1]), int(campos[2]))
            return date
    
    def get_days(self, cr, uid, date_start, date_now):
        #date_now = time.strftime("%Y-%m-%d")
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
        type_pv = form.get('type_pv')
        #Formato de la Hoja de Excel
        wb = pycel.Workbook(encoding='utf-8')
        
        style_cabecera = pycel.easyxf('font: colour black, bold True;'
                                      'align: vertical center, horizontal center;'
                                        )
            
        style_cabecerader = pycel.easyxf('font: bold True;'
                                    'align: vertical center, horizontal right;'
                                    )
        
        style_cabeceraizq = pycel.easyxf('font: bold True;'
                                    'align: vertical center, horizontal left;'
                                    )
        
        style_header = pycel.easyxf('font: bold True;'
                                    'align: vertical center, horizontal center, wrap on;'
                                    'borders: left 1, right 1, top 1, bottom 1;')
        
        linea = pycel.easyxf('borders:bottom 1;')
        
        linea_center = pycel.easyxf('font: colour black, height 140;'
                                   'align: vertical center, horizontal center, wrap on;'
                                   'borders: left 1, right 1, top 1, bottom 1;')
        
        linea_izq = pycel.easyxf('font: colour black, height 140;'
                                   'align: vertical center, horizontal left, wrap on;'
                                   'borders: left 1, right 1, top 1, bottom 1;')
        linea_izq_n = pycel.easyxf('font: colour black, height 140;'
                                   'align: vertical center, horizontal left, wrap on;'
                                   )
        linea_der = pycel.easyxf('font: colour black, height 140;'
                                 'align: vertical center, horizontal right;'
                                  'borders: left 1, right 1, top 1, bottom 1;')
        if type_pv == 'matriz':
            title = 'INV. SUSCRIP. MATRIZ'
        elif type_pv == '12oct':
            title = 'INV. SUSCRIP. 12 DE OCTUBRE'
        elif type_pv == 'guayaquil':
            title = 'INV. SUSCRIP. GUAYAQUIL'
            
        ws = wb.add_sheet(title)
        
        ws.show_grid = False
        ws.header_str = u"&LFecha de Impresion: &D Hora: &T&RPagina &P de &N"
        ws.footer_str = u"" 
        compania = self.pool.get('res.users').browse(cr, uid, uid).company_id
        print "compania", compania.name
        print "direccion", compania.partner_id
        calle1 = compania.partner_id.street
        calle2 = compania.partner_id.street2
        ruc = compania.partner_id.part_number
        if calle1 and calle2:
            direccion = str(calle1.encode('UTF-8')) +" "+ str(calle2.encode('UTF-8'))
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
        ws.write_merge(2, 2, 1, x0, 'Direccion: ' + direccion, style_cabecera)
        ws.write_merge(3, 3, 1, x0, 'Ruc: ' + ruc_part, style_cabecera)
        ws.write_merge(5, 5, 1, x0, title +" "+ time.strftime('%d de %B del %Y', time.strptime(date_to, '%Y-%m-%d %H:%M:%S')).upper(), style_cabecera)
        
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
        
        #info = self.get_payroll(cr, uid, form)
        
        xi = 8 # Cabecera de Cliente
        xe = 9
        sec = 1
        
        if type_pv == 'matriz':
            ws.write(xi, 1, 'SECUENCIAL', style_header)
            ws.write(xi, 2, 'PRODUCTO', style_header)
            ws.write(xi, 3, 'FECHA PUBLICACION', style_header)
            ws.write(xi, 4, 'INVENTARIO REAL', style_header)
            ws.write(xi, 5, 'ENTREGADO', style_header)
            ws.write(xi, 6, 'POR ENTREGAR', style_header)
            ws.write(xi, 7, 'PRECIO UNITARIO', style_header)
            ws.write(xi, 8, 'VALOR TOTAL', style_header)
            totales = self.get_lines_report_wage(cr, uid, form)
            for tot in totales:
                print "Total", tot
                t_inv = tot.get('t_invr', '')
                t_pun = tot.get('t_puni', '')
                t_tot = tot.get('t_tot', '')
                t_entreg = tot.get('t_entreg', '')
                t_pend = tot.get('t_pend', '')
            ws.write(xe, 1, '', style_header)
            ws.write(xe, 2, '', style_header)
            ws.write(xe, 3, 'TOTAL', style_header)
            ws.write(xe, 4, t_inv, linea_der)
            ws.write(xe, 5, t_entreg, linea_der)
            ws.write(xe, 6, t_pend, linea_der)
            ws.write(xe, 7, t_pun, linea_der)
            ws.write(xe, 8, t_tot, linea_der)
            
        if type_pv == '12oct':
            ws.write(xi, 1, 'SECUENCIAL', style_header)
            ws.write(xi, 2, 'PRODUCTO', style_header)
            ws.write(xi, 3, 'FECHA PUBLICACION', style_header)
            ws.write(xi, 4, 'INVENTARIO REAL', style_header)
            ws.write(xi, 5, 'ENTREGADO', style_header)
            ws.write(xi, 6, 'POR ENTREGAR', style_header)
            ws.write(xi, 7, 'PRECIO UNITARIO', style_header)
            ws.write(xi, 8, 'VALOR TOTAL', style_header)
            totales = self.get_lines_report_wage(cr, uid, form)
            for tot in totales:
                print "Total", tot
                t_inv = tot.get('t_invr', '')
                t_pun = tot.get('t_puni', '')
                t_tot = tot.get('t_tot', '')
                t_entreg = tot.get('t_entreg', '')
                t_pend = tot.get('t_pend', '')
            ws.write(xe, 1, '', style_header)
            ws.write(xe, 2, '', style_header)
            ws.write(xe, 3, 'TOTAL', style_header)
            ws.write(xe, 4, t_inv, linea_der)
            ws.write(xe, 5, t_entreg, linea_der)
            ws.write(xe, 6, t_pend, linea_der)
            ws.write(xe, 7, t_pun, linea_der)
            ws.write(xe, 8, t_tot, linea_der)
            
        if type_pv == 'guayaquil':
            ws.write(xi, 1, 'SECUENCIAL', style_header)
            ws.write(xi, 2, 'PRODUCTO', style_header)
            ws.write(xi, 3, 'FECHA PUBLICACION', style_header)
            ws.write(xi, 4, 'INVENTARIO REAL', style_header)
            ws.write(xi, 5, 'ENTREGADO', style_header)
            ws.write(xi, 6, 'POR ENTREGAR', style_header)
            ws.write(xi, 7, 'PRECIO UNITARIO', style_header)
            ws.write(xi, 8, 'VALOR TOTAL', style_header)
            totales = self.get_lines_report_wage(cr, uid, form)
            for tot in totales:
                print "Total", tot
                t_inv = tot.get('t_invr', '')
                t_pun = tot.get('t_puni', '')
                t_tot = tot.get('t_tot', '')
                t_entreg = tot.get('t_entreg', '')
                t_pend = tot.get('t_pend', '')
            ws.write(xe, 1, '', style_header)
            ws.write(xe, 2, '', style_header)
            ws.write(xe, 3, 'TOTAL', style_header)
            ws.write(xe, 4, t_inv, linea_der)
            ws.write(xe, 5, t_entreg, linea_der)
            ws.write(xe, 6, t_pend, linea_der)
            ws.write(xe, 7, t_pun, linea_der)
            ws.write(xe, 8, t_tot, linea_der)

        
        xi = xe + 1
        rf = rr = ri = 0
        amount_base = amount_calculate = 0.00
        if type_pv == 'matriz':
            lineas = self.get_lines_report_wage(cr, uid, form)
            print "***lineas: ", lineas
            for linea in lineas:
                #detalle
                ws.write(xi, 1, linea['sec'], linea_center)
                ws.write(xi, 2, linea.get('prod', ''), linea_izq)
                ws.write(xi, 3, linea.get('fecha', ''), linea_izq)
                ws.write(xi, 4, linea.get('inv_real', ''), linea_der)
                ws.write(xi, 5, linea.get('entreg', ''), linea_der)
                ws.write(xi, 6, linea.get('pendt', ''), linea_der)
                ws.write(xi, 7, linea.get('pre_uni', ''), linea_der)
                ws.write(xi, 8, linea.get('valor_total', ''), linea_der)
                xi += 1
                #totales
#             ws.write(10, 4, linea.get('t_invr', ''), linea_der)
#             ws.write(10, 5, linea.get('t_puni', ''), linea_der)
#             ws.write(10, 6, linea.get('t_tot', ''), linea_der)
        if type_pv == '12oct':
            lineas = self.get_lines_report_wage(cr, uid, form)
            print "***lineas: ", lineas
            for linea in lineas:
                #totales
#                 ws.write(xe, 4, linea.get('t_invr', ''), linea_der)
#                 ws.write(xe, 5, linea.get('t_puni', ''), linea_der)
#                 ws.write(xe, 6, linea.get('t_tot', ''), linea_der)
                #detalle
                ws.write(xi, 1, linea['sec'], linea_center)
                ws.write(xi, 2, linea.get('prod', ''), linea_izq)
                ws.write(xi, 3, linea.get('fecha', ''), linea_izq)
                ws.write(xi, 4, linea.get('inv_real', ''), linea_der)
                ws.write(xi, 5, linea.get('entreg', ''), linea_der)
                ws.write(xi, 6, linea.get('pendt', ''), linea_der)
                ws.write(xi, 7, linea.get('pre_uni', ''), linea_der)
                ws.write(xi, 8, linea.get('valor_total', ''), linea_der)
                xi += 1
        if type_pv == 'guayaquil':
            lineas = self.get_lines_report_wage(cr, uid, form)
            print "***lineas: ", lineas
            for linea in lineas:
                #totales
#                 ws.write(xe, 4, linea.get('t_invr', ''), linea_der)
#                 ws.write(xe, 5, linea.get('t_puni', ''), linea_der)
#                 ws.write(xe, 6, linea.get('t_tot', ''), linea_der)
                #detalle
                ws.write(xi, 1, linea['sec'], linea_center)
                ws.write(xi, 2, linea.get('prod', ''), linea_izq)
                ws.write(xi, 3, linea.get('fecha', ''), linea_izq)
                ws.write(xi, 4, linea.get('inv_real', ''), linea_der)
                ws.write(xi, 5, linea.get('entreg', ''), linea_der)
                ws.write(xi, 6, linea.get('pendt', ''), linea_der)
                ws.write(xi, 7, linea.get('pre_uni', ''), linea_der)
                ws.write(xi, 8, linea.get('valor_total', ''), linea_der)
                xi += 1
                                                
        ws.col(0).width = 1000
        ws.col(1).width = 3250
        ws.col(2).width = 9900
        ws.col(3).width = 5000
        ws.col(4).width = 3250
        ws.col(5).width = 3250
        ws.col(6).width = 3250
        ws.col(7).width = 3250
        ws.col(8).width = 3250
        
        ws.row(8).height = 750

        
        buf = cStringIO.StringIO()
        
        wb.save(buf)
        out = base64.encodestring(buf.getvalue())
        buf.close()
        name = "%s.xls" % ("Reporte_suscripcion")
        archivo = '/opt/temp/' + name
        res_model = 'stock.inventary.suscripcion'
        id = ids and type(ids) == type([]) and ids[0] or ids
        self.write(cr, uid, ids, {'data':out, 'name':'Reporte_suscripcion.xls'})

        self.load_doc(cr, uid, out, id, name, archivo, res_model)
        return {
            'type': 'ir.actions.client',
            'tag': 'reload'
        }

    def load_doc(self, cr, uid, out, id, data_fname, archivo, res_model):
   #     datas = open(archivo, 'rb')
        attach_vals = {
            'name': data_fname,
            'datas_fname': data_fname,
            'res_model': res_model,
#             'parent_id': activity.report_directory_id.id,
             'datas': out,
            'type': 'binary',
            'file_type': 'file_type',
       #     'res_id': period_id
        }
        if id:
            attach_vals.update( {'res_id': id} )
        self.pool.get('ir.attachment').create(cr, uid, attach_vals)

    _columns = {
        'name':fields.char('Nombre', size=64, required=False, readonly=False),
        'data':fields.binary('Archivo', filters=None),
        'date_from': fields.datetime('Fecha Desde'),
        'date_to': fields.datetime('Fecha Hasta'),
        'type_pv':fields.selection([('matriz', 'Matriz'), ('12oct', '12 Octubre'), ('guayaquil', 'Guayaquil')], 'Punto Venta', required=True),
    }
stock_inventary_suscripcion()