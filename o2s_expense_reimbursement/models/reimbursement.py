# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution - Ecuador
#    Copyright (C) 2014 BitConsultores (<http://http://bitconsultores-ec.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp import models, fields, api, _
import time
import openerp.addons.decimal_precision as dp

TYPES = [('ced', 'Cedula'),
         ('ruc', 'RUC'),
         ('passport', 'Pasaporte')
         ]


class account_invoice(models.Model):
    _inherit = 'account.invoice'

    @api.one
    def _totalExpenses(self):
        expense_total = 0.00
        for exp_line in self.reimbursement_ids:
                expense_total += exp_line.refund_total_amount
        self.total_reimbursement = expense_total

    @api.one
    def _totalWithOutTaxes(self):
        total = 0.00
        for exp_line in self.reimbursement_ids:
                total += exp_line.total_without_taxes
        self.total_without_taxes = total

    reimbursement_ids = fields.One2many('reimbursement.account', 'account_reimbursement_id', 'Reembolso de Gasto')
    total_reimbursement = fields.Float('Total Gastos', compute= _totalExpenses)
    total_without_taxes = fields.Float('Total sin IVA', compute= _totalWithOutTaxes)
    is_exp_reimb = fields.Boolean('Es Reembolso de Gasto')

account_invoice()


class reimbursement_account(models.Model):
    _name = 'reimbursement.account'

    @api.one
    def _total_amount(self):
        iva_amount = 0.00
        tax_amount = 0.00
        null_amount = 0.00
        if self.refund_base_iva > null_amount:
                tax_amount += (self.refund_base_iva * 12)/100
        for r_calc in self:
            iva_amount = r_calc.refund_base_iva
            self.active_refund_iva = tax_amount
            if iva_amount != r_calc.refund_base_iva:
                r_calc.refund_total_amount = 0.00
            r_calc.refund_total_amount += r_calc.ice_amount
            r_calc.refund_total_amount += r_calc.refund_iva
            r_calc.refund_total_amount += r_calc.refund_base_iva
            r_calc.refund_total_amount += r_calc.refund_base_iva_cero
            r_calc.refund_total_amount += r_calc.active_refund_iva
            r_calc.refund_total_amount += r_calc.taxable_iva_exempt
        self.refund_total_amount = round(r_calc.refund_total_amount, 2)

    @api.one
    def _total_without_Taxes(self):
        iva_amount = 0.00
        tax_amount = 0.00
        null_amount = 0.00
        if self.refund_base_iva > null_amount:
                tax_amount += (self.refund_base_iva * 12)/100
        for r_calc in self:
            iva_amount = r_calc.refund_base_iva
            self.active_refund_iva = tax_amount
            if iva_amount != r_calc.refund_base_iva:
                r_calc.refund_total_amount = 0.00
            r_calc.total_without_taxes += r_calc.ice_amount
            r_calc.total_without_taxes += r_calc.refund_iva
            r_calc.total_without_taxes += r_calc.refund_base_iva
            r_calc.total_without_taxes += r_calc.refund_base_iva_cero
            r_calc.total_without_taxes += r_calc.taxable_iva_exempt
        self.total_without_taxes = round(r_calc.total_without_taxes, 2)

    @api.one
    def _tax_amount(self):
        tax_amount = 0.00
        null_amount = 0.00
        if self.refund_base_iva > null_amount:
            tax_amount += (self.refund_base_iva * 12)/100
            self.active_refund_iva = tax_amount

    refund_type = fields.Char('Tipo Comprobante Reembolso')
    ident_refund = fields.Char('Cedula', size=10)
    ruc_ident_refund = fields.Char('RUC', size=13)
    pasport_ident_refund = fields.Char('Pasaporte', size=40)
    refund_series = fields.Char('Emision')
    date_refund = fields.Date('Fecha Reembolso')
    identification_type = fields.Selection(TYPES, 'Tipo ID')
    est_refund = fields.Char('Estab.')
    refund_number = fields.Char('Numero de Factura', size=20)
    refund_authorization = fields.Char('Numero de Autorizacion', size=60)
    account_reimbursement_id = fields.Many2one('account.invoice', 'Reembolso de Gastos')
    journal_id = fields.Many2one('account.journal', 'Diario')
    document_type = fields.Many2one('account.invoice.document', 'Tipo de Documento')
    date_invoice = fields.Date('Fecha de Factura')

    ice_amount = fields.Float('Monto ICE', digits=dp.get_precision('Account'))
    refund_base_iva = fields.Float('BASE 12%', digits=dp.get_precision('Account'))
    refund_iva = fields.Float('Base No Grava Iva', digits=dp.get_precision('Account'))
    refund_base_iva_cero = fields.Float('BASE IVA 0%', digits=dp.get_precision('Account'))
    active_refund_iva = fields.Float('IVA 12%', digits=dp.get_precision('Account'), compute=_tax_amount)
    taxable_iva_exempt = fields.Float('Base imponible exenta de IVA', digits=dp.get_precision('Account'))
    refund_total_amount = fields.Float('TOTAL', digits=dp.get_precision('Account'), compute=_total_amount)
    total_without_taxes = fields.Float('Total sin IVA', digits=dp.get_precision('Account'), compute=_total_without_Taxes)

    _defaults = {
        'date_refund': lambda *a: time.strftime('%Y-%m-%d %H:%M:%S'),
        'journal_id': 2,
    }

    @api.onchange('refund_number')
    def onchange_reference_inv(self):
        if self.refund_number:
            if self.refund_number.count('-') == 2:
                number_sep = self.refund_number.split('-')
                self.est_refund = number_sep[0]
                self.refund_series = number_sep[1]


reimbursement_account()


