from odoo import http
from odoo.http import request

class TicTacToeController(http.Controller):
    
    @http.route('/tic_tac_toe/move', type='json', auth="user")
    def make_move(self, game_id, position, player):
        game = request.env['tic.tac.toe'].browse(game_id)
        if game.state != 'ongoing':
            return {'error': 'Game has already ended.'}

        board = list(game.board)
        if board[position] != '-':
            return {'error': 'Invalid move, position already taken.'}

        board[position] = player
        game.board = ''.join(board)

        winner = self.check_winner(board)
        if winner:
            game.winner = winner
            game.state = 'finished'

        return {'board': game.board, 'winner': game.winner}

    def check_winner(self, board):
        win_patterns = [(0,1,2), (3,4,5), (6,7,8), (0,3,6), (1,4,7), (2,5,8), (0,4,8), (2,4,6)]
        for a, b, c in win_patterns:
            if board[a] == board[b] == board[c] and board[a] != '-':
                return board[a]
        if '-' not in board:
            return 'draw'
        return None
