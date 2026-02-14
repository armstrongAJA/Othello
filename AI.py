from Player import Player
from Board import Board, spaceState

class AI(Player):
    def __init__(self, color):
        super().__init__(color, mode="AI")

    def choose_move(self, board):
        # This function should implement the logic for the AI to choose a move based on the current state of the board
        # It could use a simple heuristic, such as choosing the move that flips the most opponent pieces, or it could implement a more complex strategy
        possible_moves = []
        for y in range(board.size):
            for x in range(board.size):
                if board.is_empty(x, y):
                    if self.can_flip(x, y, board):
                        possible_moves.append((x, y))
        if possible_moves:
            # Return the move that flips the most opponent pieces
            return max(possible_moves, key=lambda move: self.numberOfAddedPieces(move[0], move[1], board))
        return None
    
    def evaluate_board(self, board):
        # Evaluation = 0.5 * (normalized number of possible moves)
        #            + 0.5 * (normalized piece difference)
        # Normalise both terms by the total number of cells (board.size*board.size)
        max_cells = board.size * board.size if board.size > 0 else 1

        # number of possible moves for this player
        possible_moves = 0
        for y in range(board.size):
            for x in range(board.size):
                if board.is_empty(x, y) and self.can_flip(x, y, board):
                    possible_moves += 1
        moves_term = possible_moves / max_cells

        # piece difference (my pieces - opponent pieces)
        my_count = 0
        opp_count = 0
        for row in board.board:
            for cell in row:
                if cell == self.color:
                    my_count += 1
                elif cell == self.opponent_color:
                    opp_count += 1
        pieces_term = (my_count - opp_count) / max_cells

        return 0.5 * moves_term + 0.5 * pieces_term
    
    def Minimax(self, board, depth, maximizing_player):
        # This function should implement the minimax algorithm for the AI to evaluate the game tree and choose the best move
        # It would need to recursively evaluate the possible moves for both players and return the best move for the AI
        if depth == 0:
            return self.evaluate_board(board)
        if maximizing_player:
            max_eval = float('-inf')
            for y in range(board.size):
                for x in range(board.size):
                    if board.is_empty(x, y) and self.can_flip(x, y, board):
                        # Simulate the move
                        board.place_piece(x, y, self.color)
                        eval = self.Minimax(board, depth - 1, False)
                        # Undo the move
                        board.board[y][x] = spaceState.EMPTY
                        max_eval = max(max_eval, eval)
            return max_eval
        else:
            min_eval = float('inf')
            for y in range(board.size):
                for x in range(board.size):
                    if board.is_empty(x, y) and self.can_flip(x, y, board):
                        # Simulate the opponent's move
                        board.place_piece(x, y, self.opponent_color)
                        eval = self.Minimax(board, depth - 1, True)
                        # Undo the move
                        board.board[y][x] = spaceState.EMPTY
                        min_eval = min(min_eval, eval)
            return min_eval

    def choose_move_minimax(self, board, depth):
        best_move = None
        best_value = float('-inf')
        for y in range(board.size):
            for x in range(board.size):
                if board.is_empty(x, y) and self.can_flip(x, y, board):
                    # Simulate the move
                    board.place_piece(x, y, self.color)
                    move_value = self.Minimax(board, depth - 1, False)
                    # Undo the move
                    board.board[y][x] = spaceState.EMPTY
                    if move_value > best_value:
                        best_value = move_value
                        best_move = (x, y)
        return best_move 
