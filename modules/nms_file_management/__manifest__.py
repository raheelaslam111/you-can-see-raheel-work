{
    'name': "NMS File Management",

    'summary': """
        NMS File Management""",

    'description': """
        T4361, T4369, T4406, T4444,T4448,T4447,T4452,T4449,T4457,T4450,T4531,T4624,T4614,T4692
    """,

    'author': "Silverdale",
    'website': "https://www.silverdaletech.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Stock',
    'version': '14.0.0.1.0',

    # any module necessary for this one to work correctly
    'depends': ['base', 'stock', 'purchase', 'report_xml', "asn_import_file",'sale'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/nms_bounce_attachment.xml',
        'wizard/nms_file_import_wizard.xml',
        'views/nms_assets.xml',
        'views/product_template_inherit.xml',
        'views/product_product_inherit.xml',
        'report/nms_reports.xml',
        'report/uedf_report_template.xml',
        'data/nms_sequence.xml',
        'views/holidays.xml',
        'views/boost_file.xml',
        'views/stock_picking_views.xml',
        'views/production_lot_views.xml',

    ],
    'qweb': ['static/src/xml/nms_list_view.xml'],
}
# -*- coding: utf-8 -*-
