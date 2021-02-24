# -*- coding: utf-8 -*-
###############################
# ##########################  #
###############################

from openerp import models, fields, api
from openerp.exceptions import except_orm, Warning


class account_tax(models.Model):
    _inherit = 'account.tax'

    is_auxiliar_ret = fields.Boolean('retencion auxiliar?')

account_tax()


class account_invoice_tax(models.Model):
    _inherit = "account.invoice.tax"

    tax_id = fields.Many2one('account.tax', 'Impuesto')

    @api.onchange('tax_id')
    def onchange_tax_id(self):
        self.name = self.tax_id.name if self.tax_id.name else False
        self.account_id = self.tax_id.account_collected_id.id if self.tax_id.account_collected_id else False
        self.base_code_id = self.tax_id.base_code_id.id if self.tax_id.base_code_id else False
        self.tax_code_id = self.tax_id.tax_code_id.id if self.tax_id.tax_code_id else False
    #AUMENTO CALCULAR AUTOMATICA LA RETENCION
    @api.onchange('base')
    def onchange_base(self):
        print "Impuesto", self.tax_id
        print "Entro porc ret", self.tax_id.amount
        print "Entro base", self.base
        if self.tax_id and self.base:
            self.amount = round(abs(self.tax_id.amount)*self.base, 2)
        else:
            self.amount = 0.00