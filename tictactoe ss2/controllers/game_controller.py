# from odoo import http
# from odoo.http import request

# class TicTacToeController(http.Controller):

#     @http.route('/tic_tac_toe/new_game', type='json', auth='user')
#     def new_game(self):
#         """ Create a new game and return its ID """
#         game = request.env['tic.tac.toe'].create({})
#         return {'game_id': game.id, 'board': game.board, 'current_player': game.current_player}

#     @http.route('/tic_tac_toe/move', type='json', auth='user')
#     def make_move(self, game_id, position):
#         """ Make a move in the game """
#         game = request.env['tic.tac.toe'].browse(game_id)
#         game.make_move(int(position))
#         return {'board': game.board, 'current_player': game.current_player, 'winner': game.winner}
