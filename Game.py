from Board import Board, spaceState
from Player import Player
from AI import AI
import logging

logger = logging.getLogger(__name__)


class Game:
    def __init__(self, board_size, player1=None, player2=None):
        self.board = Board(board_size)
        # allow callers to provide custom player objects (AI or Player)
        self.player1 = player1 if player1 is not None else Player(spaceState.BLACK, mode="human")
        self.player2 = player2 if player2 is not None else Player(spaceState.WHITE, mode="human")
        self.current_player = self.player1

    def switch_player(self):
        if self.current_player == self.player1:
            self.current_player = self.player2
        else:
            self.current_player = self.player1
        logger.debug('Switched current_player to %s', getattr(self.current_player, 'color', None))

    def play_turn(self, x, y):
        logger.debug('play_turn called with (%s,%s) by %s', x, y, getattr(self.current_player, 'color', None))
        if not self.board.is_empty(x, y):
            logger.info('Invalid move: Space is not empty at (%s,%s)', x, y)
            return None

        if not self.current_player.can_flip(x, y, self.board):
            logger.info('Invalid move: No pieces would be flipped at (%s,%s) for %s', x, y, getattr(self.current_player, 'color', None))
            return None

        # Perform the move (Player.makeMove handles placement and flipping)
        mover = self.current_player
        flipped = mover.makeMove(x, y, self.board)
        logger.debug('play_turn result flipped=%s', flipped)

        # After a successful move, switch to the other player
        self.switch_player()

        # If neither player has moves, the game is over
        if self.check_game_over():
            logger.info('Game over detected')
            return {'flipped': flipped, 'placed': (x, y), 'mover_color': mover.color}

        # If the next player has no moves, skip their turn back to the previous player
        if not self.current_player.getPossibleMoves(self.board):
            logger.info('No valid moves for the next player; skipping turn.')
            self.switch_player()

        return {'flipped': flipped, 'placed': (x, y), 'mover_color': mover.color}
            
    def check_game_over(self):
        # This function should check if the game is over, which happens when neither player has a valid move
        # It would need to check for valid moves for both players and return True if there are no valid moves, otherwise False
        if not self.player1.getPossibleMoves(self.board) and not self.player2.getPossibleMoves(self.board):
            return True
        return False
    
    def get_winner(self):  
        #get the winner of the game using Player.calculateScore() and return the player with the higher score, or None if it's a tie
        score1 = self.player1.calculateScore(self.board)
        score2 = self.player2.calculateScore(self.board)
        if score1 > score2:
            return self.player1
        elif score2 > score1:
            return self.player2
        else:
            return None
        
    def reset(self, player1=None, player2=None):
        # Recreate board
        self.board = Board(self.board.size)

        # Optionally allow new player configurations
        if player1:
            self.player1 = player1
        if player2:
            self.player2 = player2

        self.current_player = self.player1
