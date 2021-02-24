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


class account_conciliation_tarjet(osv.Model):
    _name = "account.conciliation.tarjet"
    _description = 'Generacion Conciliacion Tarjetas Credito'
    
        
    
    def get_lines_report_wage(self, cr, uid, ids, form):
        res = []
        date_from = form.get('date_from', False)
        date_to = form.get('date_to', False)
        tarjeta = form.get('type_pv', False)
        respon = form.get('type_user', False)
        lote = form.get('lote', False)
        
        conci_obj = self.pool.get('account.conciliation.statement')
        conci_lin_obj = self.pool.get('account.conciliation.statement.line')
        bank_stat_obj = self.pool.get('account.bank.statement')
        bank_stat_line_obj = self.pool.get('account.bank.statement.line')
        tot_inv = 0.00
        tot_puini = 0.00
        tot_tot = 0.00
        
#         print "date_from", date_from
#         print "date_to", date_to
#         print "tarjeta", tarjeta[0]
#         print "resp***", respon[0]
        nam = "Generado con exito"
        if tarjeta and respon:
            print "INGRESO TARJETA Y TIENDA"
            stat_bank_ids = bank_stat_obj.search(cr, uid, [('date', '>=', date_from), ('date', '<=', date_to), ('user_id', '=', respon[0]), ('journal_id', '=', tarjeta[0]), ('conciliation_id', '=', None), ('balance_end_real', '>', 0)], order='name')
            print "LISTA IDS", stat_bank_ids
            if len(stat_bank_ids)>0:
                print "SI HAY REGISTROS"
                stat_bank_obj = bank_stat_obj.browse(cr, uid, stat_bank_ids)
                for extrac in stat_bank_obj:
                    vals = {
                        'name': 'Conciliacion'+"/"+str(respon[1]),
                          'journal_id': extrac.journal_id.id,
                          'period_id': extrac.period_id.id,
                          'user_id': extrac.user_id.id,
                          'poss_id' : extrac.pos_session_id.id,
                          'company_id' : extrac.company_id.id,
                          'comision': extrac.journal_id.comision,
                          'iva_retenido': extrac.journal_id.iva_ret,
                          'irf_retenido': extrac.journal_id.irf_ret,
                          'lote': lote,
                          'date_cierre': extrac.date,
                          'type': 'individual',
                          'state': 'open'
                    }
                    print "***vals conciliation***: ", vals
                    concil_id = conci_obj.create(cr, uid, vals) 
                    vals_stat = {'conciliation_id' : concil_id,
                              'state': 'confirm'}
                    bank_stat_obj.write(cr,uid,extrac.id,vals_stat)
                    stat_bank_line_ids = bank_stat_line_obj.search(cr, uid, [('statement_id', '=', extrac.id)], order='name')
                    stat_bank_line_obj =  bank_stat_line_obj.browse(cr, uid, stat_bank_line_ids)
                    val_b = 0.00
                    val_co = 0.00
                    val_iv = 0.00
                    val_ir = 0.00
                    val_net = 0.00
                    for extrac_line in stat_bank_line_obj:
                        vals_line = {
                                 'name': extrac_line.name,
                                 'amount': extrac_line.amount,
                                 'amount_conc': 0.00,
                                 'amount_pendiente': extrac_line.amount,
                                 'partner_id': extrac_line.partner_id.id,
                                 'account_id': extrac_line.account_id.id,
                                 'conciliation_id': concil_id,
                                 'journal_id': extrac_line.journal_id.id,
                                 'ref': extrac_line.ref,
                                 'user_id': extrac.user_id.id,
                                 'lote': lote,
                                 'company_id': extrac_line.company_id.id,
                                 'amount_comision': round((extrac_line.amount*extrac.journal_id.comision)/100,2),
                                 'amount_iva_retenido': round(((extrac_line.amount-(extrac_line.amount/1.14))*extrac.journal_id.iva_ret)/100,2),
                                 'amount_irf_retenido': round(((extrac_line.amount/1.14)*extrac.journal_id.irf_ret)/100,2),
                                 'amount_neto': round(extrac_line.amount-((extrac_line.amount*extrac.journal_id.comision)/100)-(((extrac_line.amount-(extrac_line.amount/1.14))*extrac.journal_id.iva_ret)/100)-(((extrac_line.amount/1.14)*extrac.journal_id.irf_ret)/100),2)
                        }
                        print "***vals conciliation line***: ", vals_line
                        concil_line_id = conci_lin_obj.create(cr, uid, vals_line)                  
                        val_b += extrac_line.amount
                        val_co += round((extrac_line.amount*extrac.journal_id.comision)/100,2)
                        val_iv += round(((extrac_line.amount-(extrac_line.amount/1.14))*extrac.journal_id.iva_ret)/100,2)
                        val_ir += round(((extrac_line.amount/1.14)*extrac.journal_id.irf_ret)/100,2)
                        val_net += round(extrac_line.amount-((extrac_line.amount*extrac.journal_id.comision)/100)-(((extrac_line.amount-(extrac_line.amount/1.14))*extrac.journal_id.iva_ret)/100)-(((extrac_line.amount/1.14)*extrac.journal_id.irf_ret)/100),2)
                    val_val = {'valor_bruto': val_b,
                               'valor_neto': val_net,
                               'valor_comision': val_co,
                               'valor_iva': val_iv,
                               'valor_irf': val_ir
                    }
                    conci_obj.write(cr,uid,concil_id,val_val)
                    #CREAR CONCILIACION GRUPO
                    #raise osv.except_osv("Advertencia", 'OJO')
                    acc_grup = conci_obj.search(cr, uid, [('user_id','=',respon[0]), ('type','=','grupal'), ('state','=','open')])
                    if len(acc_grup)>0:
                        id_grop = acc_grup[0]
                    else:
                        vals_g = {
                        'name': 'Conciliacion'+"/"+str(respon[1]),
                          'journal_id': extrac.journal_id.id,
                          'period_id': extrac.period_id.id,
                          'user_id': extrac.user_id.id,
                          'poss_id' : extrac.pos_session_id.id,
                          'company_id' : extrac.company_id.id,
                          'comision': extrac.journal_id.comision,
                          'iva_retenido': extrac.journal_id.iva_ret,
                          'irf_retenido': extrac.journal_id.irf_ret,
                          'lote': lote,
                          'date_cierre': extrac.date,
                          'is_con_dif': True,
                          'default_comision_account_id': extrac.user_id.pos_config.default_comision_account_id.id,
                          'type': 'grupal',
                          'state': 'open'
                        }
                        print "***vals conciliation***: ", vals_g
                        id_grop = conci_obj.create(cr, uid, vals_g)
                    acc_con_ids = conci_obj.search(cr, uid, [('id', '=', concil_id)], order='name')
                    acc_con_obj =  conci_obj.browse(cr, uid, acc_con_ids)
                    for con_gr in acc_con_obj:
                        vals_line_g = {
                                 'name': con_gr.name,
                                 'amount': round(con_gr.valor_bruto, 2),
                                 'amount_conc': 0.00,
                                 'amount_pendiente': round(con_gr.valor_bruto, 2),
                                 'conciliation_id': id_grop,
                                 'journal_id': con_gr.journal_id.id,
                                 'ref': con_gr.poss_id.name,
                                 'user_id': con_gr.user_id.id,
                                 'lote': con_gr.lote,
                                 'company_id': con_gr.company_id.id,
                                 'amount_comision': round(con_gr.valor_comision, 2),
                                 'amount_iva_retenido': round(con_gr.valor_iva, 2),
                                 'amount_irf_retenido': round(con_gr.valor_irf, 2),
                                 'amount_neto': round(con_gr.valor_neto ,2)
                        }
                        print "***vals conciliation line***: ", vals_line_g
                        concil_line_id = conci_lin_obj.create(cr, uid, vals_line_g)
            else:
                raise osv.except_osv("Advertencia", 'No existe ventas con el tipo %s y tienda responsable %s' % (str(tarjeta[1]), str(respon[1])))
        elif tarjeta and not respon:
            print "INGRESO TARJETA Y NO TIENDA"
            stat_bank_ids = bank_stat_obj.search(cr, uid, [('date', '>=', date_from), ('date', '<=', date_to), ('journal_id', '=', tarjeta[0]), ('conciliation_id', '=', None), ('balance_end_real', '>', 0)], order='name')
            print "LISTA IDS", stat_bank_ids
            if len(stat_bank_ids)>0:
                print "SI HAY REGISTROS"
                stat_bank_obj = bank_stat_obj.browse(cr, uid, stat_bank_ids)
                for extrac in stat_bank_obj:
                    vals = {
                        'name': 'Conciliacion'+"/"+str(extrac.user_id.name),
                          'journal_id': extrac.journal_id.id,
                          'period_id': extrac.period_id.id,
                          'user_id': extrac.user_id.id,
                          'poss_id' : extrac.pos_session_id.id,
                          'company_id' : extrac.company_id.id,
                          'comision': extrac.journal_id.comision,
                          'iva_retenido': extrac.journal_id.iva_ret,
                          'irf_retenido': extrac.journal_id.irf_ret,
                          'lote': lote,
                          'date_cierre': extrac.date,
                          'type': 'individual',
                          'state': 'open'
                    }
                    print "***vals conciliation***: ", vals
                    concil_id = conci_obj.create(cr, uid, vals) 
                    vals_stat = {'conciliation_id' : concil_id,
                              'state': 'confirm'}
                    bank_stat_obj.write(cr,uid,extrac.id,vals_stat)
                    stat_bank_line_ids = bank_stat_line_obj.search(cr, uid, [('statement_id', '=', extrac.id)], order='name')
                    stat_bank_line_obj =  bank_stat_line_obj.browse(cr, uid, stat_bank_line_ids)
                    val_b = 0.00
                    val_co = 0.00
                    val_iv = 0.00
                    val_ir = 0.00
                    val_net = 0.00
                    for extrac_line in stat_bank_line_obj:
                        vals_line = {
                                 'name': extrac_line.name,
                                 'amount': extrac_line.amount,
                                 'amount_conc': 0.00,
                                 'amount_pendiente': extrac_line.amount,
                                 'partner_id': extrac_line.partner_id.id,
                                 'account_id': extrac_line.account_id.id,
                                 'conciliation_id': concil_id,
                                 'journal_id': extrac_line.journal_id.id,
                                 'ref': extrac_line.ref,
                                 'user_id': extrac.user_id.id,
                                 'lote': lote,
                                 'company_id': extrac_line.company_id.id,
                                 'amount_comision': round((extrac_line.amount*extrac.journal_id.comision)/100,2),
                                 'amount_iva_retenido': round(((extrac_line.amount-(extrac_line.amount/1.14))*extrac.journal_id.iva_ret)/100,2),
                                 'amount_irf_retenido': round(((extrac_line.amount/1.14)*extrac.journal_id.irf_ret)/100,2),
                                 'amount_neto': round(extrac_line.amount-((extrac_line.amount*extrac.journal_id.comision)/100)-(((extrac_line.amount-(extrac_line.amount/1.14))*extrac.journal_id.iva_ret)/100)-(((extrac_line.amount/1.14)*extrac.journal_id.irf_ret)/100),2)
                        }
                        print "***vals conciliation line***: ", vals_line
                        concil_line_id = conci_lin_obj.create(cr, uid, vals_line)
                        val_b += extrac_line.amount
                        val_co += round((extrac_line.amount*extrac.journal_id.comision)/100,2)
                        val_iv += round(((extrac_line.amount-(extrac_line.amount/1.14))*extrac.journal_id.iva_ret)/100,2)
                        val_ir += round(((extrac_line.amount/1.14)*extrac.journal_id.irf_ret)/100,2)
                        val_net += round(extrac_line.amount-((extrac_line.amount*extrac.journal_id.comision)/100)-(((extrac_line.amount-(extrac_line.amount/1.14))*extrac.journal_id.iva_ret)/100)-(((extrac_line.amount/1.14)*extrac.journal_id.irf_ret)/100),2)
                    val_val = {'valor_bruto': val_b,
                               'valor_neto': val_net,
                               'valor_comision': val_co,
                               'valor_iva': val_iv,
                               'valor_irf': val_ir
                    }
                    conci_obj.write(cr,uid,concil_id,val_val)
                    #CREAR CONCILIACION GRUPO
                    #raise osv.except_osv("Advertencia", 'OJO')
                    acc_grup = conci_obj.search(cr, uid, [('user_id','=',respon[0]), ('type','=','grupal'), ('state','=','open')])
                    if len(acc_grup)>0:
                        id_grop = acc_grup[0]
                    else:
                        vals_g = {
                        'name': 'Conciliacion'+"/"+str(respon[1]),
                          'journal_id': extrac.journal_id.id,
                          'period_id': extrac.period_id.id,
                          'user_id': extrac.user_id.id,
                          'poss_id' : extrac.pos_session_id.id,
                          'company_id' : extrac.company_id.id,
                          'comision': extrac.journal_id.comision,
                          'iva_retenido': extrac.journal_id.iva_ret,
                          'irf_retenido': extrac.journal_id.irf_ret,
                          'lote': lote,
                          'date_cierre': extrac.date,
                          'is_con_dif': True,
                          'default_comision_account_id': extrac.user_id.pos_config.default_comision_account_id.id,
                          'type': 'grupal',
                          'state': 'open'
                        }
                        print "***vals conciliation***: ", vals_g
                        id_grop = conci_obj.create(cr, uid, vals_g)
                    acc_con_ids = conci_obj.search(cr, uid, [('id', '=', concil_id)], order='name')
                    acc_con_obj =  conci_obj.browse(cr, uid, acc_con_ids)
                    for con_gr in acc_con_obj:
                        vals_line_g = {
                                 'name': con_gr.name,
                                 'amount': round(con_gr.valor_bruto, 2),
                                 'amount_conc': 0.00,
                                 'amount_pendiente': round(con_gr.valor_bruto, 2),
                                 'conciliation_id': id_grop,
                                 'journal_id': con_gr.journal_id.id,
                                 'ref': con_gr.poss_id.name,
                                 'user_id': con_gr.user_id.id,
                                 'lote': con_gr.lote,
                                 'company_id': con_gr.company_id.id,
                                 'amount_comision': round(con_gr.valor_comision, 2),
                                 'amount_iva_retenido': round(con_gr.valor_iva, 2),
                                 'amount_irf_retenido': round(con_gr.valor_irf, 2),
                                 'amount_neto': round(con_gr.valor_neto ,2)
                        }
                        print "***vals conciliation line***: ", vals_line_g
                        concil_line_id = conci_lin_obj.create(cr, uid, vals_line_g)
            else:
                raise osv.except_osv("Advertencia", 'No existe ventas con el tipo %s' % (str(tarjeta[1])))
        elif respon and not tarjeta:
            print "INGRESO TIENDA Y NO TARJETA"
            stat_bank_ids = bank_stat_obj.search(cr, uid, [('date', '>=', date_from), ('date', '<=', date_to), ('user_id', '=', respon[0]), ('journal_id.is_fo_pa', '=', True), ('conciliation_id', '=', None), ('balance_end_real', '>', 0)], order='name')
            print "LISTA IDS", stat_bank_ids
            if len(stat_bank_ids)>0:
                print "SI HAY REGISTROS"
                stat_bank_obj = bank_stat_obj.browse(cr, uid, stat_bank_ids)
                for extrac in stat_bank_obj:
                    vals = {
                        'name': 'Conciliacion'+"/"+str(respon[1]),
                          'journal_id': extrac.journal_id.id,
                          'period_id': extrac.period_id.id,
                          'user_id': extrac.user_id.id,
                          'poss_id' : extrac.pos_session_id.id,
                          'company_id' : extrac.company_id.id,
                          'comision': extrac.journal_id.comision,
                          'iva_retenido': extrac.journal_id.iva_ret,
                          'irf_retenido': extrac.journal_id.irf_ret,
                          'lote': lote,
                          'date_cierre': extrac.date,
                          'type': 'individual',
                          'state': 'open'
                    }
                    print "***vals conciliation***: ", vals
                    concil_id = conci_obj.create(cr, uid, vals) 
                    vals_stat = {'conciliation_id' : concil_id,
                              'state': 'confirm'}
                    bank_stat_obj.write(cr,uid,extrac.id,vals_stat)
                    stat_bank_line_ids = bank_stat_line_obj.search(cr, uid, [('statement_id', '=', extrac.id)], order='name')
                    stat_bank_line_obj =  bank_stat_line_obj.browse(cr, uid, stat_bank_line_ids)
                    val_b = 0.00
                    val_co = 0.00
                    val_iv = 0.00
                    val_ir = 0.00
                    val_net = 0.00
                    for extrac_line in stat_bank_line_obj:
                        vals_line = {
                                 'name': extrac_line.name,
                                 'amount': extrac_line.amount,
                                 'amount_conc': 0.00,
                                 'amount_pendiente': extrac_line.amount,
                                 'partner_id': extrac_line.partner_id.id,
                                 'account_id': extrac_line.account_id.id,
                                 'conciliation_id': concil_id,
                                 'journal_id': extrac_line.journal_id.id,
                                 'ref': extrac_line.ref,
                                 'user_id': extrac.user_id.id,
                                 'lote': lote,
                                 'company_id': extrac_line.company_id.id,
                                 'amount_comision': round((extrac_line.amount*extrac.journal_id.comision)/100,2),
                                 'amount_iva_retenido': round(((extrac_line.amount-(extrac_line.amount/1.14))*extrac.journal_id.iva_ret)/100,2),
                                 'amount_irf_retenido': round(((extrac_line.amount/1.14)*extrac.journal_id.irf_ret)/100,2),
                                 'amount_neto': round(extrac_line.amount-((extrac_line.amount*extrac.journal_id.comision)/100)-(((extrac_line.amount-(extrac_line.amount/1.14))*extrac.journal_id.iva_ret)/100)-(((extrac_line.amount/1.14)*extrac.journal_id.irf_ret)/100),2)
                        }
                        print "***vals conciliation line***: ", vals_line
                        concil_line_id = conci_lin_obj.create(cr, uid, vals_line)
                        val_b += extrac_line.amount
                        val_co += round((extrac_line.amount*extrac.journal_id.comision)/100,2)
                        val_iv += round(((extrac_line.amount-(extrac_line.amount/1.14))*extrac.journal_id.iva_ret)/100,2)
                        val_ir += round(((extrac_line.amount/1.14)*extrac.journal_id.irf_ret)/100,2)
                        val_net += round(extrac_line.amount-((extrac_line.amount*extrac.journal_id.comision)/100)-(((extrac_line.amount-(extrac_line.amount/1.14))*extrac.journal_id.iva_ret)/100)-(((extrac_line.amount/1.14)*extrac.journal_id.irf_ret)/100),2)
                    val_val = {'valor_bruto': val_b,
                               'valor_neto': val_net,
                               'valor_comision': val_co,
                               'valor_iva': val_iv,
                               'valor_irf': val_ir
                    }
                    conci_obj.write(cr,uid,concil_id,val_val)
                    print "***vals valores***: ", val_val
                    #CREAR CONCILIACION GRUPO
                    #raise osv.except_osv("Advertencia", 'OJO')
                    acc_grup = conci_obj.search(cr, uid, [('user_id','=',respon[0]), ('type','=','grupal'), ('state','=','open')])
                    if len(acc_grup)>0:
                        id_grop = acc_grup[0]
                    else:
                        vals_g = {
                        'name': 'Conciliacion'+"/"+str(respon[1]),
                          'journal_id': extrac.journal_id.id,
                          'period_id': extrac.period_id.id,
                          'user_id': extrac.user_id.id,
                          'poss_id' : extrac.pos_session_id.id,
                          'company_id' : extrac.company_id.id,
                          'comision': extrac.journal_id.comision,
                          'iva_retenido': extrac.journal_id.iva_ret,
                          'irf_retenido': extrac.journal_id.irf_ret,
                          'lote': lote,
                          'date_cierre': extrac.date,
                          'is_con_dif': True,
                          'default_comision_account_id': extrac.user_id.pos_config.default_comision_account_id.id,
                          'type': 'grupal',
                          'state': 'open'
                        }
                        print "***vals conciliation***: ", vals_g
                        id_grop = conci_obj.create(cr, uid, vals_g)
                    acc_con_ids = conci_obj.search(cr, uid, [('id', '=', concil_id)], order='name')
                    acc_con_obj =  conci_obj.browse(cr, uid, acc_con_ids)
                    for con_gr in acc_con_obj:
                        vals_line_g = {
                                 'name': con_gr.name,
                                 'amount': round(con_gr.valor_bruto, 2),
                                 'amount_conc': 0.00,
                                 'amount_pendiente': round(con_gr.valor_bruto, 2),
                                 'conciliation_id': id_grop,
                                 'journal_id': con_gr.journal_id.id,
                                 'ref': con_gr.poss_id.name,
                                 'user_id': con_gr.user_id.id,
                                 'lote': con_gr.lote,
                                 'company_id': con_gr.company_id.id,
                                 'amount_comision': round(con_gr.valor_comision, 2),
                                 'amount_iva_retenido': round(con_gr.valor_iva, 2),
                                 'amount_irf_retenido': round(con_gr.valor_irf, 2),
                                 'amount_neto': round(con_gr.valor_neto ,2)
                        }
                        print "***vals conciliation line***: ", vals_line_g
                        concil_line_id = conci_lin_obj.create(cr, uid, vals_line_g)
            else:
                raise osv.except_osv("Advertencia", 'No existe ventas la tienda responsable %s' % (str(respon[1])))
        else:
            print "NO INGRESO PARAMETROS GENERAL"
            stat_bank_ids = bank_stat_obj.search(cr, uid, [('date', '>=', date_from), ('date', '<=', date_to), ('journal_id.is_fo_pa', '=', True), ('conciliation_id', '=', None), ('balance_end_real', '>', 0)], order='name')
            print "LISTA IDS", stat_bank_ids
            if len(stat_bank_ids)>0:
                print "SI HAY REGISTROS"
                stat_bank_obj = bank_stat_obj.browse(cr, uid, stat_bank_ids)
                for extrac in stat_bank_obj:
                    vals = {
                        'name': 'Conciliacion'+"/"+str(extrac.user_id.name),
                          'journal_id': extrac.journal_id.id,
                          'period_id': extrac.period_id.id,
                          'user_id': extrac.user_id.id,
                          'poss_id' : extrac.pos_session_id.id,
                          'company_id' : extrac.company_id.id,
                          'comision': extrac.journal_id.comision,
                          'iva_retenido': extrac.journal_id.iva_ret,
                          'irf_retenido': extrac.journal_id.irf_ret,
                          'lote': lote,
                          'date_cierre': extrac.date,
                          'type': 'individual',
                          'state': 'open'
                    }
                    print "***vals conciliation***: ", vals
                    concil_id = conci_obj.create(cr, uid, vals) 
                    vals_stat = {'conciliation_id' : concil_id,
                              'state': 'confirm'}
                    bank_stat_obj.write(cr,uid,extrac.id,vals_stat)
                    stat_bank_line_ids = bank_stat_line_obj.search(cr, uid, [('statement_id', '=', extrac.id)], order='name')
                    stat_bank_line_obj =  bank_stat_line_obj.browse(cr, uid, stat_bank_line_ids)
                    val_b = 0.00
                    val_co = 0.00
                    val_iv = 0.00
                    val_ir = 0.00
                    val_net = 0.00
                    for extrac_line in stat_bank_line_obj:
                        vals_line = {
                                 'name': extrac_line.name,
                                 'amount': extrac_line.amount,
                                 'amount_conc': 0.00,
                                 'amount_pendiente': extrac_line.amount,
                                 'partner_id': extrac_line.partner_id.id,
                                 'account_id': extrac_line.account_id.id,
                                 'conciliation_id': concil_id,
                                 'journal_id': extrac_line.journal_id.id,
                                 'ref': extrac_line.ref,
                                 'user_id': extrac.user_id.id,
                                 'lote': lote,
                                 'company_id': extrac_line.company_id.id,
                                 'amount_comision': round((extrac_line.amount*extrac.journal_id.comision)/100,2),
                                 'amount_iva_retenido': round(((extrac_line.amount-(extrac_line.amount/1.14))*extrac.journal_id.iva_ret)/100,2),
                                 'amount_irf_retenido': round(((extrac_line.amount/1.14)*extrac.journal_id.irf_ret)/100,2),
                                 'amount_neto': round(extrac_line.amount-((extrac_line.amount*extrac.journal_id.comision)/100)-(((extrac_line.amount-(extrac_line.amount/1.14))*extrac.journal_id.iva_ret)/100)-(((extrac_line.amount/1.14)*extrac.journal_id.irf_ret)/100),2)
                        }
                        print "***vals conciliation line***: ", vals_line
                        concil_line_id = conci_lin_obj.create(cr, uid, vals_line)
                        val_b += extrac_line.amount
                        val_co += round((extrac_line.amount*extrac.journal_id.comision)/100,2)
                        val_iv += round(((extrac_line.amount-(extrac_line.amount/1.14))*extrac.journal_id.iva_ret)/100,2)
                        val_ir += round(((extrac_line.amount/1.14)*extrac.journal_id.irf_ret)/100,2)
                        val_net += round(extrac_line.amount-((extrac_line.amount*extrac.journal_id.comision)/100)-(((extrac_line.amount-(extrac_line.amount/1.14))*extrac.journal_id.iva_ret)/100)-(((extrac_line.amount/1.14)*extrac.journal_id.irf_ret)/100),2)
                    val_val = {'valor_bruto': val_b,
                               'valor_neto': val_net,
                               'valor_comision': val_co,
                               'valor_iva': val_iv,
                               'valor_irf': val_ir
                    }
                    conci_obj.write(cr,uid,concil_id,val_val)
                    #CREAR CONCILIACION GRUPO
                    #raise osv.except_osv("Advertencia", 'OJO')
                    acc_grup = conci_obj.search(cr, uid, [('user_id','=',respon[0]), ('type','=','grupal'), ('state','=','open')])
                    if len(acc_grup)>0:
                        id_grop = acc_grup[0]
                    else:
                        vals_g = {
                        'name': 'Conciliacion'+"/"+str(respon[1]),
                          'journal_id': extrac.journal_id.id,
                          'period_id': extrac.period_id.id,
                          'user_id': extrac.user_id.id,
                          'poss_id' : extrac.pos_session_id.id,
                          'company_id' : extrac.company_id.id,
                          'comision': extrac.journal_id.comision,
                          'iva_retenido': extrac.journal_id.iva_ret,
                          'irf_retenido': extrac.journal_id.irf_ret,
                          'lote': lote,
                          'date_cierre': extrac.date,
                          'is_con_dif': True,
                          'default_comision_account_id': extrac.user_id.pos_config.default_comision_account_id.id,
                          'type': 'grupal',
                          'state': 'open'
                        }
                        print "***vals conciliation***: ", vals_g
                        id_grop = conci_obj.create(cr, uid, vals_g)
                    acc_con_ids = conci_obj.search(cr, uid, [('id', '=', concil_id)], order='name')
                    acc_con_obj =  conci_obj.browse(cr, uid, acc_con_ids)
                    for con_gr in acc_con_obj:
                        vals_line_g = {
                                 'name': con_gr.name,
                                 'amount': round(con_gr.valor_bruto, 2),
                                 'amount_conc': 0.00,
                                 'amount_pendiente': round(con_gr.valor_bruto, 2),
                                 'conciliation_id': id_grop,
                                 'journal_id': con_gr.journal_id.id,
                                 'ref': con_gr.poss_id.name,
                                 'user_id': con_gr.user_id.id,
                                 'lote': con_gr.lote,
                                 'company_id': con_gr.company_id.id,
                                 'amount_comision': round(con_gr.valor_comision, 2),
                                 'amount_iva_retenido': round(con_gr.valor_iva, 2),
                                 'amount_irf_retenido': round(con_gr.valor_irf, 2),
                                 'amount_neto': round(con_gr.valor_neto ,2)
                        }
                        print "***vals conciliation line***: ", vals_line_g
                        concil_line_id = conci_lin_obj.create(cr, uid, vals_line_g)
            else:
                raise osv.except_osv("Advertencia", 'No existe ventas para esta fecha')

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
        'lote':fields.char('Lote', size=64, required=False, readonly=False),
        #'type_pv':fields.selection([('matriz', 'Matriz'), ('12oct', '12 Octubre'), ('guayaquil', 'Guayaquil')], 'Punto Venta', required=True),
        'type_pv' :fields.many2one('account.journal','Tipo Tarjeta' , domain="[('is_fo_pa','=',True)]"),
        'type_user' :fields.many2one('res.users','Tienda Responsable'),
    }
account_conciliation_tarjet()