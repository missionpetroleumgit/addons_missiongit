from openerp.osv import fields, osv
from openerp import api
from openerp import tools
import openerp.addons.decimal_precision as dp
from openerp.exceptions import except_orm, Warning
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
from datetime import datetime
import time
import logging
import pdb


class purchase_order(osv.osv):
    _inherit = 'purchase.order'

    READONLY_STATES = {
        'confirmed': [('readonly', True)],
        'approved': [('readonly', True)],
        'done': [('readonly', True)]
    }

    def action_invoice_create(self, cr, uid, ids, context=None):
        """Generates invoice for given ids of purchase orders and links that invoice ID to purchase order.
        :param ids: list of ids of purchase orders.
        :return: ID of created invoice.
        :rtype: int
        """
        self.write(cr, uid, ids, {'invoice_created': True})
        return super(purchase_order, self).action_invoice_create(cr, uid, ids, context)

    def _get_order(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('purchase.order.line').browse(cr, uid, ids, context=context):
            result[line.order_id.id] = True
        return result.keys()

    def _amount_all(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        cur_obj=self.pool.get('res.currency')
        user = self.pool.get('res.users').browse(cr, uid, uid)
        for order in self.browse(cr, uid, ids, context=context):
            res[order.id] = {
                'amount_untaxed': 0.0,
                'amount_tax': 0.0,
                'amount_total': 0.0,
            }
            val = val1 = 0.0
            cur = user.company_id.currency_id
            if order.pricelist_id:
                cur = order.pricelist_id.currency_id
            for line in order.order_line:
                # Coloco el descuento en impuesto total DA
               if line.discount:
                   amount_discount = float(line.discount)/line.product_qty
               else:
                   amount_discount = 0.00
               val1 += line.price_subtotal
               for c in self.pool.get('account.tax').compute_all(cr, uid, line.taxes_id, line.price_unit - amount_discount, line.product_qty, line.product_id, order.partner_id)['taxes']:
                   val += c.get('amount', 0.0)
            res[order.id]['amount_tax']=cur_obj.round(cr, uid, cur, val)
            res[order.id]['amount_untaxed']=cur_obj.round(cr, uid, cur, val1)
            res[order.id]['amount_total']=res[order.id]['amount_untaxed'] + res[order.id]['amount_tax']
        return res

    STATE_SELECTION_APP = [
        ('except', 'Gerente General'),
        ('presupuesto', 'Financiero'),
        # ('area', 'Gerente de Area'),
        ('controller', 'Controller'),
        ('approved', 'Aprobada'),
        ('cancel', 'Cancelada')
    ]

    _columns = {
        'partner_id': fields.many2one('res.partner', 'Supplier', required=False, states=READONLY_STATES,
                                      change_default=True, track_visibility='always'),
        'pricelist_id': fields.many2one('product.pricelist', 'Pricelist', required=False,
                                       states=READONLY_STATES, help="The pricelist sets the currency used for this purchase order. It also computes the supplier price for the selected products/quantities."),
        'amount_untaxed': fields.function(_amount_all, digits=(16, 2), string='Untaxed Amount',
                                          multi="sums", help="The amount without tax", track_visibility='always'),
        'amount_tax': fields.function(_amount_all, digits=(16, 2), string='Taxes',
                                      multi="sums", help="The tax amount"),
        'amount_total': fields.function(_amount_all, digits=(16, 2), string='Total',
                                        multi="sums", help="The total amount"),
        'state_manager': fields.selection(STATE_SELECTION_APP, 'Aprobaciones', readonly=True,select=True),
        'control': fields.boolean('Aprobado por Controller'),
        'control_comment': fields.text('Comentario'),
        'is_send': fields.boolean('Enviado Aprobacion'),
        'number_req': fields.char('No. Requisicion'),
        'sale_order_id': fields.many2one('sale.order', 'Orden de Venta'),
        'customer_id': fields.many2one('res.partner', 'Cliente'),
        'not_apply': fields.boolean('No aplica'),
        'invoice_created': fields.boolean('factura creada'),
    }

    _defaults = {
        'pricelist_id': lambda self, cr, uid, context: context.get('partner_id', False) and self.pool.get('res.partner').browse(cr, uid, context['partner_id']).property_product_pricelist_purchase.id,
    }

    # Copio la funcion para generar el albaran cuando es producto o consumible, dejando solo cuando son productos DA
    def _create_stock_moves(self, cr, uid, order, order_lines, picking_id=False, context=None):
        """Creates appropriate stock moves for given order lines, whose can optionally create a
        picking if none is given or no suitable is found, then confirms the moves, makes them
        available, and confirms the pickings.

        If ``picking_id`` is provided, the stock moves will be added to it, otherwise a standard
        incoming picking will be created to wrap the stock moves (default behavior of the stock.move)

        Modules that wish to customize the procurements or partition the stock moves over
        multiple stock pickings may override this method and call ``super()`` with
        different subsets of ``order_lines`` and/or preset ``picking_id`` values.

        :param browse_record order: purchase order to which the order lines belong
        :param list(browse_record) order_lines: purchase order line records for which picking
                                                and moves should be created.
        :param int picking_id: optional ID of a stock picking to which the created stock moves
                               will be added. A new picking will be created if omitted.
        :return: None
        """
        stock_move = self.pool.get('stock.move')
        todo_moves = []
        new_group = self.pool.get("procurement.group").create(cr, uid, {'name': order.name, 'partner_id': order.partner_id.id}, context=context)

        for order_line in order_lines:
            if order_line.state == 'cancel':
                continue
            if not order_line.product_id:
                continue

            if order_line.product_id.type in ('product'):
                for vals in self._prepare_order_line_move(cr, uid, order, order_line, picking_id, new_group, context=context):
                    move = stock_move.create(cr, uid, vals, context=context)
                    todo_moves.append(move)

        todo_moves = stock_move.action_confirm(cr, uid, todo_moves)
        stock_move.force_assign(cr, uid, todo_moves)

    def wkf_bid_received(self, cr, uid, ids, context=None):
        user = self.pool.get('res.users').browse(cr, uid, uid)
        for ctl in self.browse(cr, uid, ids, context=context):
            #if ctl.app_user_id.id != uid:
            #    raise osv.except_orm('Error!', 'Usted no esta autorizado a aprobar este documento')
            total_amount = 0
            for quotes in ctl.quotes_ids:
                if quotes.state == 'done':
                    total_amount += quotes.amount_total

            if total_amount < user.company_id.max_amount:
                return self.write(cr, uid, ids, {'state': 'bid', 'bid_date': fields.date.context_today(self,cr,uid,context=context),
                                                 'state_manager': 'approved'})
            else:
                return self.write(cr, uid, ids, {'state': 'bid', 'bid_date': fields.date.context_today(self,cr,uid,context=context),
                                                 'state_manager': 'except'})

    def wkf_confirm_order(self, cr, uid, ids, context=None):
        for po in self.browse(cr, uid, ids, context=context):
            if po.state_manager == 'except':
                raise osv.except_orm('Error!', 'La Requisicion numero %s requiere aprobacion de gerencia' % po.name)
        return super(purchase_order, self).wkf_confirm_order(cr, uid, ids, context)

    def manager_approved(self, cr, uid, ids, context=None):
        for po in self.browse(cr, uid, ids, context=context):

            val = {

                'tracing_id': [(0, 0, {
                    'purchase_order_id': po.id,
                    'user_id': po.env.user.id,
                    'date_tracing': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'state': 'approved_ger'
                })]
            }
            po.write(val)
            res = super(purchase_order, self).wkf_bid_received(cr, uid, ids, context)
            self.write(cr, uid, ids, {'state_manager': 'presupuesto'})

    def action_cancel_draft(self, cr, uid, ids, context=None):
        for order in self.browse(cr, uid, ids, context):
            for quote in order.quotes_ids:
                self.pool.get('purchase.quotes').write(cr, uid, [quote.id], {'state': 'draft'})
                for line in quote.quotes_lines:
                    self.pool.get('quotes.line').write(cr, uid, [line.id], {'state': 'draft'})
        self.write(cr, uid, ids, {'state_manager': False,
                                  'is_approve_quotes': False, 'control': False, 'control_comment':False})
        return super(purchase_order, self).action_cancel_draft(cr, uid, ids, context)

    def wkf_action_cancel(self, cr, uid, ids, context=None):
        todo = []
        for po in self.browse(cr, uid, ids, context=context):
            for line in po.order_line:
                todo.append(line.id)
        if todo:
            self.pool.get('purchase.order.line').unlink(cr, uid, todo)
        self.write(cr, uid, ids, {'state': 'cancel', 'state_manager': 'cancel'}, context=context)
        self.set_order_line_status(cr, uid, ids, 'cancel', context=context)

    def action_area_manager(self, cr, uid, ids, context=None):
        for rec in self.browse(cr, uid, ids, context):
            if rec.app_user_id.id != uid:
                raise osv.except_orm('Error!', 'Usted no esta autorizado a aprobar este documento')
        return self.write(cr, uid, ids, {'state_manager': 'except'})

    def purchase_finances(self, cr, uid, ids, context=None):
        valida = 0
        for rec in self.browse(cr,uid,ids,context):
            val = {

                'tracing_id': [(0, 0, {
                    'purchase_order_id': rec.id,
                    'user_id': rec.env.user.id,
                    'date_tracing': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'state': 'control'
                })]
            }
            rec.write(val)
            for quote in rec.quotes_ids:
                if not quote:
                    raise except_orm('Error!', 'Debe definir al menos una cotizacion')
                if quote.state == 'done':
                    valida = 1
        if valida == 0:
            raise osv.except_orm('Alerta!', 'Debe aprobar al menos una cotizacion')

        return self.write(cr, uid, ids, {'state_manager': 'presupuesto'})

    def purchase_cancel_to_order(self, cr, uid, ids, context=None):
        for rec in self.browse(cr,uid,ids,context):
            val = {

                'tracing_id': [(0, 0, {
                    'purchase_order_id': rec.id,
                    'user_id': rec.env.user.id,
                    'date_tracing': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'state': 'purchase'
                })]
            }
            rec.write(val)
            rec.write({'is_approve_quotes':False,'cancel_controller':True})
            rec.wkf_send_rfq()

        return True

    def _prepare_inv_line(self, cr, uid, account_id, order_line, context=None):
        """Collects require data from purchase order line that is used to create invoice line
        for that purchase order line
        :param account_id: Expense account of the product of PO line if any.
        :param browse_record order_line: Purchase order line browse record
        :return: Value for fields of invoice lines.
        :rtype: dict
        """
        taxes = []
        fiscal = False
        for tax in order_line.taxes_id:
            tax_to_add = tax.id
            if tax.description in ('1', '2'):
                fp = self.pool.get('account.fiscal.position.tax')
                if order_line.partner_id.property_account_position:
                    fiscal = fp.search(cr, uid, [('position_id', '=', order_line.partner_id.property_account_position.id),
                                                 ('tax_src_id.description', '=', tax.description)])
                if not fiscal and order_line.partner_id.property_account_position:
                    raise osv.except_orm('Error!', 'Configure la posicion fiscal del proveedor')
                if fiscal:
                    fiscal = fp.browse(cr, uid, fiscal[0])
                    tax_to_add = fiscal.tax_dest_id.id
                else:
                    continue
            taxes.append(tax_to_add)

        return {
            'name': order_line.name,
            'account_id': account_id,
            'price_unit': order_line.price_unit or 0.0,
            'quantity': order_line.product_qty,
            'product_id': order_line.product_id.id or False,
            'uos_id': order_line.product_uom.id or False,
            'invoice_line_tax_id': [(6, 0, taxes)],
            'account_analytic_id': order_line.account_analytic_id.id or False,
            'purchase_line_id': order_line.id,
        }

    @api.multi
    def send_approved(self):
        if len(self.request_products) == 0:
            raise except_orm('Error!', 'No existen lineas de pedido')
        if self.is_procura:
            if len(self.quotes_ids) == 0:
                raise except_orm('Error!', 'Debe ingresar la cotizacion correspondiente')

            validate = 0
            for quotes in self.quotes_ids:
                if not quotes.attachment_ids and quotes.state != 'cancel':
                    raise except_orm('Error!', 'Por favor adjunte el/los documentos necesarios al documento %s' % quotes.name)
                if quotes.state == 'done':
                    validate += 1
            if validate < 1:
                raise except_orm('Error!',
                                 'Por favor, debe aprobar una o mas cotizaciones para proceder con la compra')
        return self.write({'is_send': 'True'})

purchase_order()


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

    _columns = {
        'price_subtotal': fields.function(_amount_line, string='Subtotal', digits_compute= dp.get_precision('Account')),
        'number': fields.char('No. parte'),
        'price_unit': fields.float('Precio unitario', required=True, digits_compute= dp.get_precision('Product Price')),
        'line_sequence': fields.char('Secuencia', readonly=True)
    }

purchase_order_line()


class res_company_amount(osv.osv):
    _name = 'res.company'
    _inherit = 'res.company'

    def _get_image(self, cr, uid, ids, name, args, context=None):
        result = dict.fromkeys(ids, False)
        for obj in self.browse(cr, uid, ids, context=context):
            result[obj.id] = tools.image_get_resized_images(obj.manager_sig)
        return result

    def _set_image(self, cr, uid, id, name, value, args, context=None):
        return self.write(cr, uid, [id], {'manager_sig': tools.image_resize_image_big(value)}, context=context)

    def _get_image_op(self, cr, uid, ids, name, args, context=None):
        result = dict.fromkeys(ids, False)
        for obj in self.browse(cr, uid, ids, context=context):
            result[obj.id] = tools.image_get_resized_images(obj.op_manager_sig)
        return result

    def _get_image_imp(self, cr, uid, ids, name, args, context=None):
        result = dict.fromkeys(ids, False)
        for obj in self.browse(cr, uid, ids, context=context):
            result[obj.id] = tools.image_get_resized_images(obj.importation_sig)
        return result

    def _set_image_imp(self, cr, uid, id, name, value, args, context=None):
        return self.write(cr, uid, [id], {'importation_sig': tools.image_resize_image_big(value)}, context=context)

    def _get_image_po2(self, cr, uid, ids, name, args, context=None):
        result = dict.fromkeys(ids, False)
        for obj in self.browse(cr, uid, ids, context=context):
            result[obj.id] = tools.image_get_resized_images(obj.purchase_sig2)
        return result

    def _set_image_po2(self, cr, uid, id, name, value, args, context=None):
        return self.write(cr, uid, [id], {'purchase_sig2': tools.image_resize_image_big(value)}, context=context)

    def _set_image_op(self, cr, uid, id, name, value, args, context=None):
        return self.write(cr, uid, [id], {'op_manager_sig': tools.image_resize_image_big(value)}, context=context)

    def _get_image_po(self, cr, uid, ids, name, args, context=None):
        result = dict.fromkeys(ids, False)
        for obj in self.browse(cr, uid, ids, context=context):
            result[obj.id] = tools.image_get_resized_images(obj.purchase_sig)
        return result

    def _set_image_po(self, cr, uid, id, name, value, args, context=None):
        return self.write(cr, uid, [id], {'purchase_sig': tools.image_resize_image_big(value)}, context=context)

    def _get_image_oper2(self, cr, uid, ids, name, args, context=None):
        result = dict.fromkeys(ids, False)
        for obj in self.browse(cr, uid, ids, context=context):
            result[obj.id] = tools.image_get_resized_images(obj.sec_operation_sig)
        return result

    def _set_image_oper2(self, cr, uid, id, name, value, args, context=None):
        return self.write(cr, uid, [id], {'sec_operation_sig': tools.image_resize_image_big(value)}, context=context)

    _columns = {
        'max_amount': fields.float('Valor maximo compras'),
        'manager_sig': fields.binary("Firma Gerente"),
        'image_m': fields.function(_get_image, fnct_inv=_set_image,
                                        string="Medium-sized photo", type="binary", multi="_get_image",
                                        store={
                                            'res.company': (lambda self, cr, uid, ids, c={}: ids, ['manager_sig'], 10),
                                        },
                                        help="Medium-sized photo of the employee. It is automatically " \
                                             "resized as a 128x128px image, with aspect ratio preserved. " \
                                             "Use this field in form views or some kanban views."),
        'image_s': fields.function(_get_image, fnct_inv=_set_image,
                                       string="Small-sized photo", type="binary", multi="_get_image",
                                       store={
                                           'res.company': (lambda self, cr, uid, ids, c={}: ids, ['manager_sig'], 10),
                                       },
                                       help="Small-sized photo of the employee. It is automatically " \
                                            "resized as a 64x64px image, with aspect ratio preserved. " \
                                            "Use this field anywhere a small image is required."),

        'op_manager_sig': fields.binary("Firma Operaciones"),
        'image_op': fields.function(_get_image_op, fnct_inv=_set_image_op,
                                   string="Medium-sized photo", type="binary", multi="_get_image_op",
                                   store={
                                       'res.company': (lambda self, cr, uid, ids, c={}: ids, ['op_manager_sig'], 10),
                                   },
                                   help="Medium-sized photo of the employee. It is automatically " \
                                        "resized as a 128x128px image, with aspect ratio preserved. " \
                                        "Use this field in form views or some kanban views."),
        'image_op2': fields.function(_get_image_op, fnct_inv=_set_image_op,
                                   string="Small-sized photo", type="binary", multi="_get_image_op",
                                   store={
                                       'res.company': (lambda self, cr, uid, ids, c={}: ids, ['op_manager_sig'], 10),
                                   },
                                   help="Small-sized photo of the employee. It is automatically " \
                                        "resized as a 64x64px image, with aspect ratio preserved. " \
                                        "Use this field anywhere a small image is required."),

        'purchase_sig': fields.binary("Firma Compras"),
        'image_p': fields.function(_get_image_po, fnct_inv=_set_image_po,
                                   string="Medium-sized photo", type="binary", multi="_get_image_po",
                                   store={
                                       'res.company': (lambda self, cr, uid, ids, c={}: ids, ['purchase_sig'], 10),
                                   },
                                   help="Medium-sized photo of the employee. It is automatically " \
                                        "resized as a 128x128px image, with aspect ratio preserved. " \
                                        "Use this field in form views or some kanban views."),
        'image_p2': fields.function(_get_image_po, fnct_inv=_set_image_po,
                                   string="Small-sized photo", type="binary", multi="_get_image_po",
                                   store={
                                       'res.company': (lambda self, cr, uid, ids, c={}: ids, ['purchase_sig'], 10),
                                   },
                                   help="Small-sized photo of the employee. It is automatically " \
                                        "resized as a 64x64px image, with aspect ratio preserved. " \
                                        "Use this field anywhere a small image is required."),

        'purchase_sig2': fields.binary("Firma Compras 2"),
        'image_ap': fields.function(_get_image_po2, fnct_inv=_set_image_po2,
                                   string="Medium-sized photo", type="binary", multi="_get_image_po2",
                                   store={
                                       'res.company': (lambda self, cr, uid, ids, c={}: ids, ['purchase_sig2'], 10),
                                   },
                                   help="Medium-sized photo of the employee. It is automatically " \
                                        "resized as a 128x128px image, with aspect ratio preserved. " \
                                        "Use this field in form views or some kanban views."),
        'image_ap2': fields.function(_get_image_po2, fnct_inv=_set_image_po2,
                                   string="Small-sized photo", type="binary", multi="_get_image_po2",
                                   store={
                                       'res.company': (lambda self, cr, uid, ids, c={}: ids, ['purchase_sig2'], 10),
                                   },
                                   help="Small-sized photo of the employee. It is automatically " \
                                        "resized as a 64x64px image, with aspect ratio preserved. " \
                                        "Use this field anywhere a small image is required."),

        'importation_sig': fields.binary("Firma Importaciones"),
        'image_po': fields.function(_get_image_imp, fnct_inv=_set_image_imp,
                                     string="Medium-sized photo", type="binary", multi="_get_image_imp",
                                     store={
                                         'res.company': (lambda self, cr, uid, ids, c={}: ids, ['importation_sig'], 10),
                                     },
                                     help="Medium-sized photo of the employee. It is automatically " \
                                          "resized as a 128x128px image, with aspect ratio preserved. " \
                                          "Use this field in form views or some kanban views."),
        'image_po2': fields.function(_get_image_imp, fnct_inv=_set_image_imp,
                                     string="Small-sized photo", type="binary", multi="_get_image_imp",
                                     store={
                                         'res.company': (lambda self, cr, uid, ids, c={}: ids, ['importation_sig'], 10),
                                     },
                                     help="Small-sized photo of the employee. It is automatically " \
                                          "resized as a 64x64px image, with aspect ratio preserved. " \
                                          "Use this field anywhere a small image is required."),

        'sec_operation_sig': fields.binary("Firma Operaciones 2"),
        'image_med': fields.function(_get_image_oper2, fnct_inv=_set_image_oper2,
                                   string="Medium-sized photo", type="binary", multi="_get_image_oper2",
                                   store={
                                       'res.company': (lambda self, cr, uid, ids, c={}: ids, ['sec_operation_sig'], 10),
                                   },
                                   help="Medium-sized photo of the employee. It is automatically " \
                                        "resized as a 128x128px image, with aspect ratio preserved. " \
                                        "Use this field in form views or some kanban views."),
        'image_sml': fields.function(_get_image_oper2, fnct_inv=_set_image_oper2,
                                   string="Small-sized photo", type="binary", multi="_get_image_oper2",
                                   store={
                                       'res.company': (lambda self, cr, uid, ids, c={}: ids, ['sec_operation_sig'], 10),
                                   },
                                   help="Small-sized photo of the employee. It is automatically " \
                                        "resized as a 64x64px image, with aspect ratio preserved. " \
                                        "Use this field anywhere a small image is required."),
    }


res_company_amount()

