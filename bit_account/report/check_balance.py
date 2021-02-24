from openerp.osv import fields, osv
import time
from dateutil.relativedelta import relativedelta
from openerp.report import report_sxw
from openerp.addons.account.report.common_report_header import common_report_header
from datetime import datetime
import xlwt as pycel
import base64
import StringIO
import cStringIO


class account_balance_report(osv.osv_memory):
    _inherit = "account.balance.report"
    # _name = 'account.balance.report'
    _description = 'Trial Balance Report'

    _columns = {
        'type_export': fields.selection([('xls', 'EXCEL'), ('pdf', 'PDF')], 'Tipo de archivo', required=True)
    }
    result_acc = []
    sum_debit = 0.00
    sum_credit = 0.00

    def _print_report(self, cr, uid, ids, data, context=None):
        if context is None:
            context = {}
        data = self.pre_print_report(cr, uid, ids, data, context=context)
        data['form'].update(self.read(cr, uid, ids, ['landscape', 'amount_currency', 'sortby', 'type_export', 'specific_account_id'])[0])
        chart_account_id = data['form']['chart_account_id']
        context = data['form']
        type_export = data['form']['type_export']
        if not data['form']['fiscalyear_id']:# GTK client problem onchange does not consider in save record
            data['form'].update({'initial_balance': False})

        if type_export == 'pdf':
            return self.pool['report'].get_action(cr, uid, [], 'bit_account.report_trialbalance', data=data, context=context)
        else:
            self.action_excel(cr, uid, ids, chart_account_id, data['form'], context=context)

    def action_excel(self, cr, uid, ids, chart_account_id, form=None, context=None):
        if not ids:
            return {'type_hr': 'ir.actions.act_window_close'}
        if context is None:
            context = {}
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

        ws = wb.add_sheet('HOJA DE BALANCE')

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
            period_from = 'Desde:' + self.pool.get('account.period').browse(cr, uid, form['period_from']).name
            period_to = 'Hasta' + self.pool.get('account.period').browse(cr, uid, form['period_to']).name
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
        ws.write(xi, 3, 'Cod.Matriz', style_header)
        ws.write(xi, 4, 'Cuenta Matriz', style_header)
        ws.write(xi, 5, 'Saldo Ant.', style_header)
        ws.write(xi, 6, 'Debe', style_header)
        ws.write(xi, 7, 'Haber', style_header)
        ws.write(xi, 8, 'Saldo', style_header)


            # lst_titulos = self.get_titulos_report(cr, uid, form)
        col_t = 8
            # for titulo in lst_titulos:
            #     col_t+=1
            #     ws.write(xi, col_t, titulo, style_header)

        xi += 1
        # seq = 0
        rf = rr = ri = 0
        account_pool = self.pool.get('account.account')
        ctx = dict()
        if context['filter'] != 'filter_no':
            cr.execute('SELECT MIN(date_start) FROM account_period WHERE fiscalyear_id = %s', (form['fiscalyear_id'],))
            dict_date = cr.dictfetchall()
            if context['filter'] == 'filter_period':
                date_from = self.pool.get('account.period').browse(cr, uid, context['period_from']).date_start
            else:
                date_from = form['date_from']
            if date_from > dict_date[0]['min']:
                date_from = datetime.strptime(date_from, "%Y-%m-%d") - relativedelta(days=1)
                date_from = date_from.strftime("%Y-%m-%d")
                ctx['fiscalyear'] = form['fiscalyear_id']
                ctx['date_from'] = dict_date[0]['min']
                ctx['date_to'] = date_from
                ctx['state'] = form['target_move']

        lines = self.lines(cr, uid, [chart_account_id], False, form, context=context)
        for linea in lines:
            # seq += 1
            # ws.write(xi, 1, seq, linea_center)
            account = account_pool.browse(cr, uid, linea['id'], ctx)
            ws.write(xi, 1, account.code, linea_izq if account.type != 'view' else view_style)
            ws.write(xi, 2, account.name, linea_izq if account.type != 'view' else view_style)
            ws.write(xi, 3, account.code_tiw, linea_izq if account.type != 'view' else view_style)
            ws.write(xi, 4, account.name_tiw, linea_izq if account.type != 'view' else view_style)
            ws.write(xi, 5, account.balance if ctx else 0.00, linea_der)
            ws.write(xi, 6, linea.get('debit', ''), linea_der)
            ws.write(xi, 7, linea.get('credit', ''), linea_der)
            ws.write(xi, 8, linea.get('balance', ''), linea_der)
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

            data_fname = "Balance de Comprobacion_%s.xls"
            archivo = '/opt/temp/' + data_fname
            res_model = 'account.balance.report'
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

    def lines(self, cr, uid, ids, done=None, form=None, context=None):
        self.result_acc = []
        def _process_child(accounts, disp_acc, parent):
                account_rec = [acct for acct in accounts if acct['id']==parent][0]
                currency_obj = self.pool.get('res.currency')
                acc_id = self.pool.get('account.account').browse(cr, uid, account_rec['id'])
                currency = acc_id.currency_id and acc_id.currency_id or acc_id.company_id.currency_id
                res = {
                    'id': account_rec['id'],
                    'type': account_rec['type'],
                    'code': account_rec['code'],
                    'name': account_rec['name'],
                    'level': account_rec['level'],
                    'debit': account_rec['debit'],
                    'credit': account_rec['credit'],
                    'balance': account_rec['balance'],
                    'parent_id': account_rec['parent_id'],
                    'bal_type': '',
                }
                self.sum_debit += account_rec['debit']
                self.sum_credit += account_rec['credit']
                if disp_acc == 'movement':
                    if not currency_obj.is_zero(cr, uid, currency, res['credit']) or not currency_obj.is_zero(cr, uid, currency, res['debit']) or not currency_obj.is_zero(cr, uid, currency, res['balance']):
                        self.result_acc.append(res)
                elif disp_acc == 'not_zero':
                    if not currency_obj.is_zero(cr, uid, currency, res['balance']):
                        self.result_acc.append(res)
                else:
                    self.result_acc.append(res)
                if account_rec['child_id']:
                    for child in account_rec['child_id']:
                        _process_child(accounts,disp_acc,child)

        obj_account = self.pool.get('account.account')
        # if not ids:
        #     ids = self.ids
        if not ids:
            return []
        if not done:
            done={}

        ctx = context.copy()

        ctx['fiscalyear'] = form['fiscalyear_id']
        if form['filter'] == 'filter_period':
            ctx['period_from'] = form['period_from']
            ctx['period_to'] = form['period_to']
        elif form['filter'] == 'filter_date':
            ctx['date_from'] = form['date_from']
            ctx['date_to'] =  form['date_to']
        ctx['state'] = form['target_move']
        parents = ids
        child_ids = obj_account._get_children_and_consol(cr, uid, ids, ctx)
        if child_ids:
            ids = child_ids
        accounts = obj_account.read(cr, uid, ids, ['type', 'code', 'name', 'debit', 'credit', 'balance', 'parent_id',
                                                   'level', 'child_id'], ctx)

        for parent in parents:
                if parent in done:
                    continue
                done[parent] = 1
                _process_child(accounts,form['display_account'],parent)
        return self.result_acc


