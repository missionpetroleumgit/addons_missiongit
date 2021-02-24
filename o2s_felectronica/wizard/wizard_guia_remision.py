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
import os, ssl
from XadesBes import jarWrapper


class wizard_guia_remision(models.TransientModel):
    _name = 'wizard.guia.remision'

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
        'company': lambda self, cr, uid, c: self.pool.get('res.company')._company_default_get(cr, uid, 'wizard.guia.remision', context=c)
    }
    @api.multi
    def generate_file(self):
# DECLARO VARIABLES Y DOC PARA FORMAR EL XML
        mensaje = ""
        doc = Document()
        res_sri = False
        cod_num = '12345678'
        fent = '001'
        femi = '001'
        ids = self._context['active_ids']
        print "ID DOCUMENTO 1:", ids
        for record in self:
            id_m = record.id
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
# OBTENER DATOS DE LA GUIA REMISION
        id_header = self._context['active_id']
        print "ID DOCUMENTO:",id_header
        g_remi = self.env['stock.picking'].browse([id_header])
        print "Guia Remision", g_remi
        secuencia = str(g_remi.name[7:] or '').zfill(9)
        print "secuencia", secuencia
        fechagr = g_remi.date
        lfecha =  fechagr.split('-')
        print "list fecha", lfecha
        fecha_gui = lfecha[2][:2]+"/"+lfecha[1]+"/"+lfecha[0]
        print "FECHA GUIA", fecha_gui
        # DIRECCION CLIENTE DESTINATARIO
        destd = g_remi.destinatario.id
        print "ID DESTINATARIO", destd
        id_dest =  g_remi.destinatario.part_number
        rz_dest = g_remi.destinatario.name
        if rz_dest:
            rz_dest = str(self.delete_ascii(rz_dest))
        mot_tras = g_remi.motivo
        if mot_tras:
            mot_tras = str(self.delete_ascii(mot_tras))
        if g_remi.doc_adu:
            doct_ad = g_remi.doc_adu
        else:
            doct_ad = "0"
        if g_remi.cod_ed:
            cod_est = g_remi.cod_ed
        else:
            cod_est = "000"
        if g_remi.ruta:
            ruta = g_remi.ruta
        else:
            ruta = ''
        s_obj_dest = self.env['res.partner'].search([('id', '=', destd)])
        #obj_dest = self.env['res.partner'].browse(s_obj_dest)
        dfactu = s_obj_dest.street
        if dfactu:
            dfactu = str(self.delete_ascii(dfactu))
        dfactu2 = s_obj_dest.street2
        if dfactu2:
            dfactu2 = str(self.delete_ascii(dfactu2))

        if dfactu and dfactu2:
            dfactuf = str(dfactu.encode('UTF-8')) + str(dfactu2.encode('UTF-8'))
        elif dfactu and not dfactu2:
            dfactuf = str(dfactu.encode('UTF-8'))
        elif dfactu2 and not dfactu:
            dfactuf = str(dfactu2.encode('UTF-8'))
        else:
            dfactuf = ''

        cmail = s_obj_dest.email
        if cmail:
            cliemail = cmail
        else:
            raise Warning(('Atencion !'), ('Ingrese el Email del cliente en la ficha!'))
        dpart = g_remi.d_partida.strip()
        print "DIRECCION PARTIDA", dpart
