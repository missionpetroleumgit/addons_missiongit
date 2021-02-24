from openerp.osv import osv, fields


class hr_adm_incomes(osv.osv):
    _inherit = 'hr.adm.incomes'

    _columns = {
        'not_generate_benefits': fields.boolean('No genera beneficio social?'),
        'average': fields.boolean('interviene en el promedio'),
    }
hr_adm_incomes()


