"""Native, finitely taught tile-width / input-selected prefix family.

The historical width-only prototype stays intact.  This module reuses its motif
vocabulary and reversal, while adding a full-height count -> endpoint -> prefix
permutation.  Python outputs are claims; native qualification replays them in
protected Racket.  The sampler's grammar extends the canonical strict domain.
"""
from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
import importlib.util
from pathlib import Path


HOME = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location(
    "_tile_width_997c17fd6870_legacy", HOME / "prototype.py"
)
_legacy = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_legacy)

SETTINGS = tuple(
    {"tile_width": width, "order_mode": mode}
    for width in (2, 3) for mode in ("reverse", "densest_prefix")
)
DEFAULT = {"tile_width": 2, "order_mode": "reverse"}
EXTRA_SELECTORS = (
    "top_row", "bottom_row", "rightmost", "band_count", "value_sum",
    "fixed_second", "fixed_middle", "exclude_pivot", "suffix",
)


def _settings(settings):
    if (type(settings) is not dict or set(settings) != set(DEFAULT)
            or type(settings["tile_width"]) is not int
            or settings["tile_width"] not in (2, 3)
            or type(settings["order_mode"]) is not str
            or settings["order_mode"] not in ("reverse", "densest_prefix")):
        raise ValueError("settings require tile_width=2|3 and order_mode=reverse|densest_prefix")
    return settings["tile_width"], settings["order_mode"]


def _integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be a literal integer in {low}..{high}")
    return value


def _grid(grid, width):
    _integer(width, 2, 3, "tile_width")
    if (type(grid) is not list or not 1 <= len(grid) <= 30
            or type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30):
        raise ValueError("grid dimensions must lie in 1..30")
    columns = len(grid[0])
    if columns % width or any(
        type(row) is not list or len(row) != columns
        or any(type(v) is not int or not 0 <= v <= 9 for v in row)
        for row in grid
    ):
        raise ValueError("grid must be rectangular, literal ARC colors, and tile-divisible")
    return len(grid), columns


def tile_scores(grid, tile_width):
    """Count literal nonzero cells in each full-height tile, left to right."""
    height, columns = _grid(grid, tile_width)
    return [sum(grid[r][c] != 0 for r in range(height)
                for c in range(start, start + tile_width))
            for start in range(0, columns, tile_width)]


def _scores(grid, width, selector):
    if selector in ("top_row", "bottom_row"):
        return tile_scores([grid[0 if selector == "top_row" else -1]], width)
    if selector == "value_sum":
        return [sum(row[c] for row in grid for c in range(s, s + width))
                for s in range(0, len(grid[0]), width)]
    if selector == "band_count":
        return [sum(any(grid[r][c] for r in range(band, min(band + 2, len(grid)))
                        for c in range(s, s + width))
                    for band in range(0, len(grid), 2))
                for s in range(0, len(grid[0]), width)]
    return tile_scores(grid, width)


def _transform(grid, width, selector):
    _, columns = _grid(grid, width)
    count = columns // width
    if selector == "identity":
        return deepcopy(grid)
    if selector == "reflect":
        return [row[::-1] for row in grid]
    if selector == "inside_reflect":
        return [[v for s in range(0, columns, width) for v in row[s:s + width][::-1]]
                for row in grid]
    scores = _scores(grid, width, selector)
    pivot = max(range(count), key=lambda i: (scores[i], i if selector == "rightmost" else -i))
    if selector == "fixed_second":
        pivot = min(1, count - 1)
    elif selector == "fixed_middle":
        pivot = count // 2
    elif selector == "exclude_pivot":
        pivot -= 1
    order = list(range(count))
    if selector == "suffix":
        order[pivot:] = reversed(order[pivot:])
    else:
        order[:pivot + 1] = reversed(order[:pivot + 1])
    return [[v for i in order for v in row[width * i:width * (i + 1)]] for row in grid]


def reference(grid, settings):
    """Independent Python claim; native protected Racket is label authority."""
    width, mode = _settings(settings)
    _grid(grid, width)
    if mode == "reverse":
        return _legacy.python_reference(grid, tile_width=width)
    return _transform(grid, width, "count")


