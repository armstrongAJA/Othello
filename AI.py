from Player import Player
from Board import Board, spaceState
import logging

logger = logging.getLogger(__name__)

class AI(Player):
    def __init__(self, color, depth=2):
        super().__init__(color, mode="AI")
        self.debug = False
        # search depth for minimax
        self.depth = int(depth)

    def choose_move(self, board):
        # This function should implement the logic for the AI to choose a move based on the current state of the board
        # It could use a simple heuristic, such as choosing the move that flips the most opponent pieces, or it could implement a more complex strategy
        possible_moves = []
        for y in range(board.size):
            for x in range(board.size):
                if board.is_empty(x, y) and self.can_flip(x, y, board):
                    added = self.numberOfAddedPieces(x, y, board)
                    if added > 0:
                        possible_moves.append((x, y))
                    elif self.debug:
                        logger.debug("AI debug: candidate (%s,%s) has can_flip but added==0", x, y)
        if possible_moves:
            # Return the move that flips the most opponent pieces
            choice = max(possible_moves, key=lambda move: self.numberOfAddedPieces(move[0], move[1], board))
            if self.debug:
                logger.debug('AI debug: choose_move selected %s with flips=%s', choice, self.numberOfAddedPieces(choice[0], choice[1], board))
            return choice
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

        val = 0.5 * moves_term + 0.5 * pieces_term
        logger.debug('evaluate_board -> moves_term=%s pieces_term=%s value=%s', moves_term, pieces_term, val)
        return val
    
    def Minimax(self, board, depth, maximizing_player):
        # This function should implement the minimax algorithm for the AI to evaluate the game tree and choose the best move
        # It would need to recursively evaluate the possible moves for both players and return the best move for the AI
        if depth == 0:
            return self.evaluate_board(board)

        if maximizing_player:
            max_eval = float('-inf')
            # iterate valid moves for this player
            for y in range(board.size):
                for x in range(board.size):
                    if board.is_empty(x, y) and self.can_flip(x, y, board):
                        # Simulate the move on a cloned board
                        clone = self._clone_board(board)
                        self.makeMove(x, y, clone)
                        eval = self.Minimax(clone, depth - 1, False)
                        max_eval = max(max_eval, eval)
            return max_eval
        else:
            min_eval = float('inf')
            # simulate opponent moves using a temporary Player instance
            from Player import Player as _Player
            opponent = _Player(self.opponent_color)
            for y in range(board.size):
                for x in range(board.size):
                    if board.is_empty(x, y) and opponent.can_flip(x, y, board):
                        clone = self._clone_board(board)
                        opponent.makeMove(x, y, clone)
                        eval = self.Minimax(clone, depth - 1, True)
                        min_eval = min(min_eval, eval)
            return min_eval

    def choose_move_minimax(self, board, depth=None):
        best_move = None
        best_value = float('-inf')
        if depth is None:
            depth = getattr(self, 'depth', 2)
        for y in range(board.size):
            for x in range(board.size):
                if board.is_empty(x, y) and self.can_flip(x, y, board):
                    # ensure the move flips something
                    if self.numberOfAddedPieces(x, y, board) <= 0:
                        if self.debug:
                            logger.debug('AI debug: minimax candidate (%s,%s) ignored, flips=0', x, y)
                        continue
                    # Simulate the move
                    clone = self._clone_board(board)
                    self.makeMove(x, y, clone)
                    move_value = self.Minimax(clone, depth - 1, False)
                    if move_value > best_value:
                        best_value = move_value
                        best_move = (x, y)
        if self.debug:
            logger.debug('AI debug: choose_move_minimax selected %s value=%s', best_move, best_value)
        return best_move 

    def _clone_board(self, board):
        # Create a deep copy of the board instance for safe simulation
        new_board = Board(board.size)
        new_board.board = [row.copy() for row in board.board]
        return new_board
