# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2016 Open Source Solutions.
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
    "name": "Usuarios",
    "version": "1.0",
    "description": """
Con este modulo puede escoger en el usuario el partner del mismo usuario, al crear un empleado, si no escoge un usuario en la creacion del mismo le crea un empresa y si ya tenía una tendra una repetida mas, mientras que si le escoge un usuario en la creacion del empleado se le modificara a la empresa que tenga existente.

    """,
    "author": "Open2S",
    'summary': 'Con este modulo puede escoger el partner en la creacion del usuario',
    "website": "",
    "category": "Usuarios",
    "depends": [
		    "base",
			],
	"data":[

        "views/o2s_res_users_view.xml",
			],
    "demo_xml": [
			],
    "active": False,
    "installable": True,
    "certificate" : "",
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
