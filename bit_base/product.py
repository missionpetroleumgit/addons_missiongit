# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution - Ecuador
#    Copyright (C) 2014 BitConsultores (<http://http://bitconsultores-ec.com>).
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

from openerp.tools.translate import _
from openerp.osv import fields, osv


class bit_product(osv.osv):
    
    _inherit = 'product.product'
    _description = 'Products'
    _columns = {
                
    }
    
# NAME GET
#    def name_get(self, cr, uid, ids, context=None):
#        res = super(bit_product, self).name_get(cr, uid, ids, context)
#        reads = self.read(cr, uid, ids, ['name','attribute_value_ids'], context=context)
#        for record in reads:
#            name = record['name']
#            if record['attribute_value_ids']:
#                att = ''
#                for r in record['attribute_value_ids']:
#                    att += str(r)
#                name = att+' - '+name
#            res.append((record['id'], name))
#        res = [(4, u'MOTHER FUCKER')]
#        return res

bit_product()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
