# -*- coding: utf-8 -*-
import unicodedata
from openerp import models, fields, api
from string import upper
from openerp.exceptions import except_orm, Warning
import base64
import os
import StringIO
from datetime import datetime
#**************************************************
import time
import math
from time import strftime
from decimal import *
from xml.dom.minidom import Document
from suds.client import Client
from math import *
from XadesBes import jarWrapper
import os, ssl


class wizard_comprobante_retencion(models.TransientModel):
    _name = 'wizard.comprobante.retencion'

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
        'version': lambda * a: '1.0.0',
        'ambiente': lambda * a: 'produccion',
        'company': lambda self, cr, uid, c: self.pool.get('res.company')._company_default_get(cr, uid, 'wizard.factura.electronica', context=c)
    }
    @api.multi
    def generate_file(self):
# DECLARO VARIABLES Y DOC PARA FORMAR EL XML
        mensaje = ""
        doc = Document()
        doc1 = Document()
        cod_num = '12345678'
        serie = '001001'
        ids = self._context['active_ids']
        print "ID DOCUMENTO 1:", ids
        for record in self:
            id_m = record.id
            id_ambiente = record.ambiente
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
                if url:
                    client = Client(url, timeout=10)
                else:
                    raise Warning(('Atencion !'), ('No responde SRI intente mas tarde!'))
                if url1:
                    client1 = Client(url1, timeout=10)
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
                client = Client(url, timeout=10)
                client1 = Client(url1, timeout=10)
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

        id_formulario = record.formulario
        if id_formulario == 'normal':
            temision = '1'
        elif id_formulario == 'contingencia':
            temision = '2'
