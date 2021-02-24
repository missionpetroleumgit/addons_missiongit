from openerp.osv import fields, osv


class account_deduction(osv.osv):
    _inherit = 'account.deduction'
    _columns = {
        'pos_config': fields.many2one('pos.config', 'Punto de Venta')
    }

    _defaults = {
        'pos_config': lambda s, cr, uid, c: s.pool.get('res.users')._pos_default_get(cr, uid, context=c),
    }
account_deduction
