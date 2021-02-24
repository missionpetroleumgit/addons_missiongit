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
import code

from datetime import datetime, date, time, timedelta
import calendar

class report_print_retention_lpair(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(report_print_retention_lpair, self).__init__(cr, uid, name, context)
        self.number_lines = 0
        self.number_add = 0
        self.localcontext.update({
            'time': time,
            'get_amount_in_letters': self.get_amount_in_letters,
            'get_taxes': self.get_taxes,
        })
        
    def get_amount_in_letters(self, amount):
        in_letters = self.pool.get('account.check').get_number_in_letters(amount)
        return in_letters
    
    def get_taxes(self, t_id):
        print "ID******************************", t_id
        impuesto_ids = self.pool.get('account.deduction').search(self.cr, self.uid, [('id', '=', t_id)])
        print "impuesto_ids: ", impuesto_ids
        obj_retencion = self.pool.get('account.deduction').browse(self.cr, self.uid, impuesto_ids)
        print "obj_retencion.tax_ids: ", obj_retencion.tax_ids
        return obj_retencion.tax_ids or False
    
    
class report_retencion_view_lpair(osv.AbstractModel):
    _name = 'report.bit_account_report.report_retencion_view_lpair'
    _inherit = 'report.abstract_report'
    _template = 'bit_account_report.report_retencion_view_lpair'
    _wrapped_report_class = report_print_retention_lpair
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
