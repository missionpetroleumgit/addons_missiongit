# -*- coding: utf-8 -*-
import unicodedata
from openerp import models, fields, api
from string import upper
from openerp.exceptions import except_orm, Warning
import base64
import os
import StringIO
from datetime import datetime, date, time, timedelta
#**************************************************
import time
import math
from time import strftime
from decimal import *
from xml.dom.minidom import Document
from suds.client import Client
from math import *
from XadesBes import jarWrapper
from xml.dom.minidom import parse, parseString
import os, ssl


class wizard_factura_electronica(models.TransientModel):
    _name = 'wizard.factura.electronica'

    data = fields.Binary()
    name = fields.Char('Nombre')
    mensaje = fields.Text('Resultado', readonly=1)
    formulario = fields.Selection([('normal','normal'), ('contingencia','contingencia')], 'Emision')
    contingencia = fields.Char('Clave Contingencia', size=38)
    company = fields.Many2one('res.company', 'Compania')
    version = fields.Char('Version Comprobante', size=20)
    ambiente = fields.Selection([('pruebas','PRUEBAS'), ('produccion','PRODUCCION')], 'Ambiente')

    _defaults = {
        'date_aut': lambda *a: time.strftime('%Y-%m-%d %H:%M:%S'),
        'date_aut_ret': lambda *a: time.strftime('%Y-%m-%d %H:%M:%S'),
        'state_factelectro': lambda * a: 'pendiente',
        'tipo_comp': lambda * a: True,
        'date_emision': lambda *a: time.strftime('%Y-%m-%d'),
        'formulario': lambda * a: 'normal',
        'version': lambda * a: '1.1.0',
        'ambiente': lambda * a: 'produccion',
        'company': lambda self, cr, uid, c: self.pool.get('res.company')._company_default_get(cr, uid, 'wizard.factura.electronica', context=c)
    }

    @api.multi
    def cron_generate_file(self, autorizar=True, mails=True):

        datebefore = datetime.now() - timedelta(days=1)
        invoices = self.env['account.invoice'].search(
            [('date_invoice', '=', datebefore.strftime('%Y-%m-%d')),
             ('company_id', '=', self.env.user.company_id.id)])

        # invoices = self.env['account.invoice'].browse([91550,81507])
        # Firma Facturas
        self.generate_file({'active_ids': invoices.ids})
        if autorizar:
            # Autoriza facturas
            self.generate_file({'active_ids': invoices.ids})
        if mails:
            # envio  mail de todas ,  en el metodo filtro solo autoriz.
            invoices.action_invoice_sent_elect_masivo()


    @api.multi
    def generate_file(self, context={}):
        # DECLARO VARIABLES Y DOC PARA FORMAR EL XML
        mensaje = ""
        doc = Document()
        doc1 = Document()
        cod_num = '12345678'
        serie = '001001'
        # valores por defecto cuando este metodo es llamado desde el cron
        id_ambiente = 'produccion'
        version = '1.1.0'
        id_formulario = 'normal'
        cconti = ''
        record = None
        # diccionario si viene por contexto (wizard)  array si viene de metodo cron
        ids = context.get('active_ids',[])
        for record in self:
            id_ambiente = record.ambiente
            version = record.version
            id_formulario = record.formulario
            compania = record.company
            cconti = record.contingencia

        print "ID DOCUMENTO 1:", ids

        # for record in self:
        #     id_m = record.id
        #CSV:29-12-2017:INICIALIZO LOS WS SRI
        # id_ambiente = record.ambiente
        if id_ambiente == 'pruebas':
            if (not os.environ.get('PYTHONHTTPSVERIFY', '') and 
		getattr(ssl, '_create_unverified_context', None)):
                ssl._create_default_https_context = ssl._create_unverified_context
            ambiente = '1'
            #CSV:28-12-2017: WS ON-LINE PRUEBAS
            #url = 'https://celcer.sri.gob.ec/comprobantes-electronicos-ws/RecepcionComprobantes?wsdl'
            #url1 = 'https://celcer.sri.gob.ec/comprobantes-electronicos-ws/AutorizacionComprobantes?wsdl'
            url = 'https://celcer.sri.gob.ec/comprobantes-electronicos-ws/RecepcionComprobantesOffline?wsdl'
            url1 = 'https://celcer.sri.gob.ec/comprobantes-electronicos-ws/AutorizacionComprobantesOffline?wsdl'
            client = Client(url)
            client1 = Client(url1)
            if client and client1:
                print "OK SRI"
            else:
                raise Warning(('Atencion !'), ('No responde SRI intente mas tarde!'))
        elif id_ambiente == 'produccion':
            if (not os.environ.get('PYTHONHTTPSVERIFY', '') and 
                getattr(ssl, '_create_unverified_context', None)):
                ssl._create_default_https_context = ssl._create_unverified_context
            ambiente = '2'
            #CSV:28-12-2017: WS ON-LINE PRODUCCION
            #url = 'https://cel.sri.gob.ec/comprobantes-electronicos-ws/RecepcionComprobantes?wsdl'
            #url1 = 'https://cel.sri.gob.ec/comprobantes-electronicos-ws/AutorizacionComprobantes?wsdl'
            url = 'https://cel.sri.gob.ec/comprobantes-electronicos-ws/RecepcionComprobantesOffline?wsdl'
            url1 = 'https://cel.sri.gob.ec/comprobantes-electronicos-ws/AutorizacionComprobantesOffline?wsdl'
            client = Client(url)
            client1 = Client(url1)
            if client and client1:
                print "OK SRI"
            else:
                raise Warning(('Atencion !'), ('No responde SRI intente mas tarde!'))
        #CARGO ARCHIVO FIRMA DIGITAL
        if self._uid:
            arcfd = self.env.user.company_id
            print "OBJETO USER", arcfd
            firmadig = arcfd.name
            print "TIPO", type(firmadig)
            if firmadig:
                print "FIRMA DIGITAL", firmadig
            else:
                raise Warning('Atencion !, Suba el archivo de Firma Digital en su Usuario!')
        # OBTENER DATOS DE LA COMPANIA
        user = self.env.user
        direccion = ''
        if user.company_id.partner_id.street and user.company_id.partner_id.street2:
            direccion = user.company_id.partner_id.street + ' Y ' + user.company_id.partner_id.street2
        elif user.company_id.partner_id.street and not user.company_id.partner_id.street2:
            direccion = user.company_id.partner_id.street
        elif user.company_id.partner_id.street2 and not  user.company_id.partner_id.street:
            direccion = user.company_id.partner_id.street2
        direccion = str(self.delete_ascii(direccion))
        print "direccion", direccion
        # OBTENER DATOS DE LA FACTURA
        #         id_header = self._context['active_id']
        #         print "ID DOCUMENTO:",id_header
        #CSV:28-12-2017:ONLINE
        #factura = self.env['account.invoice'].browse([id_header])
        for factura in self.env['account.invoice'].browse(ids):
            #try:
            if not record:
                # Si se llama desde el cron la compania esta vacia, utilizo la de la factura.
                compania = factura.company_id
            doc = Document()
            doc1 = Document()
            res_sri = False
            vals_accinvws1 = {}
            print "Factura", factura
            t_comp = factura.type
            print "TIPO COMPROBANTE", t_comp
            if factura.state_factelectro == 'autorizado' or factura.type not in ('out_invoice','out_refund'):
                continue
            if factura.state_factelectro not in ('autorizado', 'firmado'):
                secuencia = factura.number_seq
                #FECHA EMISION DE COMPROBANTE ELECTRONICO
                fechasf = factura.date_emision
                lfecha =  fechasf.split('-')
                print "list fecha", lfecha
                fecha = lfecha[2]+"/"+lfecha[1]+"/"+lfecha[0]
                print "FECHA EMISION ELECTRONICA", fecha
                #FECHA EMISION FACTURA
                fechasfe = factura.date_invoice
                lfechae =  fechasfe.split('-')
                print "list fecha factura", lfechae
                fechafact = lfechae[2]+"/"+lfechae[1]+"/"+lfechae[0]
                print "FECHA FACTURA", fechafact
                #DIRECCION CLIENTE/PROVEEDOR COMPROBANTE
                dfactu = factura.partner_id.street
                dfactu2 = factura.partner_id.street2
                cmail = factura.partner_id.email
                if cmail:
                    cliemail = cmail
                else:
                    raise Warning(('Atencion !'), ('Ingrese el Email del cliente en la ficha!'))
                if dfactu and dfactu2:
                    dfactuf = dfactu + dfactu2
                elif dfactu and not dfactu2:
                    dfactuf = dfactu
                elif dfactu2 and not dfactu:
                    dfactuf = dfactu2
                else:
                    dfactuf = unicode('NA')
                dfactuf = str(self.delete_ascii(dfactuf))
                print "DIR FACTU", dfactuf

                cod_ident = factura.partner_id.cod_type_ident
                print "COD IDENT", cod_ident
                #name_rzc = factura.partner_id.name
                name_rzc = self.delete_ascii(factura.partner_id.name)
                id_rzc = factura.partner_id.part_number
                tot_simp = factura.amount_untaxed
                print "TOTAL SI", tot_simp
                invdet_des = self.env['account.invoice.line'].search([('invoice_id', '=', factura.id)])
                print "LISTA DETALLE DE LA FACTURA", invdet_des
                descuentt = 0
                for det_fact in invdet_des:
                    id_line=det_fact.id
                    print "ID LINE", id_line
                    if det_fact.discount > 0:
                        descuentt += round(((det_fact.price_unit*det_fact.quantity)*det_fact.discount)/100, 2)
                    # else:
                    #     descuentt = det_fact.discount
                #tot_desc = factura.amount_discount
                tot_desc = descuentt
                print "TOTAL DES", tot_desc
                #DIRECCION SUCURSAL EMITE COMPROBANTE
                id_pars = self.env['res.partner'].search([('ref', '=', 'COEBIT'),('company_id', '=', self.env.user.company_id.id)])
                print "ID PART", id_pars.id
                id_pars_add = self.env['res.partner'].search([('id', '=', id_pars.id)])

                if id_pars_add:
                    d_suc1 = id_pars_add.street
                    d_suc2 = id_pars_add.street2
                    if d_suc1 and d_suc2:
                        dsucuf = str(d_suc1.encode('UTF-8')) +" "+ str(d_suc2.encode('UTF-8'))
                    elif d_suc1 and not d_suc2:
                        dsucuf = str(d_suc1.encode('UTF-8'))
                    elif d_suc2 and not d_suc1:
                        dsucuf = str(d_suc2.encode('UTF-8'))
                    else:
                        dsucuf = ''
                else:
                    raise Warning(('Atencion !'), ('Ingrese Informacion de la sucursal CALLE1/CALLE2'))
                print "DIRECCION SUCUR", dsucuf

                if factura.partner_id.obli_contab:
                    obli_contab = factura.partner_id.obli_contab
                    if obli_contab == 'SI':
                        cod_posfis = factura.partner_id.cod_posfis
                    else:
                        cod_posfis = '000'
                else:
                    raise Warning(('Atencion !'), ('Ingrese Informacion Fiscal en la ficha del cliente/proveedor!'))
                if factura.authorization_id.serie_entity:
                    fent = str(factura.authorization_id.serie_entity).strip()
                    print "ENTIDAD", fent
                else:
                    raise Warning(('Atencion !'), ('Ingrese Serie entidad de la factura!'))
                if factura.authorization_id.serie_emission:
                    femi = str(factura.authorization_id.serie_emission).strip()
                    print "EMISION", femi
                else:
                    raise Warning(('Atencion !'), ('Ingrese Serie emision de la factura!'))
                #Para el caso de las notas de credito saco la emision y entidad de comprobante de origen
                if t_comp == 'out_refund':
                    obj_id_nc = self.env['account.invoice'].search([('type', '=', 'out_invoice'), ('number', '=', factura.origin)])
                    #obj_id_nc = self.env['account.invoice'].browse(id_nc)[0]
                    if obj_id_nc:
                        ent_dm =  str(obj_id_nc.authorization_id.serie_entity).strip()
                        emi_dm = str(obj_id_nc.authorization_id.serie_emission).strip()
                        num_fact_ori = str(obj_id_nc.number_seq)
                        fech_dm = obj_id_nc.date_invoice
                        lfech_dm =  fech_dm.split('-')
                        print "list fecha factura", lfech_dm
                        flfech_dm = lfech_dm[2]+"/"+lfech_dm[1]+"/"+lfech_dm[0]
                        print "FECHA FACTURA MODIFICAR", flfech_dm


                # OBTENER DATOS DE LOS IMPUESTOS
                tax_id = self.env['account.invoice.tax'].search([('invoice_id', '=', factura.id), ('deduction_id', '=', False)])
                print "LISTA IMPUESTOS", tax_id
                for imp in tax_id:
                    print "LISTA IMPUESTOS 1", imp.tax_code_id
                    print "LISTA IMPUESTOS 2", imp.tax_code_id.cod_imp_fe
                # OBTENER DATOS DE LAS RETENCIONES
                ret_id = self.env['account.invoice.tax'].search([('invoice_id', '=', factura.id), ('deduction_id', '!=', False)])
                print "LISTA RETENCIONES", ret_id
                ret_det = self.env['account.invoice.tax'].browse(ret_id)
                # OBTENER DATOS DETALLE DE LA FACTURA
                invdet_id = self.env['account.invoice.line'].search([('invoice_id', '=', factura.id)])
                print "LISTA DETALLE DE LA FACTURA", invdet_id
                #**********************CONDICION FACTURA DE CLIENTE******************************************
                if t_comp == 'out_invoice':
                    cod_comp = '01'
                    # OBTENGO DATOS DEL FORM

                    print"version: ",version

                    print "compania: ",compania.id
                    # Obtener Informacion de la compania
                    lineas = self.env['res.company'].browse([compania.id])[0]
                    print"lineas:",lineas
                    empresa = lineas.partner_id.name
                    print"empresa:",empresa
                    ruc_empresa = lineas.partner_id.part_number
                    print "RUC: ", ruc_empresa

                    if id_formulario == 'normal':
                        temision = '1'
                        # FORMAR CLAVE ACCESO COMPROBANTE NORMAL
                        clav = str(lfecha[2]+lfecha[1]+lfecha[0]+cod_comp+ruc_empresa.strip()+ambiente+fent+femi+secuencia.strip()+cod_num+temision)
                        clavea = self.modulo11(clav)
                        print "CLAVE MOD 11", clavea
                        clavef = clav.strip()+clavea.strip()
                        print "CLAVE FINAL N", clavef
                        ids_accfacel = self.env['account.factura.electronica']
                        vals_r = {
                              'name' : 'Factura',
                              'clave_acceso': clavef,
                              'cod_comprobante': cod_comp,
                              'factelect_id': factura.id
                        }
                        # accfactelect_id = ids_accfacel.create(cr,uid,vals_r)
                    elif id_formulario == 'contingencia':
                        temision = '2'

                        if len(cconti) < 37:
                            raise Warning(('Atencion !'), ('Clave de contingencia debe tener 37 caracteres numericos!'))
                        else:
                            # FORMAR CLAVE ACCESO COMPROBANTE CONTINGENCIA
                            clav = str(lfecha[2]+lfecha[1]+lfecha[0]+cod_comp+cconti.strip()+temision)
                            clavea = self.modulo11(clav)
                            print "CLAVE MOD 11", clavea
                            clavef = clav.strip()+clavea.strip()
                            print "CLAVE FINAL C", clavef
                            ids_accfacel = self.env['account.factura.electronica']
                            vals_r = {
                                  'name' : 'Factura',
                                  'clave_contingencia': cconti,
                                  'contingencia': True,
                                  'cod_comprobante': cod_comp,
                                  'factelect_id': factura.id
                            }
                    #                     accfactelect_id = ids_accfacel.create(cr,uid,vals_r)

                    # TAG CONTENEDOR COMPROBANTE
                    mainform = doc.createElement('factura')
                    doc.appendChild(mainform)
                    mainform.setAttribute('id', 'comprobante')
                    mainform.setAttribute('version', version)
                    # TAGS HIJOS DEL CONTENEDOR COMPROBANTE
                    infoTributaria = doc.createElement("infoTributaria")
                    mainform.appendChild(infoTributaria)

                    infoFactura = doc.createElement("infoFactura")
                    mainform.appendChild(infoFactura)

                    detalles = doc.createElement("detalles")
                    mainform.appendChild(detalles)

                    infoAdicional = doc.createElement("infoAdicional")
                    mainform.appendChild(infoAdicional)
                    # TAGS HIJOS DEL TAG INFOTRIBUTARIA
                    ambiente_id = doc.createElement("ambiente")
                    infoTributaria.appendChild(ambiente_id)
                    nambiente_id = doc.createTextNode(ambiente.strip())
                    ambiente_id.appendChild(nambiente_id)

                    tipoemi_id = doc.createElement("tipoEmision")
                    infoTributaria.appendChild(tipoemi_id)
                    ntipoemi_id = doc.createTextNode(temision.strip())
                    tipoemi_id.appendChild(ntipoemi_id)

                    social = doc.createElement("razonSocial")
                    infoTributaria.appendChild(social)
                    psocial = doc.createTextNode(empresa.rstrip())
                    social.appendChild(psocial)

                    comercial = doc.createElement("nombreComercial")
                    infoTributaria.appendChild(comercial)
                    pcomercial = doc.createTextNode(empresa.rstrip())
                    comercial.appendChild(pcomercial)

                    ruc = doc.createElement("ruc")
                    infoTributaria.appendChild(ruc)
                    pruc = doc.createTextNode(ruc_empresa.rstrip())
                    ruc.appendChild(pruc)

                    clave = doc.createElement("claveAcceso")
                    infoTributaria.appendChild(clave)
                    nclave_id = doc.createTextNode(clavef.strip())
                    clave.appendChild(nclave_id)

                    codoc = doc.createElement("codDoc")
                    infoTributaria.appendChild(codoc)
                    ncodoc_id = doc.createTextNode(cod_comp.strip())
                    codoc.appendChild(ncodoc_id)

                    estab = doc.createElement("estab")
                    infoTributaria.appendChild(estab)
                    nestab_id = doc.createTextNode(fent.strip())
                    estab.appendChild(nestab_id)

                    ptoemi = doc.createElement("ptoEmi")
                    infoTributaria.appendChild(ptoemi)
                    nptoemi_id = doc.createTextNode(femi.strip())
                    ptoemi.appendChild(nptoemi_id)

                    secuencial = doc.createElement("secuencial")
                    infoTributaria.appendChild(secuencial)
                    nsecuencial_id = doc.createTextNode(secuencia.strip())
                    secuencial.appendChild(nsecuencial_id)

                    dirmatr = doc.createElement("dirMatriz")
                    infoTributaria.appendChild(dirmatr)
                    ndirmatr_id = doc.createTextNode(direccion.strip())
                    dirmatr.appendChild(ndirmatr_id)
                    # TAGS HIJOS DEL TAG INFOFACTURA
                    femision = doc.createElement("fechaEmision")
                    infoFactura.appendChild(femision)
                    nfemision_id = doc.createTextNode(fecha.strip())
                    femision.appendChild(nfemision_id)

                    destable = doc.createElement("dirEstablecimiento")
                    infoFactura.appendChild(destable)
                    ndestable_id = doc.createTextNode(dsucuf.strip())
                    destable.appendChild(ndestable_id)

                    contesp = doc.createElement("contribuyenteEspecial")
                    infoFactura.appendChild(contesp)
                    ncontesp_id = doc.createTextNode(cod_posfis.strip())
                    contesp.appendChild(ncontesp_id)

                    oblicont = doc.createElement("obligadoContabilidad")
                    infoFactura.appendChild(oblicont)
                    noblicont_id = doc.createTextNode(obli_contab.strip())
                    oblicont.appendChild(noblicont_id)

                    tidencomp = doc.createElement("tipoIdentificacionComprador")
                    infoFactura.appendChild(tidencomp)
                    ntidencomp_id = doc.createTextNode(cod_ident.strip())
                    tidencomp.appendChild(ntidencomp_id)

                    rasocomp = doc.createElement("razonSocialComprador")
                    infoFactura.appendChild(rasocomp)
                    nrasocomp_id = doc.createTextNode(name_rzc.strip())
                    rasocomp.appendChild(nrasocomp_id)

                    identcomp = doc.createElement("identificacionComprador")
                    infoFactura.appendChild(identcomp)
                    nidentcomp_id = doc.createTextNode(id_rzc.strip())
                    identcomp.appendChild(nidentcomp_id)

                    dircomp = doc.createElement("direccionComprador")
                    infoFactura.appendChild(dircomp)
                    dircomp_id = doc.createTextNode(dfactuf.strip())
                    dircomp.appendChild(dircomp_id)

                    tosinimp = doc.createElement("totalSinImpuestos")
                    infoFactura.appendChild(tosinimp)
                    t_simp = Decimal(tot_simp).quantize(Decimal('0.00'))
                    ntosinimp_id = doc.createTextNode(str(t_simp))
                    tosinimp.appendChild(ntosinimp_id)

                    todesc = doc.createElement("totalDescuento")
                    infoFactura.appendChild(todesc)
                    t_desc = Decimal(tot_desc).quantize(Decimal('0.00'))
                    ntodesc_id = doc.createTextNode(str(t_desc))
                    todesc.appendChild(ntodesc_id)

                    totalci = doc.createElement("totalConImpuestos")
                    infoFactura.appendChild(totalci)
                    prop = 0
                    for impuesto in tax_id:
                        # print "OJO", impuesto.name
                        if impuesto.name == '10% servicio ' or impuesto.name == '10% servicio':
                            prop += impuesto.amount
                            continue
                        if impuesto.tax_code_id.cod_imp_fe:
                            cod_imfact = impuesto.tax_code_id.cod_imp_fe
                            print "IMPUESTO", cod_imfact
                        else:
                            raise Warning(('Atencion !'), ('No hay configurado codigo en codigo impuestos!'))
                        if impuesto.tax_code_id.cod_tarifa:
                            cod_inftar = impuesto.tax_code_id.cod_tarifa
                        else:
                            raise Warning(('Atencion !'), ('No hay configurado codigo % en codigo impuestos!'))
                        totalimp = doc.createElement("totalImpuesto")
                        totalci.appendChild(totalimp)
                        # TAG SE REPITE CODIGO IMPUESTOS SEGUN LA FACTURA
                        fcodigo = doc.createElement("codigo")
                        totalimp.appendChild(fcodigo)
                        nfcodigo_id = doc.createTextNode(cod_imfact)
                        fcodigo.appendChild(nfcodigo_id)

                        codpor = doc.createElement("codigoPorcentaje")
                        totalimp.appendChild(codpor)
                        ncodpor_id = doc.createTextNode(cod_inftar)
                        codpor.appendChild(ncodpor_id)

                        #                desadic = doc.createElement("descuentoAdicional")
                        #                totalimp.appendChild(desadic)
                        #                t_desca = Decimal(tot_desc).quantize(Decimal('0.00'))
                        #                ndesadic_id = doc.createTextNode(str(t_desca))
                        #                desadic.appendChild(ndesadic_id)

                        basimp = doc.createElement("baseImponible")
                        totalimp.appendChild(basimp)
                        vbaseimp = Decimal(impuesto.base_amount).quantize(Decimal('0.00'))
                        nbasimp_id = doc.createTextNode(str(vbaseimp))
                        basimp.appendChild(nbasimp_id)

                        fvalor = doc.createElement("valor")
                        totalimp.appendChild(fvalor)
                        vamount = Decimal(impuesto.amount).quantize(Decimal('0.00'))
                        nfvalor_id = doc.createTextNode(str(vamount))
                        fvalor.appendChild(nfvalor_id)

                    # print "OJO", impuesto.name
                    print "prop", prop

                    fpropina = doc.createElement("propina")
                    infoFactura.appendChild(fpropina)
                    imptotal = Decimal(prop).quantize(Decimal('0.00'))
                    nfpropina_id = doc.createTextNode(str(prop))
                    fpropina.appendChild(nfpropina_id)

                    fimptotal = doc.createElement("importeTotal")
                    infoFactura.appendChild(fimptotal)
                    imptotal = Decimal(factura.amount_total).quantize(Decimal('0.00'))
                    nfimptotal_id = doc.createTextNode(str(imptotal))
                    fimptotal.appendChild(nfimptotal_id)

                    fmoneda = doc.createElement("moneda")
                    infoFactura.appendChild(fmoneda)
                    nfmoneda_id = doc.createTextNode('DOLAR')
                    fmoneda.appendChild(nfmoneda_id)

                    pagos = doc.createElement("pagos")
                    infoFactura.appendChild(pagos)

                    pago = doc.createElement("pago")
                    pagos.appendChild(pago)

                    formaPago = doc.createElement("formaPago")
                    pago.appendChild(formaPago)
                    nformaPago = doc.createTextNode(factura.partner_id.f_pago)
                    formaPago.appendChild(nformaPago)

                    total = doc.createElement("total")
                    pago.appendChild(total)
                    pagtotal = Decimal(factura.amount_total).quantize(Decimal('0.00'))
                    ntotal = doc.createTextNode(str(pagtotal))
                    total.appendChild(ntotal)

                    plazo = doc.createElement("plazo")
                    pago.appendChild(plazo)
                    pagplazo = Decimal(factura.partner_id.plazo).quantize(Decimal('0.00'))
                    nplazo = doc.createTextNode(str(pagplazo))
                    plazo.appendChild(nplazo)

                    unidadTiempo = doc.createElement("unidadTiempo")
                    pago.appendChild(unidadTiempo)
                    nunidadTiempo = doc.createTextNode(factura.partner_id.unid_t)
                    unidadTiempo.appendChild(nunidadTiempo)

                    valorRetIva = doc.createElement("valorRetIva")
                    infoFactura.appendChild(valorRetIva)
                    print "IVA******", factura.amount_iva
                    print "IVA 1******", factura.amount_tax
                    pagretiva = Decimal(abs(factura.amount_iva)).quantize(Decimal('0.00'))
                    print "pagretiva", pagretiva
                    nvalorRetIva = doc.createTextNode(str(pagretiva))
                    valorRetIva.appendChild(nvalorRetIva)

                    valorRetRenta = doc.createElement("valorRetRenta")
                    infoFactura.appendChild(valorRetRenta)
                    pagretrenta = Decimal(abs(factura.amount_other)).quantize(Decimal('0.00'))
                    nvalorRetRenta = doc.createTextNode(str(pagretrenta))
                    valorRetRenta.appendChild(nvalorRetRenta)
                    # OBTENER IMPUESTOS DETALLADOS POR PRODUCTO
                    for det_impf in invdet_id:
                        id_line=det_impf.id
                        print "ID LINE", id_line
                        if det_impf.discount > 0:
                            descuent = round(((det_impf.price_unit*det_impf.quantity)*det_impf.discount)/100, 2)
                        else:
                            descuent = det_impf.discount
                        detalle = doc.createElement("detalle")
                        detalles.appendChild(detalle)

                        codprin = doc.createElement("codigoPrincipal")
                        detalle.appendChild(codprin)
                        ncodprin_id = doc.createTextNode(str(det_impf.product_id.default_code or '').strip())
                        codprin.appendChild(ncodprin_id)

                        codaux = doc.createElement("codigoAuxiliar")
                        detalle.appendChild(codaux)
                        ncodaux_id = doc.createTextNode(str(det_impf.product_id.default_code or '').strip())
                        codaux.appendChild(ncodaux_id)

                        ddescrip = doc.createElement("descripcion")
                        detalle.appendChild(ddescrip)
                        nam_lin = self.delete_ascii(det_impf.name[:200])
                        nddescrip_id = doc.createTextNode(str(nam_lin or '').strip())
                        ddescrip.appendChild(nddescrip_id)

                        dcanti = doc.createElement("cantidad")
                        detalle.appendChild(dcanti)
                        fquty = Decimal(det_impf.quantity).quantize(Decimal('0.000000'))
                        ndcanti_id = doc.createTextNode(str(fquty))
                        dcanti.appendChild(ndcanti_id)

                        dpreunit = doc.createElement("precioUnitario")
                        detalle.appendChild(dpreunit)
                        pruni = Decimal(det_impf.price_unit).quantize(Decimal('0.000000'))
                        ndpreunit_id = doc.createTextNode(str(pruni))
                        dpreunit.appendChild(ndpreunit_id)

                        ddescuent = doc.createElement("descuento")
                        detalle.appendChild(ddescuent)
                        des_lin = Decimal(descuent).quantize(Decimal('0.00'))
                        nddescuent_id = doc.createTextNode(str(des_lin))
                        ddescuent.appendChild(nddescuent_id)

                        dprectotsi = doc.createElement("precioTotalSinImpuesto")
                        detalle.appendChild(dprectotsi)
                        ptsi = Decimal(det_impf.price_subtotal).quantize(Decimal('0.00'))
                        ndprectotsi_id = doc.createTextNode(str(ptsi))
                        dprectotsi.appendChild(ndprectotsi_id)
                        sql1 = "select tax_id from account_invoice_line_tax where invoice_line_id = %s"%(id_line)
                        self._cr.execute(sql1)
                        invdetax_det = self._cr.dictfetchall()
                        #print "invdetax_det***", invdetax_det
                        lista_imp = []
                        for idft in invdetax_det:
                            lista_imp.append(idft.get('tax_id'))
                        #print "lista",  lista_imp

                        for detimpp in lista_imp:
                            taxpr_id=detimpp
                            print "taxpr_id", taxpr_id
                            acctax_id = self.env['account.tax'].search([('id', '=', taxpr_id)])
                            print "LISTA CODIGO DE LOS IMPUESTOS X PRODUCTO", acctax_id
                            #acctax_det = self.env['account.tax'].browse(acctax_id)
                            for codxp in acctax_id:
                                tax_cod_id = codxp.tax_code_id
                                print "tax_cod_id", tax_cod_id.id
                                tax_idxp = self.env['account.invoice.tax'].search([('tax_code_id', '=', tax_cod_id.id), ('invoice_id', '=', factura.id), ('deduction_id', '=', False)])
                                print "LISTA IMPUESTOS producto", tax_idxp
                                #ixp = self.env['account.invoice.tax'].browse(tax_idxp)
                                #print "BROWSE", ixp
                                for tax_detxp in tax_idxp:
                                    #CSV:AUMENTO CONTROL DE PROPINA PARA RESTAURANTE
                                    if tax_detxp.name == '10% servicio ' or tax_detxp.name == '10% servicio':
                                        continue
                            # TAGS HIJOS DEL TAG
                                    dimpuestos = doc.createElement("impuestos")
                                    detalle.appendChild(dimpuestos)

                                    dimpuest = doc.createElement("impuesto")
                                    dimpuestos.appendChild(dimpuest)

                                    dcodigo = doc.createElement("codigo")
                                    dimpuest.appendChild(dcodigo)
                                    ndcodigo_id = doc.createTextNode(tax_detxp.tax_code_id.cod_imp_fe)
                                    dcodigo.appendChild(ndcodigo_id)

                                    dcodigopor = doc.createElement("codigoPorcentaje")
                                    dimpuest.appendChild(dcodigopor)
                                    ndcodigopor_id = doc.createTextNode(tax_detxp.tax_code_id.cod_tarifa)
                                    dcodigopor.appendChild(ndcodigopor_id)

                                    dtarifa = doc.createElement("tarifa")
                                    dimpuest.appendChild(dtarifa)
                                    v_tar_imp = Decimal(tax_detxp.tax_code_id.tarifa).quantize(Decimal('0.00'))
                                    ndtarifa_id = doc.createTextNode(str(v_tar_imp))
                                    dtarifa.appendChild(ndtarifa_id)

                                    dbimponi = doc.createElement("baseImponible")
                                    dimpuest.appendChild(dbimponi)
                                    vbaseimpxp = Decimal(det_impf.price_subtotal).quantize(Decimal('0.00'))
                                    ndbimponi_id = doc.createTextNode(str(vbaseimpxp))
                                    dbimponi.appendChild(ndbimponi_id)

                                    dvalor = doc.createElement("valor")
                                    dimpuest.appendChild(dvalor)
                                    vamountxp = Decimal(round(det_impf.price_subtotal*tax_detxp.tax_code_id.tarifa/100, 2)).quantize(Decimal('0.00'))
                                    ndvalor_id = doc.createTextNode(str(vamountxp))
                                    dvalor.appendChild(ndvalor_id)

                    cadicional = doc.createElement('campoAdicional')
                    infoAdicional.appendChild(cadicional)
                    cadicional.setAttribute('nombre', 'mail')
                    cadicional_id = doc.createTextNode(cliemail)
                    cadicional.appendChild(cadicional_id)

                    cadicional1 = doc.createElement('campoAdicional')
                    infoAdicional.appendChild(cadicional1)
                    cadicional1.setAttribute('nombre', 'Direccion')
                    cadicional_id1 = doc.createTextNode(dfactuf)
                    cadicional1.appendChild(cadicional_id1)

                    #print "DOC**", doc
                    try:
                        out = base64.encodestring(doc.toxml())
                    except UnicodeEncodeError:
                        continue
                    except UnicodeDecodeError:
                        continue
                    name = "%s.xml" % (clavef)
                    if record:
                        record.name = name
                    #print "NOMBRE COMPROBANTE GUARDAR", name
                    if record:
                        record.data = out
                    f = open('/home/oddo/'+firmadig+'/'+'FACTURA_ELECTRONICA/FACTURASF/'+name, 'w')
                    f.write(doc.toxml())
                    f.close()
                    if firmadig == 'MISSION PETROLEUM S.A.':
                        print "ENTRO MISSION PETROLEUM S.A."
                        res = jarWrapper('/opt/addons_mission/o2s_felectronica/wizard/XadesBes.jar',
                                         '/opt/addons_mission/o2s_felectronica/wizard/'+firmadig+'/'+'firmaMissionPetroleum2018.p12',
                                         'mission2020','/home/oddo/'+firmadig+'/'+'FACTURA_ELECTRONICA/FACTURASF/'+name,
                                         '/home/oddo/'+firmadig+'/'+'FACTURA_ELECTRONICA/FACTURAF',name)
                        print "RES", res
                        w = open('/home/oddo/'+firmadig+'/'+'FACTURA_ELECTRONICA/FACTURAF/'+name, 'rb')
                        q=w.read()
                    res_sri =  client.service.validarComprobante(base64.encodestring(q))
                    #print "RESPUESTA*****", res_sri
                            # print "ESTADO*****", res_sri[0]
                    #CSV: AUMENTO PARA EL CASO DE SOLO CONSULTAR
                    if factura.state_factelectro == 'firmado':
                        clavef = factura.num_autoelectronica
                        autorizada = 0
                        while autorizada != 1:
                            res_autcomp =  client1.service.autorizacionComprobante(clavef)
                            print "OBJETO AUTORIZA1***", res_autcomp
                            #                     print "TIPO RESPUESTA", type(res_autcomp)
                            #                     print "TAMAÑO RESPUESTA", len(res_autcomp)
                            #                     print "OBJETO autorizaciones***", res_autcomp.autorizaciones
                            #                     print "TIPO autorizaciones", type(res_autcomp.autorizaciones)
                            #                     print "TAMAÑO autorizaciones", len(res_autcomp.autorizaciones)
                            if len(res_autcomp.autorizaciones) > 0:
                                if len(res_autcomp.autorizaciones.autorizacion[0]) > 0:
                                    estado_ws = res_autcomp.autorizaciones.autorizacion[0]['estado']
                                    print "estado_ws", estado_ws
                                    autorizada = 1
                                    if str(estado_ws).strip() == 'AUTORIZADO':
                                        #******************************XML ENVIO POR MAIL CLIENTE*************************
                                        numaut_ws = res_autcomp.autorizaciones.autorizacion[0]['numeroAutorizacion']
                                        print "numaut_ws", numaut_ws
                                        fechaut_ws = res_autcomp.autorizaciones.autorizacion[0]['fechaAutorizacion']
                                        print "fechaut_ws", fechaut_ws
                                        if ambiente == '2':
                                            ambiente_ws = 'PRODUCCION'
                                        elif ambiente == '1':
                                            ambiente_ws = 'PRUEBAS'
                                        print "ambiente_ws", ambiente_ws
                                        comprobante_ws = res_autcomp.autorizaciones.autorizacion[0]['comprobante']
                                        #print "comprobante", comprobante

                                        # TAGS XML ENVIO POR MAIL AL CLIENTE
                                        autorizacion = doc1.createElement('autorizacion')
                                        doc1.appendChild(autorizacion)
                                        # TAGS HIJOS DEL TAG AUTORIZACION
                                        estado = doc1.createElement("estado")
                                        autorizacion.appendChild(estado)
                                        naestado_id = doc.createTextNode(str(estado_ws).strip())
                                        estado.appendChild(naestado_id)

                                        numaut = doc1.createElement("numeroAutorizacion")
                                        autorizacion.appendChild(numaut)
                                        nanumaut_id = doc.createTextNode(str(numaut_ws).strip())
                                        numaut.appendChild(nanumaut_id)

                                        fechaut = doc1.createElement("fechaAutorizacion")
                                        autorizacion.appendChild(fechaut)
                                        nafechaut_id = doc.createTextNode(str(fechaut_ws).strip())
                                        fechaut.appendChild(nafechaut_id)

                                        ambienteaut = doc1.createElement("ambiente")
                                        autorizacion.appendChild(ambienteaut)
                                        naambienteaut_id = doc.createTextNode(str(ambiente_ws).strip())
                                        ambienteaut.appendChild(naambienteaut_id)

                                        comprobanteaut = doc1.createElement("comprobante")
                                        autorizacion.appendChild(comprobanteaut)
                                        nacomprobanteaut_id = doc.createTextNode(str(comprobante_ws).strip())
                                        comprobanteaut.appendChild(nacomprobanteaut_id)

                                        out1 = base64.encodestring(doc1.toxml())
                                        data_fname = "%s.xml" % (clavef)
                                        f1 = open('/home/oddo/'+firmadig+'/'+'FACTURA_ELECTRONICA/AUTORIZADO/'+data_fname, 'w')
                                        f1.write(doc1.toxml())
                                        f1.close()
                                        #CSV 07-06-2017 PARA ADJUNTARLO************************
                                        archivo = '/home/oddo/'+firmadig+'/'+'FACTURA_ELECTRONICA/AUTORIZADO/'+data_fname
                                        res_model = 'account.invoice'
                                        id = ids and type(ids) == type([]) and ids[0] or ids
                                        self.load_doc(out1, factura.id, data_fname, archivo, res_model)
                                        #**************************************************************************************
                                        num_aut = res_autcomp.autorizaciones.autorizacion[0]['numeroAutorizacion']
                                        #ids_atracci = self.env['account.invoice']
                                        vals_accinv = {'num_autoelectronica' : num_aut,
                                                  'state_factelectro': 'autorizado',
                                                  'date_aut': time.strftime('%Y-%m-%d %H:%M:%S'),
                                                  'inf_electronica' : 'autorizado'}
                                        factura.write(vals_accinv)
                                        #accfactelect_id = ids_accfacel.create(vals_r)
                                        mensaje = str(estado_ws)
                                        if record:
                                            record.mensaje = mensaje
                                        #return True
                                    else:
                                        if res_autcomp.autorizaciones.autorizacion[-1]['estado'] == 'AUTORIZADO':
                                            num_aut = res_autcomp.autorizaciones.autorizacion[-1]['numeroAutorizacion']
                                            #ids_atracci = self.env['account.invoice']
                                            vals_accinv = {'num_autoelectronica' : num_aut,
                                                      'state_factelectro': 'autorizado',
                                                      'date_aut': time.strftime('%Y-%m-%d %H:%M:%S'),
                                                      'inf_electronica' : 'autorizado'}
                                            factura.write(vals_accinv)
                                            #accfactelect_id = ids_accfacel.create(vals_r)
                                            mensaje = str(res_autcomp.autorizaciones.autorizacion[-1]['estado'])
                                            if record:
                                                record.mensaje = mensaje
                                            #return True
                                        else:
                                            mensaje = str(res_autcomp)
                                            if record:
                                                record.mensaje = mensaje
                                            vals_inf_elect = {'inf_electronica' : mensaje,
                                                              'state_factelectro': 'error'}
                                            factura.write(vals_inf_elect)
                                            #return True
                                #print "MENSAJE", mensaje
                    if res_sri and res_sri['estado']=='RECIBIDA':
                        #CSV:29-12-2017: AUMENTO PARA ENVIAR ARCHIVO FIRMADO CLIENTE Y SRI PRIMER WEB SERVICES
                        #CSV: PARA ADJUNTARLO************************
                        w = open('/home/oddo/'+firmadig+'/'+'FACTURA_ELECTRONICA/FACTURAF/'+name, 'rb')
                        q=w.read()
                        out2 = base64.encodestring(q)
                        data_fname = name
                        archivo = '/home/oddo/'+firmadig+'/'+'FACTURA_ELECTRONICA/FACTURAF/'+name
                        res_model = 'account.invoice'
                        id = ids and type(ids) == type([]) and ids[0] or ids
                        self.load_doc(out2, factura.id, data_fname, archivo, res_model)
                        #Escribo en la factura*
                        num_autws1 = clavef
                        #ids_atracci = self.env['account.invoice']
                        vals_accinvws1 = {'num_autoelectronica' : num_autws1,
                                  'state_factelectro': 'firmado',
                                  'date_aut': time.strftime('%Y-%m-%d %H:%M:%S'),
                                  'inf_electronica' : 'firmado'}
                        factura.write(vals_accinvws1)
                        accfactelect_id = ids_accfacel.create(vals_r)
                        mensaje = str('firmado')
                        if record:
                            record.mensaje = mensaje

                    elif res_sri and res_sri['estado']=='DEVUELTA':
                        mensaje = str(res_sri)
                        if record:
                            record.mensaje = mensaje
                        vals_inf_elect = {'inf_electronica' : mensaje,
                                          'state_factelectro': 'error'}
                        factura.write(vals_inf_elect)
                        print "NO SE ENVIO"
                    #return True
                # if (t_comp == 'out_invoice'):
                    #     return {
                    #     'name': name,
                    #     'view_type': 'form',
                    #     'view_mode': 'form',
                    #     'res_model': 'wizard.factura.electronica',
                    #     'res_id': id_m,
                    #     'view_id': False,
                    #     'type': 'ir.actions.act_window',
                    #     'domain': [],
                    #     'target': 'new',
                    #     'context': self._context,
                    # }
                #***********************CONDICION NOTA CREDITO **************************************************************
                elif t_comp == 'out_refund':
                    cod_comp = '04'
                    amount_service = 0.00
                    #CSV:29-12-2017:INICIALIZO LOS WS SRI

                    if id_ambiente == 'pruebas':
	                if (not os.environ.get('PYTHONHTTPSVERIFY', '') and 
                        getattr(ssl, '_create_unverified_context', None)):
                	    ssl._create_default_https_context = ssl._create_unverified_context
                        ambiente = '1'
                        #CSV:28-12-2017: WS ON-LINE PRUEBAS
                        #url = 'https://celcer.sri.gob.ec/comprobantes-electronicos-ws/RecepcionComprobantes?wsdl'
                        #url1 = 'https://celcer.sri.gob.ec/comprobantes-electronicos-ws/AutorizacionComprobantes?wsdl'
                        url = 'https://celcer.sri.gob.ec/comprobantes-electronicos-ws/RecepcionComprobantesOffline?wsdl'
                        url1 = 'https://celcer.sri.gob.ec/comprobantes-electronicos-ws/AutorizacionComprobantesOffline?wsdl'
                        client = Client(url)
                        client1 = Client(url1)
                        if client and client1:
                            print "OK SRI"
                        else:
                            raise Warning(('Atencion !'), ('No responde SRI intente mas tarde!'))
                    elif id_ambiente == 'produccion':
                        if (not os.environ.get('PYTHONHTTPSVERIFY', '') and 
                        getattr(ssl, '_create_unverified_context', None)):
                            ssl._create_default_https_context = ssl._create_unverified_context
                        ambiente = '2'
                        #CSV:28-12-2017: WS ON-LINE PRODUCCION
                        #url = 'https://cel.sri.gob.ec/comprobantes-electronicos-ws/RecepcionComprobantes?wsdl'
                        #url1 = 'https://cel.sri.gob.ec/comprobantes-electronicos-ws/AutorizacionComprobantes?wsdl'
                        url = 'https://cel.sri.gob.ec/comprobantes-electronicos-ws/RecepcionComprobantesOffline?wsdl'
                        url1 = 'https://cel.sri.gob.ec/comprobantes-electronicos-ws/AutorizacionComprobantesOffline?wsdl'
                        client = Client(url)
                        client1 = Client(url1)
                        if client and client1:
                            print "OK SRI"
                        else:
                            raise Warning(('Atencion !'), ('No responde SRI intente mas tarde!'))
                    if factura.state_factelectro not in ('autorizado', 'firmado'):
                        #version = record.version
                        print"version: ",version
                        #compania = record.company
                        print "compania: ",compania.id
                        # Obtener Informacion de la compania
                        lineas = self.env['res.company'].browse([compania.id])[0]
                        print"lineas:",lineas
                        empresa = lineas.partner_id.name
                        print"empresa:",empresa
                        ruc_empresa = lineas.partner_id.part_number
                        print "RUC: ", ruc_empresa
                        #id_formulario = record.formulario
                        if id_formulario == 'normal':
                            temision = '1'
                            # FORMAR CLAVE ACCESO COMPROBANTE NORMAL
                            clav = str(lfecha[2]+lfecha[1]+lfecha[0]+cod_comp+ruc_empresa.strip()+ambiente+fent+femi+secuencia.strip()+cod_num+temision)
                            clavea = self.modulo11(clav)
                            print "CLAVE MOD 11", clavea
                            clavef = clav.strip()+clavea.strip()
                            print "CLAVE FINAL N", clavef
                            ids_accfacel = self.env['account.factura.electronica']
                            vals_r = {
                                  'name' : 'Nota Credito',
                                  'clave_acceso': clavef,
                                  'cod_comprobante': cod_comp,
                                  'factelect_id': factura.id
                            }
                        # accfactelect_id = ids_accfacel.create(cr,uid,vals_r)
                        elif id_formulario == 'contingencia':
                            temision = '2'
                            #cconti = record.contingencia
                            if len(cconti) < 37:
                                raise Warning(('Atencion !'), ('Clave de contingencia debe tener 37 caracteres numericos!'))
                            else:
                                # FORMAR CLAVE ACCESO COMPROBANTE CONTINGENCIA
                                clav = str(lfecha[2]+lfecha[1]+lfecha[0]+cod_comp+cconti.strip()+temision)
                                clavea = self.modulo11(clav)
                                print "CLAVE MOD 11", clavea
                                clavef = clav.strip()+clavea.strip()
                                print "CLAVE FINAL C", clavef
                                ids_accfacel = self.env['account.factura.electronica']
                                vals_r = {
                                      'name' : 'Nota Credito',
                                      'clave_contingencia': cconti,
                                      'contingencia': True,
                                      'cod_comprobante': cod_comp,
                                      'factelect_id': factura.id
                                }
                        # accfactelect_id = ids_accfacel.create(cr,uid,vals_r)

                        # TAG CONTENEDOR COMPROBANTE
                        mainform = doc.createElement('notaCredito')
                        doc.appendChild(mainform)
                        mainform.setAttribute('id', 'comprobante')
                        mainform.setAttribute('version', version)
                        # TAGS HIJOS DEL CONTENEDOR COMPROBANTE
                        infoTributaria = doc.createElement("infoTributaria")
                        mainform.appendChild(infoTributaria)

                        infoFactura = doc.createElement("infoNotaCredito")
                        mainform.appendChild(infoFactura)

                        detalles = doc.createElement("detalles")
                        mainform.appendChild(detalles)

                        infoAdicional = doc.createElement("infoAdicional")
                        mainform.appendChild(infoAdicional)
                        # TAGS HIJOS DEL TAG INFOTRIBUTARIA
                        ambiente_id = doc.createElement("ambiente")
                        infoTributaria.appendChild(ambiente_id)
                        nambiente_id = doc.createTextNode(ambiente.strip())
                        ambiente_id.appendChild(nambiente_id)

                        tipoemi_id = doc.createElement("tipoEmision")
                        infoTributaria.appendChild(tipoemi_id)
                        ntipoemi_id = doc.createTextNode(temision.strip())
                        tipoemi_id.appendChild(ntipoemi_id)

                        social = doc.createElement("razonSocial")
                        infoTributaria.appendChild(social)
                        psocial = doc.createTextNode(empresa.rstrip())
                        social.appendChild(psocial)

                        comercial = doc.createElement("nombreComercial")
                        infoTributaria.appendChild(comercial)
                        pcomercial = doc.createTextNode(empresa.rstrip())
                        comercial.appendChild(pcomercial)

                        ruc = doc.createElement("ruc")
                        infoTributaria.appendChild(ruc)
                        pruc = doc.createTextNode(ruc_empresa.rstrip())
                        ruc.appendChild(pruc)

                        clave = doc.createElement("claveAcceso")
                        infoTributaria.appendChild(clave)
                        nclave_id = doc.createTextNode(clavef.strip())
                        clave.appendChild(nclave_id)

                        codoc = doc.createElement("codDoc")
                        infoTributaria.appendChild(codoc)
                        ncodoc_id = doc.createTextNode(cod_comp.strip())
                        codoc.appendChild(ncodoc_id)

                        estab = doc.createElement("estab")
                        infoTributaria.appendChild(estab)
                        nestab_id = doc.createTextNode(fent.strip())
                        estab.appendChild(nestab_id)

                        ptoemi = doc.createElement("ptoEmi")
                        infoTributaria.appendChild(ptoemi)
                        nptoemi_id = doc.createTextNode(femi.strip())
                        ptoemi.appendChild(nptoemi_id)

                        secuencial = doc.createElement("secuencial")
                        infoTributaria.appendChild(secuencial)
                        nsecuencial_id = doc.createTextNode(secuencia.strip())
                        secuencial.appendChild(nsecuencial_id)

                        dirmatr = doc.createElement("dirMatriz")
                        infoTributaria.appendChild(dirmatr)
                        ndirmatr_id = doc.createTextNode(direccion.strip())
                        dirmatr.appendChild(ndirmatr_id)
                        # TAGS HIJOS DEL TAG INFOFACTURA
                        femision = doc.createElement("fechaEmision")
                        infoFactura.appendChild(femision)
                        nfemision_id = doc.createTextNode(fecha.strip())
                        femision.appendChild(nfemision_id)

                        destable = doc.createElement("dirEstablecimiento")
                        infoFactura.appendChild(destable)
                        ndestable_id = doc.createTextNode(dsucuf.strip())
                        destable.appendChild(ndestable_id)

                        tidencomp = doc.createElement("tipoIdentificacionComprador")
                        infoFactura.appendChild(tidencomp)
                        ntidencomp_id = doc.createTextNode(cod_ident.strip())
                        tidencomp.appendChild(ntidencomp_id)

                        rasocomp = doc.createElement("razonSocialComprador")
                        infoFactura.appendChild(rasocomp)
                        nrasocomp_id = doc.createTextNode(name_rzc.strip())
                        rasocomp.appendChild(nrasocomp_id)

                        identcomp = doc.createElement("identificacionComprador")
                        infoFactura.appendChild(identcomp)
                        nidentcomp_id = doc.createTextNode(id_rzc.strip())
                        identcomp.appendChild(nidentcomp_id)

                        contesp = doc.createElement("contribuyenteEspecial")
                        infoFactura.appendChild(contesp)
                        ncontesp_id = doc.createTextNode(cod_posfis.strip())
                        contesp.appendChild(ncontesp_id)

                        oblicont = doc.createElement("obligadoContabilidad")
                        infoFactura.appendChild(oblicont)
                        noblicont_id = doc.createTextNode(obli_contab.strip())
                        oblicont.appendChild(noblicont_id)

                        rise = doc.createElement("rise")
                        infoFactura.appendChild(rise)
                        nrise_id = doc.createTextNode('NO')
                        rise.appendChild(nrise_id)

                        cdm = doc.createElement("codDocModificado")
                        infoFactura.appendChild(cdm)
                        ncdm_id = doc.createTextNode('01')
                        cdm.appendChild(ncdm_id)

                        ndm = doc.createElement("numDocModificado")
                        infoFactura.appendChild(ndm)
                        nndm_id = doc.createTextNode(str(ent_dm+'-'+emi_dm+'-'+num_fact_ori.zfill(9)).strip())
                        ndm.appendChild(nndm_id)

                        feds = doc.createElement("fechaEmisionDocSustento")
                        infoFactura.appendChild(feds)
                        nfeds_id = doc.createTextNode(flfech_dm.strip())
                        feds.appendChild(nfeds_id)

                        tosinimp = doc.createElement("totalSinImpuestos")
                        infoFactura.appendChild(tosinimp)
                        t_simp = Decimal(tot_simp).quantize(Decimal('0.00'))
                        ntosinimp_id = doc.createTextNode(str(t_simp))
                        tosinimp.appendChild(ntosinimp_id)

                        fimptotal = doc.createElement("valorModificacion")
                        infoFactura.appendChild(fimptotal)
                        imptotal = Decimal(factura.amount_total-amount_service).quantize(Decimal('0.00'))
                        nfimptotal_id = doc.createTextNode(str(imptotal))
                        fimptotal.appendChild(nfimptotal_id)

                        fmoneda = doc.createElement("moneda")
                        infoFactura.appendChild(fmoneda)
                        nfmoneda_id = doc.createTextNode('DOLAR')
                        fmoneda.appendChild(nfmoneda_id)

                        totalci = doc.createElement("totalConImpuestos")
                        infoFactura.appendChild(totalci)
                        prop = 0
                        for impuesto in tax_id:
                            # print "IMPUESTO", impuesto.name
                            #print "IMPUESTO CODE ID", impuesto.tax_code_id
                            #print "IMPUESTO CODE", impuesto.tax_code_id.cod_imp_fe
                            if impuesto.name == '10% servicio ' or impuesto.name == '10% servicio':
                                prop += impuesto.amount
                                continue
                            if impuesto.tax_code_id.cod_imp_fe:
                                cod_imfact = impuesto.tax_code_id.cod_imp_fe
                            else:
                                raise Warning(('Atencion !'), ('No hay configurado codigo en codigo impuestos!'))
                            if impuesto.tax_code_id.cod_tarifa:
                                cod_inftar = impuesto.tax_code_id.cod_tarifa
                            else:
                                raise Warning(('Atencion !'), ('No hay configurado codigo % en codigo impuestos!'))

                            totalimp = doc.createElement("totalImpuesto")
                            totalci.appendChild(totalimp)
                            # TAG SE REPITE CODIGO IMPUESTOS SEGUN LA FACTURA
                            fcodigo = doc.createElement("codigo")
                            totalimp.appendChild(fcodigo)
                            nfcodigo_id = doc.createTextNode(cod_imfact)
                            fcodigo.appendChild(nfcodigo_id)

                            codpor = doc.createElement("codigoPorcentaje")
                            totalimp.appendChild(codpor)
                            ncodpor_id = doc.createTextNode(cod_inftar)
                            codpor.appendChild(ncodpor_id)

                            basimp = doc.createElement("baseImponible")
                            totalimp.appendChild(basimp)
                            vbaseimp = Decimal(abs(impuesto.base_amount)).quantize(Decimal('0.00'))
                            nbasimp_id = doc.createTextNode(str(vbaseimp))
                            basimp.appendChild(nbasimp_id)

                            fvalor = doc.createElement("valor")
                            totalimp.appendChild(fvalor)
                            vamount = Decimal(impuesto.amount).quantize(Decimal('0.00'))
                            nfvalor_id = doc.createTextNode(str(vamount))
                            fvalor.appendChild(nfvalor_id)

                        razon = doc.createElement("motivo")
                        infoFactura.appendChild(razon)
                        nrazon_id = doc.createTextNode(str(factura.name).strip())
                        razon.appendChild(nrazon_id)

                        # OBTENER IMPUESTOS DETALLADOS POR PRODUCTO
                        for det_impf in invdet_id:
                            id_line=det_impf.id
                            print "ID LINE", id_line
                            if det_impf.discount > 0:
                                descuent = round(((det_impf.price_unit*det_impf.quantity)*det_impf.discount)/100, 2)
                            else:
                                descuent = det_impf.discount

                            detalle = doc.createElement("detalle")
                            detalles.appendChild(detalle)

                            codprin = doc.createElement("codigoInterno")
                            detalle.appendChild(codprin)
                            ncodprin_id = doc.createTextNode(str(det_impf.product_id.default_code).strip())
                            codprin.appendChild(ncodprin_id)

                            codaux = doc.createElement("codigoAdicional")
                            detalle.appendChild(codaux)
                            ncodaux_id = doc.createTextNode(str(det_impf.product_id.default_code).strip())
                            codaux.appendChild(ncodaux_id)

                            ddescrip = doc.createElement("descripcion")
                            detalle.appendChild(ddescrip)
                            nam_lin = self.delete_ascii(det_impf.name[:200])
                            nddescrip_id = doc.createTextNode(str(nam_lin or '').strip())
                            ddescrip.appendChild(nddescrip_id)

                            dcanti = doc.createElement("cantidad")
                            detalle.appendChild(dcanti)
                            fquty = Decimal(det_impf.quantity).quantize(Decimal('0.000000'))
                            ndcanti_id = doc.createTextNode(str(fquty))
                            dcanti.appendChild(ndcanti_id)

                            dpreunit = doc.createElement("precioUnitario")
                            detalle.appendChild(dpreunit)
                            pruni = Decimal(det_impf.price_unit).quantize(Decimal('0.000000'))
                            ndpreunit_id = doc.createTextNode(str(pruni))
                            dpreunit.appendChild(ndpreunit_id)

                            ddescuent = doc.createElement("descuento")
                            detalle.appendChild(ddescuent)
                            des_lin = Decimal(descuent).quantize(Decimal('0.00'))
                            nddescuent_id = doc.createTextNode(str(des_lin))
                            ddescuent.appendChild(nddescuent_id)

                            dprectotsi = doc.createElement("precioTotalSinImpuesto")
                            detalle.appendChild(dprectotsi)
                            ptsi = Decimal(det_impf.price_subtotal).quantize(Decimal('0.00'))
                            ndprectotsi_id = doc.createTextNode(str(ptsi))
                            dprectotsi.appendChild(ndprectotsi_id)

                            detallesAdicionales = doc.createElement("detallesAdicionales")
                            detalle.appendChild(detallesAdicionales)
                            detAdicional = doc.createElement('detAdicional')
                            detallesAdicionales.appendChild(detAdicional)
                            detAdicional.setAttribute('nombre', 'descripcion')
                            detAdicional.setAttribute('valor', str(factura.comment))
                            detAdicional1 = doc.createElement('detAdicional')
                            detallesAdicionales.appendChild(detAdicional1)
                            detAdicional1.setAttribute('nombre', 'reference')
                            detAdicional1.setAttribute('valor', str(factura.reference))
                            detAdicional2 = doc.createElement('detAdicional')
                            detallesAdicionales.appendChild(detAdicional2)
                            detAdicional2.setAttribute('nombre', 'name')
                            detAdicional2.setAttribute('valor', str(factura.name))

                            sql1 = "select tax_id from account_invoice_line_tax where invoice_line_id = %s"%(id_line)
                            self._cr.execute(sql1)
                            invdetax_det = self._cr.dictfetchall()
                            print "invdetax_det***", invdetax_det
                            lista_imp = []
                            for idft in invdetax_det:
                                lista_imp.append(idft.get('tax_id'))
                            print "lista",  lista_imp

                            for detimpp in lista_imp:
                                taxpr_id=detimpp
                                print "taxpr_id", taxpr_id
                                acctax_id = self.env['account.tax'].search([('id', '=', taxpr_id)])
                                print "LISTA CODIGO DE LOS IMPUESTOS X PRODUCTO", acctax_id
                                #acctax_det = self.env['account.tax'].browse(acctax_id)
                                for codxp in acctax_id:
                                    tax_cod_id = codxp.tax_code_id
                                    print "tax_cod_id", tax_cod_id.id
                                    tax_idxp = self.env['account.invoice.tax'].search([('tax_code_id', '=', tax_cod_id.id), ('invoice_id', '=', factura.id), ('deduction_id', '=', False)])
                                    print "LISTA IMPUESTOS producto", tax_idxp
                                    #ixp = self.env['account.invoice.tax'].browse(tax_idxp)
                                    #print "BROWSE", ixp
                                    for tax_detxp in tax_idxp:
                                        #CSV:AUMENTO CONTROL DE PROPINA PARA RESTAURANTE
                                        if tax_detxp.name == '10% servicio ' or tax_detxp.name == '10% servicio':
                                            continue
                                        # TAGS HIJOS DEL TAG
                                        dimpuestos = doc.createElement("impuestos")
                                        detalle.appendChild(dimpuestos)

                                        dimpuest = doc.createElement("impuesto")
                                        dimpuestos.appendChild(dimpuest)

                                        dcodigo = doc.createElement("codigo")
                                        dimpuest.appendChild(dcodigo)
                                        ndcodigo_id = doc.createTextNode(tax_detxp.tax_code_id.cod_imp_fe)
                                        dcodigo.appendChild(ndcodigo_id)

                                        dcodigopor = doc.createElement("codigoPorcentaje")
                                        dimpuest.appendChild(dcodigopor)
                                        ndcodigopor_id = doc.createTextNode(tax_detxp.tax_code_id.cod_tarifa)
                                        dcodigopor.appendChild(ndcodigopor_id)

                                        dtarifa = doc.createElement("tarifa")
                                        dimpuest.appendChild(dtarifa)
                                        v_tar_imp = Decimal(tax_detxp.tax_code_id.tarifa).quantize(Decimal('0.00'))
                                        ndtarifa_id = doc.createTextNode(str(v_tar_imp))
                                        dtarifa.appendChild(ndtarifa_id)

                                        dbimponi = doc.createElement("baseImponible")
                                        dimpuest.appendChild(dbimponi)
                                        vbaseimpxp = Decimal(det_impf.price_subtotal).quantize(Decimal('0.00'))
                                        ndbimponi_id = doc.createTextNode(str(vbaseimpxp))
                                        dbimponi.appendChild(ndbimponi_id)

                                        dvalor = doc.createElement("valor")
                                        dimpuest.appendChild(dvalor)
                                        vamountxp = Decimal(round(det_impf.price_subtotal*tax_detxp.tax_code_id.tarifa/100, 2)).quantize(Decimal('0.00'))
                                        ndvalor_id = doc.createTextNode(str(vamountxp))
                                        dvalor.appendChild(ndvalor_id)

                        cadicional = doc.createElement('campoAdicional')
                        infoAdicional.appendChild(cadicional)
                        cadicional.setAttribute('nombre', 'mail')
                        cadicional_id = doc.createTextNode(cliemail)
                        cadicional.appendChild(cadicional_id)

                        cadicional1 = doc.createElement('campoAdicional')
                        infoAdicional.appendChild(cadicional1)
                        cadicional1.setAttribute('nombre', 'Direccion')
                        cadicional_id1 = doc.createTextNode(dfactuf)
                        cadicional1.appendChild(cadicional_id1)

                        out = base64.encodestring(doc.toxml())
                        name = "%s.xml" % (clavef)
                        if record:
                            record.name = name
                        print "NOMBRE COMPROBANTE GUARDAR", name
                        if record:
                            record.data = out
                        f = open('/home/oddo/'+firmadig+'/'+'FACTURA_ELECTRONICA/FACTURASF/'+name, 'w')
                        f.write(doc.toxml())
                        f.close()
                        # *********************************************************************************************************************************
			if firmadig == 'MISSION PETROLEUM S.A.':
                    	    print "ENTRO MISSION PETROLEUM S.A."
                    	    res = jarWrapper('/opt/addons_mission/o2s_felectronica/wizard/XadesBes.jar',
                            	             '/opt/addons_mission/o2s_felectronica/wizard/'+firmadig+'/'+'firmaMissionPetroleum2018.p12',
                                	     'mission2020','/home/oddo/'+firmadig+'/'+'FACTURA_ELECTRONICA/FACTURASF/'+name,
                                  	     '/home/oddo/'+firmadig+'/'+'FACTURA_ELECTRONICA/FACTURAF',name)
                            print "RES", res
                            w = open('/home/oddo/'+firmadig+'/'+'FACTURA_ELECTRONICA/FACTURAF/'+name, 'rb')
                            q=w.read()
                        #*********************************************************************************************************************************
                        res_sri =  client.service.validarComprobante(base64.encodestring(q))
                        # print "RESPUESTA*****", res_sri
                    # print "ESTADO*****", res_sri[0]
                    # CSV: AUMENTO PARA EL CASO DE SOLO CONSULTAR
                    if factura.state_factelectro == 'firmado':
                        clavef = factura.num_autoelectronica
                        autorizada = 0
                        while autorizada != 1:
                            res_autcomp =  client1.service.autorizacionComprobante(clavef)
                            print "OBJETO AUTORIZA1***", res_autcomp
                            #                     print "TIPO RESPUESTA", type(res_autcomp)
                            #                     print "TAMAÑO RESPUESTA", len(res_autcomp)
                            #                     print "OBJETO autorizaciones***", res_autcomp.autorizaciones
                            #                     print "TIPO autorizaciones", type(res_autcomp.autorizaciones)
                            #                     print "TAMAÑO autorizaciones", len(res_autcomp.autorizaciones)
                            if len(res_autcomp.autorizaciones) > 0:
                                if len(res_autcomp.autorizaciones.autorizacion[0]) > 0:
                                    estado_ws = res_autcomp.autorizaciones.autorizacion[0]['estado']
                                    print "estado_ws", estado_ws
                                    autorizada = 1
                                    if str(estado_ws).strip() == 'AUTORIZADO':
                                        #******************************XML ENVIO POR MAIL CLIENTE*************************
                                        numaut_ws = res_autcomp.autorizaciones.autorizacion[0]['numeroAutorizacion']
                                        print "numaut_ws", numaut_ws
                                        fechaut_ws = res_autcomp.autorizaciones.autorizacion[0]['fechaAutorizacion']
                                        print "fechaut_ws", fechaut_ws
                                        if ambiente == '2':
                                            ambiente_ws = 'PRODUCCION'
                                        elif ambiente == '1':
                                            ambiente_ws = 'PRUEBAS'
                                        print "ambiente_ws", ambiente_ws
                                        comprobante_ws = res_autcomp.autorizaciones.autorizacion[0]['comprobante']
                                        #print "comprobante", comprobante

                                        # TAGS XML ENVIO POR MAIL AL CLIENTE
                                        autorizacion = doc1.createElement('autorizacion')
                                        doc1.appendChild(autorizacion)
                                        # TAGS HIJOS DEL TAG AUTORIZACION
                                        estado = doc1.createElement("estado")
                                        autorizacion.appendChild(estado)
                                        naestado_id = doc.createTextNode(str(estado_ws).strip())
                                        estado.appendChild(naestado_id)

                                        numaut = doc1.createElement("numeroAutorizacion")
                                        autorizacion.appendChild(numaut)
                                        nanumaut_id = doc.createTextNode(str(numaut_ws).strip())
                                        numaut.appendChild(nanumaut_id)

                                        fechaut = doc1.createElement("fechaAutorizacion")
                                        autorizacion.appendChild(fechaut)
                                        nafechaut_id = doc.createTextNode(str(fechaut_ws).strip())
                                        fechaut.appendChild(nafechaut_id)

                                        ambienteaut = doc1.createElement("ambiente")
                                        autorizacion.appendChild(ambienteaut)
                                        naambienteaut_id = doc.createTextNode(str(ambiente_ws).strip())
                                        ambienteaut.appendChild(naambienteaut_id)

                                        comprobanteaut = doc1.createElement("comprobante")
                                        autorizacion.appendChild(comprobanteaut)
                                        nacomprobanteaut_id = doc.createTextNode(str(comprobante_ws).strip())
                                        comprobanteaut.appendChild(nacomprobanteaut_id)

                                        out1 = base64.encodestring(doc1.toxml())
                                        data_fname = "%s.xml" % (clavef)
                                        f1 = open('/home/oddo/'+firmadig+'/'+'FACTURA_ELECTRONICA/AUTORIZADO/'+data_fname, 'w')
                                        f1.write(doc1.toxml())
                                        f1.close()
                                        #CSV 07-06-2017 PARA ADJUNTARLO************************
                                        archivo = '/home/oddo/'+firmadig+'/'+'FACTURA_ELECTRONICA/AUTORIZADO/'+data_fname
                                        res_model = 'account.invoice'
                                        id = ids and type(ids) == type([]) and ids[0] or ids
                                        self.load_doc(out1, factura.id, data_fname, archivo, res_model)
                                        #**************************************************************************************
                                        num_aut = res_autcomp.autorizaciones.autorizacion[0]['numeroAutorizacion']
                                        #ids_atracci = self.env['account.invoice']
                                        vals_accinv = {'num_autoelectronica' : num_aut,
                                                  'state_factelectro': 'autorizado',
                                                  'date_aut': time.strftime('%Y-%m-%d %H:%M:%S'),
                                                  'inf_electronica' : 'autorizado'}
                                        factura.write(vals_accinv)
                                        #accfactelect_id = ids_accfacel.create(vals_r)
                                        mensaje = str(estado_ws)
                                        if record:
                                            record.mensaje = mensaje
                                        #return True
                                    else:
                                        if res_autcomp.autorizaciones.autorizacion[-1]['estado'] == 'AUTORIZADO':
                                            num_aut = res_autcomp.autorizaciones.autorizacion[-1]['numeroAutorizacion']
                                            #ids_atracci = self.env['account.invoice']
                                            vals_accinv = {'num_autoelectronica' : num_aut,
                                                      'state_factelectro': 'autorizado',
                                                      'date_aut': time.strftime('%Y-%m-%d %H:%M:%S'),
                                                      'inf_electronica' : 'autorizado'}
                                            factura.write(vals_accinv)
                                            #accfactelect_id = ids_accfacel.create(vals_r)
                                            mensaje = str(res_autcomp.autorizaciones.autorizacion[-1]['estado'])
                                            if record:
                                                record.mensaje = mensaje
                                            #return True
                                        else:
                                            mensaje = str(res_autcomp)
                                            if record:
                                                record.mensaje = mensaje
                                            vals_inf_elect = {'inf_electronica' : mensaje}
                                            factura.write(vals_inf_elect)
                                            #return True
                                #print "MENSAJE", mensaje
                    if res_sri and res_sri['estado']=='RECIBIDA':
                        #CSV:29-12-2017: AUMENTO PARA ENVIAR ARCHIVO FIRMADO CLIENTE Y SRI PRIMER WEB SERVICES
                        #CSV: PARA ADJUNTARLO************************
                        w = open('/home/oddo/'+firmadig+'/'+'FACTURA_ELECTRONICA/FACTURAF/'+name, 'rb')
                        q=w.read()
                        out2 = base64.encodestring(q)
                        data_fname = name
                        archivo = '/home/oddo/'+firmadig+'/'+'FACTURA_ELECTRONICA/FACTURAF/'+name
                        res_model = 'account.invoice'
                        id = ids and type(ids) == type([]) and ids[0] or ids
                        self.load_doc(out2, factura.id, data_fname, archivo, res_model)
                        #Escribo en la factura*
                        num_autws1 = clavef
                        #ids_atracci = self.env['account.invoice']
                        vals_accinvws1 = {'num_autoelectronica' : num_autws1,
                                  'state_factelectro': 'firmado',
                                  'date_aut': time.strftime('%Y-%m-%d %H:%M:%S'),
                                  'inf_electronica' : 'firmado'}
                        factura.write(vals_accinvws1)
                        accfactelect_id = ids_accfacel.create(vals_r)
                        mensaje = str('firmado')
                        if record:
                            record.mensaje = mensaje
                        #return True
                    elif res_sri and res_sri['estado']=='DEVUELTA':
                        mensaje = str(res_sri)
                        if record:
                            record.mensaje = mensaje
                        vals_inf_elect = {'inf_electronica' : mensaje}
                        factura.write(vals_inf_elect)
                        #return True
                        print "NO SE ENVIO"
            # except Exception as e:
            #     # JJM 2018-03-05 sobreescribo mensaje de invoice agregando error del exeption
            #     vals_inf_elect = {'inf_electronica': u'%s  Error: %s'%(factura.inf_electronica,e),
            #                       'state_factelectro': 'error'}
            #     factura.write(vals_inf_elect)
            #     continue

            return True
                # if (t_comp == 'out_refund'):
                #     return {
                #     'name': name,
                #     'view_type': 'form',
                #     'view_mode': 'form',
                #     'res_model': 'wizard.factura.electronica',
                #     'res_id': id_m,
                #     'view_id': False,
                #     'type': 'ir.actions.act_window',
                #     'domain': [],
                #     'target': 'new',
                #     'context': self._context,
                # }

    def load_doc(self, out, id, data_fname, archivo, res_model):
        attach_vals = {
            'name': data_fname,
            'datas_fname': data_fname,
            'res_model': res_model,
            'datas': out,
            'type': 'binary',
            'file_type': 'file_type',
        }
        if id:
            ir_att = self.env['ir.attachment']
            #CSV: 22-03-2018 :AUMENTO PARA LIMPIAR ADJUNTOS ANTES DE ADJUNTAR EL NUEVO
            delet = ir_att.search([('res_id', '=', id),('res_model', '=', res_model)])
            if delet:
                for line in delet:
                    line.unlink()
            #*************************************************************************
            attach_vals.update( {'res_id': id} )
        ir_att.create(attach_vals)

    def modulo11(self, cadena):
        print "CADENA ENTRA", cadena
        baseMultiplicador = 7
        cad_tam = len(cadena)
        lista = []
        multiplicador = 2
        total = 0
        verificador = 0
        indice = 0
        valor = 0
        while indice < len(cadena):
           cad_inv = cadena[indice]
        #             print cad_inv
           lista.append(cad_inv)
           indice += 1
        lista.reverse()
        #          print "LISTA INVERTIDA", lista
        for recorre in lista:
        #              print "RECORRE", recorre
            valor = int(recorre) * multiplicador
            multiplicador += 1
            if multiplicador > baseMultiplicador:
                multiplicador = 2
            total += valor
        #              print "TOTAL", total
        #         --Ya tenemos el total
        if (total == 0 or total == 1):
            verificador = 0
        else:
            if (11 - (total % 11)) != 11:
                verificador = 11 - total % 11
            else:
                verificador = 0
        if (verificador == 10):
            verificador = 1
        print "Verificador", verificador
        return str(verificador)

    def get_identification(self, partner):
        part_type = str()
        if partner.part_type == 'c':
            part_type = 'C'
        elif partner.part_type == 'r':
            part_type = 'R'
        return part_type, partner.part_number

    def get_description(self, voucher):
        return voucher.reference

    def delete_ascii(self, s):
       s = ''.join((c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn'))
       return s

    def convert(self, s):
        esp = ['á', 'à', 'â', 'ã', 'ª', 'Á', 'À', 'Â', 'Ã', 'Í', 'Ì', 'Î', 'í', 'ì', 'î', 'é', 'è', 'ê', 'É', 'È', 'Ê', 'ó', 'ò', 'ô', 'õ', 'º', 'Ó', 'Ò', 'Ô', 'Õ', 'ú', 'ù', 'û', 'Ú', 'Ù', 'Û', 'ç', 'Ç', 'ñ', 'Ñ', 'Ñ']
        nor = ['a', 'a', 'a', 'a', 'a', 'A', 'A', 'A', 'A', 'I', 'I', 'I', 'i', 'i', 'i', 'e', 'e', 'e', 'E', 'E', 'E', 'o', 'o', 'o', 'o', 'o', 'O', 'O', 'O', 'O', 'u', 'u', 'u', 'U', 'U', 'U', 'c', 'C', 'n', 'N', 'N']
        s = str(s.encode('"UTF-8"').strip())
        for indi in range(40):
            s = s.replace(esp[indi], nor[indi])
        s = str(s)
        return s
