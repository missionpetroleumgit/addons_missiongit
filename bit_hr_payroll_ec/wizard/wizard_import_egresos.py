# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as0,00
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

class wizard_import_egresos(osv.osv_memory):
    _name = 'wizard.import.egresos'
    _description = 'Egresos de Empleados'

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
        print "FORM TEXT ID", form['id'] 
        lines_id = form['id']
        file_data = form.get('data')
        fecha = form.get('date')
        egreso_id = form.get('expense_type_id')
        company_id = form.get('company_id')[0]
        print "Fecha", fecha
        print "egreso_id: ", egreso_id
        buf = base64.decodestring(file_data).split('\n')
        buf = buf[:len(buf) - 1]
        noced = []
        yeced = []
        wrong_values = []
        num_reg = 0
        num_regc = 0
        num_regb = 0
        num_total = 0
        i = 0
        #___-****____
        for item in buf:
            if i == 0:
                i = i + 1
                continue
             
            num_total = num_total + 1
            aux_1=''
            cedul=''
            nombre=''
            valor=''
            print ' item000 ', item
            item1 = item.split(',')
            print ' item111 ', item1
#            try:
            aux_1 = item1[0].replace('\"', '').strip()
            print ' aux 1111 ', aux_1
            if len(aux_1)==9:
                aux_1 = '0'+aux_1
            cedul = aux_1.strip()
            print "CEDULA: ", cedul
            
            if company_id:
                emp_id = self.pool.get('hr.employee').search(cr, uid, [('identification_id', '=', cedul), ('company_id', '=', company_id)])
            else:
                emp_id = self.pool.get('hr.employee').search(cr, uid, [('identification_id', '=', cedul)])


            print "emp_id: ", emp_id
            print "emp_id_len: ", len(emp_id)
            if len(emp_id)==0:
                print "aqui"
                raise osv.except_osv(('Atencion !'), ('Numero de cedula incorrecto:' + cedul))
            nombre = item1[2].strip()
            print "Nombre: ", nombre
            valor = item1[1].strip()
            print "Valor: ", valor
            
#            except:
#                wrong_values.append(item1[0])
#                num_regb = num_regb + 1

            egreso = self.pool.get('hr.expense')
                    
            
            vals = {
                  'expense_type_id':egreso_id[0],
                  'employee_id': emp_id[0],
                  'value': valor,
                  'date':fecha,
                  'company_id': company_id,

            }
            if valor:
                if float(valor) > 0:
                    egreso.create(cr, uid, vals)
                    num_regc = num_regc + 1
                else:
                    num_regb = num_regb + 1
            
            noced.append(cedul+ ' '+ str(nombre))
            
                       

                               
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
            'expense_type_id' : fields.many2one('hr.expense.type', 'Tipo de Egreso'),
            'data':fields.binary('Archivo',filters=None),
            'state': fields.selection([('borrador', 'Borrador'), ('cerrado', 'Cerrado')], 'Estado', readonly=True),
          #  'num_registros':fields.text('Numero de registros actualizados'),
            'num_registrosc':fields.text('Numero de registros procesados', readonly=True),
            'num_registrosb':fields.text('Numero de registros erroneos', readonly=True),
            'company_id':fields.many2one('res.company', 'Compania'),
                }
    _defaults = {
       'date': lambda *a: time.strftime('%Y-%m-%d'),
       'state': lambda * a: 'borrador',

}
wizard_import_egresos()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
