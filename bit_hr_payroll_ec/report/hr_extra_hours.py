# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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

from openerp import tools
from openerp.osv import fields, osv
from .. import hr_payroll
from openerp.addons.decimal_precision import decimal_precision as dp


class hr_payroll_analysis(osv.Model):
    _name = "hr.payroll.analysis"
    _description = "Análisis Roles"
    _auto = False
    _rec_name = 'orden'
    _order = 'orden'

    _columns = {
        'date_create': fields.datetime('Fecha', readonly=True),
        'salary_rule_id': fields.many2one('hr.salary.rule', 'Descripcion',readonly=True),
        'department_id': fields.many2one('hr.department','Departamento',readonly=True),
        'amount': fields.float('Valor', digits_compute=dp.get_precision('Payroll'),readonly=True),
        'orden': fields.integer('Orden', readonly=True),
    }
    
    def init(self, cr):
        tools.drop_view_if_exists(cr, 'hr_payroll_analysis')
        cr.execute("""
            create or replace view hr_payroll_analysis as (
                select 
                    min(pl.id) as id, 
                    pl.create_date as date_create,
                    pl.department_id as department_id,
                    pl.salary_rule_id,
                    sum(pl.amount) as amount, 
                    sr.sequence as orden
                from hr_payslip_line pl, hr_salary_rule sr
                where pl.salary_rule_id = sr.id
                and sr.code in ('INGHXT','INGHSUP','INGHNOC')
                group by  pl.create_date, pl.department_id, salary_rule_id, orden
                order by orden
            )
        """)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:


