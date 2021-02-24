from openerp.osv import fields, osv


class reintegration_employee(osv.osv_memory):
    _name = 'reintegration.employee'
    _columns = {
        'employee_id': fields.many2one('hr.employee', 'Empleado', required=True, domain=[('state_emp', '=', 'sold_out')]),
        'date': fields.date('Fecha de reingreso', required=True)
    }

    def button_ok(self, cr, uid, ids, context=None):
        reintegrations = self.browse(cr, uid, ids)
        contract_pool = self.pool.get('hr.contract')
        hr_employee_pool = self.pool.get('hr.employee')
        change_control_pool = self.pool.get('change.control')
        user = self.pool.get('res.users').browse(cr, uid, uid)
        for reintegration in reintegrations:
            contract_ids = contract_pool.search(cr, uid, [('employee_id', '=', reintegration.employee_id.id), ('state', '=', 'close')])
            if not contract_ids:
                raise osv.except_osv('Error!!', 'El empleado seleccionado no tiene contrato liquidado')
            contract_pool.write(cr, uid, contract_ids, {'state': 'open', 'date_start': reintegration.date, 'date_end': False})
            hr_employee_pool.write(cr, uid, reintegration.employee_id.id, {'state_emp': 'active', 'pagar_rol_l': False})
            contract = contract_pool.browse(cr, uid, contract_ids[0])
            vals = {
                'contract_id': contract.id,
                'change': 'reint',
                'old_value': '-',
                'current_value': contract.wage,
                'user': user.login,
                'change_date': reintegration.date
            }
            change_control_pool.create(cr, uid, vals)

        return {'type': 'ir.actions.act_window_close'}
