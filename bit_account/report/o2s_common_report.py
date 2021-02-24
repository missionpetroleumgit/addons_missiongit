import time
from datetime import datetime
from lxml import etree
from openerp.osv import fields, osv
from openerp.osv.orm import setup_modifiers
from openerp.tools.translate import _
from openerp.exceptions import Warning
from dateutil.relativedelta import relativedelta
import xlwt as pycel
import base64
import StringIO
import cStringIO


class account_common_report2(osv.osv_memory):
    _inherit = "accounting.report"

    _columns = {
        'name': fields.char('Descripcion', size=16,required=False, readonly=False),
        'txt_filename': fields.char(),
        'data': fields.binary('Archivo', filters=None),
        'type_export': fields.selection([('xls', 'EXCEL'), ('pdf', 'PDF')], 'Tipo de archivo', required=True),
        # 'level_report': fields.selection([('one', 'Nivel 1'), ('two', 'Nivel 2'), ('three', 'Nivel 3'),
        #                            ('four', 'Nivel 4'), ('five', 'Nivel 5'), ('six', 'Nivel 6')], 'Nivel', required=True)
    }

    def check_report2(self, cr, uid, ids, context=None):
        report = self.browse(cr, uid, ids[0])
        if report.type_export == 'pdf':
            return super(account_common_report2, self).check_report(cr, uid, ids, context=context)
        else:
            data = dict()
            res = super(account_common_report2, self).check_report(cr, uid, ids, context=context)
            data['form'] = self.read(cr, uid, ids, ['account_report_id', 'date_from_cmp',  'date_to_cmp',  'fiscalyear_id_cmp', 'journal_ids', 'period_from_cmp', 'period_to_cmp',  'filter_cmp',  'chart_account_id', 'target_move'], context=context)[0]
            for field in ['fiscalyear_id_cmp', 'chart_account_id', 'period_from_cmp', 'period_to_cmp', 'account_report_id']:
                if isinstance(data['form'][field], tuple):
                    data['form'][field] = data['form'][field][0]
            contexto = res['data']['form']['used_context']
            self.action_excel(cr, uid, ids, contexto)

    def _print_report(self, cr, uid, ids, data, context=None):
        data['form'].update(self.read(cr, uid, ids, ['date_from_cmp',  'debit_credit', 'date_to_cmp',  'fiscalyear_id_cmp', 'period_from_cmp', 'period_to_cmp',  'filter_cmp', 'account_report_id', 'enable_filter', 'label_filter','target_move'], context=context)[0])
        return self.pool['report'].get_action(cr, uid, [], 'bit_account.report_financial', data=data, context=context)

    def get_comparison_context(self, context):
        ctx = context.copy()
        ctx['fiscalyear'] = context['fiscalyear'][0]
        ctx['chart_account_id'] = context['chart_account_id'][0]
        if 'period_from' and 'period_to':
            ctx['period_from'] = context['period_from'][0]
            ctx['period_to'] = context['period_to'][0]
        return ctx

    def get_lines(self, cr, uid, data, context=None):
        lines = []
        account_obj = self.pool.get('account.account')
        currency_obj = self.pool.get('res.currency')
        ctx = dict()
        if data['form']['filter'] != 'filter_no':
            cr.execute('SELECT MIN(date_start) FROM account_period WHERE fiscalyear_id = %s', (data['form']['fiscalyear_id'][0],))
            dict_date = cr.dictfetchall()
            if data['form']['filter'] == 'filter_period':
                date_from = self.pool.get('account.period').browse(cr, uid, data['form']['period_from'][0]).date_start
            else:
                date_from = data['form']['date_from']
            if date_from > dict_date[0]['min']:
                date_from = datetime.strptime(date_from, "%Y-%m-%d") - relativedelta(days=1)
                date_from = date_from.strftime("%Y-%m-%d")
                ctx['fiscalyear'] = data['form']['fiscalyear_id'][0]
                ctx['date_from'] = dict_date[0]['min']
                ctx['date_to'] = date_from
                ctx['state'] = data['form']['target_move']
        ids2 = self.pool.get('account.financial.report')._get_children_by_order(cr, uid, [data['form']['account_report_id'][0]], context=None)
        ids2.sort()
        for report in self.pool.get('account.financial.report').browse(cr, uid, ids2, context):
            if report.type == 'account_report':
                vals = {
                    'name': report.name,
                    'balance': report.balance * report.sign or 0.0,
                    'type': 'report',
                    'level': bool(report.style_overwrite) and report.style_overwrite or report.level,
                    'account_type': report.type =='sum' and 'view' or False, #used to underline the financial report balances
                    'prev_balance': self.pool.get('account.financial.report').browse(cr, uid, report.id, ctx).balance * report.sign if ctx else 0.00
                }
                if data['form']['debit_credit']:
                    vals['debit'] = report.debit
                    vals['credit'] = report.credit
                if data['form']['enable_filter']:
                    vals['balance_cmp'] = self.pool.get('account.financial.report').browse(cr, uid, report.id, context=data['form']['comparison_context']).balance * report.sign or 0.0
                lines.append(vals)
            account_ids = []
            if report.display_detail == 'no_detail':
                #the rest of the loop is used to display the details of the financial report, so it's not needed here.
                continue
            if report.type == 'accounts' and report.account_ids:
                account_ids = account_obj._get_children_and_consol(cr, uid, [x.id for x in report.account_ids])
            elif report.type == 'account_type' and report.account_type_ids:
                account_ids = account_obj.search(cr, uid, [('user_type','in', [x.id for x in report.account_type_ids])])
            if account_ids:
                for account in account_obj.browse(cr, uid, account_ids, context):
                    #if there are accounts to display, we add them to the lines with a level equals to their level in
                    #the COA + 1 (to avoid having them with a too low level that would conflicts with the level of data
                    #financial reports for Assets, liabilities...)
                    if report.display_detail == 'detail_flat' and account.type == 'view':
                        continue
                    flag = False
                    vals = {
                        # 'id': account.id,
                        'code': account.code,
                        'name': account.name,
                        'balance':  account.balance != 0 and account.balance * report.sign or account.balance,
                        'type': 'account',
                        'level': report.display_detail == 'detail_with_hierarchy' and min(account.level + 1,6) or 6, #account.level + 1
                        'account_type': account.type,
                        'prev_balance': account_obj.browse(cr, uid, account.id, ctx).balance * report.sign if ctx else 0.00
                    }
                    if data['form']['debit_credit']:
                        vals['debit'] = account.debit
                        vals['credit'] = account.credit
                    if not currency_obj.is_zero(cr, uid, account.company_id.currency_id, vals['balance']):
                        flag = True
                    if data['form']['enable_filter']:
                        vals['balance_cmp'] = account_obj.browse(cr, uid, account.id,
                                                                 context=self.get_comparison_context(data['form']['comparison_context'])).balance * \
                                              report.sign or 0.0
                        if not currency_obj.is_zero(cr, uid, account.company_id.currency_id, vals['balance_cmp']):
                            flag = True
                    if flag:
                        lines.append(vals)
        # lines.reverse()
        return lines


    def action_excel(self, cr, uid, ids, context=None):
        if not ids:
            return {'type_hr': 'ir.actions.act_window_close'}
        if context is None:
            context = {}
        form = self.read(cr, uid, ids)[0]
        data = dict()
        data['form'] = form
        comparison_context = self._build_comparison_context(cr, uid, ids, data, context=context)
        data['form']['comparison_context'] = comparison_context
        lines = self.get_lines(cr, uid, data, context)
        wb = pycel.Workbook(encoding='utf-8')

        style_cabecera = pycel.easyxf('font: colour black, bold True;'
                                      'align: vertical center, horizontal center;'
                                      )

        style_header = pycel.easyxf('font: bold True;'
                                    'align: vertical center, horizontal center, wrap on;'
                                    'borders: left 1, right 1, top 1, bottom 1;')

        view_style = pycel.easyxf('font: bold True, height 160;'
                                    'align: vertical center, horizontal left, wrap on;')

        linea_izq = pycel.easyxf('font: colour black, height 150;'
                                 'align: vertical center, horizontal left, wrap on;'
                                 )
        linea_izq_n = pycel.easyxf('font: colour black, height 140;'
                                   'align: vertical center, horizontal left, wrap on;'
                                   )
        linea_der = pycel.easyxf('font: colour black, height 150;'
                                 'align: vertical center, horizontal right;'
                                 )
        if form['account_report_id'][0] == 1:
            ws = wb.add_sheet('Estado de Resultados')
        else:
            ws = wb.add_sheet('Balance General')

        ws.show_grid = False
        ws.header_str = u"&LFecha de Impresion: &D Hora: &T&RPagina &P de &N"
        ws.footer_str = u""
        compania = self.pool.get('res.users').browse(cr, uid, uid).company_id
        # x0 = 11
        ws.write_merge(1, 1, 1, 5, compania.name, style_cabecera)
        ws.write_merge(2, 2, 1, 5, 'Direccion: ' + compania.partner_id.street, style_cabecera)
        ws.write_merge(3, 3, 1, 5, 'Ruc: ' + compania.partner_id.part_number, style_cabecera)
        ws.write_merge(5, 5, 1, 5, datetime.today().strftime('%Y-%m-%d'), style_cabecera)

        if form['filter'] == 'filter_period':
            period_from = 'Desde:' + self.pool.get('account.period').browse(cr, uid, form['period_from'][0]).name
            period_to = 'Hasta' + self.pool.get('account.period').browse(cr, uid, form['period_to'][0]).name
            ws.write(6, 2, period_from, style_cabecera)
            ws.write(6, 4, period_to, style_cabecera)
        elif form['filter'] == 'filter_date':
            ws.write(6, 2, ('Desde:' + form['date_from']), style_cabecera)
            ws.write(6, 4, ('Hasta:' + form['date_to']), style_cabecera)

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
        ws.write(xi, 1, 'Codigo', style_header)
        ws.write(xi, 2, 'Cuenta', style_header)
        ws.write(xi, 3, 'Saldo Ant.', style_header)
        ws.write(xi, 4, 'Debe', style_header)
        ws.write(xi, 5, 'Haber', style_header)
        ws.write(xi, 6, 'Saldo', style_header)

        if data['form']['enable_filter']:
            ws.write(xi, 7, data['form']['label_filter'], style_header)

            # lst_titulos = self.get_titulos_report(cr, uid, form)
        col_t = 5
            # for titulo in lst_titulos:
            #     col_t+=1
            #     ws.write(xi, col_t, titulo, style_header)

        xi += 1
        # seq = 0
        rf = rr = ri = 0
        for linea in lines:
            # seq += 1
            # ws.write(xi, 1, seq, linea_center)
            ws.write(xi, 1, linea.get('code', ''), linea_izq if linea.get('account_type') != 'view' else view_style)
            ws.write(xi, 2, linea.get('name', ''), linea_izq if linea.get('account_type') != 'view' and linea.get('type') == 'account' else view_style)
            ws.write(xi, 3, linea.get('prev_balance', ''), linea_der)
            ws.write(xi, 4, linea.get('debit', ''), linea_der)
            ws.write(xi, 5, linea.get('credit', ''), linea_der)
            ws.write(xi, 6, linea.get('balance', ''), linea_der)
            if data['form']['enable_filter']:
                ws.write(xi, 7, linea.get('balance_cmp', ''), linea_der)
            col = 8
            xi += 1

        ws.col(0).width = 2000
        ws.col(1).width = 5800
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
            if form['account_report_id'][0] == 1:
                data_fname = "Estado_Resultados_%s.xls"
            else:
                data_fname = "Balance_General_%s.xls"

            archivo = '/opt/temp/' + data_fname
            res_model = 'accounting.report'
            id = ids and type(ids) == type([]) and ids[0] or ids
            self.load_doc(cr, uid, out, id, data_fname, archivo, res_model)

            return self.write(cr, uid, ids, {'data': out, 'txt_filename': data_fname, 'name': 'Reporte_Balance.xls'})

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

class account_report_general_ledger2(osv.osv_memory):
    _inherit = "account.report.general.ledger"
    _columns = {
        'type_export': fields.selection([('xls', 'EXCEL'), ('pdf', 'PDF')], 'Tipo de archivo', required=True),
        'specific_account_id': fields.many2one('account.account', 'Cuenta a analizar')
    }
    
    def _print_report(self, cr, uid, ids, data, context=None):
        if context is None:
            context = {}
        data = self.pre_print_report(cr, uid, ids, data, context=context)
        data['form'].update(self.read(cr, uid, ids, ['landscape',  'initial_balance', 'amount_currency', 'sortby', 'type_export', 'specific_account_id'])[0])
        chart_account_id = data['form']['chart_account_id']
        context = data['form'].get('used_context',{})
        specific_account_id = data['form']['specific_account_id']
        if specific_account_id:
            chart_account_id = specific_account_id[0]
        type_export = data['form']['type_export']
        if not data['form']['fiscalyear_id']:# GTK client problem onchange does not consider in save record
            data['form'].update({'initial_balance': False})

        if data['form']['landscape'] is False:
            data['form'].pop('landscape')
        else:
            context['landscape'] = data['form']['landscape']

        if type_export == 'pdf':
            return self.pool['report'].get_action(cr, uid, [], 'bit_account.report_generalledger', data=data, context=context)
        else:
            self.action_excel(cr, uid, ids, chart_account_id, context)

    def action_excel(self, cr, uid, ids, chart_accountc_id, context=None):
        if not ids:
            return {'type_hr': 'ir.actions.act_window_close'}
        if context is None:
            context = {}
        account = self.pool.get('account.account').browse(cr, uid, chart_accountc_id)
        children_accounts = self.get_children_accounts(cr, uid, ids, account, context)
        wb = pycel.Workbook(encoding='utf-8')

        style_cabecera = pycel.easyxf('font: colour black, bold True;'
                                      'align: vertical center, horizontal center;'
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
        ws = wb.add_sheet('Libro Mayor')

        ws.show_grid = False
        ws.header_str = u"&LFecha de Impresion: &D Hora: &T&RPagina &P de &N"
        ws.footer_str = u""
        compania = self.pool.get('res.users').browse(cr, uid, uid).company_id
        # x0 = 11
        ws.write_merge(1, 1, 1, 12, compania.name, style_cabecera)
        ws.write_merge(2, 2, 1, 12, 'Direccion: ' + compania.partner_id.street, style_cabecera)
        ws.write_merge(3, 3, 1, 12, 'Ruc: ' + compania.partner_id.part_number, style_cabecera)
        ws.write_merge(5, 5, 1, 12, datetime.today().strftime('%Y-%m-%d'), style_cabecera)
        if 'period_from' in context and 'period_to' in context:
            period_from = 'Desde:' + self.pool.get('account.period').browse(cr, uid, context['period_from']).name
            period_to = 'Hasta' + self.pool.get('account.period').browse(cr, uid, context['period_to']).name
            ws.write(6, 5, period_from, style_cabecera)
            ws.write(6, 6, period_to, style_cabecera)
        elif 'date_from' in context and 'date_to' in context:
            ws.write(6, 5, ('Desde:' + context['date_from']), style_cabecera)
            ws.write(6, 6, ('Hasta:' + context['date_to']), style_cabecera)

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
        ws.write(xi, 2, 'Tipo', style_header)
        ws.write(xi, 3, 'Empresa', style_header)
        ws.write(xi, 4, 'Ref', style_header)
        ws.write(xi, 5, 'Movimiento', style_header)
        ws.write(xi, 6, 'Etiqueta', style_header)
        ws.write(xi, 7, 'Contrapartida', style_header)
        ws.write(xi, 8, 'C.Costo', style_header)
        ws.write(xi, 9, 'Debito', style_header)
        ws.write(xi, 10, 'Credito', style_header)
        ws.write(xi, 11, 'Balance', style_header)
        ws.write(xi, 12, 'Moneda', style_header)


            # lst_titulos = self.get_titulos_report(cr, uid, form)
        col_t = 5
            # for titulo in lst_titulos:
            #     col_t+=1
            #     ws.write(xi, col_t, titulo, style_header)

        xi += 1
        # seq = 0
        rf = rr = ri = 0
        report = self.browse(cr, uid, ids[0])
        obj_move = self.pool.get('account.move.line')
        query = obj_move._query_get(cr, uid, obj='l', context=context)
        for children in children_accounts:
            # seq += 1
            # ws.write(xi, 1, seq, linea_center)
            ws.write(xi, 1, children.code, view_style)
            ws.write(xi, 2, children.name, view_style2)
            ws.write(xi, 9, self._sum_debit_account(cr, uid, report, query, children), view_style)
            ws.write(xi, 10, self._sum_credit_account(cr, uid, report, query, children), view_style)
            ws.write(xi, 11, self._sum_balance_account(cr, uid, report, query, children), view_style)
            # col = 8
            xi += 1
            for line in self.lines(cr, uid, report, query, children):
                ws.write(xi, 1, line.get('ldate', ''), linea_izq)
                ws.write(xi, 2, line.get('lcode', ''), linea_izq)
                ws.write(xi, 3, line.get('partner_name'), linea_center)
                ws.write(xi, 4, line.get('lref', ''), linea_center)
                ws.write(xi, 5, line.get('move', ''), linea_center)
                ws.write(xi, 6, line.get('lname', ''), linea_center)
                ws.write(xi, 7, line.get('line_corresp', ''), linea_center)
                ws.write(xi, 8, line.get('accon_name'), linea_der)
                ws.write(xi, 9, line.get('debit', ''), linea_der)
                ws.write(xi, 10, line.get('credit', ''), linea_der)
                ws.write(xi, 11, line.get('progress', ''), linea_der)
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

            data_fname = "Libro_Mayor%s.xls"
            archivo = '/opt/temp/' + data_fname
            res_model = 'account.report.general.ledger'
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
                                          WHERE m2.move_id = m1.move_id
                                          AND m2.account_id<>%%s), ', ') AS counterpart
                FROM (SELECT move_id
                        FROM account_move_line l
                        LEFT JOIN account_move am ON (am.id = l.move_id)
                        WHERE am.state IN %s and %s AND l.account_id = %%s GROUP BY move_id) m1
        """% (tuple(move_state), query)
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
            p.name AS partner_name
            FROM account_move_line l
            JOIN account_move m on (l.move_id=m.id)
            LEFT JOIN res_currency c on (l.currency_id=c.id)
            LEFT JOIN account_analytic_account aac on (l.analytic_account_id=aac.id)
            LEFT JOIN res_partner p on (l.partner_id=p.id)
            LEFT JOIN account_invoice i on (m.id =i.move_id)
            LEFT JOIN account_period per on (per.id=l.period_id)
            JOIN account_journal j on (l.journal_id=j.id)
            WHERE %s AND m.state IN %s AND l.account_id = %%s ORDER by %s
        """ %(query, tuple(move_state), sql_sort)
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
                '' AS partner_name
                FROM account_move_line l
                LEFT JOIN account_move m on (l.move_id=m.id)
                LEFT JOIN res_currency c on (l.currency_id=c.id)
                LEFT JOIN account_analytic_account aac on (l.analytic_account_id=aac.id)
                LEFT JOIN res_partner p on (l.partner_id=p.id)
                LEFT JOIN account_invoice i on (m.id =i.move_id)
                JOIN account_journal j on (l.journal_id=j.id)
                WHERE %s AND m.state IN %s AND l.account_id = %%s
            """ %(query, tuple(move_state))
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
                AND ' + query + ' '
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

# class account_financial_report(osv.osv):
#     _name = "account.financial.report"
#     _inherit = "account.financial.report"
#     _description = "Account Report"
