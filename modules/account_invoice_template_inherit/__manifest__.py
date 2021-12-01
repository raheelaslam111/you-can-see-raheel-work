##############################################################################
{
    'name': 'Account Invoice Template Inherit',
    'version': '14.0',
    'author': 'Silverdale',
    'company': 'Silverdale',
    'website': 'https://www.silverdaletech.com',
    'category': 'Accounting',
    'license': 'AGPL-3',
    'sequence': 15,
    'summary': 'customization in accounting invoice',
    'images': [],
    'depends': ['account'],
    'description': """,T3208,T3229,T3204,H1135,H1173,H1612
========================================================================
    """,
    'data': [
        'security/ir.model.access.csv',
        'views/account_invoice_template_inherit.xml',
        'views/product_view_inherit.xml',
        'views/account_report_with_payment.xml',
        'views/invoice_inherit.xml',
    ],
    # 'qweb': [
    #     "static/src/xml/reset_to_draft.xml",
    # ],
    'demo': [],
    'test': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
