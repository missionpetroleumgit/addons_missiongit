__author__ = 'guillermo'
from openerp.report import report_sxw
from openerp.osv import osv
from datetime import date

class decimo_report_parser(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context):
        super(decimo_report_parser, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'create_report': self.create_report,
        })

    def create_report(self, data):
        res = []
        date_from = data['date_from']
        date_to = data['date_to']
        type = data['type']

        remuneration_pool = self.pool.get('hr.remuneration.employee')

        decimo_ids = remuneration_pool.search(self.cr, self.uid, [('periodo_inicio', '>=', date_from),
                                                                                          ('periodo_final', '<=', date_to),
                                                                                          ('decimo_type', '=', type)])
        for decimo in remuneration_pool.browse(self.cr, self.uid, decimo_ids, context=None):
            values = {
                'cedula': decimo.employee_id.identification_id,
                'employee_name': decimo.employee_id.name,
                'decimo_type': decimo.decimo_type,
                'periodo_inicio': decimo.periodo_inicio,
                'periodo_final': decimo.periodo_final,
                'worked_time': decimo.worked_time,
                'pay_amount': decimo.pay_amount,
                'forma_pago': decimo.forma_pago
            }
            res.append(values)
        return res


class decimo_report(osv.AbstractModel):
    _name = 'report.bit_hr_payroll_ec.decimo_report'
    _inherit = 'report.abstract_report'
    _template = 'bit_hr_payroll_ec.decimo_report'
    _wrapped_report_class = decimo_report_parser
