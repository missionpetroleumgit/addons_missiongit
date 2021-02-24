from openerp import models, fields, api
from openerp.exceptions import except_orm
from openerp import SUPERUSER_ID


class mail_payslip(models.TransientModel):
    _name = 'mail.payslip'

    @api.v7
    def send_mail(self, cr, uid, ids, context=None):
        mtp = self.pool.get('email.template')
        mail = self.pool.get('mail.mail')
        ids = context['active_ids']
        tmp = mtp.search(cr, uid, [('model_id.model', '=', 'hr.payslip'), ('name', '=', 'ROL MENSUAL')])
        if not tmp:
            raise except_orm('Error!', 'No existe una plantilla definida para el modelo %s' % 'hr.payslip')
        for item in ids:
            context['active_ids'] = [item]
            mail_id = mtp.send_mail(cr, SUPERUSER_ID, tmp[0], item, False, False, context)
            # mail_obj = mail.browse(cr, uid, mail_id)
            mail.send(cr, SUPERUSER_ID, [mail_id])
        return True
