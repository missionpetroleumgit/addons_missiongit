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

class hr_adm_bono(osv.osv):
    _name = 'hr.adm.bono'
    _description = "Administracion de Bonos"

    
    _columns = {
            'name' : fields.char('Descripcion', size=64,required=True),
            'code' : fields.char('Codigo', size=64, required=True),
            'default_value': fields.float('Valor Por Defecto', digits=(8, 2)),
    }
    _defaults = {
                 'default_value' : lambda * a : 0.0,
    }
    _sql_constraints = [
            ('unique_code', 'unique(code)', 'El codigo debe ser unico')
            ]

hr_adm_bono()

class hr_bono(osv.osv):
    _name = "hr.bono"
    _description = "clase bonos"

    _columns = {
        #        'payroll_id': fields.many2one('hr.payroll', 'Rol de Pagos'),
        #  'contract_id': fields.many2one('hr.contract', 'Contrato'),
        'name': fields.char('Description', size=50),
        'adm_id': fields.many2one('hr.adm.bono', 'Tipo de Bono'),
        #        'value': fields.float('Valor', digits=(16, int(config['price_accuracy']))),
        'value': fields.float('Valor', digits=(12, 2)),
        'state': fields.selection([('draft', 'No Procesado'), ('procesado', 'Procesado'), ('no_usado', 'No Usado')], 'Status', readonly=True),
        'date': fields.datetime('Fecha de Registro'),
        'company_id': fields.many2one('res.company', 'Empresa'),
    }

    _sql_constraints = [
        ('name', 'unique(name)', 'Ya se ha cargado la informacion de este rol !.'),
    ]

    _defaults = {
        'state': lambda * a: 'draft',
        'date': lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'),
        'company_id': lambda s, cr, uid, c: s.pool.get('res.company')._company_default_get(cr, uid, 'hr.bono', context=c),
    }
hr_bono()