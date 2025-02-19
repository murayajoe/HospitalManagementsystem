# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

{
    'name' : 'Invoice Partial Payment Reconciliation',
    'version' : '18.0.0.3',
    'sequence' : '-112',
    'category' : 'Sales',
    'depends' : ['base', 
        'account', 'sale', 'sale_management', 
    ],
    'author': 'BrowseInfo',
    'summary': 'Partial Invoice payment invoice reconciliation payment with reconciliation invoice partial reconciliation payment reconciliation add outstanding with write off invoice write off invoice payment partial payment partial reconcile Partial Payment Reconcile',
    'description': '''

       Partial Invoice Payment in odoo,
       Customer make partial payments in odoo,
       Vendor make partial payment in odoo,
       Single invoice for partial payments in odoo,
       Multiple invoice for partial payments in odoo,
       Single bill for partial payments in odoo,
       Multiple bill for partial payments in odoo,
       Remaining Outstanding Credit/Debit Amount in odoo,

    ''',
    'website' : "https://www.browseinfo.com/demo-request?app=bi_partial_payment_invoice&version=17&edition=Community",
    'price': 89,
    'currency': 'EUR',
    'data': [
        'security/ir.model.access.csv',
        'wizard/account_payment_view.xml',
        'wizard/multiple_paymemt_view.xml',
        'views/account_move_view.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'bi_partial_payment_invoice/static/src/js/account_payment.js',
        ],
    },
    'qweb' : [],
    'license' : 'OPL-1',
    'auto_install': False,
    'installable': True,
    "live_test_url":'https://www.browseinfo.com/demo-request?app=bi_partial_payment_invoice&version=17&edition=Community',
    "images":['static/description/Banner.gif'],
}
