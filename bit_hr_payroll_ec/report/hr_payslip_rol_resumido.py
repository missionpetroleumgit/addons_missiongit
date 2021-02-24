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
import zipfile
from psycopg2.errorcodes import SUBSTRING_ERROR
from decimal import Decimal
from unicodedata import decimal
import csv
import mx.DateTime
from mx.DateTime import RelativeDateTime
import datetime
from openerp.exceptions import Warning
import xlwt as pycel #Libreria que Exporta a Excel
import sys, os


class hr_payslip_rol_resumido(osv.Model):
    _name = "hr.payslip.rol.resumido"
    _description = 'Reporte de rol resumido'
    
    def get_titulos_report(self, cr, uid, form):
        result = []
        period_id = form.get('period', False)
        company_id = form.get('company_id', False)
        type_hr = form.get('type_hr')
        period = self.pool.get('hr.period.period').browse(cr, uid, period_id[0])
        date_from = period.date_start
        date_to = period.date_stop
        tipo = " in ('IGBS','OINGNBS', 'SUBTOTAL') "
        if form.get('type_ing', False) == 'egreso':
            tipo = " in ('EGRE') "
        elif form.get('type_ing', False) == 'provision':
            tipo = " in ('PRO') "
        elif form.get('type_ing', False) == 'todo':
            tipo = " in ('IGBS','OINGNBS','EGRE','SUBTOTAL') "
        
        cr.execute("select distinct hr_salary_rule.name , hr_salary_rule.sequence \
                    from  hr_payslip, hr_payslip_line, hr_salary_rule, hr_salary_rule_category \
                    where hr_payslip.id = hr_payslip_line.slip_id \
                    and hr_payslip.company_id = hr_payslip_line.company_id \
                    and hr_payslip_line.salary_rule_id = hr_salary_rule.id \
                    and hr_payslip_line.category_id = hr_salary_rule_category.id \
                    and hr_salary_rule_category.code  %s \
                    and date_from = '%s' \
                    and date_to = '%s' \
                    and hr_salary_rule.active \
                    and hr_salary_rule.appears_on_payslip \
                    and hr_payslip.company_id = '%s' \
                    and hr_payslip.type = '%s' \
                    order by hr_salary_rule.sequence" % (tipo,date_from,date_to,company_id[0],type_hr))
        res = cr.fetchall()
        for r in res:
            result.append(r[0].encode('utf8'))
        return result
        
    
    def get_lines_report_wage(self, cr, uid, form):
        res = []
        period_id = form.get('period_id', False)
        tipo = form.get('type', False)
        type_hr = form.get('type_hr')
        hr_employee_obj = self.pool.get('hr.employee')
        hr_contract_obj = self.pool.get('hr.contract')
        hr_contract_period = self.pool.get('hr.contract.period')
        period_id = form.get('period', False)
        period = self.pool.get('hr.period.period').browse(cr, uid, period_id[0])
        date_from = period.date_start
        date_to = period.date_stop
        group_by = form.get('opt_group_by', False)

        tipo = " in ('IGBS','OINGNBS', 'SUBTOTAL') "
        if form.get('type_ing', False) == 'egreso':
            tipo = " in ('EGRE') "
        elif form.get('type_ing', False) == 'provision':
            tipo = " in ('PRO') "
        elif form.get('type_ing', False) == 'todo':
            tipo = " in ('IGBS','OINGNBS','EGRE','SUBTOTAL') "
        
        hr_payroll = self.pool.get('hr.payslip')
        domain = [('date_from', '=', date_from), ('date_to', '=', date_to), ('type', '=', type_hr)]
        if form['company_id']:
            domain.append(('company_id', '=', form['company_id'][0]))
        if form.get('payment_type', False) == 'chq':
            domain.append(('employee_id.emp_modo_pago', '=', 'cheque'))
        if form.get('payment_type', False) == 'transfer':
            domain.append(('employee_id.emp_modo_pago', '=', 'transferencia'))
        if group_by == 'sin_agrupar':
            payslip_ids = hr_payroll.search(cr, uid, domain, order='name') #account_analytic_id, campo del order by
        elif group_by == 'unidad_neg':
            payslip_ids = hr_payroll.search(cr, uid, domain, order='business_unit_id, name')
        elif group_by == 'departamento':
            payslip_ids = hr_payroll.search(cr, uid, domain, order='department_id, name')
        payslip_data = hr_payroll.browse(cr, uid, payslip_ids)
        sec = 1
        
        codigos = []

        cr.execute("select distinct hr_salary_rule.code , hr_salary_rule.sequence \
                    from  hr_payslip, hr_payslip_line, hr_salary_rule, hr_salary_rule_category \
                    where hr_payslip.id = hr_payslip_line.slip_id \
                    and hr_payslip.company_id = hr_payslip_line.company_id \
                    and hr_payslip_line.salary_rule_id = hr_salary_rule.id \
                    and hr_payslip_line.category_id = hr_salary_rule_category.id \
                    and hr_salary_rule_category.code %s \
                    and date_from = '%s' \
                    and date_to = '%s' \
                    and hr_salary_rule.active \
                    and hr_salary_rule.appears_on_payslip \
                    and hr_payslip.company_id = '%s'\
                    and hr_payslip.type = '%s' \
                    order by hr_salary_rule.sequence" % (tipo, date_from,date_to,form['company_id'][0],type_hr))
        res_codes = cr.fetchall()
        for r in res_codes:
            codigos.append(r[0].encode('utf8'))
            
            
        for roles in payslip_data:
            ingresos = []
            data = {}
            data['sec'] = sec
            data['nom'] = roles.employee_id.name_related
            data['ced'] = roles.employee_id.identification_id
            data['car'] = roles.employee_id.job_id.name
            # NO HAY CONTABILIDAD ANALITICA AUN
            if group_by == 'sin_agrupar':
                data['neg'] = ''
            elif group_by == 'unidad_neg':
                data['neg'] = roles.business_unit_id.name
            elif group_by == 'departamento':
                data['neg'] = roles.department_id.name

            data['fpag'] = roles.employee_id.emp_modo_pago
            data['ncta'] = roles.employee_id.bank_account_id.acc_number
            data['tcta'] = roles.employee_id.bank_account_id.state
            data['tba'] = roles.employee_id.bank_account_id.bank_name
            # JJM 2018-01-09 agrego dias trabajados al reporte
            work_days = filter(lambda x: x.code=='WORK100',roles.worked_days_line_ids)
            data['dias'] = work_days[0].number_of_days if len(work_days)>0 else ''
            for code_rules in codigos:
                valor = 0.00
                for line in roles.details_by_salary_rule_category:
                    if line.salary_rule_id.active and line.salary_rule_id.appears_on_payslip:
                        if line.salary_rule_id.code == code_rules:
                            valor = round(line.amount,2)
                            continue
                ingresos.append(valor)    
                    
