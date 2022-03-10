# -*- coding: utf-8 -*-
{
    'name': "Enz Rehla JAN",
    'author':
        'Enzapps',
    'summary': """
This module will help to payment by Check.
""",

    'description': """
        Long description of module's purpose
    """,
    'website': "",
    'category': 'base',
    'version': '12.0',
    'depends': ['base','sale','contacts','account','purchase','ezp_rehlacar'],
    "images": ['static/description/icon.png'],
    'data': [
        'security/ir.model.access.csv',
        'data/check.xml',
        'views/sale.xml',
        'views/negative.xml',
        'views/auto_form.xml',

    ],
    'demo': [
    ],
    'installable': True,
    'application': True,
}
