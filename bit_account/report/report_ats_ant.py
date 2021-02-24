# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution - Ecuador
#    Copyright (C) 2014 BitConsultores (<http://http://bitconsultores-ec.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your data/110G/odooecion) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from datetime import datetime, date, time, timedelta
import calendar
import base64
import openerp
from openerp.tools.translate import _
from openerp.osv import fields, osv
from openerp import models, api, http

from generator_ats import *
import xml
from numpy.ma.core import ids

class report_ats(osv.Model):
    _name = "report.ats"
    _description = 'Archivo ATS'
    
    def generate_XML(self, cr, uid, ids, period_ids, doc, filtro, context):
        is_ats = not filtro or False
        form = doc[2:]
        sust = doc[1:]
        print "periods ids**", period_ids
        period = self.pool.get('account.period').browse(cr, uid, period_ids, context)
        print "PERIOD", period
        my_month = period.date_stop or str(datetime.today().date())
        fecha = datetime.strptime(my_month, "%Y-%m-%d")
        mes = ('00' + str(fecha.month))[-2:]
        anho = str(fecha.year)
        per_stop = mes + anho
        doc += per_stop or my_month
        crearXML(doc)
        
    # HEADER
        company = self.pool.get('res.users').browse(cr, uid, uid, context).company_id
        ruc = company.partner_id.part_number or 'Unknow'
        if ruc == 'Unknow':
            raise osv.except_osv(_('Error!'), 
                _('El contacto asociado a la compañía no tiene definido el RUC.'))
        razon = company.partner_id.name or 'Unknow'
        header = { 'version': str(form) + anho + mes, 'ruc': ruc }
        obj_code = self.pool.get('account.tax.code')
        code_ids = obj_code.search(cr, uid, filtro)
        original = period.state != 'closed' and 'O' or 'S'
        
    # CABECERA FIJA
        head_static = { '101': mes, '102': anho, '201': ruc, '202': razon, '31': original }
        if original == 'S':
            head_static.update({'104': sust})
            
        if is_ats:  # ATS
            ventas_totales = 0
            dicc_ats = {
                            'TipoIDInformante': 'R', 'IdInformante': ruc, 
                            'razonSocial': razon, 'Anio': anho, 'Mes': mes,
                            'numEstabRuc': ruc[-3:], 'codigoOperativo': 'IVA'
                        }
            brw_codes = self.get_formato_anexo(cr, uid, dicc_ats, company, period, context)
            print 'period - 80', type(brw_codes)
            total_ventas = brw_codes and 'saldo_ventas' in brw_codes and brw_codes.pop('saldo_ventas') or 0
            print 'period - 82', type(brw_codes)
            dicc_ats.update({'totalVentas': '%.2f' % (float(total_ventas))})
            print 'period - 84', type(brw_codes)
            header = dicc_ats
            grabarXMLATS(self, cr, uid, brw_codes, header, head_static, is_ats, doc)
        else:   # CODES
            context.update({ 'period_id': period.id })
            brw_codes = obj_code.read(cr, uid, code_ids, ['code','sum_period'], context)
            grabarXML(brw_codes, header, head_static, is_ats, doc)
        
        data_fname = str(doc) + '.xml'
        archivo = '/opt/data/' + data_fname # Valor anterior '/data/110G/odooec/temp/'
        res_model = 'report.ats'
        id = ids and type(ids) == type([]) and ids[0] or ids
        self.load_doc(cr, uid, period.id, id, data_fname, archivo, res_model)
        return {
            'type': 'ir.actions.client',
            'tag': 'reload'
        }
        
    
    def action_formATS(self, cr, uid, ids, context=None):
        doc = 'AT'
        filtro = []
        form = self.read(cr, uid, ids)[0]
        period = form.get('period_id')
        print "IDS", ids
        print "PERIOD", period
        print "PERIOD 2", period[0]
        period_ids = [period[0]]
        print "PERIOD 3", ids
        self.generate_XML(cr, uid, ids, period_ids, doc, filtro, context)
        
    def get_formato_anexo(self, cr, uid, dicc_ats, company, period, context):
        obj_inv = self.pool.get('account.invoice')
        tags_ats = {'compras': [], 'ventas': [], 'ventasEstablecimiento': [], 'anulados': []}
        print 'tags_ats', tags_ats

    # COMPRAS - OK
        args_compras = [('company_id', '=', company.id), ('period_id', '=', period.id), \
                        ('currency_id', '=', company.currency_id.id), \
                        ('type', '=', 'in_invoice'), \
                        ('state', 'in', ['open', 'paid'])]
        all_inv_compras = obj_inv.search(cr, uid, args_compras)
        brw_invoices = obj_inv.browse(cr, uid, all_inv_compras, context)
        dicc_invs = self.getTagCompra(cr, uid, brw_invoices)
        tags_ats.get('compras').append(dicc_invs)
        print 'tags_ats - compras', type(tags_ats)
    # VENTAS - OK
        args_ventas = [ ('company_id', '=', company.id), ('period_id', '=', period.id), \
                        ('currency_id', '=', company.currency_id.id), \
                        ('type', '=', 'out_invoice'), \
                        ('state', 'in', ['open', 'paid'])]
        all_inv_ventas = obj_inv.search(cr, uid, args_ventas)
        brw_invoices = obj_inv.browse(cr, uid, all_inv_ventas, context)
        
        dicc_clientes = self.getTagVenta(cr, uid, brw_invoices)
        vent = dicc_clientes.pop('total_ventas')
        tags_ats.get('ventas').append(dicc_clientes)
        tags_ats.update({'saldo_ventas': vent})
        print 'tags_ats - ventas', type(tags_ats)
    # CANCEL
        args_cancel = [ ('company_id', '=', company.id), ('period_id', '=', period.id), \
                        ('currency_id', '=', company.currency_id.id), \
                        ('state', 'in', ['cancel'])]
        all_inv_cancel = obj_inv.search(cr, uid, args_cancel)
        brw_invoices = obj_inv.browse(cr, uid, all_inv_cancel, context)
        dicc_null = self.getTagCancelada(brw_invoices)
        tags_ats.get('anulados').append(dicc_null)
        print 'tags_ats - anulados', type(tags_ats)
        return tags_ats
        
    def getTagVenta(self, cr, uid, brw_invoices):
        total_ventas = 0
        dicc_type_cliente = { 'r': '04', 'c': '05', 'p': '06', 's': '07' }
        dicc_clientes = {}
        for invoice in brw_invoices:
            is_new_node = True
            tipo_cliente = dicc_type_cliente.get(invoice.partner_id.part_type)
            num_cliente = tipo_cliente != '07' and invoice.partner_id.part_number or '9999999999999'
            forma_pago = invoice.partner_id.f_pago
            tipo_doc = invoice.document_type.code
            if tipo_doc == '01':
                tipo_doc = '18'
            
            my_key = str(tipo_cliente) + str(num_cliente) + str(tipo_doc)
            if my_key in dicc_clientes.keys():
                vals = dicc_clientes.get(my_key)
    #ACTUALIZAR VALS
                obj_inv_tax = self.pool.get('account.invoice.tax')
                inv_tax_ids = obj_inv_tax.search(cr, uid, [('invoice_id', '=', invoice.id), ('deduction_id', '!=', None)])
                print "INVOICE TAX", inv_tax_ids
                inv_tax_obj = obj_inv_tax.browse(cr, uid, inv_tax_ids)
                cod_imp = []
                res = []
                cont = 0            
                for impuesto in  inv_tax_obj:
                    print "CODIGO**", impuesto.base_code_id
                    if impuesto.base_code_id:
                        tn = 'iva'
                    else:
                        tn = 'renta'
    
                    cod_imp.append(tn)
                    if tn == 'iva':
                        vals.update({ 'valorRetIva': '%.2f' % (float('valorRetIva' in vals and vals.get('valorRetIva') or 0) + 0.00) })
                        vals.update({ 'montoIva': '%.2f' % (float('montoIva' in vals and vals.get('montoIva') or 0) + 0.00) })
                    else:
                        vals.update({ 'valorRetRenta': '%.2f' % (float('valorRetRenta' in vals and vals.get('valorRetRenta') or 0) + abs(impuesto.tax_amount)) })
                is_new_node = False 
            else:
    #ACTUALIZAR VALS
                obj_inv_tax = self.pool.get('account.invoice.tax')
                inv_tax_ids = obj_inv_tax.search(cr, uid, [('invoice_id', '=', invoice.id), ('deduction_id', '!=', None)])
                print "INVOICE TAX", inv_tax_ids
                inv_tax_obj = obj_inv_tax.browse(cr, uid, inv_tax_ids)
                cod_imp = []
                res = []
                cont = 0            
                for impuesto in  inv_tax_obj:
                    print "CODIGO**", impuesto.base_code_id
                    if impuesto.base_code_id:
                        tn = 'iva'
                    else:
                        tn = 'renta'
                    if tn == 'iva':
                        vals = {
                                    'tpIdCliente': tipo_cliente,
                                    'idCliente': num_cliente,
                                    'tipoComprobante': tipo_doc,
                                    'valorRetIva': 0.00,
                                    'formaPago':forma_pago,
                                }
                    else:
                        vals = {
                                    'tpIdCliente': tipo_cliente,
                                    'idCliente': num_cliente,
                                    'tipoComprobante': tipo_doc,
                                    'valorRetRenta': abs(impuesto.tax_amount),
                                    'formaPago':forma_pago,
                                }
                if tipo_cliente != '07':
                    vals.update({ 'parteRel': 'SI' })
                else:
                    vals.update({ 'parteRel': 'NO' })
                    
                
            vals.update({ 'numeroComprobantes': ('numeroComprobantes' in vals and \
                                            vals.get('numeroComprobantes') or 0) + 1 })
            dicc_Taxes = self.cruzarTax(invoice)
            
            base_is_0 = abs('iva_cero' in dicc_Taxes and dicc_Taxes.get('iva_cero').get('base') or 0.00)
            vals.update({ 'baseNoGraIva': '%.2f' % (float('baseNoGraIva' in vals and \
                                            vals.get('baseNoGraIva') or 0) + base_is_0) })         
            
            base_no_0 = abs('iva' in dicc_Taxes and dicc_Taxes.get('iva').get('base') or 0.00)
            vals.update({ 'baseImponible': '%.2f' % (float('baseImponible' in vals and \
                                            vals.get('baseImponible') or 0) + invoice.amount_untaxed) })
            
            vals.update({ 'baseImpGrav': '0.00' })  # *** PENDIENTE
            
            amount_IVA = abs('iva' in dicc_Taxes and dicc_Taxes.get('iva').get('amount') or 0.00)
            vals.update({ 'montoIva': '%.2f' % (float('montoIva' in vals and vals.get('montoIva') or 0) + (invoice.amount_untaxed*12)/100 ) })
            vals.update({ 'montoIce': '0.00' })  # *** PENDIENTE

            am_ret_IVA = abs('ret_iva' in dicc_Taxes and dicc_Taxes.get('ret_iva').get('percent') or 0.00)
            vals.update({ 'valorRetIva': '%.2f' % (float('valorRetIva' in vals and vals.get('valorRetIva') or 0) + ((invoice.amount_untaxed*12)/100)*am_ret_IVA) })
             
            am_ret_FTE = abs('ret_fte' in dicc_Taxes and dicc_Taxes.get('ret_fte').get('amount') or 0.00)
            vals.update({ 'valorRetRenta': '%.2f' % (float('valorRetRenta' in vals and vals.get('valorRetRenta') or 0)) })
                       
            vals.update({ 'codEstab': tipo_cliente == '04' and num_cliente[-3:] or '001' })  # *** PENDIENTE
            
            vals.update({ 'ventasEstab': '%.2f' % (float('ventasEstab' in vals and vals.get('ventasEstab') or 0) + invoice.amount_untaxed) })
            
            dicc_clientes.update({ my_key: vals })
        
            total_ventas += invoice.amount_untaxed
        dicc_clientes.update({ 'total_ventas': total_ventas })
        return dicc_clientes
    
    def getTagCancelada(self, brw_invoices):
        tags = {}
        for invoice in brw_invoices:
            tag = {}
            tipo_doc = invoice.document_type.code
            tag.update({ 'tipoComprobante': tipo_doc })
            tag.update({ 'Establecimiento': invoice.authorization_id.serie_emission or '999' })
            tag.update({ 'puntoEmision': invoice.authorization_id.serie_entity or '999' })
            tag.update({ 'secuencialInicio': invoice.authorization_id.num_start })
            tag.update({ 'secuencialFin': invoice.authorization_id.num_end })
            tag.update({ 'autorizacion': invoice.number_seq })
            tags.update({ invoice.id: tag })
        return tags
        
    
    def getTagCompra(self, cr, uid, brw_invoices):
        dicc_type_prov = { 'r': '01', 'c': '02', 'p': '03' }
        tags = {}
        for invoice in brw_invoices:
            tag = {}
            if invoice.partner_id.part_type not in dicc_type_prov:
                raise osv.except_osv(_('Error!'), 
                                    _('Existe un proveedor que no tiene definido el Tipo de identificación.'))
            tipo_prov = dicc_type_prov.get(invoice.partner_id.part_type)
            if not invoice.partner_id.part_number:
                raise osv.except_osv(_('Error!'), 
                                    _('Existe un proveedor que no tiene definido el RUC, pasaporte ó cédula.'))
            num_prov = invoice.partner_id.part_number
            tipo_doc = invoice.document_type.code
            if tipo_doc == '02':
                tag.update({ 'codSustento': '02' })  # *** PENDIENTE
            else:
                tag.update({ 'codSustento': '01' })
            tag.update({ 'ifact': invoice.id })  # *** PENDIENTE
            tag.update({ 'tpIdProv': tipo_prov })
            tag.update({ 'idProv': num_prov })
            tag.update({ 'tipoComprobante': tipo_doc })
            tag.update({ 'parteRel': 'SI' })
            if tipo_prov == '03':   # *** PENDIENTE
                tag.update({ 'tipoProv': 'SI' })
                raise osv.except_osv(_('Error!'), 
                                _('Existe un proveedor que tiene definido pasaporte. \n'\
                                  + 'Está pendiente esta validación.'))
            tag.update({ 'fechaRegistro': self.my_format_date(invoice.date_invoice) })
            tag.update({ 'establecimiento': invoice.authorization_id.serie_emission or '999' })
            tag.update({ 'puntoEmision': invoice.authorization_id.serie_entity or '999' })
            if len(invoice.number_seq)<=9:
                tag.update({ 'secuencial': invoice.number_seq })
            elif len(invoice.number_seq)>9:
                tag.update({ 'secuencial': invoice.number_seq[8:] })
            tag.update({ 'fechaEmision': self.my_format_date(invoice.date_invoice) })  # *** PENDIENTE
            if invoice.is_inv_elect:
                tag.update({ 'autorizacion': invoice.elect_authorization })
            else:
                tag.update({ 'autorizacion': invoice.authorization_id.name })
            
            dicc_Taxes = self.cruzarTax(invoice)
