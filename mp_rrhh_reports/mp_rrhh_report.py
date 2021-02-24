# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution - Ecuador
#    Copyright (C) 2020 MissionPetroleum Daniel Aldaz (<daldaz@mission-petroleum.com>).
#
##############################################################################

import base64
import cStringIO
from openerp import models, fields, api
import xlwt as pycel


class HrPayrollReport(models.TransientModel):
    _name = 'hr.payroll.report'
    _description = 'Reporte Nomina Borrador'

    @api.multi
    def default_company(self):
        return self.env.user.company_id.id

    type_export = fields.Selection([('xls', 'EXCEL')], 'Tipo de archivo', required=True, default='xls')
    data = fields.Binary('Archivo', filters=None)
    path = fields.Char('Ruta')
    company_id = fields.Many2one('res.company', 'Compania', required=True, default=default_company)
    fiscal_year_id = fields.Many2one('hr.fiscalyear')
    period_id = fields.Many2one('hr.period.period', 'Periodo', domain="[('fiscalyear_id','=', fiscal_year_id)]")
    employee_id = fields.Many2one('hr.employee', 'Empleado')

    @api.multi
    def get_in_out_name(self, period_id):
        in_values = []
        exp_values = []
        if period_id:
            date_start = self.period_id.date_start
            date_stop = self.period_id.date_stop
            incoming_obj = self.env['hr.income'].search([('date', '>=', date_start), ('date', '<=', date_stop)])
            expense_obj = self.env['hr.expense'].search([('date', '>=', date_start), ('date', '<=', date_stop)])
            permanent_entry = self.env['hr.income'].search([('fijo', '=', True)])
            permanent_expense = self.env['hr.expense'].search([('fijo', '=', True)])
            for ing in incoming_obj:
                if ing.adm_id.id not in in_values:
                    in_values.append(ing.adm_id.id)
            for entry in permanent_entry:
                if entry.adm_id.id not in in_values:
                    in_values.append(entry.adm_id.id)
            in_values = tuple(in_values)
            incoming = self.env['hr.adm.incomes'].search([('id', 'in', in_values)], order="id")
            for exp in expense_obj:
                if exp.expense_type_id.id not in exp_values:
                    exp_values.append(exp.expense_type_id.id)
            for expense in permanent_expense:
                if expense.expense_type_id.id not in exp_values:
                    exp_values.append(expense.expense_type_id.id)
            exp_values = tuple(exp_values)
            expense = self.env['hr.expense.type'].search([('id', 'in', exp_values)], order="id")
            return incoming, expense

    @api.multi
    def set_header(self, ws, xi, style_header):

        xo = 5
        incomes = self.get_in_out_name(self.period_id)[0]
        expenses = self.get_in_out_name(self.period_id)[1]
        ws.write(xi, 1, 'EMPLEADO', style_header)
        ws.write(xi, 2, 'CEDULA', style_header)
        ws.write(xi, 3, 'DIAS', style_header)
        ws.write(xi, 4, 'SUELDO', style_header)
        for record in incomes:
            ws.write(xi, xo, record.name, style_header)
            xo += 1
        ws.write(xi, xo, 'F. RESERVA', style_header)
        xo += 1
        ws.write(xi, xo, 'D. TERCERO', style_header)
        xo += 1
        ws.write(xi, xo, 'D. CUARTO', style_header)
        xo += 1
        ws.write(xi, xo, 'AP. IESS', style_header)
        xo += 1
        for record in expenses:
            ws.write(xi, xo, record.name, style_header)
            xo += 1
        ws.write(xi, xo, 'BASE IESS', style_header)
        xo += 1
        ws.write(xi, xo, 'SUB. INGRESOS', style_header)
        xo += 1
        ws.write(xi, xo, 'SUB. EGRESOS', style_header)
        xo += 1
        ws.write(xi, xo, 'TOTAL', style_header)
        xo += 1
        col = 13

        return col

    @api.multi
    def get_Values_by_Employee(self, employee, period_id):
        domain = [('date', '>=', period_id.date_start), ('date', '<=', period_id.date_stop),
                  ('employee_id', '=', employee.id)]
        adm_domain = [('fijo', '=', True), ('employee_id', '=', employee.id)]
        exp_domain = [('fijo', '=', True), ('employee_id', '=', employee.id)]
        in_values = []
        exp_values = []
        amd_ids = self.env['hr.income'].search(domain, order='adm_id')
        exp_ids = self.env['hr.expense'].search(domain, order='expense_type_id')
        amd_ids_1 = self.env['hr.income'].search(adm_domain, order='adm_id')
        exp_ids_1 = self.env['hr.expense'].search(exp_domain, order='expense_type_id')
        for adm in amd_ids:
            in_values.append(adm.id)
        for adm1 in amd_ids_1:
            in_values.append(adm1.id)
        for exp in exp_ids:
            exp_values.append(exp.id)
        for exp1 in exp_ids_1:
            exp_values.append(exp1.id)
        in_values = tuple(in_values)
        exp_values = tuple(exp_values)
        amd_ids = self.env['hr.income'].search([('id', 'in', in_values)], order='adm_id')
        exp_ids = self.env['hr.expense'].search([('id', 'in', exp_values)], order='expense_type_id')
        return amd_ids, exp_ids

    @api.multi
    def get_some_values(self, employee):
        value = 0
        all_entries = 0
        all_discounts = 0
        wage = self.get_worked_days(employee, self.period_id)[1]
        domain = [('date', '>=', self.period_id.date_start), ('date', '<=', self.period_id.date_stop),
                  ('employee_id', '=', employee.id)]
        amd_ids = self.env['hr.income'].search(domain, order='adm_id')
        domain_1 = [('fijo', '=', True), ('employee_id', '=', employee.id)]
        amd_ids_1 = self.env['hr.income'].search(domain_1, order='adm_id')
        expense_ids = self.env['hr.expense'].search(domain, order='expense_type_id')
        expense_ids_1 = self.env['hr.expense'].search([('fijo', '=', True), ('employee_id', '=', employee.id)],
                                                      order='expense_type_id')
        for exp in expense_ids:
            all_discounts += exp.value
        for exp in expense_ids_1:
            all_discounts += exp.value
        for adm in amd_ids:
            all_entries += adm.value
            if not adm.adm_id.not_generate_benefits:
                value += adm.value
        for adm in amd_ids_1:
            all_entries += adm.value
            if not adm.adm_id.not_generate_benefits:
                value += adm.value
	sum_all_entries = all_entries + wage
        summary = value + wage
        sum_all_discounts = all_discounts
        return summary, sum_all_entries, sum_all_discounts, wage

    @api.multi
    def get_month_values(self, employee):
        fourth_value = float(0)
        third_value = float(0)
        reserve_fund = float(0)
        input_value = float(0)
        ies_base = int(0)
        total_entries = int(0)
        total_discounts = int(0)
        total = int(0)
        basic_wage = self.company_id.base_amount
        hours = employee.contract_id.horas_x_dia
        worked_days = self.get_worked_days(employee, self.period_id)[0]
        summary = self.get_some_values(employee)[0]
        sum_all_entries = self.get_some_values(employee)[1]
        sum_all_discounts = self.get_some_values(employee)[2]
        if employee.emp_dec_cuarto:
            fourth_value = (basic_wage * worked_days * hours) / 2880
            round(fourth_value, 2)
        if not employee.emp_fondo_reserva and int(employee.contract_id.number_of_year) > 1:
            reserve_fund = (summary * 8.33) / 100
        if employee.emp_dec_tercero:
            third_value = summary / 12
        if employee:
            input_value = (summary * 9.45) / 100
            ies_base = summary
            total_entries = sum_all_entries
	    if employee.emp_dec_cuarto:
		total_entries = total_entries + fourth_value
	    if not employee.emp_fondo_reserva and int(employee.contract_id.number_of_year) >= 1:
		total_entries = total_entries + reserve_fund
            total_discounts = sum_all_discounts + input_value
            total = total_entries - total_discounts
        return float(round(reserve_fund, 2)), float(round(third_value, 2)), float(round(fourth_value, 2)), \
               float(round(input_value, 2)), float(round(ies_base, 2)), float(round(total_entries, 2)), \
               float(round(total_discounts, 2)), float(round(total, 2))

    @api.multi
    def set_body(self, employees, incomes, expenses, worked_days, ws, xi, linea_der, linea_izq, seq, linea_izq_n,
                 linea_izq_neg, view_style, linea_der_bold, view_style_out):

        for emp in employees:
            xe = 5
            in_values = []
            ing_vals = []
            no_rep_values = []
            sum_values = []
            des_values = []
            adm_ids = self.get_in_out_name(self.period_id)[0]
            incomes = self.get_Values_by_Employee(emp, self.period_id)[0]
            last_id = False
            count_in = 1
            if not incomes:
                for ing in adm_ids:
                    ws.write(xi, xe, float(0), linea_der)
                    xe += 1
            for emp_ing in incomes:
                in_values.append(emp_ing.adm_id.id)
                if emp_ing.adm_id.id == last_id and last_id:
                    count_in += 1
                last_id = emp_ing.adm_id.id
            in_values = tuple(in_values)
            ws.write(xi, 1, emp.name_related, linea_izq)
            ws.write(xi, 2, '[' + emp.identification_id + ']', linea_izq)
            ws.write(xi, 3, worked_days, linea_izq)
	    ws.write(xi, 4, self.get_some_values(emp)[3], linea_der)
            check = False
            last_id = False
            last_ing_id = False
            value = 0
            for ing in adm_ids:
                for emp_ing in incomes:
                    if emp_ing.adm_id.id == ing.id:
                        continue
                    else:
                        if ing.id not in des_values and ing.id not in in_values:
                            des_values.append(ing.id)
                    if emp_ing.adm_id.id == last_id and last_id and last_id in sum_values and last_ing_id != emp_ing.id:
                        if len(sum_values) <= count_in:
                            value += emp_ing.value
                            check = True
                    last_ing_id = emp_ing.id
                    last_id = emp_ing.adm_id.id
                    sum_values.append(emp_ing.adm_id.id)
            des_values = tuple(des_values)
            for ing in adm_ids:
                for emp_ing in incomes:
                    if emp_ing.adm_id.id == ing.id and emp_ing.adm_id.id not in ing_vals:
                        ing_vals.append(emp_ing.adm_id.id)
                        if check:
                            ws.write(xi, xe, float(round(value, 2)), linea_der)
                        else:
                            ws.write(xi, xe, emp_ing.value, linea_der)
                        xe += 1
                    elif ing.id in des_values and ing.id not in no_rep_values:
                        no_rep_values.append(ing.id)
                        ws.write(xi, xe, float(0), linea_der)
                        xe += 1

            ws.write(xi, xe, self.get_month_values(emp)[0], linea_der)
            xe += 1
            ws.write(xi, xe, self.get_month_values(emp)[1], linea_der)
            xe += 1
            ws.write(xi, xe, self.get_month_values(emp)[2], linea_der)
            xe += 1
            ws.write(xi, xe, self.get_month_values(emp)[3], linea_der)
            xe += 1
            exp_values = []
            exp_vals = []
            no_rep_values = []
            sum_values = []
            des_values = []
            expense_ids = self.get_in_out_name(self.period_id)[1]
            expenses = self.get_Values_by_Employee(emp, self.period_id)[1]
            last_id = False
            count_out = 1
            if not expenses:
                for exp in expense_ids:
                    ws.write(xi, xe, float(0), linea_der)
                    xe += 1
            for emp_exp in expenses:
                exp_values.append(emp_exp.expense_type_id.id)
                if emp_exp.expense_type_id.id == last_id and last_id:
                    count_out += 1
                last_id = emp_exp.expense_type_id.id
            exp_values = tuple(exp_values)
            check = False
            last_id = False
            last_ing_id = False
            value = 0
            for exp in expense_ids:
                for emp_exp in expenses:
                    if emp_exp.expense_type_id.id == exp.id:
                        continue
                    else:
                        if exp.id not in des_values and exp.id not in exp_values:
                            des_values.append(exp.id)
                    if emp_exp.expense_type_id.id == last_id and last_id and last_id in sum_values and last_ing_id != emp_exp.id:
                        if len(sum_values) <= count_out:
                            value += emp_exp.value
                            check = True
                    last_ing_id = emp_exp.id
                    last_id = emp_exp.expense_type_id.id
                    sum_values.append(emp_exp.expense_type_id.id)
            des_values = tuple(des_values)
            for exp in expense_ids:
                for emp_exp in expenses:
                    if emp_exp.expense_type_id.id == exp.id and emp_exp.expense_type_id.id not in exp_vals:
                        exp_vals.append(emp_exp.expense_type_id.id)
                        if check:
                            ws.write(xi, xe, value, linea_der)
                        else:
                            ws.write(xi, xe, emp_exp.value, linea_der)
                        xe += 1
                    elif exp.id in des_values and exp.id not in no_rep_values:
                        no_rep_values.append(exp.id)
                        ws.write(xi, xe, float(0), linea_der)
                        xe += 1
            ws.write(xi, xe, self.get_month_values(emp)[4], linea_der)
            xe += 1
            ws.write(xi, xe, self.get_month_values(emp)[5], linea_der)
            xe += 1
            ws.write(xi, xe, self.get_month_values(emp)[6], linea_der)
            xe += 1
            ws.write(xi, xe, self.get_month_values(emp)[7], linea_der)

    @api.multi
    def get_data(self):
        date_from = self.period_id.date_start
        date_to = self.period_id.date_stop
        income_obj = self.env['hr.income']
        expense_obj = self.env['hr.expense']
        employee_data = []
        in_domain = [('date', '>=', date_from), ('date', '<=', date_to)]
        exp_domain = [('date', '>=', date_from), ('date', '<=', date_to)]
        if not self.employee_id:
            employee_data = self.env['hr.employee'].search([('active', '=', True), ('state_emp', '=', 'active')])
        if self.employee_id:
            employee_data = self.employee_id
        income_data = income_obj.search(in_domain, order='adm_id')
        expense_data = expense_obj.search(exp_domain, order='expense_type_id')

        return employee_data, income_data, expense_data

    @api.multi
    def get_worked_days(self, employee_id, period_id):
        days = 0
        if employee_id:
            hr_holidays_obj = self.env['hr.holidays'].search([('employee_id', '=', employee_id.id),
                                                              ('date_from', '>=', period_id.date_start),
                                                              ('date_to', '<=', period_id.date_stop)])
            for record in hr_holidays_obj:
                if record.state == 'validate':
                    days += record.number_of_days_temp
            days = 30 - days
            wage = (employee_id.contract_id.wage * days) / 30
            return days, wage

    @api.one
    def excel_action(self):
        wb = pycel.Workbook(encoding='utf-8')

        style_cabecera = pycel.easyxf('font: colour black, bold True;'
                                      'align: vertical center, horizontal center;'
                                      )
        style_header = pycel.easyxf('font: bold True;'
                                    'align: vertical center, horizontal center, wrap on;'
                                    'borders: left 1, right 1, top 1, bottom 1;')

        view_style = pycel.easyxf('font: colour green, bold true, height 200;'
                                  'align: vertical center, horizontal center, wrap on;'
                                  'borders: left 1, right 1, top 1, bottom 1;'
                                  )
        linea_izq = pycel.easyxf('font: colour black, height 150;'
                                 'align: vertical center, horizontal left, wrap on;'
                                 'borders: left 1, right 1, top 1, bottom 1;'
                                 )
        linea_izq_n = pycel.easyxf('font: colour black, height 140;'
                                   'align: vertical center, horizontal center, wrap on;'
                                   'borders: left 1, right 1, top 1, bottom 1;'
                                   )
        linea_izq_neg = pycel.easyxf('font: colour black, bold true, height 200;'
                                     'align: vertical center, horizontal left, wrap on;'
                                     'borders: left 1, right 1, top 1, bottom 1;'
                                     )
        linea_der = pycel.easyxf('font: colour black, height 150;'
                                 'align: vertical center, horizontal right;'
                                 'borders: left 1, right 1, top 1, bottom 1;'
                                 )
        linea_der_bold = pycel.easyxf('font: colour black, bold true, height 200;'
                                      'align: vertical center, horizontal right, wrap on;'
                                      'borders: left 1, right 1, top 1, bottom 1;'
                                      )
        view_style_out = pycel.easyxf('font: colour red, bold true, height 200;'
                                      'align: vertical center, horizontal center, wrap on;'
                                      'borders: left 1, right 1, top 1, bottom 1;'
                                      )

        ws = wb.add_sheet('Reporte Nomina')

        ws.show_grid = False
        ws.header_str = u"&LFecha de Impresion: &D Hora: &T&RPagina &P de &N"
        ws.footer_str = u""
        company = self.env['res.users'].browse(self._uid).company_id
        ws.write_merge(1, 1, 1, 5, company.name, style_cabecera)
        ws.write_merge(2, 2, 1, 5, 'Fecha desde: ' + self.period_id.date_start + ' - ' + 'Fecha hasta: ' +
                       self.period_id.date_stop + ' ', style_cabecera)
        ws.write_merge(3, 3, 1, 5, 'REPORTE NOMINA BORRADOR', style_cabecera)

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

        # Formato de Numero
        style = pycel.XFStyle()
        style.num_format_str = '#,##0.00'
        style.alignment = align
        style.font = font1

        # Formato de Numero Saldo
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

        xi = 5  # Cabecera de Cliente
        self.set_header(ws, xi, style_header)
        xi += 1
        data_file_name = "ReporteNominaBorrador.xls"
        seq = 0
        employee_orders = self.get_data()[0]
        income = ''
        expense = ''
        # columns = [9, 10, 11, 12]
        # total_formula = ['SUBTOTAL(9,J10:J{0})', 'SUBTOTAL(9,K10:K{0})', 'SUBTOTAL(9,L10:L{0})', 'SUBTOTAL(9,M10:M{0})']
        # stock_move_obj = self.env['stock.move']
        # importation_order_line = self.env['importation.order.line']
        for employee in employee_orders:
            worked_days = self.get_worked_days(employee, self.period_id)[0]
            self.set_body(employee, income, expense, worked_days, ws, xi, linea_der, linea_izq, seq,
                          linea_izq_n, linea_izq_neg, view_style, linea_der_bold, view_style_out)
            xi += 1

        # ws.write(xi, 7, 'TOTAL', view_style)
        # ws.write(xi, columns[0], xlwt.Formula(total_formula[0].format(xi)), linea_der_bold)
        # ws.write(xi, columns[1], xlwt.Formula(total_formula[1].format(xi)), linea_der_bold)
        # ws.write(xi, columns[2], xlwt.Formula(total_formula[2].format(xi)), linea_der_bold)
        # ws.write(xi, columns[3], xlwt.Formula(total_formula[3].format(xi)), linea_der_bold)

        ws.col(0).width = 1000
        ws.col(1).width = 11000
        ws.col(2).width = 3000
        ws.col(3).width = 1500
        ws.col(4).width = 2500
        ws.col(5).width = 3500
        ws.col(6).width = 3500
        ws.col(7).width = 3500
        ws.col(8).width = 3500
        ws.col(9).width = 3500
        ws.col(10).width = 3500
        ws.col(11).width = 3500
        ws.col(12).width = 3500
        ws.col(13).width = 3500
        ws.col(14).width = 3500
        ws.col(15).width = 3500
        ws.col(16).width = 3500
        ws.col(17).width = 3500
        ws.col(18).width = 3500
        ws.col(19).width = 3500
        ws.col(20).width = 3500
        ws.col(21).width = 3500
        ws.col(22).width = 3500
        ws.col(23).width = 3500
        ws.col(24).width = 3500
        ws.col(25).width = 3500
        ws.col(26).width = 3500
        ws.col(27).width = 3500
        ws.col(28).width = 3500
        ws.col(29).width = 3500
        ws.col(30).width = 3500
        ws.row(9).height = 950

        try:
            buf = cStringIO.StringIO()

            wb.save(buf)
            out = base64.encodestring(buf.getvalue())
            buf.close()
            res_model = 'hr.payroll.report'
            self.load_doc(out, data_file_name, res_model)

            return self.write({'data': out, 'txt_filename': data_file_name, 'name': 'reporte_nomina_borrador.xls'})

        except ValueError:
            raise Warning('Error a la hora de salvar el archivo')

    @api.one
    def load_doc(self, out, data_file_name, res_model):
        attach_vals = {
            'name': data_file_name,
            'datas_fname': data_file_name,
            'res_model': res_model,
            'datas': out,
            'type': 'binary',
            'file_type': 'file_type',
        }
        if self.id:
            attach_vals.update({'res_id': self.id})
        self.env['ir.attachment'].create(attach_vals)


HrPayrollReport()
