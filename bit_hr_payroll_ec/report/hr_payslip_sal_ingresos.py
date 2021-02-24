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
from .. import hr_payroll
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


class hr_payslip_ing_salidas(osv.Model):
    _name = "hr.payslip.ing.salidas"
    _description = 'Ingreso y Salidas'



    def get_lines_report_wage(self, cr, uid, form):
        res = []
        date_from = form.get('date_from', False)
        date_to = form.get('date_to', False)
        tipo = form.get('type_hr', False)

        hr_employee_obj = self.pool.get('hr.employee')
        hr_contract_obj = self.pool.get('hr.contract')

        if tipo == 'salida':

            hr_contract = self.pool.get('hr.contract')
            contract_ids = hr_contract.search(cr, uid, [('date_end', '>=', date_from), ('date_end', '<=', date_to)], order='company_id, name')
            contract_data = hr_contract.browse(cr, uid, contract_ids)
            sec = 1

            for contrato in contract_data:
                salidas = []
                data = {}
                data['sec'] = sec
		data['comp'] = contrato.employee_id.company_id.name
                data['ced'] = contrato.employee_id.identification_id
                data['nom'] = contrato.employee_id.name_related
                data['car'] = contrato.employee_id.job_id.name
                data['neg'] = contrato.employee_id.business_unit_id.name
                data['fing'] = contrato.employee_id.contract_id.date_start
                data['fsal'] = contrato.employee_id.contract_id.date_end

                hr_liquidacion = self.pool.get('hr.employee.liquidation')
                liquidacion_ids = hr_liquidacion.search(cr, uid, [('employee_id', '=', contrato.employee_id.id)])
                liquidacion_data = hr_liquidacion.browse(cr, uid, liquidacion_ids)
                sec = 1
                for liquidacion in liquidacion_data:
                    if liquidacion.type == 'renuncia':
                        data['mtv'] = 'Renuncia Voluntaria'
                    if liquidacion.type == 'intem_fijo':
                        data['mtv'] = 'Por Despido Intempestivo'
                    if liquidacion.type == 'intem_faltantes':
                        data['mtv'] = 'Terminación de contrato periodo de prueba'
                    if liquidacion.type == 'deshaucio':
                        data['mtv'] = 'Deshaucio'

                    data['obs'] = liquidacion.observation
                sec += 1
                res.append(data)
        elif tipo == 'ingreso':

            hr_contract = self.pool.get('hr.contract')
            contract_ids = hr_contract.search(cr, uid, [('date_start', '>=', date_from), ('date_start', '<=', date_to)], order='company_id, name')
            contract_data = hr_contract.browse(cr, uid, contract_ids)
            sec = 1

            for contrato in contract_data:
                ingresos = []
                data = {}
                data['sec'] = sec
		data['comp'] = contrato.employee_id.company_id.name
                data['ced'] = contrato.employee_id.identification_id
                data['nom'] = contrato.employee_id.name_related
                data['car'] = contrato.employee_id.job_id.name
                data['neg'] = contrato.employee_id.business_unit_id.name
                data['fing'] = contrato.employee_id.contract_id.date_start
                data['vctr'] = contrato.employee_id.contract_id.wage

                sec += 1
                res.append(data)
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
            return {'type_hr': 'ir.actions.act_window_close'}
        if context is None:
            context = {}
        form = self.read(cr, uid, ids)[0]
        date_from = form.get('date_from')
        date_to = form.get('date_to')
        type_hr = form.get('type_hr')
	company_id = form.get('company_id', False)
        #Formato de la Hoja de Excel
        wb = pycel.Workbook(encoding='utf-8')

        style_cabecera = pycel.easyxf('font: colour black, bold True;'
                                      'align: vertical center, horizontal center;'
                                        )

