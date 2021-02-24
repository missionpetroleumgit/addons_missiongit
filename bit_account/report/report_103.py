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
from openerp.exceptions import Warning
import xlwt as pycel #Libreria que Exporta a Excel


ACTION_DICT = {
    'view_type': 'form',
    'view_mode': 'form',
    'res_model': 'base.module.upgrade',
    'target': 'new',
    'type': 'ir.actions.act_window',
    'nodestroy': True,
}

class report_103(osv.Model):
    _name = "report.103"
    _description = 'Reporte Formulario 103'
    
        
    
    def get_lines_report_wage(self, cr, uid, form):
        res = []
 
        period = form.get('period_id', False)
        print "PERIODO", period
        facturas = self.pool.get('account.invoice')
        impuestos = self.pool.get('account.tax.code')
        impuestos_factura = self.pool.get('account.invoice.tax')
        roles = self.pool.get('hr.payslip.line')
        personal_expenses = self.pool.get('hr.personal.expense')

        data = {}
        if period:
            imp_id = impuestos.search(cr, uid, [('form', '=', '103')], order='code')
            imp_data = impuestos.browse(cr, uid, imp_id)
            sec = 1
            
            for code_imp in imp_data:
                base = 0.00
                ret = 0.00
                data = {}
                inv_ids = facturas.search(cr, uid, [('period_id', '=', period[0]),('state', 'in', ['paid','open']),('type', '=', 'in_invoice')], order='id')
                print "facturas", inv_ids
                print "code imp", code_imp.id 
                imp_fact = impuestos_factura.search(cr, uid, [('base_code_id', '=', code_imp.id),('invoice_id', 'in', inv_ids)])
                print "lista ids facturas", imp_fact
                if len(imp_fact)>0:
                    imp_fact_data = impuestos_factura.browse(cr, uid, imp_fact)
                    for fact_imp in imp_fact_data:
                        data = {}
                        base += abs(fact_imp.base_amount)
                        ret += abs(fact_imp.tax_amount)
                        if fact_imp.deduction_id:
                            num_ret = fact_imp.deduction_id.number
                        else:
                            num_ret = ''
                        data['sec'] = sec
                        data['name'] = 'FACTURA:'+" " + str(fact_imp.invoice_id.number)+' RET:'+" "+str(num_ret)
                        data['code'] = code_imp.code
                        data['base_imp'] = abs(fact_imp.base_amount)
                        data['code_imp'] = fact_imp.tax_code_id.code
                        data['valor_ret'] = abs(fact_imp.tax_amount)
                        data['impuesto'] = False
                        data['partner'] = fact_imp.invoice_id.partner_id.name
                        res.append(data)
                    data = {}
                    data['sec'] = sec
                    data['name'] = code_imp.name
                    data['code'] = code_imp.code
                    data['base_imp'] = base
                    data['code_imp'] = fact_imp.tax_code_id.code
                    data['valor_ret'] = ret
                    data['impuesto'] = True
                    data['partner'] = fact_imp.invoice_id.partner_id.name
                    sec += 1
                    res.append(data)
                elif code_imp.code == '302':
                    valor_base = 0.00
                    valor_ret = 0.00
                    exp_value = 0.00
                    apiess_value = 0.00
                    total_base = 0.00
                    base_rent = roles.search(cr, uid, [('code', '=', 'SUBBIESS'),('slip_id.period_id', '=', period[0])])
                    if len(base_rent)>0:
                        base_rent_data = roles.browse(cr, uid, base_rent)
                        for bas_ret in base_rent_data:
                            valor_base += bas_ret.amount
                    ret_rent = roles.search(cr, uid, [('code', '=', 'EGRIR'),('slip_id.period_id', '=', period[0])])
                    if len(ret_rent)>0:
                        ret_rent_data = roles.browse(cr, uid, ret_rent)
                        for r_ret in ret_rent_data:
                            valor_ret += r_ret.amount
                    expenses = personal_expenses.search(cr, uid, [('fiscalyear_id.period_ids.name', '=', period[0])])
                    if len(expenses) > 0:
                        if exp.total_anual_cost > 0:
                            anual_cost_value = exp.total_anual_cost / 12
                        for exp in expenses:
                            exp_value += anual_cost_value
                    base_apiess = roles.search(cr, uid,
                                             [('code', '=', 'APIES'), ('slip_id.period_id', '=', period[0])])
                    if len(base_rent) > 0:
                        base_apiess_data = roles.browse(cr, uid, base_apiess)
                        for base_apies in base_apiess_data:
                            apiess_value += base_apies.amount
                    total_base = valor_base - exp_value - apiess_value
                    data['sec'] = sec
                    data['name'] = code_imp.name
                    data['code'] = code_imp.code
                    data['base_imp'] = total_base
                    data['code_imp'] = '352'
                    data['valor_ret'] = valor_ret
                    data['impuesto'] = True
                    sec += 1
                    res.append(data)                    
        #print "res", res.reverse()
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
        
        period = form.get('period_id')
        print "PERIOD", period[0]
        per_ids = self.pool.get('account.period').browse(cr, uid, [period[0]])[0]
        print "OBJ PERIOD", per_ids.id 
        #path = form.get('path')
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
        
        linea_center_red = pycel.easyxf('font: bold True, colour blue, height 140;'
                                   'align: vertical center, horizontal center, wrap on;'
                                   'borders: left 1, right 1, top 1, bottom 1;')
        
        linea_izq = pycel.easyxf('font: colour black, height 140;'
                                   'align: vertical center, horizontal left, wrap on;'
                                   'borders: left 1, right 1, top 1, bottom 1;')
        
        linea_izq_red = pycel.easyxf('font: bold True, colour blue, height 140;'
                                   'align: vertical center, horizontal left, wrap on;'
                                   'borders: left 1, right 1, top 1, bottom 1;')
        
        linea_izq_n = pycel.easyxf('font: bold True, colour black, height 140;'
                                   'align: vertical center, horizontal left, wrap on;'
                                   'borders: left 1, right 1, top 1, bottom 1;')
        
        linea_der = pycel.easyxf('font: colour black, height 140;'
                                 'align: vertical center, horizontal right;'
                                  'borders: left 1, right 1, top 1, bottom 1;')
        
        linea_der_red = pycel.easyxf('font: colour blue, height 140;'
                                 'align: vertical center, horizontal right;'
                                  'borders: left 1, right 1, top 1, bottom 1;')
        if period:
            title = 'FORMULARIO-103'
            title1 = 'FORMULARIO-103'
            
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
       # ws.write_merge(2, 2, 1, x0, 'Direccion: ' + direccion, style_cabecera)
        ws.write_merge(3, 3, 1, x0, title , style_cabecera)
        ws.write_merge(5, 5, 1, x0, title1 +" "+ time.strftime('%d/%m/%Y', time.strptime(per_ids.date_start, '%Y-%m-%d')).upper() +" AL "+ time.strftime('%d/%m/%Y', time.strptime(per_ids.date_stop, '%Y-%m-%d')).upper(), style_cabecera)
        
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
        
        if period:
            ws.write(xi, 1, 'SECUENCIAL', style_header)
            ws.write(xi, 2, 'PROVEEDOR / CLIENTE', style_header)
            ws.write(xi, 3, 'NOMBRE', style_header)
            ws.write(xi, 4, 'CODIGO BASE', style_header)
            ws.write(xi, 5, 'BASE IMPONIBLE', style_header)
            ws.write(xi, 6, 'CODIGO IMPUESTO', style_header)
            ws.write(xi, 7, 'VALOR RETENIDO', style_header)
            totales = self.get_lines_report_wage(cr, uid, form)
