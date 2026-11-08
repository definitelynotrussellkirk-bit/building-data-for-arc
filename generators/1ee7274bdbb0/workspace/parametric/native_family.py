"""Native marked-tile turns followed by optional rigid downward settling.

The exact canonical default is retained. Python outputs are claims that the
native worker and the independent task audit verify through protected Racket.
"""
import itertools
from pathlib import Path
import random

TASK_ID = "1ee7274bdbb0"
DEFAULT = {"turn": "cw", "post": "none"}
SETTINGS = tuple({"turn": turn, "post": post}
                 for turn, post in itertools.product(("cw", "ccw"), ("none", "settle_down")))
CANONICAL_ACTION = "(if (> (count-color t 3) 0) (rotate-cw tile) tile)"
CANONICAL_PREFIX = "(rule! (let ((dummy 0))"
SETTLE_DEFINITION = """
 (define (settle-down tile)
   (let* ((th (rows tile)) (tw (cols tile))
          (occupied-rows
            (for*/list ([r (in-range th)] [c (in-range tw)]
                        #:when (= (at tile r c) 8)) r))
          (drop (if (empty? occupied-rows) 0
                    (- th 1 (apply max occupied-rows)))))
     (grid-from-fn th tw
       (lambda (r c)
         (if (>= r drop) (at tile (- r drop) c) 0)))))
"""


def _settings(settings):
    if settings is None:
        return "cw", "none"
    if type(settings) is not dict or set(settings) != {"turn", "post"}:
        raise ValueError("settings must name exactly turn and post")
    turn, post = settings["turn"], settings["post"]
    if type(turn) is not str or turn not in ("cw", "ccw"):
        raise ValueError("turn must be cw or ccw")
    if type(post) is not str or post not in ("none", "settle_down"):
        raise ValueError("post must be none or settle_down")
    return turn, post


def _integer(value, lo, hi, name):
    if type(value) is not int or not lo <= value <= hi:
        raise ValueError(f"{name} must be an exact integer in {lo}..{hi}")


def _segments(length, dividers):
    result = []
    start = 0
    for stop in (*dividers, length):
        if stop <= start:
            raise ValueError("outer or adjacent divider lines are outside the native grammar")
        result.append((start, stop))
        start = stop + 1
    return result


def lattice(grid):
    if (type(grid) is not list or not 3 <= len(grid) <= 30
            or type(grid[0]) is not list or not 3 <= len(grid[0]) <= 30):
        raise ValueError("native grid axes must be 3..30")
    h, w = len(grid), len(grid[0])
    if any(type(row) is not list or len(row) != w or
           any(type(value) is not int or value not in (0, 2, 3, 9) for value in row)
           for row in grid):
        raise ValueError("native input must be rectangular exact colors 0,2,3,9")
    divider_rows = [r for r, row in enumerate(grid) if all(value == 9 for value in row)]
    divider_cols = [c for c in range(w) if all(grid[r][c] == 9 for r in range(h))]
    rows = _segments(h, divider_rows)
    cols = _segments(w, divider_cols)
    sizes = {stop - start for start, stop in rows + cols}
    if len(sizes) != 1 or not 3 <= next(iter(sizes)) <= 30:
        raise ValueError("dividers must delimit uniform square tiles of size 3..30")
    size = next(iter(sizes))
    tiles = []
    for r0, r1 in rows:
        for c0, c1 in cols:
            tile = [row[c0:c1] for row in grid[r0:r1]]
            if any(9 in row for row in tile):
                raise ValueError("stray color9 inside a tile")
            tiles.append((r0, c0, tile))
    return size, divider_rows, divider_cols, tiles


def transform(grid, settings=None):
    turn, post = _settings(settings)
    size, divider_rows, divider_cols, tiles = lattice(grid)
    output = [[9 if r in divider_rows or c in divider_cols else 0
               for c in range(len(grid[0]))] for r in range(len(grid))]
    for r0, c0, tile in tiles:
        motif = {(r, c) for r, row in enumerate(tile) for c, value in enumerate(row) if value == 2}
        marked = any(3 in row for row in tile)
        if marked:
            motif = ({(c, size - 1 - r) for r, c in motif} if turn == "cw"
                     else {(size - 1 - c, r) for r, c in motif})
        if post == "settle_down" and motif:
            drop = size - 1 - max(r for r, c in motif)
            motif = {(r + drop, c) for r, c in motif}
        for r, c in motif:
            output[r0 + r][c0 + c] = 8
    return output


def program(settings=None):
    turn, post = _settings(settings)
    canonical = Path(__file__).with_name("canonical.rkt").read_text()
    if turn == "cw" and post == "none":
        return canonical
    if canonical.count(CANONICAL_ACTION) != 1 or canonical.count(CANONICAL_PREFIX) != 1:
        raise ValueError("selected canonical tile action no longer matches the reviewed source")
    action = f"(if (> (count-color t 3) 0) (rotate-{turn} tile) tile)"
    if post == "settle_down":
        canonical = canonical.replace(CANONICAL_PREFIX, CANONICAL_PREFIX + SETTLE_DEFINITION, 1)
        action = "(settle-down " + action + ")"
    return canonical.replace(CANONICAL_ACTION, action, 1)


