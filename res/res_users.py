import os
import re
import openerp
from openerp import SUPERUSER_ID, tools
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp.tools.safe_eval import safe_eval as eval
from openerp.tools import image_resize_image


class user(osv.osv):
    _inherit = 'res.users'

    def _pos_default_get(self, cr, uid, context=None):
        """
        Check if the object for this company have a default value
        """
#        if not context:
#            context = {}
#        user = self.pool.get('res.users').browse(cr, SUPERUSER_ID, uid, context=context)
        return True
