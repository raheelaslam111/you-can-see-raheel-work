# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'IL2000 Integration',
    'category': 'Tools',
    'sequence': 271,
    'version': '14.0.0.2.1',
    'summary': 'Integration of IL2000 Shipment Method',
    'description':
        """
        Task IDS:2836,2837,2838,2839,2840,2861,3663,H1724,H2083
        """,
    'author': "Silverdale",
    'website': "https://www.silverdaletech.com",
    'category': 'Inventory/Delivery',
    'depends': ['base','delivery','stock','website_sale_delivery'],
    'data': [
        'security/ir.model.access.csv',
        'views/res_config_settings.xml',
        'data/delivery_il2000.xml',
        'views/delivery_il2000.xml',
        'views/request_quote_view.xml',
        
        'wizard/popup_message_show.xml',
     
    ],
  
    'images': ['static/description/icon.png'],
    'installable': True,
    'application': True,
    'license': 'OEEL-1',
}
