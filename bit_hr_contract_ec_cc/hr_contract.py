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
from openerp.exceptions import except_orm, Warning, RedirectWarning

class hr_contract_analytic(osv.osv):
    _name = 'hr.contract.analytic'
    _description = 'Contratos Centro de Costos'

    _columns = {
        'account_analytic_id': fields.many2one('account.analytic.account', "Centro de Costos", required=True),
        'rate': fields.float('%', digits=(6,2), required=True),
        'contract_id': fields.many2one('hr.contract', "Contrato"),
      }
    _defaults = {
        'rate': lambda *a: 100.00,
    }
hr_contract_analytic()


class hr_contract(osv.osv):
    _inherit = 'hr.contract'
    
    def write(self, cr, uid, ids, vals, context=None):
        print "vals: ", vals
        if 'contract_analytic_ids' in vals and vals.get('contract_analytic_ids'):
            suma = 0
            gettin = False
            for acc in vals.get('contract_analytic_ids'):
                if acc[2] and acc[2].get('rate'):
                    suma += acc[2].get('rate')
                    gettin = True
            
            if suma != 100 and gettin:
                raise except_orm(('Error!'), ('La sumatoria de los porcientos debe ser igual a 100.'))
        return super(hr_contract, self).write(cr, uid, ids, vals, context=context)
    
    
    def create(self, cr, uid, vals, context=None):
        print "vals: ", vals
        if 'contract_analytic_ids' in vals and vals.get('contract_analytic_ids'):
            suma = 0
            for acc in vals.get('contract_analytic_ids'):
                if acc[2] and acc[2].get('rate'):
                    suma += acc[2].get('rate')
            
            if suma != 100:
                raise except_orm(('Error!'), ('La sumatoria de los porcientos debe ser igual a 100.'))
        return super(hr_contract, self).create(cr, uid, vals, context=context)

    _columns = {
        'contract_analytic_ids': fields.one2many('hr.contract.analytic', 'contract_id', 'Centro de Costos'),
      }
hr_contract()