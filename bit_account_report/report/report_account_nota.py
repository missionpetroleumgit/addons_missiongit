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


class report_account_nota(report_sxw.rml_parse):
    
    def __init__(self, cr, uid, name, context):
        super(report_account_nota, self).__init__(cr, uid, name, context)
        self.localcontext.update({
            'get_invoice': self.get_invoice,
        })

    def get_invoice(self, cr, uid, ids, context):
        sum_discount = 0
        for invoice in self.browse(cr, uid, ids, context):
            for line in invoice.invoice_line:
                sum_discount += line.price_subtotal * (line.discount/100 or 1)
        return sum_discount
    
class report_account_nota(osv.AbstractModel):
    _name = 'report.bit_account_report.report_account_nota'
    _inherit = 'report.abstract_report'
    _template = 'bit_account_report.report_account_nota'
    _wrapped_report_class = report_account_nota
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