#
# OBTENER DATOS DE LA FACTURA
        id_header = self._context['active_id']
        print "ID DOCUMENTO:",id_header
        #CSV:28-12-2017:ONLINE
        #factura = self.env['account.invoice'].browse([id_header])
        for factura in self.env['account.invoice'].browse(ids):
            doc = Document()
            doc1 = Document()
            res_sri = False
            vals_accinvws1 = {}
            print "Factura", factura.id
            t_comp = factura.type
            print "TIPO COMPROBANTE", t_comp
            if factura.state_factelectro == 'autorizado' or factura.type not in ('in_invoice'):
                continue
            if factura.state_factelectro not in ('autorizado', 'firmado'):
        # PARA INSTANCIAR OBJETO AUTORIZACION
                auth = self.env['account.authorization'].browse([factura.deduction_id.authorization_id.id])
                print "Autorizacion", auth
                secuencia = factura.deduction_id.number
                print "secuencia", secuencia
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
                if dfactu:
                    dfactu = self.delete_ascii(factura.partner_id.street)
                dfactu2 = factura.partner_id.street2
                if dfactu2:
                    dfactu2 = self.delete_ascii(factura.partner_id.street2)
                cmail = factura.partner_id.email
                if cmail:
                    cliemail = cmail
                else:
                    raise Warning(('Atencion !'), ('Ingrese el Email del cliente en la ficha!'))
                if dfactu and dfactu2:
                    dfactuf = str(dfactu) +" "+ str(dfactu2)
                elif dfactu and not dfactu2:
                    dfactuf = str(dfactu)
                elif dfactu2 and not dfactu:
                    dfactuf = str(dfactu2)
                else:
                    dfactuf = ''
                print "DIR FACTU", dfactuf
                t_comp = factura.type
                print "TIPO COMPROBANTE", t_comp
                cod_ident = factura.partner_id.cod_type_ident
                print "COD IDENT", cod_ident
                name_rzc = factura.partner_id.name
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
                    else:
                        descuentt = det_fact.discount
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

                if factura.is_inv_elect:
                    fent = factura.emission_point
                    femi = factura.emission_series
                else:
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
        #********************************************************************************************************
                if factura.deduction_id.authorization_id.serie_entity:
                    fentp = str(factura.deduction_id.authorization_id.serie_entity).strip()
                else:
                    raise Warning(('Atencion !'), ('Ingrese Serie entidad proveedor para emitir su comprobante!'))
                if factura.deduction_id.authorization_id.serie_emission:
                    femip = str(factura.deduction_id.authorization_id.serie_emission).strip()
                else:
                    raise Warning(('Atencion !'), ('Ingrese Serie emision proveedor para emitir su comprobante!'))
                if factura.number_seq:
                    comprobante_n = str(factura.number_seq).strip()
                else:
                    raise Warning(('Atencion !'), ('Ingrese Numero de comprobante sustento de esta retencion!'))
                cod_ds = factura.document_type.code

        # OBTENER DATOS DE LOS IMPUESTOS
                tax_id = self.env['account.invoice.tax'].search([('invoice_id', '=', factura.id), ('deduction_id', '=', False)])
                print "LISTA IMPUESTOS", tax_id
                for imp in tax_id:
                    print "LISTA IMPUESTOS 1", imp.tax_code_id
                    print "LISTA IMPUESTOS 2", imp.tax_code_id.cod_imp_fe
        # OBTENER DATOS DE LAS RETENCIONES
                ret_id = self.env['account.invoice.tax'].search([('invoice_id', '=', factura.id), ('deduction_id', '!=', False)])
                print "LISTA RETENCIONES", ret_id
                for rett in ret_id:
                    print "LISTA IMPUESTOS 1", rett.tax_code_id
                    print "LISTA IMPUESTOS 2", rett.tax_code_id.cod_imp_fe
                ret_det = self.env['account.invoice.tax'].browse(ret_id)
        # OBTENER DATOS DETALLE DE LA FACTURA
                invdet_id = self.env['account.invoice.line'].search([('invoice_id', '=', factura.id)])
                print "LISTA DETALLE DE LA FACTURA", invdet_id
                invdet_det = self.env['account.invoice.line'].browse(invdet_id)
                print "OBJETO LINE DETALLADO", invdet_det
                cod_comp = '07'

        # OBTENGO DATOS DEL FORM
                version = record.version
                print"version: ",version
                compania = record.company
                print "compania: ",compania
        # Obtener Informacion de la compania
                lineas = self.env['res.company'].browse([compania.id])[0]
                empresa = lineas.partner_id.name
                ruc_empresa = lineas.partner_id.part_number
                user = self.env.user
                print "USER**", user
                direccion = ''
                if user.company_id.partner_id.street and user.company_id.partner_id.street2:
                    direccion = str(user.company_id.partner_id.street) + ' Y ' + str(user.company_id.partner_id.street2)
                elif user.company_id.partner_id.street and not user.company_id.partner_id.street2:
                    direccion = str(user.company_id.partner_id.street)
                elif user.company_id.partner_id.street2 and not  user.company_id.partner_id.street:
                    direccion = str(user.company_id.partner_id.street2)
                print "direccion", direccion

                if id_formulario == 'normal':
                    temision = '1'
         # FORMAR CLAVE ACCESO COMPROBANTE NORMAL
                    clav = str(lfecha[2]+lfecha[1]+lfecha[0]+cod_comp+ruc_empresa.strip()+ambiente+fentp+femip+secuencia.strip()+cod_num+temision)
                    clavea = self.modulo11(clav)
                    print "CLAVE MOD 11", clavea
                    clavef = clav.strip()+clavea.strip()
                    print "CLAVE FINAL N", clavef
                    ids_accfacel = self.env['account.factura.electronica']
                    vals_r = {
                          'name' : 'Comprobante Retencion',
                          'clave_acceso': clavef,
                          'cod_comprobante': cod_comp,
                          'factelect_id': factura.id
                    }
        #                 accfactelect_id = ids_accfacel.create(cr,uid,vals_r)
                elif id_formulario == 'contingencia':
                    temision = '2'
                    cconti = record.contingencia
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
                              'name' : 'Comprobante Retencion',
                              'clave_contingencia': cconti,
                              'contingencia': True,
                              'cod_comprobante': cod_comp,
                              'factelect_id': factura.id
                        }
        #                     accfactelect_id = ids_accfacel.create(cr,uid,vals_r)
        # TAG CONTENEDOR COMPROBANTE
                mainform = doc.createElement('comprobanteRetencion')
                doc.appendChild(mainform)
                mainform.setAttribute('id', 'comprobante')
                mainform.setAttribute('version', version)
        # TAGS HIJOS DEL CONTENEDOR COMPROBANTE
                infoTributaria = doc.createElement("infoTributaria")
                mainform.appendChild(infoTributaria)

                infoFactura = doc.createElement("infoCompRetencion")
                mainform.appendChild(infoFactura)

                impuestos = doc.createElement("impuestos")
                mainform.appendChild(impuestos)

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
                nestab_id = doc.createTextNode(fentp.strip())
                estab.appendChild(nestab_id)

                ptoemi = doc.createElement("ptoEmi")
                infoTributaria.appendChild(ptoemi)
                nptoemi_id = doc.createTextNode(femip.strip())
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

                tidencomp = doc.createElement("tipoIdentificacionSujetoRetenido")
                infoFactura.appendChild(tidencomp)
                ntidencomp_id = doc.createTextNode(cod_ident.strip())
                tidencomp.appendChild(ntidencomp_id)

                rasocomp = doc.createElement("razonSocialSujetoRetenido")
                infoFactura.appendChild(rasocomp)
                nrasocomp_id = doc.createTextNode(name_rzc.strip())
                rasocomp.appendChild(nrasocomp_id)

                identcomp = doc.createElement("identificacionSujetoRetenido")
                infoFactura.appendChild(identcomp)
                nidentcomp_id = doc.createTextNode(id_rzc.strip())
                identcomp.appendChild(nidentcomp_id)

                pfiscal = doc.createElement("periodoFiscal")
                infoFactura.appendChild(pfiscal)
                npfiscal_id = doc.createTextNode(str(factura.period_id.code))
                pfiscal.appendChild(npfiscal_id)

                for impuesto in ret_id:
                    print "RET COD1", impuesto
                    print "RET COD2", impuesto.tax_code_id
                    print "RET COD3", impuesto.tax_code_id.cod_imp_fe
                    if impuesto.tax_code_id.cod_imp_fe == '1':
                        cod_retfe = impuesto.base_code_id.code
                        if cod_retfe:
                            print "ok retencion"
                        else:
                            raise Warning(('Atencion !'), ('No hay configurado codigo base de la retencion de esta factura!'))
                    else:
                        cod_retfe = impuesto.tax_code_id.cod_tarifa
                        if cod_retfe:
                            print "ok retencion"
                        else:
                            raise Warning(('Atencion !'), ("No hay configurado codigo tarifa en impuestos codigos '%s' !" )%str(impuesto.tax_code_id.name))
                    totalimp = doc.createElement("impuesto")
                    impuestos.appendChild(totalimp)
            # TAG SE REPITE CODIGO IMPUESTOS SEGUN LA FACTURA
                    fcodigo = doc.createElement("codigo")
                    totalimp.appendChild(fcodigo)
                    nfcodigo_id = doc.createTextNode(impuesto.tax_code_id.cod_imp_fe)
                    fcodigo.appendChild(nfcodigo_id)

                    codpor = doc.createElement("codigoRetencion")
                    totalimp.appendChild(codpor)
                    ncodpor_id = doc.createTextNode(cod_retfe)
                    codpor.appendChild(ncodpor_id)

                    basimp = doc.createElement("baseImponible")
                    totalimp.appendChild(basimp)
                    vbaseimp = Decimal(abs(impuesto.base_amount)).quantize(Decimal('0.00'))
                    nbasimp_id = doc.createTextNode(str(vbaseimp))
                    basimp.appendChild(nbasimp_id)

                    dtarifa = doc.createElement("porcentajeRetener")
                    totalimp.appendChild(dtarifa)
                    v_tar_imp = Decimal(impuesto.tax_code_id.tarifa).quantize(Decimal('0.00'))
                    ndtarifa_id = doc.createTextNode(str(v_tar_imp))
                    dtarifa.appendChild(ndtarifa_id)

                    fvalor = doc.createElement("valorRetenido")
                    totalimp.appendChild(fvalor)
                    vamount = Decimal(abs(impuesto.amount)).quantize(Decimal('0.00'))
                    nfvalor_id = doc.createTextNode(str(vamount))
                    fvalor.appendChild(nfvalor_id)

                    cdm = doc.createElement("codDocSustento")
                    totalimp.appendChild(cdm)
                    ncdm_id = doc.createTextNode(cod_ds.strip())
                    cdm.appendChild(ncdm_id)

                    ndm = doc.createElement("numDocSustento")
                    totalimp.appendChild(ndm)
                    nndm_id = doc.createTextNode(str(femi+fent+comprobante_n).strip())
                    ndm.appendChild(nndm_id)

                    feds = doc.createElement("fechaEmisionDocSustento")
                    totalimp.appendChild(feds)
                    nfeds_id = doc.createTextNode(fecha.strip())
                    feds.appendChild(nfeds_id)


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

                print "DOC**", doc
                out = base64.encodestring(doc.toxml())
                name = "%s.xml" % (clavef)
                record.name = name
                print "NOMBRE COMPROBANTE GUARDAR", name
                record.data = out
                f = open('/home/oddo/'+firmadig+'/'+'FACTURA_ELECTRONICA/FACTURASF/'+name, 'w')
                f.write(doc.toxml())
                f.close()
