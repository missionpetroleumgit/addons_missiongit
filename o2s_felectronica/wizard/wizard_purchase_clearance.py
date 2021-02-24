# -*- coding: utf-8 -*-
import unicodedata
from openerp import models, fields, api
from openerp.exceptions import except_orm, Warning
import base64
import time
from decimal import *
from xml.dom.minidom import Document
from suds.client import Client
from XadesBes import jarWrapper
import os, ssl


class wizard_purchase_clearance(models.TransientModel):
    _name = 'wizard.purchase.clearance'

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
    def generate_liquidation_file(self):
        # DECLARO VARIABLES Y DOC PARA FORMAR EL XML
        mensaje = ""
        doc = Document()
        doc1 = Document()
        cod_num = '12345678'
        serie = '001001'
        ids = self._context['active_ids']
        for record in self:
            id_m = record.id
            id_ambiente = record.ambiente
            if id_ambiente == 'pruebas':
                if (not os.environ.get('PYTHONHTTPSVERIFY', '') and 
                getattr(ssl, '_create_unverified_context', None)):
                    ssl._create_default_https_context = ssl._create_unverified_context

                ambiente = '1'
                url = 'https://celcer.sri.gob.ec/comprobantes-electronicos-ws/RecepcionComprobantesOffline?wsdl'
                url1 = 'https://celcer.sri.gob.ec/comprobantes-electronicos-ws/AutorizacionComprobantesOffline?wsdl'
                if url:
                    client = Client(url, timeout=10)
                else:
                    raise Warning(('Atencion !'), ('No responde SRI intente mas tarde !'))
                if url1:
                    client1 = Client(url1, timeout=10)
                else:
                    raise Warning(('Atencion !'), ('No responde SRI intente mas tarde !'))

            elif id_ambiente == 'produccion':
                if (not os.environ.get('PYTHONHTTPSVERIFY', '') and 
                getattr(ssl, '_create_unverified_context', None)):
                    ssl._create_default_https_context = ssl._create_unverified_context

                ambiente = '2'
                url = 'https://cel.sri.gob.ec/comprobantes-electronicos-ws/RecepcionComprobantesOffline?wsdl'
                url1 = 'https://cel.sri.gob.ec/comprobantes-electronicos-ws/AutorizacionComprobantesOffline?wsdl'
                client = Client(url, timeout=10)
                client1 = Client(url1, timeout=10)
                if client and client1:
                    print 'OK'
                else:
                    raise Warning(('Atencion !'), ('No responde SRI intente mas tarde!'))
        if self._uid:
            arcfd = self.env.user.company_id
            firmadig = arcfd.name
            if firmadig:
                print "FIRMA DIGITAL", firmadig
            else:
                raise Warning('Atencion !, Suba el archivo de Firma Digital en su Usuario!')

        id_formulario = record.formulario
        if id_formulario == 'normal':
            temision = '1'
        elif id_formulario == 'contingencia':
            temision = '2'
        # OBTENER DATOS DE LA FACTURA
        id_header = self._context['active_id']
        for factura in self.env['account.invoice'].browse(ids):
            doc = Document()
            doc1 = Document()
            res_sri = False
            vals_accinvws1 = {}
            t_comp = factura.type
            if factura.state_factelectro == 'autorizado' or factura.type not in ('in_invoice'):
                continue
            if factura.state_factelectro not in ('autorizado', 'firmado') and factura.document_type.code == '03':
                # Liquidacion de compras
                auth = self.env['account.authorization'].browse([factura.authorization_id.id])
                secuencia = factura.number_seq
                fechasf = factura.date_emision
                lfecha = fechasf.split('-')
                fecha = lfecha[2] + "/" + lfecha[1] + "/" + lfecha[0]
                fechasfe = factura.date_invoice
                lfechae = fechasfe.split('-')
                fechafact = lfechae[2] + "/" + lfechae[1] + "/" + lfechae[0]
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
                    raise Warning(('Atencion !'), ('Ingrese el Email del cliente en la ficha !'))
                if dfactu and dfactu2:
                    dfactuf = str(dfactu) + " " + str(dfactu2)
                elif dfactu and not dfactu2:
                    dfactuf = str(dfactu)
                elif dfactu2 and not dfactu:
                    dfactuf = str(dfactu2)
                else:
                    dfactuf = ''
                t_comp = factura.type
                cod_ident = factura.partner_id.cod_type_ident
                name_rzc = factura.partner_id.name
                id_rzc = factura.partner_id.part_number
                tot_simp = factura.amount_untaxed
                invdet_des = self.env['account.invoice.line'].search([('invoice_id', '=', factura.id)])
                descuentt = 0
                for det_fact in invdet_des:
                    id_line = det_fact.id
                    if det_fact.discount > 0:
                        descuentt += round(((det_fact.price_unit * det_fact.quantity) * det_fact.discount) / 100, 2)
                    else:
                        descuentt = det_fact.discount
                tot_desc = descuentt
                # DIRECCION SUCURSAL EMITE COMPROBANTE
                id_pars = self.env['res.partner'].search([('ref', '=', 'COEBIT'),
                                                          ('company_id', '=', self.env.user.company_id.id)])
                id_pars_add = self.env['res.partner'].search([('id', '=', id_pars.id)])

                if id_pars_add:
                    d_suc1 = id_pars_add.street
                    d_suc2 = id_pars_add.street2
                    if d_suc1 and d_suc2:
                        dsucuf = str(d_suc1.encode('UTF-8')) + " " + str(d_suc2.encode('UTF-8'))
                    elif d_suc1 and not d_suc2:
                        dsucuf = str(d_suc1.encode('UTF-8'))
                    elif d_suc2 and not d_suc1:
                        dsucuf = str(d_suc2.encode('UTF-8'))
                    else:
                        dsucuf = ''
                else:
                    raise Warning(('Atencion !'), ('Ingrese Informacion de la sucursal CALLE1/CALLE2'))

                if factura.partner_id.obli_contab:
                    obli_contab = factura.partner_id.obli_contab
                    if obli_contab == 'SI':
                        cod_posfis = factura.partner_id.cod_posfis
                    else:
                        cod_posfis = '000'
                else:
                    raise Warning(('Atencion !'), ('Ingrese Informacion Fiscal en la ficha del cliente/proveedor!'))

                if factura.authorization_id.serie_entity:
                    fentp = str(factura.authorization_id.serie_entity).strip()
                else:
                    raise Warning(('Atencion !'), ('Ingrese Serie entidad de la factura!'))
                if factura.authorization_id.serie_emission:
                    femip = str(factura.authorization_id.serie_emission).strip()
                else:
                    raise Warning(('Atencion !'), ('Ingrese Serie emision de la factura!'))
                if factura.number_seq:
                    comprobante_n = str(factura.number_seq).strip()
                else:
                    raise Warning(('Atencion !'), ('Ingrese Numero de comprobante sustento de esta retencion!'))
                cod_ds = factura.document_type.code
                if factura.is_exp_reimb:
                    tot_bas_reem = 0.00
                    total_reimb_tax = 0.00
                    invdet_idr = self.env['reimbursement.account']
                    invdet_detr = invdet_idr.search([('account_reimbursement_id', '=', factura.id)])
                    for lin_reem in invdet_detr:
                        tot_bas_reem += lin_reem.total_without_taxes
                        total_reimb_tax += lin_reem.active_refund_iva
                else:
                    tot_bas_reem = 0.00
                    total_reimb_tax = 0.00

                # OBTENER DATOS DE LOS IMPUESTOS
                # if factura.deduction_id:
                #     ret_id = self.env['account.invoice.tax'].search(
                #         [('invoice_id', '=', factura.id), ('deduction_id', '!=', False)])
                # else:
                tax_id = self.env['account.invoice.tax'].search(
                        [('invoice_id', '=', factura.id)])
                for imp in tax_id:
                    print "LISTA IMPUESTOS 1", imp.tax_code_id
                    print "LISTA IMPUESTOS 2", imp.tax_code_id.cod_imp_fe
                ret_det = self.env['account.invoice.tax'].browse(tax_id)
                invdet_id = self.env['account.invoice.line'].search([('invoice_id', '=', factura.id)])
                invdet_det = self.env['account.invoice.line'].browse(invdet_id)
                cod_comp = '03'

                version = record.version
                compania = record.company
                lineas = self.env['res.company'].browse([compania.id])[0]
                empresa = lineas.partner_id.name
                ruc_empresa = lineas.partner_id.part_number
                user = self.env.user
                direccion = ''
                plazo = str(factura.partner_id.plazo)[:2]
                if user.company_id.partner_id.street and user.company_id.partner_id.street2:
                    direccion = str(user.company_id.partner_id.street) + ' Y ' + str(user.company_id.partner_id.street2)
                elif user.company_id.partner_id.street and not user.company_id.partner_id.street2:
                    direccion = str(user.company_id.partner_id.street)
                elif user.company_id.partner_id.street2 and not user.company_id.partner_id.street:
                    direccion = str(user.company_id.partner_id.street2)
                partner_address = ''
                if not factura.partner_id.street and not factura.partner_id.street2:
                    raise Warning(('Error !', "Por favor, ingrese la direccion del proveedor."))
                if factura.partner_id.street and user.company_id.partner_id.street2:
                    partner_address = str(user.company_id.partner_id.street) + ' Y ' + \
                                      str(user.company_id.partner_id.street2)
                elif factura.partner_id.street and not user.company_id.partner_id.street2:
                    partner_address = str(user.company_id.partner_id.street)
                elif factura.partner_id.street2 and not user.company_id.partner_id.street:
                    partner_address = str(user.company_id.partner_id.street2)
                if factura.tax_support.code == '02':
                    cod_reem = '41'
                if factura.tax_support.code == '01':
                    cod_reem = '01'
                if id_formulario == 'normal':
                    temision = '1'
                    # FORMAR CLAVE ACCESO COMPROBANTE NORMAL
                    clav = str(lfecha[2] + lfecha[1] + lfecha[0] + cod_comp + ruc_empresa.strip() +
                               ambiente + fentp + femip + secuencia.strip() + cod_num + temision)
                    clavea = self.modulo11(clav)
                    clavef = clav.strip() + clavea.strip()
                    ids_accfacel = self.env['account.factura.electronica']
                    vals_r = {
                        'name': 'Liquidacion de Compra',
                        'clave_acceso': clavef,
                        'cod_comprobante': cod_comp,
                        'factelect_id': factura.id
                    }
                elif id_formulario == 'contingencia':
                    temision = '2'
                    cconti = record.contingencia
                    if len(cconti) < 37:
                        raise Warning(('Atencion !'), ('Clave de contingencia debe tener 37 caracteres numericos !'))
                    else:
                        # FORMAR CLAVE ACCESO COMPROBANTE CONTINGENCIA
                        clav = str(lfecha[2] + lfecha[1] + lfecha[0] + cod_comp + cconti.strip() + temision)
                        clavea = self.modulo11(clav)
                        clavef = clav.strip() + clavea.strip()
                        ids_accfacel = self.env['account.factura.electronica']
                        vals_r = {
                            'name': 'Liquidacion de Compra',
                            'clave_contingencia': cconti,
                            'contingencia': True,
                            'cod_comprobante': cod_comp,
                            'factelect_id': factura.id
                        }

                reimbursement_obj = self.env['reimbursement.account']
                reimbursement_ids = reimbursement_obj.search([('account_reimbursement_id', '=', factura.id)])
                # TAG CONTENEDOR COMPROBANTE
                mainform = doc.createElement('liquidacionCompra')
                doc.appendChild(mainform)
                mainform.setAttribute('id', 'comprobante')
                mainform.setAttribute('version', version)

                infoTributaria = doc.createElement("infoTributaria")
                mainform.appendChild(infoTributaria)

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

                infoLiquidacion = doc.createElement("infoLiquidacionCompra")
                mainform.appendChild(infoLiquidacion)
                # TAGS HIJOS DEL TAG INFOFACTURA
                femision = doc.createElement("fechaEmision")
                infoLiquidacion.appendChild(femision)
                nfemision_id = doc.createTextNode(fecha.strip())
                femision.appendChild(nfemision_id)

                destable = doc.createElement("dirEstablecimiento")
                infoLiquidacion.appendChild(destable)
                ndestable_id = doc.createTextNode(dsucuf.strip())
                destable.appendChild(ndestable_id)

                contesp = doc.createElement("contribuyenteEspecial")
                infoLiquidacion.appendChild(contesp)
                ncontesp_id = doc.createTextNode(cod_posfis.strip())
                contesp.appendChild(ncontesp_id)

                oblicont = doc.createElement("obligadoContabilidad")
                infoLiquidacion.appendChild(oblicont)
                noblicont_id = doc.createTextNode(obli_contab.strip())
                oblicont.appendChild(noblicont_id)

                tidencomp = doc.createElement("tipoIdentificacionProveedor")
                infoLiquidacion.appendChild(tidencomp)
                ntidencomp_id = doc.createTextNode(cod_ident.strip())
                tidencomp.appendChild(ntidencomp_id)

                rasocomp = doc.createElement("razonSocialProveedor")
                infoLiquidacion.appendChild(rasocomp)
                nrasocomp_id = doc.createTextNode(name_rzc.strip())
                rasocomp.appendChild(nrasocomp_id)

                identcomp = doc.createElement("identificacionProveedor")
                infoLiquidacion.appendChild(identcomp)
                nidentcomp_id = doc.createTextNode(id_rzc.strip())
                identcomp.appendChild(nidentcomp_id)

                identcomp = doc.createElement("direccionProveedor")
                infoLiquidacion.appendChild(identcomp)
                nidentcomp_id = doc.createTextNode(partner_address.strip())
                identcomp.appendChild(nidentcomp_id)

                total_wo_taxes = doc.createElement("totalSinImpuestos")
                infoLiquidacion.appendChild(total_wo_taxes)
                vtotal_wo_taxes = Decimal(abs(tot_simp)).quantize(Decimal('0.00'))
                nvtotal_wo_taxes = doc.createTextNode(str(vtotal_wo_taxes))
                total_wo_taxes.appendChild(nvtotal_wo_taxes)

                total_discount = doc.createElement("totalDescuento")
                infoLiquidacion.appendChild(total_discount)
                vtotal_discount = Decimal(abs(tot_desc)).quantize(Decimal('0.00'))
                ntotal_discount = doc.createTextNode(str(vtotal_discount))
                total_discount.appendChild(ntotal_discount)

                if factura.is_exp_reimb:

                    doccodreimb = doc.createElement("codDocReembolso")
                    infoLiquidacion.appendChild(doccodreimb)
                    ndoccodreimb = doc.createTextNode(cod_reem.strip())
                    doccodreimb.appendChild(ndoccodreimb)

                    totalcreimbursement = doc.createElement("totalComprobantesReembolso")
                    infoLiquidacion.appendChild(totalcreimbursement)
                    vtotalcreimbursement = Decimal(abs(factura.total_reimbursement)).quantize(Decimal('0.00'))
                    ntotalcreimbursement = doc.createTextNode(str(vtotalcreimbursement))
                    totalcreimbursement.appendChild(ntotalcreimbursement)

                    total_baseimpreimb = doc.createElement("totalBaseImponibleReembolso")
                    infoLiquidacion.appendChild(total_baseimpreimb)
                    vtotal_baseimpreimb = Decimal(abs(tot_bas_reem)).quantize(Decimal('0.00'))
                    ntotal_baseimpreimb = doc.createTextNode(str(vtotal_baseimpreimb))
                    total_baseimpreimb.appendChild(ntotal_baseimpreimb)

                    total_reimbursement_tax = doc.createElement("totalImpuestoReembolso")
                    infoLiquidacion.appendChild(total_reimbursement_tax)
                    vtotal_reimbursement_tax = Decimal(abs(total_reimb_tax)).quantize(Decimal('0.00'))
                    ntotal_reimbursement_tax = doc.createTextNode(str(vtotal_reimbursement_tax))
                    total_reimbursement_tax.appendChild(ntotal_reimbursement_tax)

                totalConImpuestos = doc.createElement("totalConImpuestos")
                infoLiquidacion.appendChild(totalConImpuestos)

                imp_base = 0.00
                imp_amount = 0.00
                tax_code = '0'
                for impuesto in tax_id:
                    ret_amount = 0.00
                    if impuesto.tax_code_id.cod_imp_fe == '1':
                        cod_retfe = impuesto.base_code_id.code
                        ret_amount = impuesto.amount
                        if cod_retfe:
                            print "ok"
                        else:
                            raise Warning('Atencion !'), 'No hay configurado codigo base de la ' \
                                                         'retencion de esta factura !'
                    else:
                        if impuesto.tax_code_id.cod_imp_fe == '2':
                            if impuesto.tax_code_id.cod_tarifa == '2':
                                tax_code = '2'
                                tarifa = '12'
                                imp_base += impuesto.base
                                imp_amount += impuesto.amount
                            if impuesto.tax_code_id.cod_tarifa == '0':
                                tax_code = '0'
                                tarifa = '0'
                                imp_base += impuesto.base
                                imp_amount += impuesto.amount

                totalImpuesto = doc.createElement("totalImpuesto")
                totalConImpuestos.appendChild(totalImpuesto)

                # TAG SE REPITE CODIGO IMPUESTOS SEGUN LA FACTURA
                fcodigo = doc.createElement("codigo")
                totalImpuesto.appendChild(fcodigo)
                nfcodigo_id = doc.createTextNode('2')
                fcodigo.appendChild(nfcodigo_id)

                fcodigoPorcentaje = doc.createElement("codigoPorcentaje")
                totalImpuesto.appendChild(fcodigoPorcentaje)
                nfcodigoPorcentaje = doc.createTextNode(tax_code.strip())
                fcodigoPorcentaje.appendChild(nfcodigoPorcentaje)

                dadicional = doc.createElement("descuentoAdicional")
                totalImpuesto.appendChild(dadicional)
                vdadicional = Decimal(tot_desc).quantize(Decimal('0'))
                ndadicional = doc.createTextNode(str(vdadicional))
                dadicional.appendChild(ndadicional)

                basimp = doc.createElement("baseImponible")
                totalImpuesto.appendChild(basimp)
                vbaseimp = Decimal(abs(imp_base)).quantize(Decimal('0.00'))
                nbasimp_id = doc.createTextNode(str(vbaseimp))
                basimp.appendChild(nbasimp_id)

                imptarifa = doc.createElement("tarifa")
                totalImpuesto.appendChild(imptarifa)
                ntarifa = doc.createTextNode(tarifa.strip())
                imptarifa.appendChild(ntarifa)

                reten_amount = doc.createElement("valor")
                totalImpuesto.appendChild(reten_amount)
                vreten_amount = Decimal(abs(imp_amount)).quantize(Decimal('0.00'))
                nreten_amount = doc.createTextNode(str(vreten_amount))
                reten_amount.appendChild(nreten_amount)

                if factura.is_exp_reimb:

                    importeTotal = doc.createElement("importeTotal")
                    infoLiquidacion.appendChild(importeTotal)
                    vimptotal = Decimal(abs(factura.amount_total)).quantize(Decimal('0.00'))
                    nbasimp_id = doc.createTextNode(str(vimptotal))
                    importeTotal.appendChild(nbasimp_id)

                else:
                    total_amount = imp_amount + factura.amount_untaxed
                    importeTotal = doc.createElement("importeTotal")
                    infoLiquidacion.appendChild(importeTotal)
                    vimptotal = Decimal(abs(total_amount)).quantize(Decimal('0.00'))
                    nbasimp_id = doc.createTextNode(str(vimptotal))
                    importeTotal.appendChild(nbasimp_id)

                moneda = doc.createElement("moneda")
                infoLiquidacion.appendChild(moneda)
                nbasimp_id = doc.createTextNode(compania.currency_id.name.rstrip())
                moneda.appendChild(nbasimp_id)

                pagos = doc.createElement("pagos")
                infoLiquidacion.appendChild(pagos)

                pago = doc.createElement("pago")
                pagos.appendChild(pago)

                formaPago = doc.createElement("formaPago")
                pago.appendChild(formaPago)
                npago = doc.createTextNode(factura.partner_id.f_pago)
                formaPago.appendChild(npago)

                pagoTotal = doc.createElement("total")
                pago.appendChild(pagoTotal)
                vpagototal = Decimal(abs(factura.amount_total)).quantize(Decimal('0.00'))
                npagototal = doc.createTextNode(str(vpagototal))
                pagoTotal.appendChild(npagototal)

                pagoplazo = doc.createElement("plazo")
                pago.appendChild(pagoplazo)
                npagoplazo = doc.createTextNode(plazo)
                pagoplazo.appendChild(npagoplazo)

                unidadTiempo = doc.createElement("unidadTiempo")
                pago.appendChild(unidadTiempo)
                nunidadTiempo = doc.createTextNode(factura.partner_id.unid_t)
                unidadTiempo.appendChild(nunidadTiempo)

                reembdetalles = doc.createElement("detalles")
                mainform.appendChild(reembdetalles)

                for lines in factura.invoice_line:
                    if not lines.product_id.default_code:
                        raise Warning(('Atencion !'),
                                      ("No esta configurado el codigo de bodega para el producto '%s' !") % str(lines.product_id.name))

                    reembdetalle = doc.createElement("detalle")
                    reembdetalles.appendChild(reembdetalle)

                    codigoPrincipal = doc.createElement("codigoPrincipal")
                    reembdetalle.appendChild(codigoPrincipal)
                    ncodigoPrincipal = doc.createTextNode(lines.product_id.default_code)
                    codigoPrincipal.appendChild(ncodigoPrincipal)

                    codigoAuxiliar = doc.createElement("codigoAuxiliar")
                    reembdetalle.appendChild(codigoAuxiliar)
                    ncodigoAuxiliar = doc.createTextNode(lines.product_id.default_code)
                    codigoAuxiliar.appendChild(ncodigoAuxiliar)

                    Productdescripcion = doc.createElement("descripcion")
                    reembdetalle.appendChild(Productdescripcion)
                    nProductdescripcion = doc.createTextNode(lines.product_id.name)
                    Productdescripcion.appendChild(nProductdescripcion)

                    unidadMedida = doc.createElement("unidadMedida")
                    reembdetalle.appendChild(unidadMedida)
                    nunidadMedida = doc.createTextNode(lines.product_id.uom_id.name)
                    unidadMedida.appendChild(nunidadMedida)

                    cantidadProducto = doc.createElement("cantidad")
                    reembdetalle.appendChild(cantidadProducto)
                    ncantidadProducto = Decimal(abs(lines.quantity)).quantize(Decimal('0.00'))
                    vcantidadProducto = doc.createTextNode(str(ncantidadProducto))
                    cantidadProducto.appendChild(vcantidadProducto)

                    precioUnitario = doc.createElement("precioUnitario")
                    reembdetalle.appendChild(precioUnitario)
                    nprecioUnitario = Decimal(abs(lines.price_unit)).quantize(Decimal('0.00'))
                    vprecioUnitario = doc.createTextNode(str(nprecioUnitario))
                    precioUnitario.appendChild(vprecioUnitario)

                    descuentoProducto = doc.createElement("descuento")
                    reembdetalle.appendChild(descuentoProducto)
                    ndescuentoProducto = Decimal(abs(lines.discount)).quantize(Decimal('0.00'))
                    vdescuentoProducto = doc.createTextNode(str(ndescuentoProducto))
                    descuentoProducto.appendChild(vdescuentoProducto)

                    precioTotalSinImpuesto = doc.createElement("precioTotalSinImpuesto")
                    reembdetalle.appendChild(precioTotalSinImpuesto)
                    nprecioTotalSinImpuesto = Decimal(abs(lines.price_subtotal)).quantize(Decimal('0.00'))
                    vprecioTotalSinImpuesto = doc.createTextNode(str(nprecioTotalSinImpuesto))
                    precioTotalSinImpuesto.appendChild(vprecioTotalSinImpuesto)

                    detallesAdicionales = doc.createElement("detallesAdicionales")
                    reembdetalle.appendChild(detallesAdicionales)

                    detAdicional = doc.createElement('detAdicional')
                    detallesAdicionales.appendChild(detAdicional)
                    detAdicional.setAttribute('nombre', 'Null')
                    detAdicional.setAttribute('valor', '0')

                    detAdicional1 = doc.createElement('detAdicional')
                    detallesAdicionales.appendChild(detAdicional1)
                    detAdicional1.setAttribute('nombre', 'Null')
                    detAdicional1.setAttribute('valor', '0')

                    lineasimpuestos = doc.createElement("impuestos")
                    reembdetalle.appendChild(lineasimpuestos)

                    seq = 2

                    for imp in tax_id:
                        cod_tarifa = '0'
                        tarifa = '0'
                        if len(tax_id) > 1:
                            if imp.tax_code_id.cod_tarifa == '2':
                                if imp.base == lines.price_subtotal:
                                    tarifa = '12'
                                    cod_tarifa = '2'
                                    lineasimpuesto = doc.createElement("impuesto")
                                    lineasimpuestos.appendChild(lineasimpuesto)

                                    impcodigo = doc.createElement("codigo")
                                    lineasimpuesto.appendChild(impcodigo)
                                    nimpcodigo = doc.createTextNode(str(seq))
                                    impcodigo.appendChild(nimpcodigo)

                                    codigoPorcentaje = doc.createElement("codigoPorcentaje")
                                    lineasimpuesto.appendChild(codigoPorcentaje)
                                    ncodigoPorcentaje = doc.createTextNode(cod_tarifa.strip())
                                    codigoPorcentaje.appendChild(ncodigoPorcentaje)

                                    imptarifa = doc.createElement("tarifa")
                                    lineasimpuesto.appendChild(imptarifa)
                                    vimptarifa = doc.createTextNode(tarifa.strip())
                                    imptarifa.appendChild(vimptarifa)

                                    impbaseImponible = doc.createElement("baseImponible")
                                    lineasimpuesto.appendChild(impbaseImponible)
                                    nimpbaseImponible = Decimal(abs(lines.price_subtotal)).quantize(Decimal('0.00'))
                                    vimpbaseImponible = doc.createTextNode(str(nimpbaseImponible))
                                    impbaseImponible.appendChild(vimpbaseImponible)

                                    impValor = doc.createElement("valor")
                                    lineasimpuesto.appendChild(impValor)
                                    nimpValor = Decimal(abs(imp.amount)).quantize(Decimal('0.00'))
                                    vimpValor = doc.createTextNode(str(nimpValor))
                                    impValor.appendChild(vimpValor)

                            elif imp.tax_code_id.cod_tarifa == '0':
                                if imp.base == lines.price_subtotal and imp.account_id.id == lines.account_id.id:
                                    if imp.tax_code_id.cod_tarifa == '0':
                                        tarifa = '0'
                                        cod_tarifa = '0'
                                    if imp.tax_code_id.cod_tarifa == '2':
                                        tarifa = '12'
                                        cod_tarifa = '2'

                                    lineasimpuesto = doc.createElement("impuesto")
                                    lineasimpuestos.appendChild(lineasimpuesto)

                                    impcodigo = doc.createElement("codigo")
                                    lineasimpuesto.appendChild(impcodigo)
                                    nimpcodigo = doc.createTextNode(str(seq))
                                    impcodigo.appendChild(nimpcodigo)

                                    codigoPorcentaje = doc.createElement("codigoPorcentaje")
                                    lineasimpuesto.appendChild(codigoPorcentaje)
                                    ncodigoPorcentaje = doc.createTextNode(cod_tarifa.strip())
                                    codigoPorcentaje.appendChild(ncodigoPorcentaje)

                                    imptarifa = doc.createElement("tarifa")
                                    lineasimpuesto.appendChild(imptarifa)
                                    vimptarifa = doc.createTextNode(tarifa.strip())
                                    imptarifa.appendChild(vimptarifa)

                                    impbaseImponible = doc.createElement("baseImponible")
                                    lineasimpuesto.appendChild(impbaseImponible)
                                    nimpbaseImponible = Decimal(abs(lines.price_subtotal)).quantize(Decimal('0.00'))
                                    vimpbaseImponible = doc.createTextNode(str(nimpbaseImponible))
                                    impbaseImponible.appendChild(vimpbaseImponible)

                                    impValor = doc.createElement("valor")
                                    lineasimpuesto.appendChild(impValor)
                                    nimpValor = Decimal(abs(imp.amount)).quantize(Decimal('0.00'))
                                    vimpValor = doc.createTextNode(str(nimpValor))
                                    impValor.appendChild(vimpValor)

                        else:
                            cod_tarifa = '0'
                            if imp.tax_code_id.cod_tarifa == '0':
                                tarifa = '0'
                                cod_tarifa = '0'
                            elif imp.tax_code_id.cod_tarifa == '2':
                                tarifa = '12'
                                cod_tarifa = '2'

                            lineasimpuesto = doc.createElement("impuesto")
                            lineasimpuestos.appendChild(lineasimpuesto)

                            impcodigo = doc.createElement("codigo")
                            lineasimpuesto.appendChild(impcodigo)
                            nimpcodigo = doc.createTextNode(str(seq))
                            impcodigo.appendChild(nimpcodigo)

                            codigoPorcentaje = doc.createElement("codigoPorcentaje")
                            lineasimpuesto.appendChild(codigoPorcentaje)
                            ncodigoPorcentaje = doc.createTextNode(cod_tarifa.strip())
                            codigoPorcentaje.appendChild(ncodigoPorcentaje)

                            imptarifa = doc.createElement("tarifa")
                            lineasimpuesto.appendChild(imptarifa)
                            vimptarifa = doc.createTextNode(tarifa.strip())
                            imptarifa.appendChild(vimptarifa)

                            impbaseImponible = doc.createElement("baseImponible")
                            lineasimpuesto.appendChild(impbaseImponible)
                            nimpbaseImponible = Decimal(abs(lines.price_subtotal)).quantize(Decimal('0.00'))
                            vimpbaseImponible = doc.createTextNode(str(nimpbaseImponible))
                            impbaseImponible.appendChild(vimpbaseImponible)

                            impValor = doc.createElement("valor")
                            lineasimpuesto.appendChild(impValor)
                            nimpValor = Decimal(abs(imp.amount)).quantize(Decimal('0.00'))
                            vimpValor = doc.createTextNode(str(nimpValor))
                            impValor.appendChild(vimpValor)

                if factura.is_exp_reimb:

                    reembolsos = doc.createElement("reembolsos")
                    mainform.appendChild(reembolsos)

                    marca = 'A'
                    modelo = 'B'
                    serie = '0'
                    cod_pais = '593'
                    partner_type = '01'
                    cod_rembursement = '41'
                    for reem_lines in reimbursement_ids:
                        cod_tarifa = '2'
                        percent_code = '0'
                        reimb_tariff = '0'
                        reem_base_imponible = '0'
                        date = reem_lines.date_refund
                        rdate = date.split('-')
                        reimb_date = rdate[2] + "/" + rdate[1] + "/" + rdate[0]
                        if reem_lines.refund_number:
                            reimbursement_number = reem_lines.refund_number[8:]
                            reimb_number = reimbursement_number.zfill(9)
                        if reem_lines.identification_type == 'ced':
                            identification = '03'
                            num_identification = reem_lines.ident_refund
                        if reem_lines.identification_type == 'ruc':
                            identification = '04'
                            num_identification = reem_lines.ruc_ident_refund
                        if reem_lines.identification_type == 'passport':
                            identification = '05'
                            num_identification = reem_lines.passport_ident_refund
                        if reem_lines.refund_base_iva > 0.00 and reem_lines.refund_base_iva_cero > 0.00:
                            reem_iva = reem_lines.active_refund_iva
                            percent_code = '2'
                            reimb_tariff = '12'
                        if reem_lines.refund_base_iva > 0.00:
                            reem_iva = reem_lines.active_refund_iva
                            percent_code = '2'
                            reimb_tariff = '12'
                        if reem_lines.refund_base_iva_cero > 0.00:
                            reem_iva = reem_lines.active_refund_iva
                            percent_code = '0'
                            reimb_tariff = '0'

                        if len(reem_lines.est_refund) < 3:
                            raise except_orm('Error !', 'El numero de establecimiento debe tener 3 digitos, verifique '
                                                        'el reembolso %s' % reem_lines.refund_number)
                        if len(reem_lines.refund_series) < 3:
                            raise except_orm('Error !', 'El numero de emision debe tener 3 digitos, verifique el '
                                                        'reembolso %s' % reem_lines.refund_number)

                        reembolsoDetalle = doc.createElement("reembolsoDetalle")
                        reembolsos.appendChild(reembolsoDetalle)

                        tipoIdentificacionProveedorReembolso = doc.createElement("tipoIdentificacionProveedorReembolso")
                        reembolsoDetalle.appendChild(tipoIdentificacionProveedorReembolso)
                        ntipoIdentificacionProveedorReembolso = doc.createTextNode(identification)
                        tipoIdentificacionProveedorReembolso.appendChild(ntipoIdentificacionProveedorReembolso)

                        identificacionProveedorReembolso = doc.createElement("identificacionProveedorReembolso")
                        reembolsoDetalle.appendChild(identificacionProveedorReembolso)
                        nidentificacionProveedorReembolso = doc.createTextNode(num_identification)
                        identificacionProveedorReembolso.appendChild(nidentificacionProveedorReembolso)

                        codPaisPagoProveedorReembolso = doc.createElement("codPaisPagoProveedorReembolso")
                        reembolsoDetalle.appendChild(codPaisPagoProveedorReembolso)
                        ncodPaisPagoProveedorReembolso = doc.createTextNode(cod_pais)
                        codPaisPagoProveedorReembolso.appendChild(ncodPaisPagoProveedorReembolso)

                        tipoProveedorReembolso = doc.createElement("tipoProveedorReembolso")
                        reembolsoDetalle.appendChild(tipoProveedorReembolso)
                        ntipoProveedorReembolso = doc.createTextNode(partner_type)
                        tipoProveedorReembolso.appendChild(ntipoProveedorReembolso)

                        codDocReembolso = doc.createElement("codDocReembolso")
                        reembolsoDetalle.appendChild(codDocReembolso)
                        ncodDocReembolso = doc.createTextNode(cod_rembursement)
                        codDocReembolso.appendChild(ncodDocReembolso)

                        estabDocReembolso = doc.createElement("estabDocReembolso")
                        reembolsoDetalle.appendChild(estabDocReembolso)
                        nestabDocReembolso = doc.createTextNode(reem_lines.est_refund)
                        estabDocReembolso.appendChild(nestabDocReembolso)

                        ptoEmiDocReembolso = doc.createElement("ptoEmiDocReembolso")
                        reembolsoDetalle.appendChild(ptoEmiDocReembolso)
                        nptoEmiDocReembolso = doc.createTextNode(reem_lines.refund_series)
                        ptoEmiDocReembolso.appendChild(nptoEmiDocReembolso)

                        secuencialDocReembolso = doc.createElement("secuencialDocReembolso")
                        reembolsoDetalle.appendChild(secuencialDocReembolso)
                        nsecuencialDocReembolso = doc.createTextNode(reimb_number)
                        secuencialDocReembolso.appendChild(nsecuencialDocReembolso)

                        fechaEmisionDocReembolso = doc.createElement("fechaEmisionDocReembolso")
                        reembolsoDetalle.appendChild(fechaEmisionDocReembolso)
                        nfechaEmisionDocReembolso = doc.createTextNode(reimb_date)
                        fechaEmisionDocReembolso.appendChild(nfechaEmisionDocReembolso)

                        numeroautorizacionDocReemb = doc.createElement("numeroautorizacionDocReemb")
                        reembolsoDetalle.appendChild(numeroautorizacionDocReemb)
                        nnumeroautorizacionDocReemb = doc.createTextNode(reem_lines.refund_authorization)
                        numeroautorizacionDocReemb.appendChild(nnumeroautorizacionDocReemb)

                        detalleImpuestos = doc.createElement("detalleImpuestos")
                        reembolsoDetalle.appendChild(detalleImpuestos)

                        detalleImpuesto = doc.createElement("detalleImpuesto")
                        detalleImpuestos.appendChild(detalleImpuesto)

                        codigoReemb = doc.createElement("codigo")
                        detalleImpuesto.appendChild(codigoReemb)
                        ncodigoReemb = doc.createTextNode(str(cod_tarifa))
                        codigoReemb.appendChild(ncodigoReemb)

                        codigoPorcentaje = doc.createElement("codigoPorcentaje")
                        detalleImpuesto.appendChild(codigoPorcentaje)
                        ncodigoPorcentaje = doc.createTextNode(percent_code.strip())
                        codigoPorcentaje.appendChild(ncodigoPorcentaje)

                        reimtariff = doc.createElement("tarifa")
                        detalleImpuesto.appendChild(reimtariff)
                        nreimtariff = doc.createTextNode(reimb_tariff)
                        reimtariff.appendChild(nreimtariff)

                        baseImponibleReembolso = doc.createElement("baseImponibleReembolso")
                        detalleImpuesto.appendChild(baseImponibleReembolso)
                        nbaseImponibleReembolso = Decimal(abs(reem_lines.total_without_taxes)).quantize(Decimal('0.00'))
                        vbaseImponibleReembolso = doc.createTextNode(str(nbaseImponibleReembolso))
                        baseImponibleReembolso.appendChild(vbaseImponibleReembolso)

                        impuestoReembolso = doc.createElement("impuestoReembolso")
                        detalleImpuesto.appendChild(impuestoReembolso)
                        nimpuestoReembolso = Decimal(abs(reem_iva)).quantize(Decimal('0.00'))
                        vimpuestoReembolso = doc.createTextNode(str(nimpuestoReembolso))
                        impuestoReembolso.appendChild(vimpuestoReembolso)

                infoAdicional = doc.createElement("infoAdicional")
                mainform.appendChild(infoAdicional)

                cadicional = doc.createElement('campoAdicional')
                infoAdicional.appendChild(cadicional)
                cadicional.setAttribute('nombre', 'Null')
                cadicional_id = doc.createTextNode('0')
                cadicional.appendChild(cadicional_id)

                cadicional1 = doc.createElement('campoAdicional')
                infoAdicional.appendChild(cadicional1)
                cadicional1.setAttribute('nombre', 'Null')
                cadicional1_id = doc.createTextNode('0')
                cadicional1.appendChild(cadicional1_id)

                out = base64.encodestring(doc.toxml())
                name = "%s.xml" % (clavef)
                record.name = name
                record.data = out
                f = open('/home/oddo/' + firmadig + '/' + 'FACTURA_ELECTRONICA/FACTURASF/' + name, 'w')
                f.write(doc.toxml())
                f.close()
                # *************************************************************************************************
                if firmadig == 'MISSION PETROLEUM S.A.':
                    print "ENTRO MISSION PETROLEUM S.A."
                    res = jarWrapper('/opt/addons_mission/o2s_felectronica/wizard/XadesBes.jar',
                                     '/opt/addons_mission/o2s_felectronica/wizard/' + firmadig +
                                     '/' + 'firmaMissionPetroleum2018.p12',
                                     'mission2020', '/home/oddo/' + firmadig + '/' + 'FACTURA_ELECTRONICA/FACTURASF/' +
                                     name,
                                     '/home/oddo/' + firmadig + '/' + 'FACTURA_ELECTRONICA/FACTURAF', name)
                    w = open('/home/oddo/' + firmadig + '/' + 'FACTURA_ELECTRONICA/FACTURAF/' + name, 'rb')
                    q = w.read()
                    # *********************************************************************************************
                res_sri = client.service.validarComprobante(base64.encodestring(q))
            # CSV: AUMENTO PARA EL CASO DE SOLO CONSULTAR
            if factura.state_factelectro == 'firmado':
                clavef = factura.liquidation_authorization
                autorizada = 0
                while autorizada != 1:
                    res_autcomp = client1.service.autorizacionComprobante(clavef)
                    if len(res_autcomp.autorizaciones) > 0:
                        if len(res_autcomp.autorizaciones.autorizacion[0]) > 0:
                            estado_ws = res_autcomp.autorizaciones.autorizacion[0]['estado']
                            autorizada = 1
                            if str(estado_ws).strip() == 'AUTORIZADO':
                                # ******************************XML ENVIO POR MAIL CLIENTE*************************
                                numaut_ws = res_autcomp.autorizaciones.autorizacion[0]['numeroAutorizacion']
                                fechaut_ws = res_autcomp.autorizaciones.autorizacion[0]['fechaAutorizacion']
                                if ambiente == '2':
                                    ambiente_ws = 'PRODUCCION'
                                elif ambiente == '1':
                                    ambiente_ws = 'PRUEBAS'
                                comprobante_ws = res_autcomp.autorizaciones.autorizacion[0]['comprobante']

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
                                # CSV 07-06-2017 PARA ADJUNTARLO************************
                                archivo = '/home/oddo/'+firmadig+'/'+'FACTURA_ELECTRONICA/AUTORIZADO/'+data_fname
                                res_model = 'account.invoice'
                                id = ids and type(ids) == type([]) and ids[0] or ids
                                self.load_doc(out1, factura.id, data_fname, archivo, res_model)
                                # **************************************************************************************
                                num_aut = res_autcomp.autorizaciones.autorizacion[0]['numeroAutorizacion']
                                vals_accinv = {'liquidation_authorization': num_aut,
                                               'state_factelectro': 'autorizado',
                                               'date_aut': time.strftime('%Y-%m-%d %H:%M:%S'),
                                               'inf_electronica': 'autorizado'}
                                factura.write(vals_accinv)
                                mensaje = str(estado_ws)
                                record.mensaje = mensaje
                            else:
                                if res_autcomp.autorizaciones.autorizacion[-1]['estado'] == 'AUTORIZADO':
                                    num_aut = res_autcomp.autorizaciones.autorizacion[-1]['numeroAutorizacion']
                                    vals_accinv = {'liquidation_authorization': num_aut,
                                                   'state_factelectro': 'autorizado',
                                                   'date_aut': time.strftime('%Y-%m-%d %H:%M:%S'),
                                                   'inf_electronica': 'autorizado'}
                                    factura.write(vals_accinv)
                                    mensaje = str(res_autcomp.autorizaciones.autorizacion[-1]['estado'])
                                    record.mensaje = mensaje
                                else:
                                    mensaje = str(res_autcomp)
                                    record.mensaje = mensaje
                                    vals_inf_elect = {'inf_electronica': mensaje}
                                    factura.write(vals_inf_elect)
            if res_sri and res_sri['estado'] == 'RECIBIDA':
                # CSV:29-12-2017: AUMENTO PARA ENVIAR ARCHIVO FIRMADO CLIENTE Y SRI PRIMER WEB SERVICES
                # CSV: PARA ADJUNTARLO************************
                w = open('/home/oddo/'+firmadig+'/'+'FACTURA_ELECTRONICA/FACTURAF/'+name, 'rb')
                q=w.read()
                out2 = base64.encodestring(q)
                data_fname = name
                archivo = '/home/oddo/'+firmadig+'/'+'FACTURA_ELECTRONICA/FACTURAF/'+name
                res_model = 'account.invoice'
                id = ids and type(ids) == type([]) and ids[0] or ids
                self.load_doc(out2, factura.id, data_fname, archivo, res_model)
                # Escribo en la factura
                num_autws1 = clavef
                val_aut = {'name': num_autws1}
                auth.write(val_aut)
                vals_accinvws1 = {'liquidation_authorization': num_autws1,
                                  'state_factelectro': 'firmado',
                                  'date_aut': time.strftime('%Y-%m-%d %H:%M:%S'),
                                  'inf_electronica': 'firmado'}
                factura.write(vals_accinvws1)
                accfactelect_id = ids_accfacel.create(vals_r)
                mensaje = str('firmado')
                record.mensaje = mensaje
            elif res_sri and res_sri['estado'] == 'DEVUELTA':
                mensaje = str(res_sri)
                record.mensaje = mensaje
                vals_inf_elect = {'inf_electronica': mensaje}
                factura.write(vals_inf_elect)
        return True

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
            # CSV: 22-03-2018:AUMENTO PARA LIMPIAR ADJUNTOS ANTES DE ADJUNTAR EL NUEVO
            delet = ir_att.search([('res_id', '=', id),('res_model', '=', res_model)])
            if delet:
                for line in delet:
                    line.unlink()
            # *************************************************************************
            attach_vals.update({'res_id': id})
        ir_att.create(attach_vals)

    def modulo11(self, cadena):
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
            lista.append(cad_inv)
            indice += 1
        lista.reverse()
        for recorre in lista:
            valor = int(recorre) * multiplicador
            multiplicador += 1
            if multiplicador > baseMultiplicador:
                multiplicador = 2
            total += valor
        if total == 0 or total == 1:
            verificador = 0
        else:
            if (11 - (total % 11)) != 11:
                verificador = 11 - total % 11
            else:
                verificador = 0
        if verificador == 10:
            verificador = 1
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

