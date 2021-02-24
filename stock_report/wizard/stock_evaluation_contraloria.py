# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#    $Id: account.py 1005 2005-07-25 08:41:42Z nicoe $
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
import time

from openerp.osv import fields, osv
from openerp.tools.translate import _

import xlwt as pycel
import cStringIO
import StringIO
import base64
import csv

class stock_evaluation_contraloria(osv.osv_memory):
    _name = 'stock.evaluation.contraloria'
    _description = 'Reporte Inventario Real'
    
    def action_excel(self, cr, uid, ids, context=None):
        tipo_rep = ''
        if not ids:
            return {'type': 'ir.actions.act_window_close'}
        if context is None:
            context = {}
        form = self.read(cr, uid, ids)[0]
        wb = pycel.Workbook(encoding='utf-8')
        #Formato de la Hoja de Excel
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
                                   )
        
        linea_izq = pycel.easyxf('font: colour black, height 140;'
                                   'align: vertical center, horizontal left, wrap on;'
                                   )
        linea_izq_n = pycel.easyxf('font: colour black, height 140;'
                                   'align: vertical center, horizontal left, wrap on;'
                                   )
        linea_der = pycel.easyxf('font: colour black, height 140;'
                                 'align: vertical center, horizontal right;'
                                  )
            
        ws = wb.add_sheet("Recursos Humanos" )
        ws.show_grid = False
        ws.header_str = u"&LFecha de Impresion: &D Hora: &T&RPagina &P de &N"
        ws.footer_str = u"" 
        compania = self.pool.get('res.users').browse(cr, uid, uid).company_id
        x0 = 11
        ws.write_merge(1, 1, 1, x0, compania.name, style_cabecera)
        ws.write_merge(2, 2, 1, x0, 'Direccion: ' + compania.name)
        ws.write_merge(3, 3, 1, x0, 'Ruc: ' + compania.name, style_cabecera)

        
#         ws.write_merge(5, 5, 1, x0, title + time.strftime('%d de %B del %Y', time.strptime(o.date_stop, '%Y-%m-%d')).upper(), style_cabecera)
        
        ws.fit_num_pages = 1
        ws.fit_height_to_pages = 0
        ws.fit_width_to_pages = 1
        #ws.paper_size_code = 1
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
        
        xi = 7 # Cabecera de Cliente
        sec = 1
        
        ws.write(xi, 1, 'Secuencial', style_header)
        ws.write(xi, 2, 'No Cédula', style_header)
        ws.write(xi, 3, 'Empleado', style_header)
        ws.write(xi, 4, 'Cliente', style_header)
        ws.write(xi, 5, 'Fecha de ingreso', style_header)
        ws.write(xi, 6, 'Fecha de salida', style_header)
        ws.write(xi, 7, 'Cargo', style_header)
        ws.write(xi, 8, 'Motivo', style_header)
        ws.write(xi, 9, 'Valor Liquidación', style_header)
        ws.write(xi, 10, 'Notas', style_header)
        
        xi += 1
        rf = rr = ri = 0
        amount_base = amount_calculate = 0.00
#         if type == 'ing':
#             lineas = self.get_lines_report_wage(cr, uid, form)
#             for linea in lineas:
#                 ws.write(xi, 1, linea['sec'], linea_center)
#                 ws.write(xi, 2, linea.get('ced', ''), linea_izq)
#                 ws.write(xi, 3, linea.get('nom', ''), linea_izq)
#                 ws.write(xi, 4, linea.get('cli', ''), linea_izq)
#                 ws.write(xi, 5, linea.get('ini', ''), linea_izq)
#                 ws.write(xi, 6, linea.get('fin', ''), linea_izq)
#                 ws.write(xi, 7, linea.get('cargo', ''), linea_izq)
#                 ws.write(xi, 8, linea.get('wage', ''), linea_der)
#                 xi += 1
                                                
        ws.col(0).width = 2000
        ws.col(1).width = 2800
        ws.col(2).width = 2200
        ws.col(3).width = 9900
        ws.col(4).width = 9900
        ws.col(5).width = 3500
        ws.col(6).width = 3500
        ws.col(7).width = 8500
        ws.row(7).height = 750
        
        buf = cStringIO.StringIO()
        
        wb.save(buf)
        print "22"
        out = base64.encodestring(buf.getvalue())
        buf.close()
        return self.write(cr, uid, ids, {'data':out, 'name':'Reporte_inventario.xls'})

    _columns = {
        'name':fields.char('Nombre', size=64, required=False, readonly=False),
        'data':fields.binary('Archivo', filters=None),
        'date_from': fields.date('Desde', required=True),
        'date_to': fields.date('Hasta', required=True),
        'p_venta': fields.selection([('matriz','Matriz'),('12octubre','12 de Octubre'),('guayaquil','Guayaquil')], 'Punto Venta', required=True)
#         'depts': fields.many2many('hr.department', 'summary_dept_rel', 'sum_id', 'dept_id', 'Department(s)'),
    }

    _defaults = {
         'date_from': lambda *a: time.strftime('%Y-%m-01'),
         'date_to': lambda *a: time.strftime('%Y-%m-01'),
    }

    def print_report(self, cr, uid, ids, context=None):
        print "***AQUI***"
        data = self.read(cr, uid, ids, context=context)[0]
        datas = {
             'ids': [],
             'model': 'ir.ui.menu',
             'form': data
            }
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'bit_hr_payroll_ec.report_payroll_resume',
            'datas': datas,
        }


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