#             for tot in totales:
#                 print "Total", tot
#                 t_inv = tot.get('t_invr', '')
#                 t_pun = tot.get('t_puni', '')
#                 t_tot = tot.get('t_tot', '')
#                 t_fis = tot.get('t_fis', '')
#                 t_pend = tot.get('t_pend', '')
#             ws.write(xe, 1, '', style_header)
#             ws.write(xe, 2, '', style_header)
#             ws.write(xe, 3, 'TOTAL', style_header)
#             ws.write(xe, 4, t_fis, linea_der)
#             ws.write(xe, 5, t_inv, linea_der)
#             ws.write(xe, 6, t_pend, linea_der)
#             ws.write(xe, 7, t_pun, linea_der)
#             ws.write(xe, 8, t_tot, linea_der)
            
        xi = xe + 1
        rf = rr = ri = 0
        amount_base = amount_calculate = 0.00
        if period:
            lineas = self.get_lines_report_wage(cr, uid, form)
            #print "***lineas: ", lineas
            for linea in lineas:
                print "OJO ES IMP", linea.get('impuesto', '')
                if not linea.get('impuesto', ''):
                    ws.write(xi, 1, linea.get('sec', ''), linea_center)
                    ws.write(xi, 2, linea.get('partner', ''), linea_center)
                    ws.write(xi, 3, linea.get('name', ''), linea_izq)
                    ws.write(xi, 4, linea.get('code', ''), linea_center)
                    ws.write(xi, 5, linea.get('base_imp', ''), linea_der)
                    ws.write(xi, 6, linea.get('code_imp', ''), linea_center)
                    ws.write(xi, 7, linea.get('valor_ret', ''), linea_der)
                    xi += 1
                elif linea.get('impuesto', ''):
                    ws.write(xi, 1, linea.get('sec', ''), linea_center_red)
                    ws.write(xi, 2, linea.get('', ''), linea_center)
                    ws.write(xi, 3, linea.get('name', ''), linea_izq_red)
                    ws.write(xi, 4, linea.get('code', ''), linea_center_red)
                    ws.write(xi, 5, linea.get('base_imp', ''), linea_der_red)
                    ws.write(xi, 6, linea.get('code_imp', ''), linea_center_red)
                    ws.write(xi, 7, linea.get('valor_ret', ''), linea_der_red)
                    xi += 1
                #totales
