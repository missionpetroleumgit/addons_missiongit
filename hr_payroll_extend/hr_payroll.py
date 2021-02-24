# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 Cubic ERP - Teradata SAC (<http://cubicerp.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import osv
from openerp.osv import fields as fields_o
from openerp import models, fields, api
import time

class hr_employee_contribution_rule(models.Model):
    _name = "hr.employee.contribution.rule"
    employee_id = fields.Many2one('hr.employee', string="Employee", required=True)
    rule_id = fields.Many2one('hr.salary.rule', string="Salary Rule", 
                              domain=[('register_employee','=',True)], required=True)
    register_id = fields.Many2one('hr.contribution.register', string="Contribution Register",
                                   domain=[('register_employee','=',True)], required=True)
    
    _sql_constraints = [
            ('employee_rule_unique','UNIQUE(employee_id,rule_id)','The salary rule must be unique per employee!'),
        ]

    @api.model
    def get_register(self, rule_id, employee_id):
        return self.search([('rule_id','=',rule_id),('employee_id','=',employee_id)]).register_id
    
    def get_register_id(self, cr, uid, rule_id, employee_id, context=None):
        ecr_ids = self.pool['hr.employee.contribution.rule'].search(cr, uid, [('rule_id','=',rule_id),
                                                                              ('employee_id','=',employee_id)], 
                                                                    context=context)
        return ecr_ids and self.pool['hr.employee.contribution.rule'].browse(cr, uid, ecr_ids[0], context=context).register_id.id or False
        

class hr_employee(osv.Model):
    _name = 'hr.employee'
    _inherit = 'hr.employee'
    
    _columns = {
            'contribution_rule_ids': fields_o.one2many('hr.employee.contribution.rule', 'employee_id', string="Contribution Rules")
        }
    
class hr_contribution_register(osv.Model):
    _name = 'hr.contribution.register'
    _inherit = 'hr.contribution.register' 
    
    _columns = {
            'register_employee': fields_o.boolean('Contribution Rules in Employee'),
            'code': fields_o.char('Code', 16),
            'employee_rule_ids': fields_o.one2many('hr.employee.contribution.rule', 'register_id', string="Employee Rules")
        }
    _defaults = {
            'register_employee': False,
        }
    
class hr_salary_rule(osv.Model):
    _name = 'hr.salary.rule'
    _inherit = 'hr.salary.rule'
    
    _columns = {
            'register_employee': fields_o.boolean('Contribution Register in Employee'),
        }
    _defaults = {
            'register_employee': False,
        }
    
    def compute_rule(self, cr, uid, rule_id, localdict, context=None):
        register_id = self.pool['hr.employee.contribution.rule'].get_register_id(cr, uid, rule_id,localdict['employee'].id, context=context)
        localdict['register'] = register_id and self.pool['hr.contribution.register'].browse(cr, uid, register_id, context=context) or False
        localdict['contribution'] = localdict['register']
        return super(hr_salary_rule,self).compute_rule(cr, uid, rule_id, localdict, context=context)
     
    def satisfy_condition(self, cr, uid, rule_id, localdict, context=None):
        register_id = self.pool['hr.employee.contribution.rule'].get_register_id(cr, uid, rule_id,localdict['employee'].id, context=context)
        localdict['register'] = register_id and self.pool['hr.contribution.register'].browse(cr, uid, register_id, context=context) or False
        localdict['contribution'] = localdict['register']
        return super(hr_salary_rule,self).satisfy_condition(cr, uid, rule_id, localdict, context=context)
    
class hr_payslip(osv.Model):
    _name = 'hr.payslip'
    _inherit = 'hr.payslip'
    
    def get_payslip_lines(self, cr, uid, contract_ids, payslip_id, context):
        res = super(hr_payslip, self).get_payslip_lines(cr, uid, contract_ids, payslip_id, context=context)
        for r in res:
            rule = self.pool['hr.salary.rule'].browse(cr, uid, r.get('salary_rule_id'), context=context)
            if rule.register_employee:
                payslip = self.pool['hr.payslip'].browse(cr, uid, payslip_id, context=context)
                r['register_id'] = self.pool['hr.employee.contribution.rule'].get_register_id(cr, uid, rule.id,payslip.employee_id.id, context=context)
        return res
        