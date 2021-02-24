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
        })
        
    def get_amount_in_letters(self, amount):
        in_letters = self.pool.get('account.check').get_number_in_letters(amount)
        return in_letters

class report_print_check(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(report_print_check, self).__init__(cr, uid, name, context)
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
	    'get_format': self.get_format,
        })
        
    def get_amount_in_letters(self, amount):
        in_letters = self.pool.get('account.check').get_number_in_letters(amount)
        return in_letters

    def get_check_number(self, statement_id):
        check_ids = self.pool.get('account.check').search(self.cr, self.uid, [('statement_id', '=', statement_id)])
        obj_check = self.pool.get('account.check').browse(self.cr, self.uid, check_ids)
        return obj_check and hasattr(obj_check, 'number') and obj_check.number or False

    def get_ref(self, line_ids):
        ref = ''
        is_first = True
        for l in line_ids:
            ref = is_first and l.ref or ref
            last_ref = l.ref
            if last_ref != ref:
                ref = 'Existen múltiples referencias'
            is_first = False
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

    def get_lines(self, move_lines):
        result = []
        dicc_acc = {}
        pos = -1
        self.number_lines = len(move_lines)
        for i in range(0, min(self.number_lines , self.number_lines)):
            if i < self.number_lines:
                my_acc = move_lines[i].account_id.id
                if not my_acc in dicc_acc.keys():
                    res = {
                        'account_id' : move_lines[i].account_id.code or 'Unknow',
                        'description' : move_lines[i].account_id.name or 'Unknow',
                        'ref' : move_lines[i].ref,
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
        return result

    def get_format(self, date):
        def_date = datetime.strptime(date, "%Y-%m-%d")
        return def_date.strftime("%Y / %m / %d")

class report_print_invoice_statement(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(report_print_invoice_statement, self).__init__(cr, uid, name, context)
        self.number_lines = 0
        self.number_add = 0
        self.localcontext.update({
            'time': time,
            'date_now': datetime.today().strftime('%Y-%m-%d %H:%M:%S'),
            'get_lines': self.get_lines,
            'get_debit': self.get_debit,
            'get_credit': self.get_credit,
            'get_amount_in_letters': self.get_amount_in_letters,
        })
        
    def get_amount_in_letters(self, amount):
        in_letters = self.pool.get('account.check').get_number_in_letters(amount)
        return in_letters

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
    
    def get_lines(self, move_lines):
        result = []
        dicc_acc = {}
        pos = -1
        self.number_lines = len(move_lines)
        for i in range(0, min(10,self.number_lines)):
            if i < self.number_lines:
                my_acc = move_lines[i].account_id.id
                if not my_acc in dicc_acc.keys():
                    res = {
                        'account_id' : move_lines[i].account_id.code or 'Unknow',
                        'description' : move_lines[i].account_id.name or 'Unknow',
                        'ref' : move_lines[i].ref,
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
        return result

class report_print_retencion_view(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(report_print_retencion_view, self).__init__(cr, uid, name, context)
        self.number_lines = 0
        self.number_add = 0
        self.localcontext.update({
            'time': time,
            'get_amount_in_letters': self.get_amount_in_letters,
        })
        
    def get_amount_in_letters(self, amount):
        in_letters = self.pool.get('account.check').get_number_in_letters(amount)
        return in_letters
    
    

class report_print_egreso_check(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(report_print_egreso_check, self).__init__(cr, uid, name, context)
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
        is_first = True
        for l in line_ids:
            ref = is_first and l.ref or ref
            last_ref = l.ref
            if last_ref != ref:
                ref = 'Existen múltiples referencias'
            is_first = False
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

    def get_lines(self, move_lines):
        result = list()
        result_debit = list()
        result_credit = list()
        # dicc_acc = {}
        # pos = -1
        for line in move_lines:
            if line.debit:
                res = {
                    'account_id': line.account_id.code or 'Unknow',
                    'description': line.account_id.name or 'Unknow',
                    'ref': line.ref,
                    'name': line.name,
                    'debit': line.debit and line.debit or 0.00,
                    'credit': 0.00,
                }
                result_debit.append(res)
            else:
                res = {
                    'account_id': line.account_id.code or 'Unknow',
                    'description': line.account_id.name or 'Unknow',
                    'ref': line.ref,
                    'name': line.name,
                    'debit': 0.00,
                    'credit': line.credit and line.credit or 0.00,
                }
                result_credit.append(res)
        result = result_debit + result_credit
        # self.number_lines = len(move_lines)
        # for i in range(0, self.number_lines):
        #     if i < self.number_lines:
        #         my_acc = move_lines[i].account_id.id
        #         if not my_acc in dicc_acc.keys():
        #             res = {
        #                 'account_id' : move_lines[i].account_id.code or 'Unknow',
        #                 'description' : move_lines[i].account_id.name or 'Unknow',
        #                 'ref' : move_lines[i].ref,
        #                 'name' : move_lines[i].name,
        #                 'debit' : move_lines[i].debit and move_lines[i].debit or 0.00,
        #                 'credit' : move_lines[i].credit and move_lines[i].credit or 0.00,
        #             }
        #         else:
        #             pos = dicc_acc.get(my_acc)
        #             new_deb = move_lines[i].debit and move_lines[i].debit or 0.00
        #             new_cred = move_lines[i].credit and move_lines[i].credit or 0.00
        #             result[pos]['debit'] += new_deb
        #             result[pos]['credit'] += new_cred
        #     else :
        #         res = {
        #             'date_due' : False,
        #             'name' : False,
        #             'debit' : False,
        #             'credit' : False,
        #         }
        return result


class report_check(osv.AbstractModel):
    _name = 'report.bit_account.report_check'
    _inherit = 'report.abstract_report'
    _template = 'bit_account.report_check'
    _wrapped_report_class = report_print_check
    
class report_retencion_view(osv.AbstractModel):
    _name = 'report.bit_account.report_retencion_view'
    _inherit = 'report.abstract_report'
    _template = 'bit_account.report_retencion_view'
    _wrapped_report_class = report_print_retencion_view
    
class report_egreso_check(osv.AbstractModel):
    _name = 'report.bit_account.report_egreso_check'
    _inherit = 'report.abstract_report'
    _template = 'bit_account.report_egreso_check'
    _wrapped_report_class = report_print_egreso_check

class report_check_supp(osv.AbstractModel):
    _name = 'report.bit_account.report_check_supp'
    _inherit = 'report.abstract_report'
    _template = 'bit_account.report_check_supp'
    _wrapped_report_class = report_print_check_supp
    
class report_account_statement(osv.AbstractModel):
    _name = 'report.bit_account.report_account_statement'
    _inherit = 'report.abstract_report'
    _template = 'bit_account.report_account_statement'
    _wrapped_report_class = report_print_invoice_statement

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
