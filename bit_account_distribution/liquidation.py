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

from openerp import models, fields, api, _
from openerp.osv import fields, osv

#----------------------------------------------------------
#    Purchase liquidation
#----------------------------------------------------------
class account_purchase_liquidation(osv.osv):
    _name = 'account.liquidation'
    _description = 'Purchase liquidation'
    
    _columns = {
    
        'name': fields.char('Name', size=128),
        'journal_id': fields.many2one('account.journal', 'Journal'),
    # Invoices lines
        'line_ids': fields.one2many('account.liquidation.line', 'liquidation_id', 'Invoices'),

    }
    
account_purchase_liquidation()

#----------------------------------------------------------
#    Purchase liquidation line
#----------------------------------------------------------
class account_liquidation_line(osv.osv):
    _name = 'account.liquidation.line'
    _description = 'Purchase liquidation lines'
    
    _columns = {
    
        'liquidation_id': fields.many2one('account.liquidation', 'Purchase liquidation'),
        'acc_partner_id': fields.many2one('account.account', 'Partner account'),
        'partner_id': fields.many2one('res.partner', 'Partner'),
        'acc_product_id': fields.many2one('account.account', 'Product account'),
        'product_id': fields.many2one('product.product', 'Product'),
        
        'price_unit': fields.float('Price unit'),
        'quantity': fields.float('Quantity'),
        'name': fields.text('Description'),

    }
    
account_liquidation_line()


