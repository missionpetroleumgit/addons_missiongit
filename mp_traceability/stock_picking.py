# -*- coding: utf-8 -*-
from openerp import api, models, fields
from openerp.exceptions import except_orm


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    wh_sig_user_id = fields.Many2one('res.users', 'Responsable Bodega')
    quality_sig_user_id = fields.Many2one('res.users', 'Responsable Calidad')
    revision_required = fields.Boolean('Requiere revision Calidad')
    wh_date = fields.Date('Fecha Revision Bodega')
    quality_date = fields.Date('Fecha Revision Calidad')
    quality_revision = fields.Boolean('Revisado por Calidad')
    wh_revision = fields.Boolean('Revisado por Bodega')
    quality_obs = fields.Text('Comentarios Calidad')
    wh_obs = fields.Text('Comentarios Bodega')


StockPicking()


class ResUsers(models.Model):
    _inherit = 'res.users'

    wh_user = fields.Boolean('Acceso rev Bodega')
    quality_user = fields.Boolean('Acceso rev Calidad')


ResUsers()


# class StockTransferDetails(models.Model):
#     _inherit = 'stock.transfer_details'
#
#     @api.one
#     def do_enter_transfer_details(self):
#         res = super(StockTransferDetails, self).do_enter_transfer_details()
#         origin1 = self.picking_id.origin[:2]
#         print 'ensamble, fabricacion', origin1
#         origin2 = self.picking_id.origin[:3]
#         print 'servicios fabricacion', origin2
#         incoming = self.picking_id.picking_type_id.code == 'incoming'
#         internal = self.picking_id.picking_type_id.code == 'internal'
#         if incoming or internal and origin1 in ('AO', 'MO') and origin2 == 'MSO':
#             if self.picking_id.revision_required:
#                 print "Entroooooo**************"
#                 if not self.picking_id.quality_revision and not self.picking_id.wh_revision:
#                     raise except_orm('Error de revisión !',
#                                      'Debe colocar los datos de revisión por calidad y bodega de este ingreso.!!')
#             else:
#                 print "Entroooooo**************2222222222222222222"
#                 if not self.picking_id.wh_revision:
#                     raise except_orm('Error de revisión !',
#                                      'Debe colocar los datos de revisión por bodega de este ingreso.!!')
#         else:
#             raise except_orm('Error de revisión !',
#                              'No ingresa.!!')
#
#         return res
#
#
# StockTransferDetails()
