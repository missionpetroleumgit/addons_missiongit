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
__author__ = ''
from openerp.osv import fields, osv
import time


class hr_income(osv.osv):
    _inherit = "hr.income"
    
    def onchange_calcula_valor_hora(self, cr, uid, ids, adm_id, employee_id, horas,analytic_id):
        res ={}
        sueldo = 0
        value = 0
        porcentaje = 100
        
        if adm_id and employee_id and horas:
            obj_contrato = self.pool.get('hr.contract')
            obj_adm_incomes = self.pool.get('hr.adm.incomes')
            
            adm_income = obj_adm_incomes.browse(cr,uid,adm_id)[0]
            contrato_id = obj_contrato.search(cr,uid,[('employee_id','=', employee_id)])
            for contratos in obj_contrato.browse(cr,uid,contrato_id):
#                 for ccostos in contratos.contract_analytic_ids:
#                     if ccostos.account_analytic_id.id == analytic_id:
#                         porcentaje = ccostos.rate
                        
                sueldo = contratos.wage
                print "sueldo: ", sueldo
                
                valor_hora = sueldo/(contratos.horas_x_dia * 30.00)
                print "valor_hora: ", valor_hora
                valor_hora = valor_hora * porcentaje / 100.00
                print "valor_hora: ", valor_hora
                value = adm_income.default_value * valor_hora * horas
                print "value: ", value
        res['value']={'value':round(value,2)}
        return res
    
    _columns = {
            'analytic_id': fields.many2one('account.analytic.account', "Centro de Costos"),
    }


hr_income()