# -*- coding: utf-8 -*-
from openerp import api, fields, models
import smtplib
from urlparse import urljoin
from openerp.exceptions import except_orm


class StockLocationRoute(models.Model):
    _inherit = 'stock.location.route'

    location_code = fields.Selection([('manufacture', 'Manufacture'), ('on_request', 'On Request')], 'Code')


class StockMove(models.Model):
    _inherit = 'stock.move'

    mrp_created = fields.Boolean('Orden hija creada', default=False)
    # post_consume_production_id = fields.Many2one('mrp.production', 'Orden de produccion')

    @api.multi
    def action_create_children_productions(self):
        mrp_production = self.env['mrp.production']
        for record in self:
            if record.product_uom_qty >= record.product_id.qty_available:
                production = mrp_production.search([('name', '=', record.picking_id.origin)])
                new_production = mrp_production.new(
                    {
                        'product_id': record.product_id.id,
                        'product_qty': record.product_uom_qty,
                        'user_id': production.user_id.id,
                        'origin': production.name,
                        'sale_id': production.sale_id.id,
                        'mrp_children': True,
                        'mrp_production_id': production.id
                    }
                )
                res = new_production.product_id_change(product_id=record.product_id.id, product_qty=record.product_uom_qty)
                values = new_production._convert_to_write(
                    {name: new_production[name] for name in new_production._cache})
                values.update(res['value'])
                mrp_production.create(values)
            else:
                raise except_orm('Advertencia', 'La cantidad de stock del producto abastece completamente a la '
                                                'orden de produccion.')
            self.mrp_created=True
        if production:
            self.action_sent_production_mail(production.id, self.product_id.id)

    @api.multi
    def _get_production_url(self, pid):
        link = ''
        production = self.env['mrp.production'].search([('id', '=', pid)])
        base_url = self.pool['ir.config_parameter'].get_param(self._cr, self._uid, 'web.base.url')
        for order in self:
            link = urljoin(
                base_url + '/web?=#id=' + str(production.id) + '&view_type=form&model=mrp.production&action=633', '')
        return link

    @api.multi
    def action_sent_production_mail(self, order_id, product):
        prod = ''
        cantidad = 0
        production_father = ''
        remitente = "<daldaz@mission-petroleum.com>"
        destinatario = "<daldaz@mission-petroleum.com>"
        production = self.env['mrp.production'].search([('id', '=', order_id)])
        product_product = self.env['product.product'].search([('id', '=', product)])
        production_children = self.env['mrp.production'].search([('origin', '=', production.name),
                                                                 ('product_id', '=', product)])
        if product:
            if not product_product.default_code:
                prod = product_product.name_template
            else:
                prod = ('[' + product_product.default_code + ']' + ' ' + product_product.name_template)
        url = self._get_production_url(production_children.id)
        production_children = production_children.name
        print production_children
        production_father = production.name
        if production:
            cantidad = '[' + str(production.product_qty) + ' ' + str(production.product_uom.name) + ']'
        else:
            cantidad = '[' + str(self.product_uom_qty) + ' ' + str(self.product_uom.name) + ']'
        mensaje = """
Estimados,

Se ha generado una orden de produccion %s de %s para el producto %s, desde la orden de produccion madre %s.

Link de la orden de produccion, %s


Saludos Cordiales,

PRODUCCION
MISSIONPETROLEUM S.A.
Av. de Los Shyris N36-188 y Naciones Unidas
Edif. Shyris Park Piso 4, Of. 401- 402 - 403 - 404
Telf.: (593) 23949380 Ext.: 225 - 226
www.mission-petroleum.com

           """ % (production_children, cantidad, prod, production_father, url)
        username = 'daldaz@mission-petroleum.com'
        password = 'N4nd0MpM1ss10n2018!$!'
        email = """From: %s
            To: %s
            Subject: %s
            %s
            """ % (remitente, destinatario, production.name, mensaje)
        try:
            smtp = smtplib.SMTP('mail.mission-petroleum.com')
            smtp.starttls()
            smtp.login(username, password)
            smtp.sendmail(remitente, destinatario, email)
            smtp.quit()
        except:
            print """Error: el mensaje no pudo enviarse.
                Compruebe que sendmail se encuentra instalado en su sistema"""
