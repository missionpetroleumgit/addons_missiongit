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


class report_account_servicio(report_sxw.rml_parse):
    
    def __init__(self, cr, uid, name, context):
        super(report_account_servicio, self).__init__(cr, uid, name, context)
        self.localcontext.update({
            'get_product': self.get_product,
        })
        
# Devuelve el total airport fee con True, Total del otros productos False
    def get_product(self, is_air_fee=True):
        sum_air = 0
        sum_prod = 0
        for prod in self:
            for line in prod.order_line:
                temp_ids = self.env['airport.fee'].search([('product_id', '=', line.product_id.id)])
                if temp_ids:
                    sum_air += line.price_subtotal
                else:
                    sum_prod += line.price_subtotal  
        if is_air_fee:
            return sum_air
        else:
            return sum_prod
    
class report_account_servicio(osv.AbstractModel):
    _name = 'report.bit_account_report.report_account_servicio'
    _inherit = 'report.abstract_report'
    _template = 'bit_account_report.report_account_servicio'
    _wrapped_report_class = report_account_servicio
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: