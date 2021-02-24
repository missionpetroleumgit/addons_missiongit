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
    'name': 'Product Retail adaptado a TIW',
    'version': '1.0',
    'summary': 'Se Modifica el proceso de creacion de las variantes',
    'description': """
    """,
    'author': 'OPEN2S',
    'website': '',
    'category': 'Product',
    'depends': ['product'],
    'init_xml': [],
    'update_xml': [
        'views/product_product_view.xml',
        'wizard/product_product_wizard.xml',
        'views/report_purchase_order_view.xml',
        'report/report_purchase_order.xml',
        'views/footer.xml'
    ],
    'installable': True,
    'auto_install': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
