# -*- coding: UTF-8 -*-


from openerp import models, fields, api, _


class res_company(models.Model):
    _inherit = 'res.company'
    is_retail = fields.Boolean('Es Retail?')
    receivable_ids = fields.Many2many('account.account', 'account_rec_company_rel', 'company_id', 'account_id', string='Cuentas por cobrar', domanin=[('type', '=', 'receivable')])
    payable_ids = fields.Many2many('account.account', 'account_pay_company_rel', 'company_id', 'account_id', string='Cuentas por pagar', domanin=[('type', '=', 'payable')])
    payable_ids = fields.Many2many('account.account', 'account_pay_company_rel', 'company_id', 'account_id', string='Cuentas por pagar', domanin=[('type', '=', 'payable')])
    taxiva_account_id = fields.Many2one('account.account', 'Cuenta por Cobrar IVA')
    taxrenta_account_id = fields.Many2one('account.account', 'Cuenta por Cobrar IR')
    advsuppl_account_id = fields.Many2one('account.account', 'Cuenta de Anticipo Proveedor')
    advcustom_account_id = fields.Many2one('account.account', 'Cuenta de Anticipo Cliente')