#             ws.write(10, 4, linea.get('t_invr', ''), linea_der)
#             ws.write(10, 5, linea.get('t_puni', ''), linea_der)
#             ws.write(10, 6, linea.get('t_tot', ''), linea_der)
                                                
        ws.col(0).width = 1000
        ws.col(1).width = 3250
        ws.col(2).width = 11100
        ws.col(3).width = 13900
        ws.col(4).width = 3250
        ws.col(5).width = 3250
        ws.col(6).width = 3250
        ws.col(7).width = 3250
        ws.col(8).width = 3250
        
        ws.row(8).height = 750

#        buf = cStringIO.StringIO()
#         name = "%s%s%s.xls" % (path, "Reporte_detallado_", datetime.datetime.now())
#         try:
#             wb.save(name)
#             raise Warning('Archivo salvado correctamente')
#         except ValueError:
#             raise Warning('Error a la hora de salvar el archivo')        
#         buf = StringIO.StringIO()
#         name = "%s%s.xls" % ("Reporte_detallado", datetime.datetime.now())
#         name1 = wb.save(name)
#         out = base64.encodestring(buf.getvalue())
# #        buf.close()
#         return self.write(cr, uid, ids, {'data':name1, 'name':name})
        buf = cStringIO.StringIO()
        
        wb.save(buf)
        out = base64.encodestring(buf.getvalue())
        buf.close()
        name = "%s.xls" % ("Reporte_103")
        archivo = '/opt/temp/' + name
        res_model = 'report.103'
        id = ids and type(ids) == type([]) and ids[0] or ids
        self.load_doc(cr, uid, out, id, name, archivo, res_model)

        return {
            'type': 'ir.actions.client',
            'tag': 'reload'
        }


        # return self.write(cr, uid, ids, {'data':out, 'name':name})

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
        'name':fields.char('', size=64, required=False, readonly=False),
        'data':fields.binary('', filters=None),
#         'date_from': fields.date('Fecha Desde'),
#         'date_to': fields.date('Fecha Hasta'),
        #'path': fields.char('Ruta'),
        'period_id':fields.many2one('account.period', 'Periodo', required=True),
    }
#     _defaults = {
#         'date_from': lambda * a: time.strftime('2015-07-01'),
#     }
report_103()
