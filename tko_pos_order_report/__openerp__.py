# -*- encoding: utf-8 -*-
# -*- coding: utf-8 -*-
# © 2018 TKO <http://tko.tko-br.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'tko_pos_order_report',
    'version': '0.007',
    'description': 'This module enhances POS Order reporting',
    'category': 'Customizations',
    'sequence': 150,
    'complexity': 'pos_customization',
    'author': 'TKOBR',
    'website': 'http://www.tko.tko-br.com',
    'images': ['images/oerp61.jpeg',
               ],
    'depends': [
        'point_of_sale',
        'tko_point_of_sale_discount_on_order',
        'tko_point_of_sale_order_type',
    ],

    'data': [
        'pos_order_report_view.xml',
        'report/pos_order_report_view.xml',
    ],

    'init': [],
    'demo': [],
    'update': [],
    'test': [],  # YAML files with tests
    'installable': True,
    'application': False,
    'auto_install': False,  # If it's True, the modules will be auto-installed when all dependencies are installed
    'certificate': '',
}
