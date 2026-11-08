"""Constructive native bar caps and bridges; production generator is separate.

Python labels are deterministic claims. Native qualification and the independent
teaching audit execute the exact programs through protected Racket.
"""
from pathlib import Path
import random

TASK_ID = "1bc09b475319"
DEFAULT = {"cap_mode": "caps"}
SETTINGS = ({"cap_mode": "caps"}, {"cap_mode": "bridge_caps"})

CAP_CONDITION = """(and (= (cell-at g r c) 0)
                   (or (and (< (+ c 2) w)
                            (= (cell-at g r (+ c 1)) 6)
                            (= (cell-at g r (+ c 2)) 6))
                       (and (>= (- c 2) 0)
                            (= (cell-at g r (- c 1)) 6)
                            (= (cell-at g r (- c 2)) 6))))"""

BRIDGE_PROGRAM = """(rule!
  (let* ((new-caps
           (for*/list ([r (in-range h)] [c (in-range w)]
                       #:when CAP_CONDITION)
             (list r c)))
         (capped
           (grid-from-fn h w
             (lambda (r c)
               (if (member (list r c) new-caps) 8 (cell-at g r c)))))
         (old-cyan
           (for*/list ([r (in-range h)] [c (in-range w)]
                       #:when (= (cell-at g r c) 8))
             (list r c)))
         (anchors new-caps)
         (bridges
           (apply append
             (for/list ([c (in-range w)])
               (let ((rows (sort (map first
                                     (filter (lambda (p) (= (second p) c)) anchors)) <)))
                 (apply append
                   (for/list ([i (in-range (max 0 (- (length rows) 1)))])
                     (let ((a (list-ref rows i)) (b (list-ref rows (+ i 1))))
                       (if (for/and ([r (in-range (+ a 1) b)])
                             (= (cell-at capped r c) 0))
                           (for/list ([r (in-range (+ a 1) b)]) (list r c))
                           '())))))))))
    (grid-from-fn h w
      (lambda (r c)
        (if (member (list r c) bridges) 8 (cell-at capped r c))))))""".replace("CAP_CONDITION", CAP_CONDITION)


def _settings(settings):
    if settings is None:
        return "caps"
    if type(settings) is not dict or set(settings) != {"cap_mode"}:
        raise ValueError("settings must contain exactly cap_mode")
    value = settings["cap_mode"]
    if type(value) is not str or value not in ("caps", "bridge_caps"):
        raise ValueError("cap_mode must be caps or bridge_caps")
    return value


def _integer(value, lo, hi, name):
    if type(value) is not int or not lo <= value <= hi:
        raise ValueError(f"{name} must be an exact integer in {lo}..{hi}")


def _grid(grid):
    if type(grid) is not list or not 7 <= len(grid) <= 30:
        raise ValueError("grid height must be 7..30")
    if type(grid[0]) is not list or not 7 <= len(grid[0]) <= 30:
        raise ValueError("grid width must be 7..30")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width or
           any(type(value) is not int or not 0 <= value <= 9 for value in row)
           for row in grid):
        raise ValueError("grid must be rectangular exact-integer colors 0..9")


def _cap_cells(grid):
    width = len(grid[0])
    return [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row)
            if value == 0 and ((c + 2 < width and row[c + 1] == row[c + 2] == 6)
                              or (c >= 2 and row[c - 1] == row[c - 2] == 6))]


def transform(grid, settings=None):
    mode = _settings(settings)
    _grid(grid)
    caps = _cap_cells(grid)
    capped = [row[:] for row in grid]
    for r, c in caps:
        capped[r][c] = 8
    if mode == "caps":
        return capped
    result = [row[:] for row in capped]
    for c in range(len(grid[0])):
        rows = sorted(r for r, column in caps if column == c)
        for top, bottom in zip(rows, rows[1:]):
            if all(capped[r][c] == 0 for r in range(top + 1, bottom)):
                for r in range(top + 1, bottom):
                    result[r][c] = 8
    return result


