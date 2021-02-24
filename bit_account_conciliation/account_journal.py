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

from openerp.osv import fields, osv
from openerp.tools import float_is_zero
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
from openerp.report import report_sxw
from openerp.tools import float_compare, float_round

import time

class account_journal(osv.osv):

    _inherit = 'account.journal'
    _description = 'DIARIOS VENTAS'
    _columns = {
        'is_fo_pa': fields.boolean('Forma Pago', help="Marcar esta opcion si el diario es una forma de pago para PV."),
        'comision': fields.float('Comision', digits_compute=dp.get_precision('Account'), help="Ingresar el porcentaje de comision para este tipo de forma pago"),
        'default_comision_account_id': fields.many2one('account.account', 'Cuenta Comision', domain="[('type','!=','view')]", help="Escoger la cuenta para comision de la concialion de tarjetas"),
        'iva_ret': fields.float('Iva Retenido', digits_compute=dp.get_precision('Account'), help="Ingresar el porcentaje de iva retenido para este tipo de forma pago"),
        'default_iva_ret_account_id': fields.many2one('account.account', 'Cuenta Iva Retenido', domain="[('type','!=','view')]", help="Escoger la cuenta para iva retenido de la concialion de tarjetas"),
        'irf_ret': fields.float('Irf Retenido', digits_compute=dp.get_precision('Account'), help="Ingresar el porcentaje de irf retenido para este tipo de forma pago"),
        'default_irf_ret_account_id': fields.many2one('account.account', 'Cuenta Irf Retenido', domain="[('type','!=','view')]", help="Escoger la cuenta para irf retenido de la concialion de tarjetas"),
        'default_bancocon_account_id': fields.many2one('account.account', 'Cuenta Banco', domain="[('type','!=','view')]", help="Escoger la cuenta para banco de la concialion de tarjetas"),
    }
    _defaults = {
        'is_fo_pa': False,
    }