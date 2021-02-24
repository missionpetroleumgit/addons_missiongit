# -*- encoding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2010 Latinux Inc (http://www.latinux.com/) All Rights Reserved.
#                    Javier Duran <jduran@corvus.com.ve>
# 
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################
from datetime import datetime, date, time, timedelta
from openerp.osv import fields, osv
from openerp.tools.translate import _




class account_voucher(osv.osv):
    _inherit = 'account.voucher'
    _description = "Cobro Terceros"
    _columns = {
        'is_thrid': fields.boolean('Es factura de terceros', help="Indica si es una factura de terceros"),
        'generador_id':fields.many2one('hr.employee', 'Generado por'),
        'terceros_desde_date': fields.date('Desde', required=False),
        'terceros_hasta_date': fields.date('Hasta', required=False),
        'voucher_ids': fields.one2many('account.terceros', 'voucher_id', 'Comprobante Id'),
        'sequence':fields.char('Secuencia', size=64),
#         'sucursal_id': fields.many2one('sale.shop', 'Sucursal', required=False),
    }
    _defaults = {
        'is_thrid': lambda * a: True,
#         'sucursal_id': lambda self, cr, uid, c: self.pool.get('res.users').browse(cr, uid, [uid], c)[0].sucursal_id.id,
    }


    def button_reset_line(self, cr, uid, ids, context):
        print "Facturas ids: ", ids[0]
        obj_cab = self.browse (cr, uid, ids[0])
        print "OBJETO CABECERA", obj_cab
    
        usuario = obj_cab.generador_id.id
        print "USER: ", usuario
#         obj_cab = self.browse (cr, uid, ids[0])
        f_desde = obj_cab.terceros_desde_date
        print "FECHA DESDE: ", f_desde
        f_hasta = obj_cab.terceros_hasta_date
        print "FECHA HASTA: ", f_hasta

        inv_obj = self.pool.get('account.invoice')
        ter_obj = self.pool.get('account.terceros')   
        vline_lst = []     
        for id in ids:
            cr.execute("DELETE FROM account_voucher_line WHERE voucher_id=%s", (id,))            

        inv_ids = inv_obj.search(cr,uid,[('is_third','=',True),('type','=','in_invoice'),('date_invoice','>=',f_desde),('date_invoice','<=',f_hasta)])
        print "IDS FACT", inv_ids
        for inv in inv_obj.browse(cr, uid, inv_ids):
            ter_ids = ter_obj.search(cr,uid,[('terceros_id','=',inv.id), ('employee','=',usuario)])
            print "TERCEROS", ter_ids
            if len(ter_ids) == 0:
                raise osv.except_osv(('Atencion !'), ('No hay valores de terceros para este Usuario!')) 
            else:
                for ter in ter_obj.browse(cr, uid, ter_ids):
                    vline_vals = {
                        'name': inv.number,
                        'account_id': ter.account_id.id,
                        'partner_id': inv.partner_id.id,
                        'employee_id': ter.employee.id,
                        'expense_id' : ter.expense_id.id,
                        'amount': ter.amount,
                        'terceros_id': inv.id
                        }
                    print "OBJ LINES", vline_vals
                    vline_lst.append((0,0,vline_vals))                

        voucher_vals = {
            'line_cr_ids': vline_lst
        }
        self.write(cr, uid, ids, voucher_vals)
            
        return True

    def move_line_get_voucher(self, cr, uid, ids, context):
        print "ids", ids[0]
        obj_cab = self.browse (cr, uid, ids[0])
        print "ID CABECERA", obj_cab
        vouc_line1 = self.pool.get('account.voucher.line').search(cr, uid, [('voucher_id', '=', ids[0])])
        print "Invoice Ids lines", vouc_line1             
        vouc_line = self.pool.get('account.voucher.line').browse(cr, uid, vouc_line1)
        print "Objeto voucher ids", vouc_line
        for det_voucher in vouc_line:
            ids_lines = self.pool.get('account.terceros').search(cr, uid, [('terceros_id', '=', det_voucher.terceros_id.id)])
            print "ids_lines: ", ids_lines
            ids_voucher = self.pool.get('account.terceros').write(cr, uid, ids_lines, {'voucher_id':ids[0]})
            print "Write", ids_voucher 
#             print "Invoice Id", det_voucher.terceros_id
#             vouc_line = self.pool.get('account.voucher.line').browse(cr, uid, det_voucher.terceros_id)
#             self.pool.get('account.terceros').write(cr, uid, det_invoice.id,{'voicher_id':ids[0]})
#         ids_mod = self.pool.get('operations.asig.consg').write(cr, uid, ids_consignas, {'consig_oper_id':ids[0]})
        if obj_cab.sequence:
            print "YA HAY SEQ", obj_cab.sequence
        else:
            secuencia_code = obj_cab.journal_id.sequence_id.code
            sequence = self.pool.get('ir.sequence').get(cr, uid, secuencia_code)
            self.write(cr, uid, ids, {'sequence':sequence}) 
   
        self.write(cr, uid, ids, {'state':'proforma'})
        return True
    

account_voucher()


class VoucherLine(osv.osv):
    _inherit = 'account.voucher.line'
    _description = "Cobro Terceros Line"
    _columns = {
        'employee_id':fields.many2one('hr.employee', 'Generado por'),
        'expense_id': fields.many2one('hr.expense.type', 'Expense'),
        'terceros_id' : fields.many2one('account.invoice', string='Terceros Reference'),
    }


    def _check_invoice(self,cr,uid,ids,context={}):
        obj_vline = self.browse(cr,uid,ids[0])

        if obj_vline.terceros_id and obj_vline.terceros_id.id:
            cr.execute('select id,terceros_id from account_voucher_line where voucher_id=%s and terceros_id=%s', (obj_vline.voucher_id.id, obj_vline.terceros_id.id))
            res=dict(cr.fetchall())
            if (len(res) == 1):
                res.pop(ids[0],False)            
            if res:
                return False
        return True


    _constraints = [
        (_check_invoice, 'Error ! Factura asignada. ', ['terceros_id'])
    ]

    def onchange_terceros_id(self, cr, uid, ids, terceros_id, context={}):
        res = super(VoucherLine, self).onchange_terceros_id(cr, uid, ids, terceros_id, context)
        invoice_obj = self.pool.get('account.invoice')
        invoice = invoice_obj.browse(cr, uid, terceros_id, context)
        res['value'].update({'account_id':invoice.account_id.id,'partner_id':invoice.partner_id.id,'name':invoice.factura,'journal_id':invoice.journal_id.id})
        return res 


VoucherLine()

class account_terceros_line(osv.osv):
    _inherit = 'account.terceros'
    _columns = {
        'voucher_id': fields.many2one('account.voucher', 'Comprobante Id'),
    }
                            
#     def move_line_get_voucher(self, cr, uid, ids, context):
#         print "ids", ids 
#         res = super(account_invoice_line, self).move_line_get_item(cr, uid, ids, context)
#         res['voucher_id'] = ids.voucher_id 
#         return res
        
account_terceros_line()