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

class hr_adm_incomes(osv.osv):
    _name = 'hr.adm.incomes'
    _description = "Administracion de Ingresos del Rol de Pagos"

    
    _columns = {
            'name' : fields.char('Descripcion', size=64,required=True),
            'code' : fields.char('Codigo', size=64, required=True),
            'payroll_label': fields.char('Etiqueta en el Rol de Pagos', size=128, required=True),
            'default_value': fields.float('Valor Por Defecto', digits=(8, 2)),
            'orden':fields.integer('Orden'),

    }
    _defaults = {
                 'default_value' : lambda * a : 0.0,
    }
    _sql_constraints = [
            ('unique_code', 'unique(code)', 'El codigo debe ser unico')
            ]

hr_adm_incomes()

class hr_income(osv.osv):
    _name = "hr.income"
    _description = "Incomes for Employee"

    def renew_license(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, { 'state': 'procesado'})

    def onchange_calcula_valor(self, cr, uid, ids, adm_id, employee_id, horas):
        res ={}
        sueldo = 0
        value = 0
        if adm_id and employee_id and horas:
            obj_contrato = self.pool.get('hr.contract')
            obj_adm_incomes = self.pool.get('hr.adm.incomes')

            adm_income = obj_adm_incomes.browse(cr,uid,adm_id)[0]
            contrato_id = obj_contrato.search(cr,uid,[('employee_id','=', employee_id)])
            for contratos in obj_contrato.browse(cr,uid,contrato_id):
                sueldo = contratos.wage
                valor_hora = sueldo/(contratos.horas_x_dia * 30)
                value = adm_income.default_value * valor_hora * horas
        res['value']={'value':value}
        return res

    def on_change_value(self, cr, uid, ids, fijo, context=None):
        res={'value':{}}
        if fijo:
            res['value'].update({'date':None})
        else:
            res['value'].update({'date':time.strftime('%Y-%m-%d')})
        return res

    _columns = {
#        'payroll_id' : fields.many2one('hr.payroll', 'Rol de Pagos'),
#        'contract_id': fields.many2one('hr.contract', 'Contrato'),
        'name': fields.char('Description', size=50),
        'adm_id': fields.many2one('hr.adm.incomes', 'Tipo de Ingreso'),
#        'value': fields.float('Valor', digits=(16, int(config['price_accuracy']))),
        'value': fields.float('Valor', digits=(12, 2)),
        'employee_id': fields.many2one('hr.employee', 'Empleado'),
        'state': fields.selection([('draft', 'No Procesado'), ('procesado', 'Procesado'), ('no_usado', 'No Usado')], 'Status', readonly=True),
        'date': fields.date('Fecha de Registro'),
        'comment':fields.text('Comentario'),
        'payslip_id': fields.many2one('hr.payslip', 'Nómina'),
        'h_registro': fields.boolean('Registrar En Horas?'),
        'horas': fields.float('Horas', digits=(6, 2)),
        'company_id': fields.many2one('res.company', 'Compania'),
        'fijo': fields.boolean('Ingreso Fijo?', help="Marque este casillero si desea que este Ingreso sea acreditado todos los meses en la nómina del empleado"),
    }

    _sql_constraints = [
        ('name', 'unique(name)', 'Ya se ha cargado la informacion de este rol !.'),
    ]

    _defaults = {
        'state': lambda * a: 'draft',
        'date': lambda * a: time.strftime('%Y-%m-%d'),
        'fijo': lambda * a: False,
        'company_id': lambda s, cr, uid, c: s.pool.get('res.company')._company_default_get(cr, uid, 'hr.income', context=c),
    }

    def unlink(self, cr, uid, ids, context=None):
        for income in self.browse(cr, uid, ids, context=None):
            if income.state != 'draft':
                raise osv.except_osv(('Error !'), ('No se pueden eliminar ingresos en estado procesado, ingreso:' + income.adm_id.name))
        return super(hr_income, self).unlink(cr, uid, ids, context=context)

hr_income()