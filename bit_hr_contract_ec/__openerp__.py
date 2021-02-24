# -*- encoding: utf-8 -*-
##############################################################################
#
#    Author :  Guillermo Herrera Banda hguille25@yahoo.com
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
    'name': 'Contratos Ecuador',
    'version': '1.0',
    'summary': 'Añade campos al contrato y anade funcionalidad',
    'description': """
    """,
    'author': 'Guillermo Herrera Banda',
    'website': '',
    'category': 'Human Resources',
    'depends': ['hr_contract'],
    'init_xml': [],
    'update_xml': [
            'security/groups.xml',
            'views/hr_contract.xml',
            'views/hr_contract_type.xml',
            'report/hr_contract_report.xml',
            'report/report_contract_view.xml',
            'report/report_contract_s_view.xml',
            'report/report_contract_full_view.xml',
            'report/report_contract_part_view.xml',
            'report/report_contract_full_lpair.xml',
            'report/report_contract_part_lpair.xml',
    ],
    'installable': True,
    'auto_install': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
