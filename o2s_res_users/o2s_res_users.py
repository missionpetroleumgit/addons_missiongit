# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
#    Copyright (C) 2010-2014 OpenERP s.a. (<http://openerp.com>).
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

from openerp.osv import fields, osv

class res_users(osv.osv):
    _name = "res.users"
    _inherit = "res.users"
    _description = 'Users'
    
    
    _columns = {
            'partner_id': fields.many2one('res.partner', required=False, ondelete='restrict')
                }
            
#     def create(self, cr, uid, vals, context=None):
#         user_id = super(res_users, self).create(cr, uid, vals, context=context)
#         user = self.browse(cr, uid, user_id, context=context)
#         #if user.partner_id.company_id: 
#         #    user.partner_id.write({'company_id': user.company_id.id})
#         return user_id