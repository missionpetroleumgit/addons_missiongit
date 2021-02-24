from openerp.osv import fields, osv


class hr_employee(osv.osv):
    _inherit = 'hr.employee'
    _description = 'Employee'
    _columns = {
        'expenses_ids': fields.one2many('hr.expense', 'employee_id', 'Egresos')
    }
