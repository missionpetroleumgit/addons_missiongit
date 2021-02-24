# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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

from openerp.osv import osv
from openerp.report import report_sxw

from datetime import datetime, date, time, timedelta
import calendar

class report_print_bco_pacif_cheq(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(report_print_bco_pacif_cheq, self).__init__(cr, uid, name, context)
        self.number_lines = 0
        self.number_add = 0
        self.localcontext.update({
            'time': time,
            'get_amount_in_letters': self.get_amount_in_letters,
            'get_format': self.get_format,
	    'format': self.comma_me,
        })

    def get_format(self, date):
        def_date = datetime.strptime(date, "%Y-%m-%d")
        return def_date.strftime("%Y / %m / %d")
        
    def get_amount_in_letters(self, amount):
        in_letters = self.pool.get('account.check').get_number_in_letters(amount)
        return in_letters

    def comma_me(self,amount):
        if not amount:
            amount = 0.0
        if type(amount) is float:
            amount = str('%.2f'%amount)
        else :
            amount = str('%.2f'%amount)
        if (amount == '0'):
            return ' '
        orig = amount
        new = re.sub("^(-?\d+)(\d{3})", "\g<1>,\g<2>", amount)
        if orig == new:
            return new
        else:
            return self.comma_me(new)

  
class report_check_bco_pacifico(osv.AbstractModel):
    _name = 'report.bit_payment.report_check_bco_pacifico'
    _inherit = 'report.abstract_report'
    _template = 'bit_payment.report_check_bco_pacifico'
    _wrapped_report_class = report_print_bco_pacif_cheq
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