def _prefix_program(width, selector="count"):
    score = "(for*/sum ([r (in-range h)] [c (in-range s (+ s k))]) (if (zero? (at g r c)) 0 1))"
    if selector in ("top_row", "bottom_row"):
        row = "0" if selector == "top_row" else "(- h 1)"
        score = f"(for/sum ([c (in-range s (+ s k))]) (if (zero? (at g {row} c)) 0 1))"
    elif selector == "value_sum":
        score = "(for*/sum ([r (in-range h)] [c (in-range s (+ s k))]) (at g r c))"
    elif selector == "band_count":
        score = "(for/sum ([r (in-range 0 h 2)]) (if (for*/or ([rr (in-range r (min h (+ r 2)))] [c (in-range s (+ s k))]) (not (zero? (at g rr c)))) 1 0))"
    compare = ">=" if selector == "rightmost" else ">"
    pivot = f"(for/fold ([best 0]) ([i (in-range 1 n)]) (if ({compare} (list-ref scores i) (list-ref scores best)) i best))"
    if selector == "fixed_second":
        pivot = "(min 1 (- n 1))"
    elif selector == "fixed_middle":
        pivot = "(quotient n 2)"
    elif selector == "exclude_pivot":
        pivot = f"(- {pivot} 1)"
    source = "(if (<= j p) (- p j) j)"
    if selector == "suffix":
        source = "(if (>= j p) (- (+ (- n 1) p) j) j)"
    return f"""(lambda (g)
  (let* ([h (rows g)] [w (cols g)] [k {width}] [n (quotient w k)]
         [scores (for/list ([s (in-range 0 w k)]) {score})]
         [p {pivot}])
    (cellmap g (r c v)
      (let* ([j (quotient c k)] [offset (remainder c k)] [source {source}])
        (at g r (+ (* source k) offset))))))"""


def program(settings):
    width, mode = _settings(settings)
    if settings == DEFAULT:
        return (HOME / "canonical.rkt").read_text(encoding="utf-8")
    if mode == "reverse":
        return "(rule! " + _legacy.racket_program({"tile_width": width}) + ")"
    return "(rule! " + _prefix_program(width) + ")"


def rivals(settings):
    """Finite named hypotheses used by both teaching selection and replay audit."""
    _settings(settings)
    names = [f"setting:{s['tile_width']}:{s['order_mode']}" for s in SETTINGS if s != settings]
    names += ["identity", "reflect", "inside_reflect"]
    if settings["order_mode"] == "densest_prefix":
        names += list(EXTRA_SELECTORS)
    return tuple(names)


def rival_reference(grid, settings, name):
    width, _ = _settings(settings)
    if name not in rivals(settings):
        raise ValueError("undeclared rival")
    if name.startswith("setting:"):
        _, k, mode = name.split(":")
        return reference(grid, {"tile_width": int(k), "order_mode": mode})
    return _transform(grid, width, name)


def rival_program(settings, name):
    width, _ = _settings(settings)
    if name not in rivals(settings):
        raise ValueError("undeclared rival")
    if name.startswith("setting:"):
        _, k, mode = name.split(":")
        return program({"tile_width": int(k), "order_mode": mode})
    if name == "identity":
        return "(rule! (lambda (g) g))"
    if name == "reflect":
        return "(rule! (lambda (g) (cellmap g (r c v) (at g r (- (- (cols g) 1) c)))))"
    if name == "inside_reflect":
        return f"(rule! (lambda (g) (cellmap g (r c v) (at g r (+ (* (quotient c {width}) {width}) (- (- {width} 1) (remainder c {width})))))))"
    return "(rule! " + _prefix_program(width, name) + ")"


