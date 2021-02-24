# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018  Open2S  (http://www.open2s.ec)
#    All Rights Reserved.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
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
{
    'name': 'Sucursales Open2S',
    'version': '8.0.1.0.0',
    'category': '',
    'sequence': 19,
    'summary': '',
    'description': """
Multi Store
===========
Permite añadir Sucursales a Odoo
    """,
    'author':  'Open Source Solutions',
    'website': 'www.open2s.ec',
    'license': 'AGPL-3',
    'images': [
    ],
    'depends': [
        'hr','multi_store'
    ],
    'data': [
        'views/hr_employee_view.xml',
    ],
    'demo': [
    ],
    'test': [
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: