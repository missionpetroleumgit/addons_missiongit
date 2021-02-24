# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
from openerp.tools import float_compare, float_is_zero
from openerp import api, models, fields, _
from openerp.exceptions import except_orm


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def invoice_validate(self):
        res = super(AccountInvoice, self).invoice_validate()
        for record in self:
            if record.period_id.state == 'done':
                raise except_orm('Error !', 'No puede crear ni modificar un registro contable cuando se ya se cerró el periodo, '
                                  'usted debe comunicarse con finanzas para abrir el periodo y validar este registro')
        return res

    @api.multi
    def action_cancel(self):
        res = super(AccountInvoice, self).action_cancel()
        for inv in self:
            if inv.period_id.state == 'done':
                raise except_orm('Error !', 'No puede crear ni modificar un registro contable cuando se ya se cerró el periodo, '
                                  'usted debe comunicarse con finanzas para abrir el periodo y validar este registro')
        return res


class AccountDeduction(models.Model):
    _inherit = 'account.deduction'

    @api.multi
    def wkf_cancel(self):
        res = super(AccountDeduction, self).wkf_cancel()
        for record in self:
            if record.invoice_id.period_id.state == 'done' and record.move_id:
                raise except_orm('Error !', 'No puede crear ni modificar un registro contable cuando se ya se cerró el periodo, '
                                            'usted debe comunicarse con finanzas para abrir el periodo y validar este registro')
        return res

    @api.multi
    def wkf_open(self):
        res = super(AccountDeduction, self).wkf_open()
        for record in self.tax_ids:
            if self.invoice_id.period_id.state == 'done':
                raise except_orm('Error !',
                                 'No puede crear ni modificar un registro contable cuando se ya se cerró el periodo, '
                                 'usted debe comunicarse con finanzas para abrir el periodo y validar este registro')
        return res


class AccountVoucher(models.Model):
    _inherit = 'account.voucher'

    @api.multi
    def cancel_voucher(self):
        res = super(AccountVoucher, self).cancel_voucher()
        for record in self.line_dr_ids:
            if record.voucher_id.period_id.state == 'done':
                raise except_orm('Error !',
                                 'No puede crear ni modificar un registro contable cuando se ya se cerró el periodo, '
                                 'usted debe comunicarse con finanzas para abrir el periodo y validar este registro')

        for record in self.line_cr_ids:
            if record.voucher_id.period_id.state == 'done':
                raise except_orm('Error !',
                                 'No puede crear ni modificar un registro contable cuando se ya se cerró el periodo, '
                                 'usted debe comunicarse con finanzas para abrir el periodo y validar este registro')

        return res

    @api.multi
    def proforma_voucher(self):
        res = super(AccountVoucher,self).proforma_voucher()
        for record in self.line_dr_ids:
            if record.voucher_id.period_id.state == 'done':
                raise except_orm('Error !',
                                 'No puede crear ni modificar un registro contable cuando se ya se cerró el periodo, '
                                 'usted debe comunicarse con finanzas para abrir el periodo y validar este registro')

        for record in self.line_cr_ids:
            if record.voucher_id.period_id.state == 'done':
                raise except_orm('Error !',
                                 'No puede crear ni modificar un registro contable cuando se ya se cerró el periodo, '
                                 'usted debe comunicarse con finanzas para abrir el periodo y validar este registro')

        return res

    @api.multi
    def validate_advance(self):
        res = super(AccountVoucher, self).validate_advance()
        for record in self:
            if record.period_id.state == 'done':
                raise except_orm('Error !',
                                 'No puede crear ni modificar un registro contable cuando se ya se cerró el periodo, '
                                 'usted debe comunicarse con finanzas para abrir el periodo y validar este registro')

        return res

    @api.multi
    def cancel_advance(self):
        res = super(AccountVoucher, self).cancel_advance()
        for record in self:
            if record.period_id.state == 'done' and record.move_ids:
                raise except_orm('Error !',
                                 'No puede crear ni modificar un registro contable cuando se ya se cerró el periodo, '
                                 'usted debe comunicarse con finanzas para abrir el periodo y validar este registro')


    @api.multi
    def validate_advance_some(self):
        res = super(AccountVoucher, self).validate_advance_some()
        for record in self:
            if record.period_id.state == 'done':
                raise except_orm('Error !',
                                 'No puede crear ni modificar un registro contable cuando se ya se cerró el periodo, '
                                 'usted debe comunicarse con finanzas para abrir el periodo y validar este registro')
        return res


class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.multi
    def button_cancel(self):
        res = super(AccountMove, self).button_cancel()
        for record in self:
            if record.period_id.state == 'done':
                raise except_orm('Error !',
                                 'No puede crear ni modificar un registro contable cuando se ya se cerró el periodo, '
                                 'usted debe comunicarse con finanzas para abrir el periodo y validar este registro')
        return res

    @api.multi
    def button_validate(self):
        res = super(AccountMove, self).button_validate()
        for record in self:
            if record.period_id.state == 'done':
                raise except_orm('Error !',
                                 'No puede crear ni modificar un registro contable cuando se ya se cerró el periodo, '
                                 'usted debe comunicarse con finanzas para abrir el periodo y validar este registro')
        return res

