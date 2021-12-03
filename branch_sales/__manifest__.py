##############################################################################
{
    'name': 'Branch Sales',
    'version': '0.15',
    'author': 'Raheel aslam',
    'website': '',
    'category': '',
    'license': 'AGPL-3',
    'sequence': 15,
    'summary': 'Company branches and sales, inventory, reports respectively',
    'images': [],
    'depends': ['base','hr','account','stock','sale','sale_stock'],
    'description': """
    Company branches and sales, inventory, reports respectively
========================================================================
    """,
    'data': [
            'security/ir.model.access.csv',
            'views/branch.xml',
            'views/user.xml',
            'views/warehouse.xml',
            'views/sales.xml',
            'views/menus.xml',
    ],
    'demo': [],
    'test': [],
    'installable': True,
    'application': False,
    'auto_install': False,
}