#         style_titulo = pycel.easyxf('font: colour blue, bold True, 16px;'
#                                       'align: vertical center, horizontal center;'
#                                         )

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
        if type_hr == 'salida':
            title = 'REPORTE DE SALIDA AL '
        elif type_hr == 'ingreso':
            title = 'REPORTE DE INGRESO AL'

        ws = wb.add_sheet(title)

        ws.show_grid = False
        ws.header_str = u"&LFecha de Impresion: &D Hora: &T&RPagina &P de &N"
        ws.footer_str = u""
        compania = self.pool.get('res.users').browse(cr, uid, uid).company_id
        print "compania", compania.name
        print "direccion", compania.partner_id
        x0 = 11
        ws.write_merge(1, 1, 1, x0, compania.name, style_cabecera)
        ws.write_merge(2, 2, 1, x0, 'Direccion: ' + compania.partner_id.street, style_cabecera)
        ws.write_merge(3, 3, 1, x0, 'Ruc: ' + compania.partner_id.part_number, style_cabecera)
        ws.write_merge(5, 5, 1, x0, title + time.strftime('%d de %B del %Y', time.strptime(date_to, '%Y-%m-%d')).upper(), style_cabecera)

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
        sec = 1

	if type_hr == 'salida':
            ws.write(xi, 1, 'SECUENCIAL', style_header)
            ws.write(xi, 2, 'COMPANIA', style_header)
            ws.write(xi, 3, 'EMPLEADO', style_header)
            ws.write(xi, 4, 'No CEDULA', style_header)
            ws.write(xi, 5, 'CARGO', style_header)
            ws.write(xi, 6, 'UNIDAD DE NEGOCIO', style_header)
            ws.write(xi, 7, 'FECHA DE INGRESO', style_header)
            ws.write(xi, 8, 'FECHA DE SALIDA', style_header)
            ws.write(xi, 9, 'MOTIVO', style_header)
            ws.write(xi, 10, 'OBSERVACION', style_header)

        if type_hr == 'ingreso':
            ws.write(xi, 1, 'SECUENCIAL', style_header)
            ws.write(xi, 2, 'COMPANIA', style_header)
            ws.write(xi, 3, 'EMPLEADO', style_header)
            ws.write(xi, 4, 'No CEDULA', style_header)
            ws.write(xi, 5, 'CARGO', style_header)
            ws.write(xi, 6, 'UNIDAD DE NEGOCIO', style_header)
            ws.write(xi, 7, 'FECHA DE INGRESO', style_header)
            ws.write(xi, 8, 'SUELDO', style_header)

        
        xi += 1
        rf = rr = ri = 0
        amount_base = amount_calculate = 0.00
        if type_hr == 'salida':
            lineas = self.get_lines_report_wage(cr, uid, form)
            print "***lineas: ", lineas
            for linea in lineas:
                ws.write(xi, 1, linea['sec'], linea_center)
                ws.write(xi, 2, linea.get('comp', ''), linea_izq)
                ws.write(xi, 3, linea.get('nom', ''), linea_izq)
                ws.write(xi, 4, linea.get('ced', ''), linea_izq)
                ws.write(xi, 5, linea.get('car', ''), linea_izq)
                ws.write(xi, 6, linea.get('neg', ''), linea_izq)
                ws.write(xi, 7, linea.get('fing', ''), linea_der)
                ws.write(xi, 8, linea.get('fsal', ''), linea_der)
                ws.write(xi, 9, linea.get('mtv', ''), linea_izq)
                ws.write(xi, 10, linea.get('obs', ''), linea_izq)
                xi += 1
        if type_hr == 'ingreso':
            lineas = self.get_lines_report_wage(cr, uid, form)
            print "***lineas: ", lineas
            for linea in lineas:
                ws.write(xi, 1, linea['sec'], linea_center)
                ws.write(xi, 2, linea.get('comp', ''), linea_izq)
                ws.write(xi, 3, linea.get('nom', ''), linea_izq)
                ws.write(xi, 4, linea.get('ced', ''), linea_izq)
                ws.write(xi, 5, linea.get('car', ''), linea_izq)
                ws.write(xi, 6, linea.get('neg', ''), linea_izq)
                ws.write(xi, 7, linea.get('fing', ''), linea_der)
                ws.write(xi, 8, linea.get('vctr', ''), linea_der)
                xi += 1

        ws.col(0).width = 2000
        ws.col(1).width = 3800
        ws.col(2).width = 9900
        ws.col(3).width = 5000
        ws.col(4).width = 6900
        ws.col(5).width = 3250
        ws.col(6).width = 2500
        ws.col(7).width = 2500
        ws.col(8).width = 8500
        ws.col(9).width = 9500
        ws.col(10).width = 6500

        ws.row(8).height = 750

        buf = cStringIO.StringIO()

        wb.save(buf)
        out = base64.encodestring(buf.getvalue())
        buf.close()
        return self.write(cr, uid, ids, {'data':out, 'txt_filename':'Reporte_RR_HH.xls', 'name':'Reporte_RR_HH.xls'})

    _columns = {
        'name' : fields.char('Descripcion', size=16,required=False, readonly=False),
        'date_from': fields.date('Fecha Desde'),
        'date_to': fields.date('Fecha Hasta'),
        'txt_filename': fields.char(),
        'type_hr':fields.selection([('salida', 'Salida'), ('ingreso', 'Ingreso')], 'Tipo De Reporte', required=True),
        'data':fields.binary('Archivo', filters=None),
    }
    
    

hr_payslip_ing_salidas()
 
        
              
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:


