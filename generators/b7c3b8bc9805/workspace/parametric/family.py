"""Native three-setting frame family; canonical source remains in prototype.py.

The sampler extends only the separate parametric grammar to 30x30. Its three
constructive demonstrations teach both phase axes, numeric cue independence,
row-major cue order, and whether moving a cue changes the controlling marker.
Python labels are claims: native qualification independently executes Racket.
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import random
from functools import lru_cache
from pathlib import Path

from reviewer_support import public_challenge_bytes


TASK_ID = "b7c3b8bc9805"
SETTINGS = ("same", "opposite", "move_then_fill")
DEMO_LIMITS = (3, 6)
QUERY_LIMITS = (1, 4)
_HOME = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("_frame_phase_original_" + hashlib.sha256(str(_HOME).encode()).hexdigest(), _HOME / "prototype.py")
_prototype = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_prototype)


def integer(value, name, low, high):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be a literal integer in {low}..{high}")
    return value


def relation(settings):
    if type(settings) is not dict or set(settings) != {"phase_relation"}:
        raise ValueError("settings must contain exactly phase_relation")
    value = settings["phase_relation"]
    if type(value) is not str or value not in SETTINGS:
        raise ValueError(f"phase_relation must be one of {SETTINGS}")
    return value


@lru_cache(maxsize=1)
def canonical():
    return _prototype.canonical_source()


def _callable(source):
    if not source.startswith("(rule! ") or not source.endswith(")"):
        raise ValueError("expected a complete rule! source")
    return source[len("(rule! "):-1]


# Bounds, marker list and moved grid are computed from this particular input.
# All corner regions in the admitted grammar contain at least four cells.
_MOVE_BINDINGS = """
         (h (rows g)) (w (cols g))
         (gray (find-color g 5))
         (top (apply min (map first gray)))
         (left (apply min (map second gray)))
         (bottom (apply max (map first gray)))
         (right (apply max (map second gray)))
         (markers (for*/list ((r (range 0 h)) (c (range 0 w))
                    #:when (and (not (= (cell-at g r c) 0)) (not (= (cell-at g r c) 5))))
                    (list r c (cell-at g r c))))
         (original-first (first markers))
         (dest-rows (if (< (first original-first) top) (range (+ bottom 1) h) (range 0 top)))
         (dest-cols (if (< (second original-first) left) (range (+ right 1) w) (range 0 left)))
         (destinations (for*/list ((r dest-rows) (c dest-cols)
                         #:when (= (cell-at g r c) 0)) (list r c)))
         (destination (first destinations))
         (moved (grid-from-fn h w (lambda (r c)
                   (cond
                     ((and (= r (first original-first)) (= c (second original-first))) 0)
                     ((and (= r (first destination)) (= c (second destination))) (third original-first))
                     (else (cell-at g r c))))))
"""


def compose_move(fill_program):
    return "(rule! (lambda (g) (let* (" + _MOVE_BINDINGS + ") (" + _callable(fill_program) + " moved))))"


def program(settings):
    mode = relation(settings)
    if mode == "same":
        return canonical()
    if mode == "opposite":
        return _prototype.materialize_rule("opposite", source=canonical())
    return compose_move(canonical())


def stale_order_program():
    """Same marker move, but interior fill wrongly reads the original grid."""
    return ("(rule! (lambda (g) (let* (" + _MOVE_BINDINGS
            + " (stale (" + _callable(canonical()) + " g))) "
            + "(grid-from-fn h w (lambda (r c) "
            + "(if (and (> r top) (< r bottom) (> c left) (< c right)) "
            + "(cell-at stale r c) (cell-at moved r c)))))))")


def analyze(grid):
    if (type(grid) is not list or not 10 <= len(grid) <= 30
            or type(grid[0]) is not list or not 10 <= len(grid[0]) <= 30):
        raise ValueError("native grid must be a 10..30 rectangle")
    h, w = len(grid), len(grid[0])
    if any(type(row) is not list or len(row) != w
           or any(type(c) is not int or not 0 <= c <= 9 for c in row) for row in grid):
        raise ValueError("grid cells must be literal ARC integers")
    gray = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 5]
    if not gray:
        raise ValueError("missing frame")
    top, bottom = min(r for r, c in gray), max(r for r, c in gray)
    left, right = min(c for r, c in gray), max(c for r, c in gray)
    if not (5 <= bottom - top + 1 <= 26 and 5 <= right - left + 1 <= 26
            and top >= 2 and left >= 2 and bottom <= h - 3 and right <= w - 3):
        raise ValueError("frame needs dimensions 5..26 and two-cell exterior margins")
    border = {(r, c) for r in range(top, bottom + 1) for c in range(left, right + 1)
              if r in (top, bottom) or c in (left, right)}
    if set(gray) != border or any(grid[r][c] for r in range(top + 1, bottom) for c in range(left + 1, right)):
        raise ValueError("frame must be complete with a blank interior")
    markers = [(r, c, grid[r][c]) for r in range(h) for c in range(w) if grid[r][c] not in (0, 5)]
    if len(markers) != 2 or markers[0][2] == markers[1][2]:
        raise ValueError("two distinct singleton marker colors are required")
    if any(not ((r < top or r > bottom) and (c < left or c > right)) for r, c, color in markers):
        raise ValueError("markers must lie in exterior corner regions")
    return dict(h=h, w=w, top=top, bottom=bottom, left=left, right=right, markers=markers)


def corner_cells(facts, quadrant):
    rows = range(facts["top"]) if quadrant[0] == "U" else range(facts["bottom"] + 1, facts["h"])
    cols = range(facts["left"]) if quadrant[1] == "L" else range(facts["right"] + 1, facts["w"])
    return [(r, c) for r in rows for c in cols]


def marker_quadrant(marker, facts):
    return ("U" if marker[0] < facts["top"] else "L") + ("L" if marker[1] < facts["left"] else "R")


def move_input(grid):
    facts = analyze(grid)
    marker = facts["markers"][0]
    quadrant = marker_quadrant(marker, facts)
    opposite = ("L" if quadrant[0] == "U" else "U") + ("R" if quadrant[1] == "L" else "L")
    destination = next((r, c) for r, c in corner_cells(facts, opposite) if grid[r][c] == 0)
    moved = copy.deepcopy(grid)
    moved[marker[0]][marker[1]] = 0
    moved[destination[0]][destination[1]] = marker[2]
    return moved


def mirror(grid, mode):
    if mode not in SETTINGS:
        raise ValueError("unknown phase relation")
    base = move_input(grid) if mode == "move_then_fill" else copy.deepcopy(grid)
    facts = analyze(base)
    m1, m2 = facts["markers"]
    quadrant = marker_quadrant(m1, facts)
    phase = (quadrant[0] == "L") ^ (quadrant[1] == "R")
    if mode == "opposite":
        phase = not phase
    # Exact canonical tie convention: the top/left half gets the middle cell.
    rmid = (facts["top"] + facts["bottom"]) // 2
    cmid = (facts["left"] + facts["right"]) // 2
    for r in range(facts["top"] + 1, facts["bottom"]):
        for c in range(facts["left"] + 1, facts["right"]):
            p = (r > rmid) ^ (c > cmid)
            base[r][c] = m1[2] if p == phase else m2[2]
    return base


# (height, width, frame height, frame width, first corner, second corner, rank)
_DEMOS = (
    (10, 12, 5, 6, "UL", "LR", "higher"),
    (10, 12, 5, 6, "UR", "UR", "lower"),
    (13, 15, 7, 7, "LR", "LL", "higher"),
    (16, 20, 9, 12, "UL", "LL", "lower"),
    (21, 23, 15, 13, "LR", "LR", "higher"),
    (24, 26, 18, 19, "UR", "LR", "lower"),
)
_QUERIES = (
    (30, 30, 26, 26, "UL", "UL", "higher"),
    (23, 27, 17, 19, "UR", "LR", "lower"),
    (30, 30, 25, 24, "LL", "LL", "higher"),
    (15, 19, 7, 11, "LR", "LR", "lower"),
)


def _input(seed, split, index):
    profile = (_DEMOS if split == "train" else _QUERIES)[index]
    h, w, fh, fw, q1, q2, rank = profile
    # Neither the episode setting nor requested counts enter this input stream.
    rng = random.Random(f"{TASK_ID}:native-input-v1:{seed}:{split}:{index}")
    top, left = rng.randint(2, h - fh - 2), rng.randint(2, w - fw - 2)
    facts = dict(h=h, w=w, top=top, left=left, bottom=top + fh - 1, right=left + fw - 1)
    grid = [[0] * w for _ in range(h)]
    for r in range(top, top + fh):
        for c in range(left, left + fw):
            if r in (top, top + fh - 1) or c in (left, left + fw - 1):
                grid[r][c] = 5
    c1, c2 = sorted(rng.sample([1, 2, 3, 4, 6, 7, 8, 9], 2), reverse=rank == "higher")
    cells1, cells2 = corner_cells(facts, q1), corner_cells(facts, q2)
    if split == "train" and index == 0:
        p1, p2 = rng.choice(cells1), cells2[0]
    elif split == "train" and index == 1:
        # Crossing row/column order before and after moving the first cue.
        p1, p2 = (0, w - 1), (top - 1, facts["right"] + 1)
    elif split == "train" and index == 2:
        # Opposite cue phases refute borrowing the second cue's phase.
        p1, p2 = (facts["bottom"] + 1, w - 1), (facts["bottom"] + 2, 0)
    elif q1 == q2:
        p1, p2 = sorted(rng.sample(cells1, 2))
    else:
        p1, p2 = rng.choice(cells1), rng.choice(cells2)
        if p1 >= p2:
            p1, p2 = cells1[0], cells2[-1]
    if not p1 < p2:
        raise AssertionError("constructive row-major profile is invalid")
    grid[p1[0]][p1[1]], grid[p2[0]][p2[1]] = c1, c2
    analyze(grid)
    return grid


def generate(seed, settings, demos=3, queries=4):
    integer(seed, "seed", 0, 2**63 - 1)
    mode = relation(settings)
    integer(demos, "demos", *DEMO_LIMITS)
    integer(queries, "queries", *QUERY_LIMITS)
    result = {"train": [], "test": [], "program_solution": program(settings)}
    for split, count in (("train", demos), ("test", queries)):
        for index in range(count):
            grid = _input(seed, split, index)
            result[split].append({"input": grid, "output": mirror(grid, mode)})
    return result


def public_query(episode, query_index):
    """One-turn model projection. Four queries stay in the private controller."""
    integer(query_index, "query_index", 0, len(episode["test"]) - 1)
    visible = {"train": episode["train"], "test": [episode["test"][query_index]]}
    # Reuse the common exact-byte allowlist and strict grid validation.
    import json
    return json.loads(public_challenge_bytes(visible))


def rival_programs(settings):
    """Finite, executable alternatives used by audit_native.py; no uniqueness claim."""
    mode = relation(settings)
    base = program({"phase_relation": "opposite" if mode == "opposite" else "same"})
    phase_site = "(m1p (remainder (+ m1qr m1qc) 2))"
    rivals = {}
    for name, expression in (
        ("always_diagonal", "0"), ("always_off_diagonal", "1"),
        ("row_only", "m1qr"), ("inverted_row_only", "(- 1 m1qr)"),
        ("column_only", "m1qc"), ("inverted_column_only", "(- 1 m1qc)"),
        ("canvas_aspect_phase", "(if (> h w) 1 0)"),
        ("frame_aspect_phase", "(if (> (- fr2 fr1) (- fc2 fc1)) 1 0)"),
    ):
        rivals[name] = base.replace(phase_site, f"(m1p {expression})", 1)
    marker_site = "(m1 (first markers)) (m2 (second markers))"
    for name, selector in (("numeric_minimum_cue", "<"), ("numeric_maximum_cue", ">")):
        rivals[name] = base.replace(marker_site,
            "(m1 (if (" + selector + " (third (first markers)) (third (second markers))) (first markers) (second markers))) "
            "(m2 (if (equal? m1 (first markers)) (second markers) (first markers)))", 1)
    rivals["last_cue"] = base.replace(marker_site, "(m1 (second markers)) (m2 (first markers))", 1)
    rivals["column_major_cue"] = base.replace(marker_site,
        "(m1 (if (< (second (second markers)) (second (first markers))) (second markers) (first markers))) "
        "(m2 (if (equal? m1 (first markers)) (second markers) (first markers)))", 1)
    rivals["second_cue_phase"] = base.replace("(m1qr (if (< (first m1) cr) 0 1))", "(m1qr (if (< (first m2) cr) 0 1))", 1).replace(
        "(m1qc (if (< (second m1) cc) 0 1))", "(m1qc (if (< (second m2) cc) 0 1))", 1)
    for name, expression in (("lower_color_primary", "(min (third m1) (third m2))"),
                             ("higher_color_primary", "(max (third m1) (third m2))")):
        other = expression.replace("(min ", "(max ") if name == "lower_color_primary" else expression.replace("(max ", "(min ")
        site = _prototype.OPPOSITE_PHASE_SITE if mode == "opposite" else _prototype.SAME_PHASE_SITE
        yes, no = (other, expression) if mode == "opposite" else (expression, other)
        rivals[name] = base.replace(site, f"(color (if (= p m1p) {yes} {no}))", 1)
    symmetric = "(remainder (+ (if (< (first m2) cr) 0 1) (if (< (second m2) cc) 0 1)) 2)"
    rivals["symmetric_marker_positions"] = base.replace(phase_site,
        f"(m1p (if (= (remainder (+ m1qr m1qc) 2) {symmetric}) (- 1 (remainder (+ m1qr m1qc) 2)) (remainder (+ m1qr m1qc) 2)))", 1)
    rivals["middle_cell_to_bottom_right"] = base.replace("(quotient (+ ir1 ir2) 2)", "(quotient (- (+ ir1 ir2) 1) 2)", 1).replace("(quotient (+ ic1 ic2) 2)", "(quotient (- (+ ic1 ic2) 1) 2)", 1)
    if mode == "move_then_fill":
        rivals = {name: compose_move(source) for name, source in rivals.items()}
        rivals["stale_marker_order"] = stale_order_program()
        rivals["skip_marker_move"] = canonical()
    return rivals

