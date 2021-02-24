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

import itertools
from lxml import etree

from openerp import models, fields, api, _
from openerp.osv import fields, osv
from openerp.exceptions import except_orm, Warning, RedirectWarning
from openerp.tools import float_compare
import openerp.addons.decimal_precision as dp

import openerp.addons.decimal_precision as dp
from datetime import datetime, date, time, timedelta
import calendar

#----------------------------------------------------------
#    Inherit - Invoice line
#----------------------------------------------------------
class account_invoice_line(osv.osv):
    _inherit = 'account.invoice.line'
    _description = 'Invoice lines'
    
    _columns = {
    
        # 'liq_line_id': fields.many2one('account.invoice.liquidation', 'Purchase liquidation'),
        'discount_third': fields.boolean('Apl. Desto.')

    }
    
account_invoice_line()

#----------------------------------------------------------
#    Inherit - Invoice
#----------------------------------------------------------
# class account_invoice(osv.osv):
#     _inherit = 'account.invoice'
#     _description = 'Invoice'
#
#     _columns = {
#
#         'liquidation_id': fields.many2one('account.invoice.liquidation', 'Purchase liquidation'),
#
#     }
#
# account_invoice()
#
# #----------------------------------------------------------
# #    Purchase liquidation
# #----------------------------------------------------------
# class account_purchase_liquidation(osv.osv):
#     _name = 'account.invoice.liquidation'
#     _description = 'Purchase liquidation'
#
#     _columns = {
#
#         'invoice_ids': fields.one2many('account.invoice', 'liquidation_id', 'Invoices'),
#         'line_ids': fields.one2many('account.invoice.line', 'liq_line_id', 'Invoices'),
#
#     }
#
#     def default_get(self, cr, uid, fields, context=None):
#         if context is None:
#             context = {}
#         res = super(account_purchase_liquidation, self).default_get(cr, uid, fields, context=context)
#         tax_line = line = inv = []
#         l_tax = [4, 7]
#
#         temp_line = {
#                         'uos_id': 1,
#                         'product_id': 2, 		# OK - line
#                         'price_unit': 100, 		# OK - line
#                         'analytics_id': False,
#                         'account_id': 19, 		# OK - line	(Product)
#                         'name': 'P',
#                         'discount': 0,
#                         'invoice_line_tax_id': [[6, False, l_tax]], 	# OK - line
#                         'tax_support': 1, 		# OK - line
#                         'quantity': 1			# OK - line
#                     }
#         line.append((0, 0, temp_line))
#
#         temp_inv = {
#             'date_due': '2015-09-06',	# OK - line
#             'company_id': 1,
#             'currency_id': 1,
#             'account_id': 13, 			# OK - line
#             'fiscal_position': False,
#             'user_id': 1,
#             'partner_id': 6, 			# OK - line	(Partner)
#             'journal_id': 1, 			# OK - head
#             'invoice_line': [[0, False, line]],
#             'authorization_id': 2, 		# OK - head
#             'date_invoice': False, 		# OK - head
#             'period_id': False,			# OK - head
#             'document_type': 1, 		# OK - head
#             'name': 'Chapulin',			# OK - head
#             'state': 'draft'			# OK - head
#         }
#         inv.append((0, 0, temp_inv))
#
#         res['invoice_ids']  = inv
#         print res
#         return res
#
# #    def create(self, cr, uid, vals, context=None):
# #        print vals
# #        return super(account_invoice, self).create(cr, uid, vals, context=context)
#
# account_purchase_liquidation()
        
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