def program(settings=None):
    if _settings(settings) == "caps":
        return Path(__file__).with_name("canonical.rkt").read_text()
    return BRIDGE_PROGRAM


def _blank(h, w):
    return [[0] * w for _ in range(h)]


def _core_one():
    result = _blank(13, 19)
    for row, start, end in ((1, 1, 4), (7, 6, 8), (4, 0, 1),
                            (10, 10, 11), (10, 15, 17)):
        result[row][start:end + 1] = [6] * (end - start + 1)
    result[2][16] = result[3][16] = 6
    return result


def _core_two():
    result = _blank(15, 23)
    for row, start, end in ((1, 1, 3), (10, 1, 3), (13, 1, 3),
                            (13, 17, 22), (7, 10, 13)):
        result[row][start:end + 1] = [6] * (end - start + 1)
    result[3][12] = result[4][12] = 6
    for r, c in ((1, 19), (10, 19), (7, 4), (7, 9), (5, 0)):
        result[r][c] = 8
    result[5][4] = 2
    result[7][14] = 3
    return result


def _field(h, w, rng, *, double_edge=False):
    """Many separated row runs, aligned caps, old-cyan decoys and blockers."""
    result = _blank(h, w)
    phase = rng.randrange(4)
    for lane in range(w // 7):
        start = 7 * lane + 1
        for index, row in enumerate(range(0, h - 1, 2)):
            length = 2 + ((phase + lane + index) % 4)
            result[row][start:start + length] = [6] * length
    result[-1] = [6] * w
    if double_edge:
        result[0] = [6] * w
    for r, c, value in ((1, w - 1, 8), (h - 3, w - 1, 8),
                         ((h // 2) | 1, 0, 8), ((h // 2) | 1, w // 2, 2),
                         (1, 3, 6), (h - 2 if h % 2 else h - 3, w - 3, 6)):
        if result[r][c] != 0:
            raise ValueError("Constructive field placement unexpectedly overlaps")
        result[r][c] = value
    return result


def _vary(grid, rng, *, shift=False):
    if shift:
        delta = rng.choice((-1, 0, 1))
        result = _blank(len(grid), len(grid[0]))
        for r, row in enumerate(grid):
            for c, value in enumerate(row):
                if value:
                    result[r + delta][c] = value
    else:
        result = [row[:] for row in grid]
    palette = [1, 2, 3, 4, 5, 7, 9]
    rng.shuffle(palette)
    mapping = dict(zip((1, 2, 3, 4, 5, 7, 9), palette))
    result = [[mapping.get(v, v) for v in row] for row in result]
    if rng.randrange(2):
        result.reverse()
    if rng.randrange(2):
        result = [row[::-1] for row in result]
    return result


def inputs(seed):
    _integer(seed, 0, 2**63 - 1, "seed")
    rng = random.Random(seed ^ 0xC4A5019)
    demos = [_vary(_core_one(), rng, shift=True), _vary(_core_two(), rng, shift=True)]
    for h, w in ((7, 7), (18, 22), (24, 27), (30, 30)):
        demos.append(_vary(_field(h, w, rng), rng))
    queries = [_vary(_field(h, w, rng, double_edge=(h == 30)), rng)
               for h, w in ((7, 9), (16, 21), (25, 29), (30, 30))]
    random.Random(seed ^ 0xB61D6E).shuffle(queries)
    return demos, queries


def generate(seed, settings=None, demos=3, queries=4):
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    chosen = (dict(random.Random(seed ^ 0x5E771A6).choice(SETTINGS))
              if settings is None else dict(settings) if type(settings) is dict else settings)
    _settings(chosen)
    demo_inputs, query_inputs = inputs(seed)
    def pairs(grids):
        return [{"input": grid, "output": transform(grid, chosen)} for grid in grids]
    return {"train": pairs(demo_inputs[:demos]), "test": pairs(query_inputs[:queries]),
            "program_solution": program(chosen), "settings": dict(chosen)}
