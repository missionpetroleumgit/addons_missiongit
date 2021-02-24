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

from openerp import api, fields, models
from openerp.tools.translate import _
from openerp.exceptions import except_orm, Warning, RedirectWarning
from openerp import SUPERUSER_ID
from time import mktime
from datetime import datetime


class account_dist(models.Model):
    _inherit = 'account.invoice'


    @api.multi
    def invoice_validate(self):
        res = super(account_dist, self).invoice_validate()
        r_id = []
        is_more_one_exp = False
        gettin = False
        for inv in self:

            for inv_line in inv.invoice_line:
                amount_line = inv_line.price_subtotal

            # Desglosar por cuentas analíticas
                if hasattr(inv_line.analytics_id, 'account_ids') and inv_line.analytics_id.account_ids:
                    # gettin = True
                    # my_bool = False

                    if len(inv_line.analytics_id.account_ids) >= 1:
                        for mov_line in inv.move_id.line_id:
                            val = abs(mov_line.debit - mov_line.credit)
                            if self.move_id.state=='posted':
                                self.move_id.button_cancel()

                            if self.type == 'in_refund':
                                if mov_line.product_id.id == inv_line.product_id.id and \
                                        val == amount_line and mov_line.credit > 0 and not mov_line.analytic_account_id:
                                    mov_line.unlink()
                                    break
                            else:
                                if mov_line.product_id.id == inv_line.product_id.id and \
                                        val == amount_line and mov_line.debit > 0 and not mov_line.analytic_account_id:
                                    mov_line.unlink()
                                    break
                        for anal_line in inv_line.analytics_id.account_ids:
                            credit = self.type in ('in_refund','out_invoice') and amount_line * \
                                                    anal_line.rate / 100 or 0
                            debit = self.type in ('out_refund','in_invoice') and amount_line * \
                                                    anal_line.rate / 100 or 0
                            debit = "{0:.3f}".format(debit)
                            account_t = inv_line.account_id.id
                            if anal_line.analytic_account_id and \
                                        anal_line.analytic_account_id.type_account == 'costo':
                                if not inv_line.product_id.property_account_cost_id:
                                    raise except_orm(_('¡¡ Error !!'), _("Debe asociar una cuenta de costo en el producto."))
                                account_t = inv_line.product_id.property_account_cost_id.id
                            values = {
                                    'company_id': self.company_id and self.company_id.id or False,
                                    'partner_id': self.partner_id.id,
                                    'analytic_account_id': anal_line.analytic_account_id.id if anal_line.analytic_account_id else \
                                                         False,
                                    'credit': credit,
                                    'debit': debit,
                                    'centralisation': 'normal',
                                    'journal_id': self.journal_id.id,
                                    'state': 'valid',
                                    'ref': self.internal_number,
                                    'account_id': account_t,
                                    'period_id': self.period_id and self.period_id.id or False,
                                    'move_id': self.move_id and self.move_id.id or False,
                                    'name': inv_line.name,
                                    'tax_amount': 0,
                                    'product_id': inv_line.product_id.id,
                                    'product_uom_id': inv_line.product_id.uom_id.id,
                                    'quantity': inv_line.quantity,
                                   }
                            ml_id = self.env['account.move.line'].create(values)
#                     elif len(inv_line.analytics_id.account_ids) == 1:
#                         for mov_line in inv.move_id.line_id:
#                             val = abs(mov_line.debit - mov_line.credit)
#                             if mov_line.account_id.id == inv_line.account_id.id and \
#                                     mov_line.product_id.id == inv_line.product_id.id and \
#                                     val == (amount_line - inv.third_amount):
# #                                 if inv.type not in ('out_refund', 'in_refund'):
#                                 mov_line.write( { 'analytic_account_id' : inv_line.analytics_id.account_ids[0].analytic_account_id.id } )
                                    
                elif hasattr(inv_line, 'account_analytic_id') and inv_line.account_analytic_id:
                    for inv_line in inv.invoice_line:
                        var = False
                        amount_line = inv_line.price_subtotal
                        for mov_line in inv.move_id.line_id:
                            val = abs(mov_line.debit - mov_line.credit)
                            if mov_line.account_id.id == inv_line.account_id.id and \
                                    mov_line.product_id.id == inv_line.product_id.id and \
                                    val == amount_line and not mov_line.analytic_account_id:
                                # if inv.is_third:
                                #     if inv.third_amount < amount_line and not var:
                                #         new_value = amount_line - inv.third_amount
                                #         if mov_line.debit > 0.00:
                                #             mov_line.write({'debit': new_value})
                                #             var = True
                                mov_line.write( { 'account_analytic_id' : inv_line.account_analytic_id.id })


            suma_round = 0.0000
            for linea in inv.move_id.line_id:
                suma_round += round(linea.debit - linea.credit, 4)
            if suma_round and suma_round < 1:
                for linea in inv.move_id.line_id:
                    if (suma_round > 0) and (linea.credit > 0):
                        to_update = linea.credit + suma_round
                        linea.write({'credit': to_update})
                        break
                    elif (suma_round < 0) and (linea.debit > 0):
                        to_update = linea.debit + -suma_round
                        linea.write({'debit': to_update})
                        break

            print 'suma_round: FINAL****', suma_round
            inv.move_id.post()
        return res
            
account_dist()


TYPES = [('na','No aplica'), ('admin','Gasto Administrativa'),
         ('comer','Gasto Comercial'),('costo','Costo'),('cxc','Por cobrar')]

class account_analytic_account(models.Model):
    _inherit = 'account.analytic.account'
    
    type_account = fields.Selection(TYPES, string="Tipo de cuenta", required=True, \
                                    default='na')
    

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

