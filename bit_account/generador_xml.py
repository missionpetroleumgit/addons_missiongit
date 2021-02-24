# -*- coding: utf-8 -*-

# Importar librerías utilizadas
from lxml import etree
from xml.dom.minidom import Document
from datetime import datetime, date, time, timedelta
from decimal import *
from openerp.osv import fields, osv
import time
from time import strftime
import os
import base64


def crearXML(doc='Unknow', url='/opt/temp/'):	# Me crea el fichero con la fecha del período
    archi=open(str(url) + str(doc) + '.xml','w')
    archi.close()

def getHeader(encabezado): # Devuelve el nodo de la Cabecera del XML
	header = etree.Element("cabecera")
	codigo_version_form = etree.SubElement(header, 'codigo_version_formulario')
	codigo_version_form.text = '01' # encabezado.get('version')
	ruc = etree.SubElement(header, 'ruc')
	ruc.text = encabezado.get('ruc')
	codigo_moneda = etree.SubElement(header, 'codigo_moneda')
	codigo_moneda.text = '1'
	return header

def getTaxes(): # Me devuelve los impuestos que se deben agregar en el XML
	return [{'num': '401', 'amount': 100.0}, 
			{'num': '411', 'amount': 75.0}, 
			{'num': '421', 'amount': 9.0},
			{'num': '402', 'amount': 100.0}, 
			{'num': '412', 'amount': 100.0}, 
			{'num': '422', 'amount': 12.0}]

def formarXML(brw_codes, header, head_static, is_ats): # Lógica para formar el XML que devolveré
    res = ''
    if is_ats:
        iva = etree.Element("iva")
        
        for h in header.keys(): # Agregando los nodos fijos
            campo = etree.SubElement(iva, h)
            campo.text = str(header.get(h))
        
        nodes = getNodes(brw_codes)
        for nodo in nodes:
            iva.append(nodo)
        res = etree.tostring(iva, pretty_print=True)
        #print "RES****", res
    else:
        formulario = etree.Element("formulario", version="0.2")
        formulario.append( getHeader(header) ) # Agregando el nodo de cabecera
        detalle = etree.SubElement(formulario, 'detalle')
        
        for h in head_static.keys():
            campo = etree.SubElement(detalle, 'campo', numero=h)
            campo.text = str(head_static.get(h))
            
        for tax in brw_codes:
            campo = False
            campo = etree.SubElement(detalle, 'campo', numero=tax.get('code'))
            campo.text = str(abs(tax.get('sum_period')))
        res = etree.tostring(formulario, pretty_print=True)
        
    return res

