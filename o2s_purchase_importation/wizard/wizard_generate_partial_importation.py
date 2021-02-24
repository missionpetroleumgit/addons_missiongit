##########################
# -*- coding: utf-8 -*- ##
##########################


from openerp import models, fields, api
from openerp.exceptions import except_orm, Warning
import openerp.addons.decimal_precision as dp


class importation_line_transit(models.TransientModel):
    _name = 'importation.line.transit'

    importation_id = fields.Many2one('importation.order', 'Importacion')
    subtotal_importation = fields.Float('Subtotal')
    name = fields.Text('Description', required=True)
    product_qty = fields.Float('Quantity', digits_compute=dp.get_precision('Product Unit of Measure'), required=True)
    date_planned = fields.Date('Scheduled Date', required=True, select=True)
    taxes_id = fields.Many2many('account.tax', 'importation_order_taxe2', 'imp_id', 'tax_id', 'Taxes')
    product_uom = fields.Many2one('product.uom', 'Product Unit of Measure', required=True)
    product_id = fields.Many2one('product.product', 'Product', domain=[('purchase_ok', '=', True)], change_default=True)
    price_unit = fields.Float('Unit Price', required=True, digits_compute=dp.get_precision('Product Price'))
    account_analytic_id = fields.Many2one('account.analytic.account', 'Analytic Account', )
    company_id = fields.Many2one('res.company', string='Company', readonly=True)
    number = fields.Char('No. parte')
    imported = fields.Boolean('Importada')
    analytics_id = fields.Many2one('account.analytic.plan.instance', 'Distribucion Analitica')
    transit_imp_id = fields.Many2one(comodel_name='generate.partials.importations',
                                     string='ID Modelo transitorio')
    to_generate = fields.Boolean('Item')


class generate_partials_importations(models.TransientModel):
    _name = 'generate.partials.importations'

    date_start = fields.Date('Inicio de importación', required=True)
    importation_line_ids = fields.One2many('importation.line.transit', 'transit_imp_id', 'Lineas de Importacion',
                                           ondelete='cascade')

    @api.onchange('importation_line_ids')
    def onchange_requisition_order_id(self):
        line_ids = []
        for order in self.env['importation.order'].browse(self._context['active_ids']):
            for line in order.order_lines:
                if not line.imported:
                    taxes = list()
                    taxes.append([6, False, [tax.id for tax in line.taxes_id]])
                    vals = (0, 0, {'product_id': line.product_id.id,
                                   'company_id': line.company_id.id,
                                   'importation_id': line.importation_id.id,
                                   'product_qty': line.product_qty,
                                   'product_uom': line.product_uom.id,
                                   'subtotal_importation': line.subtotal_importation,
                                   'name': line.name,
                                   'taxes_id': taxes,
                                   'analytics_id': line.analytics_id.id,
                                   'price_unit': line.price_unit,
                                   'imported': line.imported,
                                   'date_planned': line.date_planned
                                   })
                    line_ids.append(vals)
            self.update({'importation_line_ids': line_ids})

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
        name = ''
        for rec in self:
            imp = importation.create({'date_order': rec.date_start})
            for line in rec.importation_line_ids:
                if not line.imported:
                    if line.to_generate:
                        # line.imported = True
                        self.env['importation.order.line'].create({'importation_id': imp.id,
                                                                   'product_qty': line.product_qty,
                                                                   'date_planned': line.date_planned,
                                                                   'product_uom': line.product_uom.id,
                                                                   'product_id': line.product_id.id,
                                                                   'price_unit': line.price_unit,
                                                                   'number': line.number,
                                                                   'name': line.name,
                                                                   'subtotal_importation': line.subtotal_importation,
                                                                   'origin': line.id})

            for order in self.env['importation.order'].browse(self._context['active_ids']):
                if imp.origin:
                    name += '/' + ' ' + imp.origin + order.name
                else:
                    name += '/' + ' ' + order.name
                imp.name = name
            return True
