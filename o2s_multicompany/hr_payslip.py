# -*- coding: utf-8 -*-
from openerp import models, fields, api
from openerp.exceptions import except_orm, Warning


class hr_payslip(models.Model):
    _inherit = 'hr.payslip'
    
    @api.model
    def create(self, vals):
        if 'payslip_run_id' in vals:
            slip_run = self.env['hr.payslip.run'].browse(vals['payslip_run_id'])
            vals['company_id'] = slip_run.company_id.id
        return super(hr_payslip, self).create(vals)