def formarXMLATS(self, cr, uid, brw_codes, header, head_static, is_ats): # Lógica para formar el XML que devolveré
    res = ''
    #print "HEADER**", header
    #print "OJO******", str(header.get('TipoIDInformante'))
    tipinf = str(header.get('TipoIDInformante'))
    idinf = str(header.get('IdInformante'))
    raz = str(header.get('razonSocial'))
    anio = str(header.get('Anio'))
    mes = str(header.get('Mes'))
    numest = str(header.get('numEstabRuc'))
    totvent = str(header.get('totalVentas'))
    cod_ope = str(header.get('codigoOperativo'))
    
    if is_ats:
        doc = Document()
        
        mainform = doc.createElement("iva")
        doc.appendChild(mainform)
        
        tipo_id = doc.createElement("TipoIDInformante")
        mainform.appendChild(tipo_id)
        ptipo_id = doc.createTextNode(tipinf.strip())
        tipo_id.appendChild(ptipo_id)
        
        ruc = doc.createElement("IdInformante")
        mainform.appendChild(ruc)
        pruc = doc.createTextNode(idinf.rstrip())
        ruc.appendChild(pruc)
        
        social = doc.createElement("razonSocial")
        mainform.appendChild(social)
        psocial = doc.createTextNode(raz.replace('.', ' ').rstrip())
        social.appendChild(psocial)
        
        fec_anio = doc.createElement("Anio")
        mainform.appendChild(fec_anio)
        pfec_anio = doc.createTextNode(anio.rstrip())
        fec_anio.appendChild(pfec_anio)
        
        fec_mes = doc.createElement("Mes")
        mainform.appendChild(fec_mes)
        pfec_mes = doc.createTextNode(mes.rstrip())
        fec_mes.appendChild(pfec_mes)
        
        num_estab = doc.createElement("numEstabRuc")
        mainform.appendChild(num_estab)
        pnum_estab = doc.createTextNode(numest.strip())
        num_estab.appendChild(pnum_estab)
        
        tot_ventas = doc.createElement("totalVentas")
        mainform.appendChild(tot_ventas)
        f_tot_ventas = Decimal(totvent).quantize(Decimal('0.00'))
        ptot_ventas = doc.createTextNode(str(f_tot_ventas))
        tot_ventas.appendChild(ptot_ventas)
        
        cod_oper = doc.createElement("codigoOperativo")
        mainform.appendChild(cod_oper)
        pcod_oper = doc.createTextNode(cod_ope.strip())
        cod_oper.appendChild(pcod_oper)
        

        compras_form = doc.createElement("compras")
        mainform.appendChild(compras_form)
        #print "*OJO COMPRAS*********", brw_codes.get('compras')
        for h in brw_codes.get('compras'):
            #print "COMPRAS 1***", h
            k_list = h.keys()
            for t in k_list:
                #print '- - - 80', t
                detalle_compras_form = doc.createElement("detalleCompras")
                compras_form.appendChild(detalle_compras_form)
                tipCom = ''
                Estab = ''
                puntEmi = ''
                secIni = ''
                secFin = ''
                auto = ''
                for tag in h.get(t).keys():
                    if tag == 'codSustento':
                        cod_sus = str(h.get(t).get(tag))
                    elif tag == 'ifact':
                        idfac = h.get(t).get(tag)
                    elif tag == 'tpIdProv':
                        tip_pro = str(h.get(t).get(tag))
                    elif tag == 'idProv':
                        id_prov = str(h.get(t).get(tag))
                    elif tag == 'tipoComprobante':
                        tip_comp = str(h.get(t).get(tag))
                    elif tag == 'fechaRegistro':
                        fec_reg = str(h.get(t).get(tag))
                    elif tag == 'establecimiento':
                        estab = str(h.get(t).get(tag))
                    elif tag == 'puntoEmision':
                        punt_emi = str(h.get(t).get(tag))
                    elif tag == 'secuencial':
                        sec = str(h.get(t).get(tag))
                    elif tag == 'fechaEmision':
                        fech_emi = str(h.get(t).get(tag))
                    elif tag == 'autorizacion':
                        print "aut", str(h.get(t).get(tag))
                        aut = str(h.get(t).get(tag))
                    elif tag == 'baseNoGraIva':
                        bas_ngi = str(h.get(t).get(tag))                        
                    elif tag == 'baseImponible':
                        bas_imp = str(h.get(t).get(tag))
                    elif tag == 'baseImpGrav':
                        bas_imp_gra = str(h.get(t).get(tag))
                    elif tag == 'baseImpExe':
                        bas_imp_exe = str(h.get(t).get(tag))
                    elif tag == 'montoIce':
                        mont_ice = str(h.get(t).get(tag))
                    elif tag == 'montoIva':
                        mont_iva = str(h.get(t).get(tag))
                    elif tag == 'valRetBien10':
                        val_ret10 = str(h.get(t).get(tag))
                    elif tag == 'valRetServ20':
                        val_ret20 = str(h.get(t).get(tag))
                    elif tag == 'valorRetBienes':
                        val_retbie = str(h.get(t).get(tag))
                    elif tag == 'valRetServ50':
                        val_ret50 = str(h.get(t).get(tag))
                    elif tag == 'valorRetServicios':
                        val_retser = str(h.get(t).get(tag))
                    elif tag == 'valRetServ100':
                        val_rets100 = str(h.get(t).get(tag))
                    elif tag == 'docModificado':
                        doc_mod = str(h.get(t).get(tag))
                    elif tag == 'ptoEmiModificado':
                        pto_emi_mod = str(h.get(t).get(tag))
                    elif tag == 'secModificado':
                        sec_mod = str(h.get(t).get(tag))
                    elif tag == 'autModificado':
                        aut_mod = str(h.get(t).get(tag))
                    elif tag == 'estabRetencion1':
                        est_ret1 = str(h.get(t).get(tag))
                    elif tag == 'ptoEmiRetencion1':
                        pto_emi_ret = str(h.get(t).get(tag))
                    elif tag == 'secRetencion1':
                        print "sec", str(h.get(t).get(tag))
                        sec_ret1 = str(h.get(t).get(tag))
                    elif tag == 'autRetencion1':
                        aut_ret1 = str(h.get(t).get(tag))
                    elif tag == 'fechaEmiRet1':
                        fech_emiret = str(h.get(t).get(tag))
