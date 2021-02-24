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
    "name": "Electronic Invoicing",
    "version": "1.1",
    "description": """ Modulo de Facturación Electrónica se conecta al SRI en linea via web services

    """,
    "author": "Open2S - Cristobal Sanchez",
    "website": "",
    "category": "Invoicing & Finance",
    "depends": [
        "account"
    ],
    "data": [
        'wizard/wizard_comprobante_retencion_view.xml',
        'wizard/wizard_factura_electronica_view.xml',
        'wizard/wizard_guia_remision_view.xml',
        'wizard/wizard_purchase_clearance_view.xml',
        'account_report_fe.xml',
        'views/account_invoice_view.xml',
        'views/account_view.xml',
        'views/partner_view.xml',
        'views/stock_view.xml',
        #'views/service_ticket_view.xml',
    ],
    "demo_xml": [
    ],
    "active": False,
    "installable": True,
    "certificate" : "",
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: