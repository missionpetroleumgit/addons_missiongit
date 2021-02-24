# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution - Ecuador
#    Copyright (C) 2019 MissionPetroleum Daniel Aldaz (<daldaz@mission-petroleum.com>).
#
##############################################################################

from openerp import api, fields, models


class sale_order_transit(models.TransientModel):
    _name = 'sale.order.transit'

    date = fields.Datetime('Fecha bien/servicio', required=True)
    docs_date = fields.Datetime('Fecha Documentos')
    date_ok = fields.Boolean('OK', default=False)

    @api.multi
    def move_date_transit(self):
        sale_order = self.env['sale.order']
        date1 = self.date
        date2 = self.docs_date
        for order in sale_order.browse(self._context['active_ids']):
            self.date_ok = True
            order.invoice_control(date1)
            if self.date_ok and date2:
                order.invoice_control(date2)
        return True

sale_order_transit()
