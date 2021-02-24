# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
#    Copyright (C) 2010-2012 OpenERP s.a. (<http://openerp.com>).
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


from openerp.osv import orm
from openerp.osv import fields
from openerp.tools.translate import _


def _reopen(self, res_id, model, title):
    return {
        'name': _(title),
        'type': 'ir.actions.act_window',
        'view_mode': 'form',
        'view_type': 'form',
        'res_id': res_id,
        'res_model': self._name,
        'target': 'new',
        # save original model in context, because selecting
        # the list of available templates requires a
        # model in context
        'context': {
            'default_model': model,
        },
    }


class purchase_cost_wizard(orm.TransientModel):

    _name = "purchase.cost.wizard"
    _description = "Import incoming shipments"
    _columns = {
        'partner_id': fields.many2one('res.partner',
                                      'Supplier'),

        'picking_id': fields.many2one('stock.picking',
                                       'Incoming Shipments'),

        'state': fields.selection([
                                   ('step1', 'Step 1'),
                                   ('step2', 'Step 2'),
                                   ('done', 'Done'),
                                   ],
                                   'Status',
                                   readonly=True)
                }

    def action_copy_picking(self, cr, uid, ids, context=None):
        wizard = self.browse(cr, uid, ids[0], context=context)
        picking_obj = self.pool.get('stock.picking')
        if wizard.picking_id.id:
            picking_id = picking_obj.browse(
                                            cr,
                                            uid,
                                            wizard.picking_id.id,
                                            context=context)
            for move in picking_id.move_lines:
                res = {
                       'order_id': context['cost_order_id'],
                       'partner_id': picking_id.partner_id.id,
                       'purchase_id': picking_id.purchase_id.id,
                       'purchase_line_id': move.purchase_line_id.id,
                       'picking_id': move.picking_id.id,
                       'move_line_id': move.id,
                       'name': move.name,
                       'product_id': move.product_id.id,
                       'product_qty': move.product_qty,
                       'product_uom': move.product_uom.id,
                       'product_uos_qty': move.product_uos_qty,
                       'product_uos': move.product_uos.id,
                       'product_price_unit': move.price_unit or 0.0,
                       'standard_price_old': move.product_id.product_tmpl_id.standard_price or 0.0,
                       'product_volume': move.product_id.product_tmpl_id.volume,
                       'product_weight': move.product_id.product_tmpl_id.weight,
                       'product_weight_net': move.product_id.product_tmpl_id.weight_net,

                       }
                self.pool.get('purchase.cost.order.line').create(
                                                                cr,
                                                                uid,
                                                                res,
                                                                context=context
                                                                )

                res.clear()

        else:
            raise orm.except_orm(
                             _('Error'),
                             _('Please select incoming shippment')
                             )
        mod_obj = self.pool.get('ir.model.data')
        res = mod_obj.get_object_reference(
                                           cr,
                                           uid,
                                           'purchase_expense_distribution',
                                           'purchase_cost_order_form'
                                           )

        view_id = res and res[1] or False,

        return {
            'name': _('Purchase Cost Order'),
            'view_type': 'tree,form',
            'view_mode': 'form',
            'view_id': view_id,
            'res_model': 'purchase.cost.order',
            'type': 'ir.actions.act_window',
            'res_id': context['cost_order_id'],
            'nodestroy': True,
            'target': 'current',
        }

    def action_to_step2(self, cr, uid, ids, context=None):
        wizard = self.browse(cr, uid, ids[0], context=context)
        self.write(cr, uid, ids, {'state': 'step2'})
        return _reopen(
                       self,
                       wizard.id,
                       'purchase.cost.wizard',
                       'Please select Incoming Shippment'
                       )

    def action_back_step1(self, cr, uid, ids, context=None):
        wizard = self.browse(cr, uid, ids[0], context=context)
        self.write(cr, uid, ids, {'state': 'step1'})
        return _reopen(
                       self,
                       wizard.id,
                       'purchase.cost.wizard',
                       'Please select Supplier'
                       )






# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
