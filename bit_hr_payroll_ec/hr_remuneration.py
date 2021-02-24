__author__ = 'guillermo'
from openerp import models, fields, api
from dateutil import parser
from datetime import date, datetime, timedelta
from utils import thirdty_days_months, thirty_days_months2


class res_company(models.Model):
    _inherit = 'res.company'

    base_amount = fields.Float('Salario basico unificado')


class hr_remuneration_employee(models.Model):
    _name = 'hr.remuneration.employee'

    employee_id = fields.Many2one('hr.employee', 'Empleado', required=True)
    identification_id = fields.Char('Cedula', related='employee_id.identification_id')
    gender = fields.Selection('Genero', related='employee_id.gender')
    otherid = fields.Char('Ocupacion', related='employee_id.otherid')
    decimo_type = fields.Selection([('dc3', 'Decimo 3ro'), ('dc4', 'Decimo 4to')], 'Tipo de Decimo', required=True)
    periodo_inicio = fields.Date('Periodo inicial a pagar', required=True)
    periodo_final = fields.Date('Periodo final a pagar', required=True)
    worked_time = fields.Float('Tiempo trabajado en el periodo', required=True)
    discount_amount = fields.Float('Valor a descontar')
    pay_amount = fields.Float('Monto a pagar en el periodo', required=True)
    pay_amountbackup = fields.Float('Monto a pagar en el periodo sin descuento', required=True)
    forma_pago = fields.Selection([('transferencia', 'Transferencia'), ('cheque', 'Cheque')], 'Tipo de Pago',
                                  related='employee_id.emp_modo_pago', store=True)
    state = fields.Selection([('new', 'Nuevo'), ('draft', 'Por contabilizar'), ('done', 'Contabilizado')], 'Estado',
                             default='new')
    unbalance = fields.Boolean('Descuadre?')
    unbalance_time = fields.Float('Dieferencia de tiempo segun IESS')
    unbalance_amount = fields.Float('Dieferencia de pago segun IESS')
    company_id = fields.Many2one('res.company', 'Compania')
    
