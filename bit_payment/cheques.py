# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution - Ecuador
#    Copyright (C) 2014 BitConsultores (<http://http://bitconsultores-ec.com>).
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

from openerp import api, fields, models
from openerp.tools.translate import _
from openerp.exceptions import except_orm, Warning, RedirectWarning
import base64
import StringIO
from string import upper
from time import mktime
from datetime import datetime
import unicodedata
from openerp.tools import float_compare
import xlwt as pycel #Libreria que Exporta a Excel
import cStringIO


import logging
_logger = logging.getLogger(__name__)

class reporte_cheques(models.TransientModel):
    _name = "account.reporte_cheques"


    company_id = fields.Many2one('res.company', 'Compania', required=True)
    datefrom = fields.Date('Fecha desde', required=True)
    dateunto = fields.Date('Fecha hasta', required=True)
    statements_id = fields.Many2many('account.bank.statement', 'account_bankstatement_cheque', 'bankstatement_id', 'cheque_id', 'Statements')
    partner_ids = fields.Many2many('res.partner', string='Proveedor')
    journal_id = fields.Many2one('account.journal', 'Journal')

    @api.model
    def default_get(self, fields_list):
        res = super(reporte_cheques, self).default_get(fields_list)
        user = self.env['res.users'].browse(self._uid)
        res['company_id'] = user.company_id.id
        return res

    @api.multi
    def generar(self):

        wb = pycel.Workbook(encoding='utf-8')

        style_cabecera = pycel.easyxf('font: colour black, bold True;'
                                      'align: vertical center, horizontal center;'
                                      )
        style_header = pycel.easyxf('font: bold True;'
                                    'align: vertical center, horizontal center, wrap on;'
                                    'borders: left 1, right 1, top 1, bottom 1;')

        linea = pycel.easyxf('borders:bottom 1;')

        linea_izq = pycel.easyxf('font: colour black, height 150;'
                                 'align: vertical center, horizontal left, wrap on;'
                                 'borders: left 1, right 1, top 1, bottom 1;')

        linea_izq_red = pycel.easyxf('font: bold True, colour blue, height 150;'
                                     'align: vertical center, horizontal left, wrap on;'
                                     'borders: left 1, right 1, top 1, bottom 1;')

        linea_der = pycel.easyxf('font: colour black, height 150;'
                                 'align: vertical center, horizontal right;'
                                 'borders: left 1, right 1, top 1, bottom 1;')

        linea_der_red = pycel.easyxf('font: colour blue, height 150;'
                                     'align: vertical center, horizontal right;'
                                     'borders: left 1, right 1, top 1, bottom 1;')
        company = self.company_id

        ws = wb.add_sheet('Cheques')
        ws.show_grid = False
        ws.header_str = u"&LFecha de Impresion: &D Hora: &T&RPagina &P de &N"
        ws.footer_str = u""

        ws.write_merge(1, 1, 1, 7, company.name, style_cabecera)
        ws.write_merge(2, 2, 1, 7, 'Direccion: ' + company.partner_id.street, style_cabecera)
        ws.write_merge(3, 3, 1, 7, 'Ruc: ' + company.partner_id.part_number, style_cabecera)
        ws.write_merge(5, 5, 1, 7, 'REPORTE DE CHEQUES '+ self.datefrom + ' AL ' + self.dateunto, style_cabecera)
        ws.write_merge(6, 6, 1, 7,'Fecha Impresion: '+ datetime.today().strftime('%Y-%m-%d'), style_cabecera)

        xi = 8  # Cabecera de Cliente
        ws.write(xi, 1, 'Fecha', style_header)
        ws.write(xi, 2, 'No Cheque', style_header)
        ws.write(xi, 3, 'Banco', style_header)
        ws.write(xi, 4, 'Referencia', style_header)
        ws.write(xi, 5, 'Concepto', style_header)
        ws.write(xi, 6, 'Proveedor', style_header)
        ws.write(xi, 7, 'Beneficiario', style_header)
        ws.write(xi, 8, 'Estado', style_header)
        ws.write(xi, 9, 'Valor', style_header)
        ws.row(xi).height = 500
        xi += 1


        lines = self.get_lines()[0]
        print "lines " , lines
        # partner = 'false'
        # flat = 0
        initial = 0
        total = 0
        for check in lines:

            ws.write(xi, 1, check.get('date'), linea_izq)
            ws.write(xi, 2, check.get('nocheck'), linea_izq)
            ws.write(xi, 3, check.get('banco'), linea_izq)
            ws.write(xi, 4, check.get('reference'), linea_izq)
            ws.write(xi, 5, check.get('concept'), linea_izq)
            ws.write(xi, 6, check.get('partner'), linea_izq)
            ws.write(xi, 7, check.get('beneficiary'), linea_izq)
            ws.write(xi, 8, check.get('state'), linea_izq)
            ws.write(xi, 9, check.get('amount'), linea_der)
            initial += check.get('amount')
            total += check.get('amount')
            #Lo comentado agrupa por beneficario de cheque
            # if flat == 0:
            #     ws.write(xi, 1, check.get('date'), linea_izq)
            #     ws.write(xi, 2, check.get('nocheck'), linea_izq)
            #     ws.write(xi, 3, check.get('reference'), linea_izq)
            #     ws.write(xi, 4, check.get('concept'), linea_izq)
            #     ws.write(xi, 5, check.get('partner'), linea_izq)
            #     ws.write(xi, 6, check.get('beneficiary'), linea_izq)
            #     ws.write(xi, 7, check.get('state'), linea_izq)
            #     ws.write(xi, 8, check.get('amount'), linea_der)
            #     flat = 1
            #     partner = check.get('partner')
            #     initial += check.get('amount')
            #     total += check.get('amount')
            # else:
            #      if check.get('partner') != partner:
            #          ws.write(xi, 7, 'TOTAL', linea_izq_red)
            #          ws.write(xi, 8, initial, linea_der_red)
            #          xi += 2
            #          initial = 0
            #          ws.write(xi, 1, check.get('date'), linea_izq)
            #          ws.write(xi, 2, check.get('nocheck'), linea_izq)
            #          ws.write(xi, 3, check.get('reference'), linea_izq)
            #          ws.write(xi, 4, check.get('concept'), linea_izq)
            #          ws.write(xi, 5, check.get('partner'), linea_izq)
            #          ws.write(xi, 6, check.get('beneficiary'), linea_izq)
            #          ws.write(xi, 7, check.get('state'), linea_izq)
            #          ws.write(xi, 8, check.get('amount'), linea_der)
            #          partner = check.get('partner')
            #          initial += check.get('amount')
            #          total += check.get('amount')
            #      else:
            #          ws.write(xi, 1, check.get('date'), linea_izq)
            #          ws.write(xi, 2, check.get('nocheck'), linea_izq)
            #          ws.write(xi, 3, check.get('reference'), linea_izq)
            #          ws.write(xi, 4, check.get('concept'), linea_izq)
            #          ws.write(xi, 5, check.get('partner'), linea_izq)
            #          ws.write(xi, 6, check.get('beneficiary'), linea_izq)
            #          ws.write(xi, 7, check.get('state'), linea_izq)
            #          ws.write(xi, 8, check.get('amount'), linea_der)
            #          partner = check.get('partner')
            #          initial += check.get('amount')
            #          total += check.get('amount')

            xi += 1
        ws.write(xi, 8, 'TOTAL', linea_izq_red)
        ws.write(xi, 9, initial, linea_der_red)
        # xi += 2
        # ws.write(xi, 7, 'TOTAL GENERAL', linea_izq_red)
        # ws.write(xi, 8, total, linea_der_red)

        ws.col(0).width = 2000
        ws.col(1).width = 5000
        ws.col(2).width = 5000
        ws.col(3).width = 7000
        ws.col(4).width = 7000
        ws.col(5).width = 15000
        ws.col(6).width = 9000
        ws.col(7).width = 9000
        ws.col(8).width = 5000

        try:
            buf = cStringIO.StringIO()

            wb.save(buf)
            out = base64.encodestring(buf.getvalue())
            buf.close()

            data_fname = "reporte_cheques.xls" #"Cheques_%s.xls"

            archivo = '/opt/temp/' + data_fname
            res_model = 'account.reporte_cheques'
            self.load_doc(out, data_fname, res_model)

            return self.write({'data': out, 'txt_filename': data_fname, 'name': data_fname})
        except ValueError:
            raise Warning('Error a la hora de salvar el archivo')

    @api.one
    def get_lines(self):
        list = []
        where_st = []
        where_vo = []
        check = {}
        if self.partner_ids:
            where_st.append(('partner_id', 'in', [part.id for part in self.partner_ids]))
            where_vo.append(('partner_id', 'in', [part.id for part in self.partner_ids]))
        if self.datefrom:
            where_st.append(('date', '>=', self.datefrom))
            where_vo.append(('date', '>=', self.datefrom))
        else:
            raise except_orm('Error!!', 'Ingrese Fecha desde')
        if self.dateunto:
            where_st.append(('date', '<=', self.dateunto))
            where_vo.append(('date', '<=', self.dateunto))
        else:
            raise except_orm('Error!!', 'Ingrese Fecha hasta')
        where_st.append(('is_check','=','True'))
        where_st.append(('company_id', 'in', [part.id for part in self.company_id]))
        where_vo.append(('type','in',['advance','payment']))
        where_vo.append(('company_id', 'in', [part.id for part in self.company_id]))
        where_vo.append(('state','!=','draft'))
        # where_vo.append(('is_check','=','True'))
        if self.journal_id:
            where_vo.append(('journal_id','=',self.journal_id.id))
            where_st.append(('journal_id','=',self.journal_id.id))


        if where_st and where_vo:
            check_statement = self.env['account.bank.statement'].search(where_st, order='partner_id')
            for statement in check_statement:
                check = {}
                check['id'] = statement.id
                check['date'] = statement.date
                check['nocheck'] = statement.no_cheque or ''
                check['banco'] = statement.journal_id.name
                check['reference'] = statement.name
                check['concept'] = statement.concept
                if statement.partner_id.name:
                    check['partner'] = statement.partner_id.name or 'NO DEFINIDO'
                    check['beneficiary'] = statement.partner_id.name or 'NO DEFINIDO'
                else:
                    check_statement_line = self.env['account.bank.statement.line'].search([('statement_id','=',statement.id)],limit = 1)
                    for staline in check_statement_line:
                        check['partner'] = staline.partner_id.name or 'NO DEFINIDO'
                        check['beneficiary'] = staline.partner_id.name or 'NO DEFINIDO'

                check['amount'] = round(statement.balance_start,2)
                if statement.state == 'confirm':
                    check['state'] = 'Cerrado'
                elif statement.state == 'draft':
                    check['state'] = 'Borrador'
                else:
                    check['state']= 'No Definido'
                list.append(check)


            check_voucher = self.env['account.voucher'].search(where_vo, order='partner_id')
            for voucher in check_voucher:
                check = {}
                check['id'] = voucher.id
                check['date'] = voucher.date
                check['nocheck'] = voucher.name #voucher.name or ''
                check['banco'] = statement.journal_id.name
                check['reference'] = voucher.number
                if voucher.type == 'advance':
                    check['concept'] = voucher.narration or ''
                elif voucher.type == 'payment':
                    check['concept'] = voucher.reference or ''
                check['partner'] = voucher.partner_id.name or 'NO DEFINIDO'
                check['beneficiary'] = voucher.benef or voucher.partner_id.name or 'NO DEFINIDO'
                check['amount'] = round(voucher.amount,2)
                if voucher.state == 'posted':
                    check['state'] = 'Contablizado'
                elif voucher.state == 'cancel':
                    check['state'] = 'Cancelado'
                elif voucher.state == 'draft':
                    check['state'] = 'Borrador'
                else:
                    check['state']= 'No Definido'
                list.append(check)

        #list.sort(key=lambda x: x['date'] and x['partner']) para ordenar por beneficiario
        list.sort(key=lambda x: x['date'])
        return list

    @api.one
    def load_doc(self, out, data_fname, res_model):
        attach_vals = {
            'name': data_fname,
            'datas_fname': data_fname,
            'res_model': res_model,
             'datas': out,
            'type': 'binary',
            'file_type': 'file_type',
        }
        if self.id:
            attach_vals.update( {'res_id': self.id})
        self.env['ir.attachment'].create(attach_vals)
