# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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

from openerp import SUPERUSER_ID
from openerp.osv import fields, osv
from openerp.tools import float_is_zero
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
from openerp.report import report_sxw
from openerp.tools import float_compare, float_round

import time

class account_caja_chica(osv.osv):

    _order = "date desc, id desc"
    _name = "account.caja.chica"
    _description = "Caja Chica"
#    _inherit = ['mail.thread']

    def _get_default_company(self, cr, uid, context=None):
        company_id = self.pool.get('res.users')._get_company(cr, uid, context=context)
        if not company_id:
            raise osv.except_osv(_('Error!'), _('There is no default company for the current user!'))
        return company_id

    _columns = {
        'name': fields.char(
            'Referencia', states={'draft': [('readonly', False)]},
            readonly=True, # readonly for account_cash_statement
            copy=False,
            help='if you give the Name other then /, its created Accounting Entries Move '
                 'will be with same name as statement name. '
                 'This allows the statement entries to have the same references than the '
                 'statement itself'),
        'date': fields.date('Fecha Caja', required=True, states={'confirm': [('readonly', True)]},
                            select=True, copy=False),
        'date_cierre': fields.date('Fecha Cierre', states={'draft': [('readonly', True)]},
                            select=True, copy=False),
        'user_id': fields.many2one('res.users', 'Responsable', states={'draft': [('readonly', False)], 'open': [('readonly', False)]}, select=True, track_visibility='onchange'),
        'saldo_ini': fields.float('Saldo Inicial', digits_compute=dp.get_precision('Account'),
            states={'confirm':[('readonly',True)]}),
        'saldo_pend': fields.float('Saldo Pendiente', digits_compute=dp.get_precision('Account'),
            states={'confirm':[('readonly',True)]}),
        'valor_bruto': fields.float('Valor Bruto', digits_compute=dp.get_precision('Account'),
            states={'confirm':[('readonly',True)]}),
        'valor_neto': fields.float('Neto Pagar', digits_compute=dp.get_precision('Account'),
            states={'confirm':[('readonly',True)]}),
        'valor_iva': fields.float('Valor Iva', digits_compute=dp.get_precision('Account'),
            states={'confirm':[('readonly',True)]}),
        'valor_bruto_f': fields.float('Valor Bruto F', digits_compute=dp.get_precision('Account'),
            states={'confirm':[('readonly',True)]}),
        'valor_neto_f': fields.float('Neto Pagar F', digits_compute=dp.get_precision('Account'),
            states={'confirm':[('readonly',True)]}),
        'valor_iva_f': fields.float('Valor Iva F', digits_compute=dp.get_precision('Account'),
            states={'confirm':[('readonly',True)]}),
        'company_id': fields.related('company_id', type='many2one', relation='res.company', string='Compañia', store=True, readonly=True),
        #'company_id': fields.many2one('res.company', 'Company'),
        'line_ids': fields.one2many('account.caja.chica.line',
                                    'caja_chica_id', 'Caja chica lines',
                                    states={'confirm':[('readonly', True)]}, copy=True),
        'state': fields.selection([('draft', 'New'),
                                   ('open','Open'), # CSV:2016-04-21 used by cash statements
                                   ('pending','Pendiente'), # CSV:2016-04-21 used by pay partial
                                   ('confirm', 'Closed')],
                                   'Status', required=True, readonly="1",
                                   copy=False,
                                   help='When new statement is created the status will be \'Draft\'.\n'
                                        'And after getting confirmation from the bank it will be in \'Confirmed\' status.'),
    }

    _defaults = {
        'name': 'Caja Chica/',
        'date': fields.date.context_today,
        'state': 'draft',
        #'company_id': _get_default_company,
        'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'account.caja.chica',context=c),
        'user_id': lambda obj, cr, uid, context: uid,
    }

    def cerrar_caja(self, cr, uid, ids, context=None):
        lis_rec = []
        band = 0
        obj_caja = self.browse(cr, uid, ids)[0]
        self.write(cr, uid, ids, {'state':'pending'})
        #Creo un registro de caja nuevo con el saldo pendiente como inicial para la nueva caja
        data = {
                    'name': obj_caja.name,
                    'user_id': obj_caja.user_id.id,
                    'date': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'company_id': obj_caja.company_id.id,
                    'saldo_ini': obj_caja.saldo_pend,
                    'state':'draft',
        }
        self.create(cr, uid, data, context)
        return True

    def validar_caja(self, cr, uid, ids, context=None):
        band = 0
        lis_rec = []
        invoice_id = False
        obj_caja = self.browse(cr, uid, ids)[0]
        self.write(cr, uid, ids, {'state':'confirm', 'date_cierre':time.strftime('%Y-%m-%d %H:%M:%S')})
        inv_obj = self.pool.get('account.invoice')
        acc_jour_obj = self.pool.get('account.journal')
        inv_line_obj = self.pool.get('account.invoice.line')
        cchica_lin_obj = self.pool.get('account.caja.chica.line')
        cchica_line_ids = cchica_lin_obj.search(cr, uid, [('caja_chica_id', '=', obj_caja.id)], order='id, number_fact')
        stat_conc_line_obj =  cchica_lin_obj.browse(cr, uid, cchica_line_ids, context=context)
        # JJM 2018-02-15 utilizo el superuser_id por que se necesita validar cajas chicas de otras companias
        # evito regla de registro para account_journal sobre company_id
        journal_id = acc_jour_obj.search(cr, SUPERUSER_ID, [('code', '=', 'DCC'), ('company_id', '=', obj_caja.company_id.id)])
        if not journal_id:
            raise osv.except_osv(_('Advertencia!'), _('Primero debe crear un diario de caja chica para esta compania con codigo DCC!'))
        journal_obj = acc_jour_obj.browse(cr, uid, journal_id, context=context)
        for ji in journal_obj:
            id_journal = ji.id
        num_comp = ''
        for det_cc in stat_conc_line_obj:
            #CONDICION SI ES COMPROBANTE TIPO FACTURA
            #print "LINEAS ID", det_cc.id
            #print "LINEAS", det_cc.product_id.name
            # JJM 2017-01-28 comento siguiente linea, ahora tomo cuenta desde la compañia
            #account_id = self.pool.get('multi.account.partner.rel').search(cr, uid, [('partner_id', '=', det_cc.partner_id.id),
            #                                                                         ('type', '=', 'payable'),
            #                                                                         ('company_id', '=', det_cc.company_id.id)])
            if not det_cc.partner_id:
                raise osv.except_orm('Advertencia!', 'Debe ingresar un proveedor para la linea de %s' % (det_cc.name))
            if len(det_cc.company_id.payable_ids) == 0:
                raise osv.except_orm('Advertencia!', 'La compania %s no tiene configurada la cuenta a pagar Proveedores' % det_cc.company_id.name)
            # JJM ahora tomo la cuenta desde la compañia en lugar del multi.account
            account_id = det_cc.company_id.payable_ids[0].id
            #account_id = self.pool.get('multi.account.partner.rel').browse(cr, uid, account_id[0]).property_account.id
            if not det_cc.sudo(det_cc.user_id).product_id.property_account_expense:
                raise osv.except_orm('Advertencia!', 'No tiene configurada la cuenta de gastos para el producto %s' % (det_cc.product_id.name))
            if det_cc.cantidad <= 0:
                raise osv.except_orm('Advertencia!', 'la cantidad del producto %s no puede ser cero' % (
                det_cc.product_id.name))

            if det_cc.tipo_comp == 'factura':
            #CREO REGISTRO NUEVO SOLO SI ES COMPROBANTE DIFERENTE
                if det_cc.tipo_comp == 'factura' and det_cc.number_fact != num_comp:
                    num_comp = det_cc.number_fact
                #Creo cabecera Factura
                    vals_invoice = {
                          'name': 'CCHICA'+'-'+time.strftime('%Y-%m-%d %H:%M:%S'),
                          'journal_id': id_journal,
                          'number_seq': det_cc.number_fact,
                          'account_id': account_id,
                          'partner_id': det_cc.partner_id.id,
                          'company_id' : det_cc.company_id.id,
                          'reference': det_cc.name,
                          'type': 'in_invoice',
                          'document_type': 1,
                          'is_cchica': True,
                          'is_asum': True,
                          'is_inv_elect': False,
                          'date_invoice': time.strftime('%Y-%m-%d %H:%M:%S'),
                          'origin': 'CCHICA'+'-'+time.strftime('%Y-%m-%d %H:%M:%S'),
                          'state': 'draft'}
                    print "DICCIO FACT", vals_invoice
                    invoice_id = inv_obj.create(cr, uid, vals_invoice, context=context)
                    #Creo detalle Factura
                    if invoice_id:
                        vals_det_invoice = {
                            'name': 'CCHICA'+'-'+time.strftime('%Y-%m-%d %H:%M:%S'),
                            'invoice_id': invoice_id,
                            'company_id': det_cc.company_id.id,
                            'partner_id': det_cc.partner_id.id,
                            'product_id': det_cc.product_id.id,
                            'quantity': det_cc.cantidad,
                            'account_id': det_cc.sudo(det_cc.user_id).product_id.property_account_expense.id,
                            'price_unit': round(det_cc.amount_neto/det_cc.cantidad,2),
                            'price_subtotal': round(det_cc.amount_neto/det_cc.cantidad,2),
                            'origin': 'CCHICA'+'-'+time.strftime('%Y-%m-%d %H:%M:%S'),
                        }
                        invoice_line_id = inv_line_obj.create(cr, uid, vals_det_invoice)
                # CREO UNA LINEA MAS NADA MAS PORQUE ES DE LA MISMA FACTURA
                elif det_cc.tipo_comp == 'factura' and det_cc.number_fact == num_comp:
                    num_comp = det_cc.number_fact
                    #Creo detalle Factura
                    if invoice_id:
                        vals_det_invoice = {
                            'name': 'CCHICA'+'-'+time.strftime('%Y-%m-%d %H:%M:%S'),
                            'invoice_id': invoice_id,
                            'company_id': det_cc.company_id.id,
                            'partner_id': det_cc.partner_id.id,
                            'product_id': det_cc.product_id.id,
                            'quantity': det_cc.cantidad,
                            'account_id': det_cc.sudo(det_cc.user_id).product_id.property_account_expense.id,
                            'price_unit': round(det_cc.amount_neto/det_cc.cantidad,2),
                            'price_subtotal': round(det_cc.amount_neto/det_cc.cantidad,2),
                            'origin': 'CCHICA'+'-'+time.strftime('%Y-%m-%d %H:%M:%S'),
                        }
                        invoice_line_id = inv_line_obj.create(cr, uid, vals_det_invoice)
            #CONDICION SI ES COMPROBANTE TIPO NOTA VENTA
            elif det_cc.tipo_comp == 'nventa':
            #CREO REGISTRO NUEVO SOLO SI ES COMPROBANTE DIFERENTE
                if det_cc.tipo_comp == 'nventa' and det_cc.number_fact != num_comp:
                    num_comp = det_cc.number_fact
                #Creo cabecera COMPROBANTE TIPO NOTA VENTA
                    vals_invoice = {
                          'name': 'CCHICA'+'-'+time.strftime('%Y-%m-%d %H:%M:%S'),
                          'journal_id': id_journal,
                          'number_seq': det_cc.number_fact,
                          'account_id': account_id,
                          'partner_id': det_cc.partner_id.id,
                          'company_id' : det_cc.company_id.id,
                          'reference': det_cc.name,
                          'type': 'in_invoice',
                          'document_type': 2,
                          'is_cchica': True,
                          'is_asum': True,
                          'is_inv_elect': False,
                          'date_invoice': time.strftime('%Y-%m-%d %H:%M:%S'),
                          'origin': 'CCHICA'+'-'+time.strftime('%Y-%m-%d %H:%M:%S'),
                          'state': 'draft'}
                    invoice_id = inv_obj.create(cr, uid, vals_invoice, context=context)
                    #Creo detalle COMPROBANTE TIPO NOTA VENTA
                    if invoice_id:
                        vals_det_invoice = {
                            'name': 'CCHICA'+'-'+time.strftime('%Y-%m-%d %H:%M:%S'),
                            'invoice_id': invoice_id,
                            'company_id': det_cc.company_id.id,
                            'partner_id': det_cc.partner_id.id,
                            'product_id': det_cc.product_id.id,
                            'quantity': det_cc.cantidad,
                            'account_id': det_cc.sudo(det_cc.user_id).product_id.property_account_expense.id,
                            'price_unit': round(det_cc.amount_neto/det_cc.cantidad,2),
                            'price_subtotal': round(det_cc.amount_neto/det_cc.cantidad,2),
                            'origin': 'CCHICA'+'-'+time.strftime('%Y-%m-%d %H:%M:%S'),
                        }
                        invoice_line_id = inv_line_obj.create(cr, uid, vals_det_invoice)
                # CREO UNA LINEA MAS NADA MAS PORQUE ES DE LA MISMO COMPROBANTE TIPO NOTA VENTA
                elif det_cc.tipo_comp == 'nventa' and det_cc.number_fact == num_comp:
                    num_comp = det_cc.number_fact
                    #Creo detalle COMPROBANTE TIPO NOTA VENTA
                    if invoice_id:
                        vals_det_invoice = {
                            'name': 'CCHICA'+'-'+time.strftime('%Y-%m-%d %H:%M:%S'),
                            'invoice_id': invoice_id,
                            'company_id': det_cc.company_id.id,
                            'partner_id': det_cc.partner_id.id,
                            'product_id': det_cc.product_id.id,
                            'quantity': det_cc.cantidad,
                            'account_id': det_cc.sudo(det_cc.user_id).product_id.property_account_expense.id,
                            'price_unit': round(det_cc.amount_neto/det_cc.cantidad,2),
                            'price_subtotal': round(det_cc.amount_neto/det_cc.cantidad,2),
                            'origin': 'CCHICA'+'-'+time.strftime('%Y-%m-%d %H:%M:%S'),
                        }
                        invoice_line_id = inv_line_obj.create(cr, uid, vals_det_invoice)
            else:
                vals_recibo = {
                    'name': 'CCHICA'+'-'+time.strftime('%Y-%m-%d %H:%M:%S'),
                    'journal_id': id_journal,
                    'account_id': account_id,
                    'partner_id': det_cc.partner_id.id,
                    'company_id' : det_cc.company_id.id,
                    'reference': det_cc.name,
                    'date_invoice': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'origin': 'CCHICA'+'-'+time.strftime('%Y-%m-%d %H:%M:%S'),
                    'product_id': det_cc.product_id.id,
                    'quantity': det_cc.cantidad,
                    'account_line_id': det_cc.sudo(det_cc.user_id).product_id.property_account_expense.id,
                    'price_unit': round(det_cc.amount_neto/det_cc.cantidad,2),
                    'price_subtotal': round(det_cc.amount_neto/det_cc.cantidad,2)
                }
                lis_rec.append(vals_recibo)
                band = 1
        if band == 1:
            band1 = 0
            for inv_rec in lis_rec:
                #Creo cabecera Factura
                if band1 == 0:
                    vals_invoice = {
                          'name': inv_rec.get('name'),
                          #'journal_id': det_cc.journal_id.id,
                          'account_id': inv_rec.get('account_id'),
                          'partner_id': inv_rec.get('partner_id'),
                          'company_id' : inv_rec.get('company_id'),
                          'reference': inv_rec.get('reference'),
                          'type': 'in_invoice',
                          'document_type': 3,
                          'is_cchica': True,
                          'is_asum': True,
                          'is_inv_elect': False,
                          'date_invoice': inv_rec.get('date_invoice'),
                          'origin': inv_rec.get('origin'),
                          'state': 'draft'}
                    invoice_idr = inv_obj.create(cr, uid, vals_invoice, context=context)
                    band1 = 1
                #Creo detalle Factura
                if invoice_idr:
                    vals_det_invoice = {
                        'name': inv_rec.get('name'),
                        'invoice_id': invoice_idr,
                        'company_id': inv_rec.get('company_id'),
                        'partner_id': inv_rec.get('partner_id'),
                        'product_id': inv_rec.get('product_id'),
                        'quantity': inv_rec.get('quantity'),
                        'account_id': inv_rec.get('account_line_id'),
                        'price_unit': inv_rec.get('price_unit'),
                        'price_subtotal': inv_rec.get('price_subtotal'),
                        'origin': inv_rec.get('origin'),
                    }
                    invoice_line_id = inv_line_obj.create(cr, uid, vals_det_invoice)

        return True

    def new_ingreso(self, cr, uid, ids, context=None):
        lis_rec = []
        band = 0
        obj_caja = self.browse(cr, uid, ids)[0]
        stock_ware = self.pool.get('stock.picking.type')
        picking_obj = self.pool.get('stock.picking')
        move_obj = self.pool.get('stock.move')
        cchica_lin_obj = self.pool.get('account.caja.chica.line')
        cchica_line_ids = cchica_lin_obj.search(cr, uid, [('caja_chica_id', '=', obj_caja.id)])
        stat_conc_line_obj =  cchica_lin_obj.browse(cr, uid, cchica_line_ids, context=context)
        band = 0
        for det_cc in stat_conc_line_obj:
            #CONDICION SI ES INVENTARIO PARA PROCESAR
            print "IS INVENT", det_cc.is_inven
            print "STATE", det_cc.state
            if det_cc.is_inven and det_cc.state == 'open':
                if det_cc.product_id.type in ('product', 'consu'):
                    print "PROCESO INVENTARIO Y CONFIRMO LINEA MARCADA", det_cc.id
                    vals_lcchica = {'state' : 'confirm'}
                    cchica_lin_obj.write(cr,uid,det_cc.id,vals_lcchica)
                    pic_type_id = stock_ware.search(cr, uid, [('code', '=', 'incoming'), ('warehouse_id.company_id', '=', det_cc.user_id.company_id.id), ('name', '=', 'Recepciones')])
                    print "ID PIC TYPE", pic_type_id
                    if not pic_type_id:
                        raise osv.except_osv(_('Advertencia!'), _('Primero debe crear un tipo de albarran recepción para la compania de la operación!'))
                    pic_type_obj =  stock_ware.browse(cr, uid, pic_type_id, context=context)
                    for sw in pic_type_obj:
                        id_pt = sw.id
                        wareh_id = sw.warehouse_id.id
                        ub_origen = sw.default_location_src_id.id
                        ub_destino = sw.default_location_dest_id.id
                    if band == 0:
                        picking_vals = {
                            'picking_type_id': id_pt,
                            'partner_id': det_cc.partner_id.id,
                            'date': time.strftime('%Y-%m-%d %H:%M:%S'),
                            'origin': 'CCHICA'+'-'+time.strftime('%Y-%m-%d %H:%M:%S') or ''
                        }
                        picking_id = picking_obj.create(cr, uid, picking_vals, context=context)
                        band = 1
                    if picking_id:
                        vals_stock_move = {
                            'name': 'CCHICA'+'-'+time.strftime('%Y-%m-%d %H:%M:%S') or '',
                            'product_id': det_cc.product_id.id,
                            'product_uom': det_cc.product_id.uom_id.id,
                            'product_uos': det_cc.product_id.uos_id.id,
                            'date': time.strftime('%Y-%m-%d %H:%M:%S'),
                            'date_expected': time.strftime('%Y-%m-%d %H:%M:%S'),
                            'location_id': ub_origen,
                            'location_dest_id': ub_destino,
                            'picking_id': picking_id,
                            'partner_id': det_cc.partner_id.id,
                            'move_dest_id': False,
                            'state': 'draft',
                            #'purchase_line_id': order_line.id,
                            'company_id': det_cc.user_id.company_id.id,
                            'product_uom_qty': det_cc.cantidad,
                            'price_unit': round(det_cc.amount_neto/det_cc.cantidad,2),
                            'picking_type_id': id_pt,
                            #'group_id': group_id,
                            'procurement_id': False,
                            'origin': 'CCHICA'+'-'+time.strftime('%Y-%m-%d %H:%M:%S'),
                            #'route_ids': order.picking_type_id.warehouse_id and [(6, 0, [x.id for x in order.picking_type_id.warehouse_id.route_ids])] or [],
                            'warehouse_id': wareh_id,
                            'invoice_state': '2binvoiced' ,
                        }
                        stock_move_id = move_obj.create(cr, uid, vals_stock_move)
                else:
                    raise osv.except_osv(_('Advertencia!'), _('No puede crear albarran de un producto que no es de stock!'))
            # else:
            #     raise osv.except_osv(_('Advertencia!'), _('Ya no hay mas lineas marcadas para procesar albarranes de ingreso!'))
        return True


    def button_dummy(self, cr, uid, ids, context=None):
        print "IDS***", ids
        conci_obj = self.pool.get('account.caja.chica')
        conci_lin_obj = self.pool.get('account.caja.chica.line')
        stat_conc_line_ids = conci_lin_obj.search(cr, uid, [('caja_chica_id', '=', ids)])
        stat_conc_line_obj =  conci_lin_obj.browse(cr, uid, stat_conc_line_ids, context=context)
        valor_bruto = 0.00
        valor_neto = 0.00
        valor_iva = 0.00
        valor_brutof = 0.00
        valor_netof = 0.00
        valor_ivaf = 0.00
        for cc in self.browse(cr, uid, ids, context=context):
            sal_ini = cc.saldo_ini
        print "SAL INI", sal_ini
        for st_lin in stat_conc_line_obj:
            valor_bruto += round(st_lin.amount, 2)
            valor_neto += round(st_lin.amount_neto, 2)
            valor_iva += round(st_lin.amount_iva_retenido, 2)
            if st_lin.iva_fact:
                valor_brutof += round(st_lin.amount, 2)
                valor_netof += round(st_lin.amount_neto, 2)
                valor_ivaf += round(st_lin.amount_iva_retenido, 2)
        vals_stat = {'valor_bruto' : valor_bruto,
                  'saldo_pend' : sal_ini-valor_bruto,
                  'valor_neto' : valor_neto,
                  'valor_iva' : valor_iva,
                  'valor_bruto_f' : valor_brutof,
                  'valor_neto_f' : valor_netof,
                  'valor_iva_f' : valor_ivaf}
        conci_obj.write(cr,uid,ids,vals_stat)            
        return self.write(cr, uid, ids, {'state': 'open'}, context=context)

    def button_cancel(self, cr, uid, ids, context=None):
        bnk_st_line_ids = []
        #CSV 13-06-2017 Comento para cancelar caja chica no manejo asientos
        # for st in self.browse(cr, uid, ids, context=context):
        #     bnk_st_line_ids += [line.id for line in st.line_ids]
        # self.pool.get('account.caja.chica.line').cancel(cr, uid, bnk_st_line_ids, context=context)
        return self.write(cr, uid, ids, {'state': 'open'}, context=context)

    def abrir_caja(self, cr, uid, ids, context=None):
        print "abrir_caja: ", ids
        self.write(cr, uid, ids, {'state':'open', 'date':time.strftime('%Y-%m-%d %H:%M:%S')})
        return True