#             for line in roles.details_by_salary_rule_category:
#                 if line.salary_rule_id.active and line.salary_rule_id.appears_on_payslip:
#                     ingresos.append(round(line.amount,2))
                    
            data['ingresos'] = ingresos    
                        
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
        period_id = form.get('period', False)
        period = self.pool.get('hr.period.period').browse(cr, uid, period_id[0])
        company_id = form.get('company_id', False)
        group_by = form.get('opt_group_by', False)
        company = self.pool.get('res.company').browse(cr, uid, company_id[0])
        if not company.partner_id.part_number:
            raise Warning('Debe configurar el RUC de la Empresa')
        if not company.partner_id.street:
            raise Warning('Debe configurar el direccion de la Empresa')

        date_from = period.date_start
        date_to = period.date_stop
        type_hr = form.get('type_hr')
        dep_id = form.get('dep_id')
        path = form.get('path')
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
        if type_hr == 'rol':
            title = 'REPORTE ROL RESUMIDO '
        elif type_hr == 'quincena':
            title = 'REPORTE QUINCENA'
            
        ws = wb.add_sheet(title)
        
        ws.show_grid = False
        ws.header_str = u"&LFecha de Impresion: &D Hora: &T&RPagina &P de &N"
        ws.footer_str = u"" 
        compania = self.pool.get('res.company').browse(cr, uid, form['company_id'][0])
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
        total_general = dict()
        if type_hr in ('rol'):
            total_dict = dict()
            # JJM 2018-01-09 agrego opcion de agrupar o no por centro de costo
            if group_by == 'sin_agrupar':
                ws.write(xi, 1, 'SECUENCIAL', style_header)
            if group_by == 'unidad_neg':
                ws.write(xi, 1, 'CENTRO DE COSTO', style_header)
            if group_by == 'departamento':
                ws.write(xi, 1, 'DEPARTAMENTO', style_header)
            #ws.write(xi, 1, 'SECUENCIAL', style_header)
            ws.write(xi, 2, 'EMPLEADO', style_header)
            ws.write(xi, 3, 'No CEDULA', style_header)
            ws.write(xi, 4, 'CARGO', style_header)
            # ws.write(xi, 5, 'CENTRO DE COSTOS', style_header)
            ws.write(xi, 5, 'FORMA DE PAGO', style_header)
            ws.write(xi, 6, 'N CUENTA', style_header)
            ws.write(xi, 7, 'TIPO CUENTA', style_header)
            ws.write(xi, 8, 'BANCO', style_header)
            # JJM 2018-01-09 agrego dias trabajados
            ws.write(xi, 9, 'DIAS TRABAJADOS', style_header)

            lst_titulos = self.get_titulos_report(cr, uid, form)
            col_t = 9
            for titulo in lst_titulos:
                col_t+=1
                ws.write(xi, col_t, titulo, style_header)
                total_dict[col_t] = 0.00
                total_general[col_t] = 0.00
            
            
        
        xi += 1
        seq = 0
        rf = rr = ri = 0
        analytic_name = 'none'
        amount_base = amount_calculate = 0.00
        if type_hr in ('rol'):
            lineas = self.get_lines_report_wage(cr, uid, form)
            for linea in lineas:
                # NO HAY CONTABILIDAD ANALITICA
                #JJM valido si hay group por centro de costo
                if (group_by != 'sin_agrupar') and linea['neg'] != analytic_name:
                    if analytic_name != 'none':
                        ws.write(xi, 1, 'Subtotal', style_cabecerader)
                        for key, val in total_dict.items():
                            ws.write(xi, key, val, style_cabecerader)
                            total_dict[key] = 0.00
                        xi += 1
                    ws.write(xi, 1, linea['neg'], style_header)
                    analytic_name = linea['neg']
                    xi += 1
                    if seq > 0:
                        seq = 0
                # JJM si no agrupa pongo nombre de centro de costo
                elif group_by == 'sin_agrupar':
                    ws.write(xi, 0, linea['neg'], style_cabecerader)

                seq += 1
                ws.write(xi, 1, seq, linea_center)
                ws.write(xi, 2, linea.get('nom', ''), linea_izq)
                ws.write(xi, 3, linea.get('ced', ''), linea_izq)
                ws.write(xi, 4, linea.get('car', ''), linea_izq)
                # ws.write(xi, 5, linea.get('neg', ''), linea_izq)
                ws.write(xi, 5, linea.get('fpag', ''), linea_izq)
                ws.write(xi, 6, linea.get('ncta', ''), linea_izq)
                ws.write(xi, 7, linea.get('tcta', ''), linea_izq)
                ws.write(xi, 8, linea.get('tba', ''), linea_izq)
                ws.write(xi, 9, linea.get('dias', ''), linea_center)
                col = 9
                for ingreso in linea['ingresos']:
                    col += 1
                    ws.write(xi, col, ingreso, linea_der)
                    total_dict[col] += ingreso
                    total_general[col] += ingreso
                xi += 1
            # JJM si agrupa por centro de costo
            if group_by != 'sin_agrupar':
                ws.write(xi, 1, 'Subtotal', style_cabecerader)
                for key, val in total_dict.items():
                    ws.write(xi, key, val, style_cabecerader)
                    total_dict[key] = 0.00
        xi +=1
        ws.write(xi, 1, 'Totales', style_cabecerader)
        for key, val in total_general.items():
            ws.write(xi, key, val, style_cabecerader)
        # JJM si no agrupa mayor ancho de primera columna
        if group_by == 'sin_agrupar':
            ws.col(0).width = 2000
        else:
            ws.col(0).width = 2000

        ws.col(1).width = 7900
        ws.col(2).width = 9900
        ws.col(3).width = 5000
        ws.col(4).width = 6900
        ws.col(5).width = 6500
        ws.col(6).width = 5500
        ws.col(7).width = 5500
        ws.col(8).width = 5500
        ws.col(9).width = 2500
        ws.col(10).width = 6500
        ws.col(11).width = 6500
        ws.col(12).width = 6500
        ws.col(13).width = 6500
        ws.col(14).width = 6500
        ws.col(15).width = 6500
        ws.col(16).width = 6500
        ws.col(17).width = 6500
        ws.col(18).width = 6500
        ws.col(19).width = 6500
        ws.col(20).width = 6500
        ws.col(21).width = 6500
        ws.col(22).width = 6500
        ws.col(23).width = 6500
        ws.col(24).width = 6500
        ws.col(25).width = 6500
        ws.col(26).width = 6500
        ws.col(27).width = 6500
        ws.col(28).width = 6500
        ws.col(29).width = 6500
        ws.col(30).width = 6500
        
        ws.row(8).height = 750

        buf = cStringIO.StringIO()
        # name = "%s%s%s.xls" % (path, "Reporte_RR_HH", datetime.datetime.now())
        # exists_path = os.path.exists(path)
        # print 'esta ruta existe?', exists_path
        # print('sys.argv[0] =', sys.argv[0])
        # a = sys.path
        # pathname = os.path.dirname(os.getcwd())
        # print('path =', a)
        # print('full path =', os.path.abspath(pathname))
        try:
            # wb.save(name)
            # raise Warning('Archivo salvado correctamente')
            buf = cStringIO.StringIO()

            wb.save(buf)
            out = base64.encodestring(buf.getvalue())
            buf.close()
            
            data_fname = "Reporte_RR_HH_%s.xls" % (period.name)
            archivo = '/opt/temp/' + data_fname
            res_model = 'hr.payslip.rol.resumido'
            id = ids and type(ids) == type([]) and ids[0] or ids
            self.load_doc(cr, uid, out, id, data_fname, archivo, res_model)
            
            return self.write(cr, uid, ids, {'data':out, 'txt_filename':'Reporte_RR_HH.xls', 'name':'Reporte_RR_HH.xls'})

            # return self.write(cr, uid, ids, {'data': out, 'txt_filename': name})
        except ValueError:
            raise Warning('Error a la hora de salvar el archivo')


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
        'name': fields.char('Descripcion', size=16,required=False, readonly=False),
        'fiscalyear': fields.many2one('hr.fiscalyear', 'Año Fiscal', required=True),
        'period': fields.many2one('hr.period.period', 'Periodo', required=True,
                                  domain="[('fiscalyear_id', '=', fiscalyear)]"),
        'date_from': fields.date('Fecha Desde'),
        'date_to': fields.date('Fecha Hasta'),
        # 'dep_id' : fields.many2one('hr.department','Sucursal/Departamento'),
        'txt_filename': fields.char(),
        'type_hr':fields.selection([('quincena', 'Quincena'), ('rol', 'Rol Pagos'), ('serv10', '10% Servicios')], 'Tipo de Rol', required=True),
        'type_ing':fields.selection([('todo', 'Todo'),('ingreso', 'Ingreso'), ('egreso', 'Egreso'), ('provision', 'Provision')], 'Tipo'),
        'data':fields.binary('Archivo', filters=None),
        'path': fields.char('Ruta'),
        'company_id': fields.many2one('res.company', 'Compania'),
        'payment_type': fields.selection([('transfer', 'Transferencia'), ('chq', 'Cheque'),('both','Todos')], 'Forma Pago', required=True),
        'opt_group_by':fields.selection([('unidad_neg', 'Unidad de Negocio'), ('departamento', 'Departamento'),('sin_agrupar','Sin agrupar')], 'Agrupado por:'),
        # ('sucursal','Sucursal'),
    }



hr_payslip_rol_resumido()
 
        
        
        

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:


