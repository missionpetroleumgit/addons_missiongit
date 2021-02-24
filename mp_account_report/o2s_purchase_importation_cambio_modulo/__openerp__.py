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
    "name": "Ordenes de Importacion",
    "version": "1.0",
    "description": """
    Este modulo agrega las importaciones de compra.

    """,
    "author": "Open2S",
    "website": "",
    "category": "Purchase",
    "depends": [
        'o2s_stock_purchase',
        'purchase_tiw',
    ],
    "data": [
        'data/sequence.xml',
        'views/deleted_menu.xml',
        'views/wizard_generate_importation.xml',
        'views/wizard_generate_invoice.xml',
        'views/purchase.xml',
        'views/importation.xml',
        'views/product.xml',
        'views/account.xml',
        'views/tariff_item.xml',
        'views/res_company.xml',
        'views/report_purchase_importation_view.xml',
        'report/report_importation.xml',
        'security/groups.xml',
        # 'views/stock_view.xml',
    ],
    "demo_xml": [
    ],
    "active": False,
    "installable": True,
    "certificate" : "",
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
