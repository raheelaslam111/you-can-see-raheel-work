{
    'name': "Export Csv ASN File",

    'summary': """
        Export Csv ASN File""",

    'description': """
        T4395, T4533, T4397,T4632
    """,

    'author': "Silverdale",
    'website': "https://www.silverdaletech.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Stock',
    'version': '14.0.0.1.0',

    # any module necessary for this one to work correctly
    'depends': ['base', 'stock','nms_file_management','boost_packaging','delivery_fedex'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'report/nms_report_csv.xml',
        'views/nms_csv_attachment.xml',
        'views/stock_move_line_inherit.xml',
        'report/report_delibveryslip_extended.xml',
    ],
    # 'qweb': ['static/src/xml/nms_list_view.xml'],
}
