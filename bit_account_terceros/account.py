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


class account_tax(osv.osv):
    """
    A tax object.

    Type: percent, fixed, none, code
        PERCENT: tax = price * amount
        FIXED: tax = price + amount
        NONE: no tax line
        CODE: execute python code. localcontext = {'price_unit':pu}
            return result in the context
            Ex: result=round(price_unit*0.21,4)
    """
    
    _inherit = 'account.tax'
    _description = 'Tax'
    _columns = {
                
        'name': fields.char('Tax Name', size=255, required=True, translate=True, help="This name will be displayed on reports"),
        'is_iva':fields.boolean('Is the IVA tax ?', help="Only will be used when be the IVA tax."),        

    }
    _order = 'is_iva asc, sequence asc'
    
# NAME GET
    def name_get(self, cr, uid, ids, context=None):
        
        reads = self.read(cr, uid, ids, ['name','description'], context=context)
        res = []
        for record in reads:
            name = record['name']
            if record['description']:
                name = record['description']+' - '+name
            res.append((record['id'], name))
        return res
    
# SEARCH
    def search(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=False):
        if context is None:
            context = {}
        order='sequence'
        if 'type_tax_use' in context:
            args += [('type_tax_use', '=', context.get('type_tax_use')), ('parent_id', '=', False)]
        return super(account_tax, self).search(cr, uid, args, offset=offset, limit=limit, order=order, context=context, count=count)

account_tax()


#----------------------------------------------------------
# Tax Code
#----------------------------------------------------------
"""
a documenter
child_depend: la taxe depend des taxes filles
"""
class account_tax_code(osv.osv):
    """
    A code for the tax object.

    This code is used for some tax declarations.
    """
    
    _inherit = 'account.tax.code'
    _description = 'Tax Code'
    _rec_name = 'code'
    _columns = {
                
        'name': fields.char('Tax Case Name', size=255, required=True, translate=True),
        'form': fields.char('Form', size=4, help="DIMM Form"),
        
    }

account_tax_code()

#----------------------------------------------------------
# Document
#----------------------------------------------------------
class account_invoice_document(osv.osv):
    """
    This document is used in the invoice.
    """
    
    _name = 'account.invoice.document'
    _description = 'Invoice document'
    
    _columns = {
                
        'name': fields.char('Name', size=255, required=True, translate=True),
        'code': fields.char('Code', size=4, help="Document code"),
        'support_ids': fields.many2many('account.tax.support', 'account_document_support_rel',
            'doc_id', 'sup_id', 'Tax supports'),
        'is_retention' : fields.boolean('Is retention ?'),
        
    }
    
# NAME GET
    def name_get(self, cr, uid, ids, context=None):
        
        reads = self.read(cr, uid, ids, ['name','code'], context=context)
        res = []
        for record in reads:
            name = record['code']
            if record['name']:
                name = name+' - '+record['name']
            res.append((record['id'], name))
        return res
    
account_invoice_document()


#----------------------------------------------------------
# Tax support
#----------------------------------------------------------
class account_tax_support(osv.osv):
    """
    This document is used in the invoice.
    """
    
    _name = 'account.tax.support'
    _description = 'Tax support'
    _rec_name = 'code'
    _columns = {
                
        'type': fields.char('Type', size=255, required=True, translate=True),
        'code': fields.char('Code', size=4, help="Tax support code"),
        'document_ids': fields.many2many('account.tax.support', 'account_document_support_rel',
            'sup_id', 'doc_id', 'Invoice document'),
        
    }
    
# NAME GET
    def name_get(self, cr, uid, ids, context=None):
        
        reads = self.read(cr, uid, ids, ['type','code'], context=context)
        res = []
        for record in reads:
            name = record['code']
            if record['type']:
                name = name+' - '+record['type']
            res.append((record['id'], name))
        return res

account_tax_support()


#----------------------------------------------------------
# Partners
#----------------------------------------------------------
class res_partner(osv.osv):
    """
    This document is used in the invoice.
    """
    
    _inherit = 'res.partner'
    _description = 'Partner'
    
    _columns = {
                
        'document_type': fields.many2one('account.invoice.document', 'Invoice document', select=True),
        'tax_support': fields.many2one('account.tax.support', 'Tax support', select=True),
    }

res_partner()

#----------------------------------------------------------
# Bank statement
#----------------------------------------------------------
# class account_bank_statement(osv.osv):
#     """
#     This document is used in the invoice.
#     """
#     
#     _inherit = 'account.bank.statement'
#     _description = 'Bank statement'
#     
#     _columns = {
#                 
#             'pay_mode_id':fields.many2one('payment.mode', 'Payment mode', readonly=True, states={'draft':[('readonly',False)]}),
# 
#     }
#     
#     def onchange_pay_mode(self, cr, uid, ids, pay_mode_id, context):
#         res = {}
#         for obj_payment_mode in self.pool.get('payment.mode').browse(cr, uid, [pay_mode_id], context):
#             journal_id = obj_payment_mode.journal
#             currency_id = journal_id.company_id.currency_id.id
#             if journal_id:
#                 res = { 'value' : { 'journal_id' : journal_id.id } }
#         return res
# 
# account_bank_statement()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