##ARMO ESTRUCTURA COMPRAS*******************
                cod_sustento = doc.createElement("codSustento")
                detalle_compras_form.appendChild(cod_sustento)
                pcod_sustento = doc.createTextNode(cod_sus)
                cod_sustento.appendChild(pcod_sustento)
                 
                 
                cod_tipo_prov = doc.createElement("tpIdProv")
                detalle_compras_form.appendChild(cod_tipo_prov)
                pcod_tipo_prov = doc.createTextNode(tip_pro)
                cod_tipo_prov.appendChild(pcod_tipo_prov)
                 
                cod_id_prov = doc.createElement("idProv")
                detalle_compras_form.appendChild(cod_id_prov)
                pcod_id_prov = doc.createTextNode(str(id_prov))
                cod_id_prov.appendChild(pcod_id_prov)
                #print "pcod_id_prov", pcod_id_prov
                 
                 
                tipoComprobante_c = doc.createElement("tipoComprobante")
                detalle_compras_form.appendChild(tipoComprobante_c)
                t_comprobante = str(tip_comp)
                ptipoComprobante_c = doc.createTextNode(t_comprobante)
                tipoComprobante_c.appendChild(ptipoComprobante_c)
                #print "ptipoComprobante_c", ptipoComprobante_c
                 
                if (t_comprobante == '15'):
                    tipo_prov = doc.createElement("tipoProv")
                    detalle_compras_form.appendChild(tipo_prov)
                    p_tipo_prov = doc.createTextNode('02')
                    tipo_prov.appendChild(p_tipo_prov)
                 
                    parte_rel = doc.createElement("parteRel")
                    detalle_compras_form.appendChild(parte_rel)
                    p_parte_rel = doc.createTextNode('NO')
                    parte_rel.appendChild(p_parte_rel)
                
                fecha_reg = doc.createElement("fechaRegistro")
                detalle_compras_form.appendChild(fecha_reg)
                pfecha_reg = doc.createTextNode(str(fec_reg))
                fecha_reg.appendChild(pfecha_reg)
                 
                establec = doc.createElement("establecimiento")
                detalle_compras_form.appendChild(establec)
                pestablec = doc.createTextNode(estab)
                establec.appendChild(pestablec)
                 
                emision = doc.createElement("puntoEmision")
                detalle_compras_form.appendChild(emision)
                pemision = doc.createTextNode(punt_emi)
                emision.appendChild(pemision)
                 
                secuencial = doc.createElement("secuencial")
                detalle_compras_form.appendChild(secuencial)
                psecuencial = doc.createTextNode(str(sec))
                #print "SECUENCIAL", sec
                secuencial.appendChild(psecuencial)
                 
                fecha_emi = doc.createElement("fechaEmision")
                detalle_compras_form.appendChild(fecha_emi)
                pfecha_emi = doc.createTextNode(str(fech_emi))
                fecha_emi.appendChild(pfecha_emi)
                 
                autorizacion = doc.createElement("autorizacion")
                detalle_compras_form.appendChild(autorizacion)
                pautorizacion = doc.createTextNode(aut)
                #print "AUTORIZACION", aut
                autorizacion.appendChild(pautorizacion)
                 
                baseNoGraIva = doc.createElement("baseNoGraIva")
                detalle_compras_form.appendChild(baseNoGraIva)
                base_no_gravada = Decimal(bas_ngi).quantize(Decimal('0.00'))
                pbaseNoGraIva = doc.createTextNode(str(base_no_gravada))
                baseNoGraIva.appendChild(pbaseNoGraIva)
                 
                baseImponible = doc.createElement("baseImponible")
                detalle_compras_form.appendChild(baseImponible)
                f_base_no_gravada = Decimal(bas_imp_gra).quantize(Decimal('0.00'))
                pbaseImponible = doc.createTextNode(str(f_base_no_gravada))
                baseImponible.appendChild(pbaseImponible)
                 
                baseImpGrav = doc.createElement("baseImpGrav")
                detalle_compras_form.appendChild(baseImpGrav)
                f_base_imponible_grava = Decimal(bas_imp).quantize(Decimal('0.00'))
                pbaseImpGrav = doc.createTextNode(str(f_base_imponible_grava))
                baseImpGrav.appendChild(pbaseImpGrav)
                 
                baseImpExe = doc.createElement("baseImpExe")
                detalle_compras_form.appendChild(baseImpExe)
                pbaseImpExe = doc.createTextNode(str(bas_imp_exe))
                baseImpExe.appendChild(pbaseImpExe)
 
                montoIce = doc.createElement("montoIce")
                detalle_compras_form.appendChild(montoIce)
                pmontoIce = doc.createTextNode(str(mont_ice))
                montoIce.appendChild(pmontoIce)
                
                montoIva = doc.createElement("montoIva")
                detalle_compras_form.appendChild(montoIva)
                f_monto_iva = Decimal(mont_iva).quantize(Decimal('0.00'))
                pmontoIva = doc.createTextNode(str(f_monto_iva))
                #print "montoIva", pmontoIva
                montoIva.appendChild(pmontoIva)
                 
                valRetBien10 = doc.createElement("valRetBien10")
                detalle_compras_form.appendChild(valRetBien10)
                f_valRetBien10 = Decimal(val_ret10).quantize(Decimal('0.00'))
                pvalRetBien10 = doc.createTextNode(str(f_valRetBien10))
                valRetBien10.appendChild(pvalRetBien10)
                 
                valRetServ20 = doc.createElement("valRetServ20")
                detalle_compras_form.appendChild(valRetServ20)
                f_valRetServ20 = Decimal(val_ret20).quantize(Decimal('0.00'))
                pvalRetServ20 = doc.createTextNode(str(f_valRetServ20))
                valRetServ20.appendChild(pvalRetServ20)
                 
                valorRetBienes = doc.createElement("valorRetBienes")
                detalle_compras_form.appendChild(valorRetBienes)
                f_valor_retencion_bienes = Decimal(val_retbie).quantize(Decimal('0.00'))
                pvalorRetBienes = doc.createTextNode(str(f_valor_retencion_bienes))
                valorRetBienes.appendChild(pvalorRetBienes)

                valRetServ50 = doc.createElement("valRetServ50")
                detalle_compras_form.appendChild(valRetServ50)
                f_valRetServ50 = Decimal(val_ret50).quantize(Decimal('0.00'))
                pvalRetServ50 = doc.createTextNode(str(f_valRetServ50))
                valRetServ50.appendChild(pvalRetServ50)

                valorRetServicios = doc.createElement("valorRetServicios")
                detalle_compras_form.appendChild(valorRetServicios)
                f_valor_retencion_servicios = Decimal(val_retser).quantize(Decimal('0.00'))
                pvalorRetServicios = doc.createTextNode(str(f_valor_retencion_servicios))
                valorRetServicios.appendChild(pvalorRetServicios)
                 
                valRetServ100 = doc.createElement("valRetServ100")
                detalle_compras_form.appendChild(valRetServ100)
                f_valor_retencion_servicios_100 = Decimal(val_rets100).quantize(Decimal('0.00'))
                pvalRetServ100 = doc.createTextNode(str(f_valor_retencion_servicios_100))
                valRetServ100.appendChild(pvalRetServ100)
                tot_bas_reem = 0.00
                if (t_comprobante == '41'):
                    #print "ID FACTURA", idfac
                    invdet_idr = self.pool.get('account.invoice.line').search(cr, uid, [('invoice_id', '=', idfac)])
                    #print "LISTA DETALLE DE LA FACTURA", invdet_idr 
                    invdet_detr = self.pool.get('account.invoice.line').browse(cr, uid, invdet_idr)
                    #print "OBJETO LINE DETALLADO", invdet_detr
                    for lin_reem in invdet_detr:
                        tot_bas_reem += lin_reem.price_subtotal + lin_reem.base_ngi
                else:
                    tot_bas_reem = 0.00
 
                totbasesImpReemb = doc.createElement("totbasesImpReemb")
                detalle_compras_form.appendChild(totbasesImpReemb)
                f_valor_totbasesImpReemb = Decimal(tot_bas_reem).quantize(Decimal('0.00'))
                ptotbasesImpReemb = doc.createTextNode(str(f_valor_totbasesImpReemb))
                totbasesImpReemb.appendChild(ptotbasesImpReemb)                
