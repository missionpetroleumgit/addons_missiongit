# -*- coding: utf-8 -*-
###############################
# ##########################  #
###############################

from openerp import models, fields, api
from openerp.exceptions import except_orm, Warning


class account_deduction(models.Model):
    _inherit = 'account.deduction'

    move_id = fields.Many2one('account.move', 'Asiento contable', readonly=True,
                              help='Este campo solo tendra valor cuando la retencion se valide manualmente')

    @api.multi
    def wkf_open(self):
        res = super(account_deduction, self).wkf_open()
        for record in self:
            if not record.move_id:
                self.create_retention_move(record)
        return res

    def create_retention_move(self, deduction):
        if not deduction.tax_ids:
            return False
        debit = 0.00
        move = self.env['account.move']
        line = self.env['account.move.line']
        # CSV:23-04-2018: AUMENTO PARA CORREGIR PERIODO Y FECHA DE ASIENTO CREADO
        period = self.env['account.period']
        period_id = period.search([('date_start', '<=', deduction.emission_date),('date_stop', '>=', deduction.emission_date)])
        if not period_id:
            raise except_orm('Advertencia!', 'No existe un periodo definido en la fecha de la retencion')
        journal = self.env['account.journal'].search([('code', '=', 'DIRF')])
        if not journal:
            raise except_orm('Error!', 'No existe un diario de retenciones definido con el codigo "DIRF"')
        move_obj = move.create({'journal_id': journal.id, 'ref': deduction.number, 'period_id': period_id.id, 'date': deduction.emission_date})
        for tax_line in deduction.tax_ids:
            line.create({'move_id': move_obj.id, 'debit': tax_line.amount, 'credit': 0.00, 'account_id': tax_line.account_id.id, 'tax_code_id': tax_line.tax_code_id.id,
                         'invoice': deduction.invoice_id.id, 'name': tax_line.name, 'partner_id': deduction.partner_id.id, 'tax_amount': tax_line.amount, 'period_id': period_id.id, 'date': deduction.emission_date})
            debit += tax_line.amount
        line.create({'move_id': move_obj.id, 'debit': 0.00, 'credit': debit, 'account_id': deduction.invoice_id.account_id.id,
                     'invoice': deduction.invoice_id.id, 'partner_id': deduction.partner_id.id, 'tax_amount': tax_line.amount, 'period_id': period_id.id, 'date': deduction.emission_date})

        self.move_id = move_obj.id

        return True
