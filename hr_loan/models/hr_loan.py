# -*- coding: utf-8 -*-

from datetime import datetime
from dateutil.relativedelta import relativedelta
from openerp import models, fields, api
from openerp.exceptions import except_orm


class hr_loan(models.Model):
    _name = 'hr.loan'
    _inherit = ['mail.thread','ir.needaction_mixin']
    _description= "HR Loan Request"

    dict_type = {'EGRANTSLD': 'ANTICIPO A ', 'EGRPRE': 'PRESTAMO A '}

    @api.one
    def _compute_amount(self):
        total_paid_amount = 0.00
        for loan in self:
            for line in loan.loan_line_ids:
                if line.paid == True:
                    total_paid_amount +=line.paid_amount

            balance_amount =loan.loan_amount - total_paid_amount
            self.total_amount = loan.loan_amount
            self.balance_amount = balance_amount
            self.total_paid_amount = total_paid_amount

    @api.one
    def _get_old_loan(self):
        old_amount = 0.00
        for loan in self.search([('employee_id','=',self.employee_id.id)]):
            if loan.id != self.id:
                old_amount += loan.balance_amount
        self.loan_old_amount = old_amount

    @api.model
    def _default_company(self):
        user = self.env['res.users'].browse(self._uid)
        return user.company_id.id

    name = fields.Char(string="Nombre Prestamo", default="/", readonly=True)
    date = fields.Date(string="Fecha Solicitud", default=fields.Date.today(), readonly=True)
    employee_id = fields.Many2one('hr.employee', string="Empleado", required=True, domain="[('state_emp','=','active')]")
    parent_id = fields.Many2one('hr.employee', related= "employee_id.parent_id", string="Director")
    department_id = fields.Many2one('hr.department', related="employee_id.department_id", readonly=True, string="Departamento")
    job_id = fields.Many2one('hr.job', related="employee_id.job_id", readonly=True, string="Puesto de Trabajo")
    emp_salary = fields.Float(string="Salario",related="employee_id.contract_id.wage", readonly=True)
    loan_old_amount = fields.Float(string="Prestamos no pagados", compute='_get_old_loan')
    emp_account_id = fields.Many2one('account.account', string="Cuenta Empleado", readonly=True)
    treasury_account_id = fields.Many2one('account.account', string="Cuenta Tesorería")
    journal_id = fields.Many2one('account.journal', string="Diario")
    loan_amount = fields.Float(string="Monto Préstamo", required=True)
    total_amount = fields.Float(string="Total", readonly=True, compute='_compute_amount')
    balance_amount = fields.Float(string="Valor Total", compute='_compute_amount')
    total_paid_amount = fields.Float(string="Total valor a pagar", compute='_compute_amount')
    no_month = fields.Integer(string="No de Mes", default=1)
    payment_start_date = fields.Date(string="Fecha comienzo pago", required=True, default=fields.Date.today())
    loan_line_ids = fields.One2many('hr.loan.line', 'loan_id', string="Lineas de préstamo", index=True)
    entry_count = fields.Integer(string="Entry Count", compute = 'compute_entery_count')
    move_id = fields.Many2one('account.move', string="Entry Journal", readonly=True)
    is_anticipate = fields.Boolean('Es anticipo')
    company_id = fields.Many2one('res.company', 'Empresa', default=_default_company)
    expenses = fields.One2many('hr.expense', 'loan_id', 'Egresos', ondelete='cascade')

    state = fields.Selection([
        ('draft','Borrador'),
        ('approve','Approved'),
        ('refuse','Refused'),
    ], string="State", default='draft', track_visibility='onchange', copy=False,)

    @api.onchange('is_anticipate')
    def onchage_is_anticipate(self):
        context = self._context
        if context.get('is_anticipate'):
            self.is_anticipate = True
        else:
            self.is_anticipate = False

    @api.onchange('journal_id')
    def onchange_loan_account(self):
        self.emp_account_id = self.journal_id.default_debit_account_id.id
        self.treasury_account_id = self.journal_id.default_credit_account_id.id

    @api.model
    def create(self, values):
        values['name'] = self.env['ir.sequence'].get('hr.loan.req') or ' '
        res = super(hr_loan, self).create(values)
        return res

    @api.multi
    def unlink(self):
        for loan in self:
            if loan.state != 'draft':
                raise except_orm('Error', "No se pueden eliminar préstamos que no estén en estado borrador aqui")
            for line in loan.loan_line_ids:
                line.unlink()
        return super(hr_loan, self).unlink()

    @api.one
    def action_refuse(self):
        self.state = 'refuse'
        for expense in self.expenses:
            expense.unlink()

    @api.one
    def action_set_to_draft(self):
        for line in self.loan_line_ids:
            if line.paid:
                raise except_orm('Error', "El préstamo que desea eliminar ya tiene un plazo pagado")
        self.state = 'draft'
        self.move_id.write({'state': 'draft'})
        self.move_id.unlink()

    @api.multi
    def onchange_employee_id(self, employee_id=False):
        old_amount = 0.00
        if employee_id:
            for loan in self.search([('employee_id','=',employee_id)]):
                if loan.id != self.id:
                    old_amount += loan.balance_amount
            return {
                'value':{
                    'loan_old_amount':old_amount}
            }

    @api.one
    def action_approve(self):
        self.state = 'approve'
        if not self.emp_account_id or not self.treasury_account_id or not self.journal_id:
            raise except_orm('Warning', "You must enter employee account & Treasury account and journal to approve ")
        if not self.loan_line_ids:
            raise except_orm('Warning', 'You must compute Loan Request before Approved')
        can_close = False
        loan_obj = self.env['hr.loan']
        period_obj = self.env['account.period']
        move_obj = self.env['account.move']
        move_line_obj = self.env['account.move.line']
        currency_obj = self.env['res.currency']
        created_move_ids = []
        loan_ids = []
        for loan in self:
            loan_request_date = loan.date
            period_ids =period_obj.with_context().find(loan_request_date).id
            company_currency = loan.employee_id.company_id.currency_id.id
            current_currency = self.env.user.company_id.currency_id.id
            amount = loan.loan_amount
            loan_name = loan.employee_id.name
            partner_employee_ids = self.env['res.partner'].search([('employee_id', '=', loan.employee_id.id)])
            mpartner_id = partner_employee_ids and isinstance(partner_employee_ids, list) and partner_employee_ids[0] or partner_employee_ids or False
            reference = loan.name
            journal_id = loan.journal_id.id
            move_vals = {
                'name': loan_name,
                'date': loan_request_date,
                'ref': reference,
                'period_id': period_ids or False,
                'journal_id': journal_id,
                'state': 'posted',
            }
            move_id = move_obj.create(move_vals)
            move_line_vals = {
                'name': str(reference) + ' - ' + str(loan_name),
                'ref': reference,
                'move_id': move_id.id,
                'account_id': loan.treasury_account_id.id,
                'debit': 0.0,
                'credit': amount,
                'period_id': period_ids or False,
                'journal_id': journal_id,
                'currency_id': company_currency != current_currency and  current_currency or False,
                'amount_currency':  0.0,
                'date': loan_request_date,
                'loan_id': loan.id,
                'partner_id': mpartner_id.id
            }
            move_line_obj.create(move_line_vals)
            move_line_vals2 = {
                'name': str(reference) + ' - ' + str(loan_name),
                'ref': reference,
                'move_id': move_id.id,
                'account_id': loan.emp_account_id.id,
                'credit': 0.0,
                'debit': amount,
                'period_id': period_ids or False,
                'journal_id': journal_id,
                'currency_id': company_currency != current_currency and  current_currency or False,
                'amount_currency': 0.0,
                'date': loan_request_date,
                'loan_id': loan.id,
                'partner_id': mpartner_id.id
            }
            move_line_obj.create(move_line_vals2)
            self.write({'move_id': move_id.id})
            self.create_loan_expense()
        return True

    @api.multi
    def compute_loan_line(self):
        loan_line = self.env['hr.loan.line']
        sum_prest = 0.00
        loan_line.search([('loan_id','=',self.id)]).unlink()
        for loan in self:
            date_start_str = datetime.strptime(loan.payment_start_date,'%Y-%m-%d')
            counter = 1
            amount_per_time = loan.loan_amount / loan.no_month
            for i in range(1, loan.no_month + 1):
                sum_prest += round(amount_per_time,2)
                if i == loan.no_month:
                    print "sum_prest: ", sum_prest
                    print "loan.loan_amount: ", loan.loan_amount
                    if sum_prest != loan.loan_amount:
                        diferencia = loan.loan_amount - sum_prest
                        amount_per_time = amount_per_time + diferencia
                line_id = loan_line.create({
                    'paid_date':date_start_str,
                    'paid_amount': round(amount_per_time,2),
                    'employee_id': loan.employee_id.id,
                    'loan_id':loan.id})
                counter += 1
                date_start_str = date_start_str + relativedelta(months = 1)

        return True


    @api.model
    @api.multi
    def compute_entery_count(self):
        count = 0
        entry_count = self.env['account.move.line'].search_count([('loan_id','=',self.id)])
        self.entry_count = entry_count

    @api.multi
    def button_reset_balance_total(self):
        total_paid_amount = 0.00
        for loan in self:
            for line in loan.loan_line_ids:
                if line.paid == True:
                    total_paid_amount +=line.paid_amount
            balance_amount =loan.loan_amount - total_paid_amount
            self.write({'total_paid_amount':total_paid_amount,'balance_amount':balance_amount})

    @api.one
    def create_loan_expense(self):
        expense = self.env['hr.expense']
        expense_type = self.env['hr.expense.type']
        if self.is_anticipate:
            code = 'EGRANTSLD'
        else:
            code = 'EGRPRE'
        expense_type_obj = expense_type.search([('code', '=', code)])
        if not expense_type_obj:
            raise except_orm('Error!', 'No existe un tipo de egreso con el codigo %s' % code)
        for line in self.loan_line_ids:
            expense.create({
                'comment': self.dict_type[code] + self.employee_id.name_related,
                'expense_type_id': expense_type_obj[0].id,
                'value': line.paid_amount,
                'employee_id': self.employee_id.id,
                'state': 'draft',
                'date': line.paid_date,
                'company_id': self.company_id.id,
            })

        return True