# DIRECCION ESTABLECIMIENTO
        dest1 = g_remi.partner_id.street
        if dest1:
            dest1 = str(self.delete_ascii(dest1))
        dest2 = g_remi.partner_id.street2
        if dest2:
            dest2 = str(self.delete_ascii(dest2))
        if dest1 and dest2:
            destable = str(dest1.encode('UTF-8')) + str(dest2.encode('UTF-8'))
        elif dest1 and not dest2:
            destable = str(dest1.encode('UTF-8'))
        elif dest2 and not dest1:
            destable = str(dest2.encode('UTF-8'))
        else:
            destable = ''
        print "DIR ESTABLECIMIENTO", destable
        # DATOS TRASPORTISTA
        ntransp = g_remi.transportista.name
        if ntransp:
            ntransp = str(self.delete_ascii(ntransp))
        print "TRANSPORTISTA NOMBRE", ntransp
        tipidt =  g_remi.transportista.cod_type_ident
        print "TIPO IDENTI TRANSPORT", tipidt
        ruct =  g_remi.transportista.part_number
        print "RUC TRANSP", ruct
        if g_remi.transportista.obli_contab:
            obli_contab =  g_remi.transportista.obli_contab
            print "OBLIGADO CONTABILIDAD", obli_contab
            if obli_contab == 'SI':
                cod_posfis = g_remi.transportista.cod_posfis
            else:
                cod_posfis = '000'
        else:
            raise Warning(('Atencion !'), ('Ingrese Informacion Fiscal en la ficha del proveedor transportista!'))
        f_init = g_remi.date_it
        fecha_ini =  f_init.split('-')
        print " lista fecha ini", fecha_ini
        fecha_inicio = fecha_ini[2]+"/"+fecha_ini[1]+"/"+fecha_ini[0]
        print "FECHA INICIO", fecha_inicio
        f_fint = g_remi.date_ft
        fecha_fin =  f_fint.split('-')
        print " lista fecha fin", fecha_fin
        fecha_fint = fecha_fin[2]+"/"+fecha_fin[1]+"/"+fecha_fin[0]
        print "FECHA FIN", fecha_fint
        #placa = g_remi.placat
        # DATOS FACTURA
        if g_remi.doc_sustento:
            cod_docs = g_remi.doc_sustento.type
            if cod_docs == 'out_invoice':
                cod_sus = '01'
            if cod_docs == 'in_refund':
                cod_sus = '05'
            if cod_docs == 'out_refund':
                cod_sus = '04'
            if cod_docs == 'in_invoice':
                cod_sus = '01'
            if g_remi.doc_sustento.authorization_id.serie_entity:
                fentp = str(g_remi.doc_sustento.authorization_id.serie_entity).strip()
            else:
                raise Warning(('Atencion !'), ('Ingrese Serie entidad proveedor para emitir su comprobante!'))
            if g_remi.doc_sustento.authorization_id.serie_emission:
                femip = str(g_remi.doc_sustento.authorization_id.serie_emission).strip()
            else:
                raise Warning(('Atencion !'), ('Ingrese Serie emision proveedor para emitir su comprobante!'))
            if g_remi.doc_sustento.number_seq:
                comprobante_n = str(g_remi.doc_sustento.number_seq).strip()
            else:
                raise Warning(('Atencion !'), ('El comprobante de sustento que cogio no tiene numero o no esta validado!'))
            if g_remi.doc_sustento.num_autoelectronica:
                num_aut_ds = g_remi.doc_sustento.num_autoelectronica
            elif g_remi.doc_sustento.num_autoreten:
                num_aut_ds = g_remi.doc_sustento.num_autoreten
            else:
                num_aut_ds = ' '
            f_doc_sus = g_remi.doc_sustento.date_invoice
            sfecha =  f_doc_sus.split('-')
            print "list fecha", sfecha
            fecha = sfecha[2]+"/"+sfecha[1]+"/"+sfecha[0]
            print "FECHA", fecha
        elif g_remi.prefactura:
            cod_sus = "01"
            if g_remi.emission_point:
                fentp = g_remi.emission_point
            else:
                fentp = '001'
            if g_remi.emission_series:
                femip = g_remi.emission_series
            else:
                femip = '001'
            comprobante_n = g_remi.prefactura
            num_aut_ds = "0000000000000000000000000000000000000"
            fecha = "01/01/2017"
        else:
            cod_sus = "01"
            fentp = '001'
            femip = '001'
            comprobante_n = '000000000'
            num_aut_ds = "0000000000000000000000000000000000000"
            fecha = "01/01/2000"
# DATOS ADICIONALES
        marca = g_remi.marca
        modelo = g_remi.modelo
        chasis = g_remi.chasis
        placatt = g_remi.placat

# OBTENER DATOS DETALLADOS GUIA REMISION
        s_move_det = self.env['stock.move'].search([('picking_id', '=', id_header)])
        print "LISTA DETALLE DE LA GR", s_move_det
        # s_move_det = self.env['stock.move'].browse(s_move)
        # print "OBJETO LINE DETALLADO", s_move_det
        cod_comp = '06'
# OBTENGO DATOS DEL FORM
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

        version = record.version
        print"version: ",version
        compania = record.company
        #print "compania: ",compania
# Obtener Informacion de la compania
        lineas = self.env['res.company'].browse([compania.id])[0]
        empresa = lineas.partner_id.name
        ruc_empresa = lineas.partner_id.part_number
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

        id_formulario = record.formulario
        if id_formulario == 'normal':
            temision = '1'
 # FORMAR CLAVE ACCESO COMPROBANTE NORMAL
            clav = str(lfecha[2][:2]+lfecha[1]+lfecha[0]+cod_comp+ruc_empresa.strip()+ambiente+fent+femi+secuencia.strip()+cod_num+temision)
            clavea = self.modulo11(clav)
            print "CLAVE MOD 11", clavea
            clavef = clav.strip()+clavea.strip()
            print "CLAVE FINAL N", clavef
            ids_accfacel = self.env['stock.picking.electronica']
            vals_r = {
                  'name' : 'Guia Remision',
                  'clave_acceso': clavef,
                  'cod_comprobante': cod_comp,
                  'gremielect_id': id_header
            }
#                 accfactelect_id = ids_accfacel.create(cr,uid,vals_r)
        elif id_formulario == 'contingencia':
            temision = '2'
            cconti = record.contingencia
            if len(cconti) < 37:
                raise Warning(('Atencion !'), ('Clave de contingencia debe tener 37 caracteres numericos!'))
            else:
# FORMAR CLAVE ACCESO COMPROBANTE CONTINGENCIA
                clav = str(lfecha[2][:2]+lfecha[1]+lfecha[0]+cod_comp+cconti.strip()+temision)
                clavea = self.modulo11(clav)
                print "CLAVE MOD 11", clavea
                clavef = clav.strip()+clavea.strip()
                print "CLAVE FINAL C", clavef
                ids_accfacel = self.env['stock.picking.electronica']
                vals_r = {
                      'name' : 'Guia Remision',
                      'clave_contingencia': cconti,
                      'contingencia': True,
                      'cod_comprobante': cod_comp,
                      'gremielect_id': id_header
                }
#                     accfactelect_id = ids_accfacel.create(cr,uid,vals_r)
#         raise osv.except_osv(('Atencion !'), ('OJO!'))
# TAG CONTENEDOR COMPROBANTE
        mainform = doc.createElement('guiaRemision')
        doc.appendChild(mainform)
        mainform.setAttribute('id', 'comprobante')
        mainform.setAttribute('version', version)
# TAGS HIJOS DEL CONTENEDOR COMPROBANTE
        infoTributaria = doc.createElement("infoTributaria")
        mainform.appendChild(infoTributaria)

        infoFactura = doc.createElement("infoGuiaRemision")
        mainform.appendChild(infoFactura)

        destinatarios = doc.createElement("destinatarios")
        mainform.appendChild(destinatarios)

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
# TAGS HIJOS DEL TAG INFOGUIA
        destablecimiento = doc.createElement("dirEstablecimiento")
        infoFactura.appendChild(destablecimiento)
        ndestable_id = doc.createTextNode(destable.strip())
        destablecimiento.appendChild(ndestable_id)

        d_partida = doc.createElement("dirPartida")
        infoFactura.appendChild(d_partida)
        nd_partida = doc.createTextNode(dpart)
        d_partida.appendChild(nd_partida)

        rz_trasp = doc.createElement("razonSocialTransportista")
        infoFactura.appendChild(rz_trasp)
        nrz_trasp = doc.createTextNode(ntransp.strip())
        rz_trasp.appendChild(nrz_trasp)

        ti_identt = doc.createElement("tipoIdentificacionTransportista")
        infoFactura.appendChild(ti_identt)
        nti_identt = doc.createTextNode(tipidt.strip())
        ti_identt.appendChild(nti_identt)

        ruc_tra = doc.createElement("rucTransportista")
        infoFactura.appendChild(ruc_tra)
        nruc_tra = doc.createTextNode(ruct)
        ruc_tra.appendChild(nruc_tra)

        rise = doc.createElement("rise")
        infoFactura.appendChild(rise)
        nrise_id = doc.createTextNode('NO')
        rise.appendChild(nrise_id)

        oblicont = doc.createElement("obligadoContabilidad")
        infoFactura.appendChild(oblicont)
        noblicont_id = doc.createTextNode(obli_contab.strip())
        oblicont.appendChild(noblicont_id)

        contesp = doc.createElement("contribuyenteEspecial")
        infoFactura.appendChild(contesp)
        ncontesp_id = doc.createTextNode(cod_posfis.strip())
        contesp.appendChild(ncontesp_id)

        f_intt = doc.createElement("fechaIniTransporte")
        infoFactura.appendChild(f_intt)
        nf_intt = doc.createTextNode(fecha_inicio.strip())
        f_intt.appendChild(nf_intt)

        f_fint = doc.createElement("fechaFinTransporte")
        infoFactura.appendChild(f_fint)
        nf_fint = doc.createTextNode(fecha_fint.strip())
        f_fint.appendChild(nf_fint)

        placa = doc.createElement("placa")
        infoFactura.appendChild(placa)
        nplaca = doc.createTextNode(placatt.strip())
        placa.appendChild(nplaca)

        destinatario = doc.createElement("destinatario")
        destinatarios.appendChild(destinatario)

        id_destina = doc.createElement("identificacionDestinatario")
        destinatario.appendChild(id_destina)
        nid_destina = doc.createTextNode(id_dest.strip())
        id_destina.appendChild(nid_destina)

        rz_destina = doc.createElement("razonSocialDestinatario")
        destinatario.appendChild(rz_destina)
        nrz_destina = doc.createTextNode(rz_dest.strip())
        rz_destina.appendChild(nrz_destina)

        dir_destina = doc.createElement("dirDestinatario")
        destinatario.appendChild(dir_destina)
        ndir_destina = doc.createTextNode(dfactuf.strip())
        dir_destina.appendChild(ndir_destina)

        mot_trasla = doc.createElement("motivoTraslado")
        destinatario.appendChild(mot_trasla)
        nmot_tras = doc.createTextNode(mot_tras.strip())
        mot_trasla.appendChild(nmot_tras)

        if g_remi.doc_adu:
            doc_adunico = doc.createElement("docAduaneroUnico")
            destinatario.appendChild(doc_adunico)
            ndoc_adunico = doc.createTextNode(doct_ad.strip())
            doc_adunico.appendChild(ndoc_adunico)

        if g_remi.cod_ed:
            cod_estable = doc.createElement("codEstabDestino")
            destinatario.appendChild(cod_estable)
            ncod_estable = doc.createTextNode(cod_est.strip())
            cod_estable.appendChild(ncod_estable)

        ruta_guia = doc.createElement("ruta")
        destinatario.appendChild(ruta_guia)
        nruta_guia = doc.createTextNode(ruta.strip())
        ruta_guia.appendChild(nruta_guia)

        if g_remi.doc_sustento:
	    cod_docsus = doc.createElement("codDocSustento")
	    destinatario.appendChild(cod_docsus)
	    ncod_docsus = doc.createTextNode(cod_sus.strip())
	    cod_docsus.appendChild(ncod_docsus)

	    num_docsus = doc.createElement("numDocSustento")
	    destinatario.appendChild(num_docsus)
	    nnum_docsus = doc.createTextNode(str(fentp+'-'+femip+'-'+comprobante_n).strip())
	    num_docsus.appendChild(nnum_docsus)

	    num_autsus = doc.createElement("numAutDocSustento")
	    destinatario.appendChild(num_autsus)
	    nnum_autsus = doc.createTextNode(num_aut_ds.strip())
	    num_autsus.appendChild(nnum_autsus)

	    fe_docsus = doc.createElement("fechaEmisionDocSustento")
	    destinatario.appendChild(fe_docsus)
	    nfe_docsus = doc.createTextNode(fecha.strip())
	    fe_docsus.appendChild(nfe_docsus)

        detalles = doc.createElement("detalles")
        destinatario.appendChild(detalles)

