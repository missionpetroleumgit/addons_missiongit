# -*- encoding: utf-8 -*-
##############################################################################
#
#    Author :  Guillermo Herrera Banda: guillermo.herrera@bitconsultores-ec.com
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import fields, osv, expression
from utils import cedula_validation,ruc_validation
import re


class res_partner(osv.osv):
    _name = 'res.partner'
    _inherit = 'res.partner'

    def onchange_id_num(self, cr, uid, ids, identification_number,tipo_doc):
        res = {'value':{}}
        if tipo_doc=='c':
            cedula_validation(identification_number)
        elif tipo_doc=='r':
             ruc_validation(identification_number)   
        elif tipo_doc=='p':
                print 'tipo pasaporte'  
                print 'S/N'
        return res

    def search(self, cr, uid, args, offset=0, limit=80, order=None, context=None, count=False):
        auxiliar = list()
        for arg in args:
            if arg[0] == 'display_name':
                auxiliar.append(['part_number', 'ilike', arg[2]])
                break
        res = super(res_partner, self).search(cr, uid, args, offset, limit, order, context, count)
        if not res and auxiliar:
            res = super(res_partner, self).search(cr, uid, auxiliar, offset, limit, order, context, count)
        return res

    def name_search(self, cr, user, name='', args=None, operator='ilike', context=None, limit=None):
        if not args:
            args = []
        if name:
            positive_operators = ['=', 'ilike', '=ilike', 'like', '=like']
            ids = []
            if operator in positive_operators:
                ids = self.search(cr, user, [('name','=',name)]+ args, limit=limit, context=context)
                if not ids:
                    ids = self.search(cr, user, [('part_number','=',name)]+ args, limit=limit, context=context)

            if not ids and operator not in expression.NEGATIVE_TERM_OPERATORS:
                # Do not merge the 2 next lines into one single search, SQL search performance would be abysmal
                # on a database with thousands of matching products, due to the huge merge+unique needed for the
                # OR operator (and given the fact that the 'name' lookup results come from the ir.translation table
                # Performing a quick memory merge of ids in Python will give much better performance
                ids = self.search(cr, user, args + [('part_number', operator, name)], limit=limit, context=context)
                if not limit or len(ids) < limit:
                    # we may underrun the limit because of dupes in the results, that's fine
                    limit2 = (limit - len(ids)) if limit else False
                    ids += self.search(cr, user, args + [('name', operator, name), ('id', 'not in', ids)], limit=limit2, context=context)
            elif not ids and operator in expression.NEGATIVE_TERM_OPERATORS:
                ids = self.search(cr, user, args + ['&', ('part_number', operator, name), ('name', operator, name)], limit=limit, context=context)
            if not ids and operator in positive_operators:
                ptrn = re.compile('(\[(.*?)\])')
                res = ptrn.search(name)
                if res:
                    ids = self.search(cr, user, [('part_number','=', res.group(2))] + args, limit=limit, context=context)
        else:
            ids = self.search(cr, user, args, limit=limit, context=context)
        result = self.name_get(cr, user, ids, context=context)
        return result
    
    def name_get(self, cr, uid, ids, context=None):
        if not ids:
            return []
        if isinstance(ids, (int, long)):
                    ids = [ids]
        reads = self.read(cr, uid, ids, ['name', 'part_number'], context=context)
        res = []
        for record in reads:
            name = record['name']
            if record['part_number']:
                name = '[' + record['part_number'] + ']' + ' ' + name
            res.append((record['id'], name))
        return res


    _columns = {
        'part_number':fields.char('Numero Identificacion', size=20, ),
        'part_type':fields.selection((('c','Cedula'),('p','Pasaporte'),('r','RUC'),('s','S/N')), "Tipo Identificacion"),
        'part_birthday': fields.date('Fecha Nacimiento'),
        'use_another_id': fields.boolean('Usa otro identificador de pago?'),
        'second_identification': fields.char('Identificacion para e-Transfer', size=13)
      }
    _defaults = {
        'part_type': lambda *a: 's',
        'is_company': lambda *a: True,
    }

    _sql_constraints = [
            ('unique_part_number', 'unique(part_number, partner_id)', 'Identificacion Duplicada')
            ]

    def _check_partnumber(self, cr, uid, number, context=None):
        if self.search(cr, uid, [('part_number', '=', number)]):
            return True
        return False

    def create(self, cr, uid, values, context=None):
        if 'part_number' in values and values['part_number']:
            if self._check_partnumber(cr, uid, values['part_number'], context):
                raise osv.except_osv('Error', 'El numero de identificacion %s ya esta asociado a otro Partner ' % values['part_number'])
        return super(res_partner, self).create(cr, uid, values, context)

    def write(self, cr, uid, ids, vals, context=None):
        if 'part_number' in vals and vals['part_number']:
            if self._check_partnumber(cr, uid, vals['part_number'], context):
                raise osv.except_osv('Error', 'El numero de identificacion %s ya esta asociado a otro Partner ' % vals['part_number'])
        return super(res_partner, self).write(cr, uid, ids, vals, context)

res_partner()