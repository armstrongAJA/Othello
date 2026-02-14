from enum import Enum

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
            print(' '.join(str(cell) for cell in row))

    def place_piece(self, x, y, piece):
        if 0 <= x < self.size and 0 <= y < self.size:
            self.board[y][x] = piece
        else:
            raise ValueError("Coordinates out of bounds")

    def is_empty(self, x, y):
        if 0 <= x < self.size and 0 <= y < self.size:
            return self.board[y][x] == 0
        else:
            raise ValueError("Coordinates out of bounds")

    def clear_board(self):
        self.board = [[0 for _ in range(self.size)] for _ in range(self.size)]