# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution - Ecuador
#    Copyright (C) 2019 MissionPetroleum Daniel Aldaz (<daldaz@mission-petroleum.com>).
#
##############################################################################

from openerp import api, fields, models


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    fields_id = fields.Many2one('service.field', 'Campo')
    pit_id = fields.Many2one('service.well.line', 'Pozo')
    business_unit_id = fields.Many2one('service.line', 'Unidad de negocio')

PurchaseOrder()
