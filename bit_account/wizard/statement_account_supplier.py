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
from dateutil.relativedelta import relativedelta
import unicodedata
from openerp.tools import float_compare
import xlwt as pycel #Libreria que Exporta a Excel
import cStringIO

import logging
_logger = logging.getLogger(__name__)

class statement_account_supplier(models.TransientModel):
    _name = "statement.account.supplier"

    company_id = fields.Many2one('res.company', 'Compania', required=True)
    datefrom = fields.Date('Fecha desde', required=True)
    dateto = fields.Date('Fecha hasta', required=True)
    summary = fields.Boolean(string='Resumen')
    partner_ids = fields.Many2many('res.partner', string='Proveedor')
    account_id = fields.Many2one('account.account', 'Cuenta')


    @api.model
    def default_get(self, fields_list):
        res = super(statement_account_supplier, self).default_get(fields_list)
        user = self.env['res.users'].browse(self._uid)
        res['company_id'] = user.company_id.id
        return res

    @api.multi
    def generar(self):

        wb = pycel.Workbook(encoding='utf-8')

        style_cabecera = pycel.easyxf('font: colour black, bold True;'
                                      'align: vertical center, horizontal center;'
                                      )
        style_partner = pycel.easyxf('font: colour black;'
                                      'align: vertical center, horizontal left;'
                                      )
        style_header = pycel.easyxf('font: bold True;'
                                    'align: vertical center, horizontal center, wrap on;'
                                    'borders: left 1, right 1, top 1, bottom 1;')

        linea = pycel.easyxf('borders:bottom 1;')

        linea_izq = pycel.easyxf('font: colour black, height 150;'
                                 'align: vertical center, horizontal left, wrap on;'
                                 )

        linea_izq_red = pycel.easyxf('font: bold True, colour blue, height 150;'
                                     'align: vertical center, horizontal left, wrap on;'
                                     )

        linea_der = pycel.easyxf('font: colour black, height 150;'
                                 'align: vertical center, horizontal right;'
                                 )

        linea_der_blue = pycel.easyxf('font: colour blue, height 150, bold True;'
                                     'align: vertical center, horizontal right;'
                                     )
        company = self.company_id

        ws = wb.add_sheet('Facturas Proveedores')
        ws.show_grid = False
        ws.header_str = u"&LFecha de Impresion: &D Hora: &T&RPagina &P de &N"
        ws.footer_str = u""

        ws.write_merge(1, 1, 1, 7, company.name, style_cabecera)
        ws.write_merge(2, 2, 1, 7, 'Direccion: ' + company.partner_id.street, style_cabecera)
        ws.write_merge(3, 3, 1, 7, 'Ruc: ' + company.partner_id.part_number, style_cabecera)
        ws.write_merge(5, 5, 1, 7, 'Historial estado de cta clientes  '+ self.datefrom + ' AL ' + self.dateto, style_cabecera)
        ws.write_merge(6, 6, 1, 7,'Fecha Impresion: '+ datetime.today().strftime('%Y-%m-%d'), style_cabecera)

        xi = 8  # Cabecera de Cliente
        ws.write(xi, 1, 'No. Factura', style_header)
        ws.write(xi, 2, 'Tipo Documento', style_header)
        ws.write(xi, 3, 'No. Transaccion', style_header)
        ws.write(xi, 4, 'Fecha factura', style_header)
        ws.write(xi, 5, 'Fecha vencimiento', style_header)
        ws.write(xi, 6, 'No. Asiento', style_header)
        ws.write(xi, 7, 'Detalle', style_header)
        ws.write(xi, 8, 'Debito', style_header)
        ws.write(xi, 9, 'Credito', style_header)
        ws.write(xi, 10, 'Saldo', style_header)

        ws.row(xi).height = 500
        xi += 1

        supplier = self.get_supplier(self.dateto)[0]
        sumdebitall = 0
        sumceditall = 0
        sumsaldoall = 0
        for supp in supplier:
            invoice_line = self.get_lines(supp.get('id'),self.datefrom, self.dateto,supp.get('account'))[0][0]
            if invoice_line:
                ws.write_merge(xi, xi, 1, 7, supp.get('ruc') + ' - ' + supp.get('name'), style_partner)
                if self.summary !=  True:
                    xi += 1
                sumdebitgroup = 0
                sumceditgroup = 0
                sumsaldogroup = 0
                for line in invoice_line:
                    if self.summary != True:
                        ws.write(xi, 1, line.get('invoicenumber'), linea_izq)
                        ws.write(xi, 2, line.get('documenttype'), linea_izq)
                        ws.write(xi, 3, line.get('transacctionnumber'), linea_izq)
                        ws.write(xi, 4, line.get('date'), linea_izq)
                        ws.write(xi, 5, line.get('duedate'), linea_izq)
                        ws.write(xi, 6, line.get('journal'), linea_izq)
                        ws.write(xi, 7, line.get('description'), linea_izq)
                        ws.write(xi, 8, line.get('debit'), linea_der)
                        ws.write(xi, 9, line.get('credit'), linea_der)
                        ws.write(xi, 10, line.get('saldo'), linea_der)
                        xi += 1


                    sumdebitgroup += line.get('debit')
                    sumceditgroup += line.get('credit')
                    sumsaldogroup += round(sumdebitgroup,2) - round(sumceditgroup,2)

                ws.write_merge(xi, xi, 8, 8, sumdebitgroup, linea_der_blue)
                ws.write_merge(xi, xi, 9, 9, sumceditgroup, linea_der_blue)
                ws.write_merge(xi, xi, 10, 10, round(sumdebitgroup,2) - round(sumceditgroup,2), linea_der_blue)

                ws.row(xi).height = 500
                xi += 1
                sumdebitall += sumdebitgroup
                sumceditall += sumceditgroup
                sumsaldoall += sumdebitall - sumceditall

        ws.write(xi, 8, sumdebitall, linea_der_blue)
        ws.write(xi, 9, sumceditall, linea_der_blue)
        ws.write(xi, 10, round(sumdebitall,2) - round(sumceditall,2), linea_der_blue)
        ws.row(xi).height = 500

        ws.col(0).width = 2000
        ws.col(1).width = 5000
        ws.col(2).width = 7000
        ws.col(3).width = 5000
        ws.col(4).width = 3000
        ws.col(5).width = 3000
        ws.col(6).width = 5000
        ws.col(7).width = 9000
        ws.col(8).width = 3000
        ws.col(9).width = 3000
        ws.col(10).width = 3000

        try:
            buf = cStringIO.StringIO()

            wb.save(buf)
            out = base64.encodestring(buf.getvalue())
            buf.close()

            data_fname = "Historial cuenta proveedores.xls"

            archivo = '/opt/temp/' + data_fname
            res_model = 'statement.account.supplier'
            self.load_doc(out, data_fname, res_model)

            return self.write({'data': out, 'txt_filename': data_fname, 'name': data_fname})
        except ValueError:
            raise Warning('Error a la hora de salvar el archivo')

    @api.one
    def get_supplier(self,dateto):
        parnert_list = []
        query = {}
        partner_id = []
        cuent = []
        user = self.env['res.users'].browse(self._uid)
        company_id= user.company_id.id
        account_id = self.account_id
        if self.partner_ids:
            partner_id = [part.id for part in self.partner_ids]
        account_obj = self.env['account.account'].search([('id','=',account_id.id)])    #   (account_id.id,['type'])
        if account_obj['type'] == 'view':
            sqlaccount = "SELECT id FROM account_account WHERE parent_id in (%s)"%(account_id.id)
            self._cr.execute(sqlaccount)
            cuent1 = self._cr.dictfetchall()
            for ct in cuent1:
                cuent.append(ct['id'])
        elif account_obj['type']== 'payable':
            cuent.append(account_id.id)

        # if partner_id:
        #
        #     sql = "select a.part_number, a.id, a.name from res_partner a where a.supplier = True and a.part_number is not null and a.id in (%s) " \
        #           "group by a.part_number, a.id, a.name order by a.name" %\
        #           (','.join(str(i) for i in partner_id))
        # else:
        #     sql = "select a.part_number, a.id, a.name from res_partner a where a.supplier = True and a.part_number is not null " \
        #           "group by a.part_number, a.id, a.name order by a.name"
        #
        # print "sql ", sql
        # self._cr.execute(sql)
        # supplier = self._cr.dictfetchall()
        #
        # for supp in supplier:
        #     list = {}
        #     list['id'] = supp['id']
        #     list['name'] = supp['name']
        #     list['ruc'] = supp['part_number']
        #     list['company_id'] = company_id
        #     parnert_list.append(list)

        if len(cuent) <= 0:
             raise except_orm('Error!', 'Cuenta contable no tiene configuracion para reporte cuentas por cobrar (view, receivable)')

        if partner_id:
            partner = self.env['res.partner'].search([('property_account_payable','in',cuent),('supplier','=', True),('id','in', partner_id)])

        else:
            partner = self.env['res.partner'].search([('property_account_payable','in',cuent),('supplier','=', True)])

        for supp in partner:
            list = {}
            list['id'] = supp.id
            list['name'] = supp.name or 'S/N'
            list['ruc'] = supp.part_number or 'S/R'
            list['account'] = supp.property_account_payable.id or 'S/A'
            parnert_list.append(list)

        return parnert_list

    @api.one
    def get_lines(self,partner, datefrom, dateto, account):
        where = []
        list = []
        invoice_list = []
        whereprov = []
        if datefrom:
            where.append(('date_invoice','>=',datefrom))
            whereprov.append(('date_invoice','>=',datefrom))
        if dateto:
            where.append(('date_invoice','<=',dateto))
            whereprov.append(('date_invoice','<=',dateto))
        if where:
            where.append(('state','in',['open','paid']))
            where.append(('type', 'in', ['in_invoice','in_refund']))
            where.append(('partner_id','=',partner))
            lines_invoice = self.env['account.invoice'].search(where,order='number_seq asc')
            saldo = 0.00

            #Factura de provisiones
            whereprov.append(('type','in',['in_invoice']))
            whereprov.append(('partner_id','=',partner))
            whereprov.append(('state_provision','in',['prov','rever']))
            lines_invoice_prov =  self.env['account.invoice'].search(whereprov,order='number_seq asc')

            #Saldos Iniciales
            # saldo += self.get_saldo(partner, datetime.strptime('2016-01-01','%Y-%m-%d'), datefrom)
            saldo += self.get_saldo(partner, '2016-01-01', datefrom, account)
            if saldo != 0:
                saldolist = {}
                saldolist['id'] = 1
                saldolist['documenttype'] = 'SALDOS INICIALES'
                saldolist['invoicenumber'] = ''
                saldolist['transacctionnumber'] = ''
                saldolist['date'] = self.datefrom
                saldolist['duedate'] = ''
                saldolist['journal'] = ''
                saldolist['description'] = ''
                if saldo > 0:
                    saldolist['debit'] = saldo
                    saldolist['credit'] = 0.00
                elif saldo < 0:
                    saldolist['debit'] = 0.00
                    saldolist['credit'] = abs(saldo)
                elif saldo == 0:
                    saldolist['debit'] = saldo
                    saldolist['credit'] = saldo
                saldolist['saldo'] = round(saldo,2)
                invoice_list.append(saldolist)

            #Diarios de Saldo Inicial
            wherejournal = []
            company = self.company_id
            account_ids = [account] # [acc.id for acc in company.payable_ids]
            # account_ids.append([part.id for part in company.advsuppl_account_id])
            wherejournal.append(('account_id','in',account_ids))
            if where:
                wherejournal.append(('partner_id','=',partner))
                journal = self.env['account.journal'].search([('code','=', 'DSIN')])
                wherejournal.append(('journal_id','=',journal.id))
                moves = self.env['account.move.line'].search(wherejournal, order="partner_id asc, date_created asc")
                for mov in moves:
                    if  mov.move_id.date <= dateto and mov.move_id.date >= datefrom :
                        movlist = {}
                        movlist['id'] = mov.id
                        movlist['documenttype'] = mov.journal_id.name
                        movlist['invoicenumber'] = ''
                        movlist['transacctionnumber'] = ''
                        movlist['date'] = mov.move_id.date
                        movlist['duedate'] = ''
                        movlist['journal'] = mov.move_id.name
                        movlist['description'] = mov.name
                        movlist['debit'] = round(mov.debit,2)
                        movlist['credit'] = round(mov.credit,2)
                        saldo += round(movlist['debit'] - movlist['credit'],2)
                        movlist['saldo'] = round(saldo,2)
                        invoice_list.append(movlist)

                        wherereconcile = []
                        if mov.reconcile_id.id:
                            wherereconcile.append(('reconcile_id','=',mov.reconcile_id.id))
                        elif mov.reconcile_partial_id.id:
                            wherereconcile.append(('reconcile_partial_id','=',mov.reconcile_partial_id.id))
                        if wherereconcile:
                            partial_reconcile = self.env['account.move.line'].search(wherereconcile)
                            amount = 0
                            for parrec in  partial_reconcile:
                                if parrec.debit > 0 and parrec.move_id.date <= dateto and parrec.move_id.date >= datefrom:
                                    parlist = {}
                                    parlist['id'] = parrec.id
                                    parlist['documenttype'] = parrec.journal_id.name
                                    parlist['invoicenumber'] = ''
                                    parlist['transacctionnumber'] = ''
                                    parlist['date'] = parrec.move_id.date
                                    parlist['duedate'] = ''
                                    parlist['journal'] = parrec.move_id.name
                                    parlist['description'] = parrec.ref
                                    parlist['debit'] = abs(round(parrec.debit,2))
                                    parlist['credit'] = abs(round(parrec.credit,2))
                                    saldo += round(parlist['debit'],2)
                                    parlist['saldo'] = round(saldo,2)
                                    invoice_list.append(parlist)

            #Add Pagos de diarios, retenciones, pagos mayor a la fecha de la factura
            # invoice_after = self.get_lines_after(partner,datetime.strptime('2016-01-01','%Y-%m-%d'), datefrom,)[0]
            # invoice_after = self.get_lines_after(partner, datetime.strptime('2016-01-01','%Y-%m-%d'), self.datefrom)[0]
            invoice_after = self.get_lines_after(partner, '2016-01-01', self.datefrom, account)[0]
            for invaft in invoice_after:
                invaftlis = {}
                invaftlis['id'] = invaft.get('id')
                invaftlis['documenttype'] = invaft.get('documenttype')
                invaftlis['invoicenumber'] = invaft.get('invoicenumber')
                invaftlis['transacctionnumber'] = invaft.get('transacctionnumber')
                invaftlis['date'] = invaft.get('date')
                invaftlis['duedate'] = invaft.get('duedate')
                invaftlis['journal'] = invaft.get('journal')
                invaftlis['description'] = invaft.get('description')
                invaftlis['debit'] = invaft.get('debit')
                invaftlis['credit'] = invaft.get('credit')
                saldo += round(invaftlis['debit'] - invaftlis['credit'],2)
                invaftlis['saldo'] = saldo
                invoice_list.append(invaftlis)

            invoice_order = []
            for line in lines_invoice:
                invoice_order.append({'id':line.id, 'date_invoice':line.date_invoice, 'type':'F'})

            for lineprov in lines_invoice_prov:
                if lineprov.prov_id:
                    invoice_order.append({'id':lineprov.id, 'date_invoice': lineprov.prov_id.date, 'type':'P'})

            if invoice_order:
                invoice_order.sort(key=lambda x: x['date_invoice'])

            #Facturas Normales
            for invord in invoice_order:
                if invord['type'] == 'F':
                    lines_invoice = self.env['account.invoice'].search([('id','=', invord['id'])])
                    for line in lines_invoice:
                        invlist = {}
                        invlist['id'] = line.id
                        invlist['documenttype'] = line.document_type.name
                        invlist['invoicenumber'] = line.number_seq
                        invlist['transacctionnumber'] = line.number_seq
                        invlist['date'] = line.date_invoice
                        invlist['duedate'] = line.date_due
                        invlist['journal'] = line.move_id.name
                        invlist['description'] = str(line.move_id.name)
                        if line.type == 'in_invoice':
                            invlist['debit'] = 0.00
                            v_taxes = self._get_supplier_iva_taxes(line.id)
                            invlist['credit'] = v_taxes['amount_total_iva']  #round(line.amount_total_iva,2)
                        elif line.type == 'in_refund':
                            invlist['debit'] = round(line.amount_total,2)
                            invlist['credit'] = 0.00
                        saldo += round(invlist['debit'] - invlist['credit'],2)
                        invlist['saldo'] = saldo
                        invoice_list.append(invlist)

                        #Asume retencion de la factura
                        # if line.is_asum and line.account_retiva:
                        #     move = self.env['account.move.line'].search([('move_id','=',line.move_id.id),('account_id','=',line.account_retiva.id)])
                        #     if move:
                        #         invasum = {}
                        #         invasum['id'] = move.id
                        #         invasum['documenttype'] = move.name
                        #         invasum['invoicenumber'] = '' #line.number_seq
                        #         invasum['transacctionnumber'] = line.number_seq
                        #         invasum['date'] = line.date_invoice
                        #         invasum['duedate'] = line.date_due
                        #         invasum['journal'] = line.move_id.name
                        #         invasum['description'] = move.name
                        #         invasum['debit'] = 0.00
                        #         invasum['credit'] = abs(round(move.debit,2))
                        #         saldo += round(invasum['debit'],2) - round(invasum['credit'],2)
                        #         invasum['saldo'] = saldo
                        #         invoice_list.append(invasum)


                        #Impuestos
                        deduction = self.env['account.deduction'].search([('id','=',line.deduction_id.id),('state','in',['open','paid']),('emission_date','<=',dateto)])
                        if deduction:
                            taxinvoice = self.env['account.invoice.tax'].search([('deduction_id','=',deduction.id),])
                            for tax in taxinvoice:
                                taxeslist = {}
                                taxeslist['id'] = tax.id
                                taxeslist['documenttype'] =  'Retencion a proveedores' if deduction.type == 'supplier'  else '----'
                                taxeslist['invoicenumber'] = '' #line.number_seq
                                taxeslist['transacctionnumber'] = deduction.number
                                taxeslist['date'] = deduction.emission_date
                                taxeslist['duedate'] = deduction.emission_date
                                taxeslist['journal'] = deduction.move_id.name
                                taxeslist['description'] = tax.name
                                taxeslist['debit'] = abs(round(tax.tax_amount,2))
                                taxeslist['credit'] = 0.00
                                saldo += round(taxeslist['debit'] - taxeslist['credit'],2)
                                taxeslist['saldo'] = saldo
                                invoice_list.append(taxeslist)
                        #Pagos
                        for pay in line.payment_ids.sorted(reverse= True):
                            if pay.date <= dateto:
                                paylist = {}
                                paylist['id'] = pay.id
                                paylist['documenttype'] =  'Pagos'
                                paylist['invoicenumber'] = '' #line.number_seq
                                paylist['transacctionnumber'] = str(pay.id) + ' - ' + pay.reconcile_id.name if pay.reconcile_id else pay.reconcile_partial_id.name
                                paylist['date'] = pay.date
                                paylist['duedate'] = pay.date
                                paylist['journal'] = pay.move_id.name
                                paylist['description'] = pay.ref
                                paylist['debit'] = round(pay.debit,2)
                                paylist['credit'] = round(pay.credit,2)
                                saldo += round(paylist['debit'] - paylist['credit'],2)
                                paylist['saldo'] = round(saldo,2)
                                invoice_list.append(paylist)
                elif invord['type'] == 'P':
                    lines_invoice_prov = self.env['account.invoice'].search([('id','=', invord['id'])])
                    #Factura de Provision y Reverso
                    for lineprov in lines_invoice_prov:
                        if lineprov.prov_id:
                            invlistprov = {}
                            invlistprov['id'] = lineprov.id
                            invlistprov['documenttype'] = lineprov.document_type.name + '-' + 'Prov'
                            invlistprov['invoicenumber'] = lineprov.prov_id.name
                            invlistprov['transacctionnumber'] = lineprov.prov_id.name
                            invlistprov['date'] = lineprov.prov_id.date
                            invlistprov['duedate'] = lineprov.date_due
                            invlistprov['journal'] = lineprov.prov_id.name
                            invlistprov['description'] = lineprov.comment
                            invlistprov['debit'] = 0.00
                            invlistprov['credit'] = round(lineprov.amount_total,2)
                            saldo += round(invlistprov['debit'] - invlistprov['credit'],2)
                            invlistprov['saldo'] = saldo
                            invoice_list.append(invlistprov)
                        if lineprov.provrev_id:
                            if lineprov.provrev_id.date >= datefrom and lineprov.provrev_id.date <= dateto:
                                invlistprov = {}
                                invlistprov['id'] = lineprov.id
                                invlistprov['documenttype'] = lineprov.document_type.name + '-' + 'Rev'
                                invlistprov['invoicenumber'] = lineprov.provrev_id.name
                                invlistprov['transacctionnumber'] = lineprov.provrev_id.name
                                invlistprov['date'] = lineprov.provrev_id.date
                                invlistprov['duedate'] = lineprov.date_due
                                invlistprov['journal'] = lineprov.provrev_id.name
                                invlistprov['description'] = lineprov.comment
                                invlistprov['debit'] = round(lineprov.amount_total,2)
                                invlistprov['credit'] = 0.00
                                saldo += round(invlistprov['debit'] - invlistprov['credit'],2)
                                invlistprov['saldo'] = saldo
                                invoice_list.append(invlistprov)


            list.append(invoice_list)
            list.append(saldo)


            return list

    @api.one
    def get_lines_after(self,partner, datefrom, dateto, account):
        where = []
        list = []
        invoice_list = []
        whereprov = []
        if datefrom:
            where.append(('date_invoice','>=',datefrom))
            whereprov.append(('date_invoice','>=',datefrom))
        if dateto:
            where.append(('date_invoice','<',dateto))
            whereprov.append(('date_invoice','<',dateto))
        if where:
            where.append(('state','in',['open','paid']))
            where.append(('type', 'in', ['in_invoice','in_refund']))
            where.append(('partner_id','=',partner))
            lines_invoice = self.env['account.invoice'].search(where,order='number_seq asc')
            saldo = 0.00

            #Factura de provisiones
            whereprov.append(('type','in',['in_invoice']))
            whereprov.append(('partner_id','=',partner))
            whereprov.append(('state_provision','in',['prov','rever']))
            lines_invoice_prov =  self.env['account.invoice'].search(whereprov,order='number_seq asc')

            #Diarios de Saldo Inicial
            wherejournal = []

            company = self.company_id

            account_ids = [account] #[acc.id for acc in company.payable_ids]
            # account_ids.append([part.id for part in company.advsuppl_account_id])
            wherejournal.append(('account_id','in',account_ids))
            if where:
                wherejournal.append(('partner_id','=',partner))
                journal = self.env['account.journal'].search([('code','=', 'DSIN')])
                wherejournal.append(('journal_id','=',journal.id))
                moves = self.env['account.move.line'].search(wherejournal, order="partner_id asc, date_created asc")
                for mov in moves:
                    if mov.move_id.date < dateto and mov.move_id.date >= datefrom :
                        wherereconcile = []
                        if mov.reconcile_id.id:
                            wherereconcile.append(('reconcile_id','=',mov.reconcile_id.id))
                        elif mov.reconcile_partial_id.id:
                            wherereconcile.append(('reconcile_partial_id','=',mov.reconcile_partial_id.id))
                        if wherereconcile:
                            partial_reconcile = self.env['account.move.line'].search(wherereconcile)
                            amount = 0
                            for parrec in  partial_reconcile:
                                if parrec.debit > 0 and parrec.move_id.date >= dateto   :
                                    parlist = {}
                                    parlist['id'] = parrec.id
                                    parlist['documenttype'] = parrec.journal_id.name
                                    parlist['invoicenumber'] = ''
                                    parlist['transacctionnumber'] = ''
                                    parlist['date'] = parrec.move_id.date
                                    parlist['duedate'] = ''
                                    parlist['journal'] = parrec.move_id.name
                                    parlist['description'] = parrec.ref
                                    parlist['debit'] = round(parrec.debit,2)
                                    parlist['credit'] = round(parrec.credit,2)
                                    saldo += round(parlist['debit'],2)
                                    parlist['saldo'] = round(saldo,2)
                                    invoice_list.append(parlist)

            #Facturas
            for line in lines_invoice:

                #Asume retencion de la factura
                # if line.is_asum and line.account_retiva:
                #     move = self.env['account.move.line'].search([('move_id','=',line.move_id.id),('account_id','=',line.account_retiva.id)])
                #     if move:
                #         invasum = {}
                #         invasum['id'] = move.id
                #         invasum['documenttype'] = move.name
                #         invasum['invoicenumber'] = '' #line.number_seq
                #         invasum['transacctionnumber'] = line.number_seq
                #         invasum['date'] = line.date_invoice
                #         invasum['duedate'] = line.date_due
                #         invasum['journal'] = line.move_id.name
                #         invasum['description'] = move.name
                #         invasum['debit'] = 0.00
                #         invasum['credit'] = abs(round(move.debit,2))
                #         saldo += round(invasum['debit'],2) - round(invasum['credit'],2)
                #         invasum['saldo'] = saldo
                #         invoice_list.append(invasum)

                #Impuestos
                deduction = self.env['account.deduction'].search([('id','=',line.deduction_id.id),('state','in',['open','paid']),('emission_date','>=',dateto)])
                if deduction:
                    taxinvoice = self.env['account.invoice.tax'].search([('deduction_id','=',deduction.id),])
                    for tax in taxinvoice:
                        taxeslist = {}
                        taxeslist['id'] = tax.id
                        taxeslist['documenttype'] =  'Retencion a proveedores' if deduction.type == 'supplier'  else '----'
                        taxeslist['invoicenumber'] = line.number_seq
                        taxeslist['transacctionnumber'] = deduction.number
                        taxeslist['date'] = deduction.emission_date
                        taxeslist['duedate'] = deduction.emission_date
                        taxeslist['journal'] = deduction.move_id.name
                        taxeslist['description'] = tax.name
                        taxeslist['debit'] = abs(round(tax.tax_amount,2))
                        taxeslist['credit'] = 0.00
                        saldo += round(taxeslist['debit'] - taxeslist['credit'],2)
                        taxeslist['saldo'] = saldo
                        invoice_list.append(taxeslist)

                #Pagos
                for pay in line.payment_ids.sorted(reverse= True):
                    if pay.date >= dateto:
                        paylist = {}
                        paylist['id'] = pay.id
                        paylist['documenttype'] =  'Pagos'
                        paylist['invoicenumber'] = line.number_seq
                        paylist['transacctionnumber'] = str(pay.id) + ' - ' + pay.reconcile_id.name if pay.reconcile_id else pay.reconcile_partial_id.name
                        paylist['date'] = pay.date
                        paylist['duedate'] = pay.date
                        paylist['journal'] = pay.move_id.name
                        paylist['description'] = pay.ref
                        paylist['debit'] = round(pay.debit,2)
                        paylist['credit'] = round(pay.credit,2)
                        saldo += round(paylist['debit'] - paylist['credit'],2)
                        paylist['saldo'] = round(saldo,2)
                        invoice_list.append(paylist)

            #Factura de Provision y Reverso
            for lineprov in lines_invoice_prov:
                if lineprov.state_provision == 'rever' and lineprov.provrev_id:
                    if lineprov.provrev_id.date >= dateto:
                        invlistprov = {}
                        invlistprov['id'] = lineprov.id
                        invlistprov['documenttype'] = lineprov.document_type.name + '-' + 'Rev'
                        invlistprov['invoicenumber'] = lineprov.provrev_id.name
                        invlistprov['transacctionnumber'] = lineprov.provrev_id.name
                        invlistprov['date'] = lineprov.provrev_id.date
                        invlistprov['duedate'] = lineprov.date_due
                        invlistprov['journal'] = lineprov.provrev_id.name
                        invlistprov['description'] = lineprov.comment
                        invlistprov['debit'] = round(lineprov.amount_total,2)
                        invlistprov['credit'] = 0.00
                        saldo += round(invlistprov['debit'] - invlistprov['credit'],2)
                        invlistprov['saldo'] = saldo
                        invoice_list.append(invlistprov)

            return invoice_list

    def get_saldo(self,partner, datefrom, dateto, account):
        where = []
        list = []
        invoice_list = []
        whereprov = []
        if datefrom:
            where.append(('date_invoice','>=',datefrom))
            whereprov.append(('date_invoice','>=',datefrom))
        if dateto:
            where.append(('date_invoice','<',dateto))
            whereprov.append(('date_invoice','<',dateto))
        if where:
            where.append(('state','in',['open','paid']))
            where.append(('type', 'in', ['in_invoice','in_refund']))
            where.append(('partner_id','=',partner))
            lines_invoice = self.env['account.invoice'].search(where,order='number_seq asc')
            saldo = 0.00

            whereprov.append(('type','in',['in_invoice']))
            whereprov.append(('partner_id','=',partner))
            whereprov.append(('state_provision','in',['prov','rever']))
            lines_invoice_prov =  self.env['account.invoice'].search(whereprov,order='number_seq asc')

            #Diarios de Saldo Inicial
            wherejournal = []

            company = self.company_id

            account_ids = [account] # [acc.id for acc in company.payable_ids]
            # account_ids.append([part.id for part in company.advsuppl_account_id])
            wherejournal.append(('account_id','in',account_ids))
            if where:
                wherejournal.append(('partner_id','=',partner))
                journal = self.env['account.journal'].search([('code','=', 'DSIN')])
                wherejournal.append(('journal_id','=',journal.id))
                moves = self.env['account.move.line'].search(wherejournal, order="partner_id asc, date_created asc")
                for mov in moves:
                    if  mov.move_id.date < dateto and mov.move_id.date >= datefrom :
                        saldo += round(mov.debit - mov.credit,2)
                        wherereconcile = []
                        if mov.reconcile_id.id:
                            wherereconcile.append(('reconcile_id','=',mov.reconcile_id.id))
                        elif mov.reconcile_partial_id.id:
                            wherereconcile.append(('reconcile_partial_id','=',mov.reconcile_partial_id.id))
                        if wherereconcile:
                            partial_reconcile = self.env['account.move.line'].search(wherereconcile)
                            amount = 0
                            for parrec in  partial_reconcile:
                                if parrec.debit > 0 and parrec.move_id.date < dateto and parrec.move_id.date >= datefrom   :
                                    saldo += round(parrec.debit,2)

            #Facturas
            for line in lines_invoice:
                # saldo += round(0.00 - line.amount_total,2)
                if line.type == 'in_invoice':
                    v_taxes = self._get_supplier_iva_taxes(line.id)
                    saldo += round(0.00 - v_taxes['amount_total_iva'],2)
                elif line.type == 'in_refund':
                    saldo += round(round(line.amount_total,2) - 0.00,2)
                #Impuestos
                deduction = self.env['account.deduction'].search([('id','=',line.deduction_id.id),('state','in',['open','paid']),('emission_date','<',dateto)])
                if deduction:
                    taxinvoice = self.env['account.invoice.tax'].search([('deduction_id','=',deduction.id),])
                    for tax in taxinvoice:
                        saldo += round(tax.tax_amount - 0.00,2)
                #Pagos
                for pay in line.payment_ids.sorted(reverse= True):
                    if pay.date < dateto:
                        saldo += round(pay.debit - pay.credit,2)
            #Factura de Provision y Reverso
            for lineprov in lines_invoice_prov:
                if lineprov.prov_id:
                    saldo += 0.00 - round(lineprov.amount_total,2)
                if lineprov.provrev_id:
                    if lineprov.provrev_id.date < dateto:
                        saldo += round(lineprov.amount_total,2) - 0.00

            return saldo


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

    def _get_supplier_iva_taxes(self,id):
        # Inicializo las variables que necesito devolver
        subtotal = tax_iva = amount_other = base_sin_iva = base_iva = 0.0
        res = {}
        invoice_list = self.env['account.invoice'].search([('id','=',id)])
        for invoice in invoice_list:
            for line in invoice.invoice_line:
                if line.price_subtotal:
                    for tax in line.invoice_line_tax_id:
                        value = 0
                        if tax.child_ids:   # Para los que tengan hijos
                            for c in tax.child_ids:
                                value += tax.amount * c.amount * line.price_subtotal
                        else:
                            value = tax.amount * line.price_subtotal
                        #CSV: IVA O FACTURAS COMPRAS
                        if tax.is_iva and  not tax.description == '507' and line.invoice_id.type == 'in_invoice':
                            tax_iva += value  # IVA siempre es solo 1
                            base_iva += line.price_subtotal
                        elif tax.description == '507' and line.invoice_id.type == 'in_invoice':
                            base_sin_iva += line.price_subtotal
                        else:
                            amount_other += value # Sumo el resto de los taxes
                        #CSV: IVA O FACTURAS VENTAS
                        if tax.is_iva and  not tax.description == '403' and line.invoice_id.type == 'out_invoice':
                            tax_iva += value  # IVA siempre es solo 1
                            base_iva += line.price_subtotal
                        elif tax.description == '403' and line.invoice_id.type == 'out_invoice':
                            base_sin_iva += line.price_subtotal
                    subtotal += line.price_subtotal
            res = {
                                'base_iva'        : round(base_iva,2),
                                'base_sin_iva'        : round(base_sin_iva,2),
                                'amount_iva'        : round(tax_iva,2),
                                'amount_total_iva'  : round((subtotal + tax_iva ),2),
                                'amount_other'      : round(amount_other,2)
                              }
        return res
