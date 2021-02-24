# -*- coding: utf-8 -*-
from openerp import models, fields, api
from datetime import datetime
from openerp.exceptions import except_orm, Warning
from dateutil.relativedelta import relativedelta
import xlwt as pycel
import base64
import StringIO
import cStringIO


class third_report(models.TransientModel):
    _inherit = "account.common.account.report"
    _name = 'third.report'

    partner_ids = fields.Many2many(comodel_name='res.partner', string='Terceros', domain=['|', ('is_employee', '=', True), ('is_third_partner', '=', True)])
    period_from = fields.Many2one('account.period', 'Desde')
    period_to = fields.Many2one('account.period', 'Hasta')
    account_id = fields.Many2one('account.account', 'Cuenta', required=True)
    fiscalyear_id = fields.Many2one('account.fiscalyear', 'Ejercicio Fiscal')
    initial_balance = fields.Boolean('Include Initial Balances')
    amount_currency = fields.Boolean("With Currency")
    sortby = fields.Selection([('sort_date', 'Date'), ('sort_journal_partner', 'Journal & Partner')], 'Sort by', default='sort_date')

    @api.onchange('fiscalyear_id')
    def onchange_fiscalyear(self):
        res = dict()
        if self.fiscalyear_id:
            res.setdefault('domain', {})
            domain = [('fiscalyear_id','=',self.fiscalyear_id.id)]
            res['domain']['period_from'] = repr(domain)
            res['domain']['period_to'] = repr(domain)
        return res

    @api.one
    def check_report(self):
        data = dict()
        data['ids'] = self._context.get('active_ids', [])
        data['model'] = self._context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(['fiscalyear_id', 'journal_ids', 'period_from', 'period_to',  'filter',  'account_id', 'target_move', 'partner_ids'])[0]
        for field in ['fiscalyear_id', 'account_id', 'period_from', 'period_to']:
            if isinstance(data['form'][field], tuple):
                data['form'][field] = data['form'][field][0]
        used_context = self._build_contexts(data)
        data['form']['periods'] = used_context.get('periods', False) and used_context['periods'] or []
        data['form']['used_context'] = dict(used_context, lang=self._context.get('lang', 'en_US'))
        return self._print_report(data)

    def _print_report(self, cr, uid, ids, data, context=None):
        context = data['form']
        if 'fiscalyear' not in context:
            context['fiscalyear'] = data['form']['fiscalyear_id']
        account_id = data['form']['account_id']
        if not data['form']['fiscalyear_id']:# GTK client problem onchange does not consider in save record
            data['form'].update({'initial_balance': False})

        self.action_excel(cr, uid, ids, account_id, context)

    def action_excel(self, cr, uid, ids, chart_accountc_id, context=None):
        account = self.pool.get('account.account').browse(cr, uid, chart_accountc_id)
        children_accounts = self.get_children_accounts(cr, uid, ids, account, context)
        wb = pycel.Workbook(encoding='utf-8')

        style_cabecera = pycel.easyxf('font: colour black, bold True;'
                                      'align: vertical center, horizontal center;'
                                      )
        style_cabecera2 = pycel.easyxf('font: colour black, bold True;'
                                      'align: vertical center, horizontal right;'
                                      )
        style_header = pycel.easyxf('font: bold True;'
                                    'align: vertical center, horizontal center, wrap on;'
                                    'borders: left 1, right 1, top 1, bottom 1;')
        view_style = pycel.easyxf('font: bold True, height 160;'
                                  'align: vertical center, horizontal right, wrap on;')
        view_style2 = pycel.easyxf('font: bold True, height 160;'
                                   'align: vertical center, horizontal center, wrap on;')
        linea_izq = pycel.easyxf('font: colour black, height 150;'
                                 'align: vertical center, horizontal left, wrap on;'
                                 )
        linea_izq_n = pycel.easyxf('font: colour black, height 140;'
                                   'align: vertical center, horizontal left, wrap on;'
                                   )
        linea_der = pycel.easyxf('font: colour black, height 150;'
                                 'align: vertical center, horizontal right;'
                                 )
        linea_center = pycel.easyxf('font: colour black, height 150;'
                                 'align: vertical center, horizontal center;'
                                 )
        ws = wb.add_sheet('Reporte de Terceros')

        ws.show_grid = False
        ws.header_str = u"&LFecha de Impresion: &D Hora: &T&RPagina &P de &N"
        ws.footer_str = u""
        compania = self.pool.get('res.users').browse(cr, uid, uid).company_id
        # x0 = 11
        ws.write_merge(1, 1, 1, 6, compania.name, style_cabecera)
        ws.write_merge(2, 2, 1, 6, 'Direccion: ' + compania.partner_id.street, style_cabecera)
        ws.write_merge(3, 3, 1, 6, 'Ruc: ' + compania.partner_id.part_number, style_cabecera)
        ws.write_merge(5, 5, 1, 6, datetime.today().strftime('%Y-%m-%d'), style_cabecera)
        report = self.browse(cr, uid, ids[0])
        ws.write(6, 3, 'Desde:' + report.period_from.name, style_cabecera2)
        ws.write(6, 4, 'Hasta:' + report.period_to.name, style_cabecera)

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

        xi = 8 # Cabecera de Cliente
        sec = 1

        # if type_hr == 'rol':
        ws.write(xi, 1, 'Fecha', style_header)
        ws.write(xi, 2, 'Codigo', style_header)
        ws.write(xi, 3, 'Empresa', style_header)
        # ws.write(xi, 4, 'Ref', style_header)
        # ws.write(xi, 5, 'Movimiento', style_header)
        # ws.write(xi, 6, 'Etiqueta', style_header)
        # ws.write(xi, 7, 'Contrapartida', style_header)
        # ws.write(xi, 8, 'C.Costo', style_header)
        ws.write(xi, 4, 'Debito', style_header)
        ws.write(xi, 5, 'Credito', style_header)
        ws.write(xi, 6, 'Balance', style_header)
        # ws.write(xi, 12, 'Moneda', style_header)

            # lst_titulos = self.get_titulos_report(cr, uid, form)
        col_t = 5
            # for titulo in lst_titulos:
            #     col_t+=1
            #     ws.write(xi, col_t, titulo, style_header)

        xi += 1
        # seq = 0
        rf = rr = ri = 0
        obj_move = self.pool.get('account.move.line')
        query = obj_move._query_get(cr, uid, obj='l', context=context)
        for children in children_accounts:
            # seq += 1
            # ws.write(xi, 1, seq, linea_center)
            ws.write(xi, 1, children.code, view_style)
            ws.write(xi, 2, children.name, view_style2)
            period_ids = self.get_periods_before(cr, uid, context['period_from'], context['fiscalyear_id'])
            partner_ids = context['partner_ids']
            partner_ids = self.fix_lengh(partner_ids)
            if not partner_ids:
                partner_ids = self.pool.get('res.partner').search(cr, uid, ['|', ('is_employee', '=', True), ('is_third_partner', '=', True)])
            initial_balance = self.get_initial_balance(cr, uid, period_ids, partner_ids, children.id)
            ws.write(xi, 6, initial_balance if initial_balance else 0.00, view_style)
            # ws.write(xi, 10, self._sum_credit_account(cr, uid, report, query, children), view_style)
            # ws.write(xi, 11, self._sum_balance_account(query, children), view_style)
            # col = 8
            xi += 1
            for line in self.lines(cr, uid, report, query, children):
                ws.write(xi, 1, line.get('ldate', ''), linea_izq)
                ws.write(xi, 2, line.get('part_number', ''), linea_der)
                ws.write(xi, 3, line.get('partner_name'), linea_center)
                # ws.write(xi, 4, line.get('lref', ''), linea_center)
                # ws.write(xi, 5, line.get('move', ''), linea_center)
                # ws.write(xi, 6, line.get('lname', ''), linea_center)
                # ws.write(xi, 7, line.get('line_corresp', ''), linea_center)
                # ws.write(xi, 8, line.get('accon_name'), linea_der)
                ws.write(xi, 4, line.get('debit', ''), linea_der)
                ws.write(xi, 5, line.get('credit', ''), linea_der)
                ws.write(xi, 6, line.get('progress', ''), linea_der)
                xi += 1

        ws.col(0).width = 2000
        ws.col(1).width = 5800
        ws.col(2).width = 9900
        ws.col(3).width = 15000
        ws.col(4).width = 15000
        ws.col(5).width = 6500
        ws.col(6).width = 15000
        ws.col(7).width = 15000
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

            data_fname = "Reporte_Terceros%s.xls"
            archivo = '/opt/temp/' + data_fname
            res_model = 'third.report'
            id = ids and type(ids) == type([]) and ids[0] or ids
            self.load_doc(cr, uid, out, id, data_fname, archivo, res_model)

            # return self.write(cr, uid, ids, {'data': out, 'txt_filename': data_fname, 'name': 'Libro_Mayor.xls'})

            # return self.write(cr, uid, ids, {'data': out, 'txt_filename': name})
        except ValueError:
            raise Warning('Error a la hora de salvar el archivo')

    def load_doc(self, cr, uid, out, id, data_fname, archivo, res_model):
        attach_vals = {
            'name': data_fname,
            'datas_fname': data_fname,
            'res_model': res_model,
             'datas': out,
            'type': 'binary',
            'file_type': 'file_type',
        }
        if id:
            attach_vals.update( {'res_id': id} )
        self.pool.get('ir.attachment').create(cr, uid, attach_vals)

    def get_children_accounts(self, cr, uid, ids, account, context=None):
        res = []
        obj_move = self.pool.get('account.move.line')
        query = obj_move._query_get(cr, uid, obj='l', context=context)
        currency_obj = self.pool.get('res.currency')
        report = self.browse(cr, uid, ids[0])
        ids_acc = self.pool.get('account.account')._get_children_and_consol(cr, uid, account.id)
        currency = account.currency_id and account.currency_id or account.company_id.currency_id
        for child_account in self.pool.get('account.account').browse(cr, uid, ids_acc):
            sql = """
                SELECT count(id)
                FROM account_move_line AS l
                WHERE %s AND l.account_id = %%s
            """ % query
            cr.execute(sql, (child_account.id,))
            num_entry = cr.fetchone()[0] or 0
            sold_account = self._sum_balance_account(cr, uid, report, query, child_account)
            # self.sold_accounts[child_account.id] = sold_account
            if report.display_account == 'movement':
                if child_account.type != 'view' and num_entry <> 0:
                    res.append(child_account)
            elif report.display_account == 'not_zero':
                if child_account.type != 'view' and num_entry <> 0:
                    if not currency_obj.is_zero(cr, uid, currency, sold_account):
                        res.append(child_account)
            else:
                res.append(child_account)
        if not res:
            return [account]
        return res

    def lines(self, cr, uid, report, query, account):
        """ Return all the account_move_line of account with their account code counterparts """
        partner_ids = [part.id for part in report.partner_ids]
        partner_ids = self.fix_lengh(partner_ids)
        if not partner_ids:
            partner_ids = self.pool.get('res.partner').search(cr, uid, ['|', ('is_employee', '=', True), ('is_third_partner', '=', True)])
        move_state = ['draft', 'posted']
        if report.target_move == 'posted':
            move_state = ['posted', '']
        # First compute all counterpart strings for every move_id where this account appear.
        # Currently, the counterpart info is used only in landscape mode
        sql = """
            SELECT m1.move_id,
                array_to_string(ARRAY(SELECT DISTINCT a.code
                                          FROM account_move_line m2
                                          LEFT JOIN account_account a ON (m2.account_id=a.id)
                                          WHERE m2.move_id = m1.move_id AND m2.partner_id IN %s
                                          AND m2.account_id<>%%s), ', ') AS counterpart
                FROM (SELECT move_id
                        FROM account_move_line l
                        LEFT JOIN account_move am ON (am.id = l.move_id)
                        WHERE am.state IN %s and %s AND am.partner_id IN %s AND l.account_id = %%s GROUP BY move_id) m1
        """% (tuple(partner_ids), tuple(move_state), query, tuple(partner_ids))
        cr.execute(sql, (account.id, account.id))
        counterpart_res = cr.dictfetchall()
        counterpart_accounts = {}
        for i in counterpart_res:
            counterpart_accounts[i['move_id']] = i['counterpart']
        del counterpart_res

        # Then select all account_move_line of this account
        if report.sortby == 'sort_journal_partner':
            sql_sort='j.code, p.name, l.move_id'
        else:
            sql_sort='l.date, l.move_id'
        sql = """
            SELECT l.id AS lid, l.date AS ldate, j.code AS lcode, l.currency_id,l.amount_currency,l.ref AS lref, l.name AS lname, COALESCE(l.debit,0) AS debit, COALESCE(l.credit,0) AS credit, l.period_id AS lperiod_id, l.partner_id AS lpartner_id,
            m.name AS move_name, m.id AS mmove_id,per.code as period_code,aac.name AS accon_name,
            c.symbol AS currency_code,
            i.id AS invoice_id, i.type AS invoice_type, i.number AS invoice_number,
            p.name AS partner_name,
            p.part_number AS part_number
            FROM account_move_line l
            JOIN account_move m on (l.move_id=m.id)
            LEFT JOIN res_currency c on (l.currency_id=c.id)
            LEFT JOIN account_analytic_account aac on (l.analytic_account_id=aac.id)
            LEFT JOIN res_partner p on (l.partner_id=p.id)
            LEFT JOIN account_invoice i on (m.id =i.move_id)
            LEFT JOIN account_period per on (per.id=l.period_id)
            JOIN account_journal j on (l.journal_id=j.id)
            WHERE %s AND m.state IN %s AND l.account_id = %%s AND m.partner_id IN %s ORDER by %s
        """ %(query, tuple(move_state), tuple(partner_ids), sql_sort)
        cr.execute(sql, (account.id,))
        res_lines = cr.dictfetchall()
        res_init = []
        if res_lines and report.initial_balance:
            #FIXME: replace the label of lname with a string translatable
            sql = """
                SELECT 0 AS lid, '' AS ldate, '' AS lcode, COALESCE(SUM(l.amount_currency),0.0) AS amount_currency, '' AS lref, 'Initial Balance' AS lname, COALESCE(SUM(l.debit),0.0) AS debit, COALESCE(SUM(l.credit),0.0) AS credit, '' AS lperiod_id, '' AS lpartner_id,
                '' AS move_name, '' AS mmove_id, '' AS period_code,'' AS accon_name,
                '' AS currency_code,
                NULL AS currency_id,
                '' AS invoice_id, '' AS invoice_type, '' AS invoice_number,
                '' AS partner_name, '' AS part_number
                FROM account_move_line l
                LEFT JOIN account_move m on (l.move_id=m.id)
                LEFT JOIN res_currency c on (l.currency_id=c.id)
                LEFT JOIN account_analytic_account aac on (l.analytic_account_id=aac.id)
                LEFT JOIN res_partner p on (l.partner_id=p.id)
                LEFT JOIN account_invoice i on (m.id =i.move_id)
                JOIN account_journal j on (l.journal_id=j.id)
                WHERE %s AND m.state IN %s AND l.account_id = %%s AND m.partner_id IN %s
            """ %(query, tuple(move_state), tuple(partner_ids))
            cr.execute(sql, (account.id,))
            res_init = cr.dictfetchall()
        res = res_init + res_lines
        account_sum = 0.0
        for l in res:
            l['move'] = l['move_name'] != '/' and l['move_name'] or ('*'+str(l['mmove_id']))
            l['partner'] = l['partner_name'] or ''
            l['accon_name'] = l['accon_name'] or ''
            account_sum += l['debit'] - l['credit']
            l['progress'] = account_sum
            l['line_corresp'] = l['mmove_id'] == '' and ' ' or counterpart_accounts[l['mmove_id']].replace(', ',',')
            # Modification of amount Currency
            if l['credit'] > 0:
                if l['amount_currency'] != None:
                    l['amount_currency'] = abs(l['amount_currency']) * -1
            # if l['amount_currency'] != None:
            #     re.tot_currency = self.tot_currency + l['amount_currency']
        return res

    def _sum_debit_account(self, cr, uid, report, query, account):
        if account.type == 'view':
            return account.debit
        move_state = ['draft','posted']
        if report.target_move == 'posted':
            move_state = ['posted','']
        cr.execute('SELECT sum(debit) \
                FROM account_move_line l \
                JOIN account_move am ON (am.id = l.move_id) \
                WHERE (l.account_id = %s) \
                AND (am.state IN %s) \
                AND ' + query +' '
                , (account.id, tuple(move_state)))
        sum_debit = cr.fetchone()[0] or 0.0
        if report.initial_balance:
            cr.execute('SELECT sum(debit) \
                    FROM account_move_line l \
                    JOIN account_move am ON (am.id = l.move_id) \
                    WHERE (l.account_id = %s) \
                    AND (am.state IN %s) \
                    AND ' + query + ' '
                    ,(account.id, tuple(move_state)))
            # Add initial balance to the result
            sum_debit += cr.fetchone()[0] or 0.0
        return sum_debit

    def _sum_credit_account(self, cr, uid, report, query, account):
        if account.type == 'view':
            return account.credit
        move_state = ['draft','posted']
        if report.target_move == 'posted':
            move_state = ['posted','']
        cr.execute('SELECT sum(credit) \
                FROM account_move_line l \
                JOIN account_move am ON (am.id = l.move_id) \
                WHERE (l.account_id = %s) \
                AND (am.state IN %s) \
                AND ' + query + ' '
                   ,(account.id, tuple(move_state)))
        sum_credit = cr.fetchone()[0] or 0.0
        if report.initial_balance:
            cr.execute('SELECT sum(credit) \
                    FROM account_move_line l \
                    JOIN account_move am ON (am.id = l.move_id) \
                    WHERE (l.account_id = %s) \
                    AND (am.state IN %s) \
                    AND ' + query + ' '
                       , (account.id, tuple(move_state)))
            # Add initial balance to the result
            sum_credit += cr.fetchone()[0] or 0.0
        return sum_credit

    def _sum_balance_account(self, cr, uid, report, query, account):
        if account.type == 'view':
            return account.balance
        move_state = ['draft','posted']
        if report.target_move == 'posted':
            move_state = ['posted','']
        cr.execute('SELECT (sum(debit) - sum(credit)) as tot_balance \
                FROM account_move_line l \
                JOIN account_move am ON (am.id = l.move_id) \
                WHERE (l.account_id = %s) \
                AND (am.state IN %s) \
                AND '+ query +' '
                ,(account.id, tuple(move_state)))
        sum_balance = cr.fetchone()[0] or 0.0
        if report.initial_balance:
            cr.execute('SELECT (sum(debit) - sum(credit)) as tot_balance \
                    FROM account_move_line l \
                    JOIN account_move am ON (am.id = l.move_id) \
                    WHERE (l.account_id = %s) \
                    AND (am.state IN %s) \
                    AND '+ query +' '
                    ,(account.id, tuple(move_state)))
            # Add initial balance to the result
            sum_balance += cr.fetchone()[0] or 0.0
        return sum_balance

    def _get_sortby(self, data):
        if self.sortby == 'sort_date':
            return self._translate('Date')
        elif self.sortby == 'sort_journal_partner':
            return self._translate('Journal & Partner')
        return self._translate('Date')

    def get_periods_before(self, cr, uid, period_id, fiscalyear_id):
        fiscalyear_pool = self.pool.get('account.fiscalyear')
        period_pool = self.pool.get('account.period')
        fiscalyear = fiscalyear_pool.browse(cr, uid, fiscalyear_id)
        period = period_pool.browse(cr, uid, period_id)
        period_ids = period_pool.search(cr, uid, [('date_start', '>=', fiscalyear.date_start), ('date_start', '<=', period.date_start), ('id', '!=', period_id)])
        period_ids = self.fix_lengh(period_ids)
        return period_ids

    def fix_lengh(self, array):
        if not array:
            return False
        if len(array) == 1:
            array = [array[0], array[0]]
        return array

    def get_initial_balance(self, cr, uid, period_ids, partner_ids, account_id):
        sql = "SELECT SUM(ml.debit) - SUM(ml.credit) AS initial_balance " \
              "FROM account_move_line ml JOIN account_move am " \
              "ON am.id = ml.move_id WHERE ml.period_id in %s " \
              "AND ml.state = 'valid' AND am.state = 'posted' " \
              "AND ml.partner_id IN %s AND ml.account_id = %s " \
              "AND am.partner_id IN %s " % (tuple(period_ids), tuple(partner_ids), account_id, tuple(partner_ids))
        cr.execute(sql)
        result = cr.dictfetchall()
        return result[0]['initial_balance']