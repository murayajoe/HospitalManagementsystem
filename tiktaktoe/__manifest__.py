{
    'name': 'Tic Tac Toe',
    'version': '1.0',
    'summary': 'Play Tic-Tac-Toe inside Odoo',
    'category': 'Games',
    'author': 'Joe Muraya',
    'depends': ['base'],
    'data': [
        # 'views/tictactoe_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'tic_tac_toe/static/src/js/tictactoe.js',
        ],
    },
    'installable': True,
    'application': True,
}
