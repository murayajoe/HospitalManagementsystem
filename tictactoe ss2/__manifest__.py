{
    'name': 'Tic_Tac_Toe_Game',
    'version': '1.0',
    'summary': 'Interactive Tic-Tac-Toe game inside Odoo',
    'author': 'Joe Muraya',
    'category': 'Games',
    'depends': ['base', 'web'],
    'data': [
        'views/tic_tac_toe.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'tic_tac_toe/static/src/game.js',
            'tic_tac_toe/static/css/game.css',
        ],
    },
    'installable': True,
    'application': True,
}
