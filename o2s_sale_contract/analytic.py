# -*- coding: utf-8 -*-
###############################
#  Contratos para petroleras  #
###############################

from openerp import models, fields, api
from openerp.exceptions import except_orm, Warning


class account_analytic_account(models.Model):
    _inherit = 'account.analytic.account'

    pricelist_id = fields.Many2one('product.pricelist', 'Lista de Precio')
    child_ids = fields.One2many('account.analytic.account', 'parent_id', 'Proyectos', domain=[('type', '=', 'view')])

    @api.model
    def default_get(self, fields_list):
        res = super(account_analytic_account, self).default_get(fields_list)
        if 'type' in self._context:
            res['type'] = self._context['type']
        return res

    @api.v7
    def on_change_partner_id(self, cr, uid, ids, partner_id, name, context=None):
        res = super(account_analytic_account, self).on_change_partner_id(cr, uid, ids, partner_id, name, context)
        if res:
            partner = self.pool.get('res.partner').browse(cr, uid, partner_id, context=context)
            if partner.property_product_pricelist:
                res['pricelist_id'] = partner.property_product_pricelist.id
        return {'value': res}


