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
import time
from psycopg2.errorcodes import SUBSTRING_ERROR
from decimal import Decimal
from unicodedata import decimal
import os


class hr_payslip_file_bank(osv.Model):

    _name = "hr.payslip.file.bank"

    _columns = {
        'name' : fields.char('Descripcion', size=16),
        'date_from': fields.date('Fecha Desde'),
        'date_to': fields.date('Fecha Hasta'),
        'bank_id' : fields.many2one('res.bank','Tipo de Banco'),
        'dep_id' : fields.many2one('hr.department','Sucursal/Departamento'),
        'txt_filename': fields.char(),
        'txt_binary': fields.binary(),
        'type_hr':fields.selection([('quincena', 'Quincena'), ('rol', 'Rol Pagos'),
                                    ('dc3', 'Decimos 3ros'), ('dc4', 'Decimos 4tos'), ('serv10', '10% Servicio')], 'Tipo Pago', required=True),
        'extension': fields.selection([('txt', '.txt'), ('csv', '.csv')], 'Extension a generar'),
        'company_id': fields.many2one('res.company', 'Compania')
    }
#, ('anticipo', 'Anticipos'), ('prestamo', 'Prestamos'), ('util', 'Utilidades'), ('decim4to', 'Decimo 4to'), ('decim3ro', 'Decimo 3ro')
    def generate_file(self, cr, uid, ids, context=None):
        if not ids:
            return {'type': 'ir.actions.act_window_close'}
        if context is None:
            context = {}
        form = self.read(cr, uid, ids)[0]
        print "FORM TEXT", form 
        type_hr = form.get('type_hr')
        print "TYPO ARCH", type_hr
        sucursal_id = form.get('dep_id')
        if sucursal_id:
            s_id = sucursal_id[0]
            print "SUCURSAL", sucursal_id
            print "SUCURSAL ID", s_id
        else:
            s_id = False
        banco_id = form.get('bank_id')
        if form.get('extension'):
            extension = form.get('extension')
        else:
            extension = 'txt'
        b_id = banco_id[0]
        print "BANCO", banco_id
        print "BANCO ID", b_id
        f_desde = form.get('date_from')
        print "FECHA DESDE", f_desde
        f_hasta = form.get('date_to')
        print "FECHA HASTA", f_hasta
        aux_sql = str()
        company_id = False
        if form['company_id']:
            company_id = form['company_id'][0]
            aux_sql = "and aml.company_id = %s " % company_id
