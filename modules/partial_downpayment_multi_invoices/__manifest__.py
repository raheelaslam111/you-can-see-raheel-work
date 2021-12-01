# -*- coding: utf-8 -*-
{
    'name': "partial_downpayment_multi_invoices",

    'summary': """
    While creating invoices from sale order provides functionality to split down payment in multiple
     invoices.
    """,

    'description': """
        T3903,H2205,T4678
    """,

    'author': "Silverdale",
    'website': "http://www.silverdaletech.com",

    'category': 'Sales',
    'version': '14.0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'sale', 'sale_management','account','custom_invoice'],

    # always loaded
    'data': [
        'views/views.xml',
        'data/partial_down_payment.xml',
    ],

    'demo': [],
    'test': [],
    'installable': True,
    'application': True,
    'auto_install': False,

}
