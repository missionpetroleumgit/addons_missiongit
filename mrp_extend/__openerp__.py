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
    "name": "MRP-EXTENSION",
    "version": "1.0",
    "description": """
Agrega nuevo comportamiento al modulo MRP

    """,
    "author": "FREELANCE",
    "website": "",
    "category": "mrp",
    "depends": [
        'mrp',
        'sale',
    ],
    "data": [
        'data/data.xml',
        'views/mrp_production_views.xml',
        'views/sale_order_views.xml',
        'views/stock_views.xml',
        'wizard/new_product_wizard_views.xml',
        'wizard/mrp_product_produce_view.xml',
    ],
    "demo_xml": [
    ],
    "active": False,
    "installable": True,
    "certificate" : "",
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
