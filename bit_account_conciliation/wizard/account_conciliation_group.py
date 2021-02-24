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

from openerp import tools
from openerp.osv import fields, osv
from openerp.report import report_sxw
from openerp.addons.decimal_precision import decimal_precision as dp
from string import upper
from time import strftime
import base64
import StringIO
import cStringIO
import time
from psycopg2.errorcodes import SUBSTRING_ERROR
from decimal import Decimal
from unicodedata import decimal
import csv
import mx.DateTime
from mx.DateTime import RelativeDateTime
import datetime
import xlwt as pycel #Libreria que Exporta a Excel


class account_conciliation_group(osv.Model):
    _name = "account.conciliation.group"
    _description = 'Generacion Conciliacion Tarjetas Credito'



    def get_lines_report_wage(self, cr, uid, ids, form):
        res = []
        date_from = form.get('date_from', False)
        date_to = form.get('date_to', False)
        respon = form.get('type_user', False)

        conci_obj = self.pool.get('account.conciliation.statement')
        conci_lin_obj = self.pool.get('account.conciliation.statement.line')
        bank_stat_obj = self.pool.get('account.bank.statement')
        bank_stat_line_obj = self.pool.get('account.bank.statement.line')
        tot_inv = 0.00
        tot_puini = 0.00
        tot_tot = 0.00

        nam = "Generado con exito"
        if respon:
            print "INGRESO TIENDA GENERO CONCILIACION"
            stat_bank_ids = conci_obj.search(cr, uid, [('date', '>=', date_from), ('date', '<=', date_to), ('user_id', '=', respon[0]),  ('state', 'in', ['draft','open','pending']), ('type', '=', 'individual')], order='name')
            print "LISTA IDS", stat_bank_ids
            if len(stat_bank_ids)>0:
                print "SI HAY REGISTROS"
                stat_bank_obj = conci_obj.browse(cr, uid, stat_bank_ids)
                ban = 0
                for extrac in stat_bank_obj:
                    if ban == 0:
                        vals = {
                            'name': 'Conciliacion'+"/"+str(respon[1]),
                              'journal_id': extrac.journal_id.id,
                              'period_id': extrac.period_id.id,
                              'user_id': extrac.user_id.id,
                              'poss_id' : extrac.poss_id.id,
                              'company_id' : extrac.company_id.id,
                              'date_cierre': extrac.date,
                              'is_con_dif': True,
                              'default_comision_account_id': extrac.user_id.pos_config.default_comision_account_id.id,
                              'type': 'grupal',
                              'state': 'open'
                        }
                        print "***vals conciliation***: ", vals
                        concil_id = conci_obj.create(cr, uid, vals)
                        ban = 1
                    vals_stat = {'state': 'confirm'}
                    conci_obj.write(cr,uid,extrac.id,vals_stat)

                    vals_line = {
                             'name': extrac.name,
                             'amount': extrac.valor_bruto,
                             'amount_conc': 0.00,
                             'amount_pendiente': extrac.valor_bruto,
                             'user_id': extrac.user_id.id,
                             'conciliation_id': concil_id,
                             'journal_id': extrac.journal_id.id,
                             'company_id': extrac.company_id.id,
                             'amount_comision': round(extrac.valor_comision,2),
                             'amount_iva_retenido': round(extrac.valor_iva,2),
                             'amount_irf_retenido': round(extrac.valor_irf,2),
                             'amount_neto': round(extrac.valor_neto,2)
                    }
                    print "***vals conciliation line***: ", vals_line
                    concil_line_id = conci_lin_obj.create(cr, uid, vals_line)

            else:
                raise osv.except_osv("Advertencia", 'No existe recaps para la tienda responsable %s' % (str(respon[1])))

        return self.write(cr, uid, ids, {'name':nam})


    def action_conciliation(self, cr, uid, ids, context=None):
        if not ids:
            return {'type_pv': 'ir.actions.act_window_close'}
        if context is None:
            context = {}
        form = self.read(cr, uid, ids)[0]
        date_from = form.get('date_from')
        date_to = form.get('date_to')
        type_pv = form.get('type_pv')

        procesar = self.get_lines_report_wage(cr, uid, ids, form)

        return {
            'type': 'ir.actions.client',
            'tag': 'reload'
        }


    _columns = {
        'name':fields.char('Nombre', size=64, required=False, readonly=False),
        'data':fields.binary('Archivo', filters=None),
        'date_from': fields.date('Fecha Desde'),
        'date_to': fields.date('Fecha Hasta'),
        'type_user' :fields.many2one('res.users','Tienda Responsable'),
    }
account_conciliation_group()
