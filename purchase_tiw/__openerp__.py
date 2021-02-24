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
    "name": "Cotizaciones para compras",
    "version": "1.0",
    "description": """
Este modulo agrega las cotizacones a la requisicion de compra.

    """,
    "author": "Open2S",
    "website": "",
    "category": "Product",
    "depends": [
        'hr', 'o2s_purchase_expense_distribution', 'purchase',
    ],
    "data": [
        'security/security.xml',
        'views/quotes_report.xml',
        'views/purchase_order_report.xml',
#        'views/purchase_procura.xml',
        'views/quotes_view.xml',
        'data/sequences.xml',
        'data/purchase_quotes_data.xml',
        'views/purchase_order.xml',
        'wizard/generate_invoice_from_many_purchases.xml',
        'views/quotation_order_report.xml',
        'views/quotation_report.xml',
    ],
    "images": [
        'img/batman.png'
    ],
    "demo_xml": [
    ],
    "active": False,
    "installable": True,
    "certificate" : "",
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
