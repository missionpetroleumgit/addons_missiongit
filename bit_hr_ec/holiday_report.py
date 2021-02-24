#-*- coding:utf-8 -*-

##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    d$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
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
from openerp.report import report_sxw
import code

from datetime import datetime, date, time, timedelta
import calendar

class report_print_holidays(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(report_print_holidays, self).__init__(cr, uid, name, context)
        self.number_lines = 0
        self.number_add = 0
        self.localcontext.update({
            'get_datos': self.get_datos,
        })
        
    def get_amount_in_letters(self, amount):
        in_letters = self.pool.get('account.check').get_number_in_letters(amount)
        return in_letters
     
    def get_datos(self, employee_id):
        print "employee_id:  ", employee_id
        datos_exp = self.pool.get('hr.employee').search(self.cr, self.uid, [('id','=',employee_id)])
        print "datos_exp:  ", datos_exp
        #if datos_exp:
        object_exp = self.pool.get('hr.employee').browse(self.cr, self.uid, datos_exp)
#             for experience in object_exp:
#                 print "Experience:  ", experience
#                 
#                 identif = experience.identification_id
#                 empleado = experience.employee_id.name
#                 categoria = experience.job_id
#                 dias_vacacion = experience.availables_days
#                 region = experience.region
#          
#                 val1 = {'empleado': empleado,
#                      'categoria': categoria,
#                      'identif': identif,
#                      'region': region,
#                      'dias_vacacion': dias_vacacion
#                      }
#                 res.append(val1)
#             print "OBJETO", res      
#         else:
#             val1 = {'empleado': '',
#                      'categoria': '',
#                      'identif':'',
#                      'dias_vacacion': ''
#                      }
#             res.append(val1)
#         print "OBJETO", res 
#             
        return object_exp.employee_id or False 

        
    
    
class holiday_report_view(osv.AbstractModel):
    _name = 'report.bit_account_report.holiday_report_view'
    _inherit = 'report.abstract_report'
    _template = 'bit_account_report.holiday_report_view'
    _wrapped_report_class = report_print_holidays
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
