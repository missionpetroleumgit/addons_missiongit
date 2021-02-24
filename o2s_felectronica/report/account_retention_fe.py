# -*- encoding: utf-8 -*-
##############################################################################
#
#    Author :  Cristian Salamea cristian.salamea@gnuthink.com
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

# import time
# import pooler
# from report import report_sxw
# from mx import DateTime
# from osv import osv, fields
# import tools
# import re
import time
from number_to_text import Numero_a_Texto

import re    #Muestra los valores de numeros separados por coma
from openerp import tools

from openerp.osv import osv
from openerp.report import report_sxw

from datetime import datetime, date, time, timedelta
from openerp.exceptions import except_orm, Warning

class account_retention_fe(report_sxw.rml_parse):
    _name = 'report.account.retention.fe'

    def _get_taxes(self, id):
        print "ID", id
        res = self.pool.get('account.invoice.tax').search(self.cr, self.uid, [('invoice_id','=', id), ('deduction_id', '!=', False)])
        
        if res !=[]:
            res1  = self.pool.get('account.invoice.tax').browse(self.cr, self.uid, res)
            codigo = int(res1[0].invoice_id)
            invoice  = self.pool.get('account.invoice.tax').browse(self.cr, self.uid, codigo)
            # base = invoice.BaseRetencion
            #
            # for aux in res1:
            #     if not aux.percent:
            #         if aux.tax_group=='ret_vat':
            #             self.pool.get('account.invoice.tax').write(self.cr, self.uid, aux.id, {"percent":round(abs(aux.amount)*100/base)})
            #         else:
            #             self.pool.get('account.invoice.tax').write(self.cr, self.uid, aux.id, {"percent":round(abs(aux.amount)*100/aux.base)})
            
        return self.pool.get('account.invoice.tax').browse(self.cr, self.uid, res)

    def _get_tax_group(self,group):
        print "GROUP", group
        if group in ('721','723','725','727','729','731'):
            return 'Imp. IVA'
        else:
            return 'Imp. Renta'

    def _get_total(self, id):
        print "tot**", id
        total = 0.00
        res = self.pool.get('account.invoice.tax').search(self.cr, self.uid, [('invoice_id','=', id), ('deduction_id', '!=', False)])

        if res !=[]:
            res1  = self.pool.get('account.invoice.tax').browse(self.cr, self.uid, res)
            for tot in res1:
                total += abs(tot.amount)
        return abs(total)

    def _user(self):
        user = self.pool.get('res.users').browse(self.cr, self.uid, self.uid)
        return user.name
    
    def direccion(self, obj):
        dir = ' '
        if obj:
            if obj.street:
                dir = tools.ustr(obj.street)
                if dir !=' ':
                    if obj.street2:
                        dir = dir + ' y ' + tools.ustr(obj.street2)
        return dir[:37]
    
    def _anio(self, invoice): 
        anio = ''
        if invoice.move_id:
            anio = invoice.move_id.period_id.name.split('/')[1]
        else:
            anio=''
        return anio
    
    def _cadena(self,cadena):
        return cadena.encode('"UTF-8"')[:54]
    
    def _get_type(self, nombre):
        
        if nombre == 'invoice':
            return 'FACTURA'
        elif nombre == 'purchase_liq':
            return 'LIQUIDACION'
        elif nombre == 'sales_note':
            return 'NOTA DE VENTA'
        elif nombre == 'anticipo':
            return 'ANTICIPO'
        elif nombre == 'gas_no_dedu':
            return 'GASTO NO DEDUCIBLE'
        elif nombre == 'doc_inst_est':
            return 'DOC. ESTADO'
        elif nombre == 'doc_inst_fin':
            return 'DOC. INS. FINANCIERA'
        elif nombre == 'doc_emp_avi':
            return 'DOC. EMP. AVIACION'  
        elif nombre == 'doc_emi_ext':
            return 'DOC. EMI. EXTERIOR'               

        else:
            return ''
            
    #Funcion que separa el punto en lugar de comas y pone a 2 decimales las cantidades
    def comma_me(self,amount):
        
        print ' FORMATO a ret **** '
        if not amount:
            amount = 0.0
        if type(amount) is float:
            print ' FORMATO b ret **** '
            amount = str('%.2f'%amount)
        else :
            print ' FORMATO c ret **** '
            amount = str('%.2f'%amount)
        if (amount == '0'):
            return ' '
        orig = amount
        new = re.sub("^(-?\d+)(\d{3})", "\g<1>,\g<2>", amount)
        return new
    
    def rec_texto(self,texto):
        print 'texto',texto
        tex=re.sub("\D", "", texto)
        print "rec texto", tex
        res=''
        res=tex[0:3]
        if res.strip() == '102':
            return '20'
        elif res.strip() == '910':
            return '10'
        else:
            print 'res',res
            return res  


    def _get_percent(self,nombre):
        # tex=re.sub("\D", "", nombre)
        # nombre=tex[0:3]
        if nombre == '725':
            return '30 %'
        elif nombre == '308':
            return '2 %'
        elif nombre == '304B':
            return '8 %'
        elif nombre == '312':
            return '1.75 %'
        elif nombre == '309':
            return '1.75 %'
        elif nombre == '721':
            return '10 %'
        elif nombre == '723':
            return '20 %'
        elif nombre == '727':
            return '50 %'
        elif nombre == '729':
            return '70 %'
        elif nombre == '731':
            return '100 %'
        elif nombre == '307':
            return '2 %'
        elif nombre == '322':
            return '1.75 %'
        elif nombre == '320':
            return '8 %'
        elif nombre == '341':
            return '2 %'
        elif nombre == '340':
            return '1 %'
        elif nombre == '304':
            return '8 %'
        elif nombre == '303':
            return '10 %'
        elif nombre == '310':
            return '1 %'
        elif nombre == '3440':
            return '2.75 %'
        elif nombre.strip() == '102':
            return '20 %'
        elif nombre.strip() == '910':
            return '10 %'
        elif nombre == '411':
            return '25 %'
        else:
            return ''

    def _get_base(self,nombre,base):
        #tex=(nombre)
        base1=base 
        nombre=nombre
        print "NOMBRE", nombre
        print "BASE", base1
        if nombre == '322':
            return base1/10
        else:
            return base1 

    def get_company(self):
        print "ENTRA COMPANY"
        res = []
        nombre = ''
        direccion = ''
        ruc = ''
        user = self.pool.get('res.users').browse(self.cr, self.uid, self.uid)
        print "user***", user
        id_pars = self.pool.get('res.partner').search(self.cr, self.uid, [('ref', '=', 'COEBIT'), ('company_id', '=', user.company_id.id)])
        obj_partds = self.pool.get('res.partner').browse(self.cr, self.uid, id_pars)
        if len(obj_partds)>0:
            dsuc = obj_partds.sucursal1

        nombre = user.company_id.partner_id.name
        print "nombre", nombre
        direccion = str(user.company_id.partner_id.street) + ' Y ' + str(user.company_id.partner_id.street2)
        print "direccion", direccion
        ruc = user.company_id.partner_id.part_number
        print "ruc", ruc
        print "pos fiscal", str(user.company_id.partner_id.cod_posfis)
        if str(user.company_id.partner_id.cod_posfis) == '000':
            pos_fis = ''
        elif not user.company_id.partner_id.cod_posfis:
            pos_fis = ''
        else:
            pos_fis = 'CONTRIBUYENTE ESPECIAL N: '+str(user.company_id.partner_id.cod_posfis)
        obli_c = user.company_id.partner_id.obli_contab
        print "obli_c", obli_c
        phone = user.company_id.partner_id.phone
        print "phone", phone
        logo = user.company_id.logo
        print "logo", logo
        res = [nombre, direccion, ruc, pos_fis, obli_c, phone, dsuc, logo]
        print "res", res
        return res
    
    def get_acceso(self, id):
        name = ''
        id_acse = self.pool.get('account.factura.electronica').search(self.cr, self.uid, [('factelect_id','=',id)])
        obj_acse = self.pool.get('account.factura.electronica').browse(self.cr, self.uid, id_acse)
        name = obj_acse[0].clave_acceso
        print "RETORNO", name        
        return name

    def get_dir(self, objeto):
        res = ''
        if objeto:
            res += tools.ustr(objeto.street).upper()
            if objeto.street2:
                res += ' Y ' + tools.ustr(objeto.street2).upper()
        return res
    
    def __init__(self, cr, uid, name, context):
        super(account_retention_fe, self).__init__(cr, uid, name, context)
        self.localcontext.update({
                'time' : time,
                'rec_texto':self.rec_texto,
                'get_taxes' : self._get_taxes,
                'get_total': self._get_total,
                'user': self._user,
                'direccion':self.direccion,
                'anio':self._anio,
                'cadena':self._cadena,
                'tipo':self._get_type,
                'tax_group':self._get_tax_group,
                'formato':self.comma_me,
                '_get_percent':self._get_percent,
                '_get_base':self._get_base,
                'get_company':self.get_company,
                'get_acceso':self.get_acceso,
		'get_dir':self.get_dir,
                })
        self.context = context

report_sxw.report_sxw('report.account.retentionfe', 
                      'account.invoice', 
                      'addons_tiw/o2s_felectronica/report/account_retention.rml',
                      parser=account_retention_fe, 
                      header=False)
