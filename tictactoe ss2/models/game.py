from odoo import models, fields, api

class TicTacToeGame(models.Model):
    _name = 'tic.tac.toe'
    _description = 'Tic Tac Toe Game'

    board = fields.Text(string='Board', default="---------")  # 9-character string for the board
    current_player = fields.Selection([('X', 'Player X'), ('O', 'Player O')], default='X')
    winner = fields.Selection([('X', 'Player X'), ('O', 'Player O'), ('D', 'Draw')], default=False)

    def check_winner(self):
        """ Check if there is a winner """
        win_patterns = [(0,1,2), (3,4,5), (6,7,8), (0,3,6), (1,4,7), (2,5,8), (0,4,8), (2,4,6)]
        board = self.board

        for pattern in win_patterns:
            a, b, c = pattern
            if board[a] == board[b] == board[c] and board[a] in 'XO':
                self.winner = board[a]
                return board[a]

        if '-' not in board:
            self.winner = 'D'  # Draw
            return 'D'
        
        return False  # No winner yet

    def make_move(self, position):
        """ Update the board when a player makes a move """
        if self.board[position] == '-' and not self.winner:
            board_list = list(self.board)
            board_list[position] = self.current_player
            self.board = ''.join(board_list)
            self.check_winner()
            self.current_player = 'O' if self.current_player == 'X' else 'X'
