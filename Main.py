"""Entry point for the Othello game. Initializes the board and starts the game loop.

Supports the original Tkinter `GameUI` and a new pygame-based UI which can be launched
by passing `--pygame` on the command line or setting the `USE_PYGAME=1` environment var.
"""
import logging
import os
import sys

# Default to DEBUG so interactive runs show module debug logs; change to INFO to reduce verbosity.
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(name)s: %(message)s')
logging.getLogger().debug('Logging initialized at DEBUG level')

from Game import Game
from UI import GameUI


def _console_loop(game):
    game.board.display()
    try:
        while True:
            x, y = map(int, input(f"Player {game.current_player.color}, enter your move (x y): ").split())
            game.play_turn(x, y)
            game.board.display()
    except (EOFError, KeyboardInterrupt):
        pass


if __name__ == '__main__':
    game = Game(8)  # Initialize an 8x8 board
    if GameUI is not None:
        ui = GameUI(game)
        ui.run()
    else:
        _console_loop(game)