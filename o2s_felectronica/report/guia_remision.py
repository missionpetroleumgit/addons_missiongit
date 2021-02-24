# -*- encoding: utf-8 -*-
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 3
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.

import time
from number_to_text import Numero_a_Texto

import re    #Muestra los valores de numeros separados por coma
from openerp import tools

from openerp.osv import osv
from openerp.report import report_sxw

from datetime import datetime, date, time, timedelta
from openerp.exceptions import except_orm, Warning

class guia_remision(report_sxw.rml_parse):
    _name = 'guia.remision'
    _description = 'Guia Remision'
    
    def __init__(self, cr, uid, name, context):
        super(guia_remision, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
            'rec_texto':self.rec_texto,
            'get_text':self.get_text,
            'get_dir':self.get_dir,
            'get_tax':self.get_tax,
            'get_date':self.get_date,
            'get_contact_invoice':self.get_contact_invoice,
            'formato':self.comma_me,
            'get_company':self.get_company,
            'get_acceso':self.get_acceso,
            '_get_type':self._get_type,
            'get_dirdestino':self.get_dirdestino,
            'usuario':self._user,
        })
        self.context = context

    def _get_type(self, nombre):
        
        if nombre == 'out_invoice':
            return 'FACTURA'
        elif nombre == 'in_refund':
            return 'NOTA DE DEBITO'
        elif nombre == 'out_refund':
            return 'NOTA DE CREDITO'
        else:
            return ''

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
        
    #Funcion que separa el punto en lugar de comas y pone a 2 decimales las cantidades
    def comma_me(self,amount):
        if not amount:
            amount = 0.0
        if type(amount) is float:
            amount = str('%.2f'%amount)
        else :
            amount = str(amount)
        if (amount == '0'):
             return ' '
        orig = amount
        new = re.sub("^(-?\d+)(\d{3})", "\g<1>,\g<2>", amount)
        if orig == new:
            return new
        else:
            return self.comma_me(new)
    
    def get_contact_invoice(self, partner):
        name = ''
        if partner.address:
            for address in partner.address:
                if address.type:
                    if address.type == 'invoice':
                        if address.name:
                            name = tools.ustr(address.name).upper()
                        break
        return name
    
    def get_acceso(self, id):
        name = ''
        id_acse = self.pool.get('stock.picking.electronica').search(self.cr, self.uid, [('gremielect_id','=',id)])
        obj_acse = self.pool.get('stock.picking.electronica').browse(self.cr, self.uid, id_acse)
        name = obj_acse[0].clave_acceso
        print "RETORNO", name        
        return name

    def get_dirdestino(self, id):
        print "ID DESTINO", id
        name = ''
        id_acse = self.pool.get('res.partner').search(self.cr, self.uid, [('id','=',id)])
        obj_acse = self.pool.get('res.partner').browse(self.cr, self.uid, id_acse)[0]
        print "RETORNO***1", obj_acse
        dfactu = obj_acse.street
        dfactu2 = obj_acse.street2
        if dfactu and dfactu2:
            name = str(dfactu) + str(dfactu2)
        elif dfactu and not dfactu2:
            name = str(dfactu)
        elif dfactu2 and not dfactu:
            name = str(dfactu2)
        else:
            name = ''
        print "RETORNO********++", name
        return name
        
    def get_dir(self, objeto):
        res = ''
        if objeto:
            res += tools.ustr(objeto.street).upper()
            if objeto.street2:
                res += ' y ' + tools.ustr(objeto.street2).upper()
        return res
    
    def get_text(self, cantidad):
        cant = float(cantidad)
        res = Numero_a_Texto(cant)
        tam = len(res)
        return res

    def rec_texto(self,texto):
#        print 'texto',texto
        tex=(texto)
        res=''
        res=tex[8:11]
#        print 'res',res
        return res

    def get_date(self):
        print "get_ciudad", self.uid
        retorno = 0
        id_emp = self.pool.get('hr.employee').search(self.cr, self.uid, [('user_id','=',self.uid)])
        print "id_emp: ", id_emp
        if id_emp == []:
            raise osv.except_osv(('Aviso'), ('Usuario no tiene sucursal!'))
        else:
            obj_emp = self.pool.get('hr.employee').browse(self.cr, self.uid, id_emp)
            retorno = obj_emp[0].shop_id.name
            print "RETORNO", retorno
        return retorno  
    
    def get_tax(self, id_fac):
        tax_obj = self.pool.get('account.invoice.tax')
        res = 0
        id_imp = tax_obj.search(self.cr, self.uid, [('invoice_id', '=', int(id_fac))])
        if id_imp:
            obj_imp = self.pool.get('account.invoice.tax').browse(self.cr, self.uid, id_imp)
            code_tax = int(obj_imp[0].tax_code_id.id)

            id_tax = self.pool.get('account.tax').search(self.cr, self.uid, [('ref_tax_code_id', '=', code_tax)])

            if id_tax != []:
                obj_tax = self.pool.get('account.tax').browse(self.cr, self.uid, id_tax)
                res = int(abs((obj_tax[0].amount) * 100))
        return res

    def _user(self):
        user = self.pool.get('res.users').browse(self.cr, self.uid, self.uid)
        return tools.ustr(user.name)
    
report_sxw.report_sxw('report.guia.remision',
                      'stock.picking',
                      'addons_tiw/o2s_felectronica/report/guia_remision.rml',
                      parser=guia_remision,
                      header=False)
    
    
   
