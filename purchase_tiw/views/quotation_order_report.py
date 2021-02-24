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


class report_quotation_purchase_wrapped(report_sxw.rml_parse):
    _name = 'report.print.egreso.cheque.wrapped'

    def __init__(self, cr, uid, name, context):
        super(report_quotation_purchase_wrapped, self).__init__(cr, uid, name, context)
        self.number_lines = 0
        self.number_add = 0
        self.localcontext.update({
            'time': time,
            'date_now': datetime.today().strftime('%Y-%m-%d %H:%M:%S'),
            'get_debit': self.get_debit,
            'get_amount_in_letters': self.get_amount_in_letters,
            'get_format': self.get_format,
            'count_importation_items': self.count_importation_items,
        })

    def count_importation_items(self, cr, uid, product_qty):
        count_item = len(product_qty)
        if product_qty:
            count_item += 1
        return count_item

    def get_format(self, date):
        def_date = datetime.strptime(date, "%Y-%m-%d")
        return def_date.strftime("%Y / %m / %d")

    def get_amount_in_letters(self, amount):
        in_letters = self.pool.get('account.check').get_number_in_letters(amount)
        return in_letters

    def get_debit(self, move_line_ids):
        deb = 0
        for l in move_line_ids:
            deb += l.debit
        # locale.setlocale(locale.LC_NUMERIC, "es_EC.utf-8")
        # deb = locale.format("%.*f", (2, deb), True, True)
        return deb

    def get_total(self, order_line):
        total = 0
        for t in order_line:
            total += t.price_subtotal
        return total

    def get_quotes_lines(self, o):
        q_lines = []
        for quote in o.quotes_ids:
            if quote.state == 'done':
                for line in quote.quote_lines:
                    if line.state == 'done':
                        q_lines.append({'cantidad': line.product_qty,
                                        'descripcion': line.name,
                                        'unidad_medida': line.product_uom.name,
                                        'precio_unitario': line.price_unit,
                                        'subtotal': line.price_subtotal,
                                        'descuento': line.discount,
                                        'total': quote.amount_total,
                                        'proveedor': quote.patner_id.name,
                                        })
        return q_lines


class report_quotation(osv.AbstractModel):
    _name = 'report.bit_product_tiw.report_quotation_order_inherit'
    _inherit = 'report.abstract_report'
    _template = 'bit_product_tiw.report_quotation_order_inherit'
    _wrapped_report_class = report_quotation_purchase_wrapped

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