class hr_loan_line(models.Model):
    _name = "hr.loan.line"
    _description = "HR Loan Request Line"

    paid_date = fields.Date(string="Fecha Pago", required=True)
    employee_id = fields.Many2one('hr.employee', string="Empleado")
    paid_amount= fields.Float(string="Monto pagado", required=True)
    paid = fields.Boolean(string="Pagado")
    notes = fields.Text(string="Notas")
    loan_id = fields.Many2one('hr.loan', string="Ref. Prestamo", ondelete='cascade')
    payroll_id = fields.Many2one('hr.payslip', string="Ref. Rol")

    @api.one
    def action_paid_amount(self):
        context = self._context
        can_close = False
        loan_obj = self.env['hr.loan']
        period_obj = self.env['account.period']
        move_obj = self.env['account.move']
        move_line_obj = self.env['account.move.line']
        currency_obj = self.env['res.currency']
        payslip = self.env['hr.payslip']
        payslip_line = self.env['hr.payslip.line']
        created_move_ids = []
        loan_ids = []
        payslip_obj = payslip.search([('employee_id', '=', self.employee_id.id),
                                      ('date_from', '<=', self.paid_date), ('date_to', '>=', self.paid_date)])
        for line in self:
            if line.loan_id.state != 'approve':
                raise except_orm('Warning', "Loan Request must be approved")
            paid_date = line.paid_date
            period_ids =period_obj.with_context().find(paid_date).id
            company_currency = line.employee_id.company_id.currency_id.id
            current_currency = self.env.user.company_id.currency_id.id
            amount = line.paid_amount
            loan_name = line.employee_id.name
            reference = line.loan_id.name
            journal_id = line.loan_id.journal_id.id
            move_vals = {
                'name': loan_name,
                'date': paid_date,
                'ref': reference,
                'period_id': period_ids or False,
                'journal_id': journal_id,
                'state': 'posted',
            }
            move_id = move_obj.create(move_vals)
            move_line_vals = {
                'name': loan_name,
                'ref': reference,
                'move_id': move_id.id,
                'account_id': line.loan_id.emp_account_id.id,
                'debit': 0.0,
                'credit': amount,
                'period_id': period_ids or False,
                'journal_id': journal_id,
                'currency_id': company_currency != current_currency and current_currency or False,
                'amount_currency':  0.0,
                'date': paid_date,
                'loan_id':line.loan_id.id,
            }
            move_line_obj.create(move_line_vals)
            move_line_vals2 = {
                'name': loan_name,
                'ref': reference,
                'move_id': move_id.id,
                'account_id': line.loan_id.treasury_account_id.id,
                'credit': 0.0,
                'debit': amount,
                'period_id': period_ids or False,
                'journal_id': journal_id,
                'currency_id': company_currency != current_currency and current_currency or False,
                'amount_currency': 0.0,
                'date': paid_date,
                'loan_id': line.loan_id.id,
            }
            move_line_obj.create(move_line_vals2)
            self.write({'paid': True, 'payroll_id': payslip_obj.id})
        return True


class hr_employee(models.Model):
    _inherit = "hr.employee"

    @api.model
    @api.multi
    def _compute_loans(self):
        count = 0
        loan_remain_amount = 0.00
        for employee in self:
            loans = self.env['hr.loan'].search([('employee_id','=',employee.id)])
            for loan in loans:
                loan_remain_amount +=loan.balance_amount
                count +=1
            employee.loan_count = count
            employee.loan_amount = loan_remain_amount

    loan_amount= fields.Float(string="loan Amount", compute ='_compute_loans')
    loan_count = fields.Integer(string="Loan Count", compute = '_compute_loans')


class account_move_line(models.Model):
    _inherit = "account.move.line"
    loan_id = fields.Many2one('hr.loan', "Préstamo")


class hr_expense(models.Model):
    _inherit = "hr.expense"

    loan_id = fields.Many2one('hr.loan', 'Préstamo')

