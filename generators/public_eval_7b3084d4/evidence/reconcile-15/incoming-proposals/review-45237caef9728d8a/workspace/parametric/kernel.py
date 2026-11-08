"""Four rotation-only pieces; unique reconstruction is part of the input grammar.

This file is also the byte-identical native kernel. It has no repository imports.
The sampler proposes jagged four-region partitions, scatters their rotations,
then solves the rendered input independently and rejects ambiguous proposals.
"""
from functools import lru_cache
from math import isqrt
import random

RULE_TASK_ID = 'ee_7b3084d4'
CORNERS = ('northwest', 'northeast')


def integer(value, name, low=None, high=None):
    if type(value) is not int or (low is not None and value < low) or (high is not None and value > high):
        raise ValueError(f'{name} must be an integer in the declared range')
    return value


def strict_grid(grid):
    if (type(grid) is not list or not 1 <= len(grid) <= 30 or
            any(type(row) is not list for row in grid) or not 1 <= len(grid[0]) <= 30 or
            any(len(row) != len(grid[0]) for row in grid) or
            any(type(x) is not int or not 0 <= x <= 9 for row in grid for x in row)):
        raise ValueError('Expected a rectangular 1..30 strict integer-color grid')
    return tuple(tuple(row) for row in grid)


def normalize(piece):
    top = min(r for r, c, x in piece)
    left = min(c for r, c, x in piece)
    return tuple(sorted((r-top, c-left, x) for r, c, x in piece))


def orientations(piece):
    result = []
    current = normalize(piece)
    for _ in range(4):
        if current not in result:
            result.append(current)
        current = normalize([(c, -r, x) for r, c, x in current])
    return tuple(result)


@lru_cache(maxsize=192)
def _unique_assembly(grid, corner):
    cells = [(r,c,x) for r,row in enumerate(grid) for c,x in enumerate(row) if x]
    side = isqrt(len(cells))
    colors = {x for r,c,x in cells} - {5}
    if (side < 2 or side*side != len(cells) or len(colors) != 4 or 7 not in colors or
            sum(x == 5 for r,c,x in cells) != 1):
        raise ValueError('Expected four pieces, exactly one 5 on piece 7, and square total area')
    anchor = [(r,c,x) for r,c,x in cells if x in (5,7)]
    others = [[(r,c,x) for r,c,x in cells if x == color] for color in sorted(colors-{7})]
    prepared = []
    for piece in others:
        choices = []
        for oriented in orientations(piece):
            height = 1+max(r for r,c,x in oriented)
            width = 1+max(c for r,c,x in oriented)
            local_mask = sum(1 << (r*side+c) for r,c,x in oriented)
            choices.append((oriented,height,width,local_mask))
        prepared.append(tuple(choices))
    full = (1 << (side*side))-1
    solutions = {}

    def complete(occupied, remaining, chosen):
        if len(solutions) >= 2:
            return
        if not remaining:
            if occupied == full:
                output = [[0]*side for _ in range(side)]
                for piece in chosen:
                    for r,c,x in piece:
                        output[r][c] = x
                key = tuple(tuple(row) for row in output)
                solutions.setdefault(key, tuple(chosen))
            return
        holes = full ^ occupied
        index = (holes & -holes).bit_length()-1
        row,col = divmod(index,side)
        # Any completion must put exactly one remaining piece over this hole.
        # Align every possible cell to it rather than trusting the latent board.
        for piece_id in remaining:
            rest = tuple(i for i in remaining if i != piece_id)
            for piece,height,width,local_mask in prepared[piece_id]:
                for local_r,local_c,_ in piece:
                    dr,dc = row-local_r,col-local_c
                    if dr < 0 or dc < 0 or dr+height > side or dc+width > side:
                        continue
                    mask = local_mask << (dr*side+dc)
                    if mask & occupied:
                        continue
                    moved = tuple((r+dr,c+dc,x) for r,c,x in piece)
                    complete(occupied|mask,rest,chosen+(moved,))
                    if len(solutions) >= 2:
                        return

    target_col = 0 if corner == 'northwest' else side-1
    for oriented in orientations(anchor):
        mr,mc,_ = next(p for p in oriented if p[2] == 5)
        moved = tuple((r-mr,c-mc+target_col,x) for r,c,x in oriented)
        if any(r < 0 or c < 0 or r >= side or c >= side for r,c,x in moved):
            continue
        occupied = sum(1 << (r*side+c) for r,c,x in moved)
        complete(occupied,tuple(range(3)),(moved,))
        if len(solutions) >= 2:
            break
    if not solutions:
        raise ValueError('No rotation-only reconstruction')
    if len(solutions) != 1:
        raise ValueError('Input has ambiguous rotation-only reconstructions')
    return next(iter(solutions.items()))


