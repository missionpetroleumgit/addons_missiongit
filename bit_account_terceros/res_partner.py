from openerp.osv import fields, osv


class res_partner(osv.osv):
    _inherit = 'res.partner'

    _columns = {
        'is_third_partner': fields.boolean('Es Tercero'),
      }
