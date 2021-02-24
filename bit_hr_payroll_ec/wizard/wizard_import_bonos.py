# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
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
# import wizard
import base64
import StringIO
from time import strftime
from string import upper, capitalize
from string import join
from openerp.osv import fields, osv
import time

class wizard_import_bonos(osv.osv_memory):
    _name = 'wizard.import.bonos'
    _description = 'Bonos de empleados'
    _columns = {
            'adm_id' : fields.many2one('hr.adm.bono', 'Tipo de Bono'),
            'date': fields.date('Fecha'),
                }
    _defaults = {
       'date': lambda *a: time.strftime('%Y-%m-%d'),
    }


wizard_import_bonos()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