#**************************************************************************************************
        buf = StringIO.StringIO()
        print "type_hr: ", type_hr
        if type_hr in ('rol') and s_id:
            sql = "select  aml.id, aml.employee_id, '0.00' as debit, pr.total as credit, \
                    aml.name as ref \
                    from hr_payslip aml, hr_payslip_line pr \
                    where aml.id = pr.slip_id \
                    and aml.type = '%s' \
                    and aml.department_id = %s \
                    and aml.date_from = '%s' \
                    and aml.date_to = '%s' \
                    and pr.code='NR' " % (type_hr, s_id, f_desde, f_hasta)
            sql += aux_sql
            sql += "order by aml.name"
            print "sql1: ", sql
        elif type_hr in ('quincena'):
            sql = "select  aml.id, aml.employee_id, '0.00' as debit, pr.total as credit, \
                    aml.name as ref \
                    from hr_payslip aml, hr_payslip_line pr \
                    where aml.id = pr.slip_id \
                    and aml.type = '%s' \
                    and aml.date_from = '%s' \
                    and aml.date_to = '%s' " % (type_hr, f_desde, f_hasta)
            sql += aux_sql
            sql += "order by aml.name"
            print "sql1: ", sql
        elif type_hr in ('serv10'):
            sql = "select  aml.id, aml.employee_id, '0.00' as debit, pr.total as credit, \
                    aml.name as ref \
                    from hr_payslip aml \
                    inner join hr_payslip_line pr \
                    on aml.id = pr.slip_id \
                    where pr.code = 'NR' \
                    and aml.type = '%s' \
                    and pr.total > 0.00 \
                    and aml.date_from >= '%s' \
                    and aml.date_to <= '%s'" % (type_hr, f_desde, f_hasta)
            sql += aux_sql
            sql += "order by aml.name"
        if type_hr in ('rol') and not s_id:
            sql = "select  aml.id, aml.employee_id, '0.00' as debit, pr.total as credit, \
                    aml.name as ref \
                    from hr_payslip aml, hr_payslip_line pr \
                    where aml.id = pr.slip_id \
                    and aml.type = '%s' \
                    and aml.date_from = '%s' \
                    and aml.date_to = '%s' \
                    and pr.code = 'NR' " % (type_hr, f_desde, f_hasta)
            sql += aux_sql
            sql += "order by aml.name"
            print "sql1: ", sql
        elif type_hr in ('quincena') and not s_id:
            sql = "select  aml.id, aml.employee_id, '0.00' as debit, pr.total as credit, \
                    aml.name as ref \
                    from hr_payslip aml, hr_payslip_line pr \
                    where aml.id = pr.slip_id \
                    and aml.type = '%s' \
                    and aml.date_from >= '%s' \
                    and aml.date_to <= '%s' " % (type_hr, f_desde, f_hasta)
            sql += aux_sql
            sql += "order by aml.name"
 #           print "sql1: ", sql
    # Agregando los valores para generar el archivo para los decimos realizado por: Ing. Ramsés W. Peña
        elif type_hr == 'dc3' or type_hr == 'dc4':
            dec_pool = self.pool.get('hr.remuneration.employee')
            domain = [('decimo_type', '=', type_hr), ('periodo_inicio', '>=', f_desde),
                      ('periodo_final', '<=', f_hasta), ('state', '=', 'draft'),
                      ('forma_pago', '=', 'transferencia')]
            if company_id:
                domain.append(('company_id', '=', company_id))
            decimo_ids = dec_pool.search(cr, uid, domain)
            if not decimo_ids:
                raise osv.except_osv('Error!', 'No se han generado decimos en el periodo seleccionado')
            decimos_objs = dec_pool.browse(cr, uid, decimo_ids)
            for decimo in decimos_objs:
                cadena = self.cadena_decimos(cr, uid, decimo, b_id, context=None)
#                print '*/***///**///**////**cadena ', cadena
                buf.write(upper(cadena))

            out = base64.encodestring(buf.getvalue())
            buf.close()
            name = "%s%s%s.txt" % ("NCR", time.strftime('%Y%m%d'), "XX_01")

            return self.write(cr, uid, ids, {'txt_binary':out, 'txt_filename': name})

#        elif type_hr in ('anticipo', 'prestamo', 'decim4to','decim3ro'):
#            sql = "select aml.id as id, aml.employee_id as employee_id, aml.debit as debit, aml.credit as credit, aml.ref as ref, aml.move_id as move_id, aa.name as name, aa.code as code from account_move_line aml, account_account aa \
#            where aml.account_id = aa.id \
#            and aml.has_transfer = False \
#            and aml.employee_id is not null \
#            and aml.period_id = %s \
#            and aml.type_hr = '%s'" % (period_id, type_hr)
#            print "sql2: ", sql
        
        cr.execute(sql)
        res = cr.dictfetchall()
        valor_total = 0
        cont = 1
        cuenta_comp = ''
        bankk_account_id = 0
        if res:
            for data_total in res:
                employee = self.pool.get('hr.employee').browse(cr, uid, data_total['employee_id'])
                if employee.state_emp in ('active','sold_out') and employee.emp_modo_pago == 'transferencia':
                    valor_total += data_total['credit']
            if not company_id:
                company_id = self.pool.get('res.users')._get_company(cr, uid, context=context)
            obj_company = self.pool.get('res.company').browse(cr, uid, company_id)
            nombre_comp = obj_company.partner_id.name
            for cuenta_comp in obj_company.bank_ids:
                print cuenta_comp
                cuenta_comp = cuenta_comp.acc_number

            factual = time.strftime('%d%m%y')
            fact = factual.split('-')
#           print "fecha actual", fact
            fecha = str(factual)
      #      print "fecha: ",fecha

