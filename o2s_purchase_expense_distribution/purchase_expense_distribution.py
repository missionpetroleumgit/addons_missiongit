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

import time
from datetime import datetime
from dateutil.relativedelta import relativedelta
import openerp.addons.decimal_precision as dp
from openerp.addons.product.product import *
from openerp.tools.translate import _
from openerp.osv import orm
from openerp.osv import fields
from openerp.osv import osv
from openerp.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT
from openerp.tools.misc import DEFAULT_SERVER_DATE_FORMAT


def is_float(s):
    try:
        float(s)
        return True
    except ValueError:
        return False


def convert_couma_to_point(s):
    index = s.index(',')
    if index:
        count = s.count(',')
        if count != 1:
            raise osv.except_osv('Error!!', 'Formato equivocado')
        _str = s.replace(',', '.')
        return _str
    return s


class purchase_cost_expense_type(orm.Model):
    _name = "purchase.cost.expense.type"
    _description = "Purchase Expenses Types"
    _columns = {
                'name': fields.char('Name', size=128,
                                    required=True,
                                    translate=True,
                                    select=True),
                'ref': fields.char('Reference', size=64,
                                   required=True,
                                   select=True),
                'company_id': fields.many2one('res.company', 'Company',
                                              required=True,
                                              select=1),
                'default_expense': fields.boolean('Default Expense',
                                                  help="Specify if the expense can be automatic selected in a purchase cost order."),
                'calculation_method': fields.selection([
            ('amount', 'Amount line'),
            ('price', 'Product price'),
            ('qty', 'Product quantity'),
            ('weight', 'Product weight'),
            ('weight_net', 'Product weight net'),
            ('volume', 'Product Volume'),
            ('equal', 'Equal to')
            ], 'Calculation Method'),
                'note': fields.text('Cost Documentation'),
                }

    _defaults = {
                 'company_id': lambda self, cr, uid, c: self.pool.get('res.company')._company_default_get(cr, uid, 'purchase.cost.type', context=c),
                 'calculation_method': 'amount',
                 'default_expense': False,
                 }

    def unlink(self, cr, uid, ids, context=None):
        order_expenses = self.pool.get('purchase.cost.order.expense').search(
                                                                             cr,
                                                                             uid,
                                                                             [('type_id',
                                                                               'in',
                                                                               ids)],
                                                                             )
        if order_expenses:
            raise osv.except_osv(_('Invalid Action!'), _('You can not delete expense type, is being used!'))
        return osv.osv.unlink(self, cr, uid, ids, context=context)


