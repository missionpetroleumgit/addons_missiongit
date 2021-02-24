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

from openerp import api
from datetime import datetime, date
from openerp.osv import fields, osv



class hr_family_burden(osv.osv):
    _name = 'hr.family.burden'
    _description = 'Cargas Familiares'

    def _current_age(self, cr, uid, ids, field_name, arg, context):
        res = {}
        today = datetime.today()
        dob = today
        for family_burden in self.browse(cr, uid, ids):
            if family_burden.birth_date:
                dob = datetime.strptime(family_burden.birth_date, '%Y-%m-%d').date()
            res[family_burden.id] = today.year - dob.year
        return res

    _columns = {
        'employee_id': fields.many2one('hr.employee', string='Empleado', required=False),
        'name': fields.char(string='Nombres', size=255, required=True,),
        'last_name': fields.char(string='Apellidos', size=200, required=True,),
        'birth_date': fields.date(string='Fch. Nacimiento'),
        'relationship': fields.selection([
            ('child', 'Hijo/a'), ('nieto', 'Nieto/a'),
            ('wife_husband', 'Esposo/a'), ('padre', 'Padre'), ('madre', 'Madre'), ('co_worker', 'Conviviente'),
        ], string='Relación', select=True,),
        'age': fields.function(_current_age, method=True, string='Edad', type='integer', store=True),
        'level':fields.selection([
            ('without_instruction', 'Sin Instrucción'),
            ('primary', 'Educacion Primaria'),
            ('basic', 'Educacion Básica'),
            ('secondary', 'Educacion Secundaria'),
            ('unified_general', 'Educación General Únificado'),
            ('higher', 'Educacion Superior'),
            ('advance_technician', 'Técnico Superior'),
            ('technologist', 'Tecnólogo'),
            ('third_level', 'Título de Tercer Nivel'),
            ('fourth_level', 'Título de Cuarto Nivel'),
            ('craftsman', 'Artesano'),
            ('student', 'Estudiante Universitario'),
            ('graduated', 'Egresado'),
            ('phd',"Ph.D."),
        ], 'Nivel Educacion', select=True),
        'status': fields.selection([
            ('graduated', 'Graduado'),
            ('ongoing', 'En Curso'),
            ('abandoned', 'Abandonado'),
        ], 'Estado', select=True),

        'has_disability': fields.boolean('discapacitado?'),
        'emp_tipo_disc': fields.selection((('visual', 'Visual'), ('auditiva', 'Auditiva'),
                                           ('intelectual', 'Intelectual'), ('mental', 'Mental'), ('fisica', 'Fisica')),
                                          "Tipo"),
        'courses': fields.boolean('Cursos'),
        'courses_ids': fields.one2many('hr.family.courses', 'course_id', 'Cursos Tomados'),
        'emp_porcentaje_disc': fields.float('Porcentaje'),
        'disc_percentage': fields.float('Porcentaje'),
    }

    @api.onchange('emp_porcentaje_disc')
    def onchange_disc_percentage(self):
        if self.emp_porcentaje_disc:
            self.disc_percentage = self.emp_porcentaje_disc
        else:
            self.disc_percentage = '0.00'

    def name_get(self, cr, uid, ids, context=None):
        res = []
        for r in self.read(cr, uid, ids, ['name', 'last_name'], context):
            name = r['name']
            if r['last_name']:
                name = name + " " + r['last_name']
            res.append((r['id'], name))
        return res

hr_family_burden()


class hr_course(osv.osv):
    _name = 'hr.course'

    _columns = {
        'name': fields.char('Nombre curso',  required=1),
        'reference': fields.char('Referencia'),
    }

hr_course()


class hr_family_courses(osv.osv):
    _name = 'hr.family.courses'

    _columns = {
        'course_id': fields.many2one('hr.family.burden'),
        'course_family_id': fields.many2one('hr.course', 'Nombre del curso o seminario'),
        'institution': fields.many2one('hr.institutions', 'Institución'),
        'hours': fields.float('Horas'),
        'start_date': fields.date('Fecha Inicio'),
        'end_date': fields.date('Fecha Fin'),

    }

hr_family_courses()





class hr_institutions(osv.osv):
    _name = 'hr.institutions'

    _columns = {
        'name': fields.char('Nombre', size=32),
        'type': fields.selection((('public', 'Pública'), ('private', 'Privada')), "Tipo"),
    }
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
