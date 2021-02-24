# -*- encoding: utf-8 -*-
##############################################################################
#
#    Author :  Guillermo Herrera Banda guillermo.herrera@bitconsultores-ec.com
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
    'name': 'Centro de Costos - Contratos',
    'version': '1.0',
    'summary': 'Añade centro de costos a los contratos',
    'description': """
    """,
    'author': 'Guillermo Herrera Banda',
    'website': '',
    'category': 'Human Resources',
    'depends': ['hr_contract','bit_hr_payroll_ec'],
    'init_xml': [],
    'update_xml': [
            'views/hr_contract.xml',
            'views/hr_income.xml',
            'wizard/wizard_import_horas.xml',
            'report/hr_payslip_cc_analysis_view.xml',
            'menu.xml',
    ],
    'installable': True,
    'auto_install': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
