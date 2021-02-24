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
    "name": "Anticipos",
    "version": "1.0",
    "description": """
    Este modulo agrega los anticipos.

    """,
    "author": "Open2S",
    "website": "",
    "category": "Account",
    "depends": [
        'account_voucher', 'bit_payment'
    ],
    "data": [
        'views/account_advances.xml',
        'views/res_company.xml',
        'views/account_voucher.xml',
        'data/account_voucher_data.xml'
    ],
    "demo_xml": [
    ],
    "active": False,
    "installable": True,
    "certificate" : "",
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

