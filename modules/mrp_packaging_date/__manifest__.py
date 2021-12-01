# -*- coding: utf-8 -*-
{
    'name': "MRP Packaging Date & Propagate Schedule Date",

    'summary': """
        Add a Packaging Date when the manufacturing order is marked as Done and Propagate Dates - Schedule Date on MO to Pick and Store
""",
    'description': 'T3672, H1587, H1590,H1605/T3824, H1602/T3815,H1686, T4594, H2625, H2619 ,T5163',

    'author': "Silverdale",
    'website': "https://www.silverdaletech.com",

    'category': 'Manufacturing',

    'version': '14.0.1.5',



    # any module necessary for this one to work correctly
    'depends': ['base', 'mrp','stock','sale_mrp', 'manufacturing_notes'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/mrp_view.xml',
        'views/so_mrp_connect.xml',
        'views/email_template_salesteam.xml',
        'wizard/mrp_package_date_wizard.xml',
    ],
}
