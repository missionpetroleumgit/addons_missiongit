# -*- encoding: utf-8 -*-
########################################################################
#                                                                       
# @authors: Guillermo Herrera                                                                          
# Copyright (C) 2014 BITConsultores.                                 
#                                                                       
#This program is free software: you can redistribute it and/or modify   
#it under the terms of the GNU General Public License as published by   
#the Free Software Foundation, either version 3 of the License, or      
#(at your option) any later version.                                    
#
# This module is GPLv3 or newer and incompatible
# with OpenERP SA "AGPL + Private Use License"!
#                                                                       
#This program is distributed in the hope that it will be useful,        
#but WITHOUT ANY WARRANTY; without even the implied warranty of         
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the          
#GNU General Public License for more details.                           
#                                                                       
#You should have received a copy of the GNU General Public License      
#along with this program.  If not, see http://www.gnu.org/licenses.
########################################################################

from openerp.osv import fields, osv
from dateutil import parser
import time


class hr_acumulados(osv.osv):
    _name = "hr.acumulados"
    _description = "Acumulados Proviciones"
    
    def confirmar_acumulados(self, cr, uid, ids, context):
        self.write(cr, uid, ids, {'state':'confirm'})
        return True
    
    _columns = {'name': fields.char('Descripcion', size=128, readonly=True),
                'employee_id': fields.many2one('hr.employee', 'Empleado',required= True),
                'acumulados_line': fields.one2many('hr.acumulados.line', 'acumulado_id', 'Detalles'),
                'state': fields.selection([('draft', 'Borrador'), ('ready', 'Listo'), ('confirm', 'Confirmado')], 'Estado', readonly=True),
                'payslip_id': fields.many2one('hr.payslip', 'Liquidacion',readonly=True),
                'fch_contrato':fields.date('Inicio Contrato'),
                }
    _defaults = {
        'state': lambda * a: 'draft',
    }
    _sql_constraints = [
        ('unique_emp_acum', 'unique(employee_id)', 'Solo puede ingresar un acumulado por empleado')
        ]

    def create(self, cr, uid, vals, context=None):
        vals['state'] = 'ready'
        employee = self.pool.get('hr.employee').browse(cr, uid, vals.get('employee_id'))
        desc = 'Registro de Acumulados' + employee.name_related
        vals['name'] = desc
        return super(hr_acumulados, self).create(cr, uid, vals, context=None)

    def onchange_employee_id(self, cr, uid, ids, employee_id, context=None):
        res = {'value':{}}
        if employee_id:
            employee = self.pool.get('hr.employee').browse(cr, uid, employee_id)
            contract_ids = self.pool.get('hr.contract').search(cr, uid, [('employee_id', '=', employee_id)])
            contract = self.pool.get('hr.contract').browse(cr, uid, contract_ids[0])
            desc = 'Registro de Acumulados' + employee.name_related
            date = contract.date_start
            res['value'].update({'name': desc, 'fch_contrato': date})
        return res

hr_acumulados()

class hr_acumulados_line(osv.osv):
    _name = "hr.acumulados.line"
    _description = "Detalle Acumulados Proviciones "
    
    # Calcular decimo3 y vacaciones

    # def create(self, cr, uid, vals, context=None):
    #     # vals['decimo3'] = (vals['imponible'] * vals['dias_t']/30.00) /12
    #     # vals['vacaciones'] = (vals['imponible'] * vals['dias_t']/30.00) /24
    #     if vals['dias_t'] < 30:
    #            vals['imponible'] = vals['imponible'] * vals['dias_t']/30.00
    #     acumulado_line_id = super(hr_acumulados_line, self).create(cr, uid, vals, context=context)
    #     return acumulado_line_id

    # def write(self, cr, uid, ids, vals, context=None):
    #     if  vals.has_key('imponible') and vals.has_key('dias_t') :
    #         vals['decimo3'] = (vals['imponible']* vals['dias_t']/30.00) /12
    #         vals['vacaciones'] = (vals['imponible']* vals['dias_t']/30.00) /24
    #         if vals['dias_t'] < 30:
    #             vals['imponible'] = vals['imponible']* vals['dias_t']/30.00
    #     acumulado_line_id = super(hr_acumulados_line, self).write(cr, uid, ids, vals, context=context)
    #     return acumulado_line_id


    _columns = {
        'inicio_mes': fields.many2one('hr.period.period', 'Mes'),
        # 'inicio_mes': fields.date('Inicio del mes'),
        'name': fields.char('Descripcion', size=128),
        'acumulado_id': fields.many2one('hr.acumulados', 'Detalle', ondelete='cascade'),
        #                 'period_id': fields.many2one('hr.contract.period', 'Periodo de Trabajo', required=True),
        'imponible': fields.float('Imponible', digits=(6, 2), required=True),
        'decimo3': fields.float('Decimo 3ro', digits=(6, 2)),
        'vacaciones': fields.float('Vacaciones', digits=(6, 2)),
        'dias_t':fields.integer('Dias Trabajados', required=True),
        # 'date':fields.date('Fecha'),
        'p_inicial': fields.boolean('Perido Inicio Contrato', help='Marcas si es el perido de Inicio del Contrato',
                                    invisible=True),
        'decimo4': fields.float('Decimo 4to', digits=(6, 2), readonly=True),
                }
    _defaults = {
        'dias_t':lambda * a:30,
    }

    def onchange_inicio_mes(self, cr, uid, ids, inicio_mes, context=None):
        res = dict()
        if inicio_mes:
            inicio_mes = parser.parse(inicio_mes)
            if inicio_mes.day.real != 1:
                res['value'] = {'inicio_mes': None}
                res['warning'] = {'title': 'Alerta', 'message': 'Solo se puede seleccionar el dia primero de cada mes'}
                return res

    def calcular(self, cr, uid, ids, imponible, dias_t, context=None):
        res = {'value':{}}
        user = self.pool.get('res.users').browse(cr,uid,uid)
        if 'employee_id' in context:
            employee_id = context['employee_id']
            if dias_t and imponible:
                contract_pool = self.pool.get('hr.contract')
                contract_ids = contract_pool.search(cr, uid, [('employee_id', '=', employee_id)])
                if not contract_ids:
                    res['warning'] = {'title': 'Alerta', 'message': 'El empleado no tiene contrato'}
                    return res
                contract = contract_pool.browse(cr, uid, contract_ids[0], context=None)
                res['value']['decimo3'] = (imponible*dias_t/30.00) /12
                res['value']['vacaciones'] = (imponible*dias_t/30.00) /24
                res['value']['decimo4'] = (user.company_id.base_amount * dias_t * contract.horas_x_dia)/2880.00
        return res
#     _sql_constraints = [
#         ('unique_periodo_acum', 'unique(acumulado_id, period_id)', 'Ya se registraron datos para este Periodo!'),
#         ]
hr_acumulados_line()
