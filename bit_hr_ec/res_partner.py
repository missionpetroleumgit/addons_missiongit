__author__ = 'guillermo'

from openerp.osv import fields, osv

class res_partner(osv.osv):
    _inherit = 'res.partner'

    _columns = {
        'is_employee': fields.boolean('Es empleado'),
        'employee_id': fields.many2one('hr.employee', 'Empleado', ondelete='cascade', select=True),
        'tradename': fields.char('Nombre Comercial', size=64),
      }

    _sql_constraints = [
        ('employee_partner_uniq', 'unique(employee_id)', 'The employee is unique per partner!'),
    ]

res_partner()