class purchase_cost_order(orm.Model):

    def _recalculate_all(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for order in self.browse(cr, uid, ids, context=context):
            res[order.id] = {
                'uom_qty': 0.0,
                'weight': 0.0,
                'weight_net': 0.0,
                'purchase_amount': 0.0,
                'volume': 0.0,
                'product_price_amount': 0.0,
                }
            val1 = val2 = val3 = val4 = val5 = val6 = 0.0
            for line in order.cost_line:
                val1 += line.product_qty
                val2 += line.product_id.weight * line.product_qty
                val3 += line.product_id.weight_net * line.product_qty
                val4 += line.product_qty * line.product_price_unit
                val5 += line.product_volume * line.product_price_unit
                val6 += line.product_price_unit
            res[order.id]['uom_qty'] = val1
            res[order.id]['weight'] = val2
            res[order.id]['weight_net'] = val3
            res[order.id]['purchase_amount'] = val4
            res[order.id]['volume'] = val5
            res[order.id]['product_price_amount'] = val6
            res[order.id]['amount_total'] = val4 + order.expense_amount
        return res

    def _amount_expense(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        val = 0.0
        for order in self.browse(cr, uid, ids, context=context):
            for expenseline in order.invoice_cost_ids:
                val += expenseline.amount
            res[order.id] = val
        return res

    def _expense_id_default(self, cr, uid, ids, context=None):

        expense_type_ids = []
        expense_ids = self.pool.get(
                                    'purchase.cost.expense.type'
                                    ).search(
                                             cr,
                                             uid,
                                             [(
                                               'default_expense',
                                               '=',
                                               True
                                               )],
                                              context=context
                                              )
        if expense_ids:
            for expense in expense_ids:
                res = {
                       'type_cost_id': expense
                       }
                expense_type_ids.append(res)
            return expense_type_ids
        return False

    def _get_order(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('purchase.cost.order.line').browse(cr, uid, ids, context=context):
            result[line.order_id.id] = True
        return result.keys()

    def _get_currency(self, cr, uid, context=None):
        currency_id = self.pool.get('res.users').browse(cr,
                                                        uid,
                                                        uid,
                                                        context=context
                                                        ).company_id.currency_id.id
        res = currency_id
        return res

    def _get_expenses(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('invoice.cost.from.purchase').browse(cr,
                                                                        uid,
                                                                        ids,
                                                                        context=context):
            result[line.order_id.id] = True
        return result.keys()

    _name = "purchase.cost.order"
    _description = "Purchase Cost Order"
    _columns = {
                'name': fields.char('Name', size=128, required=True,
                                    translate=True,
                                    select=True),
                'type_cost_id': fields.many2one(
                           'purchase.cost.expense.type',
                           'Expense Type',
                           select=True,
                           readonly=True,
                           ondelete="set null"
                           ),
                'purchase_id': fields.many2one('purchase.order', 'Purchase order',
                                              required=True, domain=[('cost_id','=',False)],
                                              select=1),
                'currency_id': fields.many2one(
                                               'res.currency',
                                               'Currency',
                                               help="The optional other currency if it is a multi-currency entry."
                                               ),

                'company_id': fields.many2one('res.company', 'Company',
                                              required=True, select=1),
                'state': fields.selection(
                                          [('draft', 'Draft Order'),
                                           ('calculated', 'Order Calculated'),
                                           ('done', 'Done'),
                                           ('error', 'Error'),
                                           ('cancel', 'Cancel'),
                                           ],
                                           'Status',
                                           readonly=True
                                           ),
                'cost_update_type': fields.selection(
                                                      [
                                                       ('nation', 'National'),
                                                       ('import', 'Import'),
                                                       ],
                                                      'Cost Update Type'
                                                      ),

                'date_order': fields.date('Date', required=True,
                                          readonly=True,
                                          select=True,
                                          states={'draft': [(
                                                             'readonly',
                                                              False
                                                              )]
                                                  }
                                          ),
                'uom_qty': fields.function(_recalculate_all,
                                           digits_compute = dp.get_precision('Product UoS'),
                                           string ='Order Quantity',
                            store = {
                                     'purchase.cost.order': (lambda self,
                                                             cr,
                                                             uid,
                                                             ids,
                                                             c={}: ids,
                                                             ['cost_line'],
                                                             10
                                                             ),
                                     'purchase.cost.order.line': (_get_order,
                                                                  None,
                                                                  20
                                                                  ),
                                     }, multi='totals'
                                           ),
                'weight': fields.function(_recalculate_all,
                                          digits_compute = dp.get_precision('Stock Weight'),
                                          string='Order Gross Weight',
                                          help="The gross weight in Kg.",
                                          store={
                                                 'purchase.cost.order': (lambda self,
                                                                         cr,
                                                                         uid,
                                                                         ids,
                                                                         c={}: ids,
                                                                         ['cost_line'],
                                                                         10
                                                                         ),
                                                 'purchase.cost.order.line': (_get_order,
                                                                              None,
                                                                              20
                                                                              ),
                                                 }, multi='totals'
                                          ),
                'weight_net': fields.function(_recalculate_all,
                                              digits_compute = dp.get_precision('Stock Weight'),
                                              string='Order Net Weight',
                                              readonly=True, help="The net weight in Kg.",
                                              store={
                                                     'purchase.cost.order': (lambda self,
                                                                             cr,
                                                                             uid,
                                                                             ids,
                                                                             c={}: ids,
                                                                             ['cost_line'],
                                                                             10
                                                                             ),
                                                     'purchase.cost.order.line': (_get_order,
                                                                                  None,
                                                                                  20
                                                                                  ),
                                                     }, multi='totals'
                                              ),
                'volume': fields.function(_recalculate_all,
                                          string='Order Volume',
                                          readonly=True,
                                          help="The volume in m3.",
                                          store={
                                                 'purchase.cost.order': (lambda self,
                                                                         cr,
                                                                         uid,
                                                                         ids,
                                                                         c={}: ids,
                                                                         ['cost_line'],
                                                                         10
                                                                         ),
                                                 'purchase.cost.order.line': (_get_order,
                                                                              None,
                                                                              20
                                                                              ),
                                                 }, multi='totals'
                                          ),
                'purchase_amount': fields.function(_recalculate_all,
                                                   digits_compute = dp.get_precision('Account'),
                                                   string='Purchase Total',
                                                   store={
                                                          'purchase.cost.order': (lambda self,
                                                                                  cr,
                                                                                  uid,
                                                                                  ids,
                                                                                  c={}: ids,
                                                                                  ['cost_line'],
                                                                                  10
                                                                                  ),
                                                          'purchase.cost.order.line': (_get_order,
                                                                                       None,
                                                                                       20
                                                                                       ),
                                                          }, multi='totals'
                                                   ),
                'amount_total': fields.function(_recalculate_all,
                                                digits_compute = dp.get_precision('Account'),
                                                string='Total',
                                                   store={
                                                          'purchase.cost.order': (lambda self,
                                                                                  cr,
                                                                                  uid,
                                                                                  ids,
                                                                                  c={}: ids,
                                                                                  ['cost_line'],
                                                                                  10
                                                                                  ),
                                                          'purchase.cost.order.line': (_get_order,
                                                                                       None,
                                                                                       20
                                                                                       ),
                                                          }, multi='totals'
                                                ),

                'expense_amount': fields.function(_amount_expense,
                                                  digits_compute = dp.get_precision('Account'),
                                                  string='Expense Amount',
                                                  store={
                                                         'invoice.cost.from.purchase': (_get_expenses,
                                                                                         None,
                                                                                         20
                                                                                         ),
                                                         'purchase.cost.order.line': (_get_order,
                                                                                            None,
                                                                                            20
                                                                                            ),
                                                               }, muti='totals'
                                                  ),
                'note': fields.text('Documentation for this order'),
                'expense_line': fields.many2one(
                                                'purchase.cost.order.expense',
                                                'Cost Distributions',
                                                ondelete="set null"
                                                ),
                'cost_line': fields.one2many(
                                             'purchase.cost.order.line',
                                             'order_id',
                                             'Order Lines',
                                             ondelete="cascade"
                                             ),
                'invoice_cost_ids': fields.one2many('invoice.cost.from.purchase', 'cost_id', 
                                                    'Invoice lines', ondelete="cascade"),
                'lognote': fields.text('Log process for this order', readonly=True),

                'log_line': fields.one2many(
                                             'purchase.cost.order.log',
                                             'order_id',
                                             'Log Lines',
                                             ondelete="cascade"
                                             ),

                'product_price_amount': fields.function(_amount_expense,
                                                        digits_compute = dp.get_precision('Account'),
                                                        string='Product unit amount',
                                                        store={
                                                               'purchase.cost.order': (lambda self,
                                                                                       cr,
                                                                                       uid,
                                                                                       ids,
                                                                                       c={}: ids,
                                                                                       ['cost_line'],
                                                                                       10
                                                                                       ),
                                                               'purchase.cost.order.line': (_get_order,
                                                                                            None,
                                                                                            20
                                                                                            ),
                                                               }, muti='totals'
                                                        ),
                }

    _defaults = {
                 'company_id': lambda self, cr, uid, c: self.pool.get('res.company')._company_default_get(cr,
                                                                                                          uid,
                                                                                                          'purchase.cost.order',
                                                                                                          context=c),
                 'date_order': fields.date.context_today,
                 'type_cost_id': _expense_id_default,
                 'currency_id': _get_currency,
                 'name': lambda obj, cr, uid, context: '/',
#                 'state': 'draft',
                 'cost_update_type': 'nation',
                 }
    _order = 'name desc'

    def unlink(self, cr, uid, ids, context=None):
        cost_orders = self.read(cr, uid, ids, ['state'], context=context)
        unlink_ids = []
        for c in cost_orders:
            if c['state'] in ['draft', 'calculated']:
                unlink_ids.append(c['id'])
            else:
                raise osv.except_osv(_('Invalid Action!'),
                                     _('In order to delete a confirmed cost order!'))

        return osv.osv.unlink(self, cr, uid, unlink_ids, context=context)

    def create(self, cr, uid, vals, context=None):
        vals['state'] = 'draft'
        if vals.get('name', '/') == '/':
            vals['name'] = self.pool.get(
                                         'ir.sequence'
                                         ).get(
                                               cr,
                                               uid,
                                               'purchase.cost.order'
                                               ) or '/'
        vals.update(self._expense_id_default(cr, uid, [], context)[0])
        cost_id = super(purchase_cost_order, self).create(cr, uid, vals, context)
        self.pool.get('purchase.order').write(cr, uid, vals.get('purchase_id'), {'cost_id': cost_id}, context=context)
        return cost_id

    def onchange_purchase_id(self, cr, uid, ids, purchase_id, type_cost_id, cost_update_type, context=None):
        cost_line = []
        inv_line = []
        purchase_total = 0.0
        expense_total = 0.0
        if purchase_id:
            obj_inv = self.pool.get('account.invoice')
            obj_pur = self.pool.get('purchase.order')
            
            pur_order = obj_pur.browse(cr, uid, purchase_id, context=context)
            l_inv = obj_inv.search(cr, uid, ['|',('purchase_id', '=', purchase_id),'&',('origin', '=', pur_order.name),('purchase_id', '=', False), ('state','=','open')])
            inv_order = obj_inv.search(cr, uid, [('origin', '=', pur_order.name),('purchase_id', '=', False)])
           
        # Cargo las líneas de facturas asociadas al Pedido  
            for inv in obj_inv.browse(cr, uid, l_inv, context=context):
                for line in inv.invoice_line:
                    res = {
                           'partner_id': inv.partner_id.id,
                           'purchase_id': purchase_id,
                           'name': line.name,
                           'product_id': line.product_id.id,
                           'product_qty': line.quantity,
                           'product_uom': line.product_id.uom_id.id,
                           'product_uos': line.uos_id.id,
                           'product_price_unit': line.price_unit or 0.0,
                           'standard_price_old': line.price_subtotal or 0.0,
                           'product_volume': line.product_id.product_tmpl_id.volume,
                           'product_weight': line.product_id.product_tmpl_id.weight,
                           'product_weight_net': line.product_id.product_tmpl_id.weight_net,
                           'amount' : line.quantity * line.price_unit,
                           'amount_weight' : line.product_id.product_tmpl_id.weight * line.quantity,
                           'amount_weight_net' : line.product_id.product_tmpl_id.weight_net * line.quantity,
                           'amount_volume' : line.product_id.product_tmpl_id.volume *line.quantity,
                           'expense_amount' : 0.0,
                           'cost_ratio' : 0.0,
                           'standard_price_new' : 0.0
    
                       }                        

                    if inv.id not in inv_order:
                        expense_total += res.get('amount')
                        res.update({'invoice_number' : inv.number })
                        fact = res
                        inv_line.append(fact)
                    else:
                        purchase_total += res.get('amount')
                        purc = res
                        cost_line.append(purc)
            

        return {'value': {
                            'cost_line':cost_line, 
                            'invoice_cost_ids': inv_line,
                            'purchase_amount' : purchase_total,
                            'expense_amount' : expense_total,
                        }}
    
    def action_button_copy(self, cr, uid, ids, context=None):
        res_id = self.pool.get(
                               'purchase.cost.wizard'
                               ).create(
                                        cr,
                                        uid,
                                        {'state': 'step1'},
                                        context=context
                                        )
        mod_obj = self.pool.get('ir.model.data')
        res = mod_obj.get_object_reference(
                                           cr,
                                           uid,
                                           'purchase_expense_distribution',
                                           'purchase_cost_wizard_view'
                                           )
        view_id = res and res[1] or False,
        context.update({'cost_order_id': ids[0]})

        return {
            'name': _('Please select Supplier'),
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': view_id,
            'res_model': 'purchase.cost.wizard',
            'type': 'ir.actions.act_window',
            'res_id': res_id,
            'nodestroy': True,
            'target': 'new',
            'context': context,
        }

    def button_dummy(self, cr, uid, ids, context=None):
        return True

    def action_draft2calculated(self, cr, uid, ids, context=None):
        for order in self.browse(cr, uid, ids, context=context):
            #Check if exist lines in order
            if not order.cost_line:
                raise orm.except_orm(
                                     _('ERROR NOT LINES!'),
                                     _('No shipping lines in this order')
                                     )
            #Check data for expense type call check_datas function
            check_datas = self.test_datas_out_log(cr, uid, ids, context)
            if check_datas == True:
                self.write(cr, uid, [order.id], {'state': 'error'}, context=context)
                return False
            # Calculating expense line
            if order.type_cost_id.calculation_method == 'amount':
#                for expense in order.invoice_cost_ids:
                for line in order.cost_line:
                    percent = line.amount / order.purchase_amount   # porcentaje del total
                    por_repartir = percent * order.expense_amount
                    precio_x_unit = por_repartir / line.product_qty
                    res = {
                                'id': line.id,
                           }  
                                      
                    line.write({
                                'cost_ratio': precio_x_unit,
                                'expense_amount': por_repartir,
                                'standard_price_old': line.amount + por_repartir,
                                'standard_price_new': line.product_price_unit + precio_x_unit,
                        })

        #Write log line and change order state
        res = {
               'name': 'Calculation log %s' % (time.strftime('%Y-%m-%d %H:%M:%S')),
               'order_id': order.id,
               'state': 'done',
               'date_log': time.strftime('%Y-%m-%d %H:%M:%S'),
               'lognote': _('Calculation is Done'),
               }
        self.pool.get('purchase.cost.order.log').create(
                                                        cr,
                                                        uid,
                                                        res,
                                                        context=context
                                                        )
        self.write(cr,
                   uid,
                   [order.id],
                   {'state': 'calculated'},
                   context=context
                   )

        return True

    def action_calculated2done(self, cr, uid, ids, context=None):
        obj_prod = self.pool.get('product.product')
        for order in self.browse(cr, uid, ids, context=context):
            for line in order.cost_line:
                prod_id = line.product_id.id
                obj_prod.write(cr, uid, [prod_id], {'standard_price': line.standard_price_new })

        self.write(cr, uid, [order.id], {'state': 'done'}, context=context)
        res = {
               'name': 'Calculation log %s' % (time.strftime('%Y-%m-%d %H:%M:%S')),
               'order_id': order.id,
               'state': 'update',
               'date_log': time.strftime('%Y-%m-%d %H:%M:%S'),
               'lognote': _('Update Cost price of products is Done'),
               }
        self.pool.get('purchase.cost.order.log').create(
                                                            cr,
                                                            uid,
                                                            res,
                                                            context=context
                                                            )
        return True

    def test_datas_out_log(self, cr, uid, ids, context=None):
        test_result = False
        logtext = ""
        for order in self.browse(cr, uid, ids, context=context):
            #Check mandatory totals
            if order.purchase_amount == 0.0:
                test_result = True
                logtext += _('Missing total purchase amount.\n')
            if order.uom_qty == 0.0:
                test_result = True
                logtext += _('Missing total purchase qty.\n')
            if order.expense_amount == 0.0 and order.cost_update_type is 'import':
                test_result = True
                logtext += _('Missing total expense amount.\n')
            #Check mandatory data in lines for expense type
            for expense in order.expense_line:
                if expense.type_id.calculation_method == 'amount':
                    line_num = 1
                    for line in order.cost_line:
                        if line.amount == 0.0:
                            test_result = True
                            logtext += _(
                                'Missing total in line %s product %s.\n' %
                                         (line_num, line.name)
                                         )
                            line_num = line_num + 1
                elif expense.type_id.calculation_method == 'price':
                    line_num = 1
                    for line in order.cost_line:
                        if line.product_price_unit == 0.0:
                            test_result = True
                            logtext += _(
                                'Missing product price in line %s product %s.\n' %
                                         (line_num, line.name)
                                         )
                            line_num = line_num + 1
                elif expense.type_id.calculation_method == 'qty':
                    if order.uom_qty == 0.0:
                        test_result = True
                        logtext += _('Missing total purchase qty.\n')
                    line_num = 1
                    for line in order.cost_line:
                        if line.product_qty == 0.0:
                            test_result = True
                            logtext += _(
                                'Missing product qty in line %s product %s.\n' %
                                         (line_num, line.name)
                                         )
                            line_num = line_num + 1
                elif expense.type_id.calculation_method == 'weight':
                    if order.weight == 0.0:
                        test_result = True
                        logtext += _('Missing total purchase weight.\n')
                    line_num = 1
                    for line in order.cost_line:
                        if line.product_weight == 0.0:
                            test_result = True
                            logtext += _(
                                'Missing product weight in line %s product %s.\n' %
                                         (line_num, line.name)
                                         )
                            line_num = line_num + 1
                elif expense.type_id.calculation_method == 'weight_net':
                    if order.weight_net == 0.0:
                        test_result = True
                        logtext += _('Missing total purchase weight net.\n')
                    line_num = 1
                    for line in order.cost_line:
                        if line.product_weight_net == 0.0:
                            test_result = True
                            logtext += _(
                                'Missing product weight net in line %s product %s.\n' %
                                         (line_num, line.name)
                                         )
                            line_num = line_num + 1
                elif expense.type_id.calculation_method == 'volume':
                    if order.volume == 0.0:
                        test_result = True
                        logtext += _('Missing total purchase volume.\n')
                    line_num = 1
                    for line in order.cost_line:
                        if line.product_volume == 0.0:
                            test_result = True
                            logtext += _(
                                'Missing product volume in line Id %s product %s.\n' %
                                         (line_num, line.name)
                                         )
                            line_num = line_num + 1

        #Write log field
        if test_result == True:
            res = {
                   'name': 'Calculation log %s' %
                   (
                    time.strftime('%Y-%m-%d %H:%M:%S')
                    ),
                   'order_id': order.id,
                   'state': 'error',
                   'date_log': time.strftime('%Y-%m-%d %H:%M:%S'),
                   'lognote': logtext,
                   }
            self.pool.get('purchase.cost.order.log').create(
                                                            cr,
                                                            uid,
                                                            res,
                                                            context=context
                                                            )
            return test_result

    def action_calculated2draft(self, cr, uid, ids, context=None):
        for order in self.browse(cr, uid, ids, context=context):
            expense_line_ids = []
            for line in order.cost_line:
                for expense in line.expense_line:
                    expense_line_ids.append(expense.id)
        expense_line_obj = self.pool.get('purchase.cost.order.line.expense')
        expense_line_obj.unlink(cr, uid, expense_line_ids)
        res = {
               'name': 'Calculation log %s' % (time.strftime('%Y-%m-%d %H:%M:%S')),
               'order_id': order.id,
               'state': 'draft',
               'date_log': time.strftime('%Y-%m-%d %H:%M:%S'),
               'lognote': _('The Order has been changed from Calculated to Draft by the action of cancel button'),
               }
        self.pool.get('purchase.cost.order.log').create(
                                                            cr,
                                                            uid,
                                                            res,
                                                            context=context
                                                            )

        self.write(cr, uid, [order.id], {'state': 'draft'}, context=context)
        return True
    
#Haciendo el metodo defaul:    
    
    def default_get(self, cr, uid, fields, context=None):
        if context is None:
            context = {}
        res = super(purchase_cost_order, self).default_get(cr, uid, fields, context=context)
        cost_type_id = self.pool.get('purchase.cost.expense.type').search(cr, uid, [])
        res['type_cost_id'] = cost_type_id       
        return res
    



class purchase_cost_order_log(orm.Model):
    _name = "purchase.cost.order.log"
    _descripction = "Purchase Cost Order Calculate Log"
    _order = "id desc"
    _columns = {
                'order_id': fields.many2one(
                                            'purchase.cost.order',
                                            'Cost Order',
                                            select=True,
                                            ondelete="cascade"
                                            ),
                'name': fields.char('Name', size=128, required=True,
                                    translate=True,
                                    select=True),
                'state': fields.selection(
                                          [('error', 'Calculation Error'),
                                           ('done', 'Calculation Done'),
                                           ('update','Update products cost Done'),
                                           ('draft', 'Order return in Draft')
                                           ],
                                           'Status',
                                           readonly=True,
                                           ),
                'date_log': fields.date('Date', required=True,
                                          readonly=True,
                                          select=True),
                'lognote': fields.text('Description',
                                        readonly=True),

                }


class purchase_cost_order_expense(orm.Model):
    _name = "purchase.cost.order.expense"
    _description = "Purchase Cost Expenses"
    _columns = {
                'order_id': fields.many2one(
                                            'purchase.cost.order',
                                            'Cost Order',
                                            select=True,
                                            ondelete="cascade"
                                            ),
                'type_id': fields.many2one(
                                           'purchase.cost.expense.type',
                                           'Expense Type',
                                           select=True,
                                           ondelete="set null"
                                           ),
                'expense_amount': fields.float(
                                            'Expense Amount',
                                            digits_compute=dp.get_precision(
                                                                    'Account'
                                                                            ),
                                               required=True
                                               ),
               }

    _defaults = {
                 #'expense_amount': 0.0,
                 }


class purchase_cost_order_line(orm.Model):

    def _amount_line(self, cr, uid, ids, field_name, arg, context=None):

        res = {}
        if context is None:
            context = {}

        for line in self.browse(cr, uid, ids, context=context):

            res[line.id] = {
                            'amount': 0.0,
                            'amount_weight': 0.0,
                            'amount_weight_net': 0.0,
                            'amount_volume': 0.0,
                            }
            res[line.id]['amount'] = line.product_qty * line.product_price_unit
            res[line.id]['amount_weight'] = line.product_weight * line.product_qty
            res[line.id]['amount_weight_net'] = line.product_weight_net * line.product_qty
            res[line.id]['amount_volume'] = line.product_volume * line.product_qty

        return res

    _name = "purchase.cost.order.line"
    _description = "Purchase Cost Order Line"
    _columns = {
                'order_id': fields.many2one(
                                            'purchase.cost.order',
                                            'Cost Order',
                                            ondelete='cascade'
                                            ),
                'partner_id': fields.many2one(
                                              'res.partner',
                                              'Supplier',
                                              readonly=True,
                                              select=True
                                              ),
                'purchase_id': fields.many2one(
                                               'purchase.order',
                                               'Purchase Order',
                                               ondelete='set null',
                                               select=True
                                               ),
                'purchase_line_id': fields.many2one(
                                                    'purchase.order.line',
                                                    'Purchase Order Line',
                                                    ondelete='set null',
                                                    select=True
                                                    ),
                'expense_line': fields.one2many(
                                            'purchase.cost.order.line.expense',
                                            'order_line_id',
                                            'Expenses Distribution line',
                                            ondelete='cascade'
                                                   ),
                'picking_id': fields.many2one(
                                              'stock.picking',
                                              'Picking',
                                              ondelete='set null'
                                              ),
                'move_line_id': fields.many2one(
                                                'stock.move',
                                                'Picking Line',
                                                ondelete="set null"
                                                ),
                'name': fields.char(
                                    'Description',
                                    required=True,
                                    select=True
                                    ),
                'product_qty': fields.float(
                                    'Quantity',
                                    digits_compute=dp.get_precision(
                                                    'Product Unit of Measure'
                                                                    )
                                            ),
                'product_uom': fields.many2one(
                                               'product.uom',
                                               'Unit of Measure',
                                               ),
                'product_uos_qty': fields.float(
                                        'Quantity (UOS)',
                                        digits_compute=dp.get_precision(
                                                    'Product Unit of Measure'
                                                                        ),
                                                ),
                'product_uos': fields.many2one(
                                               'product.uom',
                                               'Product UOS',
                                               ),
                'product_id': fields.many2one(
                                              'product.product',
                                              'Product',
                                              required=True,
                                              select=True,
                                              ),
                'product_price_unit': fields.float(
                                        'Unit Price',
                                        digits_compute=dp.get_precision(
                                                                'Product Price'
                                                                        )
                                                   ),
                'product_volume': fields.float(
                                               'Volume',
                                               help="The volume in m3."
                                               ),
                'product_weight': fields.float(
                                        'Gross Weight',
                                        digits_compute=dp.get_precision(
                                                                        'Stock Weight'
                                                                        ),
                                        help="The gross weight in Kg."),
                'product_weight_net': fields.float(
                                            'Net Weight',
                                            digits_compute=dp.get_precision(
                                                                'Stock Weight'
                                                                ),
                                                   help="The net weight in Kg."
                                            ),
                'amount': fields.float(string='Amount Line',digits_compute=dp.get_precision('Account')),
                'standard_price_old': fields.float(
                                            'Cost',
                                            digits_compute=dp.get_precision(
                                                                        'Product Price'
                                                                        )
                                                   ),
                'expense_amount': fields.float(
                                               'Cost Amount',
                                            digits_compute=dp.get_precision(
                                                                    'Account'
                                                                    )
                                               ),
                'cost_ratio': fields.float(
                                           'Cost Ratio',
                                           digits_compute=dp.get_precision(
                                                                    'Account'
                                                                    )
                                           ),
                'standard_price_new': fields.float(
                                            'New Cost',
                                            digits_compute=dp.get_precision(
                                                                'Product Price'
                                                                )
                                                   ),
                'company_id': fields.related(
                                             'order_id',
                                             'company_id',
                                             type='many2one',
                                             relation='res.company',
                                             string='Company',
                                             store=True,
                                             readonly=True
                                             ),
                'amount_weight': fields.float(string='Line Gross Weight', digits_compute=dp.get_precision('Stock Weight'), help="The line gross weight in Kg."),
                'amount_weight_net': fields.float(string='Line Net Weight', digits_compute=dp.get_precision('Stock Weight'), help="The line net weight in Kg."),
                'amount_volume': fields.float(string='Line Volume', help="The line volume in m3."),


                }

    _default = {
                'expense_amount': 0.0,
                'cost_ration': 0.0,
                'standard_price_new': 0.0,
                }


class purchase_order_line_expense(orm.Model):
    _name = "purchase.cost.order.line.expense"
    _description = "Purchase Expenses Order Line Distribution"
    _columns = {
                'order_line_id': fields.many2one(
                                                 'purchase.cost.order.line',
                                                 'Cost Order Line',
                                                 ondelete="cascade"
                                                 ),
                'expense_id': fields.many2one(
                                              'invoice.cost.from.purchase',
                                              'Expenses Distribution Line',
                                              ondelete="cascade"
                                              ),
                'type_id': fields.many2one(
                                           'purchase.cost.expense.type',
                                           'Expense Type',
                                           select=True,
                                           ondelete="set null"
                                           ),

                'expense_amount': fields.float(
                                               'Expense Amount Type Line',
                                               digits_compute=dp.get_precision(
                                                                               'Account'
                                                                               )
                                               ),
                'cost_ratio': fields.float(
                                           'Cost Amount for Product',
                                           digits_compute=dp.get_precision(
                                                                           'Account'
                                                                           )
                                           ),
                }
    _default = {
                'expense_amount': 0.0,
                'cost_ration': 0.0,
                }


class invoice_cost_from_purchase(orm.Model):
    
    _name = "invoice.cost.from.purchase"
    _inherit = "purchase.cost.order.line"
    _description = "Purchase Cost Order"
    
    _columns = {
                
            'invoice_number': fields.char('Invoice number', size=64),
            'cost_id': fields.many2one('purchase.cost.order', 'Purchase cost order',
                                           select=True, ondelete="set null"),
                
    }
    
invoice_cost_from_purchase()


class purchase(orm.Model):
    
    def name_get(self,cr,uid,ids, context=None):
        res = []
        for r in self.read(cr , uid, ids, ['name','partner_id'], context):
            name = r['name']
            if r['partner_id']:
                partner = self.pool.get('res.partner').browse(cr, uid, r['partner_id'][0])
                name = name + "/ " + partner.name
            res.append((r['id'], name))
        return res

    _inherit = "purchase.order"
    _description = "Purchase Order"
    
    def _amount_all(self, cr, uid, ids, field_name, arg, context=None):
        return super(purchase, self)._amount_all(cr, uid, ids, field_name, arg, context)
    
    def _get_order(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('purchase.order.line').browse(cr, uid, ids, context=context):
            result[line.order_id.id] = True
        return result.keys()

    def _calculate_new(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for order in self.browse(cr, uid, ids, context=context):
            total = 0.0
            qty = 0.0
            for line in order.order_line:
                if line.percent:
                        total += (line.product_qty * line.price_unit) - line.price_subtotal
                qty += line.product_qty
            res[order.id] = total
        return res

    STATE_SELECTION = [
        ('draft', 'Requisicion'),
        ('sent', 'Revision'),
        ('bid', 'Presupuesto'),
        ('confirmed', 'Waiting Approval'),
        ('approved', 'Compra confirmada'),
        ('except_picking', 'Excepcion de Albaran'),
        ('except_invoice', 'Excepcion de Factura'),
        ('done', 'Realizada'),
        ('cancel', 'Cancelada')
    ]
    
    _columns = {
        'state': fields.selection(STATE_SELECTION, 'Status', readonly=True,
                                  help="The status of the purchase order or the quotation request. "
                                       "A request for quotation is a purchase order in a 'Draft' status. "
                                       "Then the order has to be confirmed by the user, the status switch "
                                       "to 'Confirmed'. Then the supplier must confirm the order to change "
                                       "the status to 'Approved'. When the purchase order is paid and "
                                       "received, the status becomes 'Done'. If a cancel action occurs in "
                                       "the invoice or in the receipt of goods, the status becomes "
                                       "in exception.",
                                  select=True, copy=False),
        'cost_id': fields.many2one('purchase.cost.order', 'Purchase cost order'),
        'is_importation': fields.boolean('Es de importación'),
        'total_discount': fields.function(_calculate_new, string='Descuento Total'),
        'amount_untaxed': fields.function(_amount_all, digits=(16, 2), string='Untaxed Amount',
                                          store={
                                              'purchase.order.line': (_get_order, None, 10),
                                          }, multi="sums", help="The amount without tax", track_visibility='always'),
        'amount_tax': fields.function(_amount_all, digits=(16, 2), string='Taxes',
                                      store={
                                          'purchase.order.line': (_get_order, None, 10),
                                      }, multi="sums", help="The tax amount"),
        'amount_total': fields.function(_amount_all, digits=(16, 2), string='Total',
                                        store={
                                            'purchase.order.line': (_get_order, None, 10),
                                        }, multi="sums", help="The total amount"),
        'order_line': fields.one2many('purchase.order.line', 'order_id', 'Order Lines',
                                      states={'approved':[('readonly',True)],
                                              'done':[('readonly',True)]},
                                      copy=True),
        # 'product_qty_total': fields.function(_calculate_new, string='Cantidad Productos', multi="sums"),
        # 'state_approval': fields.selection([('normal', 'Normal'), ('draft', 'Esperando Aprobacion'), ('done', 'Aprobado')])
        # 'is_importation_real': fields.boolean('Es de importación'),
    }

    _defaults = {
        # 'total_discount': 0.00,
        # 'state_approval': 'normal',
    }

    # def onchange_orderlines(self, cr, uid, ids, order_line=None, context=None):
    #     res = {'value': {}}
    #     qty = 0
    #     if order_line:
    #         for item in order_line:
    #             if isinstance(item[2], list) and item[2]:
    #                 for obj in self.pool.get('purchase.order.line').browse(cr, uid, item[2]):
    #                     qty += obj.product_qty
    #             elif isinstance(item[2], dict):
    #                 qty += item[2]['product_qty']
    #         res['value'].update({'product_qty_total': qty})
    #     return res

    def update_vals(self, cursor, user, ids, context=None):
        return True

    def _prepare_inv_line(self, cr, uid, account_id, order_line, context=None):
        """Collects require data from purchase order line that is used to create invoice line
        for that purchase order line
        :param account_id: Expense account of the product of PO line if any.
        :param browse_record order_line: Purchase order line browse record
        :return: Value for fields of invoice lines.
        :rtype: dict
        """
        return {
            'name': order_line.name,
            'account_id': account_id,
            'price_unit': order_line.price_unit or 0.0,
            'quantity': order_line.product_qty,
            'product_id': order_line.product_id.id or False,
            'uos_id': order_line.product_uom.id or False,
            'invoice_line_tax_id': [(6, 0, [x.id for x in order_line.taxes_id])],
            'account_analytic_id': order_line.account_analytic_id.id or False,
            'purchase_line_id': order_line.id,
            'discount': order_line.percent
        }

    def _prepare_invoice(self, cr, uid, order, line_ids, context=None):
        """Prepare the dict of values to create the new invoice for a
           purchase order. This method may be overridden to implement custom
           invoice generation (making sure to call super() to establish
           a clean extension chain).

           :param browse_record order: purchase.order record to invoice
           :param list(int) line_ids: list of invoice line IDs that must be
                                      attached to the invoice
           :return: dict of value to create() the invoice
        """
        journal_ids = self.pool['account.journal'].search(
                            cr, uid, [('type', '=', 'purchase'),
                                      ('company_id', '=', order.company_id.id)],
                            limit=1)
        if not journal_ids:
            raise osv.except_osv(
                _('Error!'),
                _('Define purchase journal for this company: "%s" (id:%d).') % \
                (order.company_id.name, order.company_id.id))
        if not order.partner_id.property_account_payable:
            raise osv.except_orm('Error!', 'La empresa %s no tiene configurada la cuenta a pagar' % order.partner_id.name)
        return {
            'name': order.partner_ref or order.name,
            'reference': order.partner_ref or order.name,
            'account_id': order.partner_id.property_account_payable.id,
            'type': 'in_invoice',
            'partner_id': order.partner_id.id,
            'currency_id': order.currency_id.id,
            'journal_id': len(journal_ids) and journal_ids[0] or False,
            'invoice_line': [(6, 0, line_ids)],
            'origin': order.name,
            'fiscal_position': order.fiscal_position.id or False,
            'payment_term': order.payment_term_id.id or False,
            'company_id': order.company_id.id,
            # 'total_discount': order.total_discount
        }

    def onchange_discount(self, cr, uid, ids, discount, context=None):
        if isinstance(discount, str):
            index = discount.index('%')
            number = discount[0: index-1]
            if not isinstance(number, (int, long)):
                raise osv.except_osv('Error!!', 'El valor no corresponde con el formato')
        elif isinstance(discount, (int, long)):
            pass

    def default_get(self, cr, uid, fields, context=None):
        if context is None:
            context = {}
        res = super(purchase, self).default_get(cr, uid, fields, context=context)
        if 'is_importation' in context and context['is_importation']:
            res['is_importation'] = True
        elif 'is_importation' in context and not context['is_importation']:
            res['is_importation'] = False
        return res

    # def over_confirm(self, cr, uid, ids, context=None):
    #     self.write(cr, uid, ids, {'state_approval': 'done'})

purchase()


class purchase_order_bill(osv.osv):    
    _inherit = "account.invoice"
    _description = "purchase"
    
        
    _columns = {
           
        'purchase_id': fields.many2one('purchase.order', 'Purchase order'),     
            
    }
    
purchase_order_bill()


class purchase_order_line(osv.osv):
    _inherit = 'purchase.order.line'

    def _amount_line(self, cr, uid, ids, prop, arg, context=None):
        res = {}
        total = 0.00
        cur_obj=self.pool.get('res.currency')
        user = self.pool.get('res.users').browse(cr, uid, uid)
        tax_obj = self.pool.get('account.tax')
        for line in self.browse(cr, uid, ids, context=context):
            taxes = tax_obj.compute_all(cr, uid, line.taxes_id, line.price_unit, line.product_qty, line.product_id, line.order_id.partner_id)
            cur = user.company_id.currency_id
            if line.order_id.pricelist_id:
                cur = line.order_id.pricelist_id.currency_id
            res[line.id] = cur_obj.round(cr, uid, cur, taxes['total'])
            if line.percent > 0:
                res[line.id] -= (res[line.id] * line.percent/100)
        return res

    # def _percent_line(self, cr, uid, ids, prop, arg, context=None):
    #     res = {}
    #     cur_obj=self.pool.get('res.currency')
    #     tax_obj = self.pool.get('account.tax')
    #     for line in self.browse(cr, uid, ids, context=context):
    #         if line.discount:
    #             taxes = tax_obj.compute_all(cr, uid, line.taxes_id, line.price_unit, line.product_qty, line.product_id, line.order_id.partner_id)
    #             cur = line.order_id.pricelist_id.currency_id
    #             price_subtotal = cur_obj.round(cr, uid, cur, taxes['total'])
    #             discount, percent = self.calculate_discount(line.discount, price_subtotal)
    #             res[line.id] = percent
    #         else:
    #             res[line.id] = 0.00
    #     return res

    _columns = {
        'price_unit': fields.float('Unit Price', required=True, digits=(16, 2)),
        'price_subtotal': fields.function(_amount_line, string='Subtotal', digits=(16, 2)),
        'discount': fields.char('Descuento', help='El descuento se aplica en % o en el monto relativo al mismo, por ejemplo: \n'
                                                  'a)12% disminuiria el 12% del monto \n'
                                                  'b)12 disminuiria 12 dolares al monto.'),
        # 'percent': fields.function(_percent_line, string='Porciento', digits_compute= dp.get_precision('Account')),
        'percent': fields.float('Porciento')
    }

    # def onchange_discount(self, cr, uid, ids, discount, price_subtotal, context=None):
    #     res = {'value': {}}
    #     if discount and discount != '0':
    #         if '.' in discount:
    #             res['warning'] = {'title': _('Error!!'), 'message': 'Formato equivocado'}
    #             res['value'] = {'discount': False}
    #             # raise osv.except_osv('Error!!', 'Formato equivocado')
    #         if discount:
    #             self.calculate_discount(discount, 0)
    #     return res
    #
    # def calculate_discount(self, discount, price_subtotal):
    #     percent = 0.00
    #     if ',' in discount:
    #         discount = convert_couma_to_point(discount)
    #     if is_float(discount):
    #         percent = float(discount) *100/price_subtotal if price_subtotal > 0 else 0.00
    #         return float(discount), percent
    #     else:
    #         if '%' in discount:
    #             index = discount.index('%')
    #             number = discount[0: index]
    #             amount = 0.00
    #             if not is_float(number):
    #                 raise osv.except_osv('Error!!', 'El valor no corresponde con el formato')
    #             amount = (price_subtotal*float(number)/100)
    #             percent = float(number)
    #         else:
    #             raise osv.except_osv('Error!!', 'El valor no corresponde con el formato')
    #     return amount, percent

    def onchange_product_id(self, cr, uid, ids, pricelist_id, product_id, qty, uom_id,
            partner_id, date_order=False, fiscal_position_id=False, date_planned=False,
            name=False, price_unit=False, state='draft', is_importation=False, context=None):
        """
        onchange handler of product_id.
        """
        print 'importacion es:', is_importation
        if context is None:
            context = {}

        res = {'value': {'price_unit': price_unit or 0.0, 'name': name or '', 'product_uom' : uom_id or False}}
        if not product_id:
            return res

        context = dict(context)
        context.update({'is_importation': is_importation})

        product_product = self.pool.get('product.product')
        product_uom = self.pool.get('product.uom')
        res_partner = self.pool.get('res.partner')
        product_pricelist = self.pool.get('product.pricelist')
        account_fiscal_position = self.pool.get('account.fiscal.position')
        account_tax = self.pool.get('account.tax')

        # - check for the presence of partner_id and pricelist_id
        #if not partner_id:
        #    raise osv.except_osv(_('No Partner!'), _('Select a partner in purchase order to choose a product.'))
        #if not pricelist_id:
        #    raise osv.except_osv(_('No Pricelist !'), _('Select a price list in the purchase order form before choosing a product.'))

        # - determine name and notes based on product in partner lang.
        context_partner = context.copy()
        if partner_id:
            lang = res_partner.browse(cr, uid, partner_id).lang
            context_partner.update( {'lang': lang, 'partner_id': partner_id} )
        product = product_product.browse(cr, uid, product_id, context=context_partner)
        #call name_get() with partner in the context to eventually match name and description in the seller_ids field
        if not name or not uom_id:
            # The 'or not uom_id' part of the above condition can be removed in master. See commit message of the rev. introducing this line.
            dummy, name = product_product.name_get(cr, uid, product_id, context=context_partner)[0]
            if product.description_purchase:
                name += '\n' + product.description_purchase
            res['value'].update({'name': name})

        # - set a domain on product_uom
        res['domain'] = {'product_uom': [('category_id','=',product.uom_id.category_id.id)]}

        # - check that uom and product uom belong to the same category
        product_uom_po_id = product.uom_po_id.id
        if not uom_id:
            uom_id = product_uom_po_id

        if product.uom_id.category_id.id != product_uom.browse(cr, uid, uom_id, context=context).category_id.id:
            if context.get('purchase_uom_check') and self._check_product_uom_group(cr, uid, context=context):
                res['warning'] = {'title': _('Warning!'), 'message': _('Selected Unit of Measure does not belong to the same category as the product Unit of Measure.')}
            uom_id = product_uom_po_id

        res['value'].update({'product_uom': uom_id})

        # - determine product_qty and date_planned based on seller info
        if not date_order:
            date_order = fields.datetime.now()


        supplierinfo = False
        precision = self.pool.get('decimal.precision').precision_get(cr, uid, 'Product Unit of Measure')
        for supplier in product.seller_ids:
            if partner_id and (supplier.name.id == partner_id):
                supplierinfo = supplier
                if supplierinfo.product_uom.id != uom_id:
                    res['warning'] = {'title': _('Warning!'), 'message': _('The selected supplier only sells this product by %s') % supplierinfo.product_uom.name }
                min_qty = product_uom._compute_qty(cr, uid, supplierinfo.product_uom.id, supplierinfo.min_qty, to_uom_id=uom_id)
                if float_compare(min_qty , qty, precision_digits=precision) == 1: # If the supplier quantity is greater than entered from user, set minimal.
                    if qty:
                        res['warning'] = {'title': _('Warning!'), 'message': _('The selected supplier has a minimal quantity set to %s %s, you should not purchase less.') % (supplierinfo.min_qty, supplierinfo.product_uom.name)}
                    qty = min_qty
        dt = self._get_date_planned(cr, uid, supplierinfo, date_order, context=context).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        qty = qty or 1.0
        res['value'].update({'date_planned': date_planned or dt})
        if qty:
            res['value'].update({'product_qty': qty})

        price = price_unit
        if price_unit is False or price_unit is None:
            # - determine price_unit and taxes_id
            if pricelist_id:
                date_order_str = datetime.strptime(date_order, DEFAULT_SERVER_DATETIME_FORMAT).strftime(DEFAULT_SERVER_DATE_FORMAT)
                price = product_pricelist.price_get(cr, uid, [pricelist_id],
                        product.id, qty or 1.0, partner_id or False, {'uom': uom_id, 'date': date_order_str})[pricelist_id]
            else:
                price = product.standard_price

        taxes_ids = False
        if not is_importation:
            taxes = account_tax.browse(cr, uid, map(lambda x: x.id, product.supplier_taxes_id))
            fpos = fiscal_position_id and account_fiscal_position.browse(cr, uid, fiscal_position_id, context=context) or False
            taxes_ids = account_fiscal_position.map_tax(cr, uid, fpos, taxes)
        res['value'].update({'price_unit': price, 'taxes_id': taxes_ids})

        return res

    def onchange_product_uom(self, cr, uid, ids, pricelist_id, product_id, qty, uom_id,
            partner_id, date_order=False, fiscal_position_id=False, date_planned=False,
            name=False, price_unit=False, state='draft', is_importation=False, context=None):
        """
        onchange handler of product_uom.
        """
        if context is None:
            context = {}
        if not uom_id:
            return {'value': {'price_unit': price_unit or 0.0, 'name': name or '', 'product_uom' : uom_id or False}}
        context = dict(context, purchase_uom_check=True)
        print 'el contexto es :', context
        return self.onchange_product_id(cr, uid, ids, pricelist_id, product_id, qty, uom_id,
            partner_id, date_order=date_order, fiscal_position_id=fiscal_position_id, date_planned=date_planned,
            name=name, price_unit=price_unit, state=state, is_importation=is_importation, context=context)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
