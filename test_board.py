from Board import Board, spaceState

if __name__ == '__main__':
    b = Board(8)
    print('Initial board:')
    b.display()

    # place a black piece in the top-left and show board again
    b.place_piece(0, 0, spaceState.BLACK)
    print('\nAfter placing BLACK at (0,0):')
    b.display()
