from openerp import models, fields, api
from openerp.exceptions import except_orm, Warning


class res_company(models.Model):
    _inherit = 'res.company'

    percent = fields.Float('Porcentaje ISD')
