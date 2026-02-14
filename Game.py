from Board import Board, spaceState
from Player import Player
from AI import AI


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

    def play_turn(self, x, y):
        if not self.board.is_empty(x, y):
            print("Invalid move: Space is not empty.")
            return

        if not self.current_player.can_flip(x, y, self.board):
            print("Invalid move: No pieces would be flipped.")
            return

        # Perform the move (Player.makeMove handles placement and flipping)
        self.current_player.makeMove(x, y, self.board)

        # After a successful move, switch to the other player
        self.switch_player()

        # If neither player has moves, the game is over
        if self.check_game_over():
            print("Game over.")
            return

        # If the next player has no moves, skip their turn back to the previous player
        if not self.current_player.getPossibleMoves(self.board):
            print("No valid moves for the next player; skipping turn.")
            self.switch_player()
            
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
