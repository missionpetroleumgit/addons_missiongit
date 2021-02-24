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
import openerp.addons.decimal_precision as dp
# from openerp.exceptions import except_orm
from datetime import datetime, date, timedelta
import calendar

# from bit_payment.account_invoice import invoice
from openerp.tools.translate import _
from openerp.osv import fields, osv
from openerp import models, api
from openerp.exceptions import except_orm
import logging
import time
from number_to_text import Numero_a_Texto

_logger = logging.getLogger(__name__)

## BEGIN COMMON

# END COMMON

class account_invoice(osv.osv):
    _inherit = 'account.invoice'
    _description = 'Invoice'

    my_seq = ''
    my_exp_date = ''
    my_auth_id = ''

    def _get_supplier_iva_taxes(self, cr, uid, ids, context):
        # Inicializo las variables que necesito devolver
        res = {}
        for invoice in self.browse(cr, uid, ids, context=context):
            subtotal = tax_iva = amount_other = base_sin_iva = base_iva = 0.0
            for line in invoice.invoice_line:
                if line.price_subtotal:
                    for tax in line.invoice_line_tax_id:
                        value = 0
                        if tax.child_ids:   # Para los que tengan hijos
                            for c in tax.child_ids:
                                value += tax.amount * c.amount * line.price_subtotal
                        else:
                            value = tax.amount * line.price_subtotal
                        #CSV: IVA O FACTURAS COMPRAS
                        if line.invoice_id.type == 'in_invoice':
                            if tax.is_iva and not tax.description in ('517', '332') and line.invoice_id.type == 'in_invoice':
                                tax_iva += value  # IVA siempre es solo 1
                                base_iva += line.price_subtotal
                            elif tax.description == '517' and line.invoice_id.type == 'in_invoice':
                                base_sin_iva += line.price_subtotal
                            else:
                                amount_other += value # Sumo el resto de los taxes
                        #CSV: IVA O FACTURAS VENTAS
                        elif line.invoice_id.type == 'out_invoice':
                            if tax.is_iva and  not tax.description == '403' and line.invoice_id.type == 'out_invoice':
                                tax_iva += value  # IVA siempre es solo 1
                                base_iva += line.price_subtotal
                            elif tax.description == '403' and line.invoice_id.type == 'out_invoice':
                                base_sin_iva += line.price_subtotal
                            else:
                                amount_other += value
                        #CSV: IVA O NOTA CREDITO
                        elif line.invoice_id.type == 'out_refund':
                            if tax.is_iva and  not tax.description == '403' and line.invoice_id.type == 'out_refund':
                                tax_iva += value  # IVA siempre es solo 1
                                base_iva += line.price_subtotal
                            elif tax.description == '403' and line.invoice_id.type == 'out_refund':
                                base_sin_iva += line.price_subtotal
                            else:
                                amount_other += value
                    subtotal += line.price_subtotal
            #CSV:27-03-2018: Aumento para escribir la base 0 y corregir impresión masiva por campos tipo funcion
            print "BASE 0", base_sin_iva
            vals_base0 = {'base0': base_sin_iva}
            invoice.write(vals_base0)
            res[invoice.id] = {
                'base_iva': round(base_iva, 2),
                'base_sin_iva': round(base_sin_iva, 2),
                'amount_iva': round(tax_iva, 2),
                'amount_total_iva': round((subtotal + tax_iva ), 2),
                'amount_other': round(amount_other, 2)
            }
        return res

    def _amount_all(self, cr, uid, ids, name, args, context=None):
        # Busco los valores para la localización del ecuador
        res = self._get_supplier_iva_taxes(cr, uid, ids, context)
        return res

    _columns = {

        'document_type': fields.many2one('account.invoice.document', 'Invoice document', select=True),
        'tax_support': fields.many2one('account.tax.support', 'Soporte Tributario'),
        'amount_iva': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='IVA', multi='all'),
        'base_iva': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Base IVA', multi='all'),
        'base_sin_iva': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Base sin IVA', multi='all'),
        'amount_other': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Tax Others', multi='all'),
        'amount_total_iva': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Subtotal + IVA', multi='all'),
        'base0': fields.float('Base 0'),
        'authorization_id' : fields.many2one('account.authorization', 'Authorization number'),
        'range': fields.char('Rango autorizacion'),
        'number_seq': fields.char('Nro. Factura', size=9),
        'auth_due_date' : fields.date('Due date'),
        'is_inv_liq' : fields.boolean('Is liquidation ?'),
        'is_inv_elect' : fields.boolean('Es factura electronica?'),
        'elect_authorization' : fields.char('Nro. Autorizacion', size=49),
        'date_cont' : fields.date('Fecha de Contabilizacion',
                                  readonly=True, states={'draft': [('readonly', False)]}),
        'number_reem': fields.char(readonly=True),
        'state': fields.selection([
            ('draft','Draft'),
            ('proforma','Pro-forma'),
            ('proforma2','Pro-forma'),
            ('open','Open'),
            ('paid','Paid'),
            ('cancel','Cancelled'),
            ('invalidate', 'Anulado'),
            ('grouped', 'Agrupado')
        ], string='Status', index=True, readonly=True, default='draft',
            track_visibility='onchange', copy=False,
            help=" * The 'Draft' status is used when a user is encoding a new and unconfirmed Invoice.\n"
                 " * The 'Pro-forma' when invoice is in Pro-forma status,invoice does not have an invoice number.\n"
                 " * The 'Open' status is used when user create invoice,a invoice number is generated.Its in open status till user does not pay invoice.\n"
                 " * The 'Paid' status is set automatically when the invoice is paid. Its related journal entries may or may not be reconciled.\n"
                 " * The 'Cancelled' status is used when user cancel invoice."),
        'deduction_id': fields.many2one('account.deduction', 'Retencion'),
        'state_provision': fields.selection([('invoice', 'Factura'), ('prov', 'Provision'), ('rever','Reverso/Prov')], 'Comportamiento'),
        'prov_id': fields.many2one('account.move', 'Asiento Provision'),
        'provrev_id': fields.many2one('account.move', 'Asiento Reverso'),
        'invoice_grouped': fields.many2one('account.invoice', 'Factura Agrupada'),
        'retention_type': fields.selection([('Manual', 'Manual'), ('Electronica', 'Electronica'), ('not_generate', 'No genera')], 'Tipo de Ret.'),
        'emission_series': fields.char('Estab.', size=3),
        'emission_point': fields.char('Emis.', size=3),
        'retention_sequence_id': fields.many2one('ir.sequence', 'Secuencia de retencion'),
        'customer': fields.char(string='Cliente', readonly=True, states={'draft': [('readonly', False)]}),
        'direc': fields.char(string='Direccion', readonly=True, states={'draft': [('readonly', False)]}),
        'ciudad': fields.char(string='Ciudad', readonly=True, states={'draft': [('readonly', False)]}),
        'provincia': fields.char(string='Provincia', readonly=True, states={'draft': [('readonly', False)]}),
        'telef': fields.char(string='Telefono', readonly=True, states={'draft': [('readonly', False)]}),
        'email': fields.char(string='Email', readonly=True, states={'draft': [('readonly', False)]}),
    }

    _defaults = {
        'is_inv_liq': False,
        'state_provision': 'invoice',
        'retention_type': 'not_generate'
    }

    _sql_constraints = [
        ('number_uniq', 'unique(number, partner_id, journal_id, type, company_id)',
         'Invoice Number must be unique per Company!'),
    ]

    def _check_number_seq(self, cr, uid, ids, context=None):
        for invoice in self.browse(cr, uid, ids, context=context):
            if invoice.type == 'in_invoice' and invoice.document_type.code == '03':
                count = self.search(cr, uid, [('number_seq', '=', invoice.number_seq), ('id', '!=', invoice.id),
                                              ('company_id', '=', invoice.company_id.id),
                                              ('document_type', '=', invoice.document_type.id)], count=True)
                if count:
                    return False
                return True
        return True

        # _constraints = [
        #     (_check_number_seq, 'La secuencia de las liquidaciones es unica por compania.', ['number_seq', 'company_id']),
        # ]

    def onchange_number_invoice(self, cr, uid, ids, number):
        result = {'value': {'number_reem': False}}

        if number:
            result['value'] = {'number_reem': number[6:0],
                               }

            # print "number_reem: ", number_reem
        return result

    @api.multi
    def action_cancel(self):
        moves = self.env['account.move']
        for inv in self:
            if inv.move_id:
                moves += inv.move_id
            if inv.payment_ids:
                for move_line in inv.payment_ids:
                    if move_line.reconcile_partial_id.line_partial_ids:
                        raise osv.except_osv(_('Error!'), _('You cannot cancel an invoice which is partially paid. '
                                                            'You need to unreconcile related payment entries first.'))
            if inv.type in ('out_invoice', 'out_refund') and inv.deduction_id.state == 'draft':
                inv.deduction_id.state = 'cancel'
        if moves:
            moves.button_cancel()
            for rec in self:
                for line in inv.move_id.line_id:
                    line.unlink()
                rec.move_id = False
            moves.unlink()
        return True

    @api.multi
    def invalidate(self):
        move_env = self.env['account.move']
        for record in self:
            if record.payment_ids:
                raise osv.except_osv(_('Error!'), _('You cannot cancel an invoice which is partially paid. You need to unreconcile related '
                                                    'payment entries first.'))
            move_id = record.move_id
            record.move_id = False
            move_id.button_cancel()
            move_id.unlink()
            record.state = 'invalidate'

    def get_invoice(self, cr, uid, ids, context):
        sum_discount = 0
        for invoice in self.browse(cr, uid, ids, context):
            for line in invoice.invoice_line:
                sum_discount += line.price_subtotal * (line.discount/100 or 1)
        return sum_discount

    def generate_provision(self, cr, uid, ids, context=None):
        for record in self.browse(cr, uid, ids, context):
            if record.state != 'draft' or record.prov_id:
                raise osv.except_orm('Error!', 'No puede provisionar una factura que no este en estado borrador o que ya tiene una provision %s'
                                               % ':' + record.prov_id.name if record.prov_id else '.')
            view_ref = self.pool['ir.model.data'].get_object_reference(cr, uid, 'bit_account', 'form_provision_entry')
            view_id = view_ref and view_ref[1] or False,
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'provision.entries',
                # 'res_id': record.id,
                'view_type': 'form',
                'view_mode': 'form',
                'view_id': view_id[0],
                'target': 'new',
            }

    def reverse_provition(self, cr, uid, ids, context=None):
        move = self.pool.get('account.move')
        line = self.pool.get('account.move.line')
        date_today = datetime.today().strftime('%Y-%m-%d')
        period_ids = self.pool.get('account.period').search(cr, uid, [('date_start', '<=', date_today), ('date_stop', '>=', date_today)])
        if not period_ids:
            raise osv.except_orm('Error!', 'No hay un periodo definido para la fecha actual: %s' % date_today)
        for record in self.browse(cr, uid, ids, context):
            move_id = move.create(cr, uid, {'ref': 'Rev.:' + record.prov_id.ref if record.prov_id.ref else '', 'period_id': period_ids[0], 'date': date_today,
                                            'journal_id': record.prov_id.journal_id.id}, context)
            for item in record.prov_id.line_id:
                line.create(cr, uid, {'name': 'Rev.:' + record.prov_id.ref if record.prov_id.ref else '', 'partner_id': item.partner_id.id, 'account_id': item.account_id.id, 'debit': item.credit,
                                      'credit': item.debit, 'move_id': move_id}, context)
            self.write(cr, uid, [record.id], {'state_provision': 'invoice'}, context)
        return True

    def onchange_partner_id(self, cr, uid, ids, move_id, partner_id, account_id=None, debit=0, credit=0, date=False, journal=False, context=None):
        # Llamo al onchange original de OpenERP
        #CSV: aumento para guardar los datos en la factura para tener un historial
        client = ''
        direc = ''
        ciudad = ''
        prov = ''
        telef = ''
        email = ''
        if not context:
            context = dict()
            inv_type = move_id
        else:
            inv_type = context.get('type')
        res = super(account_invoice, self).onchange_partner_id(cr, uid, ids, inv_type, partner_id, account_id, debit, credit, date, journal)

        if partner_id:
            property_obj = self.pool.get('res.partner')
            p = property_obj.browse(cr, uid, partner_id)
            print "RES_PARTNER", p
            client = p.name
            res['value']['customer'] = client
            #print "nombre", client
            if p.street and p.street2:
                direc = str(p.street.encode('UTF-8'))+" "+str(p.street2.encode('UTF-8'))
                res['value']['direc'] = direc
            elif p.street and not p.street2:
                direc = str(p.street.encode('UTF-8'))
                res['value']['direc'] = direc
            elif p.street2 and not p.street:
                direc = str(p.street2.encode('UTF-8'))
                res['value']['direc'] = direc
            else:
                direc = ''
                res['value']['direc'] = direc
            if p.ciudad_id:
                ciudad = str(p.ciudad_id.name.encode('UTF-8'))
                res['value']['ciudad'] = ciudad
            else:
                ciudad = ''
                res['value']['ciudad'] = ciudad
            if p.state_id:
                prov = str(p.state_id.name.encode('UTF-8'))
                res['value']['provincia'] = prov
            else:
                prov = ''
                res['value']['provincia'] = prov
            if p.phone:
                telef = str(p.phone)
                res['value']['telef'] = telef
                print "telefono", telef
            else:
                telef = ''
                res['value']['telef'] = telef
            if p.email:
                email = str(p.email.encode('UTF-8'))
                res['value']['email'] = email
            else:
                email = ''
                res['value']['email'] = email
                # Leo los valores
            read_doc_type = property_obj.read(cr,uid,partner_id,['document_type', 'property_account_position', 'supplier'])    # ID Document type          

            if read_doc_type.get('document_type'):
                # Agrego el valor al result
                document_type = read_doc_type.get('document_type')[0]
                res['value']['document_type'] = document_type
                obj_auth = self.pool.get('account.authorization')
                if read_doc_type.get('supplier'):
                    brw_doc_type = self.pool.get('account.invoice.document').browse(cr, uid, document_type, context=context)
                    if brw_doc_type.is_liquidation:
                        my_args = [('type_id', '=', document_type), ('active', '=', True)]
                    else:
                        my_args = [('partner_id', '=', partner_id), ('type_id', '=', document_type), ('active', '=', True)]
                    auth_ids = obj_auth.search(cr, uid, my_args) # Obtain auth for both case
                else:
                    my_args = [('to_customer', '=', True), ('type_id', '=', document_type), ('active', '=', True)]
                    auth_ids = obj_auth.search(cr, uid, my_args)

                if auth_ids:
                    res['value']['authorization_id'] = auth_ids[0]
                else:
                    res['value']['authorization_id'] = ''
                    #res['value']['document_type'] = ''
            else:
                res['value']['authorization_id'] = ''
                res['value']['document_type'] = ''
                res['value']['number_seq'] = ''
                res['value']['auth_due_date'] = ''

        return res

    def onchange_doc_type(self, cr, uid, ids, partner_id, document_type, is_inv_elect, context=None):
        if context is None:
            context = {}
        auth_ids = []
        res = { 'value' : {} }
        brw_user = self.pool.get('res.users').browse(cr, uid, uid)
        is_ready = False
        is_supp_liq = False
        is_fact_elec = is_inv_elect and context.get('type') in ('in_invoice', 'in_refund')
        res['domain'] = {'authorization_id': [('to_customer', '=', False), ('partner_id', '=', partner_id), ('is_electronic','=',False)]}
        if not is_fact_elec and 'load_auth' in context and context.get('load_auth') and \
                        'type' in context and context.get('type'):
            if not partner_id:
                return { 'value': { 'document_type' : '' },
                         'warning': { 'title': '¡¡ Alerta !!',
                                      'message': 'Debe registrar un cliente antes de seleccionar el tipo de documento.' } }
            obj_auth = self.pool.get('account.authorization')
            obj_doc = self.pool.get('account.invoice.document')
            brw_doc = obj_doc.browse(cr, uid, document_type, context=context)
            if brw_doc:
                if brw_doc.code == '03':
                    doc_auth_ids = self.pool.get('account.authorization').search(cr, uid, [('type_id', '=', brw_doc.id)])
                    if not doc_auth_ids:
                        raise osv.except_osv('Error!!', 'No existe autorizacion asociada a la compañia para este tipo de documento')
                    res['domain'] = {'authorization_id': [('to_customer', '=', False), ('partner_id', '=', brw_user.company_id.partner_id.id), ('is_electronic','=',False)]}
                    res['value']['authorization_id'] = doc_auth_ids[0]

                else:
                    msg = ''
                    doc_type = (brw_doc.code + ' - ' + brw_doc.name) or 'Unknow'
                    if context.get('type') == 'in_invoice' or context.get('type') == 'in_refund':
                        if document_type and partner_id:
                            obj_auth = self.pool.get('account.authorization')
                            if not brw_doc.is_liquidation:
                                my_args = [('partner_id', '=', partner_id), ('type_id', '=', document_type), ('to_customer', '=', False)]
                            else:
                                my_args = [('partner_id', '=', brw_user.company_id.partner_id.id), ('type_id', '=', document_type), ('to_customer', '=', False)]
                                is_supp_liq = True
                            partner_name = self.pool.get('res.partner').browse(cr, uid, partner_id, context=context).name or 'Unknow'
                            auth_ids = obj_auth.search(cr, uid, my_args) # Obtain auth for both case
                            msg = _('Debe registrar una nueva autorización para este tipo de documento <%s> asociada a "%s".') % (doc_type, partner_name)
                    else:
                        my_args = [('company_id', '=', brw_user.company_id.id), ('type_id', '=', document_type), ('to_customer', '=', True)]
                        msg = _('Debe registrar una nueva autorización para este tipo de documento <%s> asociada a compañía.') % (doc_type)
                        auth_ids = obj_auth.search(cr, uid, my_args) # Obtain auth for both case
                    for brw_auth in obj_auth.browse(cr, uid, auth_ids, context=context):
                        res['value'].update({'authorization_id': brw_auth.id, 'is_inv_liq': False, 'number_seq': ''})
                        if is_supp_liq:
                            res['value'].update({'number_seq': brw_auth.sequence_id.number_next,
                                                 'is_inv_liq': True
                                                 })
                        is_ready = True
                    if not is_ready:
                        return {'value': {'document_type' : '', 'is_inv_liq': False},
                                 'warning': {'title': '¡¡ Alerta !!', 'message': msg }}
        elif is_fact_elec:
            return {'value': {'document_type': document_type}}

        return res

    def onchange_authorization(self, cr, uid, ids, auth_id, context=None):
        if context is None:
            context = {}
        res = { 'value' : {} }
        number = ''
        obj_auth = self.pool.get('account.authorization')
        brw_auth = obj_auth.browse(cr, uid, auth_id, context=context)
        if brw_auth:
            res['value'].update({ 'auth_due_date' : brw_auth.expiration_date })
            self.my_exp_date = brw_auth.expiration_date
            self.my_auth_id = brw_auth.id
            range_auth = str(brw_auth.num_start) + '-' + str(brw_auth.num_end)
            res['value'].update({'range': range_auth})
        return res

    def create(self, cr, uid, vals, context=None):
        if context is None:
            context = {}
        if 'partner_id' in vals:
            obj_partner = self.pool.get('res.partner')
            partner = obj_partner.browse(cr, uid, vals.get('partner_id'))
            vals['fiscal_position'] = partner.property_account_position.id
        if self.my_seq:
            vals['number_seq'] = self.my_seq
        if self.my_exp_date:
            vals['auth_due_date'] = self.my_exp_date
        if 'number_seq' in vals:
            vals['number_seq'] = self.check_len(vals['number_seq'], 9)
            if 'is_inv_elect' not in vals:
                vals['is_inv_elect'] = False
            if vals['is_inv_elect']:
                if self.check_number_seq(cr, uid, vals['number_seq'], vals['partner_id'], 'create', vals.get('is_inv_elect',False), False, vals.get('emission_series',False), vals.get('emission_point',False), vals['authorization_id']):
		    print "id factura"
                    # raise osv.except_orm('Error', 'Ya existe una factura con el numero %s' % vals['number_seq'])
            if ('default_type' in context and context['default_type'] == 'in_invoice' and not vals['is_inv_elect']) \
                    or ('type' in context and context['type'] == 'in_invoice' and not vals['is_inv_elect']):
                aut = self.pool.get('account.authorization').browse(cr, uid, vals['authorization_id'])
                self.check_range(vals['number_seq'], aut.num_start, aut.num_end)

        return super(account_invoice, self).create(cr, uid, vals, context=context)

    def check_range(self, value, _from, _to):
        if _from <= int(value) <= _to:
            return True
        else:
            raise osv.except_orm('Error!', 'El consecutivo de autorizacion no esta en el rango de la autorizacion: de %s a %s' % (_from, _to))

    def write(self, cr, uid, ids, vals, context=None):
        invoice = self.browse(cr, uid, ids[0])
        if 'partner_id' in vals:
            obj_partner = self.pool.get('res.partner')
            partner = obj_partner.browse(cr, uid, vals.get('partner_id'))
            vals['fiscal_position'] = partner.property_account_position.id
        else:
            partner = self.browse(cr, uid, ids[0]).partner_id
        # if self.my_seq:
        #     vals['number_seq'] = self.my_seq
        if self.my_exp_date:
            vals['auth_due_date'] = self.my_exp_date
        if 'number_seq' in vals:
            vals['number_seq'] = self.check_len(vals['number_seq'], 9)
            if self.check_number_seq(cr, uid, vals['number_seq'], partner.id, 'write', invoice.is_inv_elect, invoice.type, ids[0], invoice.emission_series, invoice.emission_point):
		print "id factura"
                # raise osv.except_orm('Error', 'Ya existe una factura con el numero %s' % vals['number_seq'])
        res = super(account_invoice, self).write(cr, uid, ids, vals, context=context)
        return res

    def check_number_seq(self, cr, uid, number_seq, partener_id, method, is_inv_elect, type, obj_id=False, emission_series=False, emission_point=False):
        criteria = [('number_seq', '=', number_seq), ('partner_id', '=', partener_id), ('type', '=', type)]
        if is_inv_elect:
            criteria.append(('emission_series', '=', emission_series))
            criteria.append(('emission_point', '=', emission_point))
        if method == 'create':
            if self.search(cr, uid, criteria, count=True):
                return True
        elif method == 'write':
            criteria.append(('id', '!=', obj_id))
            if self.search(cr, uid, criteria, count=True):
                return True
        return False

    def copy(self, cr, uid, id, default=None, context=None, done_list=None, local=False):
        default = {} if default is None else default.copy()
        if done_list is None:
            done_list = []
        acc_inv = self.browse(cr, uid, id, context=context)

        default.update(document_type=False, number_seq=False, authorization_id=False, \
                       auth_due_date=False, date_invoice=datetime.today())

        return super(account_invoice, self).copy(cr, uid, id, default, context=context)

    @api.multi
    def invoice_validate(self):
        if self.state_provision == 'prov':
            raise osv.except_orm('Error!', 'La factura esta provisionada, debe revertir esta provision antes de validar')
        customer_ret = False
        number = num = 0
        is_inv_liq = False
        brw_ret_auth = None
        deduction_id = False
        if not self.authorization_id and not self.is_inv_elect:
            raise osv.except_osv(_('¡¡ Alerta !!'), _('Debe asociar una autorización a esta factura.'))
        obj_doc_type = self.pool.get('account.invoice.document')
        obj_auth = self.pool.get('account.authorization')
        obj_deduction = self.pool.get('account.deduction')
        obj_tax = self.pool.get('account.invoice.tax')
        brw_auth = self.authorization_id
        seq_name = self.document_type.name
        if len(self.document_type.name) > 32:
            seq_name = self.document_type.name[0:32]
        if self.type == 'in_invoice' or self.type == 'in_refund':  # From supplier
            if self.document_type.code == '03':
                partner_id = self.company_id.partner_id.id
            else:
                partner_id = self.partner_id.id
            ret_partner = self.company_id.partner_id.id
            is_inv_liq = brw_auth.type_id.is_liquidation
            cust = False
        else:
            cust = True
            partner_id = self.company_id.partner_id.id
            ret_partner = self.partner_id.id
            if self.authorization_id:
                customer_ret = True
        my_filter = []
        if (not self.document_type.is_liquidation or self.type == 'out_invoice' or self.type == 'out_refund') and self.type not in ('in_invoice', 'in_refund'):
            my_filter = [('name', '=', seq_name), ('partner_id', '=', partner_id)]
        else:
            my_filter = [('name', '=', seq_name), ('partner_id', '=', partner_id)]
        print "my_filter: ",  my_filter
        seq_id = self.env['ir.sequence'].search(my_filter)
        if seq_id:
            seq_id = seq_id[0].id
        if self.type in ('out_invoice', 'out_refund'):
            seq_id = self.authorization_id.sequence_id.id
        ret_seq_id = self.pool.get('ir.sequence').search(self._cr, self._uid, [('name', '=', seq_name), ('partner_id', '=', ret_partner)])
        _logger.error("seq_id: "+str(seq_id)+"        ret_seq_id: "+str(ret_seq_id))
        if is_inv_liq:
            ret_seq_id = seq_id
        if not self.is_inv_elect and not seq_id and not is_inv_liq:
            raise osv.except_osv(_('¡¡ Alerta !!'), _('Debe registrar una nueva autorización para este tipo de documento <%s> asociada a "%s".') % (seq_name, self.env['res.partner'].browse(partner_id).name))

            formato_fecha = "%Y-%m-%d"
            exp_date = datetime.strptime(self.authorization_id.expiration_date, formato_fecha).date()
            invoice_date = datetime.strptime(self.date_invoice, formato_fecha).date() or datetime.today().date()
            if exp_date < invoice_date:
                if brw_auth:
                    obj_auth.write(self._cr, self._uid, brw_auth.id, { 'active' : False })
                raise osv.except_osv(_('¡¡ Alerta !!'), _('La fecha de la autorización ha expirado. Debe registrar una nueva autorización para este tipo de documento .'))

                #  'message': _('La fecha de la autorización ha expirado. Debe registrar una nueva autorización para este tipo de documento .')# % (seq_name)
        number_inv_seq = ''
        if self.type == 'out_invoice' or self.type == 'out_refund':
            if self.number_seq:
                number_inv_seq = self.number_seq
            else:
                number_inv_seq = self.pool.get('ir.sequence').next_by_id(self._cr, self._uid, seq_id, self._context)#self.env['ir.sequence'].browse(seq_id).number_next_actual
        else:
            number_inv_seq = self.number_seq
        if not customer_ret:
            ret_ids = [False]
            doc_type_ids = obj_doc_type.search(self._cr, self._uid, [('is_retention', '=', True)], self._context)
            if self.retention_type not in ('not_generate', 'Manual'):
                # obj_auth.code_unique = '1 - 1 - 07 - Comprobante de Rete'
                # obj_auth.sequence_code = '07 - Comprobante de Retencion'
                auth_values = {
                    'name': '0000000000000',
                    'serie_entity': '001',
                    'serie_emission': '002',
                    'num_start': 1,
                    'num_end': 1,
                    'partner_id': self.partner_id.id,
                    'is_electronic': True,
                    'expiration_date': datetime.today().strftime('%Y-%m-%d'),
                    'type_id': doc_type_ids[0],
                    'is_retention': True
                }

                auth_values.update({'sequence_id': self.retention_sequence_id.id, 'num_start': self.retention_sequence_id.number_next_actual,
                                    'num_end': self.retention_sequence_id.number_next_actual})
                ret_ids = [obj_auth.create(self._cr, self._uid, auth_values)]
            elif self.retention_type == 'Manual':
                ret_ids = obj_auth.search(self._cr, self._uid, [('type_id', 'in', doc_type_ids), ('to_customer', '=', cust), ('partner_id', '=', self.company_id.partner_id.id), ('company_id', '=', self.company_id.id),
                                                                ('is_electronic', '=', False), ('expiration_date', '>=', datetime.today().strftime('%Y-%m-%d'))])
                if not ret_ids and not is_inv_liq:
                    raise osv.except_osv(_('¡¡ Alerta !!'), _('No se ha definido todavía una autorización para las retenciones manuales.'))
            if not is_inv_liq:
                ret_id = ret_ids[0]
                if self.amount_other < 0.00 and self.type == 'in_invoice':
                    if ret_id:
                        brw_ret_auth = self.pool.get('account.authorization').browse(self._cr, self._uid, ret_id)
                        number = self.pool.get('ir.sequence').next_by_id(self._cr, self._uid, brw_ret_auth.sequence_id.id, self._context)
                    if not self.is_inv_elect and brw_auth and not customer_ret and self.number_seq and not (int(self.authorization_id.num_start) <= int(number_inv_seq) <= int(self.authorization_id.num_end)):
                        raise osv.except_osv(_('¡¡ Alerta !!'), _('El número de la autorización para el documento está fuera del rango permisible ó ' \
                                                                  'la autorización se ha agotado. ' \
                                                                  'Debe registrar una nueva autorización para este tipo de documento .'))

                        # if not self.is_inv_elect and self.authorization_id and not customer_ret and number and (int(self.authorization_id.num_end) < int(number) \
                        #                                                              or int(self.authorization_id.num_start) > int(number)):
                        #     raise osv.except_osv(_('¡¡ Alerta !!'), _('El número de la autorización para las retenciones está fuera del rango permisible ó ' \
                        #                                               'la autorización para las retenciones se ha agotado. ' \
                        #                                               'Debe registrar una nueva autorización para este tipo de documento .'))
                else:
                    number = 0

        if self.type == 'out_invoice' or self.type == 'out_refund':
            ret_type = 'customer'
        else:
            ret_type = 'supplier'
            num = self.pool.get('ir.sequence').get(self._cr, self._uid, 'account.payable.deduction')
            if self.document_type and number_inv_seq:
                auth = False
                if not self.is_inv_elect:
                    auth = self.env['account.authorization'].search([('serie_entity', '=', self.authorization_id.serie_entity),
                                                                     ('serie_emission', '=', self.authorization_id.serie_emission),
                                                                     ('id', '!=', self.authorization_id.id),
                                                                     ('partner_id', '=', partner_id),
                                                                     ('type_id', '=', self.document_type.id),
                                                                     ('active', '=', True),
                                                                     ('name', '!=', self.authorization_id.name),
                                                                     ('expiration_date', '>=', self.date_invoice)])
                    if auth:
                        auth = auth[0].id
                    else:
                        auth = False
                criteria = ['|', ('type', '=', 'in_refund'), ('type', '=', 'in_invoice'), ('partner_id', '=', partner_id), \
                            ('document_type', '=', self.document_type.id), ('state', '!=', 'draft'), \
                            ('number_seq', '=', number_inv_seq), ('id', '!=', self.id), ('authorization_id', '=', auth)]
                if self.is_inv_elect:
                    criteria.append(('emission_series', '=', self.emission_series))
                    criteria.append(('emission_point', '=', self.emission_point))
                list_auth_number = self.pool.get('account.invoice').search(self._cr, self._uid, criteria)
                if list_auth_number:
                    raise osv.except_osv(_('¡¡ Alerta !!'), _('Este número ya ha sido definido en ' \
                                                              'otra autorización de factura.'))
                    #
                    #
                    #
                    # if self.type == 'out_invoice' or self.type == 'out_refund':
                    #     ret_type = 'customer'
                    # else:
                    #     ret_type = 'supplier'
                    #     num = self.pool.get('ir.sequence').get(self._cr, self._uid, 'account.payable.deduction')

                    #*********CSV:14-03-2016:VALIDAR SI EXISTE RETENCION************************
        exist_rv = obj_deduction.search(self._cr, self._uid, [('state', '=', 'open'), ('type', 'in', ('supplier', 'customer')), ('invoice_id', '=', self.id)])
        if self.retention_type in ('Manual', 'Electronica'):
            is_inv_liq = True
        if (not is_inv_liq and customer_ret or brw_ret_auth or number) or (is_inv_liq and self.retention_type in ('Manual', 'Electronica')):
            authorization_id = False
            if self.type in ('in_invoice', 'in_refund') and self.retention_type != 'not_generate':
                authorization_id = brw_ret_auth.id if brw_ret_auth else ret_ids and ret_ids[0] or False
                if not number and not exist_rv:
                    number = self.pool.get('ir.sequence').next_by_id(self._cr, self._uid, obj_auth.browse(self._cr, self._uid, authorization_id).sequence_id.id, self._context)
            vals = {
                'invoice_id': self.id,
                'tax_ids': self.tax_line,
                'type': ret_type,
                'partner_id': self.partner_id.id,
                'emission_date': self.date_invoice
            }
            if customer_ret:
                vals.update({
                    'state': 'draft',
                    'retention_type': 'Manual'
                })
            else:
                vals.update({
                    'state': 'open',
                    'number': number,
                    'name': num,
                    'authorization_id': authorization_id,
                    'retention_type': self.retention_type
                })

                # if not self.is_inv_elect and int(number_inv_seq) == int(brw_auth.num_end):
                #     self.pool.get('account.authorization').write(self._cr, self._uid, brw_auth.id, {'active': False})
                # if not customer_ret:
                # if self.retention_type != 'not_generate' and brw_ret_auth:
                #     _logger.error("Edita la secuencia "+str(brw_ret_auth.sequence_id.id)+"  por: "+str(customer_ret)+"  valores: "+str(int(number) + 1))
                # self.pool.get('ir.sequence').write(self._cr, self._uid, brw_ret_auth.sequence_id.id, { 'number_next': int(number) + 1 })
            #*********CSV:14-03-2016:VALIDAR SI EXISTE RETENCION************************
            if len(exist_rv)>0:
                deduction_id = exist_rv[0]
                print "YA EXISTE", exist_rv[0]
                vals.update({
                    'state': 'open',
                })
            else:
                if self.retention_type != 'not_generate':
                    deduction_id = obj_deduction.create(self._cr, self._uid, vals)

            l_tax_id = []
            l_tax_inv = []
            for tax_inv in self.tax_line:
                tmp_tax_inv = {
                    #    'account_id': tax_inv.account_id.id,
                    'tax_code_id': tax_inv.tax_code_id.id,
                    'base_code_id': tax_inv.base_code_id.id
                }
                #                if tmp_tax_inv not in l_tax_inv:
                if tmp_tax_inv:
                    l_tax_inv.append(tmp_tax_inv)
                    l_tax_id.append(tax_inv.id)

            l_tax_deduc = []
            for line in self.invoice_line:
                for tax_line in line.invoice_line_tax_id:
                    if not tax_line.is_iva:
                        tmp_tax_line = {}
                        if tax_line.child_depend:
                            for child in tax_line.child_ids:
                                child_tax_line = {
                                    #        'account_id': child.account_collected_id.id,
                                    'tax_code_id': child.tax_code_id.id,
                                    'base_code_id': child.base_code_id.id
                                }
                                if child_tax_line in l_tax_inv:
                                    tmp_tax_line = child_tax_line
                        else:
                            tmp_tax_line =  {
                                #        'account_id': tax_line.account_collected_id.id,
                                'tax_code_id': tax_line.tax_code_id.id,
                                'base_code_id': tax_line.base_code_id.id
                            }
                        if tmp_tax_line in l_tax_inv:
                            pos_ids = l_tax_inv.index(tmp_tax_line)
                            for _id in type(pos_ids) == type([]) and pos_ids or [pos_ids]:
                                if l_tax_id[pos_ids] not in l_tax_deduc:
                                    #  *********CSV:14-03-2016:RECORRER IMPUESTOS NECESARIOS PARA RETENCION DE CLIENTES
                                    l_tax_deduc += [l_tax_id[pos_ids]]
                                    l_tax_inv.pop(pos_ids)
                                    l_tax_id.pop(pos_ids)

            obj_tax.write(self._cr, self._uid, l_tax_deduc, { 'deduction_id' : deduction_id })

        # cant = len(str(number_inv_seq)) + len(str(brw_auth.type_id.code))
        # n = '000000000'
        # number_inv_seq = n[:9-cant] + str(number_inv_seq)
        if not self.is_inv_elect:
            new_number = str(brw_auth.type_id.code) + ' - ' + str(brw_auth.serie_entity) + ' - ' + \
                         str(brw_auth.serie_emission) + ' - ' + self.check_len(str(number_inv_seq), 9)
        else:
            new_number = self.check_len(str(number_inv_seq), 9)

        if self.type == 'in_invoice' and self.pool.get('account.invoice').search(self._cr, self._uid,[('number', '=', new_number), ('type', '=', 'in_invoice'),
                                                                                                      ('state', '!=', 'draft'), ('partner_id', '=', partner_id)]):
            raise osv.except_osv(_('¡¡ Alerta !!'),
                                 _('El número de la autorización ya ha sido utilizado.' \
                                   'Debe modificar el número de la autorización.'))

        is_ok = self.write({ 'state': 'open', 'number_seq' : number_inv_seq, \
                             'internal_number' : new_number, 'number' : new_number })
        if is_ok and self.type == 'out_invoice' or is_ok and self.type == 'out_refund' or is_inv_liq:
            _logger.error("Edita la secuencia: "+str(brw_auth.sequence_id.id)+"  Por: "+str(is_ok)+" - "+str(is_inv_liq)+"  valores: "+str(int(number_inv_seq) + 1))
            # self.pool.get('ir.sequence').write(self._cr, self._uid, brw_auth.sequence_id.id, {'number_next': int(number_inv_seq) + 1})
        #cambio 22 02 2016 - number
        if self.number and self.type == 'out_invoice':
            self.number_reem = self.number[5:]
        elif self.number and self.type == 'in_invoice' and self.is_inv_elect == False:
            self.number_reem = self.number[5:]
        elif self.number and self.type == 'in_invoice':
            if not self.is_inv_elect:
                self.number_reem = self.number
            else:
                self.number_reem = self.emission_series + '-' + self.emission_point + '-' + self.number
                self.number = self.number_reem
        else:
            self.number_reem = self.number[5:]
        if self.move_id:
            #JJM 2017-11-12
            # buscar asientos de movimientos de diario de inventario para asignarle el numero de factura
            self.move_id.ref = self.move_id.ref + u' Fact ' + self.number_reem
            # agregar la refentecia del padre para las lines de movimiento
            for line in self.move_id.line_id:
                line.ref = self.move_id.ref
            #para movimientos relacionados (carga facturas pos)
            movs = self.env['account.move'].search([('ref', 'like', self.origin)])
            for m in movs:
                m.ref = m.ref + u' Fact ' + self.number_reem
                for line in m.line_id:
                    line.ref = m.ref

        if deduction_id:
            self.deduction_id = deduction_id
            if self.deduction_id.type == 'customer':
                self.deduction_id.number = self.deduction_id.name
        return is_ok

    @api.multi
    @api.returns('self')
    def refund(self, date=None, period_id=None, description=None, journal_id=None):
        new_invoices = self.browse()
        authorization = self.env['account.authorization'].search([('type_id.code', '=', '04')])
        for invoice in self:
            # create the new invoice
            values = self._prepare_refund(invoice, date=date, period_id=period_id,
                                          description=description, journal_id=journal_id)
            values.update({'authorization_id': authorization.id, 'is_inv_elect': True, 'is_inv_liq': True,
                           'document_type': authorization.type_id.id})
            new_invoices += self.create(values)
        return new_invoices

    @api.multi
    def action_move_create(self):
        """ Creates invoice related analytics and financial move lines """
        account_invoice_tax = self.env['account.invoice.tax']
        account_move = self.env['account.move']
        move_line = self.env['account.move.line']

        for inv in self:
            if not inv.journal_id.sequence_id:
                raise except_orm(_('Error!'), _('Please define sequence on the journal related to this invoice.'))
            if not inv.invoice_line:
                raise except_orm(_('No Invoice Lines!'), _('Please create some invoice lines.'))

            ctx = dict(self._context, lang=inv.partner_id.lang)

            if not inv.date_invoice:
                inv.with_context(ctx).write({'date_invoice': time.strftime('%Y-%m-%d')})
            date_invoice = inv.date_invoice

            company_currency = inv.company_id.currency_id
            # create the analytical lines, one move line per invoice line
            iml = inv._get_analytic_lines()
            # check if taxes are all computed
            compute_taxes = account_invoice_tax.compute(inv.with_context(lang=inv.partner_id.lang))
            inv.check_tax_lines(compute_taxes)

            # I disabled the check_total feature
            if self.env['res.users'].has_group('account.group_supplier_inv_check_total'):
                if inv.type in ('in_invoice', 'in_refund') and abs(inv.check_total - inv.amount_total) >= (inv.currency_id.rounding / 2.0):
                    raise except_orm(_('Bad Total!'), _('Please verify the price of the invoice!\nThe encoded total does not match the computed total.'))

            if inv.payment_term:
                total_fixed = total_percent = 0
                for line in inv.payment_term.line_ids:
                    if line.value == 'fixed':
                        total_fixed += line.value_amount
                    if line.value == 'procent':
                        total_percent += line.value_amount
                total_fixed = (total_fixed * 100) / (inv.amount_total or 1.0)
                if (total_fixed + total_percent) > 100:
                    raise except_orm(_('Error!'), _("Cannot create the invoice.\nThe related payment term is probably misconfigured as it gives a computed amount greater than the total invoiced amount. In order to avoid rounding issues, the latest line of your payment term must be of type 'balance'."))

            # one move line per tax line
            iml += account_invoice_tax.move_line_get(inv.id)

            if inv.type in ('in_invoice', 'in_refund'):
                ref = inv.reference
            else:
                ref = inv.number

            diff_currency = inv.currency_id != company_currency
            # create one move line for the total and possibly adjust the other lines amount
            total, total_currency, iml = inv.with_context(ctx).compute_invoice_totals(company_currency, ref, iml)

            name = inv.supplier_invoice_number or inv.name or '/'
            totlines = []
            if inv.payment_term:
                totlines = inv.with_context(ctx).payment_term.compute(total, date_invoice)[0]
            if totlines:
                res_amount_currency = total_currency
                ctx['date'] = date_invoice
                for i, t in enumerate(totlines):
                    if inv.currency_id != company_currency:
                        amount_currency = company_currency.with_context(ctx).compute(t[1], inv.currency_id)
                    else:
                        amount_currency = False

                    # last line: add the diff
                    res_amount_currency -= amount_currency or 0
                    if i + 1 == len(totlines):
                        amount_currency += res_amount_currency

                    iml.append({
                        'type': 'dest',
                        'name': name,
                        'price': t[1],
                        'account_id': inv.account_id.id,
                        'date_maturity': t[0],
                        'amount_currency': diff_currency and amount_currency,
                        'currency_id': diff_currency and inv.currency_id.id,
                        'ref': ref,
                    })
            else:
                iml.append({
                    'type': 'dest',
                    'name': name,
                    'price': total,
                    'account_id': inv.account_id.id,
                    'date_maturity': inv.date_due,
                    'amount_currency': diff_currency and total_currency,
                    'currency_id': diff_currency and inv.currency_id.id,
                    'ref': ref
                })

            date = date_invoice

            part = self.env['res.partner']._find_accounting_partner(inv.partner_id)

            line = [(0, 0, self.line_get_convert(l, part.id, date)) for l in iml]
            line = inv.group_lines(iml, line)

            journal = inv.journal_id.with_context(ctx)
            if journal.centralisation:
                raise except_orm(_('User Error!'),
                                 _('You cannot create an invoice on a centralized journal. Uncheck the centralized counterpart box in the related journal from the configuration menu.'))

            line = inv.finalize_invoice_move_lines(line)
            if not inv.move_id:
                move_vals = {
                    'ref': (inv.reference or inv.name),
                    'line_id': line,
                    'journal_id': journal.id,
                    'date': inv.date_invoice,
                    'narration': inv.comment,
                    'company_id': inv.company_id.id,
                }
                ctx['company_id'] = inv.company_id.id
                period = inv.period_id
                if not period:
                    period = period.with_context(ctx).find(date_invoice)[:1]
                if period:
                    move_vals['period_id'] = period.id
                    for i in line:
                        i[2]['period_id'] = period.id

                ctx['invoice'] = inv
                ctx_nolang = ctx.copy()
                ctx_nolang.pop('lang', None)
                move = account_move.with_context(ctx_nolang).create(move_vals)

                # make the invoice point to that move
                vals = {
                    'move_id': move.id,
                    'period_id': period.id,
                    'move_name': move.name,
                }
                inv.with_context(ctx).write(vals)
            else:
                for a, b, val in line:
                    val.update({'move_id': self.move_id.id})
                    move_line.create(val)
                    # self.move_id.post()
                    # Pass invoice in context in method post: used if you want to get the same
                    # account move reference when creating the same invoice after a cancelled one:
                    # move.post()
        self._log_event()
        return True

    def check_len(self, string, value):
        if isinstance(string, int):
            string = str(string)
        if len(string) < value:
            while len(string) < value:
                string = '0' + string
        return string

    @api.multi
    def amount_to_text(self, amount):
        return Numero_a_Texto(amount)


