##########################
# -*- coding: utf-8 -*- ##
##########################


from openerp import models, fields, api
from openerp.exceptions import except_orm, Warning
from datetime import datetime


#----------------------------------------------------------
#    IR.SEQUENCE
#----------------------------------------------------------
class bit_ir_sequence(models.Model):
    _inherit = 'ir.sequence'

    partner_id = fields.Many2one('res.partner', 'Empresa')
    sequence_retention = fields.Boolean('Es secuancia de retencion', help="Marque esta opcion si es una secuancia de retenciones de la compania")


class account_authorization(models.Model):
    _name = 'account.authorization'

    @api.model
    def _get_type(self):
        return self._context.get('to_customer')

    @api.model
    def _defaylt_company(self):
        return self.env.user.company_id.id

    # Metodo para el cron y desactivar las autorizaciones vencidas
    @api.model
    def inactive_authorization(self, use_new_cursor=False, company_id=False):
        objs = self.env['account.authorization'].sudo().search([])
        for record in objs:
            if record.expiration_date < datetime.now().strftime('%Y-%m-%d'):
                record.write({'active': False})
        return True

    name = fields.Char('Authorization number', size=128, required=True)
    serie_entity = fields.Char('Serie entity', size=3, required=True, default='001')
    serie_emission = fields.Char('Serie emission', size=3, required=True, default='002')
    num_start = fields.Integer('Number since', required=True)
    num_end = fields.Integer('Number until', required=True)
    num_resolution = fields.Integer('Resolution number')
    expiration_date = fields.Date('Vigente hasta', required=True)
    active = fields.Boolean('Activo?', default=True)
    type_id = fields.Many2one('account.invoice.document', 'Document types', required=True)
    partner_id = fields.Many2one('res.partner', 'Empresa', required=True)
    company_id = fields.Many2one('res.company', 'Company', default=_defaylt_company)
    sequence_id = fields.Many2one('ir.sequence', 'Secuencia')
    to_customer = fields.Boolean('Is customer authorization ?', default=_get_type)
    is_retention = fields.Boolean('Is retention authorization ?')
    is_electronic = fields.Boolean('autorizacion elect.?')

    @api.v7
    def _check_exist(self, cr, uid, ids, context=None):
        auth = False
        today = datetime.today().strftime('%Y-%m-%d')
        auth_actual = self.browse(cr, uid, ids[0])
        if not auth_actual.is_retention and not auth_actual.is_electronic:
            auth = self.search(cr, uid, [('name', '=', auth_actual.name), ('partner_id', '=', auth_actual.partner_id.id), ('company_id', '=', auth_actual.company_id.id),
                                         ('expiration_date', '>=', today), ('type_id', '=', auth_actual.type_id.id), ('id', 'not in', ids)])
        if auth:
            return False
        return True

    _constraints = [
        (_check_exist, 'Ya existe una autorizacion con el numero insertado vigente para el proveedor en la compañía', ['name']),
    ]

    @api.onchange('to_customer')
    def onchange_to_customer(self):
        res = dict()
        res['domain'] = {'partner_id': [('supplier', '=', True)]}
        if self.to_customer:
            res['domain'].update({'partner_id': [('customer', '=', True)]})
        return res

    @api.onchange('expiration_date')
    def onchange_expiration_date(self):
        res = dict()
        if self.expiration_date:
            exp_date = datetime.strptime(self.expiration_date, '%Y-%m-%d')
            today = datetime.today()
            if exp_date < today:
                res['warning'] = {'title': "Alerta", "message": "La fecha vigencia debe ser mayor que la fecha de actual"}
                self.expiration_date = False
        return res

    def _check_zeros_or_order(self, num_start, num_end):
        if num_start <= 0 or num_end <= 0 or num_start > num_end:
            return True
        return False

    @api.model
    def create(self, vals):
        if 'sequence_id' not in vals or ('sequence_id' in vals and not vals['sequence_id']):
            if self._check_zeros_or_order(vals['num_start'], vals['num_end']):
                raise except_orm('Error!', 'Revise los numero de inicio y fin, los mismos no pueden ser cero ni puede ser'
                                           ' mayor el numero final al inicial')
            obj_seq_type = self.env['ir.sequence.type']
            doc_type_obj = self.env['account.invoice.document'].browse(vals['type_id'])
            seq_type = obj_seq_type.search([('code', '=', doc_type_obj.name)])
            if not seq_type:
                vals_code = {
                    'code': doc_type_obj.name,
                    'name': doc_type_obj.name,
                }
                seq_type = obj_seq_type.create(vals_code)
            vals_seq = {
                'name': seq_type.code,
                'padding': len(str(vals['num_end'])) or 3,
                'partner_id': vals['partner_id'],
                'number_next': int(vals['num_start']),
                'code': seq_type.code,
            }

            seq = self.env['ir.sequence'].create(vals_seq)
            vals.update({'sequence_id': seq.id})

        return super(account_authorization, self).create(vals)