#**********************************************************************************************************
                if firmadig == 'MISSION PETROLEUM S.A.':
                    print "ENTRO MISSION PETROLEUM S.A."
                    res = jarWrapper('/opt/addons_mission/o2s_felectronica/wizard/XadesBes.jar',
                                     '/opt/addons_mission/o2s_felectronica/wizard/'+firmadig+'/'+'firmaMissionPetroleum2018.p12',
                                     'mission2020','/home/oddo/'+firmadig+'/'+'FACTURA_ELECTRONICA/FACTURASF/'+name,
                                     '/home/oddo/'+firmadig+'/'+'FACTURA_ELECTRONICA/FACTURAF',name)
                    print "RES", res
                    w = open('/home/oddo/'+firmadig+'/'+'FACTURA_ELECTRONICA/FACTURAF/'+name, 'rb')
                    q=w.read()
#***********************************************************************************************************
                res_sri =  client.service.validarComprobante(base64.encodestring(q))
               # print "RESPUESTA*****", res_sri
    #             print "ESTADO*****", res_sri[0]
            #CSV: AUMENTO PARA EL CASO DE SOLO CONSULTAR
            if factura.state_factelectro == 'firmado':
                clavef = factura.num_autoreten
                print "factura.num_autoreten", factura.num_autoreten
                print "factura.state_factelectro", factura.state_factelectro
                autorizada = 0
                while autorizada != 1:
                    res_autcomp =  client1.service.autorizacionComprobante(clavef)
                    # print "OBJETO AUTORIZA1***", res_autcomp
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
                                vals_accinv = {'num_autoreten' : num_aut,
                                          'state_factelectro': 'autorizado',
                                          'date_aut': time.strftime('%Y-%m-%d %H:%M:%S'),
                                          'inf_electronica' : 'autorizado'}
                                factura.write(vals_accinv)
                                #accfactelect_id = ids_accfacel.create(vals_r)
                                mensaje = str(estado_ws)
                                record.mensaje = mensaje
                            else:
                                if res_autcomp.autorizaciones.autorizacion[-1]['estado'] == 'AUTORIZADO':
                                    num_aut = res_autcomp.autorizaciones.autorizacion[-1]['numeroAutorizacion']
                                    #ids_atracci = self.env['account.invoice']
                                    vals_accinv = {'num_autoreten' : num_aut,
                                              'state_factelectro': 'autorizado',
                                              'date_aut': time.strftime('%Y-%m-%d %H:%M:%S'),
                                              'inf_electronica' : 'autorizado'}
                                    factura.write(vals_accinv)
                                    #accfactelect_id = ids_accfacel.create(vals_r)
                                    mensaje = str(res_autcomp.autorizaciones.autorizacion[-1]['estado'])
                                    record.mensaje = mensaje
                                else:
                                    mensaje = str(res_autcomp)
                                    record.mensaje = mensaje
                                    vals_inf_elect = {'inf_electronica' : mensaje}
                                    factura.write(vals_inf_elect)
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
                val_aut = {'name' : num_autws1}
                auth.write(val_aut)
                vals_accinvws1 = {'num_autoreten' : num_autws1,
                          'state_factelectro': 'firmado',
                          'date_aut': time.strftime('%Y-%m-%d %H:%M:%S'),
                          'inf_electronica' : 'firmado'}
                factura.write(vals_accinvws1)
                accfactelect_id = ids_accfacel.create(vals_r)
                mensaje = str('firmado')
                record.mensaje = mensaje
            elif res_sri and res_sri['estado']=='DEVUELTA':
                mensaje = str(res_sri)
                record.mensaje = mensaje
                vals_inf_elect = {'inf_electronica' : mensaje}
                factura.write(vals_inf_elect)
                print "NO SE ENVIO"
        return True
        # return {
        #         'name': name,
        #         'mensaje': mensaje,
        #         'view_type': 'form',
        #         'view_mode': 'form',
        #         'res_model': 'wizard.comprobante.retencion',
        #         'res_id': id_m,
        #         'view_id': False,
        #         'type': 'ir.actions.act_window',
        #         'domain': [],
        #         'target': 'new',
        #         'context': self._context,
        #     }

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