account_invoice()


class account_invoice_line(models.Model):
    _inherit = 'account.invoice.line'
    _description = 'Account invoice line'

    my_step = 0.0

    @api.one
    @api.depends('price_unit', 'discount', 'invoice_line_tax_id', 'quantity',
                 'product_id', 'invoice_id.partner_id', 'invoice_id.currency_id')
    def _compute_price(self):
        price = self.price_unit * (1 - (self.discount or 0.0) / 100.0)
        taxes = self.invoice_line_tax_id.compute_all(price, self.quantity, product=self.product_id, partner=self.invoice_id.partner_id)
        self.price_subtotal = taxes['total']
        if self.invoice_id:
            self.price_subtotal = self.price_subtotal

    def _get_refund(self, cr, uid, ids, name, args, context=None):
        res = {}
        for inv_line in self.browse(cr, uid, ids):
            refund = False
            if hasattr(inv_line, 'invoice_id'):
                refund = inv_line.invoice_id.type == 'out_refund' and True or False
            res[inv_line.id] = refund
        return res

    _columns = {

        'is_reemb': fields.boolean(string='Reembolsable'),
        # 'rel_price_unit': fields.function(_get_price_unit, type='float', string='Unit price', store=True),
        'rel_price_unit' : fields.char('Unit price', size=64),
        'refund' : fields.function(_get_refund, type='boolean', string='Tipo'),
        # 'reimbursement_id': fields.many2one('reimbursement', 'Reembolso de Gasto')

    }

    def default_get(self, cr, uid, fields, context=None):
        res = super(account_invoice_line, self).default_get(cr, uid, fields, context=context)
        if 'product_id' in context:
            res['rel_price_unit'] = res.get('price_unit') or 0.0
        return res

    @api.multi
    def product_id_change(self, product, uom_id, qty=0, name='', type='out_invoice',
                          partner_id=False, fposition_id=False, price_unit=False, currency_id=False,
                          company_id=None):
        if company_id == None:
            company_id = self.env.user.company_id.id
        brw_prod = self.pool.get('product.product').browse(self._cr, self._uid, product, self._context)
        if 'hr_expense_ok' in brw_prod._fields and brw_prod.hr_expense_ok:
            pass
        else:
            if brw_prod and type == 'in_invoice':
                codes = []
                for tax in brw_prod.supplier_taxes_id:
                    #CSV 08-03-2017 VALIDAR QUE SIEMPRE EXISTA UN IMPUESTO COIGO 3.. Y 5..
                    if tax.description:
                        codes.append(tax.description[0])
                if '3' not in codes:
                    mess = 'El codigo de impuesto 300 no se encuentra en el producto: %s' % brw_prod.name
                    res = {'value': {'product_id': False}, 'warning': {'title': 'Alerta', 'message': mess}}
                    return res
                if '5' not in codes:
                    mess = 'El codigo de impuesto 500 no se encuentra en el producto: %s' % brw_prod.name
                    res = {'value': {'product_id': False}, 'warning': {'title': 'Alerta', 'message': mess}}
                    return res
        res = super(account_invoice_line, self).product_id_change(product, uom_id, qty, name, type, partner_id, fposition_id, price_unit, currency_id, company_id)
        if 'value' in res and 'price_unit' in res.get('value'):
            res.get('value').update({ 'rel_price_unit': 'price_unit' in res.get('value') and \
                                                        res.get('value').get('price_unit') or 0.0})
        return res

    def create(self, cr, uid, vals, context=None):
        if 'price_unit' in vals:
            vals['rel_price_unit'] = vals.get('price_unit') or 0.0
        return super(account_invoice_line, self).create(cr, uid, vals, context=context)

    def write(self, cr, uid, ids, vals, context=None):
        if 'price_unit' in vals:
            vals['rel_price_unit'] = vals.get('price_unit') or 0.0
        return super(account_invoice_line, self).write(cr, uid, ids, vals, context=context)

