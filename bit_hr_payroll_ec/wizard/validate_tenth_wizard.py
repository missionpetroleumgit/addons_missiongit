# -*- encoding: utf-8 -*-
from openerp import models, fields, api
from dateutil import parser
from dateutil.relativedelta import relativedelta
from datetime import date
from openerp.exceptions import except_orm


class validate_tenth(models.TransientModel):
    _name = 'validate.tenth'
    period_id = fields.Many2one('hr.period.period', 'Periodo')
    type = fields.Selection([('dc3', 'Decimo 3ro'), ('dc4', 'Decimo 4to')], 'Tipo de Decimo',
                            required=True)
    region = fields.Selection([('costa', 'Costa'), ('sierra', 'Sierra')], 'Region')

    @api.one
    def validate_tenth(self):
        tenth = self.env['hr.remuneration.employee']
        move_env = self.env['account.move']
        amount = 0.00
        user = self.env['res.users'].browse(self._uid)
        company = user.company_id
        res = []
        journal = False
        if self.type == 'dc3':
            datetime_start = parser.parse(self.period_id.date_start) - relativedelta(months=11)
            date_start = datetime_start.strftime('%Y-%m-%d')
            date_stop = self.period_id.date_stop
            tenth_ids = tenth.search([('decimo_type', '=', self.type), ('periodo_inicio', '>=', date_start),
                                      ('periodo_final', '<=', date_stop), ('state', '=', 'draft')])
            journal = company.decimo3_journal_id
            period = self.env['account.period'].search([('name', '=', self.period_id.name)])[0]
        else:
            if self.region == 'costa':
                tenth_ids = tenth.search([('decimo_type', '=', self.type), ('periodo_inicio', '>=', company.fecha_init_costa),
                                          ('periodo_final', '<=', company.fecha_fin_costa),
                                          ('state', '=', 'draft')])
            elif self.region == 'sierra':
                tenth_ids = tenth.search([('decimo_type', '=', self.type), ('periodo_inicio', '>=', company.fecha_init_sierra),
                                          ('periodo_final', '<=', company.fecha_fin_sierra),
                                          ('state', '=', 'draft')])
            journal = company.decimo4_journal_id
            period = self.env['account.period'].search([('date_start', '<=', date.today().strftime('%Y-%m-%d')), ('date_stop', '>=', date.today().strftime('%Y-%m-%d'))])[0]
        # tenth.write(tenth_ids, {'state': 'done'})
        if not journal:
            raise except_orm('Error', "No se han configurado los diarios de decimos para la empresa %s" % company.name)
        if not journal.default_credit_account_id:
            raise except_orm('Error', "No se han configurado la cuenta de credito del diario de decimos para la empresa %s" % company.name)
        elif not journal.default_debit_account_id:
            raise except_orm('Error', "No se han configurado la cuenta de debito del diario de decimos para la empresa %s" % company.name)

        name = 'Pago de %s' % self.type

        for tenth_id in tenth_ids:
            tenth_id.write({'state': 'done'})
            amount += tenth_id.pay_amount
            partner_employee_ids = self.env['res.partner'].search([('name', '=', tenth_id.employee_id.name_related)])
            if partner_employee_ids:
                partner_employee = partner_employee_ids[0]
            else:
                partner_employee = False
            debit_line = {
                'name': name,
                'date': date.today(),
                'partner_id': (partner_employee.id if partner_employee else False),
                'account_id': journal.default_debit_account_id.id,
                'journal_id': journal.id,
                'period_id': period.id,
                'debit': tenth_id.pay_amount,
                'credit': 0.00,
            }
            res.append((0, 0, debit_line))
        bank_name = ''
        for bank in company.bank_ids:
            bank_name = bank.bank.name
            break

        credit_line = {
            'name': name + '/' + bank_name,
            'date': date.today(),
            'partner_id': (company.partner_id.id or False),
            'account_id': journal.default_credit_account_id.id,
            'journal_id': journal.id,
            'period_id': period.id,
            'debit': 0.00,
            'credit': amount,
        }
        res.append((0, 0, credit_line))
        move = {
            'narration': name,
            'date': date.today(),
            'ref': name,
            'journal_id': journal.id,
            'period_id': period.id,
            'line_id': res
        }
        move_env.create(move)

    @api.onchange('type')
    def onchange_type(self):
        if self.type == 'dc3':
            user = self.env['res.users'].browse(self._uid)
            self.period_id = user.company_id.period_decimo3_pay.id
            self.region = None
        else:
            self.period_id = None