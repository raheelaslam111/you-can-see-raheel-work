# -*- coding: utf-8 -*-
{
    'name': "Customize Chatter",
    'summary': """
        Hide/Show Chatter Window""",

    'description': """
        notification of send message in chatter
    """,

    'author': "Silverdaletech",
    'website': "http://www.silverdaletech.com",
    'category': 'Chatter',
    'version': '14.0.2049',
    'sequence': 2,
    'depends': ['base', 'web', 'mail'],

    'data': [

        'views/assets.xml',

    ],

    'qweb': [
        # "static/src/xml/message.xml",
        # "static/src/xml/chatter_topbar.xml",
    ],
    "installable": True,
    "auto_install": False,
    'application': True,
}
