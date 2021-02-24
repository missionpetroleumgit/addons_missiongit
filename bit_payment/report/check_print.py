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

class report_print_check_supp(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(report_print_check_supp, self).__init__(cr, uid, name, context)
        self.number_lines = 0
        self.number_add = 0
        self.localcontext.update({
            'time': time,
            'get_amount_in_letters': self.get_amount_in_letters,
            'get_format': self.get_format,
        })

    def get_format(self, date):
        def_date = datetime.strptime(date, "%Y-%m-%d")
        return def_date.strftime("%Y / %m / %d")
        
    def get_amount_in_letters(self, amount):
        in_letters = self.pool.get('account.check').get_number_in_letters(amount)
        return in_letters
  
class report_check_supp(osv.AbstractModel):
    _name = 'report.bit_payment.report_check_supp'
    _inherit = 'report.abstract_report'
    _template = 'bit_payment.report_check_supp'
    _wrapped_report_class = report_print_check_supp
    

class report_print_check_egreso(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(report_print_check_egreso, self).__init__(cr, uid, name, context)
        self.number_lines = 0
        self.number_add = 0
        self.localcontext.update({
            'time': time,
            'date_now': datetime.today().strftime('%Y-%m-%d %H:%M:%S'),
            'get_lines': self.get_lines,
            'get_ref': self.get_ref,
            'get_amount': self.get_amount,
            'get_debit': self.get_debit,
            'get_credit': self.get_credit,
            'get_check_number': self.get_check_number,
            'get_amount_in_letters': self.get_amount_in_letters,
        })

    def get_amount_in_letters(self, line_ids):
        amount = self.get_amount(line_ids)
        in_letters = self.pool.get('account.check').get_number_in_letters(amount)
        return in_letters

    def get_check_number(self, statement_id):
        check_ids = self.pool.get('account.check').search(self.cr, self.uid, [('statement_id', '=', statement_id)])
        obj_check = self.pool.get('account.check').browse(self.cr, self.uid, check_ids)
        return obj_check and hasattr(obj_check, 'number') and obj_check.number or False

    def get_ref(self, line_ids):
        ref = ''
        have_name = False
        for l in line_ids:
            if not have_name:
                ref = l.name or ''
                have_name = l.name and True or False
        return ref

    def get_debit(self, move_line_ids):
        deb = 0
        for l in move_line_ids:
            deb += l.debit
        return deb
    
    def get_credit(self, move_line_ids):
        cred = 0
        for l in move_line_ids:
            cred += l.credit
        return cred
    
    def get_amount(self, line_ids):
        amount = 0
        for l in line_ids:
            amount += l.amount
        return abs(amount)

    def get_lines(self, move_lines, is_group):
        result = []
        dicc_acc = {}
        pos = -1
        self.number_lines = len(move_lines)
        if is_group:
            for i in range(0, min(10,self.number_lines)):
                if i < self.number_lines:
                    my_acc = move_lines[i].account_id.id
                    other_ref = move_lines[i].other_ref or ''
                    if not my_acc in dicc_acc.keys():
                        res = {
                            'account_id' : move_lines[i].account_id.code or 'Unknow',
                            'description' : move_lines[i].account_id.name or 'Unknow',
                            'ref' : move_lines[i].ref + ' ' + other_ref,
                            'name' : move_lines[i].name,
                            'debit' : move_lines[i].debit and move_lines[i].debit or 0.00,
                            'credit' : move_lines[i].credit and move_lines[i].credit or 0.00,
                        }
                    else:
                        pos = dicc_acc.get(my_acc)
                        new_deb = move_lines[i].debit and move_lines[i].debit or 0.00
                        new_cred = move_lines[i].credit and move_lines[i].credit or 0.00
                        result[pos]['debit'] += new_deb
                        result[pos]['credit'] += new_cred
                else :
                    res = {
                        'date_due' : False,
                        'name' : False,
                        'debit' : False,
                        'credit' : False,
                    }
                if my_acc not in dicc_acc.keys():
                    result.append(res)
                    pos += 1
                    dicc_acc[my_acc] = pos
        else:
            for i in range(0, min(10,self.number_lines)):
                if i < self.number_lines:
                    my_acc = move_lines[i].account_id.id
                    other_ref = move_lines[i].other_ref or ''
                    res = {
                        'account_id' : move_lines[i].account_id.code or 'Unknow',
                        'description' : move_lines[i].account_id.name or 'Unknow',
                        'ref' : move_lines[i].ref + ' ' + other_ref,
                        'name' : move_lines[i].name,
                        'debit' : move_lines[i].debit and move_lines[i].debit or 0.00,
                        'credit' : move_lines[i].credit and move_lines[i].credit or 0.00,
                    }
                else :
                    res = {
                        'date_due' : False,
                        'name' : False,
                        'debit' : False,
                        'credit' : False,
                    }
                if res:
                    result.append(res)
                    pos += 1
                    dicc_acc[my_acc] = pos
        return result
    
class report_check_egreso(osv.AbstractModel):
    _name = 'report.bit_payment.report_check_egreso'
    _inherit = 'report.abstract_report'
    _template = 'bit_payment.report_check_egreso'
    _wrapped_report_class = report_print_check_egreso

# Formatos cheques Hornero para extractos bancarios

class report_statement_inter_check(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(report_statement_inter_check, self).__init__(cr, uid, name, context)
        self.number_lines = 0
        self.number_add = 0
        self.localcontext.update({
            'time': time,
            'get_amount_in_letters': self.get_amount_in_letters,
            'get_format': self.get_format,
        })

    def get_format(self, date):
        def_date = datetime.strptime(date, "%Y-%m-%d")
        return def_date.strftime("%Y / %m / %d")

    def get_amount_in_letters(self, amount):
        in_letters = self.pool.get('account.check').get_number_in_letters(amount)
        return in_letters

class wrapped_report_statement_inter_check(osv.AbstractModel):
    _name = 'report.bit_payment.report_statement_inter_check'
    _inherit = 'report.abstract_report'
    _template = 'bit_payment.report_statement_inter_check'
    _wrapped_report_class = report_statement_inter_check


class voucher_solidario_check_report(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(voucher_solidario_check_report, self).__init__(cr, uid, name, context)
        self.number_lines = 0
        self.number_add = 0
        self.localcontext.update({
            'time': time,
            'get_amount_in_letters': self.get_amount_in_letters,
            'get_format': self.get_format,
        })

    def get_format(self, date):
        def_date = datetime.strptime(date, "%Y-%m-%d")
        return def_date.strftime("%Y / %m / %d")

    def get_amount_in_letters(self, amount):
        in_letters = self.pool.get('account.check').get_number_in_letters(amount)
        return in_letters

class wrapped_voucher_solidario_check_report(osv.AbstractModel):
    _name = 'report.bit_payment.voucher_solidario_check_report'
    _inherit = 'report.abstract_report'
    _template = 'bit_payment.voucher_solidario_check_report'
    _wrapped_report_class = voucher_solidario_check_report


class statement_solidario_check_report(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(statement_solidario_check_report, self).__init__(cr, uid, name, context)
        self.number_lines = 0
        self.number_add = 0
        self.localcontext.update({
            'time': time,
            'get_amount_in_letters': self.get_amount_in_letters,
            'get_format': self.get_format,
        })

    def get_format(self, date):
        def_date = datetime.strptime(date, "%Y-%m-%d")
        return def_date.strftime("%Y / %m / %d")

    def get_amount_in_letters(self, amount):
        in_letters = self.pool.get('account.check').get_number_in_letters(amount)
        return in_letters

class wrapped_statement_solidario_check_report(osv.AbstractModel):
    _name = 'report.bit_payment.statement_solidario_check_report'
    _inherit = 'report.abstract_report'
    _template = 'bit_payment.statement_solidario_check_report'
    _wrapped_report_class = statement_solidario_check_report


class a_statement_pichincha_check_report(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(a_statement_pichincha_check_report, self).__init__(cr, uid, name, context)
        self.number_lines = 0
        self.number_add = 0
        self.localcontext.update({
            'time': time,
            'get_amount_in_letters': self.get_amount_in_letters,
            'get_format': self.get_format,
        })

    def get_format(self, date):
        def_date = datetime.strptime(date, "%Y-%m-%d")
        return def_date.strftime("%Y / %m / %d")

    def get_amount_in_letters(self, amount):
        in_letters = self.pool.get('account.check').get_number_in_letters(amount)
        return in_letters

class wrapped_a_statement_pichincha_check_report(osv.AbstractModel):
    _name = 'report.bit_payment.a_statement_pichincha_check_report'
    _inherit = 'report.abstract_report'
    _template = 'bit_payment.a_statement_pichincha_check_report'
    _wrapped_report_class = a_statement_pichincha_check_report


class a_voucher_pichincha_check_report(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(a_voucher_pichincha_check_report, self).__init__(cr, uid, name, context)
        self.number_lines = 0
        self.number_add = 0
        self.localcontext.update({
            'time': time,
            'get_amount_in_letters': self.get_amount_in_letters,
            'get_format': self.get_format,
        })

    def get_format(self, date):
        def_date = datetime.strptime(date, "%Y-%m-%d")
        return def_date.strftime("%Y / %m / %d")

    def get_amount_in_letters(self, amount):
        in_letters = self.pool.get('account.check').get_number_in_letters(amount)
        return in_letters

class wrapped_a_voucher_pichincha_check_report(osv.AbstractModel):
    _name = 'report.bit_payment.a_voucher_pichincha_check_report'
    _inherit = 'report.abstract_report'
    _template = 'bit_payment.a_voucher_pichincha_check_report'
    _wrapped_report_class = a_voucher_pichincha_check_report

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