account_invoice_line()

#-----------------------------------
#    AUTHORIZATION
#-----------------------------------
# class account_authorization(osv.osv):
#     _name = 'account.authorization'
#     _description = 'Account authorization'
#     my_seq = ''
#     my_num_start = ''
#     my_num_end = ''
#     my_exp_date = ''
#     my_company = ''
#     my_partner_c = ''
#     my_partner_s = ''
#     my_to_customer = ''
#     code_unique = ''
#     set_sequence = None
#     sequence_code = None
#
#     def _get_type(self, cr, uid, context=None):
#         if context is None:
#             context = {}
#         self.my_to_customer = context.get('to_customer')
#         return context.get('to_customer')
#
#     _columns = {
#
#         'name' : fields.char('Authorization number', size=128, required=True),
#         'serie_entity' : fields.char('Serie entity', size=3, required=True),
#         'serie_emission' : fields.char('Serie emission', size=3, required=True),
#         'num_start' : fields.integer('Number since', required=True),
#         'num_end' : fields.integer('Number until', required=True),
#         'num_resolution' : fields.integer('Resolution number'),
#         'expiration_date' : fields.date('Expiration date', required=True),
#         'active' : fields.boolean('Is active ?'),
#         'type_id': fields.many2one('account.invoice.document', 'Document types', required=True),
#         'partner_id' : fields.many2one('res.partner', 'Partner'),
#         'partner_id_c' : fields.many2one('res.partner', 'Customer', domain=[('customer', '=', True)]),
#         'partner_id_s' : fields.many2one('res.partner', 'Supplier'),
#         'company_id' : fields.many2one('res.company', 'Company'),
#         'sequence_id' : fields.many2one('ir.sequence', 'Secuencia'),
#         'to_customer' : fields.boolean('Is customer authorization ?'),
#         'is_retention' : fields.boolean('Is retention authorization ?'),
#         'is_electronic': fields.boolean('autorizacion elect.?')
#     #    'rel_type_retention': fields.related('type_id', 'is_retention', type='boolean', string='Relation retention'),
#
#     }
#
#     _defaults = {
#         'serie_entity': '001',
#         'serie_emission': '001',
#         'active': True,
#         'to_customer': _get_type
#     }
#
#     def onchange_type_id(self, cr, uid, ids, type_id, num_start, num_end, partner_id_c, partner_id_s, to_customer, is_retention, context):
#         res = { 'value' : {} }
#         num_start = num_start or 1
#         seq_id = False
#         set_seq = True
#         obj_seq = self.pool.get('ir.sequence')
#         obj_doc_type = self.pool.get('account.invoice.document')
#         brw_doc_type = obj_doc_type.browse(cr, uid, type_id)
#         partner_id = ''
#         if to_customer:
#             if not is_retention:
#                 partner_id = self.pool.get('res.users').browse(cr, uid, uid).company_id.partner_id.id
#             else:
#                 set_seq = False
#         else:
#             partner_id = partner_id_s
#             if not partner_id and is_retention:
#                 partner_id = self.pool.get('res.users').browse(cr, uid, uid).company_id.partner_id.id
#                 res['value'].update({'partner_id_s': partner_id})
#
#         if brw_doc_type:
#             seq_code = (brw_doc_type.code + ' - ' + brw_doc_type.name).encode('utf-8')
#             seq_id = obj_seq.search(cr, uid, [('name', '=', seq_code), ('partner_id', '=', partner_id)])
#             code_unique = (str(partner_id).encode('utf-8') + ' - ' + str(num_end).encode('utf-8') + ' - ' + seq_code)[:60]
#
#             if seq_id and set_seq:
#                 seq_id = seq_id[0]
#                 read_seq = obj_seq.read(cr, uid, seq_id, ['number_next'])
#                 res.get('value').update({
#                     'num_start' : read_seq.get('number_next'),
#                     'num_end' : read_seq.get('number_next'),
#                 })
#                 self.my_num_start = read_seq.get('number_next')
#                 self.my_num_end = read_seq.get('number_next')
#             else:
#                 if 'search_doc_type' in context and context.get('search_doc_type'):
#                     if num_start == 0 or num_end == 0 or num_end < num_start:
#                         return {'value': { 'type_id' : '', 'sequence_id' : '' },
#                                 'warning':{ 'title': '¡¡ Alerta !!',
#                                             'message': _('No se ha definido correctamente el "número desde" o el "número hasta". ' \
#                                                          'Ambos deben ser mayor que cero y "número desde" menor que "número hasta"')
#                                             }}
#                 # if set_seq:
#                 #     code_id = obj_seq_type.search(cr, uid, [('code', '=', code_unique)])
#                 #     if not code_id:
#                 #         vals_code =  {
#                 #             'code': code_unique,
#                 #             'name': seq_code,
#                 #         }
#                 #         code_id = obj_seq_type.create(cr, uid, vals_code)
#                 #     vals_seq =  {
#                 #         'name': seq_code,
#                 #         'padding': len(str(num_end)) or 3,
#                 #         'partner_id': partner_id,
#                 #         'number_next': int(num_start)
#                 #     }
#                 #     seq_id = obj_seq.create(cr, uid, vals_seq)
#
#                 #            code_unique = str(code_unique).encode('utf-8')
#             self.code_unique = code_unique
#             self.sequence_code = seq_code
#             if set_seq:
#                 self.my_seq = seq_id
#                 res.get('value').update({'sequence_id': seq_id})
#                 # cr.execute('update ir_sequence set code=%s where id=%s', (code_unique, seq_id))
#                 # obj_seq.write(cr, uid, seq_id, { 'number_next' : num_start }, context=context)
#         return res
#
#     def onchange_partner_id(self, cr, uid, ids, to_customer, partner_id_c, partner_id_s, is_retention, context=None):
#         if context is None:
#            context = {}
#         res = { 'value' : {} }
#         brw_user = self.pool.get('res.users').browse(cr, uid, uid)
#         res['value']['company_id'] = brw_user.company_id.id
#         self.my_company = brw_user.company_id.id
# #        self.my_partner = partner_id
#         obj_partner = self.pool.get('res.partner')
#         if to_customer:
#             if not is_retention:
#                 res['value']['partner_id'] = ''
#                 res['value']['type_id'] = ''
#         else:
#             # Agrego el valor al result
#             if partner_id_s:
#                 if not is_retention:
#                     read_partner_s = obj_partner.read(cr, uid, partner_id_s, ['document_type'])    # ID Document type
#                     self.my_partner_s = partner_id_s
#                     if read_partner_s.get('document_type'):
#                         res['value']['type_id'] = read_partner_s.get('document_type')[0]
#         if is_retention:
#             res['value']['partner_id_s'] = brw_user.company_id.partner_id.id
#         return res
#
#     def onchange_expiration_date(self, cr, uid, ids, expiration_date, num_start, num_end, context=None):
#         if context is None:
#             context = self.pool['res.users'].context_get(cr, uid)
#         if expiration_date:
#             formato_fecha = "%Y-%m-%d"
#             exp_date = datetime.strptime(expiration_date, formato_fecha).date()
#             now = datetime.today().date()
#             if exp_date and now:
#                 if exp_date < now:
#                     return { 'value' : { 'expiration_date' : '' },
#                              'warning':{'title': "Error", "message": "La fecha vigencia debe ser mayor que la fecha de hoy"}}
#             self.my_exp_date = expiration_date
#         if num_start: self.my_num_start = num_start
#         if num_end: self.my_num_end = num_end
#
#         return { 'value' : { 'expiration_date' : expiration_date } }
#
#     #
#     def create(self, cr, uid, vals, context=None):
#         auth_ids = []
#         partner = False
#         if vals['partner_id_s']:
#             partner = vals['partner_id_s']
#         else:
#             if vals['partner_id_c']:
#                 partner = vals['partner_id_c']
#         vals['partner_id'] = partner
#         if 'sequence_id' not in vals or ('sequence_id' in vals and not vals['sequence_id']):
#             obj_seq_type = self.pool.get('ir.sequence.type')
#             doc_type_obj = self.pool.get('account.invoice.document').browse(cr, uid, vals['type_id'])
#             code_id = obj_seq_type.search(cr, uid, [('code', '=', doc_type_obj.name)])
#             seq_type = obj_seq_type.browse(cr, uid, code_id)
#             if not code_id:
#                 vals_code = {
#                     'code': doc_type_obj.name,
#                     'name': doc_type_obj.name,
#                 }
#                 seq_type = obj_seq_type.browse(cr, uid, obj_seq_type.create(cr, uid, vals_code))
#             # if self.my_seq:
#             #     vals['sequence_id'] = self.my_seq
#             #     self.pool.get('ir.sequence').write(cr, uid, self.my_seq, {'code': self.code_unique[:32], 'number_next': vals['num_start']})
#             # else:
#             company = self.pool.get('res.users').browse(cr, uid, uid).company_id
#             if not partner:
#                 partner = company.partner_id.id
#             vals_seq = {
#                 'name': seq_type.code,
#                 'padding': len(str(vals['num_end'])) or 3,
#                 'partner_id': partner,
#                 'number_next': int(vals['num_start']),
#                 'code': seq_type.code,
#             }
#             seq_id = self.pool.get('ir.sequence').create(cr, uid, vals_seq)
#             vals['sequence_id'] = seq_id
#
#         if self.my_exp_date: vals['expiration_date'] = self.my_exp_date
#         if self.my_num_start: vals['num_start'] = self.my_num_start
#         if self.my_num_end: vals['num_end'] = self.my_num_end
#         if self.my_company: vals['company_id'] = self.my_company
#         if self.my_partner_c:
#             vals['partner_id_c'] = self.my_partner_c
#             vals['partner_id'] = self.my_partner_c
#         if self.my_partner_s:
#             vals['partner_id_s'] = self.my_partner_s
#             vals['partner_id'] = self.my_partner_s
#         company = self.pool.get('res.company').browse(cr, uid, vals.get('company_id'), context)
#         doc_type = self.pool.get('account.invoice.document').browse(cr, uid, vals.get('type_id'), context)
#         if doc_type.is_liquidation:
#             vals['partner_id'] = company.partner_id.id
#         if self.my_to_customer != '': vals['to_customer'] = self.my_to_customer
#
#         if 'to_customer' in vals and vals.get('to_customer'):
#             if 'is_retention' in vals and vals.get('is_retention'):
#                 args = [('partner_id_c', '=', self.my_partner_c), ('type_id', '=', vals.get('type_id'))]
#             else:
#                 if self.my_company:
#                     brw_company = self.pool.get('res.company').browse(cr, uid, self.my_company, context=context)
#                     vals['partner_id'] = brw_company.partner_id.id
#                 args = [('partner_id', '=', vals.get('partner_id')), ('company_id', '=', self.my_company), ('type_id', '=', vals.get('type_id')), ('serie_emission', '=', vals.get('serie_emission'))]
#
#             auth_ids = self.search(cr, uid, args)
#             msg = _('No puede registrar una nueva autorización para este Cliente/Proveedor con tipo de documento, debido a que tiene una autorización vigente. Debe al menos modificar la serie de emisión.')
#         elif 'to_customer' in vals and not vals.get('to_customer'):
#             if 'is_retention' in vals and vals.get('is_retention'):
#                 if self.my_company:
#                     brw_company = self.pool.get('res.company').browse(cr, uid, self.my_company, context=context)
#                     vals['partner_id'] = brw_company.partner_id.id
#                 args = [('partner_id', '=', vals.get('partner_id')), ('company_id', '=', self.my_company), ('type_id', '=', vals.get('type_id')), ('serie_emission', '=', vals.get('serie_emission'))]
#             else:
#                 args = [('partner_id_s', '=', self.my_partner_s), ('type_id', '=', vals.get('type_id')), ('serie_emission', '=', vals.get('serie_emission'))]
#             auth_ids = self.search(cr, uid, args)
#             msg = _('No puede registrar una nueva autorización con este tipo de documento para su compañía, debido a que tiene una autorización vigente.')
#
#         if auth_ids and not vals['is_electronic']:
#             raise osv.except_osv(_('¡¡ Error !!'), msg)
#
#         if vals.get('num_end') < vals.get('num_start') or vals.get('num_start') == 0 or vals.get('num_end') == 0:
#             raise osv.except_osv(_('¡¡ Error !!'), _('No se ha definido correctamente el "número desde" o el "número hasta". ' \
#                                                      'Ambos deben ser mayor que cero y "número desde" menor que "número hasta"'))
#         if vals.get('sequence_id') and not vals['is_retention']:
#             self.pool.get('ir.sequence').write(cr, uid, vals.get('sequence_id'), { 'number_next' : vals.get('num_start') }, context=context)
#         return super(account_authorization, self).create(cr, uid, vals, context=context)
#
# account_authorization()

