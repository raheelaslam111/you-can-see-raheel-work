##############################################################################
{
    'name': 'Sale Coupon Ext',
    'version': '14.0',
    'author': 'Silverdale',
    'company': 'Silverdale',
    'website': 'https://www.silverdaletech.com',
    'category': 'Sale',
    'license': 'AGPL-3',
    'sequence': 15,
    'summary': 'customization in Sale Coupon',
    'images': [],
    'depends': ['sale_coupon'],
    'description': """,T3295
========================================================================
    """,
    'data': [
        'security/ir.model.access.csv',
        # 'views/account_invoice_template_inherit.xml',
        # 'views/product_view_inherit.xml',
        # 'views/account_report_with_payment.xml',
        # 'views/invoice_inherit.xml',
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
