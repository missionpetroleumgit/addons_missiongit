from datetime import datetime
from dateutil.relativedelta import relativedelta
from openerp import models, fields, api
from openerp.exceptions import except_orm
from dateutil import parser
import xlwt as pycel
import base64
import StringIO
import cStringIO


class payables_account(models.TransientModel):
    _name = 'payables.account'

    company_id = fields.Many2one('res.company', 'Company', required=True)
    partner_ids = fields.Many2many('res.partner', string='Clientes/Proveedores')
    period_length = fields.Integer('Longitud del periodo (dias)')
    type_export = fields.Selection([('xls', 'EXCEL')], 'Tipo de archivo', required=True)
    account_type = fields.Selection([('customer', 'Cuentas por Cobrar'), ('supplier', 'Cuentas por Pagar')], 'Cuentas')
    start_period = fields.Many2one('account.period', 'Periodo Inicial')
    end_period = fields.Many2one('account.period', 'Periodo Final')
    account_move_id = fields.Many2one('account.move', 'Asiento contable')

    v1 = 0.00
    v2 = 0.00
    v3 = 0.00
    v4 = 0.00
    v5 = 0.00

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
        if self.account_type == 'supplier':
            query = [('state', '=', 'open')]
            query.append(('type', 'in', ['in_invoice', 'in_refund']))
        elif self.account_type == 'customer':
            query = ['|',('state_provision', '=', 'invoice'), ('state','=','open')]
            query.append(('type', 'in', ['out_invoice','out_refund']))
        if self.partner_ids:
            query.append(('partner_id', 'in', [part.id for part in self.partner_ids]))

        if self.company_id:
            query.append(('company_id', 'in', [part.id for part in self.company_id]))
        if self.start_period:
            query.append(('date_invoice', '>=', self.start_period.date_start))
        if self.end_period:
            query.append(('date_invoice', '<=', self.end_period.date_stop))
        if not query:
            raise except_orm('Error!!', 'No existen parametros para la busqueda')
        if not self.period_length:
            raise except_orm('Error!!', 'Defina longitud del periodo')
        print 'query ', query
        invoices = self.env['account.invoice'].search(query, order='partner_id asc, date_invoice asc')
        return invoices

    @api.one
    def get_lines_journal(self, partner_id):
        where = []
        if partner_id:
            where.append(('partner_id', '=', partner_id))
        where.append(('company_id', 'in', [part.id for part in self.company_id]))
        company = self.company_id
        if self.account_type == 'supplier':
            account_ids = [acc.id for acc in company.payable_ids]
            account_ids.append([part.id for part in company.advsuppl_account_id])
            where.append(('account_id', 'in', account_ids))
        else:
            account_ids = [acc.id for acc in company.receivable_ids]
            account_ids.append([part.id for part in company.advcustom_account_id])
            where.append(('account_id', 'in', account_ids))
        if where:
            moves = self.env['account.move.line'].search(where, order="partner_id asc, date_created asc")
        return moves

    def get_initial_balance(self, partner_id):
        where = []
        wherevoucher = []
        saldos = 0.00
        if partner_id:
            where.append(('partner_id', '=', partner_id))
        if self.account_move_id:
            where.append(('move_id', 'in', [part.id for part in self.account_move_id]))
        if self.company_id:
            where.append(('company_id', 'in', [part.id for part in self.company_id]))
        journal_name = self.env['account.journal'].search([('code', '=', 'DSIN')])
        where.append(('journal_id', '=', journal_name.id))
        moves = self.env['account.move.line'].search(where, order='partner_id')
        print "where ", where
        if self.account_type == 'supplier':
            for moveslist in moves:
                saldos += moveslist.credit
                wherevoucher.append(('move_line_id', '=', moveslist.id))
                vouchers = self.env['account.voucher.line'].search(wherevoucher)
                for voucher in vouchers:
                    saldos -= voucher.amount

        elif self.account_type == 'customer':
            for moveslist in moves:
                saldos += moveslist.debit
                wherevoucher.append(('move_line_id', '=', moveslist.id))
                vouchers = self.env['account.voucher.line'].search(wherevoucher)
                for voucher in vouchers:
                    saldos -= voucher.amount
        print "saldos Iniciales ", saldos
        return saldos

    def get_lines_saldo(self, partner_id):
        query = []
        if partner_id:
            query.append(('partner_id', '=', partner_id))
        if self.account_type == 'supplier':
            query.append(('type', '=', 'in_invoice'))
        elif self.account_type == 'customer':
            query.append(('type', '=', 'out_invoice'))
        if self.company_id:
            query.append(('company_id', 'in', [part.id for part in self.company_id]))
        query.append(('state', '=', 'open'))
        if self.start_period:
            query.append(('date_invoice', '<', self.start_period.date_start))
            invoices = self.env['account.invoice'].search(query, order='partner_id')
            invoice_saldo = 0
            for invoice in invoices:
                invoice_saldo += invoice.amount_total
        else:
            invoice_saldo = 0
        print "Saldos Iniciales facturas ", invoice_saldo
        return invoice_saldo

    def set_header(self, ws, xi, account_type, style_header, length):
        if account_type == 'customer':
            ws.write(xi, 0, 'Tipo Documento', style_header)
            ws.write(xi, 1, 'Cuenta Contable', style_header)
            ws.write(xi, 2, 'Empresas', style_header)
            ws.write(xi, 3, 'RUC', style_header)
            ws.write(xi, 4, 'Fecha Factura', style_header)
            ws.write(xi, 5, 'Centros de Costo', style_header)
            ws.write(xi, 6, 'No. Factura', style_header)
            ws.write(xi, 7, 'No. Asiento', style_header)
            ws.write(xi, 8, 'Sub Total', style_header)
            ws.write(xi, 9, 'Iva', style_header)
            ws.write(xi, 10, 'Fac+Iva', style_header)
            ws.write(xi, 11, 'Ret. Fuente', style_header)
            ws.write(xi, 12, 'Ret. Iva', style_header)
            ws.write(xi, 13, 'Total por Cobrar', style_header)
            ws.write(xi, 14, 'Vencimiento', style_header)
            ws.write(xi, 15, 'Abonos', style_header)
            ws.write(xi, 16, ('0-' + str(length)), style_header)
            ws.write(xi, 17, (str(length) + '-' + str(2*length)), style_header)
            ws.write(xi, 18, (str(2*length) + '-' + str(3*length)), style_header)
            ws.write(xi, 19, (str(3*length) + '-' + str(4*length)), style_header)
            ws.write(xi, 20, '+' + str(4*length), style_header)
            # ws.write(xi, 19, 'Total', style_header)
            ws.write(xi, 21, 'Observaciones', style_header)
            col = 21
        elif account_type == 'supplier':
            ws.write(xi, 0, 'Tipo Documento', style_header)
            ws.write(xi, 1, 'Cuenta Contable', style_header)
            ws.write(xi, 2, 'Empresas', style_header)
            ws.write(xi, 3, 'RUC', style_header)
            ws.write(xi, 4, 'Documento', style_header)
            ws.write(xi, 5, 'Fecha de Emision', style_header)
            ws.write(xi, 6, 'Vencimiento', style_header)
            ws.write(xi, 7, 'Dias de Vencida', style_header)
            ws.write(xi, 8, 'Abonos', style_header)
            ws.write(xi, 9, ('0-' + str(length)), style_header)
            ws.write(xi, 10, (str(length) + '-' + str(2*length)), style_header)
            ws.write(xi, 11, (str(2*length) + '-' + str(3*length)), style_header)
            ws.write(xi, 12, (str(3*length) + '-' + str(4*length)), style_header)
            ws.write(xi, 13, '+' + str(4*length), style_header)
            ws.write(xi, 14, 'Total Factura', style_header)
            ws.write(xi, 15, 'Total factura - Abonos', style_header)
            ws.write(xi, 16, 'Observaciones', style_header)

            col = 15
        return col

    def get_ret_iva_fuente(self, line):
        iva = 0.00
        fuent = 0.00
        user = self.env['res.users'].browse(self._uid)
        cta_iva = [acc.id for acc in user.company_id.taxiva_account_id]
        cta_fuente = [acc.id for acc in user.company_id.taxrenta_account_id]
        code_iva = self.env['account.account'].search([('id','in',cta_iva)])
        code_fuente = self.env['account.account'].search([('id','in',cta_fuente)])
        taxline = self.env['account.invoice.tax'].search([('deduction_id','=',line.deduction_id.id)])
        for tax in taxline:
            if tax.account_id.code == code_iva.code and tax.deduction_id.state == 'open':
                iva += tax.amount
            elif tax.account_id.code == code_fuente.code and tax.deduction_id.state == 'open':
                fuent += tax.amount

        # for tax_line in line.tax_line:
        #     if tax_line.account_id.code == '1010501002':
        #         iva = tax_line.amount
        #     elif tax_line.account_id.code == '1010502001':
        #         fuent = tax_line.amount
        return fuent, iva

    def get_iva(self, line):
        iva = 0.00
        for tax_line in line.tax_line:
            if tax_line.account_id.code in ('2104010101', '2104010107'):
                iva += tax_line.amount
        return iva

    def get_range(self, line, length):
        v1 = 0.00
        v2 = 0.00
        v3 = 0.00
        v4 = 0.00
        v5 = 0.00
        today = datetime.today()
        if line.date_due and line.type == 'out_invoice':
            if today > parser.parse(line.date_due):
                relative_days = today - parser.parse(line.date_due)
            else:
                v1 = line.residual
                return v1, v2, v3, v4, v5
            if relative_days.days in range(0, length):
                v1 = line.residual
            elif relative_days.days in range(length, 2*length):
                v2 = line.residual
            elif relative_days.days in range(2*length, 3*length):
                v3 = line.residual
            elif relative_days.days in range(3*length, 4*length):
                v4 = line.residual
            else:
                v5 = line.residual
        return v1, v2, v3, v4, v5

    def set_body(self, ws, xi, account_type, line, linea_der, length, linea_izq):
        if line.date_invoice <= datetime.today().strftime('%Y-%m-%d'):
            v1, v2, v3, v4, v5 = self.get_range(line, length)
            if account_type == 'customer':
                ws.write(xi, 1, (line.account_id.code + ' ' + line.account_id.name), linea_izq)
                ws.write(xi, 2, line.partner_id.name, linea_izq)
                ws.write(xi, 3, line.partner_id.part_number, linea_der)
                ws.write(xi, 4, line.date_invoice, linea_der)
                cost_centers = [obj.account_analytic_id.name for obj in line.invoice_line]
                ws.write(xi, 5, cost_centers[0], linea_der)
                ws.write(xi, 6, line.number, linea_der)
                ws.write(xi, 7, line.move_id.name, linea_der)
                if line.type == 'out_invoice':
                    ws.write(xi, 8, line.amount_untaxed, linea_der)
                    ws.write(xi, 10, line.amount_untaxed + line.amount_tax, linea_der)
                    if line.state_provision == 'invoice':
                        ws.write(xi, 13, line.residual, linea_der)
                    elif line.state_provision == 'prov':
                        ws.write(xi, 13, line.amount_total, linea_der)
                else: #Notas de Credito
                    ws.write(xi, 8, line.amount_untaxed * -1, linea_der)
                    ws.write(xi, 10, (line.amount_untaxed + line.amount_tax) * -1, linea_der)
                    ws.write(xi, 13, line.residual * -1, linea_der)
                ws.write(xi, 9, line.amount_tax, linea_der)
                ws.write(xi, 11, self.get_ret_iva_fuente(line)[0], linea_der)
                ws.write(xi, 12, self.get_ret_iva_fuente(line)[1], linea_der)

                ws.write(xi, 14, line.date_due, linea_der)
                if line.state_provision == 'invoice' :
                    ws.write(xi, 15, line.amount_total - line.residual, linea_der)
                else:
                    ws.write(xi, 15, 0, linea_der)
                ws.write(xi, 16, v1, linea_der)
                ws.write(xi, 17, v2, linea_der)
                ws.write(xi, 18, v3, linea_der)
                ws.write(xi, 19, v4, linea_der)
                ws.write(xi, 20, v5, linea_der)
                # ws.write(xi, 19, 'Total', linea_der)
                ws.write(xi, 21, 'Observaciones', linea_der)
            elif account_type == 'supplier':
                ws.write(xi, 1, (line.account_id.code + ' ' + line.account_id.name), linea_izq)
                ws.write(xi, 2, line.partner_id.name, linea_izq)
                ws.write(xi, 3, line.partner_id.part_number, linea_der)
                ws.write(xi, 4, line.number, linea_der)
                ws.write(xi, 5, line.date_invoice, linea_der)
                ws.write(xi, 6, line.date_due, linea_der)
                if line.date_due:
                    ws.write(xi, 7, self.get_due_days(line.date_due), linea_der)
                else:
                    ws.write(xi, 7, 0, linea_der)
                ws.write(xi, 8, line.amount_total - line.residual, linea_der)
                ws.write(xi, 9, v1, linea_der)
                ws.write(xi, 10, v2, linea_der)
                ws.write(xi, 11, v3, linea_der)
                ws.write(xi, 12, v4, linea_der)
                ws.write(xi, 13, v5, linea_der)
                ws.write(xi, 14, line.amount_total, linea_der)
                ws.write(xi, 15, line.residual, linea_der)
                ws.write(xi, 16, 'Observaciones', linea_der)
            return v1, v2, v3, v4, v5

    def set_body_journal(self, ws, xi, account_type, line, linea_der, length, linea_izq):
        if line.date <= datetime.today().strftime('%Y-%m-%d'):
            # v1, v2, v3, v4, v5 = self.get_range(line, length)
            if account_type == 'customer':
                ws.write(xi, 1, (line.account_id.code + ' ' + line.account_id.name), linea_izq)
                ws.write(xi, 2, line.partner_id.name, linea_izq)
                ws.write(xi, 3, line.partner_id.part_number, linea_der)
                ws.write(xi, 4, line.date, linea_der)
                ws.write(xi, 5, '0', linea_der)
                ws.write(xi, 6, line.name, linea_der)
                ws.write(xi, 7, line.ref, linea_der)
                ws.write(xi, 8, 0, linea_der)
                ws.write(xi, 9, '0', linea_der)
                if line.debit <= 0:
                    ws.write(xi, 10, line.credit * -1, linea_der)
                    ws.write(xi, 13, line.credit * -1, linea_der)
                    ws.write(xi, 15, 0, linea_der)
                else:
                    ws.write(xi, 10, line.debit, linea_der)
                    if self.amount_part_reconcile(line) > 0:
                        ws.write(xi, 13, self.amount_part_reconcile(line), linea_der)
                        ws.write(xi, 15, line.debit - self.amount_part_reconcile(line), linea_der)
                    else:
                        ws.write(xi, 13, line.debit, linea_der)
                        ws.write(xi, 15, 0, linea_der)
                ws.write(xi, 11, 0, linea_der)
                ws.write(xi, 12, 0, linea_der)
                ws.write(xi, 16, 0, linea_der)
                ws.write(xi, 17, 0, linea_der)
                ws.write(xi, 18, 0, linea_der)
                ws.write(xi, 19, 0, linea_der)
                ws.write(xi, 20, 0, linea_der)
                # ws.write(xi, 19, 'Total', linea_der)
                ws.write(xi, 21, 'Observaciones', linea_der)
            elif account_type == 'supplier':
                ws.write(xi, 1, (line.account_id.code + ' ' + line.account_id.name), linea_izq)
                ws.write(xi, 2, line.partner_id.name, linea_izq)
                ws.write(xi, 3, line.partner_id.part_number, linea_der)
                ws.write(xi, 4, line.date, linea_der)
                ws.write(xi, 5, '0', linea_der)
                ws.write(xi, 6, line.ref, linea_der)
                ws.write(xi, 7, line.name, linea_der)
                if self.amount_part_reconcile(line) != 0:
                    ws.write(xi, 8, line.credit + self.amount_part_reconcile(line), linea_der)
                    ws.write(xi, 15, self.amount_part_reconcile(line) * -1, linea_der)
                else:
                    ws.write(xi, 8, line.credit, linea_der)
                    ws.write(xi, 15, line.credit, linea_der)

                ws.write(xi, 9, 0, linea_der)
                ws.write(xi, 10, 0, linea_der)
                ws.write(xi, 11, 0, linea_der)
                ws.write(xi, 12, 0, linea_der)
                ws.write(xi, 13, 0, linea_der)
                ws.write(xi, 14, line.credit, linea_der)
                ws.write(xi, 16, 'Observaciones', linea_der)
            # return v1, v2, v3, v4, v5

    def amount_part_reconcile(self,line):
        amount = 0
        if line.reconcile_partial_id.id:
            partial_reconcile = self.env['account.move.line'].search([('reconcile_partial_id','=', line.reconcile_partial_id.id)])
            amount = 0
            for parrec in  partial_reconcile:
                amount += parrec.debit - parrec.credit
        return amount


    def validate_company_fields(self, company):
        if not company.name:
            raise except_orm('Error!!', 'La empresa no tiene configurado el nombre')
        elif not company.partner_id.street:
            raise except_orm('Error!!', 'La empresa no tiene configurada la direccion en el partner asociado: "%s"' % company.partner_id.name)
        elif not company.partner_id.part_number:
            raise except_orm('Error!!', 'La empresa no tiene configurado el numero de identificacion en el partner asociado: "%s"' % company.partner_id.name)

    @api.one
    def create_excel(self):
        wb = pycel.Workbook(encoding='utf-8')

        style_cabecera = pycel.easyxf('font: colour black, bold True;'
                                      'align: vertical center, horizontal center;'
                                      )
        style_cabecera_saldo = pycel.easyxf('font: colour black, bold True;'
                                      'align: vertical center, horizontal left;'
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
        linea_izq_sal = pycel.easyxf('font: bold True,colour black, height 150;'
                                 'align: vertical center, horizontal right, wrap on;'
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

        ws = wb.add_sheet('X COBRAR Y X PAGAR')

        ws.show_grid = False
        ws.header_str = u"&LFecha de Impresion: &D Hora: &T&RPagina &P de &N"
        ws.footer_str = u""
        compania = self.env['res.users'].browse(self._uid).company_id
        self.validate_company_fields(compania)
        # x0 = 11
        ws.write_merge(1, 1, 1, 5, compania.name, style_cabecera)
        ws.write_merge(2, 2, 1, 5, 'Direccion: ' + compania.partner_id.street, style_cabecera)
        ws.write_merge(3, 3, 1, 5, 'Ruc: ' + compania.partner_id.part_number, style_cabecera)
        if self.start_period and self.end_period:
            if self.account_type == 'supplier':
                ws.write_merge(5, 5, 1, 5, 'ESTADO CUENTAS POR PAGAR DEL '+ self.start_period.date_start + ' AL ' + self.end_period.date_stop, style_cabecera)
            else:
                ws.write_merge(5, 5, 1, 5, 'ESTADO CUENTAS POR COBRAR DEL '+ self.start_period.date_start + ' AL ' + self.end_period.date_stop, style_cabecera)
        else:
            if self.account_type == 'supplier':
                ws.write_merge(5, 5, 1, 5, 'ESTADO CUENTAS POR PAGAR',style_cabecera)
            else:
                ws.write_merge(5, 5, 1, 5, 'ESTADO CUENTAS POR COBRAR', style_cabecera)

        ws.write_merge(6, 6, 1, 5,'Fecha Impresion: '+ datetime.today().strftime('%Y-%m-%d'), style_cabecera)

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

        #info = self.get_payroll(cr, uid, form)

        xi = 8  # Cabecera de Cliente
        sec = 1
        self.set_header(ws, xi, self.account_type, style_header, self.period_length)
        col_t = 8
        xi += 1
        # seq = 0
        rf = rr = ri = 0
        lines = self.get_lines()[0]

        # print "lines", lines
        line2 = {}
        part_id = False
        total = 0
        totaltotal =0
        if self.account_type == 'customer':
            columns = [16, 17, 18, 19, 20, 21,13]
        elif self.account_type == 'supplier':
            columns = [9, 10, 11, 12, 13, 14,15]
        for linea in lines:
            # seq += 1
           # ws.write(xi, 1, 'SALDO INICIAL', view_style)
            if part_id != linea.partner_id.id and part_id:
                ws.write(xi, 1, 'TOTAL', view_style)
                ws.write(xi, columns[6], total, linea_der_bold)
                ws.write(xi, columns[0], line2[part_id]['v1'], linea_der_bold)
                ws.write(xi, columns[1], line2[part_id]['v2'], linea_der_bold)
                ws.write(xi, columns[2], line2[part_id]['v3'], linea_der_bold)
                ws.write(xi, columns[3], line2[part_id]['v4'], linea_der_bold)
                ws.write(xi, columns[4], line2[part_id]['v5'], linea_der_bold)
                xi += 1
                ws.write(xi, 1, 'SALDO INICIAL', view_style)
                ws.write(xi, columns[5], self.get_initial_balance(linea.partner_id.id) + self.get_lines_saldo(linea.partner_id.id), linea_izq_sal)
                xi +=1
                part_id = linea.partner_id.id
                total = 0
                journal_lines = self.get_lines_journal(linea.partner_id.id)[0]
                for journal in journal_lines:
                    if journal.reconcile_partial_id or not journal.reconcile_id:
                        self.set_body_journal(ws, xi, self.account_type, journal, linea_der, self.period_length, linea_izq)
                        ws.write(xi, 0, journal.journal_id.name, linea_izq)
                        if self.account_type == 'customer':
                            if journal.debit <= 0:
                                total += journal.credit * -1
                                totaltotal += journal.credit * -1
                            else:
                                if self.amount_part_reconcile(journal) > 0:
                                    total += self.amount_part_reconcile(journal)
                                    totaltotal += self.amount_part_reconcile(journal)
                                else:
                                    total += journal.debit
                                    totaltotal += journal.debit
                        else:
                            if journal.credit <= 0:
                                total += journal.debit * -1
                                totaltotal += journal.debit * -1
                            else:
                                if self.amount_part_reconcile(journal) *-1 > 0:
                                    total += self.amount_part_reconcile(journal) * -1
                                    totaltotal += self.amount_part_reconcile(journal) * -1
                                else:
                                    total += journal.credit
                                    totaltotal += journal.credit
                        xi += 1

            elif part_id != linea.partner_id.id and not part_id:
                ws.write(xi, 1, 'SALDO INICIAL', view_style)
                ws.write(xi, columns[5], self.get_initial_balance(linea.partner_id.id)  +  self.get_lines_saldo(linea.partner_id.id), linea_izq_sal)
                xi +=1
                #Development SaldosInicales
                total = 0
                journal_lines = self.get_lines_journal(linea.partner_id.id)[0]
                for journal in journal_lines:
                    if journal.reconcile_partial_id or not journal.reconcile_id:
                        self.set_body_journal(ws, xi, self.account_type, journal, linea_der, self.period_length, linea_izq)
                        ws.write(xi, 0, journal.journal_id.name, linea_izq)
                        if self.account_type == 'customer':
                            if journal.debit <= 0:
                                total += journal.credit * -1
                                totaltotal += journal.credit * -1
                            else:
                                if self.amount_part_reconcile(journal) > 0:
                                    total += self.amount_part_reconcile(journal)
                                    totaltotal += self.amount_part_reconcile(journal)
                                else:
                                    total += journal.debit
                                    totaltotal += journal.debit
                        else:
                            if journal.credit <= 0:
                                total += journal.debit * -1
                                totaltotal += journal.debit * -1
                            else:
                                if self.amount_part_reconcile(journal) *-1 > 0:
                                    total += self.amount_part_reconcile(journal) * -1
                                    totaltotal += self.amount_part_reconcile(journal) * -1
                                else:
                                    total += journal.credit
                                    totaltotal += journal.credit


                        xi += 1

                part_id = linea.partner_id.id

            v1, v2, v3, v4, v5 = self.set_body(ws, xi, self.account_type, linea, linea_der, self.period_length, linea_izq)
            ws.write(xi, 0, linea.journal_id.name, linea_izq)
            if linea.type == 'out_invoice':
                if linea.state_provision == 'invoice':
                    total += round(linea.residual,2)
                    totaltotal += round(linea.residual,2)
                elif linea.state_provision == 'prov':
                    total += round(linea.amount_total,2)
                    totaltotal += round(linea.amount_total,2)
            elif linea.type == 'out_refund':
                total -= round(linea.residual,2)
                totaltotal -= round(linea.residual,2)
            if linea.type == 'in_invoice':
                if linea.state_provision == 'invoice':
                    total += round(linea.residual,2)
                    totaltotal += round(linea.residual,2)
                elif linea.state_provision == 'prov':
                    total += round(linea.amount_total,2)
                    totaltotal += round(linea.amount_total,2)
            elif linea.type == 'in_refund':
                total -= round(linea.residual,2)
                totaltotal -= round(linea.residual,2)

            xi += 1
            self.group_lines(linea, line2, v1, v2, v3, v4, v5)
        if lines:
            ws.write(xi, 1, 'TOTAL', view_style)
            ws.write(xi, columns[6], total, linea_der_bold)
            ws.write(xi, columns[0], line2[linea.partner_id.id]['v1'], linea_der_bold)
            ws.write(xi, columns[1], line2[linea.partner_id.id]['v2'], linea_der_bold)
            ws.write(xi, columns[2], line2[linea.partner_id.id]['v3'], linea_der_bold)
            ws.write(xi, columns[3], line2[linea.partner_id.id]['v4'], linea_der_bold)
            ws.write(xi, columns[4], line2[linea.partner_id.id]['v5'], linea_der_bold)
            xi +=1
            #LINE TOTAL GENERAL
            for key, val in line2.items():
                self.v1 += val['v1']
                self.v2 += val['v2']
                self.v3 += val['v3']
                self.v4 += val['v4']
                self.v5 += val['v5']

            ws.write(xi, 1, 'TOTAL GENERAL', view_style)
            ws.write(xi, columns[6], totaltotal,linea_der_bold)
            ws.write(xi, columns[0], self.v1, linea_der_bold)
            ws.write(xi, columns[1], self.v2, linea_der_bold)
            ws.write(xi, columns[2], self.v3, linea_der_bold)
            ws.write(xi, columns[3], self.v4, linea_der_bold)
            ws.write(xi, columns[4], self.v5, linea_der_bold)

        ws.col(0).width = 9800
        ws.col(1).width = 9800
        ws.col(2).width = 9900
        ws.col(3).width = 5000
        ws.col(4).width = 6900
        ws.col(5).width = 6500
        ws.col(6).width = 5500
        ws.col(7).width = 5500
        ws.col(8).width = 5500
        ws.col(9).width = 5500
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
        ws.col(21).width = 6500
        ws.col(22).width = 6500
        ws.col(23).width = 6500
        ws.col(24).width = 6500
        ws.col(25).width = 6500
        ws.col(26).width = 6500
        ws.col(27).width = 6500
        ws.col(28).width = 6500
        ws.col(29).width = 6500
        ws.col(30).width = 6500

        ws.row(8).height = 750

        buf = cStringIO.StringIO()
        # name = "%s%s%s.xls" % (path, "Reporte_RR_HH", datetime.datetime.now())
        # exists_path = os.path.exists(path)
        # print 'esta ruta existe?', exists_path
        # print('sys.argv[0] =', sys.argv[0])
        # a = sys.path
        # pathname = os.path.dirname(os.getcwd())
        # print('path =', a)
        # print('full path =', os.path.abspath(pathname))
        try:
            # wb.save(name)
            # raise Warning('Archivo salvado correctamente')
            buf = cStringIO.StringIO()

            wb.save(buf)
            out = base64.encodestring(buf.getvalue())
            buf.close()

            data_fname = "CuentasXcobrarXpagar_%s.xls"
            archivo = '/opt/temp/' + data_fname
            res_model = 'payables.account'
            # id = ids and type(ids) == type([]) and ids[0] or ids
            self.load_doc(out, data_fname, res_model)

            return self.write({'data': out, 'txt_filename': data_fname, 'name': 'Reporte_Balance.xls'})

            # return self.write(cr, uid, ids, {'data': out, 'txt_filename': name})
        except ValueError:
            raise Warning('Error a la hora de salvar el archivo')

    def group_lines(self, line, line2, v1, v2, v3, v4, v5):
        """Merge account lines """

        # for l in line:
        tmp = line.partner_id.id
        if tmp in line2:
            line2[tmp]['v1'] += v1
            line2[tmp]['v2'] += v2
            line2[tmp]['v3'] += v3
            line2[tmp]['v4'] += v4
            line2[tmp]['v5'] += v5
        else:
            line2[tmp] = {'v1': v1, 'v2': v2, 'v3': v3, 'v4': v4, 'v5': v5}

    def get_due_days(self, date_due):
        date_today = datetime.today()
        date_due = datetime.strptime(date_due, '%Y-%m-%d')
        if date_due > date_today:
            return 0
        else:
            days = date_today - date_due
        return days.days.real

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

