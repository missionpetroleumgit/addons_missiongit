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



class report_supplier(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context):
        super(report_supplier, self).__init__(cr, uid, name, context)
        self.localcontext.update({
            'get_retencion': self.get_retencion,
            'get_lines': self.get_lines
        })
    
    def get_retencion(self, f_id):
        print "abc"
        retencion_ids = self.pool.get('account.deduction').search(self.cr, self.uid, [('invoice_id', '=', f_id)])
        print "retencion_ids: ", retencion_ids
        obj_retencion = self.pool.get('account.deduction').browse(self.cr, self.uid, retencion_ids)
        print "obj_retencion.number: ", obj_retencion.number
        return obj_retencion.number or False

    def group_lines(self, line):
        """Merge account lines """
        line2 = {}
        for l in line:
            tmp = l.account_id.id
            if tmp in line2:
                am = line2[tmp]['debit'] - line2[tmp]['credit'] + (l.debit - l.credit)
                line2[tmp]['debit'] = (am > 0) and am or 0.00
                line2[tmp]['credit'] = (am < 0) and -am or 0.00
            else:
                line2[tmp] = {'debit': l.debit, 'credit': l.credit, 'account': l.account_id.name, 'aa_name': l.analytic_account_id.name, 'ref': l.ref, 'code': l.account_id.code}
        res = []
        for key, val in line2.items():
            res.append(val)
        return res

    def get_lines(self, obj):
        res = self.group_lines(obj.move_id.line_id)
        res = self.order_by_debit(res)
        return res

    def order_by_debit(self, array):
        debit_lines = list()
        credit_lines = list()
        for item in array:
            if int(item['debit']) > 0:
                debit_lines.append(item)
            elif int(item['credit']) > 0:
                credit_lines.append(item)
        debit_lines += credit_lines
        return debit_lines
        


class report_asiento_view_supplier(osv.AbstractModel):
    _name = 'report.bit_account_report.report_asiento_view_supplier'
    _inherit = 'report.abstract_report'
    _template = 'bit_account_report.report_asiento_view_supplier'
    _wrapped_report_class = report_supplier


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: