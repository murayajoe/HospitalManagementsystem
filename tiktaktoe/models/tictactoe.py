from odoo import models, fields, api

class TicTacToeGame(models.Model):
    _name = 'tic.tac.toe'
    _description = 'Tic Tac Toe Game'

    name = fields.Char(string="Game Name", required=True, default="Tic-Tac-Toe")
    player_x = fields.Many2one('res.users', string="Player X", required=True)
    player_o = fields.Many2one('res.users', string="Player O", required=True)
    board = fields.Text(string="Game Board", default="---------")  # 3x3 grid stored as a string
    winner = fields.Selection([('x', 'Player X'), ('o', 'Player O'), ('draw', 'Draw')], string="Winner", readonly=True)
    state = fields.Selection([('ongoing', 'Ongoing'), ('finished', 'Finished')], string="State", default="ongoing")

    @api.model
    def create_new_game(self, player_x, player_o):
        """ Creates a new game session """
        return self.create({
            'player_x': player_x,
            'player_o': player_o,
            'board': '---------',  # Empty board
            'state': 'ongoing'
        })