#    contract_date = fields.Date(
#    compute='_get_date',
#    string='Inicio Contrato')

    @api.onchange('discount_amount')
    def onchange_discount_amount(self):
        if self.discount_amount:
            if self.discount_amount <=  self.pay_amountbackup:
                self.pay_amount = self.pay_amountbackup - self.discount_amount
            else:
                raise except_orm('Error!!', 'Valor a descontar es mayor a monto a pagar')

    @api.model
    def default_get(self, fields_list):
        res = super(hr_remuneration_employee, self).default_get(fields_list)
        user = self.env['res.users'].browse(self._uid)
        res['company_id'] = user.company_id.id
        return res

    @api.onchange('unbalance_amount')
    def onchange_unbalance_amount(self):
        if self.unbalance_amount:
            self.pay_amount += self.unbalance_amount
    
    @api.onchange('unbalance_time')
    def onchange_unbalance_time(self):
        if self.unbalance_time:
            self.worked_time += self.unbalance_time

    @api.onchange('unbalance_amount')
    def onchange_unbalance_amount(self):
        if self.unbalance_amount:
            self.pay_amount += self.unbalance_amount

    @api.multi
    def tenth_amount_calculate(self, type, employee_id, init_date, end_date):
        amount = 0.00
        days = 0
        if type == 'dc3':
            payslip = self.env['hr.payslip']
            slips = payslip.search([('employee_id', '=', employee_id), ('date_from', '>=', init_date),
                                    ('date_to', '<=', end_date), ('state', 'in', ['draft', 'done'])])

            for slip in slips:
                for line in slip.details_by_salary_rule_category:
                    if line.code == 'D3':
                        amount += line.total
                for line in slip.worked_days_line_ids:
                    if line.code != 'BA':
                        days += line.number_of_days

            acumulated_lines = self.env['hr.acumulados.line'].search([('acumulado_id.employee_id', '=', employee_id),
                                                                      ('inicio_mes.date_start', '>=', init_date),
                                                                      ('inicio_mes.date_start', '<=', end_date)])
            if acumulated_lines:
                for line in acumulated_lines:
                    amount += line.decimo3
                    days += line.dias_t

        elif type == 'dc4':
            # contract = self.env['hr.contract'].search([('employee_id', '=', employee_id)])
            employee = self.env['hr.employee'].browse(employee_id)
            contract = employee.contract_id
            mat_pat = self.env['hr.holidays'].search([('holiday_status_id.name', '=', 'LICENCIA SIN REMUNERACION MAT/PAT'),
                                                      ('employee_id', '=', employee_id)])
            mat_pat = self.period_mat_pat(mat_pat, init_date, end_date)
            if contract:
                controls = self.env['change.control'].search([('contract_id', '=', contract.id), ('change_date', '>', init_date),
                                               ('change_date', '<', end_date), ('change', 'in', ['horas_x_dia'])])
                if not mat_pat:
                    if controls:
                        aux_date = init_date
                        amount = 0.00
                        for control in controls:
                            a, days_ax = self.compute_values(init_date, contract, end_date, control.change_date, aux_date, 0, int(control.old_value), True)
                            amount += a
                            days += days_ax
                            break
                    else:
                        # if not contract.employee_id.emp_dec_cuarto:
                        horas = contract.horas_x_dia
                        thirdty_days_months_val = thirdty_days_months(parser.parse(contract.date_start).month, parser.parse(end_date).month)
                        if contract.date_start <= init_date:
                            amount = contract.horas_x_dia * self.env.user.company_id.base_amount / 8.00
                            days = 360
                        else:
                            amount, days = self.compute_values(init_date, contract, end_date, end_date, contract.date_start, thirdty_days_months_val, contract.horas_x_dia, False)
                else:
                    if controls:
                        if contract.date_start <= init_date:
                            for control in controls:
                                for lic in mat_pat:
                                    if lic.date_from > control.change_date and lic.date_to < end_date:
                                        lic_days = parser.parse(lic.date_to) - parser.parse(lic.date_from)
                                        days30 = thirty_days_months2(lic.date_from, lic.date_to)
                                        lic_days = lic_days.days.real - days30 + 1
                                        amount, days = self.compute_values3(init_date, control.change_date, control.old_value)
                                        amount2, days2 = self.compute_values3(control.change_date, end_date, contract.horas_x_dia, lic_days)
                                        amount += amount2
                                        days += days2
                                    elif lic.date_from > control.change_date and lic.date_to > end_date:
                                        lic_days = parser.parse(end_date) - parser.parse(lic.date_from)
                                        days30 = thirty_days_months2(lic.date_from, end_date)
                                        lic_days = lic_days.days.real - days30 + 1
                                        amount, days = self.compute_values3(init_date, control.change_date, control.old_value)
                                        amount2, days2 = self.compute_values3(control.change_date, end_date, contract.horas_x_dia, lic_days)
                                        amount += amount2
                                        days += days2
                                    elif end_date > lic.date_to < control.change_date and lic.date_from > init_date:
                                        lic_days = parser.parse(lic.date_to) - parser.parse(lic.date_from)
                                        days30 = thirty_days_months2(lic.date_from, lic.date_to)
                                        lic_days = lic_days.days.real - days30 + 1
                                        amount, days = self.compute_values3(init_date, control.change_date, control.old_value, lic_days)
                                        amount2, days2 = self.compute_values3(control.change_date, end_date, contract.horas_x_dia)
                                        amount += amount2
                                        days += days2
                                    elif end_date > lic.date_to < control.change_date and lic.date_from < init_date:
                                        lic_days = parser.parse(lic.date_to) - parser.parse(init_date)
                                        days30 = thirty_days_months2(init_date, lic.date_to)
                                        lic_days = lic_days.days.real - days30 + 1
                                        amount, days = self.compute_values3(init_date, control.change_date, control.old_value, lic_days)
                                        amount2, days2 = self.compute_values3(control.change_date, end_date, contract.horas_x_dia)
                                        amount += amount2
                                        days += days2
                                    break
                                break
                        else:
                            for control in controls:
                                for lic in mat_pat:
                                    if lic.date_from > control.change_date and lic.date_to < end_date:
                                        lic_days = parser.parse(lic.date_to) - parser.parse(lic.date_from)
                                        days30 = thirty_days_months2(lic.date_from, lic.date_to)
                                        lic_days = lic_days.days.real - days30 + 1
                                        amount, days = self.compute_values3(contract.date_start, control.change_date, control.old_value)
                                        amount2, days2 = self.compute_values3(control.change_date, end_date, contract.horas_x_dia, lic_days)
                                        amount += amount2
                                        days += days2
                                    elif lic.date_from > control.change_date and lic.date_to > end_date:
                                        lic_days = parser.parse(end_date) - parser.parse(lic.date_from)
                                        days30 = thirty_days_months2(lic.date_from, end_date)
                                        lic_days = lic_days.days.real - days30 + 1
                                        amount, days = self.compute_values3(contract.date_start, control.change_date, control.old_value)
                                        amount2, days2 = self.compute_values3(control.change_date, end_date, contract.horas_x_dia, lic_days)
                                        amount += amount2
                                        days += days2
                                    elif end_date > lic.date_to < control.change_date:
                                        lic_days = parser.parse(lic.date_to) - parser.parse(lic.date_from)
                                        days30 = thirty_days_months2(lic.date_from, lic.date_to)
                                        lic_days = lic_days.days.real - days30 + 1
                                        amount, days = self.compute_values3(contract.date_start, control.change_date, control.old_value, lic_days)
                                        amount2, days2 = self.compute_values3(control.change_date, end_date, contract.horas_x_dia, 0)
                                        amount += amount2
                                        days += days2
                                    break
                                break
                    else:
                        if contract.date_start <= init_date:
                            for lic in mat_pat:
                                if lic.date_from > init_date and lic.date_to < end_date:
                                    lic_days = parser.parse(lic.date_to) - parser.parse(lic.date_from)
                                    days30 = thirty_days_months2(lic.date_from, lic.date_to)
                                    lic_days = lic_days.days.real - days30 + 1
                                    amount, days = self.compute_values2(init_date, contract, end_date, False, False, contract.horas_x_dia, lic_days)
                                elif init_date < lic.date_from < end_date < lic.date_to:
                                    lic_days = parser.parse(end_date) - parser.parse(lic.date_from)
                                    days30 = thirty_days_months2(lic.date_from, end_date)
                                    lic_days = lic_days.days.real - days30 + 1
                                    amount, days = self.compute_values2(init_date, contract, end_date, False, False, contract.horas_x_dia, lic_days)
                                elif lic.date_from < init_date < lic.date_to < end_date:
                                    lic_days = parser.parse(lic.date_to) - parser.parse(init_date)
                                    days30 = thirty_days_months2(init_date, lic.date_to)
                                    lic_days = lic_days.days.real - days30 + 1
                                    amount, days = self.compute_values2(init_date, contract, end_date, False, False, contract.horas_x_dia, lic_days)
                                elif lic.date_from <= init_date and lic.date_to >= end_date:
                                    amount = days = 0
                                break
                        else:
                            for lic in mat_pat:
                                if end_date > contract.date_start < lic.date_from < end_date > lic.date_to:
                                    lic_days = parser.parse(lic.date_to) - parser.parse(lic.date_from)
                                    days30 = thirty_days_months2(lic.date_from, lic.date_to)
                                    lic_days = lic_days.days.real - days30 + 1
                                    amount, days = self.compute_values2(contract.date_start, contract, end_date, lic.date_to, False, contract.horas_x_dia, lic_days)
                                elif end_date > contract.date_start < lic.date_from < end_date < lic.date_to:
                                    lic_days = parser.parse(end_date) - parser.parse(lic.date_from)
                                    days30 = thirty_days_months2(lic.date_from, end_date)
                                    lic_days = lic_days.days.real - days30 + 1
                                    amount, days = self.compute_values2(contract.date_start, contract, end_date, lic.date_to, False, contract.horas_x_dia, lic_days)
                                break

        return amount, days

    def period_mat_pat(self, mat_pat, init_date, end_date):
        objects = list()
        for hd in mat_pat:
            if end_date < hd.date_from:
                continue
            elif init_date > hd.date_to:
                continue
            objects.append(hd)
        return objects

    @api.model
    def create(self, vals):
        vals['state'] = 'draft'
        return super(hr_remuneration_employee, self).create(vals)

    def compute_values3(self, init_date, end_date, hours, lic=0):
        amount = 0.00
        total_days = 0
        if int(hours) == 8:
            thirdty_days_months_val = thirty_days_months2(init_date, end_date)
            days_to_pay = parser.parse(end_date) - parser.parse(init_date)
            total_days = days_to_pay.days.real - thirdty_days_months_val + 1 - lic
            amount = total_days * (self.env.user.company_id.base_amount / 360)

        else:
            thirdty_days_months_val = thirty_days_months2(init_date, end_date)
            days_to_pay = parser.parse(end_date) - parser.parse(init_date)
            days_contract = int(hours) * 0.125
            days_ax = days_to_pay.days.real - thirdty_days_months_val - lic
            total_days = days_ax * days_contract
            amount = total_days * (self.env.user.company_id.base_amount / 360)
            total_days = days_ax
        return amount, total_days

    def compute_values(self, init_date, contract, end_date, change_date, aux_date, thirdty_days_months_val, hours, control):
        amount = 0.00
        total_days = 0
        feb = 0
        if parser.parse(end_date).month.real == 2:
            if parser.parse(end_date).day.real == 28:
                feb += 2
            else:
                feb += 1
        tot2 = 0
        if control:
            if contract.date_start <= init_date and change_date <= init_date:
                days_to_pay = parser.parse(end_date) - parser.parse(init_date)
                thirdty_days_months_val = thirty_days_months2(init_date, end_date)
                total_days = days_to_pay.days.real - thirdty_days_months_val + feb
                days_a1 = total_days
                if int(hours) == 8:
                    amount = total_days * (self.env.user.company_id.base_amount / 360)
                else:
                    days_contract = int(hours) * 0.125
                    total_days *= days_contract
                    amount = total_days * (self.env.user.company_id.base_amount / 360)
                total_days = days_a1

            elif contract.date_start <= init_date and init_date < change_date < end_date:
                days_to_pay = parser.parse(change_date) - parser.parse(init_date)
                thirdty_days_months_val = thirty_days_months2(init_date, change_date)
                total_days = days_to_pay.days.real - thirdty_days_months_val
                tot2 = total_days
                if int(hours) == 8:
                    amount = total_days * (self.env.user.company_id.base_amount / 360)
                else:
                    days_contract = int(hours) * 0.125
                    total_days *= days_contract
                    amount = total_days * (self.env.user.company_id.base_amount / 360)
                days_to_pay = parser.parse(end_date) - parser.parse(change_date)
                thirdty_days_months_val = thirty_days_months2(change_date, end_date)
                total_days = days_to_pay.days.real - thirdty_days_months_val + 1 + feb
                tot2 += total_days
                if int(contract.horas_x_dia) == 8:
                    amount += total_days * (self.env.user.company_id.base_amount / 360)
                else:
                    days_contract = int(contract.horas_x_dia) * 0.125
                    total_days *= days_contract
                    amount += total_days * (self.env.user.company_id.base_amount / 360)
                total_days = tot2
            elif contract.date_start > init_date and init_date < change_date < end_date:
                days_to_pay = parser.parse(change_date) - parser.parse(contract.date_start)
                thirdty_days_months_val = thirty_days_months2(contract.date_start, change_date)
                total_days = days_to_pay.days.real - thirdty_days_months_val
                tot2 = total_days
                if int(hours) == 8:
                    amount = total_days * (self.env.user.company_id.base_amount / 360)
                else:
                    days_contract = int(hours) * 0.125
                    total_days *= days_contract
                    amount = total_days * (self.env.user.company_id.base_amount / 360)
                days_to_pay = parser.parse(end_date) - parser.parse(change_date)
                thirdty_days_months_val = thirty_days_months2(change_date, end_date)
                total_days = days_to_pay.days.real - thirdty_days_months_val + 1 + feb
                tot2 += total_days
                if int(contract.horas_x_dia) == 8:
                    amount += total_days * (self.env.user.company_id.base_amount / 360)
                else:
                    days_contract = int(hours) * 0.125
                    total_days *= days_contract
                    amount += total_days * (self.env.user.company_id.base_amount / 360)
                total_days = tot2
            elif contract.date_start > init_date and change_date > end_date:
                days_to_pay = parser.parse(end_date) - parser.parse(contract.date_start)
                thirdty_days_months_val = thirty_days_months2(contract.date_start, end_date)
                total_days = days_to_pay.days.real - thirdty_days_months_val + feb
                tot2 = total_days
                if int(hours) == 8:
                    amount = total_days * (self.env.user.company_id.base_amount / 360)
                else:
                    days_contract = int(hours) * 0.125
                    total_days *= days_contract
                    amount = total_days * (self.env.user.company_id.base_amount / 360)
                total_days = tot2
            elif contract.date_start < init_date and change_date > end_date:
                days_to_pay = parser.parse(end_date) - parser.parse(init_date)
                thirdty_days_months_val = thirty_days_months2(init_date, end_date)
                total_days = days_to_pay.days.real - thirdty_days_months_val + 1 +feb
                tot2 = total_days
                # if int(contract.horas_x_dia) == 5:
                #     hrs_parcial = self.env.user.company_id.base_amount * 5 / 8
                #     amount = total_days * (hrs_parcial / 360)
                if int(hours) == 8:
                    amount = total_days * (self.env.user.company_id.base_amount / 360)
                else:
                    days_contract = int(hours) * 0.125
                    total_days *= days_contract
                    amount = total_days * (self.env.user.company_id.base_amount / 360)
                total_days = tot2

            return amount, total_days

        elif init_date < contract.date_start < end_date and hours == 8:
            days_to_pay = parser.parse(change_date) - parser.parse(aux_date)
            total_days = days_to_pay.days.real + thirdty_days_months_val + 1
            amount = total_days * (self.env.user.company_id.base_amount / 360)

        elif init_date < contract.date_start < end_date and hours != 8:
            days_to_pay = parser.parse(change_date) - parser.parse(aux_date)
            days_contract = hours * 0.125
            days_ax = days_to_pay.days.real + thirdty_days_months_val + 1
            total_days = days_ax * days_contract
            amount = total_days * (self.env.user.company_id.base_amount / 360)
            total_days = days_ax
        return amount, total_days

    def compute_values2(self, init_date, contract, end_date, change_date, aux_date, hours, lic=0):
        amount = 0.00
        total_days = 0
        if contract.date_start <= init_date and hours == 8:
            thirdty_days_months_val = thirty_days_months2(init_date, end_date)
            days_to_pay = parser.parse(end_date) - parser.parse(init_date)
            total_days = days_to_pay.days.real - thirdty_days_months_val + 1 - lic
            amount = total_days * (self.env.user.company_id.base_amount / 360)

        elif contract.date_start <= init_date and hours != 8:
            thirdty_days_months_val = thirty_days_months2(init_date, end_date)
            days_to_pay = parser.parse(end_date) - parser.parse(init_date)
            days_contract = hours * 0.125
            days_ax = days_to_pay.days.real - thirdty_days_months_val + 1 - lic
            total_days = days_ax * days_contract
            amount = total_days * (self.env.user.company_id.base_amount / 360)
            total_days = days_ax

        elif contract.date_start < end_date > change_date and hours == 8:
            thirdty_days_months_val = thirty_days_months2(init_date, end_date)
            days_to_pay = parser.parse(end_date) - parser.parse(init_date)
            total_days = days_to_pay.days.real - thirdty_days_months_val + 1 - lic
            amount = total_days * (self.env.user.company_id.base_amount / 360)

        elif contract.date_start < end_date > change_date and hours != 8:
            thirdty_days_months_val = thirty_days_months2(init_date, end_date)
            days_to_pay = parser.parse(end_date) - parser.parse(init_date)
            days_contract = hours * 0.125
            days_ax = days_to_pay.days.real + thirdty_days_months_val + 1 - lic
            total_days = days_ax * days_contract
            amount = total_days * (self.env.user.company_id.base_amount / 360)
            total_days = days_ax

        elif contract.date_start < end_date < change_date and hours == 8:
            thirdty_days_months_val = thirty_days_months2(init_date, end_date)
            days_to_pay = parser.parse(end_date) - parser.parse(init_date)
            total_days = days_to_pay.days.real - thirdty_days_months_val + 1 - lic
            amount = total_days * (self.env.user.company_id.base_amount / 360)

        elif contract.date_start < end_date < change_date and hours != 8:
            thirdty_days_months_val = thirty_days_months2(init_date, end_date)
            days_to_pay = parser.parse(end_date) - parser.parse(init_date)
            days_contract = hours * 0.125
            days_ax = days_to_pay.days.real + thirdty_days_months_val + 1 - lic
            total_days = days_ax * days_contract
            amount = total_days * (self.env.user.company_id.base_amount / 360)
            total_days = days_ax
        return amount, total_days
    
    #O2SGH150316: Fecha de inicio de contrato     
#    @api.one
#    def _get_date(self):
#        for contract in self.employee_id.contract_ids:
#            self.contract_date = contract.date_start 
