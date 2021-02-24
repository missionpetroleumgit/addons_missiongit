# -*- coding: utf-8 -*-
from openerp.osv import fields, osv
import base64
import StringIO
from lxml import etree
from time import strftime
import os
from lxml.doctestcompare import strip


class rdep(osv.osv_memory):
    _name = 'rdep'
    _description = 'RDEP'

    _columns = {
        'fiscalyear_id': fields.many2one('hr.fiscalyear', 'Anno Fiscal', required=True),
        'company_id': fields.many2one('res.company', 'Empresa', required=True),
        'file': fields.binary('Archivo XML')
    }

    def generate_file(self, cr, uid, ids, context=None):
        form = self.read(cr, uid, ids)[0]
        obj_company = self.pool.get('res.company').browse(cr, uid, form.get('company_id')[0], context=None)
        obj_partner_related = obj_company.partner_id
        ruc_empresa = obj_partner_related.part_number
        obj_fiscalyear = self.pool.get('hr.fiscalyear').browse(cr, uid, form.get('fiscalyear_id')[0], context=None)
        # name_fiscal = obj_fiscalyear.name
        date_start = obj_fiscalyear.date_start
        date_stop = obj_fiscalyear.date_stop
        employee_ids = self.pool.get('hr.employee').search(cr, uid, [('state_emp', '=', 'active'),
                                                                     ('contract_id.date_start', '<', obj_fiscalyear.date_stop),
                                                                     ('id', '!=', 1)])
        if employee_ids:
            rdep = etree.Element('rdep')
            etree.SubElement(rdep, 'numRuc').text = ruc_empresa
            etree.SubElement(rdep, 'anio').text = obj_fiscalyear.name
            retRelDep = etree.Element('retRelDep')
            for employee in self.pool.get('hr.employee').browse(cr, uid, employee_ids, context=None):
                datRetRelDep = etree.Element('datRetRelDep')
                empleado = etree.Element('empleado')
                retRelDep.append(datRetRelDep)
                datRetRelDep.append(empleado)
                etree.SubElement(empleado, 'benGalpg').text = 'NO'
                etree.SubElement(empleado, 'enfcatastro').text = 'NO'
                if employee.emp_tipo_doc == 'c':
                    etree.SubElement(empleado, 'tipIdRet').text = 'C'
                else:
                    etree.SubElement(empleado, 'tipIdRet').text = 'P'
                etree.SubElement(empleado, 'idRet').text = employee.identification_id
                etree.SubElement(empleado, 'apellidoTrab').text = employee.emp_apellidos
                etree.SubElement(empleado, 'nombreTrab').text = employee.emp_nombres
                etree.SubElement(empleado, 'estab').text = '001'
                etree.SubElement(empleado, 'residenciaTrab').text = "01"
                etree.SubElement(empleado, 'paisResidencia').text = '593'
                etree.SubElement(empleado, 'aplicaConvenio').text = 'NA'
                etree.SubElement(empleado, 'tipoTrabajDiscap').text = '01'
                etree.SubElement(empleado, 'porcentajeDiscap').text = '0'
                etree.SubElement(empleado, 'tipIdDiscap').text = 'N'
                etree.SubElement(empleado, 'idDiscap').text = '999'
                rdep.append(retRelDep)
                suelsal = self.calculate_base_wage(cr, uid, employee.id, date_start, date_stop, context=None)
                apoPerIess = self.calculate_apoPerIess(cr, uid, employee.id, date_start, date_stop, context=None)
                etree.SubElement(datRetRelDep, 'suelSal').text = str(suelsal)
                etree.SubElement(datRetRelDep, 'sobSuelComRemu').text = str(self.calculate_sobSuelComRemu(cr, uid, employee.id, date_start, date_stop, context=None))
                etree.SubElement(datRetRelDep, 'partUtil').text = str(self.calculate_partUtil(cr, uid, employee.id, date_start, date_stop, context=None))
                etree.SubElement(datRetRelDep, 'intGrabGen').text = str(self.calculate_intGrabGen(cr, uid, employee.id, date_start, date_stop, context=None))
                etree.SubElement(datRetRelDep, 'impRentEmpl').text = str(self.calculate_impRent(cr, uid, employee.id, date_start, date_stop, context=None))
                etree.SubElement(datRetRelDep, 'decimTer').text = str(self.calculate_decimTer(cr, uid, employee.id, date_start, date_stop, context=None))
                etree.SubElement(datRetRelDep, 'decimCuar').text = str(self.calculate_decimCuar(cr, uid, employee.id, date_start, date_stop, context=None))
                etree.SubElement(datRetRelDep, 'fondoReserva').text = str(self.calculate_fondoReserva(cr, uid, employee.id, date_start, date_stop, context=None))
                etree.SubElement(datRetRelDep, 'salarioDigno').text = '0.00'
                etree.SubElement(datRetRelDep, 'otrosIngRenGrav').text = '0.00'
                etree.SubElement(datRetRelDep, 'ingGravConEsteEmpl').text = str(self.calculate_base_wage(cr, uid, employee.id, date_start, date_stop, context=None))
                etree.SubElement(datRetRelDep, 'sisSalNet').text = '1'
                etree.SubElement(datRetRelDep, 'apoPerIess').text = str(apoPerIess)
                etree.SubElement(datRetRelDep, 'aporPerIessConOtrosEmpls').text = '0.00'
                etree.SubElement(datRetRelDep, 'deducVivienda').text = str(self.waste_deduction(cr, uid, employee.id, str('Vivienda'), obj_fiscalyear.id, context=None))
                etree.SubElement(datRetRelDep, 'deducSalud').text = str(self.waste_deduction(cr, uid, employee.id, str('Salud'), obj_fiscalyear.id, context=None))
                etree.SubElement(datRetRelDep, 'deducEduca').text = str(self.waste_deduction(cr, uid, employee.id, str('Educacion'), obj_fiscalyear.id, context=None))

                etree.SubElement(datRetRelDep, 'deducEducartcult').text = '0.00'
                etree.SubElement(datRetRelDep, 'deducAliement').text = str(self.waste_deduction(cr, uid, employee.id, str('Alimentacion'), obj_fiscalyear.id, context=None))
                etree.SubElement(datRetRelDep, 'deducVestim').text = str(self.waste_deduction(cr, uid, employee.id, str('Vestimenta'), obj_fiscalyear.id, context=None))
                etree.SubElement(datRetRelDep, 'exoDiscap').text = '0.00'
                etree.SubElement(datRetRelDep, 'exoTerEd').text = '0.00'
                etree.SubElement(datRetRelDep, 'basImp').text = str(suelsal - apoPerIess)
                etree.SubElement(datRetRelDep, 'impRentCaus').text = str(self.calculate_impRent(cr, uid, employee.id, date_start, date_stop, context=None))
                etree.SubElement(datRetRelDep, 'valRetAsuOtrosEmpls').text = '0.00'
                etree.SubElement(datRetRelDep, 'valImpAsuEsteEmpl').text = '0.00'
                etree.SubElement(datRetRelDep, 'valRet').text = '0.00'
            xml_file = etree.tostring(rdep, pretty_print=True, encoding='iso-8859-1')
            buf = StringIO.StringIO()
            buf.write(xml_file)
            out = base64.encodestring(buf.getvalue())
            buf.close()
            name = "%s%s.XML" % ("RDEP", strftime("%Y"))
            return self.write(cr, uid, ids, {'file': out})
        pass

    def calculate_base_wage(self, cr, uid, employee_id, date_start, date_stop, context=None):
        base = 0.00
        slip_pool = self.pool.get('hr.payslip.line')
        slip_ids = slip_pool.search(cr, uid, [('employee_id', '=', employee_id),
                                              ('slip_id.date_from', '>=', date_start),
                                              ('slip_id.date_to', '<=', date_stop),
                                              ('code', 'in', ('BASICO', 'IPE', 'INGHEXT', 'INGCOM', 'INGHSUP', 'INGBN', 'BANP'))])
        for line in slip_pool.browse(cr, uid, slip_ids, context=None):
            base += line.total
        return base

    def calculate_sobSuelComRemu(self, cr, uid, employee_id, date_start, date_stop, context=None):
        sobSuelComRemu = 0.00
        income_pool = self.pool.get('hr.income')
        income_ids = income_pool.search(cr, uid, [('employee_id', '=', employee_id),
                                                  ('date', '>=', date_start),
                                                  ('date', '<=', date_stop),
                                                  ('adm_id.name', '=', 'INGSOB')])
        for income in income_pool.browse(cr, uid, income_ids, context=None):
            sobSuelComRemu += income.value
        return sobSuelComRemu

    def calculate_partUtil(self, cr, uid, employee_id, date_start, date_stop, context=None):
        partUtil = 0.00
        income_pool = self.pool.get('hr.income')
        income_ids = income_pool.search(cr, uid, [('employee_id', '=', employee_id),
                                                  ('date', '>=', date_start),
                                                  ('date', '<=', date_stop),
                                                  ('adm_id.name', '=', 'INGUTL')])
        for income in income_pool.browse(cr, uid, income_ids, context=None):
            partUtil += income.value
        return partUtil

    # Reimplementar este metodo cuando se determine la manera de calcular su valor
    def calculate_intGrabGen(self, cr, uid, employee_id, date_start, date_stop, context=None):
        intGrabGen = 0.00
        return intGrabGen

    def calculate_impRent(self, cr, uid, employee_id, date_start, date_stop, context=None):
        tax = 0.00
        slip_pool = self.pool.get('hr.payslip.line')
        slip_ids = slip_pool.search(cr, uid, [('employee_id', '=', employee_id),
                                              ('slip_id.date_from', '>=', date_start),
                                              ('slip_id.date_to', '<=', date_stop),
                                              ('code', '=', 'EGRIR')])
        for line in slip_pool.browse(cr, uid, slip_ids, context=None):
            tax += line.total
        return tax

    def calculate_decimTer(self, cr, uid, employee_id, date_start, date_stop, context=None):
        decimo3 = 0.00
        slip_pool = self.pool.get('hr.payslip.line')
        slip_ids = slip_pool.search(cr, uid, [('employee_id', '=', employee_id),
                                              ('slip_id.date_from', '>=', date_start),
                                              ('slip_id.date_to', '<=', date_stop),
                                              ('code', '=', 'D3')])
        for line in slip_pool.browse(cr, uid, slip_ids, context=None):
            decimo3 += line.total
        return decimo3

    def calculate_decimCuar(self, cr, uid, employee_id, date_start, date_stop, context=None):
        decimo4 = 0.00
        slip_pool = self.pool.get('hr.payslip.line')
        slip_ids = slip_pool.search(cr, uid, [('employee_id', '=', employee_id),
                                              ('slip_id.date_from', '>=', date_start),
                                              ('slip_id.date_to', '<=', date_stop),
                                              ('code', '=', 'D4')])
        for line in slip_pool.browse(cr, uid, slip_ids, context=None):
            decimo4 += line.total
        return decimo4

    def calculate_fondoReserva(self, cr, uid, employee_id, date_start, date_stop, context=None):
        fondo = 0.00
        slip_pool = self.pool.get('hr.payslip.line')
        slip_ids = slip_pool.search(cr, uid, [('employee_id', '=', employee_id),
                                              ('slip_id.date_from', '>=', date_start),
                                              ('slip_id.date_to', '<=', date_stop),
                                              ('code', '=', 'FDRP')])
        for line in slip_pool.browse(cr, uid, slip_ids, context=None):
            fondo += line.total
        return fondo

    def calculate_apoPerIess(self, cr, uid, employee_id, date_start, date_stop, context=None):
        iess = 0.00
        slip_pool = self.pool.get('hr.payslip.line')
        slip_ids = slip_pool.search(cr, uid, [('employee_id', '=', employee_id),
                                              ('slip_id.date_from', '>=', date_start),
                                              ('slip_id.date_to', '<=', date_stop),
                                              ('code', '=', 'APIES')])
        for line in slip_pool.browse(cr, uid, slip_ids, context=None):
            val = line.total
            if val < 0:
                val = -(val)
            iess += val
        return iess

    def waste_deduction(self, cr, uid, employee_id, name, fiscalyear_id, context=None):
        waste = 0.00
        employee_pool = self.pool.get('hr.employee')
        fiscalyear_pool = self.pool.get('hr.fiscalyear')
        fiscal_year_id = fiscalyear_pool.search(cr, uid, [('id', '=', fiscalyear_id)])
        fiscalyear_id = fiscalyear_pool.browse(cr, uid, fiscal_year_id, context=None)
        obj_employee = employee_pool.browse(cr, uid, employee_id, context=None)
        for expense in obj_employee.personal_expense_ids:
            expense_name = str(expense.personal_expense_catalog_id.name)
            if expense_name == name and expense.fiscalyear_id.code == fiscalyear_id.code:
                waste = expense.total_annual_cost
                break
        return waste

rdep()
