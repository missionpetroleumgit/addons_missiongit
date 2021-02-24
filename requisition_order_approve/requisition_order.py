# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution - Ecuador
#    Copyright (C) 2019 MissionPetroleum Daniel Aldaz (<daldaz@mission-petroleum.com>).
#
##############################################################################

from openerp import fields, models, api


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    material_type = fields.Selection([('critical', 'Material Critico'), ('stock', 'Stock/Consumibles')],
                                     'Tipo Material')

    @api.onchange('material_type')
    def onchange_approver_id(self):
        res_users = self.env['res.users']
        oper_user_id = res_users.search([('login', '=', 'marcelo_carvajal')])
        adm_user_id = res_users.search([('login', '=', 'roger_intriago')])
        for record in self:
            if record.material_type == 'critical':
                record.app_user_id = oper_user_id.id
            if record.material_type == 'stock':
                record.app_user_id = adm_user_id.id

PurchaseOrder()
