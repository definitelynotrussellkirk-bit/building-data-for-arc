"""Frame-relative reflection variants with protected Racket labels.

The vertical default is the exact selected canonical source.  The extended
input grammar has two disjoint odd-sided outlines, unique maximum perimeter,
and colored content drawn from compatible fourfold reflection orbits.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
import random

from arcpuzzles import Catalog
from arcpuzzles.parametric_worker import _grid, _real_evaluator

ROOT = Path(__file__).resolve().parents[4]
TASK_ID = "9126300ec565"
AXES = ("vertical", "horizontal", "long_axis")


@lru_cache(maxsize=1)
def canonical_program():
    catalog = Catalog(ROOT)
    selected = catalog.describe(TASK_ID)
    programs = {row["program_solution"] for row in
                catalog._variants()[selected.get("rule_task_id", TASK_ID)]}
    if len(programs) != 1:
        raise ValueError("Expected one selected canonical Racket authority")
    return next(iter(programs))


def _settings(settings):
    if (type(settings) is not dict or set(settings) != {"axis"}
            or type(settings["axis"]) is not str or settings["axis"] not in AXES):
        raise ValueError("settings must contain exactly axis=vertical|horizontal|long_axis")
    return settings["axis"]


def _integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def program(settings):
    axis = _settings(settings)
    return canonical_program() if axis == "vertical" else diagnostic_rule(axis)


def diagnostic_rule(axis, selection="largest", mode="normal"):
    """Executable finite rivals, also the source of the two alternative rules.

    Rivals are private authoring tools, not additional supported settings.
    They are total on the admitted two-frame input grammar.
    """
    if axis not in (*AXES, "short_axis"):
        raise ValueError("Unknown diagnostic axis")
    scores = {
        "largest": "(obj-size a)",
        "smallest": "(- (obj-size a))",
        "largest_area": "(* (+ 1 (- (obj-r2 a) (obj-r1 a))) (+ 1 (- (obj-c2 a) (obj-c1 a))))",
        "first": "(- (+ (* 31 (obj-r1 a)) (obj-c1 a)))",
        "last": "(+ (* 31 (obj-r1 a)) (obj-c1 a))",
    }
    if selection not in scores or mode not in {
        "normal", "canvas_axis", "source_half", "first_color", "exterior",
        "yellow_only", "canonical_colors", "all_frames", "decoy_axis",
        "canvas_orientation", "inverse_canvas_orientation",
    }:
        raise ValueError("Unknown diagnostic selection/mode")
    score_a = scores[selection]
    score_b = score_a.replace(" a)", " b)")
    horizontal = {"vertical": "#f", "horizontal": "#t",
                  "long_axis": "(> (- c2 c1) (- r2 r1))",
                  "short_axis": "(< (- c2 c1) (- r2 r1))"}[axis]
    if mode == "decoy_axis":
        horizontal = "(let ((d (last ordered))) (> (- (obj-c2 d) (obj-c1 d)) (- (obj-r2 d) (obj-r1 d))))"
    elif mode == "canvas_orientation":
        horizontal = "(> (length (first g)) (length g))"
    elif mode == "inverse_canvas_orientation":
        horizontal = "(<= (length (first g)) (length g))"
    row_sum = "(- (length g) 1)" if mode == "canvas_axis" else "(+ r1 r2)"
    col_sum = "(- (length (first g)) 1)" if mode == "canvas_axis" else "(+ c1 c2)"
    rows = "(in-range (length g))" if mode == "exterior" else "(in-range (+ r1 1) r2)"
    cols = "(in-range (length (first g)))" if mode == "exterior" else "(in-range (+ c1 1) c2)"
    bounds = ("(<= 0 mr) (< mr (length g)) (<= 0 mc) (< mc (length (first g)))"
              if mode == "exterior" else "(< r1 mr) (< mr r2) (< c1 mc) (< mc c2)")
    extra = "#t"
    if mode == "source_half":
        extra = "(if horizontal? (< (* 2 r) (+ r1 r2)) (< (* 2 c) (+ c1 c2)))"
    elif mode == "first_color":
        extra = """(not (for*/or ((pr (in-range (+ r1 1) r2))
                                   (pc (in-range (+ c1 1) c2)))
                         (and (or (< pr r) (and (= pr r) (< pc c)))
                              (= (at g pr pc) v))))"""
    elif mode == "yellow_only":
        extra = "(= (obj-color frame) 4)"
    elif mode == "canonical_colors":
        extra = "(member? (obj-color frame) '(4 6 8))"
    finish = ("(for/fold ((out g)) ((f ordered)) (complete f out))"
              if mode == "all_frames" else "(complete (first ordered) g)")
    return f"""(rule!
      (let ()
        (define (outline-cells r1 c1 r2 c2)
          (remove-duplicates
            (append (for/list ((c (in-range c1 (+ c2 1)))) (list r1 c))
                    (for/list ((c (in-range c1 (+ c2 1)))) (list r2 c))
                    (for/list ((r (in-range r1 (+ r2 1)))) (list r c1))
                    (for/list ((r (in-range r1 (+ r2 1)))) (list r c2)))))
        (define (rect-outline? obj)
          (let* ((r1 (obj-r1 obj)) (c1 (obj-c1 obj))
                 (r2 (obj-r2 obj)) (c2 (obj-c2 obj))
                 (cells (obj-cells obj)) (expected (outline-cells r1 c1 r2 c2)))
            (and (>= (- r2 r1) 2) (>= (- c2 c1) 2)
                 (= (length cells) (length expected))
                 (all? (lambda (p) (member? p cells)) expected))))
        (define ordered
          (sort (filter rect-outline? (objects g 0))
                (lambda (a b) (> {score_a} {score_b}))))
        (define (complete frame base)
          (let* ((r1 (obj-r1 frame)) (c1 (obj-c1 frame))
                 (r2 (obj-r2 frame)) (c2 (obj-c2 frame))
                 (horizontal? {horizontal}))
            (for*/fold ((out base)) ((r {rows}) (c {cols}))
              (let* ((v (at g r c))
                     (mr (if horizontal? (- {row_sum} r) r))
                     (mc (if horizontal? c (- {col_sum} c))))
                (if (and (not (= v 0)) (not (= v (obj-color frame)))
                         {bounds} {extra})
                    (set-cell out mr mc v) out)))))
        {finish}))"""


def rivals(axis):
    """Declared executable alternatives; no universal uniqueness claim."""
    _settings({"axis": axis})
    result = {"identity": "(rule! (lambda (g) g))"}
    result.update({f"setting_{a}": program({"axis": a}) for a in AXES})
    for selection in ("smallest", "largest_area", "first", "last"):
        result[f"select_{selection}"] = diagnostic_rule(axis, selection)
    for mode in ("canvas_axis", "source_half", "first_color", "exterior",
                 "yellow_only", "canonical_colors", "all_frames"):
        result[mode] = diagnostic_rule(axis, mode=mode)
    if axis == "long_axis":
        result["short_axis"] = diagnostic_rule("short_axis")
        result["decoy_axis"] = diagnostic_rule(axis, mode="decoy_axis")
        result["canvas_orientation"] = diagnostic_rule(axis, mode="canvas_orientation")
        result["inverse_canvas_orientation"] = diagnostic_rule(axis, mode="inverse_canvas_orientation")
    return result


def _outline(grid, top, left, height, width, color):
    for r in range(top, top + height):
        for c in range(left, left + width):
            if r in (top, top + height - 1) or c in (left, left + width - 1):
                grid[r][c] = color


def _contents(grid, box, colors, rng, dense):
    """One original cell per fourfold orbit; labels are never calculated here."""
    top, left, height, width = box
    cr, cc = top + height // 2, left + width // 2
    orbits = [(dr, dc) for dr in range(1, height // 2)
              for dc in range(1, width // 2)]
    rng.shuffle(orbits)
    count = max(4, int(len(orbits) * (0.80 if dense else 0.65)))
    count = min(len(orbits), count)
    # All four source quadrants occur, including repeated colors.
    for i, (dr, dc) in enumerate(orbits[:count]):
        sr, sc = ((-1, -1), (1, 1), (-1, 1), (1, -1))[i % 4]
        grid[cr + sr * dr][cc + sc * dc] = colors[i % len(colors)]
    # A mark on each symmetry axis is fixed by one setting but moved by another.
    grid[cr - 1][cc] = colors[0]
    grid[cr][cc + 1] = colors[-1]


def _scene(seed, index, profile, transpose, main_first):
    rng = random.Random(f"{TASK_ID}:inputs:v1:{seed}:{index}")
    # (canvas h,w, main h,w, decoy h,w, stacking, density)
    shapes = {
        "selection": (19, 21, 5, 15, 11, 7, True, False),
        "small": (13, 19, 7, 9, 5, 5, False, False),
        "medium": (21, 25, 9, 17, 7, 11, True, False),
        "stress": (30, 30, 13, 27, 13, 15, True, True),
    }
    height, width, mh, mw, dh, dw, stack, dense = shapes[profile]
    if profile == "selection" and index % 2:
        # Same canvas orientation, opposite selected-frame orientations in
        # the two mandatory demos. Canvas aspect cannot stand in for frame aspect.
        height, width = width, height
    grid = [[0] * width for _ in range(height)]
    if stack:
        free = height - mh - dh - 1
        top = (0 if index % 2 == 0 else free) if dense else rng.randrange(free + 1)
        mt, dt = ((top, top + mh + 1) if main_first else (top + dh + 1, top))
        ml = (0 if index % 2 == 0 else width - mw) if dense else rng.randrange(width - mw + 1)
        dl = rng.randrange(width - dw + 1)
        if profile == "selection" and transpose:
            # Transpose exchanges row and column order. Preserve both a first
            # and a last selected-frame demonstration after that exchange.
            ml = 0 if main_first else width - mw
            dl = width - dw if main_first else 0
    else:
        free = width - mw - dw - 1
        left = rng.randrange(free + 1)
        ml, dl = ((left, left + mw + 1) if main_first else (left + dw + 1, left))
        mt, dt = rng.randrange(height - mh + 1), rng.randrange(height - dh + 1)
    # First distinguishing scene always refutes familiar literal-color gates.
    frame_color = rng.choice((1, 2, 3, 5, 7, 9) if index == 0 else tuple(range(1, 10)))
    decoy_color = rng.choice([c for c in range(1, 10) if c != frame_color])
    palette = rng.sample([c for c in range(1, 10) if c not in (frame_color, decoy_color)], 3)
    main, decoy = (mt, ml, mh, mw), (dt, dl, dh, dw)
    for box, color in ((main, frame_color), (decoy, decoy_color)):
        _outline(grid, *box, color)
        _contents(grid, box, palette, rng, dense and box == main)
    # Teach unchanged exterior scope constructively, under BOTH possible axes.
    # Random noise alone can all clip when mirrored and fail to teach scope.
    outside = [(r, c) for r in range(height) for c in range(width)
               if all(not (t <= r < t + h and l <= c < l + w) for t, l, h, w in (main, decoy))]
    outside_set, reserved = set(outside), set()
    for horizontal in (False, True):
        candidates = []
        for r, c in outside:
            partner = (2 * mt + mh - 1 - r, c) if horizontal else (r, 2 * ml + mw - 1 - c)
            if (partner != (r, c) and partner in outside_set
                    and (r, c) not in reserved and partner not in reserved):
                candidates.append(((r, c), partner))
        if candidates:
            source, partner = rng.choice(candidates)
            grid[source[0]][source[1]] = palette[0]
            reserved.update((source, partner))
        elif profile == "selection":
            raise ValueError("Mandatory teaching scene has no exterior mirror witness")
    free_outside = [point for point in outside if point not in reserved]
    for r, c in rng.sample(free_outside, min(3, len(free_outside))):
        grid[r][c] = rng.choice(palette)
    return [list(row) for row in zip(*grid)] if transpose else grid


def inputs(seed, demos=3, queries=4):
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    # Separate fixed indices make prefixes independent of requested counts.
    train = [_scene(seed, i, "selection" if i < 2 else "small",
                    bool((seed + i) % 2), bool(i % 2)) for i in range(demos)]
    profiles = ("small", "medium", "stress", "stress")
    test = [_scene(seed, 100 + i, profiles[i], bool((seed + i) % 2), bool(i % 2))
            for i in range(queries)]
    return train, test


def generate(seed, settings, demos=3, queries=4):
    rule = program(settings)
    train, test = inputs(seed, demos, queries)
    apply, identity, bridge = _real_evaluator(ROOT / "shared/runtime")
    try:
        pairs = [[{"input": grid, "output": _grid(apply(rule, grid))} for grid in grids]
                 for grids in (train, test)]
    finally:
        bridge.close()
    return {"train": pairs[0], "test": pairs[1], "program_solution": rule,
            "settings": dict(settings), "seed": seed, "racket": identity}