#----------------------------------------------------------
#    INVOICE TAX
#----------------------------------------------------------
class account_invoice_tax(osv.osv):
    _inherit = 'account.invoice.tax'
    _description = 'Account invoice tax'

    def _get_taxes(self, cr, uid, ids, name, args, context=None):
        # Busco los valores para la localización del ecuador
        res = {}
        dicc_type = { 'ret_iva': 'Ret. IVA', 'ret_fte': 'Ret. Renta' }
        for tax in self.browse(cr, uid, ids, context):
            temp_res = self.cruzarTax(tax)
            print "temp_res: " , temp_res
            dicc_temp = temp_res.get(tax.id)
            print 'TEMP RES ', temp_res, '------------------------'
            print 'dicc_temp: ', dicc_temp
            number = 'number' in dicc_temp and dicc_temp.get('number') or 'N/D'
            print 'number: ', number
            percent = 'amount' in dicc_temp and dicc_temp.get('amount') or '0.0'
            tax_type = 'type' in dicc_temp and dicc_temp.get('type') or False
            tax_type = tax_type and dicc_type.get(tax_type) or 'N/D'
            if abs(float(percent)) == 0.001:
                percent *= 10
            #             print 'IMPRIMIR ', tax, '------------------------'
            res[tax.id] = { 'tax_number': int(number),
                            'tax_percent': str(int(abs(float(percent) * 100))) + ' %',
                            'tax_type': tax_type }
            print 'RESULTADO', res
        return res

    _columns = {

        'deduction_id' : fields.many2one('account.deduction', 'Deduction'),
        'tax_number': fields.function(_get_taxes, type='char', string='Tax number', multi='all'),
        'tax_percent': fields.function(_get_taxes, type='char', string='Tax percent', multi='all'),
        'tax_type': fields.function(_get_taxes, type='char', string='Tax type', multi='all'),

    }

    def cruzarTax(self, tax_inv):
        dicc_Taxes = {}

        tmp_tax_inv = {
            'tax_code_id': tax_inv.tax_code_id.id,
            'base_code_id': tax_inv.base_code_id.id
        }

        _type = False
        l_tax_deduc = []
        for line in tax_inv.invoice_id.invoice_line:
            for tax_line in line.invoice_line_tax_id:
                percent = 0
                tmp_tax_line = {}
                if tax_line.child_depend:
                    for child in tax_line.child_ids:
                        child_tax_line = {
                            'tax_code_id': child.tax_code_id.id,
                            'base_code_id': child.base_code_id.id
                        }
                        if child_tax_line == tmp_tax_inv:
                            return { tax_inv.id: {
                                'type': 'ret_iva',
                                'amount': float(child.amount),
                                'number': child.description } }
                else:
                    tmp_tax_line =  {
                        'tax_code_id': tax_line.tax_code_id.id,
                        'base_code_id': tax_line.base_code_id.id
                    }
                    if not tax_line.is_iva:
                        if tmp_tax_line == tmp_tax_inv:
                            return { tax_inv.id: {
                                'type': 'ret_fte',
                                'amount': float(tax_line.amount),
                                'number': tax_line.description } }
        print 'Probando lo que devuelve', dicc_Taxes
        return dicc_Taxes

