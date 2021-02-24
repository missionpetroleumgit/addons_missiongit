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


class payslip_report_resumen(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context):
        super(payslip_report_resumen, self).__init__(cr, uid, name, context)
        self.localcontext.update({
            'get_payslip_lines': self.get_payslip_lines,
            'get_horas': self.get_horas,
            'get_analytics': self.get_analytics
        })

    def get_horas(self, slip_id, code):
        horas = 0
        if code in ('INGHXT','INGHNOC','INGHSUP','INGHRF'):
            input_obj = self.pool.get('hr.payslip.input')
            input_ids = input_obj.search(self.cr,self.uid,[('payslip_id','=', slip_id),('code','=', code)])
            for input in input_obj.browse(self.cr, self.uid, input_ids):
                horas += input.horas
        else:
            return ""
        return "  (" + str(horas) + " h)"

#Modificación para HORNERO 19/12/2016 Daniel Aldaz - O2S

    def get_analytics(self, contract):
#        analityc_account = str()
#        for analityc in contract.contract_analytic_ids:
#            analityc_account = analityc.account_analytic_id.name + '-'
#        aux = analityc_account[len(analityc_account)-1:len(analityc_account)]
#        if analityc_account[len(analityc_account)-1:len(analityc_account)] == '-':
#            analityc_account = analityc_account[0:len(analityc_account)-2]
        return True
    
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

    def days_work(self, days):
        retorno = 0.00
        for days_line in days:
            if days_line.code == 'WORK100':
                return days_line.number_of_days
        return retorno

    def days_no_work(self, days):
        retorno = 0.00
        for days_line in days:
            if days_line.code not in ('WORK100','BA'):
                retorno += days_line.number_of_days
        return retorno


class wrapped_report_payslip_resumen(osv.AbstractModel):
    _name = 'report.bit_hr_payroll_ec.report_payslip_resumen'
    _inherit = 'report.abstract_report'
    _template = 'bit_hr_payroll_ec.report_payslip_resumen'
    _wrapped_report_class = payslip_report_resumen

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
