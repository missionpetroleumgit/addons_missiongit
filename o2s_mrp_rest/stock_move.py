# -*- coding: utf-8 -*-
#####
#  Stock move for restaurants
#####
from datetime import datetime, date, time, timedelta
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
import calendar
from openerp import models, fields, api
from openerp.exceptions import except_orm, Warning
import openerp.addons.decimal_precision as dp


class stock_move(models.Model):
    _inherit = 'stock.move'

    @api.one
    def _daysxdate(self):
         res = {}
         dif = 0
         ahora = datetime.now()
         print "Ahora", ahora

         if self.date_expected:
             dif = (ahora - datetime.strptime(self.date_expected, DEFAULT_SERVER_DATETIME_FORMAT)).days
         self.days_rest = dif

    @api.one
    def _daysresxdate(self):
         res = {}
         dif = 0

         if self.days_vig:
             dif = self.days_vig-self.days_rest
         self.days_rest1 = dif

    @api.one
    def _state_prod(self):
         res = {}
         dif = 0
         stad = ''
         if self.days_vig > 0:
             dif = self.days_vig-self.days_rest
             if dif >= 2:
                 stad = 'Normal'
             elif dif < 2 and dif > 0:
                 stad = 'Por Caducar'
             elif dif <= 0:
                 stad = 'Caducado'
         self.state_prod = stad



    days_vig = fields.Integer('Vigencia', help="Dias de vigencia si es produccion.")
    days_rest = fields.Integer('Dias Produccion', compute=_daysxdate, help="Dias de vigencia restante.")
    days_rest1 = fields.Integer('Dias Restantes', compute=_daysresxdate, help="Dias de vigencia restante.")
    state_prod = fields.Char('E. Produccion', compute=_state_prod, help="Dias de vigencia restante.")