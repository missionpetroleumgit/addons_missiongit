# -*- coding: utf-8 -*-
#####
#  Facturación electrónica
#####

from openerp import models, fields, api, _
from openerp import netsvc
import tempfile
import base64
from openerp.exceptions import except_orm, Warning
import openerp.addons.decimal_precision as dp
import time
from datetime import datetime, timedelta


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def action_electronic_shipping_purchase_liquidation(self):
        """ Open a window to compose an email, with the edi invoice template
            message loaded by default
        """
        assert len(self) == 1, 'This option should only be used for a single id at a time.'
        for record in self:
            mtp = self.env['email.template']
            mail = self.env['mail.mail']
            clave = ''
            # #CAPTURO XML AUTORIZADO PARA ENVIAR AL CLIENTE JUNTO AL PDF
            fact_elect_id = self.env['account.factura.electronica'].search([('factelect_id', '=', record.id)])
            for clave in fact_elect_id:
                claveac = clave.clave_acceso
            name = "%s.xml" % (claveac)
            att = self.env['ir.attachment'].search([('res_id','=',record.id),('res_model','=',self._name),
                                                    ('name','=',name)])

            template = mtp.search([('model_id.model', '=', self._name), ('name', '=', 'FACTURA ELECTRONICA')])
            template.attachment_ids = False
            template.attachment_ids = [[6,0, [att.id]]]
            compose_form = self.env.ref('mail.email_compose_message_wizard_form', False)
            ctx = dict(
                default_model='account.invoice',
                default_res_id=self.id,
                default_use_template=bool(template),
                default_template_id=template.id,
                default_composition_mode='comment',
                mark_invoice_as_sent=True,
            )
        return {
            'name': _('Compose Email'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form.id, 'form')],
            'view_id': compose_form.id,
            'target': 'new',
            'context': ctx,
        }
#CSV:07-02-2018: AUMENTO PARA ENVIO FACTURAS MASIVO DE MAILS
    @api.multi
    def action_invoice_sent_elect_masivo(self):
        """ Open a window to compose an email, with the edi invoice template
            message loaded by default
        """
        ids = self.ids
        mtp = self.env['email.template']
        template = mtp.search([('model_id.model', '=', self._name), ('name', '=', 'FACTURA ELECTRONICA')])
        for record in self:
            # solo autorizadas envio masivo
            if record.state_factelectro == 'autorizado':
                fact_elect_id = self.env['account.factura.electronica'].search([('factelect_id', '=', record.id)])
                if fact_elect_id:
                    for clave in fact_elect_id:
                        claveac = clave.clave_acceso
                    name = "%s.xml" % (claveac)
                    att = self.env['ir.attachment'].search([('res_id','=',record.id),('res_model','=',self._name),
                                                            ('name','=', name)])
                    if att:
                        # JJM solo si encuentro el xml envio mail
                        template.attachment_ids = [[6, 0, [att.id]]]
                        template.send_mail(record.id)
                        record = record.with_context(mail_post_autofollow=True)
                        record.write({'sent': True})
                        record.message_post(body=_("Invoice sent"))
                    else:
                        # borro cache para envio del mail, sin otros adjuntos Ojo debio encontrarse el xml !!!
                        template.attachment_ids = [[6, 0, []]]
        return True

    @api.multi
    def send_mymail_elect(self):
        mtp = self.env['email.template']
        mail = self.env['mail.mail']
        for record in self:
            tmp = mtp.search([('model_id.model', '=', self._name), ('name', '=', 'Purchase Order - Send by Email')])
            mail_id = tmp.send_mail(record.id)
        mail_obj = mail.browse(mail_id)
        mail_obj.send()
        return True

    liquidation_authorization = fields.Char('Autorizacion liquidacion', size=100)