# OBTENER DETALLE POR PRODUCTO
        for det_impf in s_move_det:
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
            nam_lin = self.delete_ascii(det_impf.name)
            nddescrip_id = doc.createTextNode(str(nam_lin or '').strip())
            ddescrip.appendChild(nddescrip_id)

            dcanti = doc.createElement("cantidad")
            detalle.appendChild(dcanti)
            fquty = Decimal(det_impf.product_qty).quantize(Decimal('0.00'))
            ndcanti_id = doc.createTextNode(str(fquty))
            dcanti.appendChild(ndcanti_id)


            detallesAdicionales = doc.createElement("detallesAdicionales")
            detalle.appendChild(detallesAdicionales)
            detAdicional = doc.createElement('detAdicional')
            detallesAdicionales.appendChild(detAdicional)
            detAdicional.setAttribute('nombre', 'Marca')
            detAdicional.setAttribute('valor', str(marca))
            detAdicional1 = doc.createElement('detAdicional')
            detallesAdicionales.appendChild(detAdicional1)
            detAdicional1.setAttribute('nombre', 'Modelo')
            detAdicional1.setAttribute('valor', str(modelo))
            detAdicional2 = doc.createElement('detAdicional')
            detallesAdicionales.appendChild(detAdicional2)
            detAdicional2.setAttribute('nombre', 'Chasis')
            detAdicional2.setAttribute('valor', str(chasis))


        cadicional = doc.createElement('campoAdicional')
        infoAdicional.appendChild(cadicional)
        cadicional.setAttribute('nombre', 'mail')
        cadicional_id = doc.createTextNode(cliemail)
        cadicional.appendChild(cadicional_id)


        out = base64.encodestring(doc.toxml())
        name = "%s.xml" % (clavef)
        print "NOMBRE COMPROBANTE GUARDAR", name
        record.data = out
        f = open('/home/oddo/'+firmadig+'/'+'FACTURA_ELECTRONICA/GUIASF/'+name, 'w')
        f.write(doc.toxml())
        f.close()