def _scene(seed, role, index, height, columns, kind="spread"):
    rng = _legacy.stable_rng(seed, f"997c17fd6870|native-v2|{role}|{index}", "2.0.0")
    colors = rng.sample(range(1, 10), 2)
    rows, cols = height // 2, columns // 2
    quotas = [rng.randint(max(1, rows // 4), max(1, rows - 1)) for _ in range(cols)]
    peak = decoy = None
    if kind == "tie":
        # Whole motifs give identical per-column occupancy.  Both width2 and
        # width3 have interior maximum ties, independent of colors/positions.
        quotas = [1, 1, rows - 2, rows - 2, 1, 1]
    elif kind == "count_decoy":
        peak, decoy = rng.sample(list(range(1, cols - 1)), 2)
        high = max(4, rows - 2)
        quotas = [rng.randint(1, max(1, high - 2)) for _ in range(cols)]
        quotas[peak], quotas[decoy] = high, min(rows, high + 1)
    grid = [[0] * columns for _ in range(height)]
    for col, quota in enumerate(quotas):
        positions = rng.sample(range(rows), quota)
        # Real content reaches upper/lower boundaries; no padded small scene.
        if col == 0 and 0 not in positions:
            positions[0] = 0
        if col == cols - 1 and rows - 1 not in positions:
            positions[-1] = rows - 1
        if col == peak and quota < rows:
            positions = rng.sample(range(1, rows), quota)
        if col == decoy and 0 not in positions:
            positions[0] = 0
        for row in positions:
            choices = ("hook", "checker", "corner", "gap")
            if kind == "tie" or col == peak:
                choices = ("hook", "checker")
            elif col == decoy:
                choices = ("corner", "gap")
            a, b = colors if rng.randrange(2) else colors[::-1]
            motif = _legacy._motif(rng.choice(choices), a, b)
            _legacy._paint_motif(grid, row, col, motif)
    return grid


_HYPOTHESES = tuple((s, name) for s in SETTINGS for name in rivals(s))
_SETTING_BITS = sum(1 << i for i, (_, name) in enumerate(_HYPOTHESES) if name.startswith("setting:"))


def _coverage(grid):
    answers = {(s["tile_width"], s["order_mode"]): reference(grid, s) for s in SETTINGS}
    return sum(1 << i for i, (s, name) in enumerate(_HYPOTHESES)
               if rival_reference(grid, s, name) != answers[(s["tile_width"], s["order_mode"])])


def _frozen(grid):
    return tuple(map(tuple, grid))


@lru_cache(maxsize=16)
def _lesson(seed):
    query_shapes = ((6, 6), (12, 18), (24, 24), (30, 30))
    queries = [_scene(seed, "query", i, h, w) for i, (h, w) in enumerate(query_shapes)]
    required = _SETTING_BITS
    for grid in queries:
        required |= _coverage(grid)
    candidates, masks, selected = [], [], None
    seen = {_frozen(g) for g in queries}
    for i in range(48):
        if i % 4 == 0:
            h, w, kind = (12, 18, 24)[(i // 4) % 3], 12, "tie"
        elif i % 4 == 1:
            h, w, kind = (16, 20, 24)[(i // 4) % 3], (18, 24)[(i // 4) % 2], "count_decoy"
        else:
            h, w, kind = (12, 18, 24)[i % 3], (12, 18, 24)[(i // 3) % 3], "spread"
        grid = _scene(seed, "demo-candidate", i, h, w, kind)
        key = _frozen(grid)
        if key in seen:
            continue
        seen.add(key)
        mask = _coverage(grid)
        for j, previous in enumerate(masks):
            if (previous | mask) & required == required:
                selected = (j, len(candidates))
                break
        candidates.append(grid)
        masks.append(mask)
        if selected is not None:
            break
    if selected is None:
        raise RuntimeError("48-candidate budget cannot teach all query-relevant declared rivals with two demos")
    demos = [candidates[i] for i in selected]
    for grid in candidates:
        if _frozen(grid) not in {_frozen(g) for g in demos}:
            demos.append(grid)
        if len(demos) == 6:
            break
    extra = 0
    while len(demos) < 6:
        h, w = ((12, 18), (18, 24), (24, 18), (30, 30))[extra % 4]
        grid = _scene(seed, "extra-demo", extra, h, w)
        extra += 1
        if _frozen(grid) not in seen:
            seen.add(_frozen(grid))
            demos.append(grid)
        if extra > 12:
            raise RuntimeError("extra-demo distinctness budget exhausted")
    return demos, queries, {"candidate_count": len(candidates), "selected_demo_indices": list(selected),
                           "declared_setting_rival_pairs": len(_HYPOTHESES),
                           "required_distinctions": required.bit_count(), "two_demo_cover": True}


def generate(seed, settings, demos=3, queries=4):
    """Matched deterministic lessons; 2..6 demos and independent 1..4 queries.

    Always plan all four controller queries.  Requests for fewer return a prefix,
    so an evaluation stopped after one answer has identical first-turn bytes.
    """
    _settings(settings)
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    demo_inputs, query_inputs, sampling = _lesson(seed)
    def pairs(inputs):
        return [{"input": deepcopy(g), "output": reference(g, settings)} for g in inputs]
    return {"train": pairs(demo_inputs[:demos]), "test": pairs(query_inputs[:queries]),
            "program_solution": program(settings), "settings": deepcopy(settings),
            "sampling": deepcopy(sampling)}
