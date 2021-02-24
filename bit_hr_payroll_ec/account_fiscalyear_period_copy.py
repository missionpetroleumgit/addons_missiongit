__author__ = 'guillermo'
from openerp.addons.account.account import account_fiscalyear, account_period
from openerp.osv import fields, osv
from openerp.tools.translate import _
from datetime import datetime
from dateutil.relativedelta import relativedelta


class hr_fiscalyear(osv.osv):
    _name = 'hr.fiscalyear'
    _inherit = 'account.fiscalyear'


    _columns = {
        'period_ids': fields.one2many('hr.period.period', 'fiscalyear_id', 'Periodos'),
    }

    def close_fiscalyear(self, cr, uid, ids, context=None):
        period_pool = self.pool.get('hr.period.period')
        period_ids = period_pool.search(cr, uid, [('fiscalyear_id', 'in', ids)])
        period_pool.write(cr, uid, period_ids, {'state':'done'})
        self.write(cr, uid, ids, {'state': 'done'})

    def create_period(self, cr, uid, ids, context=None, interval=1):
        period_obj = self.pool.get('hr.period.period')
        for fy in self.browse(cr, uid, ids, context=context):
            ds = datetime.strptime(fy.date_start, '%Y-%m-%d')
            while ds.strftime('%Y-%m-%d') < fy.date_stop:
                de = ds + relativedelta(months=interval, days=-1)

                if de.strftime('%Y-%m-%d') > fy.date_stop:
                    de = datetime.strptime(fy.date_stop, '%Y-%m-%d')

                period_obj.create(cr, uid, {
                    'name': ds.strftime('%m/%Y'),
                    'code': ds.strftime('%m/%Y'),
                    'date_start': ds.strftime('%Y-%m-%d'),
                    'date_stop': de.strftime('%Y-%m-%d'),
                    'fiscalyear_id': fy.id,
                })
                ds = ds + relativedelta(months=interval)
        return True

    def create(self, cr, uid, values, context=None):
        fy_ids = self.search(cr, uid, [('state', '=', 'draft')])
        if len(fy_ids) == 2:
            raise osv.except_osv('Error', 'No pueden existir dos annos fiscales abiertos')
        return super(hr_fiscalyear, self).create(cr, uid, values)

class hr_period_period(osv.osv):
    _name = 'hr.period.period'
    _inherit = 'account.period'

    _columns = {
        'fiscalyear_id': fields.many2one('hr.fiscalyear', 'Fiscal Year', states={'done':[('readonly',True)]}, select=True),
        # 'hr_fiscalyear_id': fields.many2one('hr.fiscalyear', 'Fiscal Year', required=True, states={'done':[('readonly',True)]}, select=True),
    }
