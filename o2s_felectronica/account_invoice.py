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


class account_invoice(models.Model):
    _inherit = 'account.invoice'
# Para facturacion electronica

#     @api.multi
#     def action_invoice_sent_elect(self):
#         """ Open a window to compose an email, with the edi invoice template
#             message loaded by default
#         """
#         assert len(self) == 1, 'This option should only be used for a single id at a time.'
#         #MANDO A GENERAR EL PDF Y CAPTURO XML PARA ADJUNTARLO
#
#         firmadig = self.env.user.company_id.name
#         print "COMPANIA MAIL", firmadig
#         print "IDSS", self.ids[0]
#         # attachment_ids = self.env['ir.attachment'].search([('res_model', '=', 'account.invoice'),
#         #                                         ('res_id', '=', self.ids[0])])
#         attachments = []
#         attach_name = []
#         # for attach in self.env['ir.attachment'].browse(attachment_ids):
#         #     f_name = tempfile.gettempdir() +'/'+ attach.name
#         #     open(f_name,'wb').write(base64.decodestring(attach.datas))
#         #     attachments.append(f_name)
#         #     attach_name.append(attach.name)
#
#         po_state = self.env['account.invoice'].browse(self.ids).state
#         print "po_state: ", po_state
#         if po_state == 'draft' :
#             raise Warning(('Error enviando email'), ('No puede enviar comprobantes que no esten pagados'))
#
#         report_name = {'open' : 'account.invoice.indfe',}
#     #    report_id = pool.get('ir.actions.report.xml').search(cr, uid,
#     #                                [('model', '=', 'purchase.order'),
#     #                                 ('internal_name' ,'=', report_name[po_state])])
#
#     #    report_obj = pool.get('ir.actions.report.xml').browse(cr, uid, report_id)
#     #    if report_obj :
#     #        if report_obj.attachment_use and attachment:
#     #            name =
#
#         service = netsvc.LocalService("report."+report_name[po_state]);
#         (result, format) = service.create(self._cr, self._uid, self.ids[0], {})
#
#         f_name = tempfile.gettempdir() +'/o2s_felectronica.' + format
#         open(f_name,'wb').write(result)
# #CAPTURO XML AUTORIZADO PARA ENVIAR AL CLIENTE JUNTO AL PDF
#         fact_elect_id = self.env['account.factura.electronica'].search([('factelect_id', '=', self.ids[0])])
#         print "fact_elect_id", fact_elect_id
#         # n_clave = self.env['account.factura.electronica'].browse(fact_elect_id)
#         # print "n_clave", n_clave
#         for clave in fact_elect_id:
#             print "CLAVE", clave.clave_acceso
#             claveac = clave.clave_acceso
#         print "CLAVE ACCESO", claveac
#         name = "%s.xml" % (claveac)
#
#         w = open('/home/guillermo/Documentos/'+firmadig+'/'+'FACTURA_ELECTRONICA/FACTURAF/'+name, 'rb')
#         q=w.read()
#         f_name1 = tempfile.gettempdir() +'/'+ name
#         open(f_name1,'wb').write(base64.encodestring(q))
#         attachments.append(f_name1)
#         attachments.append(f_name)
#         print "attachments**", attachments
#
#
#         template = self.env.ref('account.email_template_edi_invoice', False)
#
#         compose_form = self.env.ref('mail.email_compose_message_wizard_form', False)
#         ctx = dict(
#             default_model='account.invoice',
#             default_res_id=self.id,
#             default_use_template=bool(template),
#             default_template_id=template.id,
#             default_composition_mode='comment',
#             mark_invoice_as_sent=True,
#             attachment_ids= [x for x in attachments],
#         )
#         return {
#             'name': _('Compose Email'),
#             'type': 'ir.actions.act_window',
#             'view_type': 'form',
#             'view_mode': 'form',
#             'res_model': 'mail.compose.message',
#             'views': [(compose_form.id, 'form')],
#             'view_id': compose_form.id,
#             'target': 'new',
#             'context': ctx,
#         }

    @api.multi
    def action_invoice_sent_elect(self):
        """ Open a window to compose an email, with the edi invoice template
            message loaded by default
        """
        assert len(self) == 1, 'This option should only be used for a single id at a time.'
        print "OJO***", self.id
        for record in self:
            #template = self.env.ref('account.email_template_edi_invoice', False)
            mtp = self.env['email.template']
            mail = self.env['mail.mail']
            clave = ''
            # #CAPTURO XML AUTORIZADO PARA ENVIAR AL CLIENTE JUNTO AL PDF
            fact_elect_id = self.env['account.factura.electronica'].search([('factelect_id', '=', record.id)])
            print "fact_elect_id", fact_elect_id
            for clave in fact_elect_id:
                print "CLAVE", clave.clave_acceso
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
        print "ID DOCUMENTO 1:", ids
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
    def action_retention_sent_elect(self):
        """ Open a window to compose an email, with the edi invoice template
            message loaded by default
        """
        assert len(self) == 1, 'This option should only be used for a single id at a time.'
        for record in self:
            #template = self.env.ref('account.email_template_edi_invoice', False)
            mtp = self.env['email.template']
            mail = self.env['mail.mail']
            clave = ''
            # #CAPTURO XML AUTORIZADO PARA ENVIAR AL CLIENTE JUNTO AL PDF
            fact_elect_id = self.env['account.factura.electronica'].search([('factelect_id', '=', record.id)])
            print "fact_elect_id", fact_elect_id
            for clave in fact_elect_id:
                print "CLAVE", clave.clave_acceso
                claveac = clave.clave_acceso
            name = "%s.xml" % (claveac)
            att = self.env['ir.attachment'].search([('res_id','=',record.id),('res_model','=',self._name),
                                                    ('name','=',name)])

            template = mtp.search([('model_id.model', '=', self._name), ('name', '=', 'RETENCION ELECTRONICA')])
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
    def action_retention_sent_elect_masivo(self):
        """ Open a window to compose an email, with the edi invoice template
            message loaded by default
        """
        ids = self._context['active_ids']
        print "ID DOCUMENTO 1:", ids
        for record in ids:
            #template = self.env.ref('account.email_template_edi_invoice', False)
            mtp = self.env['email.template']
            mail = self.env['mail.mail']
            clave = ''
            # #CAPTURO XML AUTORIZADO PARA ENVIAR AL CLIENTE JUNTO AL PDF
            fact_elect_id = self.env['account.factura.electronica'].search([('factelect_id', '=', record)])
            if fact_elect_id:
                print "fact_elect_id", fact_elect_id
                for clave in fact_elect_id:
                    print "CLAVE", clave.clave_acceso
                    claveac = clave.clave_acceso
                name = "%s.xml" % (claveac)
                att = self.env['ir.attachment'].search([('res_id','=',record),('res_model','=',self._name),
                                                        ('name','=',name)])

            template = mtp.search([('model_id.model', '=', self._name), ('name', '=', 'RETENCION ELECTRONICA')])
            template.attachment_ids = False
            if fact_elect_id:
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

    num_autoelectronica = fields.Char('Autorizacion Electronica', size=100)
    state_factelectro = fields.Selection([('pendiente', 'Pendiente'), ('autorizado', 'Autorizado'), ('firmado', 'Firmado'), ('error', 'Error')], 'Estado FE')
    tipo_comp = fields.Boolean('Factura Electronica', help="Indica si la factura es de tipo electronica")
    factuele_id = fields.One2many('account.factura.electronica', 'factelect_id', 'Factura Electronica')
    date_aut = fields.Datetime('Fecha Autorizacion', readonly=1)
    num_autoreten = fields.Char('Autorizacion Retencion', size=100)
    date_aut_ret = fields.Datetime('Fecha Autorizacion', readonly=1)
    date_emision = fields.Date('Fecha Emision', required=1)
    por_iva = fields.Selection([('10%', '10%'),
                                        ('12%', '12%'),
                                        ('14%', '14%')], '% IVA RIDE', help="Seleccionar el porcentaje de iva para el formato RIDE", required=1)
    is_importa = fields.Boolean('Importacion', help="Indica si la factura es de tipo importacion esta no me afecta al ats")
    #CSV:28-12-2017:Aumento para guardar info electronica offline
    inf_electronica = fields.Text('Info Electronica')

    _defaults = {
        'date_aut': lambda *a: time.strftime('%Y-%m-%d %H:%M:%S'),
        'date_aut_ret': lambda *a: time.strftime('%Y-%m-%d %H:%M:%S'),
        'state_factelectro': lambda * a: 'pendiente',
        'tipo_comp': lambda * a: True,
        'date_emision': lambda *a: time.strftime('%Y-%m-%d'),
        'por_iva': lambda * a: '12%',
    }


class account_factura_electronica(models.Model):
    _name = 'account.factura.electronica'
    _description = 'Facturacion Electronica'

    name = fields.Char('Nombre', size=64)
    clave_acceso = fields.Char('Clave Acceso', size=64)
    clave_contingencia = fields.Char('Clave Contingencia', size=64)
    contingencia = fields.Boolean('Contingencia', help="Indica si la clave de acceso del comprobante es de contingencia")
    cod_comprobante = fields.Char('Codigo Comprobante', size=64)
    factelect_id = fields.Many2one('account.invoice', 'Factura Electronica')
    note = fields.Text('Historial', translate=True)

    _defaults = {
        'name': lambda * a: 'Comprobante Electronico',
    }

