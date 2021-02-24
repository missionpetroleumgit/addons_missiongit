# -*- coding: utf-8 -*-
from openerp.osv import fields, osv
import openerp.addons.decimal_precision as dp


class account_voucher(osv.osv):
    _inherit = 'account.voucher'

    def _compute_amount(self, cr, uid, ids, name, args, context=None):
        total = 0.00
        res = dict()
        for obj in self.browse(cr, uid, ids, context=None):
            for line in obj.line_dr_ids:
                total += line.amount

            res[obj.id] = total
        return res

    _columns = {
        'is_advance': fields.boolean('es Anticipo?'),
        'amount_payment': fields.function(_compute_amount, string='Total', type='float', digits_compute=dp.get_precision('Account'), readonly=True),
        'amount': fields.float('Total', digits_compute=dp.get_precision('Account'), readonly=True, states={'draft': [('readonly',False)]}),
#        'pos_config': fields.many2one('pos.config', 'Punto de Venta')

    }

#    _defaults = {
#        'pos_config': lambda s, cr, uid, c: s.pool.get('res.users')._pos_default_get(cr, uid, context=c),
#    }

    def create(self, cr, uid, values, context=None):
        if 'is_advance' in values:
            if not values['is_advance']:
                create_id = super(account_voucher, self).create(cr, uid, values, context)
                obj = self.browse(cr, uid, create_id)
                self.write(cr, uid, create_id, {'amount': obj.amount_payment})
                return create_id
        return super(account_voucher, self).create(cr, uid, values, context)
    
    def write(self, cr, uid, ids, values, context=None):
        if 'line_dr_ids' in values:
            obj = self.browse(cr, uid, ids[0])
            if not obj.is_advance:
                var = super(account_voucher, self).write(cr, uid, ids, values, context)
                return self.write(cr, uid, obj.id, {'amount': obj.amount_payment})
        return super(account_voucher, self).write(cr, uid, ids, values, context)

account_voucher()
