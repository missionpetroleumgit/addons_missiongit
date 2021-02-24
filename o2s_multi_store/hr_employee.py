# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in module root
# directory
##############################################################################
from openerp import models, fields


class hr_employee(models.Model):
    _inherit = 'hr.employee'

    store_id = fields.Many2one('res.store', 'Sucursal')

