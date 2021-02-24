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

from openerp.osv import fields, osv
from openerp.tools.translate import _

class sale_group_invoice(osv.osv_memory):
    _name = "sale.group.invoice"
    _description = "Sales Group Invoice"
    _columns = {
        # 'grouped': fields.boolean('Group the invoices', help='Check the box to group the invoices for the same customers'),
        'invoice_date': fields.date('Invoice Date'),
    }
    _defaults = {
        # 'grouped': False,
        'invoice_date': fields.date.context_today,
    }

    def view_init(self, cr, uid, fields_list, context=None):
        if context is None:
            context = {}
        record_id = context and context.get('active_ids', False)
        invoices_list = self.pool.get('account.invoice').browse(cr, uid, record_id, context=context)
        partner_id = False
        contract = False
        for invoice in invoices_list:
            if invoice.partner_id !=  partner_id and partner_id != False:
                raise osv.except_osv(_('Error!'), _('Facturas no corresponden al mismo clientes.'))
            if invoice.state != 'draft' or  invoice.state_provision == 'prov':
                raise osv.except_osv(_('Error!'), _('No se pueden agrupar facturas en estado. ' + invoice.state + ' estado de provision ' + invoice.state_provision))
            for contr in invoice.ticket_ids:
                if contr.contract_id != contract and contract != False:
                    raise osv.except_osv(_('Error!'), _('No se pueden agrupar facturas de contratos diferentes. '+ invoice.state))
                contract = contr.contract_id
            partner_id = invoice.partner_id

        return False

    def group_invoices(self, cr, uid, ids, context=None):
        record_id = context and context.get('active_ids', False)
        invoices_list = self.pool.get('account.invoice').browse(cr, uid, record_id, context=context)

        inv_ref = self.pool.get('account.invoice')
        inv_line_ref = self.pool.get('account.invoice.line')

        invoice_id = False
        number_rem = 'FACT: '
        data = self.read(cr, uid, ids)[0]
        linesinvoice = []
        ticket = []


        for invoice in invoices_list:
            acc = invoice.partner_id.property_account_receivable.id
            # if invoice.origin:
            #     number_rem = number_rem + ' - ' + invoice.origin #number_reem
            if invoice.ticket_ids:
                for tickinv in invoice.ticket_ids:
                    number_rem = number_rem + ' - ' + tickinv.name
                    ticket.append(tickinv.id)
            else:
                number_rem = number_rem + ' - ' + invoice.origin

            if invoice_id == False:
                inv = {
                    'date_invoice': data['invoice_date'],
                    'name': number_rem,
                    'origin':number_rem , #  'AGRUPACION FACTURAS',
                    'account_id': invoice.account_id.id,
                    'journal_id': invoice.journal_id.id or None,
                    'type': 'out_invoice',
                    'reference': 'AGRUPACION FACTURAS',
                    'partner_id': invoice.partner_id.id,
                    'comment': '',
                    'fiscal_position': False,
                    'currency_id': invoice.currency_id.id, # considering partner's sale pricelist's currency
                    'oc': invoice.oc,
                    'oet': invoice.oet,
                    'pre_invoice': invoice.pre_invoice,
                    'ticket_ids': [[6, 0, ticket]],
                }
                invoice_id = inv_ref.create(cr, uid, inv, context=context)
            else:
                inv_ref.write(cr, uid, [invoice_id], {'name': number_rem, 'ticket_ids': [[6, 0, ticket]], 'origin':number_rem}, context=context)
            self.pool.get('account.invoice').write(cr, uid, [invoice.id],{'state': 'grouped','invoice_grouped':invoice_id})

            #Inserta Lineas Factura - Agrupa
            line_list_ids = self.pool.get('account.invoice.line').search(cr, uid, [('invoice_id','=', invoice.id)], context=context)
            line_list = self.pool.get('account.invoice.line').browse(cr, uid, line_list_ids, context=context)

            for line in line_list:
                count = 0
                if len(linesinvoice) == 0:
                    inv_line = {
                        'invoice_id': invoice_id,
                        'product_id': line.product_id.id,
                        'quantity': line.quantity,
                        'account_analytic_id': line.account_analytic_id,
                    }
                    inv_line.update(inv_line_ref.product_id_change(cr, uid, [],
                                                                   line.product_id.id,
                                                                   line.product_id.uom_id.id,
                                                                   line.quantity, partner_id = invoice.partner_id.id)['value'])

                    inv_line['price_unit'] = line.price_unit
                    inv_line['discount'] = line.discount
                    inv_line['name'] = line.name
                    inv_line['account_id'] = line.account_id.id
                    # inv_line['invoice_line_tax_id'] = [(6, 0, inv_line['invoice_line_tax_id'])]
                    # invoiceline_id = inv_line_ref.create(cr, uid, inv_line, context=context)
                    linesinvoice.append(inv_line)
                else:
                    for invlist in linesinvoice:
                        if invlist.get('product_id') == line.product_id.id:
                            invlist['quantity'] =  invlist['quantity'] + line.quantity
                            count = 1
                    if count == 0:
                        inv_line = {
                            'invoice_id': invoice_id,
                            'product_id': line.product_id.id,
                            'quantity': line.quantity,
                            'account_analytic_id': line.account_analytic_id,
                        }
                        inv_line.update(inv_line_ref.product_id_change(cr, uid, [],
                                                                       line.product_id.id,
                                                                       line.product_id.uom_id.id,
                                                                       line.quantity, partner_id = invoice.partner_id.id)['value'])
                        inv_line['price_unit'] = line.price_unit
                        inv_line['discount'] = line.discount
                        inv_line['name'] = line.name
                        inv_line['account_id'] = line.account_id.id
                        linesinvoice.append(inv_line)
                        # inv_line['invoice_line_tax_id'] = [(6, 0, [x.id for x in line.product_id.taxes_id] )]

        # inv_ref.button_reset_taxes(cr, uid, [invoice_id], context=context)

        for lines in linesinvoice:
            inv_line_ref.create(cr, uid, lines, context=context)

        # if not inv_ids: return {}

        mod_obj = self.pool.get('ir.model.data')
        res = mod_obj.get_object_reference(cr, uid, 'account', 'invoice_form')
        res_id = res and res[1] or False
        return {
            'name': _('Customer Invoice'),
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': [res_id],
            'res_model': 'account.invoice',
            'context': "{'type':'out_invoice'}",
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
            'res_id': invoice_id or False,
        }
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
