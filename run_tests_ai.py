#!/usr/bin/env python3
from Game import Game
from Board import spaceState
from AI import AI


g = Game(8)
# use AI players
p1 = AI(spaceState.BLACK)
p2 = AI(spaceState.WHITE)
# enable debug to surface candidate info
p1.debug = True
p2.debug = True

g.reset(player1=p1, player2=p2)

print('Starting AI vs AI simulation')
turn = 0
errors = []
max_turns = 200

while not g.check_game_over() and turn < max_turns:
    cp = g.current_player
    print(f"Turn {turn}, current {cp.color}")
    if getattr(cp, 'mode', 'human') != 'AI':
        moves = cp.getPossibleMoves(g.board)
        print('Human moves:', moves)
        if not moves:
            g.switch_player()
            turn += 1
            continue
        x,y = moves[0]
        res = g.play_turn(x, y)
        print('play_turn returned', res)
        if res is None:
            errors.append(f"Human move rejected at {(x,y)}")
            break
    else:
        move = cp.choose_move(g.board)
        print('AI chose', move)
        if move is None:
            g.switch_player()
            turn += 1
            continue
        x,y = move
        can = cp.can_flip(x, y, g.board)
        added = cp.numberOfAddedPieces(x, y, g.board)
        print('can', can, 'added', added)
        res = g.play_turn(x, y)
        print('play_turn returned', res)
        if res is None:
            errors.append(f"play_turn rejected AI move {(x,y)} can_flip={can} added={added}")
            break
        flipped = res.get('flipped', [])
        if added > 0 and len(flipped) == 0:
            errors.append(f"AI move {(x,y)} had added={added} but flipped returned 0")
            break
    turn += 1

print('finished', turn)
if errors:
    print('ERRORS')
    for e in errors:
        print(e)
else:
    print('NO ERRORS')
