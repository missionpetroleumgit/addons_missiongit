# -*- coding: utf-8 -*-
from openerp import models, fields, api
import base64
import StringIO
from datetime import datetime
from openerp.exceptions import except_orm
from dateutil.relativedelta import *
from dateutil import parser


def _get_years(self):
    year = datetime.today().year
    domain = list()
    for val in range(year - 5, year + 6):
        domain.append((str(val), str(val)))
    return domain


class exel_utilities(models.TransientModel):
    _name = 'exel.utilities'

    name = fields.Char('Nombre')
    year = fields.Selection(_get_years, string='Año a analizar')
    txt_binary = fields.Binary()

    @api.multi
    def generate_file(self):
        user = self.env['res.users'].browse(self._uid)
        contract_env = self.env['hr.contract']
        for record in self:
            file_txt = StringIO.StringIO()
            ids = self._context['active_ids']
            file_txt.write(self.header_string())
            for employee in self.env['hr.employee'].browse(ids):
                fiscalyear = self.env['hr.fiscalyear'].search([('code', '=', record.year)])
                if not fiscalyear:
                    raise except_orm('Error', 'No existe ningun ejercicio fiscal con el codigo %s' % record.year)
                fiscalyear = fiscalyear[0]
                contract = contract_env.search([('employee_id', '=', employee.id)])
                if not contract:
                    continue
                if contract.date_end and contract.date_end <= fiscalyear.date_start:
                    continue
                file_txt.write(self.set_string(self.get_data(employee, record.year, user)))
            out = base64.encodestring(file_txt.getvalue().encode('utf-8'))
            file_txt.close()
            record.txt_binary = out
            record.name = 'Archivo Utilidades(%s).csv' % datetime.now().strftime('%Y%m%d%H%M%S')
            return {
                'name': 'Archivo Generado',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'exel.utilities',
                'res_id': record.id,
                'view_id': False,
                'type': 'ir.actions.act_window',
                'domain': [],
                'target': 'new',
                'context': self._context,
            }

    def get_data(self, obj, year, user):
        data = self.get_data_contract(obj.id)
        data = data[0]
        type_reserve = 'FDRP'
        if obj.emp_fondo_reserva:
            type_reserve = 'FDRT'
        vals = {
            'column1': obj.identification_id or '-',
            'column2': obj.emp_nombres.encode('utf-8') or '-',
            'column3': obj.emp_apellidos.encode('utf-8') or '-',
            'column4': self.return_gender(obj.gender) or '-',
            'column5': obj.job_id.name or '-',#ocupacion
            'column6': str(self.get_familyburden(obj, year)),#Cargas familiares
            'column7': str(int(self.get_labor_days(year, obj)[0])),#Dias Laborados
            ##
            'column8': self.return_payment(obj.emp_modo_pago) or '-',#Tipo de Pago Utilidad
            'column9': data['jpperm'],#Jornada Parcial Permanente
            'column10': data['hours'],#Horas Estipuladas Jornada Parcial
            'column11': data['discap'],#Discapacidad
            'column12': user.company_id.partner_id.part_number or '-',#RUC de la empresa complementaria
            'column13': str(self.get_tenth(year, obj, 'D3')[0]),#Decimo Tercero
            ##
            'column14': str(self.get_tenth(year, obj, 'D4')[0]),#Decimo Cuarto
            'column15': '',#Participacion de Utilidades
            'column16': str(round(self.get_other_payments(year, obj, 'IGBS')[0], 2)),#Salarios Percibidos, Aqui se estan sumando todas categorias igbs del rol
            'column17': str(self.get_other_payments(year, obj, type_reserve)[0]),#Fondos de Reserva
            'column18': '',#Comisiones
            'column19': '',#Beneficios Adicionales en Efectivo
            'column20': '',#Anticipo de Utilidad
            'column21': '',#Retencion Judicial
            'column22': str(self.get_other_payments(year, obj, 'EGRRFT')[0]),#Impuesto Retencion
            'column23': '',#Informacion MDT
            'column24': '',#Tipo de Pago Salario Digno
        }
        return vals

    @api.one
    def get_labor_days(self, year, employee):
        days = 0
        fiscalyear = self.env['hr.fiscalyear'].search([('code', '=', year)])
        if not fiscalyear:
            raise except_orm('Error', 'No existe ningun ejercicio fiscal con el codigo %s' % year)
        fiscalyear = fiscalyear[0]
        lines = self.env['hr.payslip.worked_days'].search([('payslip_id.employee_id', '=', employee.id), ('code', 'in', ('WORK100', 'ENFERMEDAD', 'PERMISOS PERSONALES')), ('payslip_id.date_from', '>=', fiscalyear.date_start),
                                                           ('payslip_id.date_to', '<=', fiscalyear.date_stop)])
        for line in lines:
            days += line.number_of_days
        if days > 360:
            days = 360
        return days

    def get_familyburden(self, employee, year):
        fiscalyear = self.env['hr.fiscalyear'].search([('code', '=', year)])
        if not fiscalyear:
            raise except_orm('Error', 'No existe ningun ejercicio fiscal con el codigo %s' % year)
        number = 0
        for burd in employee.child_ids:
            if not burd.birth_date:
                raise except_orm('Error!', 'El familiar %s asociado al empleado %s no tiene fecha de nacimiento insertada' % (burd.name, employee.name))
            age = (parser.parse(fiscalyear.date_start) - parser.parse(burd.birth_date)).days / 365
            if burd.relationship == 'child' and age > 18 and not burd.has_disability:
                continue
            number += 1
        return number

    @api.one
    def get_tenth(self, year, employee, tenth_type):
        amount = 0.00
        remuneration_env = self.env['hr.remuneration.employee']
        fiscalyear = self.env['hr.fiscalyear'].search([('code', '=', year)])
        if not fiscalyear:
            raise except_orm('Error', 'No existe ningun ejercicio fiscal con el codigo %s' % year)
        fiscalyear = fiscalyear[0]
        date_from = fiscalyear.date_start
        date_to = fiscalyear.date_stop
        if tenth_type == 'D3':
            my_type = 'dc3'
        else:
            my_type = 'dc4'
        remuneration = remuneration_env.search([('decimo_type', '=', my_type), ('employee_id', '=', employee.id), ('periodo_final', '>', date_from),
                                                ('periodo_final', '<', date_to)])
        if remuneration:
            amount = remuneration.pay_amount
        return round(amount, 2)

    @api.one
    def get_other_payments(self, year, employee, tenth_type):
        amount = 0.00
        acumulates_env = self.env['hr.acumulados']
        fiscalyear = self.env['hr.fiscalyear'].search([('code', '=', year)])
        if not fiscalyear:
            raise except_orm('Error', 'No existe ningun ejercicio fiscal con el codigo %s' % year)
        fiscalyear = fiscalyear[0]
        date_from = fiscalyear.date_start
        date_to = fiscalyear.date_stop
        # if tenth_type in ('D3', 'D4'):
        #     acumulates = acumulates_env.search([('employee_id', '=', employee.id)])
        #     if tenth_type == 'D4':
        #         if employee.region == 'sierra':
        #             date_from = fiscalyear.company_id.fecha_init_sierra
        #             date_to = fiscalyear.company_id.fecha_fin_sierra
        #         elif employee.region == 'costa':
        #             date_from = fiscalyear.company_id.fecha_init_costa
        #             date_to = fiscalyear.company_id.fecha_fin_costa
        #         for acumulate in acumulates:
        #             for line in acumulate.acumulados_line:
        #                 if date_from <= line.inicio_mes.date_start <= date_to:
        #                     amount += line.decimo4
        #     elif tenth_type == 'D3':
        #         date_from = parser.parse(fiscalyear.company_id.period_decimo3_pay.date_start) - relativedelta(months=11)
        #         date_from = date_from.strftime('%Y-%m-%d')
        #         date_to = fiscalyear.company_id.period_decimo3_pay.date_stop
        #         for acumulate in acumulates:
        #             for line in acumulate.acumulados_line:
        #                 if date_from <= line.inicio_mes.date_start <= date_to:
        #                     amount += line.decimo3
        if tenth_type == 'IGBS':
            lines = self.env['hr.payslip.line'].search([('slip_id.employee_id', '=', employee.id), ('category_id.code', '=', tenth_type), ('slip_id.date_from', '>=', date_from),
                                                    ('slip_id.date_to', '<=', date_to)])
        else:
            lines = self.env['hr.payslip.line'].search([('slip_id.employee_id', '=', employee.id), ('code', '=', tenth_type), ('slip_id.date_from', '>=', date_from),
                                                        ('slip_id.date_to', '<=', date_to)])
        for line in lines:
            amount += line.total
        return amount

    @api.one
    def get_data_contract(self, employee):
        data = {
            'jpperm': '-',
            'hours': '-',
            'discap': '-'
        }
        contract = self.pool.get('hr.contract')
        contract_id = contract.search(self._cr, self._uid, [('employee_id', '=', employee)])
        if contract_id:
            contract_id = contract_id[0]
            obj_contract = contract.browse(self._cr, self._uid, contract_id)
            if obj_contract.working_hours.name == 'Horario Normal 240 H/M':
                data['jpperm'] = '-'
                data['hours'] = '-'
            else:
                data['jpperm'] = 'X'
                data['hours'] = str(5*obj_contract.horas_x_dia)
            if obj_contract.employee_id.emp_discapacidad:
                data['discap'] = 'X'
            else:
                data['discap'] = '-'
        return data

    def header_string(self):
        string = "CEDULA" + "," + "NOMBRES" + "," + "APELLIDOS" + "," + "GENERO" + "," + "OCUPACION" + "," + "CARGAS FAMILIARES" + "," + "DIAS LABORADOS" + "," + "TIPO DE PAGO UTILIDAD" + "," + \
                 "JORNADA PARCIAL PERMANENTE" + "," + "HORAS ESTIPULADAS JORNADA PARCIAL" + "," + "DISCAPACIDAD" + "," + "RUC DE LA EMPRESA COMPLEMENTARIA O DE UNIFICACION" + "," + \
                 "DECIMO TERCERO" + "," + "DECIMO CUARTO" + "," + "PARTICIPACION DE UTILIDADES" + "," + "SALARIOS PERCIBIDOS" + "," + "FONDOS DE RESERVA" + "," + \
                 "COMISIONES" + "," + "BENEFICIOS ADICIONALES EN EFECTIVO" + "," + "ANTICIPO DE UTILIDAD" + "," + "RETENCION JUDICIAL" + "," + "IMPUESTO RETENCION" + "," + \
                 "INFORMACION MDT" + "," + "TIPO DE PAGO SALARIODIGNO" + chr(13) + chr(10)
        return string

    def set_string(self, values):
        return values['column1'] + ',' + values['column2'].decode('utf-8') + ',' + values['column3'].decode('utf-8') + ',' + values['column4'] + ',' + \
               values['column5'] + ',' + values['column6'] + ',' + values['column7'] + ',' + values['column8'] + ',' + values['column9'] + ',' + values['column10'] + ',' + \
               values['column11'] + ',' + values['column12'] + ',' + values['column13'] + ',' + values['column14'] + ',' + values['column15'] + ',' + values['column16'] + ',' + \
               values['column17'] + ',' + values['column18'] + ',' + values['column19'] + ',' + values['column20'] + ',' + values['column21'] + ',' + values['column22'] + ',' + \
               values['column23'] + ',' + values['column24'] + chr(13) + chr(10)

    def return_gender(self, gender):
        letter = ''
        if gender == 'female':
            letter = 'M'
        if gender == 'male':
            letter = 'H'
        return letter

    def return_payment(self, payment):
        letter = ''
        if payment == 'transferencia':
            letter = 'A'
        if payment == 'cheque':
            letter = 'P'
        return letter