account_invoice_tax()

#----------------------------------------------------------
#    DEDUCTIONS
#----------------------------------------------------------
class account_deduction(osv.osv):
    _name = 'account.deduction'
    _description = 'Account deduction'
    # _rec_name = 'number'

    def name_get(self, cr, uid, ids, context=None):
        res = []
        for rec in self.browse(cr, uid, ids, context=context):
            name = rec.number
            if rec.type == 'supplier':
                name = str(rec.authorization_id.serie_entity) + '-' + str(rec.authorization_id.serie_emission) + '-' + str(rec.number)
            res.append((rec.id, name))
        return res

    _columns = {

        'name' : fields.char('Retention', size=128, required=True),
        'auth_customer' : fields.char('Customer authorization', size=64, required=False),
        'authorization_id' : fields.many2one('account.authorization', 'Retentions authorization', required=False),
        'number' : fields.char('Retention number', size=128),
        'type':fields.selection([
            ('customer', 'Customer retention'),
            ('supplier', 'Supplier retention'),
        ],'Type'),
        'partner_id' : fields.many2one('res.partner', 'Partner'),
        'emission_date' : fields.date('Emission date'),
        'invoice_id' : fields.many2one('account.invoice', 'Account invoice'),
        'tax_ids': fields.one2many('account.invoice.tax', 'deduction_id', 'Taxes'),
        'company_id': fields.related('invoice_id', 'company_id', type='many2one', relation='res.company', string='Company', store=True),
        'state': fields.selection([
            ('draft','Draft'),
            ('open','Open'),
            ('paid','Paid'),
            ('cancel','Cancelled'),
        ],'Status', select=True, readonly=True, track_visibility='onchange'),
        'retention_type': fields.selection([('Manual', 'Manual'), ('Electronica', 'Electronica')], 'Tipo de Ret.'),

    }

    def default_get(self, cr, uid, fields, context=None):
        if context is None:
            context = {}
        res = super(account_deduction, self).default_get(cr, uid, fields, context=context)
        seq_id = self.pool.get('ir.sequence').search(cr, uid, [('code', '=', 'account.receivable.deduction')])
        number = self.pool.get('ir.sequence')._next(cr, uid, seq_id, context)
        res['name'] = number
        return res

    def create(self, cr, uid, vals, context=None):
        if vals.get('name','/') == '/':
            vals['name'] = self.pool.get('ir.sequence').get(cr, uid, 'account.receivable.deduction') or '/'
            # invoice = self.pool.get('account.invoice').browse(cr, uid, vals['invoice_id'])
            # if invoice.amount_other < 0.00 and vals['type'] == 'supplier':
            #     seq_id = self.pool.get('ir.sequence').search(cr, uid, [('code', '=', 'account.receivable.deduction')])
            #     number = self.pool.get('ir.sequence')._next(cr, uid, seq_id, context)
            #     vals['number'] = number
            # Llamo al super y obtengo el id
        res = super(account_deduction, self).create(cr, uid, vals, context=context)
        return res

    def wkf_draft(self, cr, uid, ids,context=None):
        self.write(cr, uid, ids, { 'state' : 'draft' })
        return True

    def wkf_open(self, cr, uid, ids,context=None):
        self.write(cr, uid, ids, { 'state' : 'open' })
        return True

    def wkf_paid(self, cr, uid, ids,context=None):
        self.write(cr, uid, ids, { 'state' : 'paid' })
        return True

    def wkf_cancel(self, cr, uid, ids,context=None):
        if context is None:
            context = {}
        # brw_deduction = self.browse(cr, uid, ids, context=context)
        # if ids and brw_deduction.invoice_id.type == 'in_invoice':
        #     seq_id = brw_deduction.authorization_id.sequence_id.id
        #     number = self.pool.get('ir.sequence').browse(cr, uid, seq_id).number_next
        #     values =  { 'number': number }
        #     id = type(ids) == type([]) and ids[0] or ids
        #     self.copy(cr, uid, id, values, context=context)
        #     self.pool.get('ir.sequence').write(cr, uid, seq_id, { 'number_next': int(number) + 1 })

        self.write(cr, uid, ids, { 'state' : 'draft' })
        return True

    def wkf_cancel1(self, cr, uid, ids,context=None):
        if context is None:
            context = {}
        # brw_deduction = self.browse(cr, uid, ids, context=context)
        # if ids and brw_deduction.invoice_id.type == 'in_invoice':
        #     seq_id = brw_deduction.authorization_id.sequence_id.id
        #     number = self.pool.get('ir.sequence').browse(cr, uid, seq_id).number_next
        #     values =  { 'number': number }
        #     id = type(ids) == type([]) and ids[0] or ids
        #     self.copy(cr, uid, id, values, context=context)
        #     self.pool.get('ir.sequence').write(cr, uid, seq_id, { 'number_next': int(number) + 1 })

        self.write(cr, uid, ids, { 'state' : 'cancel' })
        return True

    def get_taxes(self, cr, uid, t_id):
        print "ID******************************", t_id
        cod_imp = []
        res = []
        cont = 0
        impuesto_ids = self.pool.get('account.deduction').search(cr, uid, [('id', '=', t_id)])
        print "impuesto_ids: ", impuesto_ids
        obj_retencion = self.pool.get('account.deduction').browse(cr, uid, impuesto_ids)
        print "obj_retencion.tax_ids: ", obj_retencion.tax_ids
        for imp in obj_retencion.tax_ids:
            if cont == 0:
                tn = imp.tax_number
                if tn  in ('332', '507'):
                    continue
                print "TAX NUMBER", tn
                cod_imp.append(tn)
                if imp:
                    tax_number = imp.tax_number
                    base = round(imp.base, 2)
                    tax_type = imp.tax_type
                    tax_percent = imp.tax_percent
                    amount = abs(round(imp.amount, 2))
                else:
                    tax_number = ''
                    base = ''
                    tax_type = ''
                    tax_percent = ''
                    amount = ''
                val1 = {'tax_number': tax_number,
                        'base': base,
                        'tax_type': tax_type,
                        'tax_percent': tax_percent,
                        'amount': amount,
                        }
                res.append(val1)
                cont = 1

            elif cont == 1:
                band = 0
                tn = imp.tax_number
                if tn  in ('332', '507'):
                    continue
                for recorre in cod_imp:
                    print "RECORRE IMP", str(recorre) +" "+"CODE"+" "+str(imp.tax_number)
                    if recorre == imp.tax_number:
                        for rec_old in res:
                            print "ACTUALIZO EL REGISTRO", rec_old
                            if rec_old.get('tax_number') == imp.tax_number:
                                print "actualizo"
                                base_ant = rec_old.get('base')
                                amount_ant = rec_old.get('amount')
                                base_new = float(base_ant) + float(imp.base)
                                amount_new = float(amount_ant) + float(abs(imp.amount))
                                rec_old['base'] = round(base_new, 2)
                                rec_old['amount'] = round(amount_new, 2)
                            else:
                                continue
                        band = 1
                if band != 1:
                    cod_imp.append(imp.tax_number)
                    if imp:
                        tax_number = imp.tax_number
                        base = round(imp.base, 2)
                        tax_type = imp.tax_type
                        tax_percent = imp.tax_percent
                        amount = abs(round(imp.amount, 2))
                    else:
                        tax_number = ''
                        base = ''
                        tax_type = ''
                        tax_percent = ''
                        amount = ''
                    val1 = {'tax_number': tax_number,
                            'base': base,
                            'tax_type': tax_type,
                            'tax_percent': tax_percent,
                            'amount': amount,
                            }
                    res.append(val1)
        print "DIC FINAL IMP", res
        print "LISTA FINAL IMP", cod_imp
        return res

    def reconcile_deduction(self, cr, uid, ids,context=None):
        print "reconcile deduction"
        if context is None:
            context = {}
        move_line = self.pool.get('account.move.line')
        for rec in self.browse(cr, uid, ids, context=context):
            if not rec.move_id:
                return {'warning':{
                    'title': 'Advertencia!','message': 'La retención no tiene un asiento contable asociado',
                }
                }
            if not (rec.invoice_id and rec.invoice_id.move_id):
                return {'warning': {
                    'title': 'Advertencia!',
                    'message': 'La Factura no tiene un asiento contable asociado',
                }
                }
            # busco move_lines que coincidan con cuentas y reconcilio:
            conciliado = False
            for deduction_move_line in rec.move_id.line_id:
                if not deduction_move_line.reconcile_partial_id:
                    for invoice_move_line in rec.invoice_id.move_id.line_id :
                        if (deduction_move_line.account_id.id == invoice_move_line.account_id.id):
                            move_line.reconcile_partial(cr, uid, [deduction_move_line.id,invoice_move_line.id], 'manual',context=context)
                            conciliado = True
                else:
                    conciliado = True
            if conciliado:
                rec.wkf_paid()
        return True

account_deduction()



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

