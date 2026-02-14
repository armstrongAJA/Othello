#Entry point for the Othello game. Initializes the board and starts the game loop.
import logging

# Default to DEBUG so interactive runs show module debug logs; change to INFO to reduce verbosity.
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(name)s: %(message)s')
logging.getLogger().debug('Logging initialized at DEBUG level')

from Game import Game
try:
    from UI import GameUI
except Exception:
    GameUI = None


if __name__ == '__main__':
    game = Game(8) # Initialize an 8x8 board
    if GameUI is not None:
        ui = GameUI(game)
        ui.run()
    else:
        # Fall back to console loop if UI can't be imported
        game.board.display()
        while True:
            x, y = map(int, input(f"Player {game.current_player.color}, enter your move (x y): ").split())
            game.play_turn(x, y)
            game.board.display()