def solve(grid, corner='northwest'):
    if type(corner) is not str or corner not in CORNERS:
        raise ValueError('Unknown anchor corner')
    output,_ = _unique_assembly(strict_grid(grid),corner)
    return [list(row) for row in output]


def assemble_details(grid, corner='northwest'):
    if type(corner) is not str or corner not in CORNERS:
        raise ValueError('Unknown anchor corner')
    output,placements = _unique_assembly(strict_grid(grid),corner)
    return {'side':len(output), 'anchor_corner':corner,
            'anchor_cells':[list(p) for p in placements[0]],
            'piece_placements':[[list(p) for p in piece] for piece in placements],
            'output':[list(row) for row in output]}


def _partition(rng, q):
    colors = [7]+rng.sample([1,2,3,4,6,8,9],3)
    side = 2*q
    cut_r,cut_c = q+rng.choice((-1,0,1)),q+rng.choice((-1,0,1))
    board = [[colors[(r >= cut_r)*2+(c >= cut_c)] for c in range(side)] for r in range(side)]
    # Four independent internal seams. One-cell tabs in either direction vary
    # in count, length and orientation; outside corners remain owned by regions.
    for start,stop in ((0,cut_r),(cut_r,side)):
        for r in range(start+1,stop-1):
            delta = rng.choice((-1,0,0,1))
            if delta:
                c = cut_c if delta == 1 else cut_c-1
                board[r][c] = colors[(r >= cut_r)*2+(0 if delta == 1 else 1)]
    for start,stop in ((0,cut_c),(cut_c,side)):
        for c in range(start+1,stop-1):
            delta = rng.choice((-1,0,0,1))
            if delta:
                r = cut_r if delta == 1 else cut_r-1
                board[r][c] = colors[(0 if delta == 1 else 1)*2+(c >= cut_c)]
    board[0][0] = 5
    return board,colors


def _scatter(rng, board, colors, height, width):
    grid = [[0]*width for _ in range(height)]
    middle_r,middle_c = (height-1)//2,(width-1)//2
    slots = [(0,middle_r,0,middle_c),(0,middle_r,middle_c+1,width),
             (middle_r+1,height,0,middle_c),(middle_r+1,height,middle_c+1,width)]
    rng.shuffle(slots)
    for color,(r0,r1,c0,c1) in zip(colors,slots):
        piece = [(r,c,x) for r,row in enumerate(board) for c,x in enumerate(row)
                 if x == color or (color == 7 and x == 5)]
        for _ in range(rng.randrange(4)):
            piece = [(c,-r,x) for r,c,x in piece]
        piece = normalize(piece)
        piece_h = 1+max(r for r,c,x in piece)
        piece_w = 1+max(c for r,c,x in piece)
        dr = rng.randint(r0,r1-piece_h)
        dc = rng.randint(c0,c1-piece_w)
        for r,c,x in piece:
            grid[dr+r][dc+c] = x
    return grid


def generate(seed=0, sample_index=0, difficulty='medium', *, quarter_size=None,
             grid_h=None, grid_w=None):
    integer(seed,'seed')
    integer(sample_index,'sample_index',0)
    if type(difficulty) is not str or difficulty not in ('easy','medium','hard'):
        raise ValueError('difficulty must be easy, medium or hard')
    rng = random.Random(f'jigsaw-7b3084d4:{seed}:{sample_index}')
    if quarter_size is None:
        quarter_size = rng.choice({'easy':(3,4,5),'medium':(4,5,6,7,8),
                                  'hard':(7,8,9,10,11,12)}[difficulty])
    q = integer(quarter_size,'quarter_size',3,12)
    minimum = 2*q+5
    height = rng.randint(minimum,min(30,minimum+4)) if grid_h is None else integer(grid_h,'grid_h',minimum,30)
    width = rng.randint(minimum,min(30,minimum+4)) if grid_w is None else integer(grid_w,'grid_w',minimum,30)
    for _ in range(192):
        board,colors = _partition(rng,q)
        grid = _scatter(rng,board,colors,height,width)
        try:
            reconstructed = solve(grid)
        except ValueError:
            continue
        if reconstructed != board:
            raise AssertionError('Unique reconstruction disagrees with the proposed partition')
        return grid
    raise ValueError('Bounded sampler exhausted unique jigsaw proposals')


def self_check(grid, difficulty='medium'):
    try:
        solve(grid)
    except ValueError as exc:
        return [str(exc)]
    return []
