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

class res_partner_bank(osv.osv):
    _inherit = 'res.partner.bank'

    _columns = {
        'employee_id': fields.many2one('hr.employee', 'Empleado', ondelete='cascade', select=True),
        'state': fields.selection([('bank', 'Cuenta de Banco'), ('CTE', 'Cuenta Corriente'), ('AHO', 'Cuenta de Ahorro')], 'Tipo de Cuenta Bancaria', required=True)
      }
    
res_partner_bank()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: