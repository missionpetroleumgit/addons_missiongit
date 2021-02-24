# -*- coding:utf-8 -*-
#    Copyright (C) 2019 Daniel Aldaz <daldaz@mission-petroleum.com>.
#    All Rights Reserved.



{
    'name': 'Reportes Nomina',
    'version': '1.0',
    'category': 'Generic Modules/RRHH',
    'author': "Daniel Aldaz, MissionPetroleum Developer",
    'description': """
Reporteria Nomina
======================
    """,
    'depends': [
        'hr',
        'hr_payroll',
    ],
    'data': [
        'views/mp_rrhh_report_view.xml',
    ],
    'test': [
    ],
    'installable': True,
}
