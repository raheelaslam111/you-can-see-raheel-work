##############################################################################
{
    'name': 'Appraisal Core Evaluation',
    'version': '14.0.2051',
    'author': 'silverdaletech',
    'website': 'www.silverdaletech.com',
    'category': 'Appraisal',
    'license': 'AGPL-3',
    'sequence': 15,
    'summary': 'customization in Appraisal',
    'images': [],
    'depends': ['base','hr_appraisal'],
    'description': """
========================================================================
    """,
    'data': [
            'security/ir.model.access.csv',
            'views/view.xml',
            'views/web_tree_dynamic_colored_field.xml',

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

