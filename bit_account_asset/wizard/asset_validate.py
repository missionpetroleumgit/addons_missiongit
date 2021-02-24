# -*- coding: utf-8 -*-
from calendar import month
from openerp import models, fields, api
from string import upper
from openerp.exceptions import except_orm, Warning
import base64
import os
import StringIO
from datetime import datetime
import time
from dateutil.relativedelta import relativedelta


class asset_validate(models.TransientModel):
    _name = 'asset.validate'

    period_id = fields.Many2one('account.period', 'Periodo a depreciar')
    txt_filename = fields.Char()

    @api.multi
    def deprecate(self):
        asset_env = self.env['account.asset.asset']
        ids = self._context['active_ids']
        for asset in asset_env.browse(ids):
            if asset.state != 'close':
                if asset.state == 'draft':
                    asset.validate()
                for line in asset.depreciation_line_ids:
                    if self.period_id.date_start <= line.depreciation_date <= self.period_id.date_stop:
                        if not line.move_check:
                            line.create_move()
                        break
        return True


class asset_modify(models.TransientModel):
    _name = 'asset.modify'
    _inherit = 'asset.modify'

    new_date = fields.Date('Fecha de Reprogramacion', required=True)
    new_residual = fields.Float('Nuevo valor a depreciar')

    @api.v7
    def modify(self, cr, uid, ids, context=None):
        """ Modifies the duration of asset for calculating depreciation
        and maintains the history of old values.
        @param self: The object pointer.
        @param cr: A database cursor
        @param uid: ID of the user currently logged in
        @param ids: List of Ids
        @param context: A standard dictionary
        @return: Close the wizard.
        """
        if not context:
            context = {}
        asset_obj = self.pool.get('account.asset.asset')
        history_obj = self.pool.get('account.asset.history')
        asset_id = context.get('active_id', False)
        asset = asset_obj.browse(cr, uid, asset_id, context=context)
        data = self.browse(cr, uid, ids[0], context=context)
        history_vals = {
            'asset_id': asset_id,
            'name': data.name,
            'method_time': asset.method_time,
            'method_number': asset.method_number,
            'method_period': asset.method_period,
            'method_end': asset.method_end,
            'user_id': uid,
            'date': time.strftime('%Y-%m-%d'),
            'note': data.note,
        }
        history_obj.create(cr, uid, history_vals, context=context)
        aux_date = asset.purchase_date
        salvage_value = asset.salvage_value
        new_date = datetime.strptime(data.new_date, "%Y-%m-%d")
        new_date = new_date - relativedelta(months=1)
        asset_vals = {
            'method_number': data.method_number,
            'method_period': data.method_period,
            'method_end': data.method_end,
            'purchase_date': new_date.strftime("%Y-%m-%d"),
            'salvage_value': asset.purchase_value - asset.value_residual if not data.new_residual else asset.purchase_value - data.new_residual
        }
        asset_obj.write(cr, uid, [asset_id], asset_vals, context=context)
        asset_obj.compute_depreciation_board(cr, uid, [asset_id], context=context)
        asset_obj.write(cr, uid, [asset_id], {'purchase_date': aux_date}, context=context)
        if not data.new_residual:
            asset_obj.write(cr, uid, [asset_id], {'salvage_value': salvage_value}, context=context)
        return {'type': 'ir.actions.act_window_close'}

