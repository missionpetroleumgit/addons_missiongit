# -*- coding: utf-8 -*-
from openerp import api, fields, models, _
import smtplib
from urlparse import urljoin


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    productions = fields.One2many('mrp.production', 'sale_id', 'Total Productions')
    production_count = fields.Integer(compute='_compute_production_count')

    @api.multi
    @api.depends('order_line.productions')
    def _compute_production_count(self):
        for order in self:
            order.production_count = len(order.productions)

    @api.multi
    def action_open_productions(self):
        self.ensure_one()
        action = self.env.ref('mrp.mrp_production_action').read()[0]
        action.update({'domain': [('id', 'in', self.mapped('productions').ids)]})
        return action

    def action_ship_create(self, cr, uid, ids, context=None):
        """Create the required procurements to supply sales order lines, also connecting
        the procurements to appropriate stock moves in order to bring the goods to the
        sales order's requested location.

        :return: True
        """
        context = dict(context or {})
        context['lang'] = self.pool['res.users'].browse(cr, uid, uid).lang
        procurement_obj = self.pool.get('procurement.order')
        sale_line_obj = self.pool.get('sale.order.line')
        for order in self.browse(cr, uid, ids, context=context):
            proc_ids = []
            vals = self._prepare_procurement_group(cr, uid, order, context=context)
            if not order.procurement_group_id:
                group_id = self.pool.get("procurement.group").create(cr, uid, vals, context=context)
                order.write({'procurement_group_id': group_id})

            for line in order.order_line:
                if line.state == 'cancel':
                    continue
                if 'manufacture' in line.product_id.mapped('route_ids').mapped('location_code'):
                    if not order.productions.filtered(lambda p: p.state not in 'cancel'):
                        line._create_production()
                        continue
                #Try to fix exception procurement (possible when after a shipping exception the user choose to recreate)
                if line.procurement_ids:
                    #first check them to see if they are in exception or not (one of the related moves is cancelled)
                    procurement_obj.check(cr, uid, [x.id for x in line.procurement_ids if x.state not in ['cancel', 'done']])
                    line.refresh()
                    #run again procurement that are in exception in order to trigger another move
                    except_proc_ids = [x.id for x in line.procurement_ids if x.state in ('exception', 'cancel')]
                    procurement_obj.reset_to_confirmed(cr, uid, except_proc_ids, context=context)
                    proc_ids += except_proc_ids
                elif sale_line_obj.need_procurement(cr, uid, [line.id], context=context):
                    if (line.state == 'done') or not line.product_id:
                        continue
                    vals = self._prepare_order_line_procurement(cr, uid, order, line, group_id=order.procurement_group_id.id, context=context)
                    ctx = context.copy()
                    ctx['procurement_autorun_defer'] = True
                    proc_id = procurement_obj.create(cr, uid, vals, context=ctx)
                    proc_ids.append(proc_id)
            #Confirm procurement order such that rules will be applied on it
            #note that the workflow normally ensure proc_ids isn't an empty list
            procurement_obj.run(cr, uid, proc_ids, context=context)

            #if shipping was in exception and the user choose to recreate the delivery order, write the new status of SO
            if order.state == 'shipping_except':
                val = {'state': 'progress', 'shipped': False}

                if (order.order_policy == 'manual'):
                    for line in order.order_line:
                        if (not line.invoiced) and (line.state not in ('cancel', 'draft')):
                            val['state'] = 'manual'
                            break
                order.write(val)
        return True


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    productions = fields.One2many('mrp.production', 'order_line_id', 'Own Productions')

    @api.multi
    def _create_production(self):
        mrp_production = self.env['mrp.production']
        stock_location_route = self.env['stock.location.route']
        for record in self.order_id.order_line:
            if record.product_uom_qty >= record.product_id.qty_available:
                new_production = mrp_production.new(
                    {
                        'product_id': record.product_id.id,
                        'product_qty': record.product_uom_qty,
                        'user_id': record.order_id.user_id.id,
                        'origin': record.order_id.name,
                        'order_line_id': record.id
                    }
                )
                res = new_production.product_id_change(product_id=record.product_id.id, product_qty=record.product_uom_qty)
                values = new_production._convert_to_write(
                    {name: new_production[name] for name in new_production._cache})
                values.update(res['value'])
                mrp_production.create(values)
                record.order_id.action_sent_quotation_mail(record.order_id.id, record.id)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def _get_sale_url(self):
        link = ''
        base_url = self.pool['ir.config_parameter'].get_param(self._cr, self._uid, 'web.base.url')
        for order in self:
            link = urljoin(base_url+'/web?=#id='+str(order.id)+'&view_type=form&model=sale.order&menu_id=411&action=504', '')
        return link

    @api.multi
    def action_sent_quotation_mail(self, order_id, line_id):
        sale_order = self.env['sale.order'].search([('id', '=', order_id)])
        mrp_production = self.env['mrp.production'].search([('origin', '=', sale_order.name),
                                                            ('order_line_id', '=', line_id)])
        remitente = "<daldaz@mission-petroleum.com>"
        destinatario = "<daldaz@mission-petroleum.com>"
        url = self._get_sale_url()
        saleorder = sale_order.name
        mensaje = """
Estimados,

Se ha generado una orden de produccion %s, desde la orden de venta %s.

Link, %s


Saludos Cordiales,

PRODUCCION
MISSIONPETROLEUM S.A.
Av. de Los Shyris N36-188 y Naciones Unidas
Edif. Shyris Park Piso 4, Of. 401 - 402 - 403 - 404
Telf.: (593) 23949380 Ext.: 225 - 226
www.mission-petroleum.com

       """ % (mrp_production.name, saleorder, url)
        username = 'daldaz@mission-petroleum.com'
        password = 'N4nd0MpM1ss10n2018!$!'
        email = """From: %s
        To: %s
        Subject: %s
        %s
        """ % (remitente, destinatario, mrp_production.name, mensaje)
        try:
            smtp = smtplib.SMTP('mail.mission-petroleum.com')
            smtp.starttls()
            smtp.login(username, password)
            smtp.sendmail(remitente, destinatario, email)
            smtp.quit()
        except:
            print """Error: el mensaje no pudo enviarse.
            Compruebe que sendmail se encuentra instalado en su sistema"""
