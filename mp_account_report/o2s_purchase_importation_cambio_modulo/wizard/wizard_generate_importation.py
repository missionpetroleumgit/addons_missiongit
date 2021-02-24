##########################
# -*- coding: utf-8 -*- ##
##########################


from openerp import models, fields, api
from openerp.exceptions import except_orm, Warning


class generate_importation(models.TransientModel):
    _name = 'generate.importation'

    date_start = fields.Date('Inicio de importación', required=True)

    def check_disctint_partner(self, ids):
        partners = list()
        for order in self.env['importation.order'].browse(ids):
            if order.partner_id.id not in partners:
                partners.append(order.partner_id.id)
            else:
                raise except_orm('Error!', 'No puede importar ordenes de distintos proveedores')
        return True

    def check_lines(self, order):
        count = 0
        for line in order.order_lines:
            if line.imported:
                count += 1
        if len(order.order_lines) == count:
            return True
        return False

    @api.multi
    def button_generate(self):
        importation = self.env['purchase.importation']
        # self.check_disctint_partner(self._context['active_ids'])
        for rec in self:
            imp = importation.create({'date_order': rec.date_start})
            for order in self.env['importation.order'].browse(self._context['active_ids']):
                if self.check_lines(order):
                    raise except_orm('Error!', 'Las lineas de la orden %s ya fueron importadas' % order.name)
                if order.state != 'done':
                    raise except_orm('Error!', 'No puede generar una importación de una orden que no este confirmada, orden %s' % order.name)
                for line in order.order_lines:
                    if not line.imported:
                        self.env['importation.order.line'].create({'importation_id': imp.id, 'product_qty': line.product_qty, 'date_planned': line.date_planned,
                                                                   'product_uom': line.product_uom.id, 'product_id': line.product_id.id, 'price_unit': line.price_unit,
                                                                   'number': line.number, 'name': line.name, 'subtotal_importation': line.subtotal_importation,
                                                                   'origin': line.id})
                if imp.origin:
                    imp.origin += ', ' + order.name
                else:
                    imp.origin = order.name
            return True
