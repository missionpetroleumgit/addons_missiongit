__author__ = 'guillermo'

from openerp.report import report_sxw
from openerp.osv import osv
from datetime import date

class common_sancion_report(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context):
        super(common_sancion_report, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'create_report': self._create_report,
        })

    def _create_report(self, data):
        res = []
        dict_values = {}
        # sancion = self.pool.get()
        employee_id = data.get('employee_id')[0]
        employee_name = data.get('employee_id')[1]
        amount = data.get('value')
        cost_center = []
        type = data.get('expense_type_id')[1]
        use_percent = data.get('reg_porcentaje')
        if use_percent:
            percent = data.get('porcentaje')
        employee = self.pool.get('hr.employee').browse(self.cr, self.uid, employee_id)
        dict_values.update({'cedula': employee.identification_id})
        dict_values.update({'provincia': employee.provincia_id.name})
        dict_values.update({'pais': employee.country_id.name})
        dict_values.update({'nacionalidad': employee.country_id.name})
        contract_id = self.pool.get('hr.contract').search(self.cr, self.uid, [('employee_id', '=', employee_id)])[0]
        contract = self.pool.get('hr.contract').browse(self.cr, self.uid, contract_id)
        center = ''
        for analytic in contract.contract_analytic_ids:
            center = analytic.account_analytic_id.name
            break
            # cost_center.append(str(analytic.account_analytic_id.name))
        dict_values.update({'centros': center})
        dict_values.update({'contract_type': contract.type_id.name})
        dict_values.update({'puesto': contract.job_id.name})
        dict_values.update({'fecha_contrato': contract.date_start})
        # wage = str(contract.wage) + '' + contract.schedule_pay
        wage = contract.wage
        if not use_percent:
            percent = amount*100/wage
        dict_values.update({'percent': percent})
        dict_values.update({'value': amount})
        dict_values.update({'wage': wage})
        dict_values.update({'comment': data.get('comment')})
        dict_values.update({'today': date.today()})
        res.append(dict_values)
        return res


class sancion_report(osv.AbstractModel):
    _name = 'report.bit_hr_payroll_ec.sancion_report'
    _inherit = 'report.abstract_report'
    _template = 'bit_hr_payroll_ec.sancion_report'
    _wrapped_report_class = common_sancion_report

