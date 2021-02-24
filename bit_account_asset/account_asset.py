# -*- coding: utf-8 -*-

from openerp import api, fields, models
from openerp.tools.translate import _
from openerp.exceptions import except_orm, Warning, RedirectWarning

from datetime import datetime, date, time, timedelta
import calendar

TYPES = [('diferido', 'Diferido'),
         ('fijo', 'Fijo'),
         ('intangible', 'Intangible')]  # Diferido / Intangible / Fijo


class account_asset_category(models.Model):
    _inherit = 'account.asset.category'

    account_cost_id = fields.Many2one('account.account', string='Cost Account', required=True, domain=[('type','=','other')])


class account_asset_asset(models.Model):
    _inherit = 'account.asset.asset'

    asset_type = fields.Selection(TYPES, string="Tipo de Activo")
    invoice_id = fields.Many2one('account.invoice', 'Invoice')
    analytics_id = fields.Many2one('account.analytic.plan.instance', 'Analytic Distribution')
    responsible = fields.Many2one('hr.employee', 'Responsable')
    marck = fields.Char('Marca')
    color = fields.Char('Color')
    identification = fields.Char('Placa')
    motor = fields.Char('Motor')
    cilin = fields.Char('Cilindraje')

    case = fields.Char('Chasis')
    model = fields.Char('Modelo')
    serial = fields.Char('Serie')
    delivery_date = fields.Date('Fecha de entrega')
    note = fields.Text('Descripcion')

    @api.one
    def delete_all_depreciation_line(self):
        obj_dep_line = self.env['account.asset.depreciation.line']
        for line in self.depreciation_line_ids:
            if not line.move_check:
                line.unlink()
        return True

    def get_next_date(self, last_date, step, day):
        sum_y = sum_m = 0
        if last_date.month + step > 12:
            sum_y = ( last_date.month + step ) / 12
            sum_m = ( last_date.month + step ) % 12 or last_date.month + 1
        else:
            sum_m = last_date.month + step
        max_day = calendar.monthrange(last_date.year + sum_y, sum_m)[1]
        day = max_day > day and day or max_day
        return datetime(last_date.year + sum_y, sum_m, day)

    @api.multi
    def compute_depreciation_board(self):
        amount_to_devalue = self.purchase_value - self.salvage_value
        purchase_date = datetime.strptime(self.purchase_date, '%Y-%m-%d')
        anho_add = amount = am_increm = 0
        dia = self.prorata and purchase_date.day or 1
        mese_add = not self.prorata and 1 or 0

        self.delete_all_depreciation_line() # Elimino los que existen

        if self.method == 'linear':
            amount = round( float(amount_to_devalue) / self.method_number , 2 ) # Valor
        if self.method == 'degressive':
            amount = round( float(amount_to_devalue) * self.method_progress_factor , 4 ) # Valor

        start_date = self.get_next_date(purchase_date, mese_add, dia)
        cant_dep = self.method_number
        while cant_dep != 0:
            if cant_dep == 1 and self.method == 'linear': # Al último le agrego lo que sobra
                amount += amount_to_devalue - amount * self.method_number

            cant_dep -= 1
            am_increm += amount
            vals = {
                    'name': str(self.method_number - cant_dep),
                    'sequence': self.method_number - cant_dep,
                    'amount': amount,
                    'asset_id': self.id,
                    'remaining_value': amount_to_devalue - am_increm,
                    'depreciated_value': am_increm,
                    'depreciation_date': start_date,
                }

            self.env['account.asset.depreciation.line'].create(vals)
            start_date = self.get_next_date(start_date, self.method_period, dia)
            if self.method == 'degressive':
                if cant_dep == 1:
                    amount = float(amount_to_devalue - am_increm)
                else:
                    amount = round( float(amount_to_devalue - am_increm) * self.method_progress_factor , 4 ) # Valor
        return True

class account_invoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def action_cancel(self):
        rec_asset = self.env['account.asset.asset'].search([('invoice_id', '=', self.id), \
                                                            ('state', '!=', 'draft')])
        if rec_asset:
            raise except_orm(_('¡¡ Error !!'), _("No puede cancelarse una factura de compra " + \
                                                 "de un ACTIVO si este ya ha sido confirmado."))
        res = super(account_invoice, self).action_cancel()
        rec_asset = self.env['account.asset.asset'].search([('invoice_id', '=', self.id)])
        if rec_asset:
            rec_asset.unlink()
        return res


from openerp.osv import fields, osv
class account_invoice_line(osv.osv):
    _inherit = 'account.invoice.line'
    _columns = {
        'asset_category_id': fields.many2one('account.asset.category', 'Asset Category'),
    }

    @api.onchange('asset_category_id')
    def onchange_categ(self):
        if self.asset_category_id:
            self.account_id = self.asset_category_id.account_asset_id.id

    @api.multi
    def write(self, vals):
    #O2SDA: 05032016: Correcion a la api nueva
        for record in self:
            if 'asset_category_id' in vals or record.asset_category_id:
                vals['account_id'] = record.asset_category_id.account_asset_id.id or record.product_id.property_account_expense.id
        return super(account_invoice_line, self).write(vals)

    def asset_create(self, cr, uid, lines, context=None):
        context = context or {}
        asset_obj = self.pool.get('account.asset.asset')
        for line in lines:
            cant = line.quantity
            while cant > 0:
                if line.asset_category_id:
                    vals = {
                        'name': line.name,
                        'code': line.invoice_id.number or False,
                        'category_id': line.asset_category_id.id,
                        'purchase_value': line.price_unit,
                        'period_id': line.invoice_id.period_id.id,
                        'partner_id': line.invoice_id.partner_id.id,
                        'company_id': line.invoice_id.company_id.id,
                        'currency_id': line.invoice_id.currency_id.id,
                        'purchase_date' : line.invoice_id.date_invoice,
#                      Add bit
                        'invoice_id': line.invoice_id.id,
                        'analytics_id': line.analytics_id.id
                    }
                    changed_vals = asset_obj.onchange_category_id(cr, uid, [], vals['category_id'], context=context)
                    vals.update(changed_vals['value'])
                    asset_id = asset_obj.create(cr, uid, vals, context=context)
                    if line.asset_category_id.open_asset:
                        asset_obj.validate(cr, uid, [asset_id], context=context)
                cant -= 1
        return True


