##############################################################################
{
    'name': 'AV IQ Product (T1522) ',
    'version': '12.0',
    'author': 'Silverdale',
    'website': 'https://www.silverdaletech.com',
    'category': 'website',
    'license': 'AGPL-3',
    'sequence': 15,
    'summary': 'For importing product data through AV-IQ Product API',
    'images': [],
    'depends': ['base','product','stock_account'],
    'description': """
    T_3331.
========================================================================
    """,
    'data': [
            'security/ir.model.access.csv',

            'views/menus.xml',
            'views/api_settings_view.xml',
            'views/manufacturer_view.xml',
            'views/categories_view.xml',
            'views/api_product_view.xml',
            'views/api_product_lines_view.xml',
            'views/product_inherit_view.xml',

            'data/api_settings_data.xml',
            'wizard/import_wizard.xml',
    ],

    'demo': [],
    'test': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}