class account_balance_inh(report_sxw.rml_parse, common_report_header):
    _name = 'report.account.account.balance.inh'

    def __init__(self, cr, uid, name, context=None):
        super(account_balance_inh, self).__init__(cr, uid, name, context=context)
        self.sum_debit = 0.00
        self.sum_credit = 0.00
        self.date_lst = []
        self.date_lst_string = ''
        self.result_acc = []
        self.localcontext.update({
            'time': time,
            'lines': self.lines,
            'sum_debit': self._sum_debit,
            'sum_credit': self._sum_credit,
            'get_fiscalyear':self._get_fiscalyear,
            'get_filter': self._get_filter,
            'get_start_period': self.get_start_period,
            'get_end_period': self.get_end_period ,
            'get_account': self._get_account,
            'get_journal': self._get_journal,
            'get_start_date':self._get_start_date,
            'get_end_date':self._get_end_date,
            'get_target_move': self._get_target_move,
        })
        self.context = context

    def set_context(self, objects, data, ids, report_type=None):
        new_ids = ids
        # if (data['model'] == 'ir.ui.menu'):
        new_ids = 'chart_account_id' in data['form'] and [data['form']['chart_account_id']] or []
        objects = self.pool.get('account.account').browse(self.cr, self.uid, new_ids)
        return super(account_balance_inh, self).set_context(objects, data, new_ids, report_type=report_type)

    def lines(self, form, ids=None, done=None):
        def _process_child(accounts, disp_acc, parent):
                account_rec = [acct for acct in accounts if acct['id']==parent][0]
                currency_obj = self.pool.get('res.currency')
                acc_id = self.pool.get('account.account').browse(self.cr, self.uid, account_rec['id'])
                currency = acc_id.currency_id and acc_id.currency_id or acc_id.company_id.currency_id
                res = {
                    'id': account_rec['id'],
                    'type': account_rec['type'],
                    'code': account_rec['code'],
                    'name': account_rec['name'],
                    'level': account_rec['level'],
                    'debit': account_rec['debit'],
                    'credit': account_rec['credit'],
                    'balance': account_rec['balance'],
                    'parent_id': account_rec['parent_id'],
                    'bal_type': '',
                }
                self.sum_debit += account_rec['debit']
                self.sum_credit += account_rec['credit']
                if disp_acc == 'movement':
                    if not currency_obj.is_zero(self.cr, self.uid, currency, res['credit']) or not currency_obj.is_zero(self.cr, self.uid, currency, res['debit']) or not currency_obj.is_zero(self.cr, self.uid, currency, res['balance']):
                        self.result_acc.append(res)
                elif disp_acc == 'not_zero':
                    if not currency_obj.is_zero(self.cr, self.uid, currency, res['balance']):
                        self.result_acc.append(res)
                else:
                    self.result_acc.append(res)
                if account_rec['child_id']:
                    for child in account_rec['child_id']:
                        _process_child(accounts,disp_acc,child)

        obj_account = self.pool.get('account.account')
        if not ids:
            ids = self.ids
        if not ids:
            return []
        if not done:
            done={}

        ctx = self.context.copy()

        ctx['fiscalyear'] = form['fiscalyear_id']
        if form['filter'] == 'filter_period':
            ctx['period_from'] = form['period_from']
            ctx['period_to'] = form['period_to']
        elif form['filter'] == 'filter_date':
            ctx['date_from'] = form['date_from']
            ctx['date_to'] =  form['date_to']
        ctx['state'] = form['target_move']
        parents = ids
        child_ids = obj_account._get_children_and_consol(self.cr, self.uid, ids, ctx)
        if child_ids:
            ids = child_ids
        accounts = obj_account.read(self.cr, self.uid, ids, ['type','code','name','debit','credit','balance','parent_id','level','child_id'], ctx)

        for parent in parents:
                if parent in done:
                    continue
                done[parent] = 1
                _process_child(accounts,form['display_account'],parent)
        return self.result_acc


class report_trialbalance(osv.AbstractModel):
    _name = 'report.bit_account.report_trialbalance'
    _inherit = 'report.abstract_report'
    _template = 'bit_account.report_trialbalance'
    _wrapped_report_class = account_balance_inh

