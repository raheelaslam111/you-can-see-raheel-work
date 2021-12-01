##############################################################################
{
    'name': 'Add Warehouse to Analytic Default Rules',

    'version': '14.0.0.1.3',

    'author': 'Silverdale',
    'company': 'Silverdale',
    'website': 'https://www.silverdaletech.com',
    'category': 'Accounting',
    'license': 'AGPL-3',
    'sequence': 15,
    'summary': 'customization in accounting invoice & Ticket 471 Document Upload Bug fix for invoice ',
    'images': [],
    'depends': ['account','sale','purchase','stock','account_asset'],
    'description': """
        Sprint : S2115
<<<<<<< HEAD
        Task: T3307/TH1184, T4315, T4443,T4462,H2310,T4662,T4648
=======
        Task: T3307/TH1184, T4315, T4443,T4462,H2310,T4661/H2358,T4662,T4648
>>>>>>> T4648_valuation_entries_items_filter
    """,
    'data': [
            'views/analytic_account_inherit.xml',
            'views/purchase.xml',
    ],
    'demo': [],
    'test': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}

