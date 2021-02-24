##########################
# -*- coding: utf-8 -*- ##
##########################


from openerp import models, fields, api
from openerp.exceptions import except_orm, Warning
from datetime import datetime



class control_sheet_report(models.Model):

    _name = 'control.sheet.report'

    name = fields.Char(string="Nombre Control de hoja")
    report = fields.Char(string="Nombre del Reporte")
    code = fields.Char(string="Codigo")
    review = fields.Char(string="Revision")
    issue = fields.Date(string="Emision")
    model_id = fields.Many2one('ir.model', string="Modelo")





