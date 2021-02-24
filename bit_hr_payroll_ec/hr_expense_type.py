# -*- coding: utf-8 -*-
##############################################################################
#
#    Open2S, Open Source Solutions S.A.
#    Copyright (C) 2015 Open2S.
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

class hr_expense_type(osv.osv):
    _name = 'hr.expense.type'
    _description = "Administracion de Egresos al Rol de Pagos"


    _columns = {
        'name': fields.char('Descripcion', size=64,required=True),
        'code': fields.char('Codigo', size=64, required=True),
        'payroll_label': fields.char('Etiqueta en el Rol de Pagos', size=128, required=True),
        'aporte_iess': fields.boolean('Aportes Iess'),
        'impuesto_renta': fields.boolean('Impuesto Renta'),
        'fondo_reserva': fields.boolean('Fondo de Reserva', help="Seleccione si es su valor se toma en cuenta para el fondo de reserva"),
        'default_value': fields.float('Valor Por Defecto', digits=(8, 2)),
        'orden':fields.integer('Orden'),
        'account_id': fields.many2one('account.account', 'Cuenta contable', required=False)

    }
    _defaults = {
        'default_value': lambda * a: 0.0,
    }
    _sql_constraints = [
        ('unique_code', 'unique(code)', 'El codigo debe ser unico')
    ]

hr_expense_type()



class hr_expense(osv.osv):
    _name = "hr.expense"
    _description = "Expenses for Employee"
    _rec_name = 'employee_id'

    def renew_license(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, { 'state': 'procesado'})

    def onchange_calcula_valor(self, cr, uid, ids, employee_id, porcentaje):
        res ={}
        sueldo = 0
        value = 0
        if employee_id and porcentaje:
            obj_contrato = self.pool.get('hr.contract')
            contrato_id = obj_contrato.search(cr,uid,[('employee_id','=', employee_id)])
            for contratos in obj_contrato.browse(cr,uid,contrato_id):
                sueldo = contratos.wage
                value = sueldo * porcentaje / 100.00
        res['value']={'value':value}
        return res


    _columns = {
        #        'payroll_id': fields.many2one('hr.payroll', 'Rol de Pagos'),
        #'contract_id': fields.many2one('hr.contract', 'Contrato'),
        'name': fields.char('Descripcion', size=128),
        'expense_type_id': fields.many2one('hr.expense.type', 'Tipo de Egreso'),
        'value': fields.float('Valor', digits=(16, 2)),
        'employee_id': fields.many2one('hr.employee', "Empleado"),
        'state': fields.selection([('draft', 'No Procesado'), ('procesado', 'Procesado')], 'Status'),
        'date': fields.date('Fecha de Registro'),
        #        'res_partner':fields.many2one('res.partner', 'Proveedor', domain=[('active', '=', True), ('supplier', '=', True)]),
        'comment':fields.text('Comentario'),
        #         'sucursal_id': fields.many2one('sale.shop', 'Sucursal'),sale.shop
        'reg_porcentaje': fields.boolean('Registrar en Porcentaje?'),
        'porcentaje': fields.float('Porcentaje', digits=(6, 2)),
        'rel_name': fields.char('rel name'),

        'fijo': fields.boolean('Egreso Fijo?', help="Marque este casillero si desea que este EGRESO sea descontado todos los meses en la nómina del empleado"),
        'date_egr_f': fields.date('Fecha Inicio Egr Fijo', help="Fecha de inicio de aplicación del Egreso Fijo"),
        'invoice_id': fields.many2one('account.invoice', 'Ref. factura'),
        'company_id': fields.many2one('res.company', 'Empresa'),
    }

    # _sql_constraints = [
    #     ('name', 'unique(name)', 'El pago por mes es único.'),
    #     ]

    _defaults = {
        'state': lambda * a: 'draft',
        'date': lambda * a: time.strftime('%Y-%m-%d'),
        'fijo': lambda * a: False,
        'company_id': lambda s, cr, uid, c: s.pool.get('res.company')._company_default_get(cr, uid, 'hr.expense', context=c),
    }
    def on_change_value(self, cr, uid, ids, fijo, context=None):
        res={'value':{}}
        if fijo:
            res['value'].update({'date':None})
        else:
            res['value'].update({'date':time.strftime('%Y-%m-%d'), 'date_egr_f':None})
        return res

    def onchange_expense_type(self, cr, uid, ids, expense_type_id, context=None):
        res = {}
        if expense_type_id:
            expense_type = self.pool.get('hr.expense.type').browse(cr, uid, expense_type_id, context=None)
            res['value'] = {'rel_name': expense_type.name}
        return res

    def unlink(self, cr, uid, ids, context=None):
        for expense in self.browse(cr, uid, ids, context=None):
            if expense.state != 'draft':
                raise osv.except_osv(('Error !'), ('No se pueden eliminar egresos en estado procesado, egreso:' + expense.expense_type_id.name))
        return super(hr_expense, self).unlink(cr, uid, ids, context=context)

    def print_report(self, cr, uid, ids, context=None):
        data = self.read(cr, uid, ids, context=context)[0]
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'bit_hr_payroll_ec.sancion_report',
            'datas': data,
        }

hr_expense()