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
from datetime import datetime, date, time, timedelta


class report_stock_picking_outs_wrapped(report_sxw.rml_parse):
    _name = 'report.stock.picking.outs.wrapped'

    def __init__(self, cr, uid, name, context):
        super(report_stock_picking_outs_wrapped, self).__init__(cr, uid, name, context)
        self.number_lines = 0
        self.number_add = 0
        self.localcontext.update({
            'time': time,
            'date_now': datetime.today().strftime('%Y-%m-%d %H:%M:%S'),
        })


class report_importation(osv.AbstractModel):
    _name = 'report.purchase_adjustment.report_print_picking_out'
    _inherit = 'report.abstract_report'
    _template = 'purchase_adjustment.report_print_picking_out'
    _wrapped_report_class = report_stock_picking_outs_wrapped

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
