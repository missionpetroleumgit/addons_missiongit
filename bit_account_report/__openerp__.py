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
    'name': 'Facturas',
    'version': '1.0',
    'summary': 'Añade',
    'description': """
    """,
    'author': '',
    'website': '',
    'category': '',
    'depends': ['account'
                ],
    'init_xml': [],
    'update_xml': [
            'report/hr_account_report.xml',
            'report/report_account_view.xml',
            'report/report_account_view_lpair.xml',
            'report/report_retencion_view.xml',
            'report/report_retencion_view_lpair.xml',
            'report/report_asiento_view.xml',
            'report/report_asiento_view_supplier.xml',
            'report/report_account_nota.xml',
            'report/report_liquidacion_view.xml',
            'report/report_account_servicio.xml',
            'report/report_retencion_inv_supplier.xml',
            'report/report_retencion_view_lpair.xml',
            'report/report_liquidacion_view_lpair.xml',
            #'report/report_account_nota_lpair.xml',
            #'report/report_factura_lpair.xml',
            #'report/report_liquidacion_lpair.xml',
            #'report/report_retencion_lpair.xml',
    ],
    'installable': True,
    'auto_install': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
