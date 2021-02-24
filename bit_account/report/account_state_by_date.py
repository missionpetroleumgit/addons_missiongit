from datetime import datetime
from dateutil.relativedelta import relativedelta
from openerp import models, fields, api
from openerp.exceptions import except_orm
from dateutil import parser
import xlwt as pycel
import base64
import StringIO
import cStringIO


class account_state_bydate(models.TransientModel):
    _name = 'account.state.bydate'

    account_type = fields.Selection([('customer', 'Cuentas por Cobrar'), ('supplier', 'Cuentas por Pagar')], 'Cuentas', required=True)
    file = fields.Binary('Archivo Generado')
    file_name = fields.Char('Nombre archivo')
    period_length = fields.Integer('Longitud del periodo (dias)', default=30)
    start_period = fields.Many2one('account.period', 'Periodo Inicial', required=True)
    end_period = fields.Many2one('account.period', 'Periodo Final', required=True)

    @api.one
    def create_report(self):
        pass

    @api.one
    def create_excel(self):
        val1 = 0.00
        val2 = 0.00
        val3 = 0.00
        val4 = 0.00
        val5 = 0.00
        wb = pycel.Workbook(encoding='utf-8')
        ws, lines_styles = self.set_document_style(wb, self.account_type)
        xi = 8
        self.env['payables.account'].set_header(ws, xi, self.account_type, lines_styles['style_header'], self.period_length)
        if self.account_type == 'customer':
            columns = [15, 16, 17, 18, 19, 20]
        elif self.account_type == 'supplier':
            columns = [9, 10, 11, 12, 13, 14]
        xi += 1
        records = self.get_lines()[0]
        acc_id = False
        invoice = False
        for item in records:
            exist_invoice = False
            discount = 0.00
            if 'invoice_id' in item and item['invoice_id']:
                exist_invoice = True
                invoice = self.env['account.invoice'].browse(item['invoice_id'])
                for payment in invoice.payment_ids:
                    if payment.period_id.id <= self.end_period.id:
                        if self.account_type == 'supplier':
                            discount += payment.debit
                        else:
                            discount += payment.credit
            elif 'reconcile_partial_id' in item:
                if self.env['account.invoice'].search([('move_id', '=', item['move_id'])]):
                    continue
                elif item['reconcile_partial_id'] is None:
                    discount = 0.00
                    if self.account_type == 'supplier':
                        debit = item['saldo']
                        credit = 0.00
                    else:
                        debit = 0.00
                        credit = item['saldo']
                else:
                    reconcile = self.env['account.move.reconcile'].browse(item['reconcile_partial_id'])
                    debit = 0.00
                    credit = 0.00
                    for line in reconcile.line_partial_ids:
                        debit += line.debit
                        credit += line.credit
                    if debit-credit != 0:
                        discount = item['saldo'] + (debit - credit)
                    else:
                        continue
                invoice = self.env['account.move.line'].browse(item['id'])

            if discount == -item['saldo'] and self.account_type == 'supplier':
                records.remove(item)
            elif discount == item['saldo'] and self.account_type == 'customer':
                records.remove(item)
            else:
                if acc_id != item['account_id'] and acc_id:
                    ws.write(xi, 1, name_acc, lines_styles['view_style'])
                    ws.write(xi, columns[0], val1, lines_styles['linea_der_bold'])
                    ws.write(xi, columns[1], val2, lines_styles['linea_der_bold'])
                    ws.write(xi, columns[2], val3, lines_styles['linea_der_bold'])
                    ws.write(xi, columns[3], val4, lines_styles['linea_der_bold'])
                    ws.write(xi, columns[4], val5, lines_styles['linea_der_bold'])
                    ws.write(xi, columns[5], val1+val2+val3+val4+val5, lines_styles['linea_der_bold'])
                    xi += 1
                    acc_id = item['account_id']
                    val1 = 0.00
                    val2 = 0.00
                    val3 = 0.00
                    val4 = 0.00
                    val5 = 0.00
                elif acc_id != item['account_id'] and not acc_id:
                    acc_id = item['account_id']
                    account = self.env['account.account'].browse(acc_id)
                    name_acc = ('[' + account.code + ']' + account.name)
                if discount > 0 and exist_invoice:
                    residual = (invoice.amount_total - discount)
                elif discount <= 0 and exist_invoice:
                    residual = (invoice.amount_total + discount)
                elif not exist_invoice:
                    residual = debit - credit
                if residual < 0:
                    residual *= -1
                if discount < 0:
                    discount *= -1
                # move_name = self.env['account.move'].browse(item['move_id']).name
                #v1, v2, v3, v4, v5 son los valores de deuda por linea en cada rango de periodo
                v1, v2, v3, v4, v5 = self.set_body(ws, xi, self.account_type, invoice, lines_styles['linea_der'], self.period_length, lines_styles['linea_izq'], residual, discount,
                                                   exist_invoice)
                val1 += v1
                val2 += v2
                val3 += v3
                val4 += v4
                val5 += v5
                xi += 1
        if records and invoice:
            ws.write(xi, 1, ('[' + invoice.account_id.code + ']' + invoice.account_id.name), lines_styles['view_style'])
            ws.write(xi, columns[0], val1, lines_styles['linea_der_bold'])
            ws.write(xi, columns[1], val2, lines_styles['linea_der_bold'])
            ws.write(xi, columns[2], val3, lines_styles['linea_der_bold'])
            ws.write(xi, columns[3], val4, lines_styles['linea_der_bold'])
            ws.write(xi, columns[4], val5, lines_styles['linea_der_bold'])
            ws.write(xi, columns[5], val1+val2+val3+val4+val5, lines_styles['linea_der_bold'])
        ws.col(0).width = 2000
        ws.col(1).width = 9800
        ws.col(2).width = 25000
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

        name = "%s%s.xls" % ("Cuentas por Cobrar ", datetime.today().now())
        if self.account_type == 'supplier':
            name = "%s%s.xls" % ("Cuentas por Pagar ", datetime.today().now())
        buf = cStringIO.StringIO()
        try:
            buf = cStringIO.StringIO()
            wb.save(buf)
            out = base64.encodestring(buf.getvalue())
            buf.close()
            self.file = out
            self.file_name = name

        except ValueError:
            raise Warning('Error a la hora de salvar el archivo')

    @api.one
    def get_lines(self):
        user = self.env['res.users'].browse(self._uid)
        if self.account_type == 'supplier':
            account_ids = [acc.id for acc in user.company_id.payable_ids]
            invoice_type = 'in_invoice'
        else:
            account_ids = [acc.id for acc in user.company_id.receivable_ids]
            invoice_type = 'out_invoice'
        if not account_ids:
            raise except_orm('Error!', 'Configure las cuentas para el reporte en la compania')
        if len(account_ids) == 1:
            account_ids.append(account_ids[0])
        sql = "select aml.account_id,aml.partner_id,aml.move_id, (aml.debit-aml.credit) as saldo, ai.number_reem, ai.id as invoice_id from account_move_line aml " \
              "inner join account_invoice ai on ai.move_id = aml.move_id"
        where_condition = " where aml.period_id between %s and %s and aml.account_id in %s and ai.state='open' and ai.type='%s'" % \
                          (self.start_period.id, self.end_period.id, tuple(account_ids), invoice_type)

        order = " order by aml.account_id,aml.partner_id,ai.id"
        sql += where_condition + order
        self._cr.execute(sql)
        records = self._cr.dictfetchall()
        records = self.group_lines(records)
        sql2 = "select aml.id, aml.account_id,aml.partner_id,aml.move_id, (aml.debit-aml.credit) as saldo, aml.reconcile_partial_id from account_move_line aml"
        if self.account_type == 'supplier':
            where_condition = " where aml.period_id between %s and %s and aml.account_id in %s and credit>0.00 and (aml.reconcile_partial_id is not null or " \
                              "(aml.reconcile_partial_id " \
                              "is null and aml.reconcile_id is null))" % \
                              (self.start_period.id, self.end_period.id, tuple(account_ids))
        else:
            where_condition = " where aml.period_id between %s and %s and aml.account_id in %s and debit>0.00 and (aml.reconcile_partial_id is not null or " \
                              "(aml.reconcile_partial_id " \
                              "is null and aml.reconcile_id is null))" % \
                              (self.start_period.id, self.end_period.id, tuple(account_ids))
        sql2 += where_condition
        self._cr.execute(sql2)
        records2 = self._cr.dictfetchall()
        # records2 = self.group_lines(records2)
        if records2:
            for rec in records2:
                if self.env['account.invoice'].search([('move_id', '=', rec['move_id'])]):
                    records2.remove(rec)
            records += records2
        records.sort(key=lambda x: account_ids.index(x['account_id']))
        return records

    def group_lines(self, line):
        """Merge account move lines that are equals"""
        line2 = {}
        for item in line:
            tmp = str(item['partner_id']) + str(item['invoice_id'])
            if tmp in line2:
                am = line2[tmp]['saldo'] + item['saldo']
                line2[tmp]['saldo'] = am
            else:
                line2[tmp] = item
        line = []
        for key, val in line2.items():
            line.append(val)
        return line

    def set_body(self, ws, xi, account_type, line, linea_der, length, linea_izq, residual, discount, exist_invoice):
        gettin = False
        if exist_invoice:
            if line.date_invoice <= datetime.today().strftime('%Y-%m-%d'):
                v1, v2, v3, v4, v5 = self.get_range(line, residual, length, exist_invoice)
                gettin = True
        else:
            v1, v2, v3, v4, v5 = self.get_range(line, residual, length, exist_invoice)
            gettin = True
        if gettin:
            if account_type == 'customer':
                if exist_invoice:
                    ws.write(xi, 1, ('[' + line.account_id.code + ']' + line.account_id.name), linea_izq)
                    ws.write(xi, 2, line.partner_id.name, linea_izq)
                    ws.write(xi, 3, line.partner_id.part_number, linea_der)
                    ws.write(xi, 4, line.date_invoice, linea_der)
                    cost_centers = [obj.account_analytic_id.name for obj in line.invoice_line]
                    ws.write(xi, 5, cost_centers[0], linea_der)
                    ws.write(xi, 6, line.number, linea_der)
                    ws.write(xi, 7, line.move_id.name, linea_der)
                    ws.write(xi, 8, line.amount_untaxed, linea_der)
                    ws.write(xi, 9, self.env['payables.account'].get_iva(line), linea_der)
                    ws.write(xi, 10, line.amount_untaxed + self.env['payables.account'].get_iva(line), linea_der)
                    ws.write(xi, 11, self.env['payables.account'].get_ret_iva_fuente(line)[0], linea_der)
                    ws.write(xi, 12, self.env['payables.account'].get_ret_iva_fuente(line)[1], linea_der)
                    ws.write(xi, 13, line.amount_total, linea_der)
                    ws.write(xi, 14, line.date_due, linea_der)
                    ws.write(xi, 15, discount, linea_der)
                    ws.write(xi, 16, v1, linea_der)
                    ws.write(xi, 17, v2, linea_der)
                    ws.write(xi, 18, v3, linea_der)
                    ws.write(xi, 19, v4, linea_der)
                    ws.write(xi, 20, v5, linea_der)
                    # ws.write(xi, 19, 'Total', linea_der)
                    ws.write(xi, 21, 'Observaciones', linea_der)
                else:
                    ws.write(xi, 1, ('[' + line.account_id.code + ']' + line.account_id.name), linea_izq)
                    ws.write(xi, 2, line.partner_id.name, linea_izq)
                    ws.write(xi, 3, line.partner_id.part_number, linea_der)
                    ws.write(xi, 4, line.create_date, linea_der)
                    ws.write(xi, 5, '', linea_der)
                    ws.write(xi, 6, line.ref, linea_der)
                    ws.write(xi, 7, line.move_id.name, linea_der)
                    ws.write(xi, 8, '', linea_der)
                    ws.write(xi, 9, '', linea_der)
                    ws.write(xi, 10, '', linea_der)
                    ws.write(xi, 11, '', linea_der)
                    ws.write(xi, 12, '', linea_der)
                    ws.write(xi, 13, line.credit, linea_der)
                    ws.write(xi, 14, '', linea_der)
                    ws.write(xi, 15, discount, linea_der)
                    ws.write(xi, 16, v1, linea_der)
                    ws.write(xi, 17, v2, linea_der)
                    ws.write(xi, 18, v3, linea_der)
                    ws.write(xi, 19, v4, linea_der)
                    ws.write(xi, 20, v5, linea_der)
                    # ws.write(xi, 19, 'Total', linea_der)
                    ws.write(xi, 21, 'Observaciones', linea_der)
            elif account_type == 'supplier':
                if exist_invoice:
                    ws.write(xi, 1, ('[' + line.account_id.code + ']' + line.account_id.name), linea_izq)
                    ws.write(xi, 2, line.partner_id.name, linea_izq)
                    ws.write(xi, 3, line.partner_id.part_number, linea_der)
                    ws.write(xi, 4, line.move_id.ref, linea_der)
                    ws.write(xi, 5, line.date_cont, linea_der)
                    ws.write(xi, 6, line.date_due, linea_der)
                    ws.write(xi, 7, self.get_due_days(line.date_due, self.end_period.date_stop), linea_der)
                    ws.write(xi, 8, discount, linea_der)
                    ws.write(xi, 9, v1, linea_der)
                    ws.write(xi, 10, v2, linea_der)
                    ws.write(xi, 11, v3, linea_der)
                    ws.write(xi, 12, v4, linea_der)
                    ws.write(xi, 13, v5, linea_der)
                    ws.write(xi, 14, line.amount_total, linea_der)
                    ws.write(xi, 15, 'Observaciones', linea_der)
                else:
                    ws.write(xi, 1, ('[' + line.account_id.code + ']' + line.account_id.name), linea_izq)
                    ws.write(xi, 2, line.partner_id.name, linea_izq)
                    ws.write(xi, 3, line.partner_id.part_number, linea_der)
                    ws.write(xi, 4, line.ref, linea_der)
                    ws.write(xi, 5, line.create_date, linea_der)
                    ws.write(xi, 6, '', linea_der)
                    ws.write(xi, 7, '', linea_der)
                    ws.write(xi, 8, discount, linea_der)
                    ws.write(xi, 9, v1, linea_der)
                    ws.write(xi, 10, v2, linea_der)
                    ws.write(xi, 11, v3, linea_der)
                    ws.write(xi, 12, v4, linea_der)
                    ws.write(xi, 13, v5, linea_der)
                    ws.write(xi, 14, (line.credit - line.debit), linea_der)
                    ws.write(xi, 15, 'Observaciones', linea_der)

            return v1, v2, v3, v4, v5

    def get_range(self, line, value, length, exist_invoice):
        v1 = 0.00
        v2 = 0.00
        v3 = 0.00
        v4 = 0.00
        v5 = 0.00
        if not exist_invoice:
            v5 = value
            return v1, v2, v3, v4, v5
        today = datetime.today()
        if today > parser.parse(line.date_due):
            relative_days = today - parser.parse(line.date_due)
        else:
            v1 = value
            return v1, v2, v3, v4, v5
        if relative_days.days in range(0, length):
            v1 = value
        elif relative_days.days in range(length, 2*length):
            v2 = value
        elif relative_days.days in range(2*length, 3*length):
            v3 = value
        elif relative_days.days in range(3*length, 4*length):
            v4 = value
        else:
            v5 = value
        return v1, v2, v3, v4, v5

    def get_due_days(self, date_due, date_from):
        date_today = datetime.strptime(date_from, '%Y-%m-%d')
        date_due = datetime.strptime(date_due, '%Y-%m-%d')
        if date_due > date_today:
            return 0
        else:
            days = date_today - date_due
        return days.days.real

    def set_document_style(self, wb, account_type):
        lines_styles = dict()

        style_cabecera = pycel.easyxf('font: colour black, bold True;'
                                      'align: vertical center, horizontal center;'
                                      )
        lines_styles['style_cabecera'] = style_cabecera

        style_header = pycel.easyxf('font: bold True;'
                                    'align: vertical center, horizontal center, wrap on;'
                                    'borders: left 1, right 1, top 1, bottom 1;')
        lines_styles['style_header'] = style_header

        view_style = pycel.easyxf('font: bold True, height 170;'
                                  'align: vertical center, horizontal left, wrap on;'
                                  )
        lines_styles['view_style'] = view_style

        linea_izq = pycel.easyxf('font: colour black, height 150;'
                                 'align: vertical center, horizontal left, wrap on;'
                                 )
        lines_styles['linea_izq'] = linea_izq

        linea_izq_n = pycel.easyxf('font: colour black, height 140;'
                                   'align: vertical center, horizontal left, wrap on;'
                                   )
        lines_styles['linea_izq_n'] = linea_izq_n

        linea_der = pycel.easyxf('font: colour black, height 150;'
                                 'align: vertical center, horizontal right;'
                                 )
        lines_styles['linea_der'] = linea_der

        linea_der_bold = pycel.easyxf('font: bold True, height 160;'
                                      'align: vertical center, horizontal right;'
                                      )
        lines_styles['linea_der_bold'] = linea_der_bold

        if account_type == 'customer':
            ws = wb.add_sheet('Cuentas por cobrar')
        else:
            ws = wb.add_sheet('Cuentas por pagar')

        ws.show_grid = False
        ws.header_str = u"&LFecha de Impresion: &D Hora: &T&RPagina &P de &N"
        ws.footer_str = u""
        ws.show_grid = False
        ws.header_str = u"&LFecha de Impresion: &D Hora: &T&RPagina &P de &N"
        ws.footer_str = u""
        compania = self.env['res.users'].browse(self._uid).company_id
        # x0 = 11
        ws.write_merge(1, 1, 1, 5, compania.name, style_cabecera)
        ws.write_merge(2, 2, 1, 5, 'Direccion: ' + compania.partner_id.street, style_cabecera)
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

        return ws, lines_styles
