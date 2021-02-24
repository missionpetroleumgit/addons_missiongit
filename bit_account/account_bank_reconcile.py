# -*- coding: utf-8 -*-
from openerp import models, fields, api
from openerp.exceptions import except_orm


class account_bank_reconcile(models.Model):
    _name = 'account.bank.reconcile'

    @api.multi
    @api.onchange('account_id','journal_id','period_id')
    def get_amount_before(self):
        move_state = ['posted', '']
        for record in self:
            print "amount_before", record.name
            if record.state != 'draft':
                list_period = record.period_id.code.split('/')
                mount = int(list_period[0:1][0])
                year = int(list_period[1:2][0])
                if mount == 1:
                    mountbefore = 12
                    yearbefore = year - 1
                else:
                    mountbefore = mount - 1
                    yearbefore = year
                if len(str(mountbefore)) <= 1:
                    monthfinal = '0' + str(mountbefore)
                else:
                    monthfinal = str(mountbefore)
                period_before  = self.env['account.period'].search(
                    [('code', '=', monthfinal + '/' + str(yearbefore)), ('company_id', '=', record.company_id.id)])
                if period_before:
                    if record.find_to == 'account':
                        domain_reconcile_before = [('account_id', '=', record.account_id.id), ('period_id', '=', period_before.id),
                                                   ('company_id', '=', record.company_id.id)]
                        account_id = record.account_id.id
                    else:
                        account_id = record.journal_id.default_debit_account_id.id
                        domain_reconcile_before = [('journal_id', '=', record.journal_id.id), ('period_id', '=', period_before.id),
                                                   ('company_id', '=', record.company_id.id)]

                    reconcile_before = self.search(domain_reconcile_before)
                    if reconcile_before:
                        record.amount_before = reconcile_before.amount
                        record.amount_before_saldo = reconcile_before.amount_ledger
                    else:
                        # si hay periodo anterior
                        self._cr.execute("SELECT COALESCE(sum(debit),0), COALESCE (sum(credit),0) \
                                                        FROM account_move_line l \
                                                        JOIN account_move am ON (am.id = l.move_id) \
                                                        WHERE (l.account_id = %s) \
                                                        AND l.state <> 'draft' \
                                                        AND (am.state IN %s) \
                                                        AND l.period_id = %s ",
                                         (account_id, tuple(move_state), period_before.id))
                        res = self._cr.fetchone()

                        sum_debit = res[0] or 0.0
                        sum_credit = res[1] or 0.0
                        record.amount_before = sum_debit - sum_credit
                else:
                    record.amount_before = 0.0
                record.get_amount_ledger()

    @api.multi
    def get_amount_ledger(self):
        move_state = ['posted','']
        for record in self:
            print "amount_ledger", record.name
            if record.state != 'draft':
                if record.find_to == 'account':
                    account_id = record.account_id.id
                else:
                    account_id = record.journal_id.default_debit_account_id.id
                query = "l.state <> 'draft' AND l.period_id IN (SELECT id FROM account_period WHERE fiscalyear_id = %s AND id = %s) AND l.move_id IN (SELECT id FROM account_move" \
                        " WHERE account_move.state = 'posted') AND l.account_id = %s" % (record.period_id.fiscalyear_id.id, record.period_id.id, account_id)
                self._cr.execute("SELECT COALESCE(sum(debit),0), COALESCE (sum(credit),0) \
                                        FROM account_move_line l \
                                        JOIN account_move am ON (am.id = l.move_id) \
                                        WHERE (l.account_id = %s) \
                                        AND l.state <> 'draft' \
                                        AND (am.state IN %s) \
                                        AND l.period_id = %s ", (account_id, tuple(move_state), record.period_id.id))
                res = self._cr.fetchone()
                sum_debit = res[0] or 0.0
                sum_credit = res[1] or 0.0
                record.amount_ledger = record.amount_before_saldo + (sum_debit - sum_credit)

    # @api.model
    # def _default_company_get(self):
    #     return self.env.user.company_id.id

    @api.multi
    @api.onchange('amount_ledger', 'reconcile_lines')
    def get_amount_tr_vc(self):
        for record in self:
            print "amount_tr-vc", record.name
            if record.state != 'draft':
                amount_transit = 0.00
                amount_voucher = 0.00
                for line in record.reconcile_lines:
                    if not line.is_reconciled:
                        amount_transit += line.debit
                        amount_voucher += line.credit
                record.amount_transit = amount_transit
                record.amount_voucher = amount_voucher
                record.amount = record.amount_ledger - amount_transit + amount_voucher

    name = fields.Char('Numero', default='/', readonly=1)
    journal_id = fields.Many2one('account.journal', 'Diario Contable')
    period_id = fields.Many2one('account.period', 'Periodo', required=True)
    date_created = fields.Date('Fecha de Registro')
    amount_before = fields.Float('Saldo Anterior', help=u'Saldo final del periodo anterior, o suma de lineas de movimiento en el mes anterior')
    amount_ledger = fields.Float('Saldo Libro', help=u'Saldo Anterior + suma total de débito - suma de credito (de '
                                                     u'los movimientos de la cuenta en el periodo actual)')
    amount_transit = fields.Float('Deposito en Transito', help=u'Suma de los debitos de las lineas a conciliar')
    amount_voucher = fields.Float('Cheques no cobrados', help=u'Suma de los créditos de las lineas a conciliar')
    amount = fields.Float('Saldo Final', help=u'Saldo Libro - Deposito en transito + Cheques no cobrados')
    state = fields.Selection([('draft', 'Nueva'), ('process', 'En Proceso'), ('reconciled', 'Conciliado')], 'Estado', default='draft')
    total_debit = fields.Float('Total Debito')
    total_credit = fields.Float('Total Credito')
    reconcile_lines = fields.One2many('account.bank.reconcile.lines', 'reconcile_id', 'Detalles de Conciliacion', ondelete='cascade')
    company_id = fields.Many2one('res.company', 'Company', required=True, default=lambda self: self.env.user.company_id)
    find_to = fields.Selection([('account', 'por Cuenta')], 'Buscar por', required=True, default='account')
    account_id = fields.Many2one('account.account', 'Cuenta', domain=[('user_type.code', '=', 'bank')])
    amount_before_saldo = fields.Float('Saldo Libro Anterior')

    @api.multi
    def unlink(self):
        for record in self:
            if record.state not in ('draft', 'process'):
                raise Warning('No se puede eliminar una conciliacion que no este en los estados nueva o en proceso.')
            for line in record.reconcile_lines:
                line.unlink()
        return super(account_bank_reconcile, self).unlink()

    @api.multi
    def load_lines(self):
        account_mline_env = self.env['account.move.line']
        account_voucher = self.env['account.voucher']
        lines = list()
        for record in self:
            grouping_lines = dict()
            domain = [('period_id', '=', record.period_id.id), ('move_id.state', '=', 'posted'), ('company_id', '=', record.company_id.id)]
            actual_period = self.env['account.period'].search([('id','=',record.period_id.id),('company_id','=', record.company_id.id)])
            list_period = actual_period.code.split('/')
            mount = int(list_period[0:1][0])
            year = int(list_period[1:2][0])
            lines_pending = []
            if mount == 1:
                mountbefore = 12
                yearbefore = year -1
            else:
                mountbefore = mount - 1
                yearbefore = year
            if len(str(mountbefore)) <= 1:
                monthfinal = '0' + str(mountbefore)
            else:
                monthfinal = str(mountbefore)
            periodbefore = self.env['account.period'].search([('code','=', monthfinal + '/' + str(yearbefore)),('company_id','=', record.company_id.id)])
            if record.find_to == 'journal':
                domain.append(('journal_id', '=', record.journal_id.id))
                domain.append(('account_id', '=', record.journal_id.default_debit_account_id.id))
                account_id = record.journal_id.default_debit_account_id.id
                domain_reconcile_before = [('journal_id', '=', record.journal_id.id), ('period_id', '=', periodbefore.id), ('company_id', '=', record.company_id.id)]
            else:
                domain.append(('account_id', '=', record.account_id.id))
                account_id = record.account_id.id
                domain_reconcile_before = [('account_id', '=', record.account_id.id), ('period_id', '=', periodbefore.id), ('company_id', '=', record.company_id.id)]
            if not record.reconcile_lines:
                move_lines = account_mline_env.search(domain)
                for_group = []
                for line in move_lines:
                    # si tiene asiento envio a  agrupar
                    if line.statement_id:
                        for_group.append(line)
                    else:
                        # lineas sin statement, pueden incluir la de los vouchers, por eso hago al final
                        lines_pending.append(line)
                grouping_lines = self.group_lines(for_group)
                for key, val in grouping_lines.items():
                    lines.append((0, 0, val))
                vouchers = account_voucher.search([('date', '>=', record.period_id.date_start), ('date', '<=', record.period_id.date_stop), ('state', '=', 'posted'),
                                                  ('amount', '>', 0.00), ('company_id', '=', record.company_id.id)])
                lines_from_voucher = list()
                for voucher in vouchers:
                    voucher_lines = account_mline_env.search([('move_id', '=', voucher.move_id.id), ('state', '=', 'valid'),
                                                              ('account_id', '=', account_id), ('company_id', '=', record.company_id.id)])
                    lines_from_voucher.append((voucher.id, voucher_lines))
                voucher_group = self.group_lines_by_voucher(lines_from_voucher)
                for key, val in voucher_group.items():
                    lines.append((0, 0, val))
                reconcile_before = self.search(domain_reconcile_before)
                if reconcile_before:
                    for line in reconcile_before.reconcile_lines:
                        if not line.is_reconciled:
                            lines.append((0, 0, {'date_line': line.date_line, 'name': line.name, 'partner_id': line.partner_id.id, 'debit': line.debit, 'credit': line.credit,
                                         'is_reconcile': False, 'moves': line.moves, 'line_id': line.line_id.id}))
                record.reconcile_lines = lines
            else:
                list_lines = list()
                move_lines = account_mline_env.search(domain)
                for line in move_lines:
                    getin = False
                    for line2 in record.reconcile_lines:
                        if line2.moves and str(line.id) in line2.moves.split(','):
                            getin = True
                            break
                    if not getin:
                        if line.statement_id:
                            list_lines.append(line)
                        else:
                            # creo linea
                            lines_pending.append(line)
                grouping_lines = self.group_lines(list_lines)
                for key, val in grouping_lines.items():
                    val.update({'reconcile_id': record.id})
                    self.env['account.bank.reconcile.lines'].create(val)
                # Carga los cheques de meses anteriores que se eliminan
                reconcile_before = self.search(domain_reconcile_before)
                if reconcile_before:
                    for line in reconcile_before.reconcile_lines:
                        if not line.is_reconciled:
                            getin = False
                            for line2 in record.reconcile_lines:
                                # JJM comparo si la linea tiene asiento, caso contrario tambien comparo si es el mismo numero de cheque
                                if (line.line_id and str(line.line_id.id) in str(line2.line_id.id)) or (line.no_check == line2.no_check):
                                    getin = True
                                    break
                            if not getin:
                                # list_lines.append(line)
                                self.env['account.bank.reconcile.lines'].create({'date_line': line.date_line, 'name': line.name, 'partner_id': line.partner_id.id, 'debit': line.debit, 'credit': line.credit,
                                               'is_reconciled': False, 'line_id': line.line_id.id, 'moves': line.moves, 'reconcile_id': record.id, 'no_check': line.no_check})
                #Fin desarrollo de cheques de meses anteriores
                list_lines = list()
                vouchers = account_voucher.search([('date', '>=', record.period_id.date_start), ('date', '<=', record.period_id.date_stop), ('state', '=', 'posted'),
                                                  ('amount', '>', 0.00), ('company_id', '=', record.company_id.id)])
                lines_from_voucher = list()
                for voucher in vouchers:
                    voucher_lines = account_mline_env.search([('move_id', '=', voucher.move_id.id), ('state', '=', 'valid'),
                                                              ('account_id', '=', account_id), ('company_id', '=', record.company_id.id)])
                    lines_from_voucher.append((voucher.id, voucher_lines))
                for line in lines_from_voucher:
                    getin = False
                    for item in line[1]:
                        if getin:
                            break
                        aux = str(item.id)
                        for line2 in record.reconcile_lines:
                            amlids = set(line2.moves.split(',')) if line2.moves else []
                            if aux in amlids:
                                getin = True
                                break
                    if not getin:
                        list_lines.append(line)
                grouping_lines = self.group_lines_by_voucher(list_lines)
                for key, val in grouping_lines.items():
                    val.update({'reconcile_id': record.id})
                    self.env['account.bank.reconcile.lines'].create(val)
            for line in lines_pending:
                getin = False
                for line2 in record.reconcile_lines:
                    if line2.moves and str(line.id) in line2.moves.split(','):
                        getin = True
                        break
                if not getin:
                    # creo linea luego de los vouchers
                    vals = {'date_line': line.move_id.date, 'name': line.ref,
                            'partner_id': line.partner_id.id, 'debit': line.debit, 'credit': line.credit,
                            'is_reconciled': False, 'line_id': line.id, 'moves': str(line.id) + ',',
                            'reconcile_id': record.id}
                    self.env['account.bank.reconcile.lines'].create(vals)
            print "record ", record
            #record.get_amount_ledger()
            return True

    def group_lines(self, lines):
        group = dict()

        countdebit = 0
        countcredit= 0
        for line in lines:

            if line.move_id.state != 'posted':
                continue
            if line.debit > 0 or line.credit > 0:
                if group.get(line.statement_id):
                    group[line.statement_id]['debit'] += line.debit
                    group[line.statement_id]['credit'] += line.credit
                    group[line.statement_id]['moves'] += str(line.id) + ','
                else:
                    statement = self.env['account.bank.statement'].search([('id','=', line.statement_id.id)])
                    concept = line.statement_id.concept if line.statement_id.concept else ''
                    group[line.statement_id] = {'date_line': line.move_id.date, 'name': u'%s %s' % (line.ref, concept), 'partner_id': line.partner_id.id, 'debit': line.debit, 'credit': line.credit,
                                                   'is_reconcile': False, 'line_id': line.id, 'moves': str(line.id) + ',','no_check': statement.no_cheque}

        return group

    def group_lines_by_voucher(self, lines):
        group = dict()

        for line in lines:
            for item in line[1]:
                voucher = self.env['account.voucher'].search([('move_id','=', item.move_id.id)])
                if item.debit > 0:
                    if line[0] not in group:
                        group[line[0]] = {'date_line': item.date, 'name': item.move_id.ref, 'partner_id': item.partner_id.id, 'debit': item.debit,
                                          'credit': item.credit, 'is_reconcile': False, 'line_id': item.id, 'moves': str(item.id) + ',', 'no_check': voucher.name}
                    else:
                        group[line[0]]['debit'] += item.debit
                        group[line[0]]['moves'] += str(item.id) + ','
                else:
                    if line[1] not in group:
                        group[line[1]] = {'date_line': item.date, 'name': item.move_id.ref, 'partner_id': item.partner_id.id, 'debit': item.debit,
                                          'credit': item.credit, 'is_reconcile': False, 'line_id': item.id, 'moves': str(item.id) + ',', 'no_check': voucher.name}
                    else:
                        group[line[1]]['credit'] += item.credit
                        group[line[1]]['moves'] += str(item.id) + ','

        return group

    @api.multi
    def set_draft(self):
        for record in self:
            record.state = 'process'

    @api.model
    def create(self, vals):
        name = self.env['ir.sequence'].get('account.bank.reconcile', context=self._context)
        vals.update({'name': name})
        vals['state'] = 'process'
        return super(account_bank_reconcile, self).create(vals)

    @api.one
    def set_reconciled(self):
        count = 0
        for line in self.reconcile_lines:
            if not line.is_reconciled:
                count += 1
        if len(self.reconcile_lines) == count:
            raise except_orm('Error!', 'No tiene ninguna linea marcada como conciliada.')
        self.state = 'reconciled'

    @api.multi
    def automatic_reconcile(self):
        return False

    @api.multi
    def check_lines(self):
        """
        Marco o desmarco las lineas con el visto de concicliadp
        :return:
        """
        self.ensure_one()
        if self.reconcile_lines:
            checked = self.reconcile_lines[0].is_reconciled
            self.reconcile_lines.write({'is_reconciled': not checked})


class account_bank_reconcile_lines(models.Model):
    _name = 'account.bank.reconcile.lines'

    date_line = fields.Date('Fecha')
    name = fields.Char('Referencia')
    partner_id = fields.Many2one('res.partner', 'Empresa')
    debit = fields.Float('Debito')
    credit = fields.Float('Credito')
    is_reconciled = fields.Boolean('Conciliado?')
    reconcile_id = fields.Many2one('account.bank.reconcile', 'Conciliacion')
    line_id = fields.Many2one('account.move.line', 'Linea de asiento')
    moves = fields.Char('Lineas de asiento')
    company_id = fields.Many2one('res.company', 'Compania', related='reconcile_id.company_id')
    no_check = fields.Char('No. Cheque', size=16)
    no_transfer = fields.Char('No. Transfer', size=16)

    @api.multi
    @api.onchange('debit','credit','is_reconciled')
    def _onchange_line(self):
        for record in self:
            print "change line", record.name
            #record.reconcile_id.get_amount_tr_vc()