#                           
#             cadena = "D" + str(nombre_comp).ljust(40) + str(cuenta_comp) + str('%.2f' % valor_total).replace(".","").zfill(14) +fecha + "N" + '\n'
#             buf.write(upper(cadena))
#             cont = cont + 1
            
            
            
            for data in res:
     #           print ' data ', data
                employee = self.pool.get('hr.employee').browse(cr, uid, data['employee_id'])
    #            print "OBJ EMPLE", employee
   #             print "EMPLE STATE", employee.state_emp
  #              print "EMP CUENTA ID", employee.bank_account_id
                
 #               print "banco *********", employee.bank_account_id.bank 
                   
                cadena = ""
                  
                if employee.state_emp in ('active','sold_out') and employee.emp_modo_pago == 'transferencia':
                    if (employee.bank_account_id.acc_number and employee.bank_account_id.bank.id == b_id):
                        if data['credit']:
                            cadena = self.obtener_cadena(cr, uid, employee, f_hasta, b_id, data, cont, context)
                            buf.write(upper(cadena))
                            cont = cont + 1

        else:
            raise osv.except_osv("Pagos Nomina ", 'No existen registros para el tipo. %s' % (type_hr))
            return
        # **************************************************************************************************

        out = base64.encodestring(buf.getvalue())
        buf.close()
        bank_account = self.pool.get('res.company').browse(cr, uid, company_id).partner_id.bank_ids[0]
        if bank_account.bank_bic == '10':
            name = "%s%s%s.%s" % ("NCR", time.strftime('%Y%m%d'), "XX_01", extension)
        elif bank_account.bank_bic == '32':
            name = "%s%s.%s" % ("PHEASYP_FULL", time.strftime('%Y%m%d'), extension)

        return self.write(cr, uid, ids, {'txt_binary':out, 'txt_filename': name})

    def obtener_formato(self):

        # formato banco guayaquil
        linea = []
        detalle_linea0 = {}
        detalle_linea0['nombre'] = 'tipo_cuenta'
        detalle_linea0['dato'] = 'employee.bank_account_id.type'
        detalle_linea0['orden'] = 1
        detalle_linea0['numero_espacios'] = 1
        detalle_linea0['separador'] = ''
        detalle_linea0['tipo'] = 'obtenido'

        linea.append(detalle_linea0)

        detalle_linea1 = {}
        detalle_linea1['nombre'] = 'numero_cuenta_guayaquil'
        detalle_linea1['dato'] = 'employee.bank_account_id.name'
        detalle_linea1['orden'] = 2
        detalle_linea1['numero_espacios'] = 10
        detalle_linea1['separador'] = ''
        detalle_linea1['tipo'] = 'obtenido'

        linea.append(detalle_linea1)

        detalle_linea2 = {}
        detalle_linea2['nombre'] = 'valor'
        detalle_linea2['dato'] = 'debit'
        detalle_linea2['orden'] = 3
        detalle_linea2['numero_espacios'] = 15
        detalle_linea2['separador'] = ''
        detalle_linea2['tipo'] = 'obtenido'

        linea.append(detalle_linea2)

        detalle_linea3 = {}
        detalle_linea3['nombre'] = 'codigo'
        detalle_linea3['dato'] = 'XX'
        detalle_linea3['orden'] = 4
        detalle_linea3['numero_espacios'] = 2
        detalle_linea3['separador'] = ''
        detalle_linea3['tipo'] = 'fijo'

        linea.append(detalle_linea3)

        detalle_linea4 = {}
        detalle_linea4['nombre'] = 'nota'
        detalle_linea4['dato'] = 'Y'
        detalle_linea4['orden'] = 5
        detalle_linea4['numero_espacios'] = 1
        detalle_linea4['separador'] = ''
        detalle_linea4['tipo'] = 'fijo'

        linea.append(detalle_linea4)

        detalle_linea5 = {}
        detalle_linea5['nombre'] = 'agencia'
        detalle_linea5['dato'] = '01'
        detalle_linea5['orden'] = 6
        detalle_linea5['numero_espacios'] = 2
        detalle_linea5['separador'] = ''
        detalle_linea5['tipo'] = 'fijo'

        linea.append(detalle_linea5)

        detalle_linea6 = {}
        detalle_linea6['nombre'] = 'banco'
        detalle_linea6['dato'] = 'employee.bank_account_id.res_bank_id.code'
        detalle_linea6['orden'] = 7
        detalle_linea6['numero_espacios'] = 2
        detalle_linea6['separador'] = ''
        detalle_linea6['tipo'] = 'obtenido'

        linea.append(detalle_linea6)

        detalle_linea7 = {}
        detalle_linea7['nombre'] = 'numero_cuenta_otros'
        detalle_linea7['dato'] = 'employee.bank_account_id.name'
        detalle_linea7['orden'] = 8
        detalle_linea7['numero_espacios'] = 18
        detalle_linea7['separador'] = ''
        detalle_linea7['tipo'] = 'obtenido'

        linea.append(detalle_linea7)

        detalle_linea8 = {}
        detalle_linea8['nombre'] = 'empleado'
        detalle_linea8['dato'] = 'employee.name'
        detalle_linea8['orden'] = 9
        detalle_linea8['numero_espacios'] = 18
        detalle_linea8['separador'] = ''
        detalle_linea8['tipo'] = 'obtenido'

        linea.append(detalle_linea8)

        return linea

    def get_data(self, employee, data, formato):

        esp = ['á', 'à', 'â', 'ã', 'ª', 'Á', 'À', 'Â', 'Ã', 'Í', 'Ì', 'Î', 'í', 'ì', 'î', 'é', 'è', 'ê', 'É', 'È', 'Ê', 'ó', 'ò', 'ô', 'õ', 'º', 'Ó', 'Ò', 'Ô', 'Õ', 'ú', 'ù', 'û', 'Ú', 'Ù', 'Û', 'ç', 'Ç', 'ñ', 'Ñ', 'Ñ']
        nor = ['a', 'a', 'a', 'a', 'a', 'A', 'A', 'A', 'A', 'I', 'I', 'I', 'i', 'i', 'i', 'e', 'e', 'e', 'E', 'E', 'E', 'o', 'o', 'o', 'o', 'o', 'O', 'O', 'O', 'O', 'u', 'u', 'u', 'U', 'U', 'U', 'c', 'C', 'n', 'N', 'N']

        if formato['nombre'] == 'tipo_cuenta':
            espacios = formato['numero_espacios']
            print ' get_data tipo_cuenta ', employee.bank_account_id.state.strip().upper()
            return employee.bank_account_id.state.upper()[0:espacios]

        if formato['nombre'] == 'numero_cuenta_guayaquil' and employee.bank_account_id.bank.id == 1:
            cta_gye = employee.bank_account_id.name.strip()
            return cta_gye.zfill(formato['numero_espacios'])
        elif formato['nombre'] == 'numero_cuenta_guayaquil' and employee.bank_account_id.bank.id != 1:
            cta_otros = ''
            return cta_otros.zfill(formato['numero_espacios'])

        if formato['nombre'] == 'valor':
            tot = '{0:.2f}'.format(data['credit'])
            val = tot.split('.')
            l = ""
            for item in val[0]:
                l += item
            if len(val[1]) < 2:
                val[1] += '0'
            for item in val[1]:
                l += item
            return l.zfill(formato['numero_espacios'])

        if formato['nombre'] == 'banco' and employee.bank_account_id.bank.id == 1:
            return '  '
        elif formato['nombre'] == 'banco' and employee.bank_account_id.bank.id != 1:
            return employee.bank_account_id.bank.bic.strip().zfill(formato['numero_espacios'])

        if formato['nombre'] == 'numero_cuenta_otros' and employee.bank_account_id.bank.id == 1:
            return '                  '
        elif formato['nombre'] == 'numero_cuenta_otros' and employee.bank_account_id.bank.id != 1:
            return employee.bank_account_id.bank_name.strip().zfill(formato['numero_espacios'])

        if formato['nombre'] == 'empleado':
            nom = str(employee.name_related.encode('"UTF-8"').strip())
            for indi in range(40):
                nom = nom.replace(esp[indi], nor[indi])
            nombre = str(nom)

            if len(nombre) < 18:
                tam = len(nombre)
                num_espacion = 18 - tam
                for i in range(18):
                    nombre = nombre + ' '

            return nombre[0:formato['numero_espacios']]

    def complete_zeros(self, _str, length):
        iterator = len(_str)
        while iterator < length:
            _str = '0' + _str
            iterator += 1
        return _str

    def set_amount(self, amount):
        decimal_units = round(amount - int(amount), 2)
        if decimal_units > 0:
            value = str(int(amount)) + str(int(decimal_units*100))
        else:
            value = str(int(amount))
        return value

    def cadena_decimos(self, cr, uid, decimo, b_id, company_id, context=None):
        acc_number = False
        cur = 'USD'
        char = 'C'
        bank_objects = list()
        if company_id:
            company = self.pool.get('res.company').browse(cr, uid, company_id)
            bank_objects = [bank for bank in company.bank_ids]
        else:
            user = self.pool.get('res.users').browse(cr, uid, uid)
            bank_objects = [bank for bank in user.company_id.bank_ids]
        for bank in bank_objects:
            if bank.bank.id == b_id:
                acc_number = bank.acc_number
                bic = bank.bank.bic
                break
        if not acc_number:
            raise osv.except_osv('Error!', 'Debe asociar una cuenta bancaria a la empresa')
        if len(acc_number) < 10:
            acc_number = self.complete_zeros(acc_number, 10)
        account_employee = decimo.employee_id.bank_account_id.acc_number
        if decimo.employee_id.bank_account_id.state == 'CTE':
            tipo_cuenta = 'CTE'
        elif decimo.employee_id.bank_account_id.state == 'AHO':
            tipo_cuenta = 'AHO'
        else:
            tipo_cuenta = 'BAN'
        amount = self.set_amount(decimo.pay_amount)
        if len(amount) < 13:
            amount = self.complete_zeros(amount, 13)
        # if len(bic) < 4:
        #     bic = self.complete_zeros(bic, 4)
        ced = decimo.employee_id.identification_id
        if decimo.employee_id.emp_tipo_doc == 'p':
            char = 'P'
        ref = 'Pago de Decimos'
        nombre = decimo.employee_id.name_related.encode('utf-8')
        if not account_employee:
            raise osv.except_osv('Error!', 'El empleado %s no tiene cuanta bancaria asociada' % decimo.employee_id.name_related)

        space = ''
        cadena = "PA" + ced + space.ljust(20-len(ced)) + cur + amount + 'CTA' + tipo_cuenta + account_employee + \
                 space.ljust(20-len(account_employee)) + ref + space.ljust(40-len(ref)) + char + ced + space.ljust(14-len(ced)) + \
                 nombre.ljust(41+13-len(bic)) + bic + os.linesep

        return cadena
    
    def obtener_cadena(self, cr, uid, employee, f_hasta, b_id, data, cont, context):
        #metodo que obtiene la cadena segun formato del banco que se configure
        #TODO Hacer la configuracion del banco con el que se va ha pagar y del formato
        #En este caso hacemos solo para el banco de guayaquil

        ref = "SUELDO DE" + " " + time.strftime('%B del %Y', time.strptime(f_hasta, '%Y-%m-%d')).upper()
        buf = StringIO.StringIO()
        id_char = 'C'
        ced = str(employee.identification_id)
        if employee.emp_tipo_doc == 'p':
            id_char = 'P'
        esp = ['á', 'à', 'â', 'ã', 'ª', 'Á', 'À', 'Â', 'Ã', 'Í', 'Ì', 'Î', 'í', 'ì', 'î', 'é', 'è', 'ê', 'É', 'È', 'Ê', 'ó', 'ò', 'ô', 'õ', 'º', 'Ó', 'Ò', 'Ô', 'Õ', 'ú', 'ù', 'û', 'Ú', 'Ù', 'Û', 'ç', 'Ç', 'ñ', 'Ñ', 'Ñ']
        nor = ['a', 'a', 'a', 'a', 'a', 'A', 'A', 'A', 'A', 'I', 'I', 'I', 'i', 'i', 'i', 'e', 'e', 'e', 'E', 'E', 'E', 'o', 'o', 'o', 'o', 'o', 'O', 'O', 'O', 'O', 'u', 'u', 'u', 'U', 'U', 'U', 'c', 'C', 'n', 'N', 'N']
        forma_pago = "CTA"
        cur = "USD"
        numero_banco = '884'
        band = 0
        # banco == Guayaquil
        if employee.bank_account_id.bank.bic == '17':
            # Si es banco de guayaquil
            cadena = ''
            cadena_formato = self.obtener_formato()
            print ' cadena_formato ', cadena_formato
            for dato in cadena_formato:
                if dato['tipo'] == 'fijo':
                    cadena = cadena + dato['dato'] + dato['separador']
                    print '  cadena ', cadena
                else:
                    cadena = cadena + self.get_data(employee, data, dato) + dato['separador']
                    print '  cadena2 ', cadena
            return cadena + numero_banco + os.linesep
        # Cooperative Cotocollao
        elif employee.bank_account_id.bank.bic == '18':
            factual = time.strftime('%Y-%m-%d')
            fact = factual.split('-')
            print "fecha actual", fact
            fecha = str(fact[2]+'/'+fact[1]+'/'+fact[0])
            tot = str(data['credit'])
            print ' tot ', tot
            val = tot.split('.')
            l = ""
            for item in val[0]:
                l += item
            if len(val[1]) < 2:
                val[1] += '0'
            print 'val[1] ', val[1]
            for item in val[1]:
                l += item
            t_cta = str(employee.bank_account_id.state)
            if t_cta == 'ahorro':
                t_cta = 'C'
            elif t_cta == 'corriente':
                t_cta = 'C'

            t_cod = str(employee.bank_account_id.bank.bic)
            tam_cod = len(t_cod)
            if tam_cod < 3:
                for i in range(3 - tam_cod):
                    t_cod += ' '
            num_cta = str(employee.bank_account_id.acc_number.strip())
            tam_cta = len(num_cta)
            if tam_cta < 13:
                for i in range(13 - tam_cta):
                    num_cta += ' '

            cadena = fecha + ',' + '0' + ',' + '1' + ',' + num_cta.strip() + ',' + t_cta + ',' + tot + ',' + t_cod + os.linesep
            return cadena