CORE_A = (
    (((0, 0), (1, 0), (2, 0), (2, 1)), ()),
    (((0, 1), (1, 1), (2, 1), (2, 2)), ((0, 2),)),
    (((0, 0), (0, 1), (2, 3), (3, 4)), ((2, 2),)),
    (((0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1), (2, 2)), ((0, 4), (4, 4))),
    (((0, 3), (1, 3), (2, 3)), ()),
    (((0, 3), (1, 1), (1, 3), (2, 1), (3, 4)), ((1, 0), (4, 2), (4, 4))),
)
CORE_B = (
    (((0, 0), (0, 1), (1, 0)), ((1, 1),)),
    (((0, 0), (0, 2), (1, 2)), ()),
    (((0, 0), (0, 1), (0, 2), (1, 1)), ((2, 0), (2, 2))),
    (((0, 0), (1, 2), (2, 0)), ((0, 1), (1, 0), (2, 1))),
    (((0, 1), (0, 2), (1, 1), (2, 1)), ((1, 0),)),
    (((0, 0), (0, 1)), ()),
)


def _tile(size, motif, markers):
    motif, markers = set(motif), set(markers)
    if motif & markers or any(not (0 <= r < size and 0 <= c < size) for r, c in motif | markers):
        raise ValueError("constructed tile has overlapping or out-of-bounds roles")
    return [[2 if (r, c) in motif else 3 if (r, c) in markers else 0
             for c in range(size)] for r in range(size)]


def _assemble(tiles, nr, nc, size):
    if len(tiles) != nr * nc:
        raise ValueError("exact tile count required")
    result = [[9] * (nc * (size + 1) - 1) for _ in range(nr * (size + 1) - 1)]
    for index, tile in enumerate(tiles):
        rr, cc = divmod(index, nc)
        for r in range(size):
            result[rr * (size + 1) + r][cc * (size + 1):cc * (size + 1) + size] = tile[r][:]
    return result


def _core(roles, size, rng):
    row_order, col_order = [0, 1], [0, 1, 2]
    rng.shuffle(row_order)
    rng.shuffle(col_order)
    tiles = [_tile(size, *roles[r * 3 + c]) for r in row_order for c in col_order]
    return _assemble(tiles, 2, 3, size)


def _sample_tile(size, index, marker_count, rng):
    cells = [(r, c) for r in range(size) for c in range(size)]
    lo, hi = size * size // 3 + 1, size * size - max(4, size)
    count = rng.randint(lo, hi)
    recipe = index % 4
    if recipe == 0:
        motif = {rng.choice(cells)}
        while len(motif) < count:
            frontier = sorted({(r + dr, c + dc) for r, c in motif
                               for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))
                               if 0 <= r + dr < size and 0 <= c + dc < size} - motif)
            motif.add(rng.choice(frontier))
    elif recipe == 1:
        motif = set(rng.sample(cells, count))
    elif recipe == 2:
        perimeter = [p for p in cells if p[0] in (0, size - 1) or p[1] in (0, size - 1)]
        motif = set(perimeter if len(perimeter) <= size * size - 3
                    else rng.sample(perimeter, size * size - 3))
    else:
        motif = {(r, c) for r, c in cells if c < r}
    if rng.randrange(2):
        motif = {(size - 1 - r, c) for r, c in motif}
    if rng.randrange(2):
        motif = {(r, size - 1 - c) for r, c in motif}
    remaining = sorted(set(cells) - motif)
    markers = rng.sample(remaining, marker_count)
    return _tile(size, motif, markers)


def _field(size, nr, nc, rng, *, offset=0):
    marker_counts = [(index + offset) % 4 for index in range(nr * nc)]
    rng.shuffle(marker_counts)
    tiles = [_sample_tile(size, index + offset, count, rng)
             for index, count in enumerate(marker_counts)]
    return _assemble(tiles, nr, nc, size)


def _large_single(rng, marker_count):
    size = 30
    phase = rng.randrange(7)
    motif = {(r, c) for r in range(27) for c in range(1, 28)
             if (3 * r + 5 * c + phase) % 7 and not (r < 10 and c > 20)}
    markers = [(29, 0), (29, 29), (0, 29)][:marker_count]
    return _tile(size, motif, markers)


def inputs(seed):
    _integer(seed, 0, 2**63 - 1, "seed")
    rng = random.Random(seed ^ 0x71AE5)
    demos = [_core(CORE_A, 5, rng), _core(CORE_B, 3, rng),
             _field(3, 1, 1, rng, offset=1), _field(4, 4, 4, rng),
             _field(9, 3, 3, rng), _large_single(rng, 2)]
    queries = [_field(3, 1, 3, rng, offset=1), _field(5, 3, 2, rng, offset=2),
               _field(6, 4, 4, rng, offset=3), _large_single(rng, 3)]
    random.Random(seed ^ 0x4F0A).shuffle(queries)
    return demos, queries


def generate(seed, settings=None, demos=3, queries=4):
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    chosen = (dict(random.Random(seed ^ 0xA11CE).choice(SETTINGS))
              if settings is None else dict(settings) if type(settings) is dict else settings)
    _settings(chosen)
    train_inputs, test_inputs = inputs(seed)
    def pairs(grids):
        return [{"input": grid, "output": transform(grid, chosen)} for grid in grids]
    return {"train": pairs(train_inputs[:demos]), "test": pairs(test_inputs[:queries]),
            "program_solution": program(chosen), "settings": dict(chosen)}
