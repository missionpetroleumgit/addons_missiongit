# -*- encoding: utf-8 -*-
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
#import wizard
import base64
import StringIO
from time import strftime
from string import upper, capitalize
from string import join
from openerp.osv import fields, osv
import time

class wizard_import_horas(osv.osv_memory):
    _name = 'wizard.import.horas'
    _description = 'Ingresos de empleados'

    def load_csv(self, cr, uid, data, context=None):
        result = {}
        res = {'value':{}}
#         print "DATA", data
#         print "CONTEXT", context 
        if not data:
            return {'type': 'ir.actions.act_window_close'}
        if context is None:
            context = {}
        form = self.read(cr, uid, data)[0]
#         print "FORM TEXT", form
        lines_id = form['id']
        file = form.get('data')
        fecha = form.get('date') 
        centro_id = form.get('analytic_id')
        buf = base64.decodestring(file).split('\n')
        buf = buf[:len(buf) - 1]
        noced = []
        yeced = []
        wrong_values = []
        num_reg = 0
        num_regc = 0
        num_regb = 0
        num_total = 0
        valor_pagar = 0
        valor_hora_tra = 0
        i = 0
        porcentaje = 100.00
        
        obj_contrato = self.pool.get('hr.contract')
        
        #___-****____
        for item in buf:
            if i == 0:
                i = i + 1
                continue
             
            
            aux_1=''
            cedul=''
            nombre=''
            horas=''
            item1 = item.split(',')
            aux_1 = item1[0].replace('\"', '').strip()
            if len(aux_1)==9:
                aux_1 = '0'+aux_1
            cedul = aux_1.strip()
            emp_id = self.pool.get('hr.employee').search(cr, uid, [('identification_id', '=', cedul)])
            if len(emp_id)==0:
                raise osv.except_osv(('Atencion !'), ('Empleado no encontrado:' + cedul))
            nombre = item1[1].strip()
           
            # Modificacion para que el tipo de hora lo lea del archivo

            obj_adm_incomes = self.pool.get('hr.adm.incomes')
            ingreso = self.pool.get('hr.income')
            
            valor_festivo = float(item1[2].strip())
            valor_extra = float(item1[3].strip())
            valor_suple = float(item1[4].strip())
            valor_nocturno = float(item1[5].strip())
            
            contrato_id = obj_contrato.search(cr,uid,[('employee_id','=', emp_id[0])])
            for contratos in obj_contrato.browse(cr,uid,contrato_id):
                sueldo = contratos.wage
                valor_hora_tra = sueldo/(contratos.horas_x_dia * 30.00)
                valor_hora_tra = valor_hora_tra * porcentaje / 100.00
            
            # HORAS FESTIVAS
            print "valor_festivo: ", valor_festivo
            if valor_festivo > 0:
                num_total = num_total + 1
                print "float:"
                tipo_hora_id = obj_adm_incomes.search(cr, uid, [('code', '=', 'INGHRF')])
                if len(tipo_hora_id)==0:
                    raise osv.except_osv(('Atencion !'), ('Tipo de Hora Festivo no configurada' ))
                ingreso_id = tipo_hora_id
                
                adm_income = obj_adm_incomes.browse(cr,uid,ingreso_id[0])[0]
                valor_pagar = float(adm_income.default_value) * float(valor_hora_tra) * float(valor_festivo)
                
                vals = {
                     'adm_id':ingreso_id[0], 'employee_id': emp_id[0], 'value': valor_pagar, 'date':fecha,
                      'horas':valor_festivo, 'analytic_id':centro_id[0], 'h_registro': True,
                }
                
                ingreso.create(cr, uid, vals)
                num_regc = num_regc + 1
            else:
                num_total = num_total + 1
                num_regb = num_regb + 1   
                         
            # HORAS EXTRAORDINARIAS
            if valor_extra > 0:
                num_total = num_total + 1
                tipo_hora_id = obj_adm_incomes.search(cr, uid, [('code', '=', 'INGHXT')])
                if len(tipo_hora_id)==0:
                    raise osv.except_osv(('Atencion !'), ('Tipo de Hora Festivo no configurada' ))
                ingreso_id = tipo_hora_id
                
                adm_income = obj_adm_incomes.browse(cr,uid,ingreso_id[0])[0]
                valor_pagar = float(adm_income.default_value) * float(valor_hora_tra) * float(valor_extra)
                
                vals = {
                     'adm_id':ingreso_id[0], 'employee_id': emp_id[0], 'value': valor_pagar, 'date':fecha,
                      'horas':valor_extra, 'analytic_id':centro_id[0], 'h_registro': True,
                }
                
                ingreso.create(cr, uid, vals)
                num_regc = num_regc + 1
            else:
                num_regb = num_regb + 1
                num_total = num_total + 1
            
            # HORAS SUPLEMENTARIAS
            if valor_suple > 0:
                num_total = num_total + 1
                tipo_hora_id = obj_adm_incomes.search(cr, uid, [('code', '=', 'INGHSUP')])
                if len(tipo_hora_id)==0:
                    raise osv.except_osv(('Atencion !'), ('Tipo de Hora Festivo no configurada' ))
                ingreso_id = tipo_hora_id
                
                adm_income = obj_adm_incomes.browse(cr,uid,ingreso_id[0])[0]
                valor_pagar = float(adm_income.default_value) * float(valor_hora_tra) * float(valor_suple)
                
                vals = {
                     'adm_id':ingreso_id[0], 'employee_id': emp_id[0], 'value': valor_pagar, 'date':fecha,
                      'horas':valor_suple, 'analytic_id':centro_id[0], 'h_registro': True,
                }
                
                ingreso.create(cr, uid, vals)
                num_regc = num_regc + 1                          
            else:
                num_regb = num_regb + 1
                num_total = num_total + 1

            # HORAS NOCTURNA
            if valor_nocturno > 0:
                num_total = num_total + 1
                tipo_hora_id = obj_adm_incomes.search(cr, uid, [('code', '=', 'INGHNOC')])
                if len(tipo_hora_id)==0:
                    raise osv.except_osv(('Atencion !'), ('Tipo de Hora Festivo no configurada' ))
                ingreso_id = tipo_hora_id
                
                adm_income = obj_adm_incomes.browse(cr,uid,ingreso_id[0])[0]
                valor_pagar = float(adm_income.default_value) * float(valor_hora_tra) * float(valor_nocturno)
                
                vals = {
                     'adm_id':ingreso_id[0], 'employee_id': emp_id[0], 'value': valor_pagar, 'date':fecha,
                      'horas':valor_nocturno, 'analytic_id':centro_id[0], 'h_registro': True,
                }
                
                ingreso.create(cr, uid, vals)
                num_regc = num_regc + 1  
            else:
                num_regb = num_regb + 1
                num_total = num_total + 1
                
                
        self.write(cr, uid, data, {'state':'cerrado',
                                   'num_registros': str(num_reg) + ' de ' + str(num_total),
                                   'num_registrosc': str(num_regc) + ' de ' + str(num_total),
                                   'num_registrosb': str(num_regb) + ' de ' + str(num_total)}),
#         return result
        return {'name': ('Resultado Archivo Procesado'), 'type': 'ir.actions.act_window_close'}
     

#         name = 'cerrado'
#         return self.write(cr, uid, data, {'yes_ced':'\n'.join(yeced), 'state': name})
    _columns = {
            'date': fields.date('Fecha'),    
            'analytic_id': fields.many2one('account.analytic.account', "Centro de Costos", required=True),
            'data':fields.binary('Archivo',filters=None),
            'state': fields.selection([('borrador', 'Borrador'), ('cerrado', 'Cerrado')], 'Estado', readonly=True),
           # 'num_registros':fields.text('Numero de registros actualizados'),
            'num_registrosc':fields.text('Numero de registros creados', readonly=True),
            'num_registrosb':fields.text('Numero de registros con valor 0', readonly=True),
                }
    _defaults = {
       'date': lambda *a: time.strftime('%Y-%m-%d'),
       'state': lambda * a: 'borrador',

}
wizard_import_horas()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