#banco == Pichincha
        elif employee.bank_account_id.bank.bic in ['10', '32']: #32 es del banco internacional, 10 del pichincha, el archivo contiene la misma informacion, le hago aqui Ramses
            #Si el banco es el pichincha
            code = employee.bank_account_id.bank.bic
            tam_ced = len(ced)
            if tam_ced < 10:
                for i in range(10 - tam_ced):
                    ced += ' '
            tot = str(data['credit'])
            print ' tot ', tot
            val = tot.split('.')
            l = ""
            for item in val[0]:
                l += item
            if len(val[1]) < 2:
                val[1] += '0'
            print 'val[1] ', val[1]
            for item in val[1]:
                l += item
            t_cta = str(employee.bank_account_id.state)
            t_cod = str(employee.bank_account_id.bank.bic)
            tam_cod = len(t_cod)
            if tam_cod < 3:
                for i in range(3 - tam_cod):
                    t_cod += ' '
            num_cta = str(employee.bank_account_id.acc_number.strip())
            tam_cta = len(num_cta)
            if tam_cta < 13:
                for i in range(13 - tam_cta):
                    num_cta += ' '
            t_em = str(employee.id)

            nom = str(employee.name_related.encode('"UTF-8"'))

            for indi in range(40):
                nom = nom.replace(esp[indi], nor[indi])
            nombre = str(nom)
            print nombre
            tam_nom = len(nombre)
            if tam_nom < 45:
                for i in range(45 - tam_nom):
                    nombre += ' '
            num = str(cont)
            tam_cont = len(num)
            if tam_cont < 3:
                for i in range(3 - tam_cont):
                    num += ' '
            space = ''
            if code == '10':
                cadena = "PA" + ced + space.ljust(20-len(ced)) + cur + l.zfill(13) + forma_pago + t_cta + num_cta + space.ljust(20-len(num_cta))+ ref + space.ljust(40-len(ref)) + id_char + ced + space.ljust(14-len(ced)) + nombre.ljust(41+13-len(code)) + str(code) + os.linesep
            else:
                company_account = employee.company_id.partner_id.bank_ids
                if not company_account:
                    raise osv.except_orm('Error!', 'La Compania no tiene cuenta bancaria asociada')
                slip = self.pool.get('hr.payslip').browse(cr, uid, data['id'])
                cadena = "PA" + '\t' + str(cont) + '\t' + cur + '\t' + l.zfill(13) + '\t' + forma_pago + '\t' + t_cta + '\t' + num_cta[:10] + '\t' + '\t' + id_char + '\t' + ced + '\t' + \
                         nombre[0:40] + chr(13) + chr(10)
            return cadena

        # Produbanco Cooperative
        elif employee.bank_account_id.bank.bic == '36':

            factual = time.strftime('%d%m%y')
            fecha = str(factual)
            print "fecha: ",fecha
            tot = str(data['credit'])
            print ' tot ', tot
            val = tot.split('.')
            l = ""
            for item in val[0]:
                l += item
            if len(val[1]) < 2:
               val[1] += '0'
            print 'val[1] ', val[1]
            for item in val[1]:
                l += item
            t_cta = str(employee.bank_account_id.state)
            if t_cta == 'Débito':
                t_cta = 'D'
            elif t_cta == 'Crédito':
                t_cta = 'C'
            t_cod = str(employee.bank_account_id.bank.bic)
            tam_cod = len(t_cod)
            if tam_cod < 3:
                for i in range(3 - tam_cod):
                    t_cod += ' '
            num_cta = str(employee.bank_account_id.acc_number.strip())
            tam_cta = len(num_cta)
            if tam_cta < 13:
                for i in range(13 - tam_cta):
                    num_cta += ' '
            
            
            nom = str(employee.name_related.encode('"UTF-8"'))
            for indi in range(40):
                nom = nom.replace(esp[indi], nor[indi])

            twoplaces = Decimal(10) ** -2
            
            cadena = "C" + str(nom).ljust(40) + num_cta.strip() + str(Decimal(tot).quantize(twoplaces)).replace(".", "").zfill(14) + fecha + "N" + os.linesep
            return cadena

        
        
    
    def validar(self, cr, uid, data, context):
        print "context: ", data
        sucursal_id = data['form']['sucursal_id']
        # Validar si existen cuentas repetidas
        sql = "select b.id from hr_employee e join hr_employee_bank b on e.bank_account_id = b.id and e.state_emp in ('active','sold_out') and e.shop_id = " + str(sucursal_id) +" group by b.id having count(b.id) > 1"
        print "validar sql: ", sql
        cr.execute(sql)
        cuentas = cr.fetchall()

        sql = "select name from hr_employee where shop_id = " +str(sucursal_id)+ " and state_emp in ('active','sold_out') and modo_pago = 'transferencia' and bank_account_id is null"
        cr.execute(sql)
        pagos = cr.dictfetchall()

        if not cuentas and not pagos:
            return self.crear_cash(cr, uid, data, context)
        else:
            cadena = []
            if cuentas:
                for cuenta in cuentas:
                    texto = ''
                    ids = pooler.get_pool(cr.dbname).get('hr.employee').search(cr, uid, [('bank_account_id', '=', cuenta)])
                    emps = pooler.get_pool(cr.dbname).get('hr.employee').browse(cr, uid, ids)
                    for emp in emps:
                        texto += emp.name + ", "
                    cadena.append("%s por poseer la cuenta: %s\n\n" % (texto, emps[0].bank_account_id.name))
                texto = ''
                for txt in cadena:
                    texto += "Conflicto entre los empleados: %s" % txt
                raise osv.except_osv("No se puede generar cash!!", '%s' % (texto))
                return {}

            if pagos:
                names = ''
                for pago in pagos:
                    names = names + pago['name'] + ' '
                texto = 'Estos empleados tienen forma de pago transferencia pero no tienen cta bancaria ' + names
                raise osv.except_osv("No se puede generar cash!!!", '%s' % (texto))
                return {}


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
