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


class hr_payslip_variation_hours(osv.Model):

    _name = "hr.payslip.variation.hours"

    _columns = {
        'name' : fields.char('Descripcion', size=16),
        'date_from': fields.date('Fecha Desde'),
        'date_to': fields.date('Fecha Hasta'),
        'txt_filename': fields.char('Nombre Archivo', readonly=True),
        'txt_binary': fields.binary(),
        'company_id': fields.many2one('res.company', 'Compania'),
    }

    _defaults = {
        'txt_filename': 'Nombre Archivo',
    }

    def obtener_cadena(self, cr, uid, employee, f_hasta, data, cont, context):
        #metodo que obtiene la cadena segun formato del banco que se configure
        #TODO Hacer la configuracion del banco con el que se va ha pagar y del formato
        #En este caso hacemos solo para el banco de guayaquil

        buf = StringIO.StringIO()

        esp = ['á', 'à', 'â', 'ã', 'ª', 'Á', 'À', 'Â', 'Ã', 'Í', 'Ì', 'Î', 'í', 'ì', 'î', 'é', 'è', 'ê', 'É', 'È', 'Ê', 'ó', 'ò', 'ô', 'õ', 'º', 'Ó', 'Ò', 'Ô', 'Õ', 'ú', 'ù', 'û', 'Ú', 'Ù', 'Û', 'ç', 'Ç', 'ñ', 'Ñ', 'Ñ']
        nor = ['a', 'a', 'a', 'a', 'a', 'A', 'A', 'A', 'A', 'I', 'I', 'I', 'i', 'i', 'i', 'e', 'e', 'e', 'E', 'E', 'E', 'o', 'o', 'o', 'o', 'o', 'O', 'O', 'O', 'O', 'u', 'u', 'u', 'U', 'U', 'U', 'c', 'C', 'n', 'N', 'N']
        forma_pago = "CTA"
        cur = "USD"
        numero_banco = '884'

        fact = f_hasta.split('-')
        fecha = str(fact[0]+';'+fact[1])
        tot = str(data['credit'])
        val = tot.split('.')
        l = ""
        ncedula = str(employee.identification_id)

        obj_company = self.pool.get('res.company').browse(cr, uid, data['company_id'])
        cadena = str(obj_company.partner_id.part_number) + ';' + '0001' + ';' + fecha + ';' + 'INS' + ';' + ncedula + ';' + tot + ';' + 'X' + '\r\n'
        return cadena


    def generate_file(self, cr, uid, ids, context=None):
        if not ids:
            return {'type': 'ir.actions.act_window_close'}
        if context is None:
            context = {}
        form = self.read(cr, uid, ids)[0]
        type_hr = form.get('type_hr')
        sucursal_id = form.get('dep_id')
        if sucursal_id:
            s_id = sucursal_id[0]
        else:
            s_id = False
        banco_id = form.get('bank_id')
        f_desde = form.get('date_from')
        f_hasta = form.get('date_to')
        id_company = form.get('company_id')[0]

#**************************************************************************************************
        buf = StringIO.StringIO()

        sql="select aml.employee_id, '0.00' as debit, sum(pr.total) as credit, aml.name as ref, aml.company_id as company_id \
                from hr_payslip aml, hr_payslip_line pr, hr_salary_rule_category src\
                where aml.id = pr.slip_id \
                and pr.category_id = src.id \
                and aml.date_from = '%s' \
                and aml.date_to = '%s' \
                and src.code = 'IGBS' \
                and pr.code <> 'BASICO' \
                and aml.company_id = '%s' \
                group by aml.employee_id, ref, aml.company_id \
                order by aml.name" % (f_desde, f_hasta, id_company)

        cr.execute(sql)
        res = cr.dictfetchall()

        cont = 1
        bankk_account_id = 0
        if res:
            for data in res:
                employee = self.pool.get('hr.employee').browse(cr, uid, data['employee_id'])
                cadena = ""
                  
                if employee.state_emp == 'active':
                    if data['credit']:
                        cadena = self.obtener_cadena(cr, uid, employee, f_hasta, data, cont, context)
                        buf.write(upper(cadena))
                        cont += 1
        else:
            raise osv.except_osv("Pagos Nomina ", 'No existen registros para el tipo. %s' % (type_hr))
            return
#**************************************************************************************************

        out = base64.encodestring(buf.getvalue())
        buf.close()
        name = "%s%s%s.csv" % ("NCR", time.strftime('%Y%m%d'), "XX_01")
        return self.write(cr, uid, ids, {'txt_binary': out, 'txt_filename': name})
    
    
hr_payslip_variation_hours()
#, ('anticipo', 'Anticipos'), ('prestamo', 'Prestamos'), ('util', 'Utilidades'), ('decim4to', 'Decimo 4to'), ('decim3ro', 'Decimo 3ro')

