# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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
    'name': 'Report Inventary',
    'version': '1.1',
    'author': 'Cristobal Sanchez',
    'summary': ' Report Inventory, Logistic, Valuation',
    'description': """
Modulo Reportes de inventario
======================
Este modulo aniade reportes de inventario real

Key Features
------------
* Reporte Kardex (periodical or automatic)
* Por compania y fecha

Kardex Report / Incluye reportes de productos a la fecha:
------------------------------------------------------
* Reportes de inventario a la fecha (también soporta fechas anteriores)
    """,
    'website': 'https://www.odoo.com/page/warehouse',
    'images': [],
    'depends': ['stock', 'account'],
    'category': 'Hidden',
    'sequence': 16,
    'demo': [
        'stock_account_demo.xml'
    ],
    'data': [
        'report/stock_inventary_real_view.xml',
        'report/stock_inventary_detallado_view.xml',
        'report/inventory_stock_report_view.xml',
        'report/stock_location_kardex_report_view.xml',
        'views/stock_move_report_view.xml',
    ],
    'test': [

    ],
    'installable': True,
    'auto_install': True,
}