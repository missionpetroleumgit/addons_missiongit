# -*- coding:utf-8 -*-
#
#
#    Copyright (C) 2019 Daniel Aldaz <daldaz@mission-petroleum.com>.
#    All Rights Reserved.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.


{
    'name': 'Holidays Import',
    'version': '1.0',
    'category': 'Generic Modules/RRHH',
    'author': "Daniel Aldaz, MissionPetroleum Developer",
    'description': """
======================
    """,
    'depends': [
        'sale', 'hr_holidays'
    ],
    'data': [
        'views/wizard_import_holidays_view.xml',
    ],
    'test': [
    ],
    'installable': True,
}
