# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2013 jmesteve All Rights Reserved
#                       https://github.com/jmesteve
#                       <jmesteve@me.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
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

{
    'name': "Yowsup",
    'version': '0.1',
    'category': 'Tools',
    'description': """
        [ENG] Add Whatsapp.
    """,
    'author': 'jmesteve',
    'website': 'https://github.com/jmesteve',
    'license': 'AGPL-3',
    "depends": ['base','warning_box'],
    "data": ['security/groups.xml',
             'security/ir.model.access.csv',
             'yowsup_view.xml',
             'yowsup_partner_send_view.xml'
             ],
    'images': ['images/Partners.png',
               'images/gateway.png',
               'images/history.png',
               'images/Sendmessage.png',
               'images/security.png',
               ],
    "active": False,
    "installable": True
}
