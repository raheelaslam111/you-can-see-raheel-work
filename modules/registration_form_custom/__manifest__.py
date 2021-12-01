##############################################################################
{
    'name': 'Registration Form',
    'version': '14.0',
    'author': 'Raheel Aslam',
    'company': 'Self employee',
    'website': 'https://www.abc.com',
    'category': 'hidden',
    'license': 'AGPL-3',
    'sequence': 15,
    'summary': 'customization in Sale purchase',
    'images': [],
    'depends': ['base','auth_signup','website','maintenance','product','stock'],
    'description': """
========================================================================
    """,
    'data': [
        'security/ir.model.access.csv',
        'views/registration_form_template.xml',
        'views/res_partner.xml',
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
