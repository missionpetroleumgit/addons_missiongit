# -*- coding: utf-8 -*-
from openerp.tools import float_compare, float_is_zero
from openerp import api, models, fields, _
from openerp.exceptions import except_orm


class MrpBomLine(models.Model):
    _inherit = 'mrp.bom.line'

    type = fields.Selection(selection_add=[('service', 'Servicio')])


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    account_move_ids = fields.Many2many('account.move', 'production_move_rel', 'move_id', 'prod_id', 'Asientos')
    move_count = fields.Integer(compute='_calc_move_count')

    @api.multi
    def _calc_move_count(self):
        for production in self:
            production.move_count = len(production.account_move_ids)

    @api.multi
    def action_view_account_moves(self):
        self.ensure_one()
        action = self.env.ref('account.action_move_journal_line').read()[0]
        action.update({'domain': [('id', 'in', self.mapped('account_move_ids').ids)]})
        return action

    def action_confirm(self, cr, uid, ids, context=None):
        res = super(MrpProduction, self).action_confirm(cr, uid, ids, context=context)
        for record in self.browse(cr, uid, ids, context=context):
            if record.state == 'ready':
                record._make_journal_item(mode='inventory')
        return res

    # def action_assign(self, cr, uid, ids, context=None):
    #     res = super(MrpProduction, self).action_assign(cr, uid, ids, context=context)
    #     for record in self.browse(cr, uid, ids, context=context):
    #         if record.state == 'ready':
    #             record._make_journal_item(mode='inventory')
    #     return res

    def action_produce(self, cr, uid, production_id, production_qty, production_mode, wiz=False, context=None):
        res = super(MrpProduction, self).action_produce(cr, uid, production_id, production_qty, production_mode, wiz=wiz, context=context)
        prod = self.browse(cr, uid, production_id, context=context)
        for record in self.browse(cr, uid, production_id, context=context):
            for item in record.stock_moves:
                if item.state != 'done' and record.post_consum:
                    raise except_orm('Error', 'Debe procesar primero las transferencias de post consumo.')
            if record.state == 'in_production':
                record.state = 'done'
        if production_mode == 'consume':
            prod._make_journal_item('production_cost')
            if prod.state == 'ready':
                self.signal_workflow(cr, uid, [production_id], 'button_produce')
        elif production_mode == 'consume_produce':
            prod._make_journal_item('inventory_out')
        return res

    # modes: inventory_in, production_cost, inventory_out

    @api.multi
    def _make_journal_item(self, mode):
        self.ensure_one()
        AccountMove = self.env['account.move']
        journal = self.env.ref('stock_account.stock_journal')
        move = AccountMove.create({'journal_id': journal.id,
                                   'ref': self.name})
        if mode == 'inventory':
            self._create_inventory_in_move_lines(move.id)
        elif mode == 'production_cost':
            standard_price = self._create_cost_move_lines(move.id)
            self.product_id.write({'standard_price': standard_price})
        elif mode == 'inventory_out':
            self._create_inventory_final_move_lines(move.id)
        self.write({'account_move_ids': [(4, move.id)]})
        return True

    def _create_inventory_in_move_lines(self, move_id):
        AccountMoveLine = self.env['account.move.line']
        production_stock = self.env.ref('stock.location_production')
        lines_values = {}
        debit = 0.0
        if not self.move_lines and not self.move_lines2:
            raise except_orm('Error', 'Debe generar una lista de materiales o asignar uno a la orden de produccion actual.')
        if not self.move_lines2.filtered(lambda ml: ml.state == 'done'):
            raise except_orm('Error', 'Debe aceptar primero las transferencias de materias primas.')
        for sm in self.move_lines2.filtered(lambda ml: ml.state == 'done'):
            if not sm.product_id.property_stock_account_input:
                raise except_orm('Error', 'Configure la cuenta de inventario para el producto %s.' % sm.product_id.name)
            debit += sm.product_id.standard_price * sm.product_qty
            if sm.product_id.property_stock_account_input.id not in lines_values:
                lines_values[sm.product_id.property_stock_account_input.id] = {
                    'account_id': sm.product_id.property_stock_account_input.id,
                    'name': self.name,
                    'credit': sm.product_id.standard_price * sm.product_qty,
                    'move_id': move_id,
                    'debit': 0.0,
                }
            else:
                lines_values[sm.product_id.property_stock_account_input.id]['credit'] += sm.product_id.standard_price * sm.product_qty
        for key, val in lines_values.iteritems():
            AccountMoveLine.create(val)
        if not production_stock.valuation_in_account_id:
            raise except_orm('Error', 'Configure la cuenta de inventario para la ubicacion %s.' % production_stock.name)
        AccountMoveLine.create({
            'account_id': production_stock.valuation_in_account_id.id,
            'name': self.name,
            'debit': debit,
            'credit': 0.0,
            'move_id': move_id

        })

    def _create_cost_move_lines(self, move_id):
        AccountMoveLine = self.env['account.move.line']
        production_stock = self.env.ref('stock.location_production')
        lines_values = {}
        credit = 0.0
        for sm in self.move_lines2.filtered(lambda ml: ml.state == 'done'):
            if not sm.product_id.property_account_cost_id:
                raise except_orm('Error', 'Configure la cuenta de costo para el producto %s.' % sm.product_id.name)
            credit += sm.product_id.standard_price * sm.product_qty
            if sm.product_id.property_account_cost_id.id not in lines_values:
                lines_values[sm.product_id.property_account_cost_id.id] = {
                    'account_id': sm.product_id.property_account_cost_id.id,
                    'name': self.name,
                    'debit': sm.product_id.standard_price * sm.product_qty,
                    'move_id': move_id,
                    'credit': 0.0,
                }
            else:
                lines_values[sm.product_id.property_account_cost_id.id]['debit'] += sm.product_id.standard_price * sm.product_qty
        service_lines = self.bom_id.bom_line_ids.filtered(lambda l: l.type == 'service')
        for item in service_lines:
            if not item.product_id.property_account_cost_id:
                raise except_orm('Error', 'Configure la cuenta de costo para el producto %s.' % item.product_id.name)
            credit += item.product_id.standard_price * item.product_qty
            if item.product_id.property_account_cost_id.id not in lines_values:
                lines_values[item.product_id.property_account_cost_id.id] = {
                    'account_id': item.product_id.property_account_cost_id.id,
                    'name': self.name,
                    'debit': item.product_id.standard_price * item.product_qty,
                    'move_id': move_id,
                    'credit': 0.0,
                }
            else:
                lines_values[item.product_id.property_account_cost_id.id]['debit'] += item.product_id.standard_price * item.product_qty

        for key, val in lines_values.iteritems():
            AccountMoveLine.create(val)
        if not production_stock.valuation_in_account_id:
            raise except_orm('Error', 'Configure la cuenta de inventario para la ubicacion %s.' % production_stock.name)
        AccountMoveLine.create({
            'account_id': production_stock.valuation_in_account_id.id,
            'name': self.name,
            'credit': credit,
            'debit': 0.0,
            'move_id': move_id

        })
        return credit

    def _create_inventory_final_move_lines(self, move_id):
        AccountMoveLine = self.env['account.move.line']
        lines_values = {}
        debit = 0.0
        for sm in self.move_lines2.filtered(lambda ml: ml.state == 'done'):
            if not sm.product_id.property_account_cost_id:
                raise except_orm('Error', 'Configure la cuenta de costo para el producto %s.' % sm.product_id.name)
            debit += sm.product_id.standard_price * sm.product_qty
            if sm.product_id.property_account_cost_id.id not in lines_values:
                lines_values[sm.product_id.property_account_cost_id.id] = {
                    'account_id': sm.product_id.property_account_cost_id.id,
                    'name': self.name,
                    'credit': sm.product_id.standard_price * sm.product_qty,
                    'move_id': move_id,
                    'debit': 0.0,
                }
            else:
                lines_values[sm.product_id.property_account_cost_id.id]['credit'] += sm.product_id.standard_price
        service_lines = self.bom_id.bom_line_ids.filtered(lambda l: l.type == 'service')
        for item in service_lines:
            if not item.product_id.property_account_cost_id:
                raise except_orm('Error', 'Configure la cuenta de costo para el producto %s.' % item.product_id.name)
            debit += item.product_id.standard_price * item.product_qty
            if item.product_id.property_account_cost_id.id not in lines_values:
                lines_values[item.product_id.property_account_cost_id.id] = {
                    'account_id': item.product_id.property_account_cost_id.id,
                    'name': self.name,
                    'credit': item.product_id.standard_price * item.product_qty,
                    'move_id': move_id,
                    'debit': 0.0,
                }
            else:
                lines_values[item.product_id.property_account_cost_id.id]['credit'] += item.product_id.standard_price * item.product_qty

        for key, val in lines_values.iteritems():
            AccountMoveLine.create(val)
        if not self.product_id.property_stock_account_input:
            raise except_orm('Error', 'Configure la cuenta de inventario para el producto %s.' % self.product_id.name)
        AccountMoveLine.create({
            'account_id': self.product_id.property_stock_account_input.id,
            'name': self.name,
            'credit': 0.0,
            'debit': debit,
            'move_id': move_id

        })

    @api.multi
    def action_cancel(self):
        res = super(MrpProduction, self).action_cancel()
        for production in self:
            production.account_move_ids.button_cancel()
            production.account_move_ids.unlink()
        return True

