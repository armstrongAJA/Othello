from Board import spaceState


class Player:
    def __init__(self, color, mode = "human"):
        self.color = color
        self.mode = mode

    @property
    def opponent_color(self):
        if self.color == spaceState.BLACK:
            return spaceState.WHITE
        return spaceState.BLACK
    def getPossibleMoves(self, board):
        # Return a list of (x, y) tuples representing valid moves for this player
        moves = []
        for y in range(board.size):
            for x in range(board.size):
                if board.is_empty(x, y):
                    if self.can_flip(x, y, board):
                        moves.append((x, y))
        return moves

    def can_flip(self, x, y, board):
        # This function should check if placing a piece at (x, y) would flip any opponent pieces
        # It would need to check in all 8 directions for a valid move
        # Check in each direction for opponent pieces followed by a piece of the player's color
        if board.is_empty(x, y):
            for direction in [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)]:
                dx, dy = direction
                if self.check_direction(x, y, dx, dy, self.opponent_color, board):
                    return True
        return False
                
    def check_direction(self, x, y, dx, dy, opponent_color, board):
        # This function should check in a specific direction (dx, dy) for opponent pieces followed by a piece of the player's color
        # It would return True if it finds a valid move in that direction, otherwise False
        
        x += dx
        y += dy
    
        # Check if the first piece in this direction is an opponent's piece
        if 0 <= x < board.size and 0 <= y < board.size and board.board[y][x] == opponent_color:
            # Continue checking in this direction
            while 0 <= x < board.size and 0 <= y < board.size:
                x += dx
                y += dy
                if 0 <= x < board.size and 0 <= y < board.size:
                    # If we find an empty space, then this is not a valid move
                    if board.board[y][x] == spaceState.EMPTY:
                        break
                    # If we find a piece of the player's color, then this is a valid move
                    if board.board[y][x] == self.color:
                        return True
        return False
    
    def numberOfAddedPieces(self, x, y, board):
        # This function should return the number of opponent pieces that would be flipped if the player places a piece at (x, y)
        # It would need to check in all 8 directions and count the number of pieces that would be flipped
        count = 0
        for direction in [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)]:
            dx, dy = direction
            if self.check_direction(x, y, dx, dy, self.opponent_color, board):
                # Count the number of opponent pieces flipped in this direction
                x_temp = x + dx
                y_temp = y + dy
                while 0 <= x_temp < board.size and 0 <= y_temp < board.size and board.board[y_temp][x_temp] == self.opponent_color:
                    count += 1
                    x_temp += dx
                    y_temp += dy
        return count
    
    def calculateScore(self, board):
        # This function should calculate the player's score based on the current state of the board
        # It would count the number of pieces of the player's color on the board
        score = 0
        for row in board.board:
            for cell in row:
                if cell == self.color:
                    score += 1
        return score
    
    def makeMove(self, x, y, board):
        # This function should place a piece at (x, y) and flip the opponent's pieces accordingly
        if board.is_empty(x, y) and self.can_flip(x, y, board):
            board.place_piece(x, y, self.color)
            # Flip the opponent's pieces in all 8 directions
            for direction in [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)]:
                dx, dy = direction
                if self.check_direction(x, y, dx, dy, self.opponent_color, board):
                    # Flip the pieces in this direction
                    x_temp = x + dx
                    y_temp = y + dy
                    while 0 <= x_temp < board.size and 0 <= y_temp < board.size and board.board[y_temp][x_temp] == self.opponent_color:
                        board.place_piece(x_temp, y_temp, self.color)
                        x_temp += dx
                        y_temp += dy

    