# -*- encoding: utf-8 -*-
##############################################################################
#
#    Author :  Guillermo Herrera Banda: guillermo.herrera@bitconsultores-ec.com
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

from openerp.osv import fields, osv
from openerp import api
from datetime import date, datetime
import time


class hr_business_unit(osv.osv):
    _description = "Unidad de Negocio"
    _name = 'hr.business.unit'
    _columns = {
        'name': fields.char('Nombre', size=64),
        'codigo': fields.char('Codigo', size=64),
        'department_id': fields.many2one('hr.department', string="Departamento"),
    }
hr_business_unit()


class hr_employee(osv.osv):
    _inherit = 'hr.employee'
    _description = 'Employee'

    _columns = {
        'business_unit_id': fields.many2one('hr.business.unit', 'Unidad de Negocio'),
        #'work_area_id': fields.many2one('hr.employee.work.area', 'Area'),
        'is_foreign': fields.boolean('Es extranjero'),
        'foreign_code': fields.char('Codigo Extranjero', size=32),
        'job_center': fields.char('Centro de Trabajo', size=124),
    }

hr_employee()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: