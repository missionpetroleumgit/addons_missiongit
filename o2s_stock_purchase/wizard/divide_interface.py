##########################
# -*- coding: utf-8 -*- ##
##########################


from openerp import models, fields, api
from openerp.exceptions import except_orm, Warning


class iterface(models.TransientModel):
    _name = 'interface'

    quantity = fields.Float('Cantidad de producto')
    lines = fields.One2many('interface.line', 'int_id', 'lineas')

    @api.model
    def default_get(self, fields_list):
        res = dict()
        move = self.env['stock.move'].browse(self._context['active_id'])
        res['quantity'] = move.product_uom_qty
        return res

    @api.multi
    def create_operation(self):
        l = list()
        serials = list()
        serial_item = self.env['serial.item']
        move = self.env['stock.move'].browse(self._context['active_id'])
        for record in self:
            for line in record.lines:
                if line.serial not in serials:
                    l.append(serial_item.create({'name': line.serial, 'origin': move.picking_id.origin, 'product_id': move.product_id.id}))
                    serials.append(line.serial)
                else:
                    raise except_orm('Error!', 'No puede tener seriales repetidos: serial %s' % line.serial)
            if len(l) != int(record.quantity):
                raise except_orm('Error!', 'No puede generar un numero de series menor a la cantidad de elementos del movimiento')
            record.divide_lines(move, record.quantity)
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def items_order(self, product, origin):
        items_qty = 0
        objs = list()
        for serial in product.serial_items:
            if serial.origin == origin:
                items_qty += 1
                objs.append(serial.id)
        return items_qty, objs

    def divide_lines(self, move, quantity):
        items_qty, objs = self.items_order(move.product_id, move.picking_id.origin)
        count = items_qty
        for serial in objs:
            if count > 1:
                aux = move.copy()
                aux.product_uom_qty = move.product_uom_qty - quantity
                aux.serial_item_id = serial
                aux.action_confirm()
                aux.action_assign()
                count -= 1

        move.product_uom_qty = move.product_uom_qty - quantity
        move.serial_item_id = serial


class interface_line(models.TransientModel):
    _name = 'interface.line'

    serial = fields.Char('No. Serie', required=True)
    int_id = fields.Many2one('interface', 'Interface')
