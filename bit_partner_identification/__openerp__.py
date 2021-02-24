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
    'name': 'Identify Partner',
    'version': '1.0',
    'summary': 'Añade Identificacion de las Empresas',
    'description': """ Crear campos de CI/RUC en partner
    """,
    'author': 'Guillermo Herrera Banda',
    'website': '',
    'category': 'Accounting',
    'depends': ['base'],
    'init_xml': [],
    'update_xml': [
        'views/partner_view.xml',
        'views/partner_country.xml',
        
    ],
    'installable': True,
    'active': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
