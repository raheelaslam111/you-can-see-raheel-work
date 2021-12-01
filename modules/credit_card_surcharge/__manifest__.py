# -*- coding: utf-8 -*-
{
    'name': "Add Credit Card Surcharge",

    'summary': """
        As a Finance team member, I want to add a % surcharge onto the invoice at the point of online payment in order to make sure that customers are paying for the payment acquirer fees and not the Company.""",

    'description': """T1068 ,H_1494, H1598, H1608.
    """,

    'author': "Silverdale",
    'company': "Silverdale",
    'website': "https://www.silverdaletech.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '14.0.2',

    # any module necessary for this one to work correctly
    'depends': ['base', 'payment','payment_helcim'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/product_demo.xml',
        'views/views_payment_acquirer.xml',
        'views/account_move_inherit.xml',
    ],
    'installable': True,
    'application': True,
}