#CSV-24-08-2016/AUMENTO PARA ACTUALIZAR LAS BASES GRABADAS Y NO GRABADAS Y RETENCIONES DE IVA
            bas_grav = 0.00
            m_iva = 0.00
            bas_ngrav = 0.00
            iva10 = 0.00
            iva20 = 0.00
            iva30 = 0.00
            iva50 = 0.00
            iva70 = 0.00
            iva100 = 0.00
            obj_fact_imp = self.pool.get('account.invoice.tax')
            args_fact_imp = [('invoice_id', '=', invoice.id)]
            fact_imp_ids = obj_fact_imp.search(cr, uid, args_fact_imp)
            for factt in obj_fact_imp.browse(cr, uid, fact_imp_ids, {}):
                print "CODIGO IMP COMPRAS**", factt.base_code_id.code
                if factt.base_code_id.code == '500' or factt.base_code_id.code == '500 14%':
                    bas_grav = abs(factt.base_amount)
                    m_iva = abs(factt.tax_amount)
                elif factt.base_code_id.code == '507':
                    bas_ngrav = abs(factt.base_amount)
                elif factt.base_code_id.code == '721':
                    iva10 = abs(factt.tax_amount)
                elif factt.base_code_id.code == '723':
                    iva20 = abs(factt.tax_amount)
                elif factt.base_code_id.code == '725':
                    iva30 = abs(factt.tax_amount)
                elif factt.base_code_id.code == '727':
                    iva50 = abs(factt.tax_amount)
                elif factt.base_code_id.code == '729':
                    iva70 = abs(factt.tax_amount)
                elif factt.base_code_id.code == '731':
                    iva100 = abs(factt.tax_amount)
            
            base_is_0 = 'iva_cero' in dicc_Taxes and dicc_Taxes.get('iva_cero').get('base') or 0.00
            if base_is_0 > 0:
                tag.update({ 'baseNoGraIva': '%.2f' % float(bas_ngrav) })
            else:
                tag.update({ 'baseNoGraIva': '%.2f' % float(base_is_0) })
            
            base_no_0 = 'iva' in dicc_Taxes and dicc_Taxes.get('iva').get('base') or 0.00
            if tipo_doc == '02':
                tag.update({ 'baseImponible': '%.2f' % float(invoice.amount_untaxed) })
            else:
                tag.update({ 'baseImponible': '%.2f' % float(bas_grav) })
            
            tag.update({ 'baseImpGrav': '0.00' })  
            tag.update({ 'baseImpExe': '0.00' })  # *** PENDIENTE
            
            amount_IVA = 'iva' in dicc_Taxes and dicc_Taxes.get('iva').get('amount') or 0.00
            tag.update({ 'montoIva': '%.2f' % float(m_iva) })
            tag.update({ 'montoIce': '0.00' })  # *** PENDIENTE
            
            pc_ret_IVA = abs('ret_iva' in dicc_Taxes and int(dicc_Taxes.get('ret_iva').get('percent') * 100) or 0.00)
            am_ret_IVA = abs('ret_iva' in dicc_Taxes and dicc_Taxes.get('ret_iva').get('amount') or 0.00)
            tag.update({ 'valRetBien10': '%.2f' % float(iva10 or 0) })
            tag.update({ 'valRetServ20': '%.2f' % float(iva20 or 0) })
            tag.update({ 'valorRetBienes': '%.2f' % float(iva30 or 0) })
            tag.update({ 'valRetServ50': '%.2f' % float(iva50 or 0) })
            tag.update({ 'valorRetServicios': '%.2f' % float(iva70 or 0) })
            tag.update({ 'valRetServ100': '%.2f' % float(iva100 or 0) })
            if pc_ret_IVA != 0 and pc_ret_IVA != 10 and pc_ret_IVA !=20 and pc_ret_IVA != 30 and pc_ret_IVA != 50 and pc_ret_IVA != 70 and pc_ret_IVA != 100:
                raise osv.except_osv(_('Error!'),
                                _('Existe una factura con retención de IVA no válida. \n'\
                                  + 'Revise que los impuestos del IVA estén definidos (¿ Es el IVA ?).\n'
                                  + 'La retención de IVA debe ser de 0, 10, 20, 30, 50, 70 ó 100 %.'))
                
            tag.update({ 'pagoLocExt': '01' })  # *** PENDIENTE
            if tag.get('pagoLocExt') == '02':
                tag.update({ 'paisEfecPago': '01' })  # *** PENDIENTE
                tag.update({ 'aplicConvDobTrib': 'SI' })  # *** PENDIENTE                
                if tag.get('aplicConvDobTrib') == 'NO':
                    tag.update({ 'pagExtSujRetNorLeg': 'SI' })  # *** PENDIENTE  
                tag.update({ 'pagoRegFis': 'SI' })  # *** PENDIENTE   
                tag.update({ 'formaPag': '107' })  # *** PENDIENTE   
                tag.update({ 'codRetAir': '332' })  # *** PENDIENTE   
                tag.update({ 'baseImpAir': tag.get('baseImponible') })  # *** PENDIENTE   
                tag.update({ 'porcentajeAir': tag.get('montoIva') })    # *** PENDIENTE   
                tag.update({ 'valRetAir': '%.2f' % float(am_ret_IVA) }) # *** PENDIENTE   
                tag.update({ 'fechaPagoDiv': str(invoice.date_invoice) })    # *** PENDIENTE
                tag.update({ 'imRentaSoc': '327' })    # *** PENDIENTE
                tag.update({ 'anioUtDiv': '2015' })    # *** PENDIENTE
                tag.update({ 'NumCajBan': '338' })    # *** PENDIENTE  
                tag.update({ 'PrecCajBan': '338' })    # *** PENDIENTE
                
            obj_ded = self.pool.get('account.deduction')
            args_ret = [('invoice_id', '=', invoice.id)]
            ret_ids = obj_ded.search(cr, uid, args_ret)
            if len(ret_ids)>0:
                for brw_ded in obj_ded.browse(cr, uid, ret_ids, {}):               
                    tag.update({ 'estabRetencion1': brw_ded.authorization_id.serie_entity or '999' }) 
                    tag.update({ 'ptoEmiRetencion1': brw_ded.authorization_id.serie_emission or '999' }) 
                    tag.update({ 'secRetencion1': brw_ded.number }) 
                    tag.update({ 'autRetencion1': brw_ded.authorization_id.name }) 
                    tag.update({ 'fechaEmiRet1': self.my_format_date(brw_ded.emission_date) })
            else:
                tag.update({ 'secRetencion1': '0' })
            
            obj_reemb = self.pool.get('account.invoice')
            args_reemb = [('origin', '=', invoice.number), ('type', '=', 'in_refund')]
            reem_ids = obj_reemb.search(cr, uid, args_reemb)
            for reemb in obj_reemb.browse(cr, uid, reem_ids, {}):
                tag.update({ 'docModificado': reemb.document_type.code or '03' })    # *** PENDIENTE
                tag.update({ 'estabModificado': reemb.authorization_id.serie_entity or '999' })    # *** PENDIENTE
                tag.update({ 'ptoEmiModificado': reemb.authorization_id.serie_emission or '999' })    # *** PENDIENTE
                tag.update({ 'secModificado': reemb.number_seq })    # *** PENDIENTE
                tag.update({ 'autModificado': reemb.authorization_id.name })    # *** PENDIENTE
                tag.update({ 'tipoComprobanteReemb': invoice.document_type.code })    # *** PENDIENTE
                tag.update({ 'tpIdProvReemb': tipo_prov })    # *** PENDIENTE
                tag.update({ 'idProvReemb': num_prov })    # *** PENDIENTE
                tag.update({ 'establecimientoReemb': invoice.authorization_id.serie_entity or '999' })    # *** PENDIENTE
                tag.update({ 'puntoEmisionReemb': invoice.authorization_id.serie_emission or '999' })    # *** PENDIENTE
                tag.update({ 'secuencialReemb': invoice.number_seq })    # *** PENDIENTE
                tag.update({ 'fechaEmisionReemb': self.my_format_date(invoice.date_invoice) })    # *** PENDIENTE
                tag.update({ 'autorizacionReemb': invoice.authorization_id.name })    # *** PENDIENTE
                
                tag.update({ 'baseImponibleReemb': '%.2f' % float(0) })    # *** PENDIENTE
                tag.update({ 'baseImpGravReemb': '%.2f' % float(0) })    # *** PENDIENTE
                tag.update({ 'baseNoGraIvaReemb': '%.2f' % float(0) })    # *** PENDIENTE
                tag.update({ 'baseImpExeReemb': '%.2f' % float(0) })    # *** PENDIENTE
                tag.update({ 'totbasesImpReemb': '%.2f' % float(0) })    # *** PENDIENTE
                tag.update({ 'montoIceReemb': '%.2f' % float(0) })    # *** PENDIENTE
                tag.update({ 'montoIvaRemb': '%.2f' % float(0) })    # *** PENDIENTE
                    
            tags.update({ invoice.id: tag })
            
        return tags

    def cruzarTax(self, invoice):
        dicc_Taxes = {}
        
        l_tax_inv = []
        l_tax_base = []
        l_tax_amount = []
        for tax_inv in invoice.tax_line:
            tmp_tax_inv = {
                            'tax_code_id': tax_inv.tax_code_id.id,
                            'base_code_id': tax_inv.base_code_id.id
                           }
            if tmp_tax_inv not in l_tax_inv:
                l_tax_inv.append(tmp_tax_inv)
                l_tax_base.append(tax_inv.base)
                l_tax_amount.append(tax_inv.amount)
        
        _type = False
        l_tax_deduc = []
        for line in invoice.invoice_line:
            for tax_line in line.invoice_line_tax_id:
                percent = 0
                tmp_tax_line = {}
                if tax_line.child_depend:
                    for child in tax_line.child_ids:
                        child_tax_line = { 
                                            'tax_code_id': child.tax_code_id.id,
                                            'base_code_id': child.base_code_id.id
                                          }
                        if child_tax_line in l_tax_inv:
                            tmp_tax_line = child_tax_line
                            _type = 'ret_iva'
                            percent = child.amount
                else:
                    tmp_tax_line =  {
                                        'tax_code_id': tax_line.tax_code_id.id,
                                        'base_code_id': tax_line.base_code_id.id
                                     }
                    if tax_line.is_iva:
                        _type = tax_line.amount and 'iva' or 'iva_cero'
                    else:
                        _type = 'ret_fte'
                        
                if tmp_tax_line in l_tax_inv:
                    pos_ids = l_tax_inv.index(tmp_tax_line)
                    total_base = total_monto = 0                  
                    for _id in type(pos_ids) == type([]) and pos_ids or [pos_ids]:
                        total_monto += l_tax_amount[_id]
                        total_base += l_tax_base[_id]
                    
                    sum_tax_m = _type in dicc_Taxes and dicc_Taxes.get(_type).get('amount') or 0
                    sum_tax_b = _type in dicc_Taxes and dicc_Taxes.get(_type).get('base') or 0
                    dicc_Taxes.update({ _type: { 
                                            'base': sum_tax_b + total_base,
                                            'amount': sum_tax_m + total_monto,
                                            'percent': percent } })
        print 'Probando lo que devuelve', dicc_Taxes
        return dicc_Taxes
    
    def my_format_date(self, str_date):
        str_date = str_date or '1980-01-01'
        fecha = str_date and datetime.strptime(str_date, '%Y-%m-%d').date()
        return fecha.strftime('%d/%m/%Y')
    
    def load_doc(self, cr, uid, period_id, id, data_fname, archivo, res_model):
        datas = open(archivo, 'rb')
        attach_vals = {
            'name': data_fname,
            'datas_fname': data_fname,
            'res_model': res_model,
#             'parent_id': activity.report_directory_id.id,
            'datas': base64.encodestring(datas.read()),
            'type': 'binary',
            'file_type': 'file_type',
            'res_id': period_id
        }
        if id:
            attach_vals.update( {'res_id': id} )
        self.pool.get('ir.attachment').create(cr, uid, attach_vals)
         

    _columns = {
        'name':fields.char('', size=64, required=False, readonly=False),
        'data':fields.binary('', filters=None),
        'period_id':fields.many2one('account.period', 'Periodo', required=True),
    }
report_ats()