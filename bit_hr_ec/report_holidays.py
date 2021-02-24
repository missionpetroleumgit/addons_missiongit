#!/usr/bin/env python
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
import time
from dateutil.relativedelta import relativedelta
from openerp.report import report_sxw
from openerp.addons.account.report.common_report_header import common_report_header
from datetime import datetime
import xlwt as pycel
import base64
import StringIO
import cStringIO

class hr_payroll_vacaciones_report(osv.osv_memory):
    _name = 'hr.payroll.vacaciones.report'
    _description = 'Reportes de Vacaciones'
    
    
    _columns = {
        'data':fields.binary('Archivo', filters=None),
        'file_name': fields.char('Nombre Archivo'),
        'region': fields.selection([('sierra', 'Sierra'), ('costa', 'Costa')], 'Region', required=True),
        'company_id': fields.many2one('res.company', 'Compania')
    }

    
    def get_default_employee(self, cr, uid, ids, context=None):
        eval_obj = self.browse(cr, uid, ids)[0]
 #       context.update({'planes_ids':eval_obj.planes_ids.id})
        return {
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'hr.eval.group.employee',
                'type': 'ir.actions.act_window',
                'target': 'new',
                'context': context
                }
        
    def get_datos(self, cr, uid, region, company_id):
        print "region:  ", region
        res=[]
        employee_pool = self.pool.get('hr.employee')
        data = {}
        domain = list()
        if company_id:
            domain.append(('company_id','=',company_id))
        if region:
            domain.append(('state_emp','=','active'))
            domain.append(('region','=',region))
            employee_ids = employee_pool.search(cr, uid, domain)
        else:
            domain.append(('state_emp','=','active'))
            employee_ids = employee_pool.search(cr, uid, domain)
        print "datos_exp:  ", employee_ids
        if employee_ids:
            sec = 1
            for employee_id in employee_ids:
                employee = employee_pool.browse(cr, uid, employee_id, context=None)
                print "employee:  ", employee
                data = {}
                data['sec'] = sec
                data['identif'] = employee.identification_id
                data['empleado'] = employee.name
                data['categoria'] = employee.job_id.name
                data['dias_vacacion'] = employee.availables_days
                data['region'] = employee.region
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
            return {'region': 'ir.actions.act_window_close'}
        if context is None:
            context = {}
        form = self.read(cr, uid, ids)[0]
        company_id = form.get('company_id')
        region = form.get('region')
        print "region11: ",region
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
        title = 'REPORTE DE VACACIONES'

            
        ws = wb.add_sheet('Reporte de Vacaciones')

        ws.show_grid = False
        ws.header_str = u"&LFecha de Impresion: &D Hora: &T&RPagina &P de &N"
        ws.footer_str = u""
        compania = self.pool.get('res.users').browse(cr, uid, uid).company_id
        x0 = 6
        ws.write_merge(1, 1, 1, 5, compania.name, style_cabecera)
        ws.write_merge(2, 2, 1, 5, 'Direccion: ' + compania.partner_id.street, style_cabecera)
        ws.write_merge(3, 3, 1, 5, 'Ruc: ' + compania.partner_id.part_number, style_cabecera)


        
        ws.write_merge(5, 5, 1, x0, title , style_cabecera)
        
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
        ws.write(xi, 2, 'Cédula', style_header)
        ws.write(xi, 3, 'Empleado', style_header)
        ws.write(xi, 4, 'Cargo', style_header)
        ws.write(xi, 5, 'Region', style_header)
        ws.write(xi, 6, 'Días Disponibles', style_header)
            
        xi += 1
        holidays = self.get_datos(cr, uid, region, company_id)
        print "holidays: ", holidays
        for holi in holidays:
            ws.write(xi, 1, holi['sec'], linea_center)
            ws.write(xi, 2, holi.get('identif', ''), linea_izq)
            ws.write(xi, 3, holi.get('empleado', ''), linea_izq)
            ws.write(xi, 4, holi.get('categoria', ''), linea_izq)
            ws.write(xi, 5, holi.get('region', ''), linea_izq)
            ws.write(xi, 6, holi.get('dias_vacacion', ''), linea_der)
            xi += 1
        
        ws.col(0).width = 2000
        ws.col(1).width = 3500
        ws.col(2).width = 2200
        ws.col(3).width = 8000
        ws.col(4).width = 6500
        ws.col(5).width = 4000
        ws.col(6).width = 7000
        
        buf = cStringIO.StringIO()
        print "dddddddddddddddddd"
        try:    
            
            buf = cStringIO.StringIO()

            wb.save(buf)
            out = base64.encodestring(buf.getvalue())
            buf.close()
    
            data_fname = "Reporte_vacaciones_a_%s.xls" % datetime.today().strftime("%Y-%m-%d %H:%M:%S")
            archivo = '/opt/temp/' + data_fname
            res_model = 'hr.payroll.vacaciones.report'
            id = ids and type(ids) == type([]) and ids[0] or ids
            self.load_doc(cr, uid, out, id, data_fname, archivo, res_model)
    
            return self.write(cr, uid, ids, {'data': out, 'file_name': data_fname, 'name': 'Reporte_vacaciones.xls'})

        # return self.write(cr, uid, ids, {'data': out, 'txt_filename': name})
        except ValueError:
            raise Warning('Error a la hora de guardar el archivo')

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
            attach_vals.update( {'res_id': id} )
        self.pool.get('ir.attachment').create(cr, uid, attach_vals)
        

hr_payroll_vacaciones_report()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: