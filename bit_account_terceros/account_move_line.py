import time
from datetime import datetime

from openerp import workflow
from openerp.osv import fields, osv
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
from openerp import tools
from openerp.report import report_sxw
import openerp


class account_move_line(osv.osv):
    _inherit = "account.move.line"

    def create(self, cr, uid, vals, context=None, check=True):
        if 'third_partner_id' in vals and 'reemb_product' in vals:
            if vals['reemb_product']:
                if not vals['third_partner_id']:
                    raise osv.except_osv('Error!!', 'Debe seleccionar el cliente tercero en la factura')
                vals['partner_id'] = vals['third_partner_id']
        return super(account_move_line, self).create(cr, uid, vals, context, check)