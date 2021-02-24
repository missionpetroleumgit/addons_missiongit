#-*- coding:utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution    
#    Copyright (C)
#    All Rights Reserved
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from datetime import datetime
from openerp.osv import fields, osv
from openerp.tools.translate import _

class hr_education_area(osv.osv):
    _name = 'hr.education.area'
    _description = "Area de Educacion"
    _columns = {
        'name':fields.char('Nombre', size=255),
    }
hr_education_area()

class hr_education_level(osv.osv):
    _name = "hr.education.level"
    _description = "Nivel de Educacion"

    _columns = {
        'title': fields.char('Titulo', size=255, ),
        'country_id': fields.many2one('res.country', 'Región', required=False),
        'institution': fields.many2one('hr.institutions', 'Institución'),
        'start_date': fields.date('Fecha Inicio'),
        'end_date': fields.date('Fecha Fin'),
        'at_present': fields.boolean('Actualmente?',),
        'level': fields.selection([
            ('without_instruction', 'Sin Instrucción'),
            ('primary', 'Educacion Primaria'),
            ('basic', 'Educacion Básica'),
            ('secondary', 'Educacion Secundaria'),
            ('unified_general', 'Educación General Únificado'),
            ('higher', 'Educacion Superior'),
            ('advance_technician', 'Técnico Superior'),
            ('technologist',"Tecnólogo"),
            ('third_level', 'Título de Tercer Nivel'),
            ('fourth_level',"Título de Cuarto Nivel"),
            ('craftsman', 'Artesano'),
            ('student', 'Estudiante Universitario'),
            ('graduated', 'Egresado'),
            ('phd',"Ph.D."),
        ], 'Nivel Educación', select=True),
        'status': fields.selection([
            ('graduated', 'Graduado'),
            ('ongoing', 'En Curso'),
            ('abandoned', 'Abandonado'),
        ],    'Estado', select=True,),
        'education_area_id': fields.many2one('hr.education.area', 'Area de Educación'),
        'employee_id': fields.many2one('hr.employee', 'Employee'),
        'education_levels_ids': fields.one2many('hr.education.level.course', 'level_id', 'Cursos'),

    }

    _rec_name = "title"

hr_education_level()


class hr_education_level_course(osv.osv):
    _name = "hr.education.level.course"

    _columns = {
        'level_id': fields.many2one('hr.education.area','Niveles Educación'),
        'name': fields.char('Año/Semestre', size=32),
        'date': fields.datetime('Horarios'),
        'ref': fields.char('Observaciones', size=64),

    }


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
