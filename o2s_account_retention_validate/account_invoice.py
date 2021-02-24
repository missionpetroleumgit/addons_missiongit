# -*- coding: utf-8 -*-
###############################
# ##########################  #
###############################

from openerp import models, fields, api
from openerp.exceptions import except_orm, Warning


class account_invoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def invoice_validate(self):
        res = super(account_invoice, self).invoice_validate()
        for rec in self:
            for line in rec.invoice_line:
                if self.check_retention(line):
                    if not rec.deduction_id:
                        raise except_orm('Error!', 'Usted tiene configurado el impuesto auxiliar pero selecciono "No genera retencion"')
                    rec.deduction_id.state = 'draft'
                    break
        return res

    def check_retention(self, line):
        for tax in line.invoice_line_tax_id:
            if tax.is_auxiliar_ret:
                return True
        return False

    # Onchange para poner la fecha de emision y el periodo en FP
    @api.onchange('date_cont')
    def onchange_date(self):
        if self.date_cont:
            moth = self.date_cont[5:7]
            year = self.date_cont[0:4]
            code = moth + '/' + year
            account_period = self.env['account.period']
            period_id = account_period.search([('code', '=', code)])
            self.period_id = period_id
            self.date_emision = self.date_cont


account_invoice()