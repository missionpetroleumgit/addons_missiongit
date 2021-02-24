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

import xlwt
from datetime import datetime
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT as DSTF
from openerp import models, fields, api
from openerp.exceptions import except_orm
from dateutil import parser
import xlwt as pycel
import base64
import cStringIO

class statement_account_customer(models.TransientModel):
    _name = "statement.account.customer"

    partner_ids = fields.Many2many('res.partner', string='Clientes/Proveedores')
    company_id = fields.Many2one('res.company', 'Company', required=True)
    period_length = fields.Integer('Longitud del periodo (dias)')
    type_export = fields.Selection([('xls', 'EXCEL')], 'Tipo de archivo', required=True)
    start_period = fields.Many2one('account.period', 'Periodo Inicial', required=True)
    end_period = fields.Many2one('account.period', 'Periodo Final', required=True)
    account_type = fields.Selection([('customer', 'Cuentas por Cobrar'), ('supplier', 'Cuentas por Pagar')], 'Cuentas')

    @api.model
    def default_get(self, fields_list):
        res = dict()
        type = False
        res['period_length'] = 30
        if 'supplier' in self._context:
            type = self._context.get('supplier')
        if type:
            res['account_type'] = 'supplier'
        else:
            res['account_type'] = 'customer'
        return res

    @api.multi
    def print_accounts_report(self):
        pass

    @api.one
    def get_lines(self):
        query = [('date_invoice', '>=', self.start_period.date_start),
                 ('date_invoice', '<=', self.end_period.date_stop), ('state', 'in', ('open', 'paid'))]
        query_noinvoice_moves = [('move_id.date', '>=', self.start_period.date_start), ('move_id.date', '<=', self.end_period.date_stop),
                                 ('move_id.state', '=', 'posted')]
        if self.partner_ids:
            query.append(('partner_id', 'in', [part.id for part in self.partner_ids]))
            query_noinvoice_moves.append(('partner_id', 'in', [part.id for part in self.partner_ids]))
        if self.account_type == 'supplier':
            query.append(('type', '=', 'in_invoice'))
            filtered = 'lambda l: l.credit > 0 and l.account_id == l.invoice.account_id'
            query_noinvoice_moves.extend([('credit', '>', 0), ('account_id.type', '=', 'payable')])
        elif self.account_type == 'customer':
            query.append(('type', 'in', ('out_invoice', 'out_refund')))
            filtered = 'lambda l: l.debit > 0'
            notes_filtered = 'lambda l: l.credit > 0 and l.account_id.code == "101020101" and not l.reconcile_id'
            query_noinvoice_moves.extend([('debit', '>', 0), ('account_id.type', '=', 'receivable')])
        if not query:
            raise except_orm('Error!!', 'No existen parametros para la busqueda')
        if not self.period_length:
            raise except_orm('Error!!', 'Defina longitud del periodo')

        invoices = self.env['account.invoice'].search(query, order='partner_id')
        invoice_move_lines = invoices.mapped('move_id').mapped('line_id').filtered(eval(filtered))
        refund_move_lines = invoices.mapped('move_id').mapped('line_id').filtered(eval(notes_filtered))
        query_noinvoice_moves.append(('id', 'not in', invoices.mapped('move_id').mapped('line_id').ids))
        move_lines = self.env['account.move.line'].search(query_noinvoice_moves, order='partner_id')
        return move_lines + invoice_move_lines + refund_move_lines

    def set_header(self, ws, xi, account_type, style_header, length):
        if account_type == 'customer':
            # ws.write(xi, 1, 'Cuenta Contable', style_header)
            ws.write(xi, 1, 'Cliente', style_header)
            ws.write(xi, 2, 'RUC', style_header)
            ws.write(xi, 3, 'No. Factura', style_header)
            ws.write(xi, 4, 'Fecha Factura', style_header)
            ws.write(xi, 5, 'Vencimiento', style_header)
            ws.write(xi, 6, 'DV', style_header)
            ws.write(xi, 7, 'Total', style_header)
            ws.write(xi, 8, 'Abono', style_header)
            ws.write(xi, 9, 'Saldo', style_header)
            col = 20
        elif account_type == 'supplier':
            ws.write(xi, 1, 'Cuenta Contable', style_header)
            ws.write(xi, 2, 'Proveedor', style_header)
            ws.write(xi, 3, 'RUC', style_header)
            ws.write(xi, 4, 'Documento', style_header)
            ws.write(xi, 5, 'Fecha de Caucacion', style_header)
            ws.write(xi, 6, 'Vencimiento', style_header)
            ws.write(xi, 7, 'Dias de Vencida', style_header)
            ws.write(xi, 8, 'Sin deuda', style_header)
            ws.write(xi, 9, ('0-' + str(length)), style_header)
            ws.write(xi, 10, (str(length) + '-' + str(2*length)), style_header)
            ws.write(xi, 11, (str(2*length) + '-' + str(3*length)), style_header)
            ws.write(xi, 12, (str(3*length) + '-' + str(4*length)), style_header)
            ws.write(xi, 13, '+' + str(4*length), style_header)
            ws.write(xi, 14, 'Total', style_header)
            ws.write(xi, 15, 'Observaciones', style_header)
            col = 15
        return col

    def get_ret_iva_fuente(self, line):
        iva = 0.00
        fuent = 0.00
        for tax_line in line.tax_line:
            if tax_line.account_id.code == '11050102':
                iva = tax_line.amount
            elif tax_line.account_id.code == '11050301':
                fuent = tax_line.amount
        return fuent, iva

    def get_iva(self, line):
        iva = 0.00
        for tax_line in line.tax_line:
            if tax_line.account_id.code in ('2010301', '1010501'):
                iva += tax_line.amount
        return iva

    def get_range(self, line, length):
        amount_0_30 = 0.00
        amount_30_60 = 0.00
        amount_60_90 = 0.00
        amount_90_120 = 0.00
        amount_gt_120 = 0.00
        residual = line.invoice and line.invoice.residual or line.company_id.currency_id.with_context(date=line.date). \
            compute(line.amount_residual, line.currency_id or line.company_id.currency_id)
        amount_gt_120 = residual
        return amount_0_30, amount_30_60, amount_60_90, amount_90_120, amount_gt_120

    def write_supplier_cells(self, v1, v2, v3, v4, v5, ws, xi, account, partner, number,
                             residual, amount_total, linea_izq, linea_der, date_due=False, date_cont=False):
        ws.write(xi, 1, (account.code + ' ' + account.name), linea_izq)
        ws.write(xi, 2, partner.name, linea_izq)
        ws.write(xi, 3, partner.part_number, linea_der)
        ws.write(xi, 4, number, linea_der)
        ws.write(xi, 5, date_cont or "", linea_der)
        ws.write(xi, 6, date_due or "", linea_der)
        ws.write(xi, 7, date_due and self.get_due_days(date_due) or "", linea_der)
        ws.write(xi, 8, amount_total - residual, linea_der)
        ws.write(xi, 9, v1, linea_der)
        ws.write(xi, 10, v2, linea_der)
        ws.write(xi, 11, v3, linea_der)
        ws.write(xi, 12, v4, linea_der)
        ws.write(xi, 13, v5, linea_der)
        ws.write(xi, 14, amount_total, linea_der)
        ws.write(xi, 15, 'Observaciones', linea_der)

    def write_customer_cells(self, ws, line, xi, v1, v2, v3, v4, v5, doc_date, date_due, doc_name, amount_untaxed,
                             amount_total, residual, linea_izq, linea_der, iva=0, ret_iva=0, ret_fuente=0):
        cost_centers = ""
        if line.invoice:
            analytics = []
            for invoice_line in line.invoice.invoice_line:
                if invoice_line.account_analytic_id:
                    analytics.append(invoice_line.account_analytic_id.name)
            if analytics:
                cost_centers = ','.join(analytics)
        # ws.write(xi, 1, (line.account_id.code + ' ' + line.account_id.name), linea_izq)
        ws.write(xi, 1, line.partner_id.name, linea_izq)
        ws.write(xi, 2, line.partner_id.part_number, linea_der)
        ws.write(xi, 3, doc_name, linea_der)
        ws.write(xi, 4, doc_date, linea_der)
        ws.write(xi, 5, date_due, linea_der)
        ws.write(xi, 6, self.get_due_days(date_due), linea_der)
        if line.credit > 0:
            ws.write(xi, 7, -v5, linea_der)
        if line.debit > 0:
            ws.write(xi, 7, line.debit, linea_der)
        if line.credit > 0:
            ws.write(xi, 8, '0', linea_der)
        if line.debit > 0:
            ws.write(xi, 8, line.debit - residual, linea_der)
        if line.debit > 0:
            ws.write(xi, 9, v5, linea_der)
        if line.credit > 0:
            ws.write(xi, 9, line.debit - residual, linea_der)

    def set_body(self, ws, xi, account_type, line, linea_der, length, linea_izq):
        amount_0_30, amount_30_60, amount_60_90, amount_90_120, amount_gt_120 = self.get_range(line, length)
        if line.invoice:
            if line.invoice.date_invoice <= datetime.today().strftime('%Y-%m-%d'):
                if account_type == 'customer':
                    self.write_customer_cells(ws, line, xi, amount_0_30, amount_30_60, amount_60_90, amount_90_120, amount_gt_120, line.invoice.date_invoice, line.invoice.date_due, line.invoice.number_reem, line.invoice.amount_untaxed,
                                              line.invoice.amount_untaxed + self.get_iva(line.invoice), line.invoice.residual, linea_izq, linea_der,
                                              self.get_iva(line.invoice), self.get_ret_iva_fuente(line.invoice)[1],
                                              self.get_ret_iva_fuente(line.invoice)[0])
                elif account_type == 'customer' and line.invoice.type == 'out_refund' and line.invoice.state == 'open':
                    self.write_customer_cells(ws, line, xi, amount_0_30, amount_30_60, amount_60_90, amount_90_120, (amount_gt_120 * -1), line.invoice.date_invoice, line.invoice.date_due, line.invoice.number, (int(line.invoice.amount_untaxed)) * -1,
                                              (int(line.invoice.amount_untaxed) + int(self.get_iva(line.invoice))) * -1, (int(line.invoice.residual)) * -1, linea_izq, linea_der,
                                              (int(self.get_iva(line.invoice))) * -1, self.get_ret_iva_fuente(line.invoice)[1],
                                              self.get_ret_iva_fuente(line.invoice)[0])
                elif account_type == 'supplier':
                    self.write_supplier_cells(amount_0_30, amount_30_60, amount_60_90, amount_90_120, amount_gt_120, ws, xi, line.account_id, line.partner_id, line.invoice.number,
                                              line.invoice.residual, line.invoice.amount_total, linea_izq, linea_der, date_due=False, date_cont=False)
        else:
            if line.date <= datetime.today().strftime('%Y-%m-%d'):
                residual = line.company_id.currency_id.with_context(date=line.date).compute(line.amount_residual, line.currency_id or line.company_id.currency_id)
                if account_type == 'supplier':
                    self.write_supplier_cells(amount_0_30, amount_30_60, amount_60_90, amount_90_120, amount_gt_120, ws, xi, line.account_id, line.partner_id, line.name,
                                              residual, line.credit, linea_izq, linea_der, line.date_maturity, False)
                elif account_type == 'customer':
                    self.write_customer_cells(ws, line, xi, amount_0_30, amount_30_60, amount_60_90, amount_90_120, amount_gt_120, line.date, line.date_maturity, line.name, 0,
                                              line.debit, residual, linea_izq, linea_der)
        return True

    @api.one
    def create_excel(self):
        wb = pycel.Workbook(encoding='utf-8')

        style_cabecera = pycel.easyxf('font: colour black, bold True;'
                                      'align: vertical center, horizontal center;'
                                      )

        style_header = pycel.easyxf('font: bold True;'
                                    'align: vertical center, horizontal center, wrap on;'
                                    'borders: left 1, right 1, top 1, bottom 1;')

        view_style = pycel.easyxf('font: bold True, height 170;'
                                  'align: vertical center, horizontal left, wrap on;'
                                  )

        linea_izq = pycel.easyxf('font: colour black, height 150;'
                                 'align: vertical center, horizontal left, wrap on;'
                                 )
        linea_izq_n = pycel.easyxf('font: colour black, height 140;'
                                   'align: vertical center, horizontal left, wrap on;'
                                   )
        linea_der = pycel.easyxf('font: colour black, height 150;'
                                 'align: vertical center, horizontal right;'
                                 )
        linea_der_bold = pycel.easyxf('font: bold True, height 160;'
                                      'align: vertical center, horizontal right;'
                                      )
        linea_der_red = pycel.easyxf('font: bold True, height 160;'
                                     'align: vertical center, horizontal right;'
                                     )

        ws = wb.add_sheet('ESTADO DE CUENTAS')

        ws.show_grid = False
        ws.header_str = u"&LFecha de Impresion: &D Hora: &T&RPagina &P de &N"
        ws.footer_str = u""
        compania = self.env['res.users'].browse(self._uid).company_id
        ws.write_merge(1, 1, 1, 5, compania.name, style_cabecera)
        ws.write_merge(2, 2, 1, 5, 'Direccion: ' + compania.partner_id.street + ' ' + compania.partner_id.street2, style_cabecera)
        ws.write_merge(3, 3, 1, 5, 'Ruc: ' + compania.partner_id.part_number, style_cabecera)
        ws.write_merge(5, 5, 1, 5, datetime.today().strftime('%Y-%m-%d'), style_cabecera)

        ws.fit_num_pages = 1
        ws.fit_height_to_pages = 0
        ws.fit_width_to_pages = 1
        ws.portrait = 1

        align = pycel.Alignment()
        align.horz = pycel.Alignment.HORZ_RIGHT
        align.vert = pycel.Alignment.VERT_CENTER

        font1 = pycel.Font()
        font1.colour_index = 0x0
        font1.height = 140

        linea_izq_n.width = 150

        #Formato de Numero
        style = pycel.XFStyle()
        style.num_format_str = '#,##0.00'
        style.alignment = align
        style.font = font1

        #Formato de Numero Saldo
        font = pycel.Font()
        font.bold = True
        font.colour_index = 0x27

        style1 = pycel.XFStyle()
        style1.num_format_str = '#,##0.00'
        style1.alignment = align
        style1.font = font

        font2 = pycel.Font()
        font2.bold = True
        font2.colour_index = 0x0

        style2 = pycel.XFStyle()
        style2.num_format_str = '#,##0.00'
        style2.alignment = align
        style2.font = font2

        style3 = pycel.XFStyle()
        style3.num_format_str = '0'
        style3.alignment = align
        style3.font = font1

        xi = 8  # Cabecera de Cliente
        self.set_header(ws, xi, self.account_type, style_header, self.period_length)
        xi += 1
        lines = self.get_lines()[0]
        part_id = False
        data_fname = str()
        formated_cell_formula = []
        if self.account_type == 'customer':
            columns = [7, 8, 9]
            data_fname = "Cuentas_por_cobrar_%s.xls" % datetime.now().strftime(DSTF)
            cell_formula = ['SUBTOTAL(9,H%s:H{0})', 'SUBTOTAL(9,I%s:I{0})', 'SUBTOTAL(9,J%s:J{0})']
            total_formula = ['SUBTOTAL(9,H9:H{0})', 'SUBTOTAL(9,I9:I{0})', 'SUBTOTAL(9,J9:J{0})']
        elif self.account_type == 'supplier':
            columns = [9, 10, 11, 12, 13]
            data_fname = "Cuentas_por_pagar_%s.xls" % datetime.now().strftime(DSTF)
            cell_formula = ['SUBTOTAL(9,J%s:J{0})', 'SUBTOTAL(9,K%s:K{0})', 'SUBTOTAL(9,L%s:L{0})', 'SUBTOTAL(9,M%s:M{0})', 'SUBTOTAL(9,N%s:N{0})']
            total_formula = ['SUBTOTAL(9,J9:J{0})', 'SUBTOTAL(9,K9:K{0})', 'SUBTOTAL(9,L9:L{0})', 'SUBTOTAL(9,M9:M{0})', 'SUBTOTAL(9,N9:N{0})']
        for item in cell_formula:
            formated_cell_formula.append(item % xi)
        data = []
        for linea in lines:
            if self.account_type == 'customer' and linea.account_id.code in ('101020101', '101020102') and linea.partner_id and linea.name != '/':
                if part_id != linea.partner_id.id and part_id:
                    ws.write(xi, 1, 'SUBTOTAL', view_style)
                    ws.write(xi, columns[0], xlwt.Formula(formated_cell_formula[0].format(xi)), linea_der_bold)
                    ws.write(xi, columns[1], xlwt.Formula(formated_cell_formula[1].format(xi)), linea_der_bold)
                    ws.write(xi, columns[2], xlwt.Formula(formated_cell_formula[2].format(xi)), linea_der_bold)
                    xi += 1
                    part_id = linea.partner_id.id
                    formated_cell_formula = []
                    for item in cell_formula:
                        formated_cell_formula.append(item % xi)
                elif part_id != linea.partner_id.id and not part_id:
                    part_id = linea.partner_id.id
                self.set_body(ws, xi, self.account_type, linea, linea_der, self.period_length, linea_izq)
                xi += 1
            elif self.account_type == 'supplier' and linea.account_id.code == '2010101' and not linea.reconcile_id and linea.partner_id and linea.name != '/':
                if part_id != linea.partner_id.id and part_id:
                    ws.write(xi, 1, 'SUBTOTAL', view_style)
                    ws.write(xi, columns[0], xlwt.Formula(formated_cell_formula[0].format(xi)), linea_der_bold)
                    ws.write(xi, columns[1], xlwt.Formula(formated_cell_formula[1].format(xi)), linea_der_bold)
                    ws.write(xi, columns[2], xlwt.Formula(formated_cell_formula[2].format(xi)), linea_der_bold)
                    ws.write(xi, columns[3], xlwt.Formula(formated_cell_formula[3].format(xi)), linea_der_bold)
                    ws.write(xi, columns[4], xlwt.Formula(formated_cell_formula[4].format(xi)), linea_der_bold)
                    xi += 1
                    part_id = linea.partner_id.id
                    formated_cell_formula = []
                    for item in cell_formula:
                        formated_cell_formula.append(item % xi)
                elif part_id != linea.partner_id.id and not part_id:
                    part_id = linea.partner_id.id
                self.set_body(ws, xi, self.account_type, linea, linea_der, self.period_length, linea_izq)
                xi += 1
        # The last line in loop does not get in to the condition so its needed to doit later
        ws.write(xi, 1, 'SUBTOTAL', view_style)
        ws.write(xi, columns[0], xlwt.Formula(formated_cell_formula[0].format(xi)), linea_der_bold)
        ws.write(xi, columns[1], xlwt.Formula(formated_cell_formula[1].format(xi)), linea_der_bold)
        ws.write(xi, columns[2], xlwt.Formula(formated_cell_formula[2].format(xi)), linea_der_bold)
        xi +=1
        # LINE TOTAL GENERAL
        ws.write(xi, 1, 'TOTAL', view_style)
        ws.write(xi, columns[0], xlwt.Formula(total_formula[0].format(xi)), linea_der_bold)
        ws.write(xi, columns[1], xlwt.Formula(total_formula[1].format(xi)), linea_der_bold)
        ws.write(xi, columns[2], xlwt.Formula(total_formula[2].format(xi)), linea_der_bold)

        ws.col(0).width = 2000
        ws.col(1).width = 9800
        ws.col(2).width = 3000
        ws.col(3).width = 4500
        ws.col(4).width = 4500
        ws.col(5).width = 4500
        ws.col(6).width = 1000
        ws.col(7).width = 3000
        ws.col(8).width = 3000
        ws.col(9).width = 3000
        ws.col(10).width = 6500
        ws.col(11).width = 6500
        ws.col(12).width = 6500
        ws.col(13).width = 6500
        ws.col(14).width = 6500
        ws.col(15).width = 6500
        ws.col(16).width = 6500
        ws.col(17).width = 6500
        ws.col(18).width = 6500
        ws.col(19).width = 6500
        ws.col(20).width = 6500
        ws.row(8).height = 750

        try:
            buf = cStringIO.StringIO()

            wb.save(buf)
            out = base64.encodestring(buf.getvalue())
            buf.close()
            res_model = 'statement.account.customer'
            self.load_doc(out, data_fname, res_model)

            return self.write({'data': out, 'txt_filename': data_fname, 'name': 'Reporte_Historial.xls'})

        except ValueError:
            raise Warning('Error a la hora de salvar el archivo')

    def get_due_days(self, date_due):
        days = 0
        date_today = datetime.today().strftime('%Y-%m-%d')
        if date_due:
            days = parser.parse(date_today) - parser.parse(date_due)
            return days.days.real
        else:
            return days

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
            attach_vals.update({'res_id': self.id})
        self.env['ir.attachment'].create(attach_vals)