#*******************************************************************************************************************
	if firmadig == 'MISSION PETROLEUM S.A.':
            print "ENTRO MISSION PETROLEUM S.A."
            res = jarWrapper('/opt/addons_mission/o2s_felectronica/wizard/XadesBes.jar',
                             '/opt/addons_mission/o2s_felectronica/wizard/'+firmadig+'/'+'firmaMissionPetroleum2018.p12',
                             'mission2020','/home/oddo/'+firmadig+'/'+'FACTURA_ELECTRONICA/GUIASF/'+name,
                             '/home/oddo/'+firmadig+'/'+'FACTURA_ELECTRONICA/GUIAF',name)
            print "RES", res
            w = open('/home/oddo/'+firmadig+'/'+'FACTURA_ELECTRONICA/GUIAF/'+name, 'rb')
            q=w.read()

        res_sri =  client.service.validarComprobante(base64.encodestring(q))
        print "RESPUESTA*****", res_sri['estado']
        if g_remi.state_remielectro == 'firmado':
            clavef = g_remi.num_autoremi
            autorizada = 0
            while autorizada != 1:
                res_autcomp =  client1.service.autorizacionComprobante(clavef)
                print "OBJETO AUTORIZA1***", res_autcomp
                if len(res_autcomp.autorizaciones) > 0:
                    if len(res_autcomp.autorizaciones.autorizacion[0]) > 0:
                        estado_ws = res_autcomp.autorizaciones.autorizacion[0]['estado']
                        autorizada = 1
                        if str(estado_ws).strip() == 'AUTORIZADO':
                            num_aut = res_autcomp.autorizaciones.autorizacion[0]['numeroAutorizacion']
                            ids_atracci = self.env['stock.picking']
                            vals_accinv = {'num_autoremi' : num_aut,
                                      'state_remielectro': 'autorizado',
                                      'date_aut_remi': time.strftime('%Y-%m-%d %H:%M:%S')}#'inf_electronica' : 'firmado'
                            g_remi.write(vals_accinv)
                            #accfactelect_id = ids_accfacel.create(vals_r)
                            mensaje = str(estado_ws)
                            record.mensaje = mensaje
                        else:
                            if res_autcomp.autorizaciones.autorizacion[-1]['estado'] == 'AUTORIZADO':
                                num_aut = res_autcomp.autorizaciones.autorizacion[-1]['numeroAutorizacion']
                                ids_atracci = self.env['stock.picking']
                                vals_accinv = {'num_autoremi' : num_aut,
                                          'state_remielectro': 'autorizado',
                                          'date_aut_remi': time.strftime('%Y-%m-%d %H:%M:%S')}#'inf_electronica' : 'firmado'
                                g_remi.write(vals_accinv)
                                #accfactelect_id = ids_accfacel.create(vals_r)
                                mensaje = str(res_autcomp.autorizaciones.autorizacion[-1]['estado'])
                            else:
                                mensaje = str(res_autcomp)
                                record.mensaje = mensaje

        if res_sri and res_sri['estado']=='RECIBIDA':
            #CSV:29-12-2017: AUMENTO PARA ENVIAR ARCHIVO FIRMADO CLIENTE Y SRI PRIMER WEB SERVICES
            #CSV: PARA ADJUNTARLO************************
            # w = open('/home/oddo/'+firmadig+'/'+'FACTURA_ELECTRONICA/GUIAF/'+name, 'rb')
            # q=w.read()
            # out2 = base64.encodestring(q)
            # data_fname = name
            # archivo = '/home/oddo/'+firmadig+'/'+'FACTURA_ELECTRONICA/GUIAF/'+name
            # res_model = 'account.invoice'
            # id = ids and type(ids) == type([]) and ids[0] or ids
            # self.load_doc(out2, g_remi.id, data_fname, archivo, res_model)
            #Escribo en el albarran*
            num_autws1 = clavef
            vals_accinv = {'num_autoremi' : num_autws1,
                          'state_remielectro': 'firmado',
                          'date_aut_remi': time.strftime('%Y-%m-%d %H:%M:%S')} #'inf_electronica' : 'firmado'
            g_remi.write(vals_accinv)
            accfactelect_id = ids_accfacel.create(vals_r)
            mensaje = str('firmado')
            record.mensaje = mensaje
        elif res_sri['estado'] == 'DEVUELTA':
            mensaje = str(res_sri)
            record.mensaje = mensaje
            print "NO SE ENVIO"

        return {
                'name': name,
                'mensaje': mensaje,
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'wizard.guia.remision',
                'res_id': id_m,
                'view_id': False,
                'type': 'ir.actions.act_window',
                'domain': [],
                'target': 'new',
                'context': self._context,
            }

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
            attach_vals.update( {'res_id': id})
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
