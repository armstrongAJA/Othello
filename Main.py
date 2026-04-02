"""Entry point for the Othello game. Initializes the board and starts the game loop."""
import logging
import sys

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(name)s: %(message)s')

from Game import Game
from pygame_ui import PygameUI


if __name__ == '__main__':
    game = Game(8)  # Initialize an 8x8 board
    ui = PygameUI(game)
    ui.run()