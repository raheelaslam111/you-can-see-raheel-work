##############################################################################
{
    'name': 'SaleOrder Product Smartbutton',
    'version': '14.0',
    'author': 'Silverdale',
    'company': 'Silverdale',
    'website': 'https://www.silverdaletech.com',
    'category': 'saleorder',
    'license': 'AGPL-3',
    'sequence': 15,
    'summary': 'saleorder product smart button addings',
    'images': [],
    'depends': ['base','sale','delivery'],
    'description': """T3204,H1589
========================================================================
    """,
    'data': [
            'security/ir.model.access.csv',
            'wizard/product_select.xml',
            'wizard/product_select_gift.xml',
            'views/view.xml',
            'views/delivery_view_inherit.xml',
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

