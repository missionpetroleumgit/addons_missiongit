##########################
# -*- coding: utf-8 -*-  #
##########################
from openerp import models, fields, api


class purchase_order(models.Model):
    _inherit = 'purchase.order'

    @api.one
    def responsable_onchange(self):
        for record in self:
            hr_employee = self.env['hr.employee']
            employee = hr_employee.search([('id', '=', record.req_user_id.id)])
            record.req_responsable_id = employee.id

    services = fields.Selection([('service', 'Servicios')], 'Tipo de Productos')
    stock = fields.Selection([('consu', 'Consumibles'), ('product', 'Productos'), ('service', ('Servicios'))],
                             'Tipo de Productos')
    req_responsable_id = fields.Many2one('hr.employee', 'Responsable Requisicion', compute='responsable_onchange',
                                         required=True)

    @api.onchange('services')
    def change_purchase_service_onchange(self):
        for record in self:
            if record.services == 'service':
                record.type_purchase = 'service'

    @api.onchange('stock')
    def change_purchase_stock_onchange(self):
        for record in self:
            if record.stock == 'consu':
                record.type_purchase = 'consu'
            if record.stock == 'product':
                record.type_purchase = 'product'
            if record.stock == 'service':
                record.type_purchase = 'service'

    @api.onchange('req_user_id')
    def req_onchange(self):
        for record in self:
            res_users = self.env['res.users']
            hr_employee = self.env['hr.employee']
            user_not_apply = res_users.search([('not_apply', '=', True)])
            employee = hr_employee.search([('id', '=', record.req_user_id.id)])
            if user_not_apply:
                req_user = record.req_user_id.user_id.login
                for nousers in user_not_apply:
                    if req_user == nousers.login:
                        continue
	            else:
                        record.req_responsable_id = employee.id
            else:
                record.req_responsable_id = employee.id

purchase_order()


class ResUsers(models.Model):
    _inherit = 'res.users'

    not_apply = fields.Boolean('No aplica', help='Marque este campo para definir que este usuario deba obligatoriamente'
                                                 ' asignar un responsable en la requisicion')

ResUsers()


class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.multi
    def _requisition_count(self):
        PurchaseOrder = self.env['purchase.order']
        if len(self) >= 1:
            prod_id = self[0].id
        else:
            prod_id = False
        product_id = PurchaseOrder.search([('request_products.product_id', '=', prod_id),
                                           ('state', 'in', ('draft', 'sent', 'bid'))])
        count = 0
        if product_id:
            count = len(product_id)
            self.requisition_count = count
            self.action_requisitions_view()
        return count

    @api.multi
    def action_requisitions_view(self):
        if isinstance(self.ids, (int, long)):
            ids = [self.ids]
        action = self.env.ref('purchase_adjustment.action_request_products_tree').read()[0]
        action.update({'domain': [('id', 'in', self.mapped('request_lines').ids)]})
        return action

    requisition_count = fields.Integer('Requisiciones', compute=_requisition_count)
    request_lines = fields.One2many('request.product', 'product_id', 'Lineas de requisiciones', ondelete='cascade')


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.multi
    def _requisition_count(self):
        if len(self) >= 1:
            p_ids = self[0].id
        else:
            p_ids = False
        res = dict.fromkeys(self[0], 0)
        variants = self.env['product.template'].search([('id', '=', p_ids)])
        p_variants = 0
        for template in variants:
            p_variants = sum([p.requisition_count for p in template.product_variant_ids])
            self[0].requisition_count = p_variants
        return p_variants

    def action_view_requisitions(self, cr, uid, ids, context=None):
        products = self._get_products(cr, uid, ids, context=context)
        result = self._get_act_window_dict(cr, uid, 'purchase_adjustment.action_request_products_tree', context=context)
        result['domain'] = "[('product_id','in',[" + ','.join(map(str, products)) + "])]"
        return result

    requisition_count = fields.Integer('Requisiciones', compute=_requisition_count)