# #CVS pago exterior                
                detalle_exter_form = doc.createElement("pagoExterior")
                detalle_compras_form.appendChild(detalle_exter_form)
                if (t_comprobante == '15'):                   
                    pago_exter = doc.createElement("pagoLocExt")
                    detalle_exter_form.appendChild(pago_exter)
                    ppago_exter = doc.createTextNode("02")
                    pago_exter.appendChild(ppago_exter)
     
                    pais_efec = doc.createElement("paisEfecPago")
                    detalle_exter_form.appendChild(pais_efec)
                    ppais_efec = doc.createTextNode("110")
                    pais_efec.appendChild(ppais_efec)
                     
                    pago_trib = doc.createElement("aplicConvDobTrib")
                    detalle_exter_form.appendChild(pago_trib)
                    ppago_trib = doc.createTextNode("NO")
                    pago_trib.appendChild(ppago_trib) 
                       
                    pago_leg = doc.createElement("pagExtSujRetNorLeg")
                    detalle_exter_form.appendChild(pago_leg)
                    ppago_leg = doc.createTextNode("NO")
                    pago_leg.appendChild(ppago_leg)
                     
                    pagoRegFis = doc.createElement("pagoRegFis")
                    detalle_exter_form.appendChild(pagoRegFis)
                    ppagoRegFis = doc.createTextNode("NO")
                    pagoRegFis.appendChild(ppagoRegFis)
                else:
                    pago_exter = doc.createElement("pagoLocExt")
                    detalle_exter_form.appendChild(pago_exter)
                    ppago_exter = doc.createTextNode("01")
                    pago_exter.appendChild(ppago_exter)
     
                    pais_efec = doc.createElement("paisEfecPago")
                    detalle_exter_form.appendChild(pais_efec)
                    ppais_efec = doc.createTextNode("NA")
                    pais_efec.appendChild(ppais_efec)
                     
                    pago_trib = doc.createElement("aplicConvDobTrib")
                    detalle_exter_form.appendChild(pago_trib)
                    ppago_trib = doc.createTextNode("NA")
                    pago_trib.appendChild(ppago_trib) 
                       
                    pago_leg = doc.createElement("pagExtSujRetNorLeg")
                    detalle_exter_form.appendChild(pago_leg)
                    ppago_leg = doc.createTextNode("NA")
                    pago_leg.appendChild(ppago_leg)
 
                    pagoRegFis = doc.createElement("pagoRegFis")
                    detalle_exter_form.appendChild(pagoRegFis)
                    ppagoRegFis = doc.createTextNode("NA")
                    pagoRegFis.appendChild(ppagoRegFis)
                                         
# #CSV Formas de pago
                if ((f_base_no_gravada >= 1000.00) or (f_base_imponible_grava >= 1000.00) or (base_no_gravada>= 1000.00) or (f_base_no_gravada + f_monto_iva >= 1000.00) or (base_no_gravada + f_monto_iva >= 1000.00) or (f_base_imponible_grava + f_monto_iva >= 1000.00) or (f_base_imponible_grava + f_base_no_gravada >= 1000.00) or (f_base_imponible_grava + f_base_no_gravada + f_monto_iva >= 1000.00) or (base_no_gravada + f_base_imponible_grava + f_base_no_gravada + f_monto_iva >= 1000.00)) :
                    detalle_fpago_form = doc.createElement("formasDePago")
                    detalle_compras_form.appendChild(detalle_fpago_form)
                       
                    f_fpago = doc.createElement("formaPago")
                    detalle_fpago_form.appendChild(f_fpago)
                    pf_fpago = doc.createTextNode("02")
                    f_fpago.appendChild(pf_fpago)
# #CSV Detalle Nota de Credito
                if (t_comprobante == '04'): 
                    docModificado = doc.createElement("docModificado")
                    detalle_compras_form.appendChild(docModificado)
                    pdocModificado = doc.createTextNode(str(detalle_compras.documento_modificado))
                    docModificado.appendChild(pdocModificado)
                      
                    estabModificado = doc.createElement("estabModificado")
                    detalle_compras_form.appendChild(estabModificado)
                    pestabModificado = doc.createTextNode(str(doc_mod))
                    estabModificado.appendChild(pestabModificado)
                      
                    ptoEmiModificado = doc.createElement("ptoEmiModificado")
                    detalle_compras_form.appendChild(ptoEmiModificado)
                    pptoEmiModificado = doc.createTextNode(str(pto_emi_mod))
                    ptoEmiModificado.appendChild(pptoEmiModificado)
                     
                    secModificado = doc.createElement("secModificado")
                    detalle_compras_form.appendChild(secModificado)
                    psecModificado = doc.createTextNode(str(sec_mod))
                    secModificado.appendChild(psecModificado)
                      
                      
                    autModificado = doc.createElement("autModificado")
                    detalle_compras_form.appendChild(autModificado)
                    pautModificadoo = doc.createTextNode(str(aut_mod))
                    autModificado.appendChild(pautModificadoo)
# #CSV Detalle retenciones
                if ((t_comprobante != '04') and (t_comprobante != '15')) :
                    air_form = doc.createElement("air")
                    detalle_compras_form.appendChild(air_form)
                    #print "ID FACTURA**", idfac
                    retenciones_idr = self.pool.get('account.invoice.tax').search(cr, uid, [('invoice_id', '=', idfac), ('deduction_id', '!=', None)])
                    #print "LISTA IDS RETEN", retenciones_idr 
                    detalle_retenciones = self.pool.get('account.invoice.tax').browse(cr, uid, retenciones_idr)
                    #print "OBJETO RETEN DETALLADO", detalle_retenciones
                    base_retencion = 0.00
                    val_reten = 0.00
                    codigo_ret = ''
                    val_por = 0.00
                    val_base = 0.00
                    band = 0
                    porcentaje_ret = 0.00
                    cont = 0
                    res = []
                    lis = []
                    for detalle_retencion in detalle_retenciones:
                        codigo_ret = detalle_retencion.base_code_id.code
                        #print "CODIGO**", detalle_retencion.base_code_id.code
                        if codigo_ret == '332':
                            val_por = 0.0
                            val_base = abs(detalle_retencion.base_amount) or 0.00
                            val_reten = abs(detalle_retencion.tax_amount) or 0.00
                        elif codigo_ret in ('721', '723', '725', '727', '729', '731'):
                            continue
                        elif codigo_ret == '3440':
                            val_por = 2.75
                            val_base = abs(detalle_retencion.base_amount) or 0.00
                            val_reten = abs(detalle_retencion.tax_amount) or 0.00
                        elif codigo_ret == '312':
                            val_por = 1.75
                            val_base = abs(detalle_retencion.base_amount) or 0.00
                            val_reten = abs(detalle_retencion.tax_amount) or 0.00
                        elif codigo_ret == '310':
                            val_por = 1.0
                            val_base = abs(detalle_retencion.base_amount) or 0.00
                            val_reten = abs(detalle_retencion.tax_amount) or 0.00
                        elif codigo_ret == '304':
                            val_por = 8.0
                            val_base = abs(detalle_retencion.base_amount) or 0.00
                            val_reten = abs(detalle_retencion.tax_amount) or 0.00
                        elif codigo_ret == '322':
                            val_por = 1.75
                            val_base = abs(detalle_retencion.base_amount/10) or 0.00
                            val_reten = abs(detalle_retencion.tax_amount) or 0.00
                        elif codigo_ret == '307':
                            val_por = 2.0
                            val_base = abs(detalle_retencion.base_amount) or 0.00
                            val_reten = abs(detalle_retencion.tax_amount) or 0.00
                        elif codigo_ret == '303':
                            val_por = 10.0
                            val_base = abs(detalle_retencion.base_amount) or 0.00
                            val_reten = abs(detalle_retencion.tax_amount) or 0.00
                        elif codigo_ret == '308':
                            val_por = 10.0
                            val_base = abs(detalle_retencion.base_amount) or 0.00
                            val_reten = abs(detalle_retencion.tax_amount) or 0.00
                        elif codigo_ret == '320':
                            val_por = 8.0
                            val_base = abs(detalle_retencion.base_amount) or 0.00
                            val_reten = abs(detalle_retencion.tax_amount) or 0.00
                        else:
                            val_por = 0.00
                            val_base = abs(detalle_retencion.base_amount) or 0.00
                            val_reten = abs(detalle_retencion.tax_amount) or 0.00
                        
                        if cont == 0:
                            lis.append(codigo_ret)
                            #print "PRIMER ELEMENTO LISTA REGISTRO", lis
                            val1 = {'codigo_ret': codigo_ret,
                                 'val_base': val_base,
                                 'val_por': val_por,
                                 'val_reten': val_reten,
                                 }
                            res.append(val1)
                            cont = 1
                        elif cont == 1:
                            band = 0
                            for recorre in lis:
                                #print "RECORRE RC", str(recorre) +" "+"CODE"+" "+str(codigo_ret)
            #                     print "move.account_id.code: ", move.account_id.code
                                if recorre == codigo_ret:
                                    for rec_old in res:
                                        #print "ACTUALIZO EL REGISTRO", rec_old
                                        if rec_old.get('codigo_ret') == codigo_ret:
                                            #print "actualizo"
                                            val_base_ant = rec_old.get('val_base')
                                            val_reten_ant = rec_old.get('val_reten')
                                            val_base_new = float(val_base_ant) + float(val_base)
                                            val_reten_new = float(val_reten_ant) + float(val_reten)
                                            rec_old['val_base'] = val_base_new
                                            rec_old['val_reten'] = val_reten_new
                                        else:
                                            continue
                                    band = 1
                            if band != 1:
                                val1 = {'codigo_ret': codigo_ret,
                                     'val_base': val_base,
                                     'val_por': val_por,
                                     'val_reten': val_reten,
                                     }
                                res.append(val1)                                
                        #print "LISTA FINAL IMP", lis
                        
                    for detalle_ret in res:
                        detalleAir_form = doc.createElement("detalleAir")
                        air_form.appendChild(detalleAir_form)
                        
                        codigoRet = doc.createElement("codRetAir")
                        detalleAir_form.appendChild(codigoRet)
                        pcodigoRet = doc.createTextNode(str(detalle_ret.get('codigo_ret')))
                        codigoRet.appendChild(pcodigoRet)
                          
                        baseImp = doc.createElement("baseImpAir")
                        detalleAir_form.appendChild(baseImp)
                        f_baseImpAir = Decimal(detalle_ret.get('val_base')).quantize(Decimal('0.00'))
                        pbaseImp = doc.createTextNode(str(f_baseImpAir))
                        baseImp.appendChild(pbaseImp)
                          
                        porcentajeRet = doc.createElement("porcentajeAir")
                        detalleAir_form.appendChild(porcentajeRet)
                        f_porcentajeAir = Decimal(detalle_ret.get('val_por')).quantize(Decimal('0.00'))
                        pporcentajeRet = doc.createTextNode(str(f_porcentajeAir))
                        porcentajeRet.appendChild(pporcentajeRet)
                          
                        valorRet = doc.createElement("valRetAir")
                        detalleAir_form.appendChild(valorRet)
                        f_valRetAir = Decimal(detalle_ret.get('val_reten')).quantize(Decimal('0.00'))                    
                        pvalorRet = doc.createTextNode(str(f_valRetAir))
                        valorRet.appendChild(pvalorRet)
                
            
                if sec_ret1 != '0':                 
                    estabRetencion1 = doc.createElement("estabRetencion1")
                    detalle_compras_form.appendChild(estabRetencion1)
                    pestabRetencion1 = doc.createTextNode(str(est_ret1))
                    estabRetencion1.appendChild(pestabRetencion1)
                     
                    ptoEmiRetencion1 = doc.createElement("ptoEmiRetencion1")
                    detalle_compras_form.appendChild(ptoEmiRetencion1)
                    pptoEmiRetencion1 = doc.createTextNode(str(pto_emi_ret))
                    ptoEmiRetencion1.appendChild(pptoEmiRetencion1)
                     
                    secRetencion1 = doc.createElement("secRetencion1")
                    detalle_compras_form.appendChild(secRetencion1)
                    sec_ret_rep = sec_ret1.replace('R-UIO','').replace('R-GYE','').replace('R-CUE','')
                    psecRetencion1 = doc.createTextNode(str(sec_ret_rep))
                    secRetencion1.appendChild(psecRetencion1)
                     
                    autRetencion1 = doc.createElement("autRetencion1")
                    detalle_compras_form.appendChild(autRetencion1)
                    pautRetencion1 = doc.createTextNode(str(aut_ret1))
                    autRetencion1.appendChild(pautRetencion1)
                     
                    fechaEmiRet1 = doc.createElement("fechaEmiRet1")
                    detalle_compras_form.appendChild(fechaEmiRet1)
                    if not fech_emiret:
                        fch_emi_ret = '00/00/0000'
                    else:
                        fch_emi_ret = str(fech_emiret)
                    #print "fch_emi_ret: ", fch_emi_ret    
                    pfechaEmiRet1 = doc.createTextNode(fch_emi_ret)    
                    fechaEmiRet1.appendChild(pfechaEmiRet1)

#******FIN ESTRUCTURA COMPRAS***************
        
        
        ventas_form = doc.createElement("ventas")
        mainform.appendChild(ventas_form)
        #print "*OJO VENTAS****2222*******", brw_codes.get('ventas')

        for h in brw_codes.get('ventas'):
            #print '- - 77', h
            k_list = h.keys()
            for t in k_list:
                #print '- VENTAS - 80', t
                detalle_ventas_form = doc.createElement("detalleVentas")
                ventas_form.appendChild(detalle_ventas_form)
                tpIdC = ''
                idCli = ''
                fpago = ''
                partr = ''
                tipoComp = ''
                numComp = ''
                baseNGI = ''
                basImp = ''
                basImpGr = ''
                monIva = ''
                valRetIva = ''
                valRetRent = ''
                for tag in h.get(t).keys():
                    if tag == 'tpIdCliente':
                        tpIdC = str(h.get(t).get(tag))
                        #print "tpIdCliente", tpIdC
                    elif tag == 'idCliente':
                        idCli = str(h.get(t).get(tag))
                        #print "idCliente", idCli
                    elif tag == 'formaPago':
                        fpago = str(h.get(t).get(tag))
                    elif tag == 'parteRel':
                        partr = str(h.get(t).get(tag))
                        #print "parteRel", partr
                    elif tag == 'tipoComprobante':
                        tipoComp = str(h.get(t).get(tag))
                        #print "tipoComprobante", tipoComp
                    elif tag == 'numeroComprobantes':
                        numComp = str(h.get(t).get(tag))
                        #print "numeroComprobantes", numComp
                    elif tag == 'baseNoGraIva':
                        baseNGI = str(h.get(t).get(tag))
                        #print "baseNoGraIva", baseNGI
                    elif tag == 'baseImponible':
                        basImp = str(h.get(t).get(tag))
                        #print "baseImponible", basImp
                    elif tag == 'baseImpGrav':
                        basImpGr = str(h.get(t).get(tag))
                        #print "baseImpGrav", basImpGr
                    elif tag == 'montoIva':
                        monIva = str(h.get(t).get(tag))
                        #print "montoIva", monIva
                    elif tag == 'montoIce':
                        monIce = str(h.get(t).get(tag))
                        #print "montoIce", monIce
                    elif tag == 'valorRetIva':
                        valRetIva = str(h.get(t).get(tag))
                        #print "valorRetIva", valRetIva
                    elif tag == 'valorRetRenta':
                        valRetRent = str(h.get(t).get(tag))
                        #print "valorRetRenta", valRetRent                        
                        
                    
                tpIdCliente = doc.createElement("tpIdCliente")
                detalle_ventas_form.appendChild(tpIdCliente)
                ptpIdCliente = doc.createTextNode(tpIdC)
                tpIdCliente.appendChild(ptpIdCliente)
                
                idCliente = doc.createElement("idCliente")
                detalle_ventas_form.appendChild(idCliente)
                pidCliente = doc.createTextNode(idCli)
                idCliente.appendChild(pidCliente)
                
                if tpIdC != '07':
                    parteRelVtas = doc.createElement("parteRelVtas")
                    detalle_ventas_form.appendChild(parteRelVtas)
                    pparteRelVtas = doc.createTextNode(partr)
                    parteRelVtas.appendChild(pparteRelVtas)
                
                tipoComprobante = doc.createElement("tipoComprobante")
                detalle_ventas_form.appendChild(tipoComprobante)
                ptipoComprobante = doc.createTextNode(tipoComp)
                tipoComprobante.appendChild(ptipoComprobante)

                tipoEmision = doc.createElement("tipoEmision")
                detalle_ventas_form.appendChild(tipoEmision)
                ptipoEmision = doc.createTextNode("F")
                tipoEmision.appendChild(ptipoEmision)
                
                numeroComprobantes = doc.createElement("numeroComprobantes")
                detalle_ventas_form.appendChild(numeroComprobantes)
                pnumeroComprobantes = doc.createTextNode(str(numComp))
                numeroComprobantes.appendChild(pnumeroComprobantes)
                
                baseNoGraIva = doc.createElement("baseNoGraIva")
                detalle_ventas_form.appendChild(baseNoGraIva)
                pbaseNoGraIva = doc.createTextNode(str(baseNGI))
                baseNoGraIva.appendChild(pbaseNoGraIva)
                
                baseImponible = doc.createElement("baseImponible")
                detalle_ventas_form.appendChild(baseImponible)
                v_baseImponible = Decimal(basImpGr).quantize(Decimal('0.00'))
                pbaseImponible = doc.createTextNode(str(v_baseImponible))
                baseImponible.appendChild(pbaseImponible)

                baseImpGrav = doc.createElement("baseImpGrav")
                detalle_ventas_form.appendChild(baseImpGrav)
                v_baseImpGrav = Decimal(basImp).quantize(Decimal('0.00'))
                pbaseImpGrav = doc.createTextNode(str(v_baseImpGrav))
                baseImpGrav.appendChild(pbaseImpGrav)
                
                montoIva = doc.createElement("montoIva")
                detalle_ventas_form.appendChild(montoIva)
                v_montoIva = Decimal(monIva).quantize(Decimal('0.00'))
                pmontoIva = doc.createTextNode(str(v_montoIva))
                montoIva.appendChild(pmontoIva)
                
                montoIcev = doc.createElement("montoIce")
                detalle_ventas_form.appendChild(montoIcev)
                pmontoIcev = doc.createTextNode(str(monIce))
                montoIcev.appendChild(pmontoIcev)
                
                valorRetIva = doc.createElement("valorRetIva")
                detalle_ventas_form.appendChild(valorRetIva)
                v_valorRetIva = Decimal(valRetIva).quantize(Decimal('0.00'))
                pvalorRetIva = doc.createTextNode(str(v_valorRetIva))
                valorRetIva.appendChild(pvalorRetIva)
                
                valorRetRenta = doc.createElement("valorRetRenta")
                detalle_ventas_form.appendChild(valorRetRenta)
                v_valorRetRenta = Decimal(valRetRent).quantize(Decimal('0.00'))
                pvalorRetRenta = doc.createTextNode(str(v_valorRetRenta))
                valorRetRenta.appendChild(pvalorRetRenta)
                #CSV-17-10-2016 AUMENTO FORMAS DE PAGO
                pago = doc.createElement("formasDePago")
                detalle_ventas_form.appendChild(pago)
                formaPago = doc.createElement("formaPago")
                pago.appendChild(formaPago)
                nformaPago = doc.createTextNode(str(fpago))
                formaPago.appendChild(nformaPago)
        
        detalle_venest_form = doc.createElement("ventasEstablecimiento")
        mainform.appendChild(detalle_venest_form)

        f_venest_form = doc.createElement("ventaEst")
        detalle_venest_form.appendChild(f_venest_form)

        coEstab = doc.createElement("codEstab")
        f_venest_form.appendChild(coEstab)
        pcoEstab = doc.createTextNode("001")
        coEstab.appendChild(pcoEstab)
        
        ventEstab = doc.createElement("ventasEstab")
        f_venest_form.appendChild(ventEstab)
        pventEstab = doc.createTextNode(str(totvent))
        ventEstab.appendChild(pventEstab)
        
        anulados_form = doc.createElement("anulados")
        mainform.appendChild(anulados_form)
        #print "*OJO ANULADOS****2222*******", brw_codes.get('anulados')
        for h in brw_codes.get('anulados'):
            #print '- - 77', h
            k_list = h.keys()
            for t in k_list:
                #print '- - - 80', t
                detalle_anuladas_form = doc.createElement("detalleAnulados")
                anulados_form.appendChild(detalle_anuladas_form)
                tipCom = ''
                Estab = ''
                puntEmi = ''
                secIni = ''
                secFin = ''
                auto = ''
                for tag in h.get(t).keys():
                    if tag == 'puntoEmision':
                        puntEmi = str(h.get(t).get(tag))
                        #print "puntoEmision", puntEmi
                    elif tag == 'tipoComprobante':
                        tipCom = str(h.get(t).get(tag))
                        #print "tipoComprobante", tipCom
                    elif tag == 'Establecimiento':
                        Estab = str(h.get(t).get(tag))
                        #print "Establecimiento", Estab
                    elif tag == 'secuencialInicio':
                        secIni = str(h.get(t).get(tag))
                        #print "secuencialInicio", secIni
                    elif tag == 'secuencialFin':
                        secFin = str(h.get(t).get(tag))
                        #print "secuencialFin", secFin
                    elif tag == 'autorizacion':
                        auto = str(h.get(t).get(tag))
                        #print "autorizacion", auto
                    
                tipoComprobante = doc.createElement("tipoComprobante")
                detalle_anuladas_form.appendChild(tipoComprobante)
                ptipoComprobante = doc.createTextNode(tipCom)
                tipoComprobante.appendChild(ptipoComprobante)

                establecimiento = doc.createElement("establecimiento")
                detalle_anuladas_form.appendChild(establecimiento)
                pestablecimiento = doc.createTextNode(Estab)
                establecimiento.appendChild(pestablecimiento)
                
                puntoEmision = doc.createElement("puntoEmision")
                detalle_anuladas_form.appendChild(puntoEmision)
                ppuntoEmision = doc.createTextNode(puntEmi)
                puntoEmision.appendChild(ppuntoEmision)
                
                secuencialInicio = doc.createElement("secuencialInicio")
                detalle_anuladas_form.appendChild(secuencialInicio)
                psecuencialInicio = doc.createTextNode(secIni)
                secuencialInicio.appendChild(psecuencialInicio)
                
                
                secuencialFin = doc.createElement("secuencialFin")
                detalle_anuladas_form.appendChild(secuencialFin)
                psecuencialFin = doc.createTextNode(secFin)
                secuencialFin.appendChild(psecuencialFin)
                
                autorizacion = doc.createElement("autorizacion")
                detalle_anuladas_form.appendChild(autorizacion)
                pautorizacion = doc.createTextNode(auto)
                autorizacion.appendChild(pautorizacion)
                    
        res = doc.toxml()

        #print "RES**", res
        #res = etree.tostring(out, pretty_print=True)
    else:
        formulario = etree.Element("formulario", version="0.2")
        formulario.append( getHeader(header) ) # Agregando el nodo de cabecera
        detalle = etree.SubElement(formulario, 'detalle')
        
        for h in head_static.keys():
            campo = etree.SubElement(detalle, 'campo', numero=h)
            campo.text = str(head_static.get(h))
            
        for tax in brw_codes:
            campo = False
            campo = etree.SubElement(detalle, 'campo', numero=tax.get('code'))
            campo.text = str(abs(tax.get('sum_period')))
        res = etree.tostring(formulario, pretty_print=True)
        
    return res
    
def grabarXML(brw_codes, header, head_static, is_ats, doc='Unknow', url='/opt/temp/'): # Guardar la información en el fichero
    archi=open(str(url) + str(doc) + '.xml','w')
  # Escribo en el XML
    archi.write('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n')
    res = formarXML(brw_codes, header, head_static, is_ats) # Me devuelve el formato XML-104 para salvar
    archi.write(res)
  # Cierro el fichero
    archi.close()
    
def grabarXMLATS(self, cr, uid, brw_codes, header, head_static, is_ats, doc='Unknow', url='/opt/temp/'): # Guardar la información en el fichero
    archi=open(str(url) + str(doc) + '.xml','w')
  # Escribo en el XML
    #archi.write('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n')
    res = formarXMLATS(self, cr, uid, brw_codes, header, head_static, is_ats) # Me devuelve el formato XML-104 para salvar
    archi.write(res)
  # Cierro el fichero
    archi.close()

def getNodes(tags_ats): # Lógica para formar el XML que devolveré
    list_nodes = []
    #print '71', type(tags_ats)
    if not isinstance(tags_ats, dict):
        tags_ats = dict(tags_ats)
        #print '72', type(tags_ats), 'a', tags_ats
    for k in tags_ats.keys():
        #print '- 74'
        nodo = etree.Element(k)
        for h in tags_ats.get(k):
            #print '- - 77'
            k_list = h.keys()
            for t in k_list:
                #print '- - - 80'
                detalle = etree.SubElement(nodo, 'detalle' + str(k).capitalize())
                for tag in h.get(t).keys():
                    #print ' - - - - 83'
                    campo = etree.SubElement(detalle, str(tag))
                    campo.text = str(h.get(t).get(tag))
        list_nodes.append(nodo)
    #print 'listado de nodos', list_nodes
    return list_nodes
