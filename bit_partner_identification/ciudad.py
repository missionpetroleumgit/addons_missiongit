# -*- encoding: utf-8 -*-
##############################################################################
#
#    Author :  Guillermo Herrera Banda hguille25@yahoo.com
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

class gen_country_city(osv.osv):
    _description="Country City"
    _name = 'gen.country.city'
    _columns = {
        'name': fields.char('Ciudad', size=64, required=True),
        'country_state_id': fields.many2one('res.country.state', 'Country State',required=True),
    }
gen_country_city()

class res_partner(osv.osv):
    _name = 'res.partner'
    _inherit = 'res.partner'
    _columns = {
        'ciudad_id': fields.many2one('gen.country.city', 'Ciudad', domain="[('country_state_id','=',state_id)]"),
      }
res_partner()