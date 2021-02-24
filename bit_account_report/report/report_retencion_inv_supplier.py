#-*- coding:utf-8 -*-

##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    d$
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

from openerp.osv import osv
from openerp.report import report_sxw



class report_invoice_supplier(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context):
        super(report_invoice_supplier, self).__init__(cr, uid, name, context)
        self.localcontext.update({
            'get_invoice': self.get_invoice,
            'get_date': self.get_date,
            'get_taxes': self.get_taxes,
        })
    
    
    def get_invoice(self, i_id):
        print "abc"
        inv_ids = self.pool.get('account.deduction').search(self.cr, self.uid, [('invoice_id', '=', i_id),('state','=','paid')])
        if inv_ids:
            inv_id = inv_ids[0]
            obj_retencion = self.pool.get('account.deduction').browse(self.cr, self.uid, inv_id)
            return obj_retencion.invoice_id
        
    def get_date(self, d_id):
        print "abc"
        fecha_ids = self.pool.get('account.deduction').search(self.cr, self.uid, [('invoice_id', '=', d_id)])
        print "fecha_ids: ", fecha_ids
        obj_retencion = self.pool.get('account.deduction').browse(self.cr, self.uid, fecha_ids)
        
        for obj in obj_retencion:
            print "obj_retencion.emission_date: ", obj.emission_date
            
        #return obj_retencion.emission_date or False
    
    def get_taxes(self, t_id):
        print "abc"
        impuesto_ids = self.pool.get('account.deduction').search(self.cr, self.uid, [('invoice_id', '=', t_id)])
        print "impuesto_ids: ", impuesto_ids
        obj_retencion = self.pool.get('account.deduction').browse(self.cr, self.uid, impuesto_ids)
        print "obj_retencion.tax_ids: ", obj_retencion.tax_ids
        return obj_retencion.tax_ids or False
    
class report_asiento_view_supplier(osv.AbstractModel):
    _name = 'report.bit_account_report.report_retencion_inv_supplier'
    _inherit = 'report.abstract_report'
    _template = 'bit_account_report.report_retencion_inv_supplier'
    _wrapped_report_class = report_invoice_supplier


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: