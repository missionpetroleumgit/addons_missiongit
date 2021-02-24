# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution - Ecuador
#    Copyright (C) 2019 MissionPetroleum Daniel Aldaz (<daldaz@mission-petroleum.com>).
#
##############################################################################

from openerp import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    service_type = fields.Selection([('rental', 'Alquiler Equipos'), ('gas', 'Combustible'),
                                     ('buy', 'Compra de madera'), ('hardware', 'Ferreteria Industrial'),
                                     ('maintenance', 'Mantenimiento Automotriz'), ('move', 'Movilizacion'),
                                     ('civil', 'Obra Civil'), ('replacement', 'Repuesto Mecanico'),
                                     ('cservice', 'Servicio de Combustible'), ('a_service', 'Servicio de Alimentacion'),
                                     ('technical', 'Servicio Tecnico'), ('transport', 'Transporte Pesados'),
                                     ('treatment', 'Tratamiento Desechos')], 'Servicios Prestados')

    service_categ = fields.Selection([('feeding', 'Alimentacion'), ('eq_rental', 'Alquiler de Equipos'),
                                      ('car_rental', 'Alquiler de Vehiculos'),
                                      ('hardware', 'Ferreteria, equipos y herramientas'),
                                      ('others', 'Otros'), ('gas_provision', 'Provision de Combustible y Lubricantes'),
                                      ('wood_provision', 'Provision de Madera'),
                                      ('replacement', 'Repuesto, Mecanica y mantenimiento'),
                                      ('transport', 'Transporte')], 'Categorizacion de servicios')

    region = fields.Selection([('coast', 'Costa'), ('sierra', 'Sierra'), ('east', 'Oriente'),
                               ('inter', 'Internacional')], 'Region')

    canton_id = fields.Many2one('canton.state', 'Canton')
    parish_id = fields.Many2one('parish.state', 'Parroquia')

ResPartner()


class ParishState(models.Model):
    _name = 'parish.state'

    name = fields.Char('Nombre Parroquia', required=True)
    code = fields.Char('Codigo')

ParishState()


class CantonState(models.Model):
    _name = 'canton.state'

    name = fields.Char('Nombre Canton', required=True)
    code = fields.Char('Codigo')

CantonState()
