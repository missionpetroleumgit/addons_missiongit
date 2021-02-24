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

from openerp.tools.translate import _
from openerp.osv import fields, osv
from openerp import api


class account_move(osv.osv):
    _inherit = 'account.move'

    _columns = {
        'group_report_by_account': fields.boolean('agrupar cuantas en reporte?'),
        #CSV:25-06-2018: AÑADO PARA MARCAR LOS ASIENTOS DIRECTOS PARA QUE BAJEN LAS LINEAS A LA CONCILIACIÓN
        'is_conci_direct': fields.boolean('Conciliar directo', help='Marcar si es un asiento directo y queremos que se muestre en la conciliacion'),
    }

    def group_accounts(self, cr, uid, line_id):
        res = {}
        result = []
        for line in line_id:
            if line.account_id.id not in res:
                res[line.account_id.id] = {'partner_id': line.partner_id.name, 'account_id': line.account_id.code + '  ' + line.account_id.name,
                                           'debit': line.debit, 'credit': line.credit}
            else:
                res[line.account_id.id]['debit'] += line.debit
                res[line.account_id.id]['credit'] += line.credit
        for key, value in res.items():
            result.append(value)
        return result

    def post(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        invoice = context.get('invoice', False)
        valid_moves = self.validate(cr, uid, ids, context)

        if not valid_moves:
            raise osv.except_osv(_('Error!'), _('You cannot validate a non-balanced entry.\nMake sure you have configured payment terms properly.\nThe latest payment term line should be of the "Balance" type.'))
        obj_sequence = self.pool.get('ir.sequence')
        for move in self.browse(cr, uid, valid_moves, context=context):
            if move.name == '/':
                journal = move.journal_id
                if journal.sequence_id:
                    c = {'fiscalyear_id': move.period_id.fiscalyear_id.id}
                    new_name = obj_sequence.next_by_id(cr, uid, journal.sequence_id.id, c)
                else:
                    raise osv.except_osv(_('Error!'), _('Please define a sequence on the journal.'))

                if new_name:
                    self.write(cr, uid, [move.id], {'name':new_name})

        cr.execute('UPDATE account_move '\
                   'SET state=%s '\
                   'WHERE id IN %s',
                   ('posted', tuple(valid_moves),))
        self.invalidate_cache(cr, uid, context=context)
        return True

account_move()


class account_tax(osv.osv):
    """
    A tax object.

    Type: percent, fixed, none, code
        PERCENT: tax = price * amount
        FIXED: tax = price + amount
        NONE: no tax line
        CODE: execute python code. localcontext = {'price_unit':pu}
            return result in the context
            Ex: result=round(price_unit*0.21,4)
    """
    
    _inherit = 'account.tax'
    _description = 'Tax'
    _columns = {
         
        'name': fields.text('Tax Name', required=True),       
        #'name': fields.char('Tax Name', size=254, required=True, translate=False, help="This name will be displayed on reports."),
        'is_iva':fields.boolean('Is the IVA tax ?', help="Only will be used when be the IVA tax."),
        'string_percent': fields.char('Descripcion', size=20)

    }
    _order = 'is_iva asc, sequence asc'
    
# NAME GET
    def name_get(self, cr, uid, ids, context=None):
        
        reads = self.read(cr, uid, ids, ['name','description', 'string_percent'], context=context)
        res = []
        for record in reads:
            name = record['description']
            if record['string_percent']:
                name += ' ' + record['string_percent']
            if not record['description']:
                name = record['name']
            res.append((record['id'], name))
        return res
    
# SEARCH
    def search(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=False):
        if context is None:
            context = {}
        order='sequence'
        if 'type_tax_use' in context:
            args += [('type_tax_use', '=', context.get('type_tax_use')), ('parent_id', '=', False)]
        return super(account_tax, self).search(cr, uid, args, offset=offset, limit=limit, order=order, context=context, count=count)

    @api.v7
    def compute_all(self, cr, uid, taxes, price_unit, quantity, product=None, partner=None, force_excluded=False):
        """
        :param force_excluded: boolean used to say that we don't want to consider the value of field price_include of
            tax. It's used in encoding by line where you don't matter if you encoded a tax with that boolean to True or
            False
        RETURN: {
                'total': 0.0,                # Total without taxes
                'total_included: 0.0,        # Total with taxes
                'taxes': []                  # List of taxes, see compute for the format
            }
        """

        # By default, for each tax, tax amount will first be computed
        # and rounded at the 'Account' decimal precision for each
        # PO/SO/invoice line and then these rounded amounts will be
        # summed, leading to the total amount for that tax. But, if the
        # company has tax_calculation_rounding_method = round_globally,
        # we still follow the same method, but we use a much larger
        # precision when we round the tax amount for each line (we use
        # the 'Account' decimal precision + 5), and that way it's like
        # rounding after the sum of the tax amounts of each line
        precision = 4
        tax_compute_precision = precision
        if taxes and taxes[0].company_id.tax_calculation_rounding_method == 'round_globally':
            tax_compute_precision += 5
        totalin = totalex = round(price_unit * quantity, precision)
        tin = []
        tex = []
        for tax in taxes:
            if not tax.price_include or force_excluded:
                tex.append(tax)
            else:
                tin.append(tax)
        tin = self.compute_inv(cr, uid, tin, price_unit, quantity, product=product, partner=partner, precision=tax_compute_precision)
        for r in tin:
            totalex -= r.get('amount', 0.0)
        totlex_qty = 0.0
        try:
            totlex_qty = totalex/quantity
        except:
            pass
        tex = self._compute(cr, uid, tex, totlex_qty, quantity, product=product, partner=partner, precision=tax_compute_precision)
        for r in tex:
            totalin += r.get('amount', 0.0)
        return {
            'total': totalex,
            'total_included': totalin,
            'taxes': tin + tex
        }

    @api.v8
    def compute_all(self, price_unit, quantity, product=None, partner=None, force_excluded=False):
        return self._model.compute_all(
            self._cr, self._uid, self, price_unit, quantity,
            product=product, partner=partner, force_excluded=force_excluded)

account_tax()


#----------------------------------------------------------
# Tax Code
#----------------------------------------------------------
"""
a documenter
child_depend: la taxe depend des taxes filles
"""
class account_tax_code(osv.osv):
    """
    A code for the tax object.

    This code is used for some tax declarations.
    """
    
    _inherit = 'account.tax.code'
    _description = 'Tax Code'
    _rec_name = 'code'

    def _sum2(self, cr, uid, ids, name, args, context, where ='', where_params=(), debit=False):
        parent_ids = tuple(self.search(cr, uid, [('parent_id', 'child_of', ids)]))
        if debit:
            if context.get('based_on', 'invoices') == 'payments':
                cr.execute('SELECT line.tax_code_id, sum(line.debit) \
                        FROM account_move_line AS line, \
                            account_move AS move \
                            LEFT JOIN account_invoice invoice ON \
                                (invoice.move_id = move.id) \
                        WHERE line.tax_code_id IN %s '+where+' \
                            AND move.id = line.move_id \
                            AND ((invoice.state = \'paid\') \
                                OR (invoice.id IS NULL)) \
                                GROUP BY line.tax_code_id',
                           (parent_ids,) + where_params)
            else:
                cr.execute('SELECT line.tax_code_id, sum(line.debit) \
                        FROM account_move_line AS line, \
                        account_move AS move \
                        WHERE line.tax_code_id IN %s '+where+' \
                        AND move.id = line.move_id \
                        GROUP BY line.tax_code_id',
                           (parent_ids,) + where_params)
        else:
            if context.get('based_on', 'invoices') == 'payments':
                cr.execute('SELECT line.tax_code_id, sum(line.credit) \
                        FROM account_move_line AS line, \
                            account_move AS move \
                            LEFT JOIN account_invoice invoice ON \
                                (invoice.move_id = move.id) \
                        WHERE line.tax_code_id IN %s '+where+' \
                            AND move.id = line.move_id \
                            AND ((invoice.state = \'paid\') \
                                OR (invoice.id IS NULL)) \
                                GROUP BY line.tax_code_id',
                           (parent_ids,) + where_params)
            else:
                cr.execute('SELECT line.tax_code_id, sum(line.credit) \
                        FROM account_move_line AS line, \
                        account_move AS move \
                        WHERE line.tax_code_id IN %s '+where+' \
                        AND move.id = line.move_id \
                        GROUP BY line.tax_code_id',
                           (parent_ids,) + where_params)
        res=dict(cr.fetchall())
        obj_precision = self.pool.get('decimal.precision')
        res2 = {}
        for record in self.browse(cr, uid, ids, context=context):
            def _rec_get(record):
                amount = res.get(record.id) or 0.0
                for rec in record.child_ids:
                    amount += _rec_get(rec) * rec.sign
                return amount
            res2[record.id] = round(_rec_get(record), obj_precision.precision_get(cr, uid, 'Account'))
        return res2

    def _sum_debit(self, cr, uid, ids, name, args, context):
        if context is None:
            context = {}
        if 280 in ids:
            pass
        move_state = ('posted', )
        if context.get('state', False) == 'all':
            move_state = ('draft', 'posted', )
        if context.get('period_id', False):
            period_id = context['period_id']
        else:
            period_id = self.pool.get('account.period').find(cr, uid, context=context)
            if not period_id:
                return dict.fromkeys(ids, 0.0)
            period_id = period_id[0]
        return self._sum2(cr, uid, ids, name, args, context,
                          where=' AND line.period_id=%s AND move.state IN %s', where_params=(period_id, move_state), debit=True)

    def _sum_credit(self, cr, uid, ids, name, args, context):
        if context is None:
            context = {}
        if 280 in ids:
            pass
        move_state = ('posted', )
        if context.get('state', False) == 'all':
            move_state = ('draft', 'posted', )
        if context.get('period_id', False):
            period_id = context['period_id']
        else:
            period_id = self.pool.get('account.period').find(cr, uid, context=context)
            if not period_id:
                return dict.fromkeys(ids, 0.0)
            period_id = period_id[0]
        return self._sum2(cr, uid, ids, name, args, context,
                          where=' AND line.period_id=%s AND move.state IN %s', where_params=(period_id, move_state), debit=False)

    _columns = {
                
        'name': fields.char('Tax Case Name', size=255, required=True, translate=True),
        'form': fields.char('Form', size=4, help="DIMM Form"),
        'debit': fields.function(_sum_debit, string="Debito"),
        'credit': fields.function(_sum_credit, string="Credito")
        
    }

account_tax_code()

#----------------------------------------------------------
# Document
#----------------------------------------------------------
class account_invoice_document(osv.osv):
    """
    This document is used in the invoice.
    """
    
    _name = 'account.invoice.document'
    _description = 'Invoice document'
    
    _columns = {
                
        'name': fields.char('Name', size=255, required=True, translate=True),
        'code': fields.char('Code', size=4, help="Document code"),
        'support_ids': fields.many2many('account.tax.support', 'account_document_support_rel',
            'doc_id', 'sup_id', 'Tax supports'),
        'is_retention' : fields.boolean('Is retention ?'),
        'is_liquidation' : fields.boolean('Is liquidation ?'),
        'only_sale' : fields.boolean('Only sales'),
        
    }
    _defaults = { 'only_sale': False }
    
# NAME GET
    def name_get(self, cr, uid, ids, context=None):
        
        reads = self.read(cr, uid, ids, ['name','code'], context=context)
        res = []
        for record in reads:
            name = record['code']
            if record['name']:
                name = name+' - '+record['name']
            res.append((record['id'], name))
        return res
    
account_invoice_document()


#----------------------------------------------------------
# Tax support
#----------------------------------------------------------
class account_tax_support(osv.osv):
    """
    This document is used in the invoice.
    """
    
    _name = 'account.tax.support'
    _description = 'Tax support'
    _rec_name = 'code'
    _columns = {
                
        'type': fields.char('Type', size=255, required=True, translate=True),
        'code': fields.char('Code', size=4, help="Tax support code"),
        'document_ids': fields.many2many('account.tax.support', 'account_document_support_rel',
            'sup_id', 'doc_id', 'Invoice document'),
        
    }
    
# NAME GET
    def name_get(self, cr, uid, ids, context=None):
        
        reads = self.read(cr, uid, ids, ['type','code'], context=context)
        res = []
        for record in reads:
            name = record['code']
            if record['type']:
                name = name+' - '+record['type']
            res.append((record['id'], name))
        return res

account_tax_support()


#----------------------------------------------------------
# Partners
#----------------------------------------------------------
class res_partner(osv.osv):
    """
    This document is used in the invoice.
    """
    
    _inherit = 'res.partner'
    _description = 'Partner'

    def _get_default_property_account_receivable(self, cr, uid, context=None):
        user = self.pool.get('res.users').browse(cr, uid, uid)
        if user.company_id.is_retail:
            account_id = self.pool.get('account.account').search(cr, uid, [('code', '=', '1.1.2.0.01')])
            return account_id[0]
        return False

    _columns = {

        'document_type': fields.many2one('account.invoice.document', 'Invoice document', select=True),
        'tax_support': fields.many2one('account.tax.support', 'Tax support', select=True),
    }

    def create(self, cr, uid, values, context=None):
        if 'property_account_receivable' not in values and 'supplier' not in values:
            values['property_account_receivable'] = self._get_default_property_account_receivable(cr, uid)
        return super(res_partner, self).create(cr, uid, values, context)

   # def write(self, cr, uid, ids, vals, context=None):
   #     obj_partner = self.pool['res.partner']
   #     partner_ids = obj_partner.search(cr, uid, [('is_employee', '=', False)], limit=None)
      #  print "partner_ids: ",  partner_ids
   #     for partner in obj_partner.browse(cr, uid, partner_ids):
   #         if partner.customer:
   #             vals['property_account_payable'] = 4590
   #         if partner.supplier:
   #             vals['property_account_receivable'] = 4531
   #     super(res_partner, self).write(cr, uid, partner.id, vals, context=context)
   #     return super(res_partner, self).write(cr, uid, partner_ids, vals, context=context)

res_partner()


class account_journal(osv.osv):
    _inherit = 'account.journal'

    _columns = {
        'type': fields.selection([('sale', 'Sale'),('sale_refund','Sale Refund'),
                                  ('purchase', 'Purchase'), ('purchase_refund','Purchase Refund'),
                                  ('cash', 'Cash'), ('bank', 'Bank and Checks'), ('general', 'General'),
                                  ('situation', 'Opening/Closing Situation'), ('provv', 'Provision Ventas'),
                                  ('provc', 'Provision Compras')], 'Type', size=32, required=True,
                                 help="Select 'Sale' for customer invoices journals."\
                                 " Select 'Purchase' for supplier invoices journals."\
                                 " Select 'Cash' or 'Bank' for journals that are used in customer or supplier payments."\
                                 " Select 'General' for miscellaneous operations journals."\
                                 " Select 'Opening/Closing Situation' for entries generated for new fiscal years."),
    }
account_journal()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
