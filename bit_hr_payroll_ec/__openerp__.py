# -*- encoding: utf-8 -*-
##############################################################################
#
#    Author :  Open Source Solutions
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    'name': 'Nomina Ecuador',
    'version': '1.0',
    'summary': 'Estructuras y Reglas Salariales Ecuador',
    'description': """
    """,
    'author': 'Open Source Solutions Open2S',
    'website': '',
    'category': 'Human Resources',
    'depends': ['account','hr_payroll','hr_public_holidays','bit_hr_ec'],
#     'init_xml': [
#              'data/data_init.xml',
# #              'data/hr.salary.rule.category.csv',
# #              'data/hr.salary.rule.csv',
#                  ],
    'data': [
        'views/report_payslip_confidential.xml',
    ],
    'update_xml': [
        'views/hr_contract.xml',
        'data/horario_normal.xml',
        'wizard/wizard_employee_liquidation.xml',
        'wizard/wizard_import_ingresos.xml',
        'wizard/wizard_import_egresos.xml',
        'wizard/wizard_import_bonos.xml',
        'wizard/generate_tenth_view.xml',
        'wizard/validate_tenth_view.xml',
        'wizard/decimo_report_wizard.xml',
        'wizard/decimo_report_template.xml',
        'wizard/reintegration_employee.xml',
        'wizard/tenth_file.xml',
        'wizard/exel_utilities.xml',
 #       'wizard/service_percent.xml',
        'views/hr_adm_income.xml',
        'views/hr_expense_type.xml',
        'views/hr_bono.xml',
        'views/hr_payroll.xml',
        'views/report_payslip_resume.xml',
        'report/hr_extra_hours_analysis_view.xml',
        'report/hr_payslip_analysis_view.xml',
        'report/hr_payslip_last_analysis_view.xml',
        'report/hr_payslip_last_analysis_categ_view.xml',
        'report/hr_payslip_last_analysis_provi_view.xml',
        'report/hr_payslip_department_analysis_view.xml',
        'report/hr_payslip_file_bank_view.xml',
        'report/hr_payroll_report.xml',
        'report/report_payslip_resumen.xml',
        'report/report_payslip_resumen_slogo.xml',
        'report/hr_payslip_last_quin_analysis_view.xml',
        'report/hr_payslip_variation_hours_view.xml',
        'report/hr_payslip_rol_resumido_view.xml',
        'report/hr_payslip_sal_ingresos_view.xml',
        'views/hr_employee_acumulados.xml',
        'views/hr_remuneration_view.xml',
        'views/fiscalyear_period_view.xml',
        'report/report_payslip_liquidation.xml',
        'report/hr_expense_sancion_template.xml',

        'menu.xml',
    ],
    'installable': True,
    'auto_install': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
