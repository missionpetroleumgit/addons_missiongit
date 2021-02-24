# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution - Ecuador
#    Copyright (C) 2019 MissionPetroleum Daniel Aldaz (<daldaz@mission-petroleum.com>).
#
##############################################################################

from openerp import api, fields, models
from datetime import datetime, timedelta
from openerp.exceptions import except_orm


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    fields_id = fields.Many2one('service.field', 'Campo')
    pit_id = fields.Many2one('service.well.line', 'Pozo')
    business_unit_id = fields.Many2one('service.line', 'Unidad de negocio')

AccountInvoice()
