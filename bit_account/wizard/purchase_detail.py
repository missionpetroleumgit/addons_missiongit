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

class purchase_detail(models.Model):
    _name = "purchase.detail"

    company_id = fields.Many2one('res.company', 'Compañia', required=True)
    datefrom = fields.Date('Fecha desde', required=True)
    dateto = fields.Date('Fecha hasta', required=True)
    partner_ids = fields.Many2many('res.partner', string='Proveedor')

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

        linea_der_blue = pycel.easyxf('font: colour blue, height 150, bold True;'
                                     'align: vertical center, horizontal right;'
                                     'borders: left 1, right 1, top 1, bottom 1;')
        company = self.company_id

        ws = wb.add_sheet('Detalle Facturas')
        ws.show_grid = False
        ws.header_str = u"&LFecha de Impresion: &D Hora: &T&RPagina &P de &N"
        ws.footer_str = u""

        ws.write_merge(1, 1, 1, 7, company.name, style_cabecera)
        ws.write_merge(2, 2, 1, 7, 'Direccion: ' + company.partner_id.street, style_cabecera)
        ws.write_merge(3, 3, 1, 7, 'Ruc: ' + company.partner_id.part_number, style_cabecera)
        ws.write_merge(5, 5, 1, 7, 'Detalle de Compras '+ self.datefrom + ' AL ' + self.dateto, style_cabecera)
        ws.write_merge(6, 6, 1, 7,'Fecha Impresion: '+ datetime.today().strftime('%Y-%m-%d'), style_cabecera)

        xi = 8  # Cabecera de Cliente
        ws.write(xi, 1, 'RUC', style_header)
        ws.write(xi, 2, 'Proveedor', style_header)
        ws.write(xi, 3, 'Tipo de contribuyente', style_header)
        ws.write(xi, 4, 'Tipo comprobante', style_header)
        ws.write(xi, 5, 'Asiento Contable', style_header)
        ws.write(xi, 6, 'Fecha factura', style_header)
        ws.write(xi, 7, 'No. Serie', style_header)
        ws.write(xi, 8, 'No. Comp', style_header)
        ws.write(xi, 9, 'Código de sustento', style_header)
        ws.write(xi, 10, 'Base imp. 0', style_header)
        ws.write(xi, 11, 'Base imp. grabada', style_header)
        ws.write(xi, 12, 'Iva Pagado', style_header)
        ws.write(xi, 13, 'Código Impuesto IVA', style_header)
        ws.write(xi, 14, 'Ret IVA', style_header)
        ws.write(xi, 15, 'Código Impuesto Ret IVA', style_header)
        ws.write(xi, 16, 'Ret RENTA', style_header)
        ws.write(xi, 17, 'Código Impuesto Ret Renta', style_header)
        ws.row(xi).height = 500
        xi += 1


        lines = self.get_lines()[0]
        sum_baseimp0 = 0
        sum_baseimpgrabada = 0
        sum_ivapagado = 0
        sum_retiva = 0
        sum_retrenta = 0
        for invoices in lines:
            ws.write(xi, 1, invoices.get('ruc'), linea_izq)
            ws.write(xi, 2, invoices.get('partner'), linea_izq)
            ws.write(xi, 3, invoices.get('typecontrib'), linea_izq)
            ws.write(xi, 4, invoices.get('typecomprob'), linea_izq)
            ws.write(xi, 5, invoices.get('asientocontable'), linea_izq)
            ws.write(xi, 6, invoices.get('dateinvoice'), linea_izq)
            ws.write(xi, 7, invoices.get('noserie'), linea_izq)
            ws.write(xi, 8, invoices.get('nocomp'), linea_der)
            ws.write(xi, 9, invoices.get('codsustent'), linea_der)
            ws.write(xi, 10, invoices.get('baseimp0'), linea_der)
            ws.write(xi, 11, invoices.get('baseimpgrabada'), linea_der)
            ws.write(xi, 12, invoices.get('ivapagado'), linea_der)
            ws.write(xi, 13, invoices.get('codimpivapag'), linea_der)
            ws.write(xi, 14, invoices.get('retiva'), linea_der)
            ws.write(xi, 15, invoices.get('codimpiva'), linea_der)
            ws.write(xi, 16, invoices.get('retrenta'), linea_der)
            ws.write(xi, 17, invoices.get('codimprenta'), linea_der)

            xi += 1
            sum_baseimp0 += invoices.get('baseimp0')
            sum_baseimpgrabada += invoices.get('baseimpgrabada')
            sum_ivapagado += invoices.get('ivapagado')
            sum_retiva += invoices.get('retiva')
            sum_retrenta += invoices.get('retrenta')


        ws.write(xi, 10, sum_baseimp0, linea_der_blue)
        ws.write(xi, 11, sum_baseimpgrabada, linea_der_blue)
        ws.write(xi, 12, sum_ivapagado, linea_der_blue)
        ws.write(xi, 13, '', linea_der_blue)
        ws.write(xi, 14, sum_retiva, linea_der_blue)
        ws.write(xi, 15, '', linea_der_blue)
        ws.write(xi, 16, sum_retrenta, linea_der_blue)
        ws.write(xi, 17, '', linea_der_blue)

        ws.col(0).width = 2000
        ws.col(1).width = 5000
        ws.col(2).width = 10000
        ws.col(3).width = 7000
        ws.col(4).width = 7000
        ws.col(5).width = 9000
        ws.col(6).width = 9000
        ws.col(8).width = 5000
        ws.col(9).width = 5000
        ws.col(10).width = 5000
        ws.col(11).width = 5000
        ws.col(12).width = 5000
        ws.col(13).width = 5000
        ws.col(14).width = 5000
        ws.col(15).width = 5000
        ws.col(16).width = 5000
        ws.col(17).width = 5000
        try:
            buf = cStringIO.StringIO()

            wb.save(buf)
            out = base64.encodestring(buf.getvalue())
            buf.close()

            data_fname = "Detalle-Compras.xls"

            archivo = '/opt/temp/' + data_fname
            res_model = 'purchase.detail'
            self.load_doc(out, data_fname, res_model)

            return self.write({'data': out, 'txt_filename': data_fname, 'name': data_fname})
        except ValueError:
            raise Warning('Error a la hora de salvar el archivo')

    @api.one
    def get_lines(self):

        where = []
        invoice_list = []

        if self.partner_ids:
            where.append(('partner_id','in',[part.id for part in self.partner_ids]))
        if self.datefrom:
            where.append(('date_invoice','>=',self.datefrom ))
        if self.dateto:
            where.append(('date_invoice','<=', self.dateto))
        if self.company_id:
            where.append(('company_id', 'in', [part.id for part in self.company_id]))
        where.append(('type','in',['in_invoice','in_refund']))
        where.append(('state','in',['open','paid']))
        print 'where ', where
        if where:
            invoice = self.env['account.invoice'].search(where, order='partner_id')
            for invo in invoice:
                invlist = {}
                invlist['id'] = invo.id
                invlist['ruc'] = invo.partner_id.part_number
                invlist['partner'] = invo.partner_id.name
                invlist['typecontrib'] = invo.fiscal_position.name
                invlist['typecomprob'] = invo.document_type.name
                invlist['asientocontable'] = invo.move_id.name
                invlist['dateinvoice'] = invo.date_invoice
                if invo.is_inv_elect == True and invo.type == 'in_invoice':
                    invlist['noserie'] = invo.number[0:7]
                else:
                    invlist['noserie'] = invo.authorization_id.serie_entity + invo.authorization_id.serie_emission
                invlist['nocomp'] = invo.number_seq
                invlist['codsustent'] = invo.tax_support.code
                invlist['base0bien'] = 0
                invlist['base0servicio'] = 0
                invlist['basegrbien'] = 0
                invlist['basegrservicio'] = 0
                invlist['ivabien'] = 0
                invlist['ivaservicio'] = 0
                invoice_tax = self.env['account.invoice.tax'].search([('invoice_id','=', invo.id)])
                ivacero = 0
                iva12 = 0
                retiva = 0
                retir = 0
                iva12pay = 0
                codeiva = ''
                coderenta = ''
                codeivacerodoce = ''
                for tax in invoice_tax:
		    
		    if tax.base_code_id.code:

                        if tax.base_code_id.code in ['500','512','510']:
                            if invo.type == 'in_refund':
                                iva12 += tax.base_amount
                                iva12pay += tax.tax_amount
                            else:
                                iva12 += abs(tax.base_amount)
                                iva12pay += abs(tax.tax_amount)
                            codeivacerodoce = codeivacerodoce + ' ' + tax.base_code_id.code
                        elif tax.base_code_id.code in ['507','541']:
                            ivacero += abs(tax.base_amount)
                            codeivacerodoce = codeivacerodoce + ' ' + tax.base_code_id.code
                        elif tax.base_code_id.code in ['725','721','723','729','731','727']:
                            retiva += abs(tax.tax_amount)
                            codeiva = codeiva + ' ' + tax.base_code_id.code
                        else:
                            retir += abs(tax.tax_amount)
                            coderenta = coderenta + ' ' + tax.base_code_id.code or ''

                invlist['baseimp0'] =  ivacero
                invlist['baseimpgrabada'] = iva12
                invlist['ivapagado'] = round(iva12pay,2)
                invlist['codimpivapag'] = codeivacerodoce
                invlist['retiva'] = retiva
                invlist['retrenta'] = retir
                invlist['codimpiva'] = codeiva
                invlist['codimprenta'] = coderenta

                invoice_list.append(invlist)

            invoice_list.sort(key=lambda x: x['dateinvoice'])
        return invoice_list

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
