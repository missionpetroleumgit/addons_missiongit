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


class payslip_report_liquidation(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context):
        self.total_d3 = 0.00
        self.total_d4 = 0.00
        self.total_vac = 0.00
        super(payslip_report_liquidation, self).__init__(cr, uid, name, context)
        self.localcontext.update({
            'get_payslip_lines': self.get_payslip_lines,
            'get_third_detail': self._get_third_detail,
            'get_vacation_detail': self._get_vacation_detail,
            'get_total': self._get_total,
            'get_proy': self._get_proy,
            'get_four_detail': self._get_four_detail,
            'return_totals': self.return_totals
        })
    total_d4 = 0.00
    total_d3 = 0.00
    total_vac = 0.00

    def _get_proy(self, obj):
        proy = str()
        count = len(obj.contract_id.contract_analytic_ids)
        for line in obj.contract_id.contract_analytic_ids:
            proy += line.account_analytic_id.name
            if count > 1:
                proy += ','
            count -= 1
        return proy

    def _get_total(self, obj):
        total = 0.00
        for line in obj.details_by_salary_rule_category:
            if line.category_id.code in ['IGBS', 'OINGNBS', 'PRO']:
                total += line.total
            elif line.category_id.code == 'EGRE':
                total -= line.total
        return total

    def get_payslip_lines(self, obj):
        payslip_line = self.pool.get('hr.payslip.line')
        res = []
        ids = []
        for id in range(len(obj)):
            if obj[id].appears_on_payslip is True:
                ids.append(obj[id].id)
        if ids:
            res = payslip_line.browse(self.cr, self.uid, ids)
        return res

    def _get_third_detail(self, obj):
        vals = []
        detail_pool = self.pool.get('detail.liquidation.history')
        details = detail_pool.search(self.cr, self.uid, [('employee_id', '=', obj.employee_id.id), ('role_id', '=', obj.payslip_run_id.id),
                                                         ('name', '=', 'D3')], order='date_from')
        for det in detail_pool.browse(self.cr, self.uid, details):
            vals.append({'date_from': det.date_from, 'date_to': det.date_to, 'amount': det.amount, 'total_amount': det.amount * 12.00})
            self.total_d3 += det.amount
        payslip_pool = self.pool.get('hr.payslip.line')
        payslip_line_ids = payslip_pool.search(self.cr, self.uid, [('slip_id.employee_id', '=', obj.employee_id.id), ('slip_id.payslip_run_id', '=', obj.payslip_run_id.id),
                                                                   ('code', '=', 'INGD3LIQ')])
        if payslip_line_ids:
            payslip_line_ids = payslip_line_ids[0]
            payslip_line = payslip_pool.browse(self.cr, self.uid, payslip_line_ids)
            vals.append({'date_from': payslip_line.slip_id.date_from, 'date_to': payslip_line.slip_id.date_to, 'amount': payslip_line.amount, 'total_amount': payslip_line.amount * 12.00})
            self.total_d3 += payslip_line.amount
        return vals

    def _get_four_detail(self, obj):
        vals = []
        detail_pool = self.pool.get('detail.liquidation.history')
        details = detail_pool.search(self.cr, self.uid, [('employee_id', '=', obj.employee_id.id), ('role_id', '=', obj.payslip_run_id.id),
                                                         ('name', '=', 'D4')], order='date_from')
        for det in detail_pool.browse(self.cr, self.uid, details):
            vals.append({'date_from': det.date_from, 'date_to': det.date_to, 'amount': det.amount, 'total_amount': round((det.employee_id.company_id.base_amount * det.employee_id.contract_id.horas_x_dia) / 8.00, 2)})
            self.total_d4 += det.amount
        payslip_pool = self.pool.get('hr.payslip.line')
        payslip_line_ids = payslip_pool.search(self.cr, self.uid, [('slip_id.employee_id', '=', obj.employee_id.id), ('slip_id.payslip_run_id', '=', obj.payslip_run_id.id),
                                                                   ('code', '=', 'INGD4LIQ')])
        if payslip_line_ids:
            payslip_line_ids = payslip_line_ids[0]
            payslip_line = payslip_pool.browse(self.cr, self.uid, payslip_line_ids)
            vals.append({'date_from': payslip_line.slip_id.date_from, 'date_to': payslip_line.slip_id.date_to, 'amount': payslip_line.amount, 'total_amount': round((det.employee_id.company_id.base_amount * det.employee_id.contract_id.horas_x_dia) / 8.00, 2)})
            self.total_d4 += payslip_line.amount
        return vals

    def _get_vacation_detail(self, obj):
        vals = []
        detail_pool = self.pool.get('detail.liquidation.history')
        if obj.employee_id.pending_payment > 0.00:
            vals.append({'date_from': 'Pend. ult. vac.', 'date_to': '', 'amount': round(obj.employee_id.pending_payment, 2), 'total_amount': round(obj.employee_id.pending_payment * 24.00, 2)})
            self.total_vac += round(obj.employee_id.pending_payment, 2)
        details = detail_pool.search(self.cr, self.uid, [('employee_id', '=', obj.employee_id.id), ('role_id', '=', obj.payslip_run_id.id),
                                                         ('name', '=', 'PROVAC')], order='date_from')
        for det in detail_pool.browse(self.cr, self.uid, details):
            vals.append({'date_from': det.date_from, 'date_to': det.date_to, 'amount': det.amount, 'total_amount': det.amount * 24.00})
            self.total_vac += det.amount
        payslip_pool = self.pool.get('hr.payslip.line')
        payslip_line_ids = payslip_pool.search(self.cr, self.uid, [('slip_id.employee_id', '=', obj.employee_id.id), ('slip_id.payslip_run_id', '=', obj.payslip_run_id.id),
                                                                   ('code', '=', 'PROVAC')])
        if payslip_line_ids:
            payslip_line_ids = payslip_line_ids[0]
            payslip_line = payslip_pool.browse(self.cr, self.uid, payslip_line_ids)
            vals.append({'date_from': payslip_line.slip_id.date_from, 'date_to': payslip_line.slip_id.date_to, 'amount': payslip_line.amount, 'total_amount': payslip_line.amount * 24})
            self.total_vac += payslip_line.amount
        return vals

    def return_totals(self):
        return [self.total_d3, self.total_d4, self.total_vac]


class wrapped_report_payslip_liquidation(osv.AbstractModel):
    _name = 'report.bit_hr_payroll_ec.report_payslip_liquidation'
    _inherit = 'report.abstract_report'
    _template = 'bit_hr_payroll_ec.report_payslip_liquidation'
    _wrapped_report_class = payslip_report_liquidation

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
