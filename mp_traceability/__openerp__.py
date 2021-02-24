#  -*- encoding: utf-8 -*-
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
    "name": "Trazabilidad",
    "version": "1.0",
    "description": """
    .

    """,
    "author": "Daniel Aldaz",
    "website": "",
    "category": "stock",
    "depends": [
        'stock',
        'o2s_purchase_importation',
        'report'
    ],
    "data": [
        'views/stock_view.xml',
        'report/traceability_report.xml',
        'report/traceability_material_report.xml',
        'report/traceability_view_report.xml',
        'views/stock_picking_view.xml',
    ],
    "demo_xml": [
    ],
    "active": False,
    "installable": True,
    "certificate": "",
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
