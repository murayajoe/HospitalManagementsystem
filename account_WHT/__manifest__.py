# -*- coding: utf-8 -*-
{
    'name': "Withholding Tax - WHT",

    'summary': """
        This module will allow you to deduct WHT at the time of payment or Inovice/Bill. """,

    'description': """
        This module is used for the setting calculation and deduction of Withholding Tax (WHT). It enables user to set up WHT as per the regulation of their respective region of operation.
    """,

    'author': "One Stop Odoo",
    'maintainer': "One Stop Odoo",
    'sequence': '-113',
    'website': "https://www.onestopodoo.com",
    'license': 'OPL-1',
    'category': 'Accounting',
    'version': '18.0.1.0.0',
    'depends': ['account'],
    'data': [
        'data/wht_data.xml',
        'security/account_wht_security.xml',
        'security/ir.model.access.csv',
        'views/account_wht.xml',
        'views/account_move.xml',
        'views/account_payment.xml',
        'views/account_payment_register.xml',
        'views/account_tax.xml',
        'wizard/wht_bill_wizard.xml'
    ],
    "images": 
    [
        'static/description/banner.gif',
        'static/description/icon.png',
    ],

    #  'price': 190,
     'currency': 'USD',
     'installable': True,
     'auto_install': False,
     'application': True
}