class account_asset_depreciation_line(osv.osv):
    _inherit = 'account.asset.depreciation.line'

    def create_move(self, cr, uid, ids, context=None):
        context = dict(context or {})
        can_close = False
        asset_obj = self.pool.get('account.asset.asset')
        period_obj = self.pool.get('account.period')
        move_obj = self.pool.get('account.move')
        move_line_obj = self.pool.get('account.move.line')
        currency_obj = self.pool.get('res.currency')
        created_move_ids = []
        asset_ids = []
        for line in self.browse(cr, uid, ids, context=context):
            depreciation_date = line.depreciation_date
            period_ids = period_obj.find(cr, uid, depreciation_date, context=context)
            depreciation_date = period_obj.browse(cr, uid, period_ids[0]).date_stop
            company_currency = line.asset_id.company_id.currency_id.id
            current_currency = line.asset_id.currency_id.id
            context.update({'date': depreciation_date})
            amount = currency_obj.compute(cr, uid, current_currency, company_currency, line.amount, context=context)
            sign = (line.asset_id.category_id.journal_id.type == 'purchase' and 1) or -1
            asset_name = "Dep. " + line.asset_id.name + ':' + line.depreciation_date
            if line.asset_id.category_id.journal_id.sequence_id:
                asset_name = line.asset_id.category_id.journal_id.sequence_id._next()
            else:
                asset_name = "/"
            reference = line.asset_id.name
            move_vals = {
                'name': asset_name,
                'date': depreciation_date,
                'ref': reference,
                'period_id': period_ids and period_ids[0] or False,
                'journal_id': line.asset_id.category_id.journal_id.id,
                }
            move_id = move_obj.create(cr, uid, move_vals, context=context)
            journal_id = line.asset_id.category_id.journal_id.id
            partner_id = line.asset_id.partner_id.id
            move_line_obj.create(cr, uid, {
                'name': asset_name,
                'ref': reference,
                'move_id': move_id,
                'account_id': line.asset_id.category_id.account_depreciation_id.id,
                'debit': 0.0,
                'credit': amount,
                'period_id': period_ids and period_ids[0] or False,
                'journal_id': journal_id,
                'partner_id': partner_id,
                'currency_id': company_currency != current_currency and  current_currency or False,
                'amount_currency': company_currency != current_currency and - sign * line.amount or 0.0,
                'date': depreciation_date,
            })
#        INICIO
#             aa_asset = hasattr(line.asset_id, 'analytics_id') and \
#                         line.asset_id.analytics_id or False
#             aa_line = hasattr(aa_asset, 'account_ids') and aa_asset.account_ids or False # Comentado aun no esta el modulo account.analytic
            aa_line = False # Comentar cuando se ponga el modulo account.analytic
            if aa_line:
                cant = len(aa_line)
            else:
                cant = 1
            resto = 0
            while cant > 0:
                resto = amount
                amount = cant != 1 and amount * aa_line[cant-1].rate / 100 or amount

                account_t = line.asset_id.category_id.account_expense_depreciation_id.id
                if aa_line:
                    if aa_line[cant-1].analytic_account_id and \
                                aa_line[cant-1].analytic_account_id.type_account == 'costo':
                        if not line.asset_id.category_id.account_cost_id.id:
                            raise except_orm(_('¡¡ Error !!'), _("Debe asociar una cuenta de costo en el producto."))
                        account_t = line.asset_id.category_id.account_cost_id.id

                my_vals = {
                    'name': asset_name,
                    'ref': reference,
                    'move_id': move_id,
                    'account_id': account_t,
                    'credit': 0.0,
                    'debit': amount,
                    'period_id': period_ids and period_ids[0] or False,
                    'journal_id': journal_id,
                    'partner_id': partner_id,
                    'currency_id': company_currency != current_currency and  current_currency or False,
                    'amount_currency': company_currency != current_currency and sign * line.amount or 0.0,
                    'analytic_account_id': aa_line[cant-1].analytic_account_id.id if aa_line else False,
                    'date': depreciation_date,
                    'asset_id': line.asset_id.id
                }
                move_line_obj.create(cr, uid, my_vals)
                cant -= 1
                amount = resto - amount
#        FIN
            self.write(cr, uid, line.id, {'move_id': move_id}, context=context)
            created_move_ids.append(move_id)
            asset_ids.append(line.asset_id.id)
        # we re-evaluate the assets to determine whether we can close them
        for asset in asset_obj.browse(cr, uid, list(set(asset_ids)), context=context):
            if currency_obj.is_zero(cr, uid, asset.currency_id, asset.value_residual):
                asset.write({'state': 'close'})
        return created_move_ids

account_asset_depreciation_line()


class generate_invoices(models.TransientModel):
    _name = "generate.invoices"

    @api.multi
    def invoices_to_draft(self):
        for invoices in self.env['account.invoice'].browse(self._context['active_ids']):
            if invoices.state == 'cancel':
                invoices.action_cancel_draft()
        return True
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
