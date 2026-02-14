from enum import Enum
import logging

logger = logging.getLogger(__name__)

class spaceState(Enum):
    EMPTY = 0
    BLACK = 1
    WHITE = 2

class Board:
    def __init__(self, size):
        self.size = size
        self.board = [[spaceState.EMPTY for _ in range(size)] for _ in range(size)]
        mid = size // 2 # set mid to centre of the board (upper if even, centre if odd)
        self.board[mid - 1][mid - 1] = spaceState.WHITE
        self.board[mid][mid] = spaceState.WHITE
        self.board[mid - 1][mid] = spaceState.BLACK
        self.board[mid][mid - 1] = spaceState.BLACK

    def display(self):
        for row in self.board:
            line = ' '.join(str(cell) for cell in row)
            print(line)
        logger.debug('Displayed board (size=%s)', self.size)

    def place_piece(self, x, y, piece):
        if 0 <= x < self.size and 0 <= y < self.size:
            self.board[y][x] = piece
            logger.debug('Placed piece %s at (%s,%s)', piece, x, y)
        else:
            raise ValueError("Coordinates out of bounds")

    def is_empty(self, x, y):
        if 0 <= x < self.size and 0 <= y < self.size:
            empty = self.board[y][x] == spaceState.EMPTY
            logger.debug('is_empty(%s,%s) -> %s', x, y, empty)
            return empty
        else:
            raise ValueError("Coordinates out of bounds")

    def clear_board(self):
        self.board = [[spaceState.EMPTY for _ in range(self.size)] for _ in range(self.size)]
        logger.debug('Cleared board')
    