class account_caja_chica_line(osv.osv):

    def cancel(self, cr, uid, ids, context=None):
        account_move_obj = self.pool.get('account.move')
        move_ids = []
        for line in self.browse(cr, uid, ids, context=context):
            if line.journal_entry_id:
                move_ids.append(line.journal_entry_id.id)
                for aml in line.journal_entry_id.line_id:
                    if aml.reconcile_id:
                        move_lines = [l.id for l in aml.reconcile_id.line_id]
                        move_lines.remove(aml.id)
                        self.pool.get('account.move.reconcile').unlink(cr, uid, [aml.reconcile_id.id], context=context)
                        if len(move_lines) >= 2:
                            self.pool.get('account.move.line').reconcile_partial(cr, uid, move_lines, 'auto', context=context)
        if move_ids:
            account_move_obj.button_cancel(cr, uid, move_ids, context=context)
            account_move_obj.unlink(cr, uid, move_ids, context)

    _order = "caja_chica_id desc"
    _name = "account.caja.chica.line"
    _description = "Caja Chica Detalle"
#    _inherit = ['ir.needaction_mixin']
    _columns = {
        'name': fields.char('Concepto', required=True),
        'date': fields.date('Fecha', required=True),
        'partner_id': fields.many2one('res.partner', 'Proveedor'),
        'product_id': fields.many2one('product.product', 'Producto'),
        'cantidad': fields.float('Cantidad', select=True, help="Cantidad requerida.", digits_compute=dp.get_precision('Account')),
        'amount': fields.float('Total', digits_compute=dp.get_precision('Account')),
        'caja_chica_id': fields.many2one('account.caja.chica', 'Caja Chica', select=True, required=True, ondelete='restrict'),
        'amount_iva_retenido': fields.float('Iva', help="The amount expressed in an optional other currency if it is a multi-currency entry.", digits_compute=dp.get_precision('Account')),
        'amount_neto': fields.float('Subtotal', help="The amount expressed in an optional other currency if it is a multi-currency entry.", digits_compute=dp.get_precision('Account')),
        'is_inven': fields.boolean('Inventario', help="Marcar si es un registro que necesitamos afecte inventarios"),
        'is_iva': fields.boolean('IVA', help="Marcar si es un registro que aplica iva"),
        'iva_fact': fields.boolean('I.F', help="Marcar si quiere verificar el valor total del iva de la factura saldra en la parte inferior"),
        'user_id': fields.many2one('res.users', 'Responsable', required=False),
        'company_id': fields.related('caja_chica_id', 'company_id', type='many2one', relation='res.company', string='Company', store=True, readonly=True),
        #'partner_name': fields.char('Proveedor Nombre', help="Este campo es usado en el caso que no exista el proveedor requerido para que contabilidad lo cree"),
        #'note': fields.text('Notes'),
        'sequence': fields.integer('Sequence', select=True, help="Gives the sequence order when displaying a list of caja chica."),
        'number_fact': fields.char('Factura', size=9, required=True),
        'tipo_comp': fields.selection([('factura', 'Factura'),
                                   ('recibo','Recibo'),
                                   ('nventa','N. Venta')],
                                   'Documento', required=True,
                                   copy=False,
                                   help='Seleccione el tipo de documento que esta registrando.'),
        'state': fields.selection([('open','Open'), # CSV:2016-04-21 used by cash statements
                                   ('confirm', 'Closed')],
                                   'Status', required=True, readonly="1",
                                   copy=False,
                                   help='When new statement is created the status will be \'Draft\'.\n'
                                        'And after getting confirmation from the bank it will be in \'Confirmed\' status.'),
        'por_iva': fields.selection([('10', '10%'),
                                   ('12','12%'),
                                   ('14','14%')],
                                   '%IVA', required=True,
                                   copy=False,
                                   help='Seleccione el % de iva de la factura.'),
    }
    _defaults = {
        #'name': lambda self,cr,uid,context={}: self.pool.get('ir.sequence').get(cr, uid, 'account.caja.chica.line'),
        'date': lambda self,cr,uid,context={}: context.get('date', fields.date.context_today(self,cr,uid,context=context)),
        'user_id': lambda obj, cr, uid, context: uid,
        'state': 'open',
        'por_iva': '12',
    }

    def onchange_is_factura(self, cr, uid, ids, tipo_comp, context=None):
        result = {}
        print "TIPO Comp", tipo_comp

        if tipo_comp == 'factura':
            result = { 'value' : { 'is_iva' : True }}
        else:
            result = { 'value' : { 'is_iva' : False }}
        return result

    def onchange_valor_iva(self, cr, uid, ids, tipo_comp, is_iva, amount_neto, por_iva, context=None):
        result = {}
        print "TIPO COMP", tipo_comp
        print "IS IVA", is_iva
        print "SUBTOTAL", amount_neto
        iva = int(por_iva)

        if tipo_comp == 'factura' and is_iva:
            result = { 'value' : { 'amount_iva_retenido' : round((amount_neto*iva)/100,2),
                                   'amount' : round(amount_neto+((amount_neto*iva)/100),2) }}
        elif tipo_comp == 'factura' and not is_iva:
            result = { 'value' : { 'amount_iva_retenido' : 0.00,
                                   'amount' : round(amount_neto,2) }}
        else:
            result = { 'value' : { 'amount_iva_retenido' : 0.00,
                                   'amount' : round(amount_neto,2) }}
        return result

    def onchange_is_iva(self, cr, uid, ids, tipo_comp, is_iva, amount_neto, por_iva, context=None):
        result = {}
        print "TIPO COMP", tipo_comp
        print "IS IVA", is_iva
        print "SUBTOTAL", amount_neto
        iva = int(por_iva)

        if tipo_comp == 'factura' and is_iva:
            result = { 'value' : { 'amount_iva_retenido' : round((amount_neto*iva)/100,2),
                                   'amount' : round(amount_neto+((amount_neto*iva)/100),2) }}
        elif tipo_comp == 'factura' and not is_iva:
            result = { 'value' : { 'amount_iva_retenido' : 0.00,
                                   'amount' : round(amount_neto,2) }}
        else:
            result = { 'value' : { 'amount_iva_retenido' : 0.00,
                                   'amount' : round(amount_neto,2) }}
        return result

    def onchange_valor_proc(self, cr, uid, ids, tipo_comp, amount, context=None):
        result = {}
        print "amount", amount
        amount_conc = amount
        print "amount_conc", amount_conc
        if tipo_comp != 'factura':
            result = {'value' : { 'amount_iva_retenido' : 0.00,
                                   'amount_neto' : round(amount,2) }}
        else:
            result = { 'value' : { 'amount_iva_retenido' : round((amount*14)/100,2),
                                   'amount_neto' : round(amount-((amount*14)/100),2) }}
        return result
