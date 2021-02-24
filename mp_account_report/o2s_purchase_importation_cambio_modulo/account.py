##########################
# -*- coding: utf-8 -*- ##
##########################


from openerp import models, fields, api


class account_journal(models.Model):
    _inherit = 'account.journal'

    cost_account_id = fields.Many2one('account.account', 'Cuenta de Costo de Importaciones')
    isd_cc_account_id = fields.Many2one('account.account', 'Cuenta x Cobrar ISD')
    isd_cp_account_id = fields.Many2one('account.account', 'Cuenta x Pagar ISD')
