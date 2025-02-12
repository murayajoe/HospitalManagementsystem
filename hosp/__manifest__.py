{
    'name': 'Hospital Management System',
    'version': '18.0',
    'summary': 'Module for managing hospital operations',
    'sequence': -100,
    'description': """
        A comprehensive Hospital Management System for managing patients, doctors,
        appointments, medical records, billing, and more.
    """,
    'category': 'Healthcare',
    'author': 'Joe Muraya',
    'maintainer': 'Joe Muraya',
    'website': 'https://clickpoa.odoo.com',
    'license': 'LGPL-3',
    'depends': [],
    'data': [
        'security/ir.model.access.csv',
        'views/menu.xml', 
        'views/patient_view.xml',    
    ],
    'assets': {},
    'installable': True,
    'application': True,
    'auto_install': False,
}
