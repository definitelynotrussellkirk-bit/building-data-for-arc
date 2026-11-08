"""Whole-color majority selection followed by left/right mask attachment.

The first two constructive demonstrations teach the declared rule and the
finite shortcuts exposed by rival_programs. Random inputs are independent of
settings, demo count and query count. Labels here are claims: qualification and
verify.py independently execute their exact programs through protected Racket.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import random


HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location(
    "_base_683b2102b08c", HERE.parents[1] / "generator.py"
)
BASE = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(BASE)
CANONICAL = (HERE / "canonical.rkt").read_text(encoding="utf-8")
LEFT_ANCHOR = "(target-c1 (- (+ main-c1 1) sec-w))"
MAIN_MASK = "(main-cells (filter (lambda (cc) (= (third cc) main-color)) cells-below))"
SEC_MASK = "(sec-cells (filter (lambda (cc) (= (third cc) sec-color)) cells-below))"
COLORS = tuple(c for c in range(10) if c not in (4, 7))


def _side(settings):
    if type(settings) is not dict or set(settings) != {"attach_side"}:
        raise ValueError("settings must contain exactly attach_side")
    side = settings["attach_side"]
    if type(side) is not str or side not in ("left", "right"):
        raise ValueError("attach_side must be left or right")
    return side


def _replace(source, old, new):
    if source.count(old) != 1:
        raise ValueError("reference source changed at an expected rule binding")
    return source.replace(old, new, 1)


def program(settings):
    if _side(settings) == "left":
        return CANONICAL
    return _replace(" ".join(CANONICAL.split()), LEFT_ANCHOR, "(target-c1 main-c2)")


def _rng(seed, stream):
    digest = hashlib.sha256(f"683b2102b08c:v1:{seed}:{stream}".encode()).digest()
    return random.Random(int.from_bytes(digest, "big"))


def analyze(grid):
    analysis = BASE._analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    facts = analysis["facts"]
    if any(4 in row for row in grid[facts["line_row"] + 1:]):
        raise ValueError("yellow is reserved for the separator")
    if facts["main_c2"] + facts["secondary_width"] > facts["width"]:
        raise ValueError("right attachment must fit without clipping")
    mr = facts["main_bbox"][0]
    sr, sc = facts["secondary_bbox"][:2]
    main_targets = {(r - mr, c) for r, c in facts["main_cells"]}
    right_targets = {
        (facts["target_secondary_r1"] + r - sr, facts["main_c2"] + c - sc)
        for r, c in facts["secondary_cells"]
    }
    facts["collisions_left"] = facts["collision_count"]
    facts["collisions_right"] = len(main_targets & right_targets)
    return facts


def mirror(grid, settings):
    side = _side(settings)
    f = analyze(grid)
    if side == "left":
        return [row[:] for row in f["output"]]
    out = [[7] * f["width"] for _ in range(f["height"])]
    out[f["line_row"]] = [4] * f["width"]
    for r, c in f["main_cells"]:
        out[r - f["main_bbox"][0]][c] = f["main_color"]
    for r, c in f["secondary_cells"]:
        rr = f["target_secondary_r1"] + r - f["secondary_bbox"][0]
        cc = f["main_c2"] + c - f["secondary_bbox"][1]
        out[rr][cc] = f["secondary_color"]
    return out


def _grid(h, w, line, main, secondary, origins, colors):
    grid = [[7] * w for _ in range(h)]
    grid[line] = [4] * w
    for cells, (rr, cc), color in zip((main, secondary), origins, colors):
        for r, c in cells:
            assert line < rr + r < h and 0 <= cc + c < w
            assert grid[rr + r][cc + c] == 7
            grid[rr + r][cc + c] = color
    analyze(grid)
    return grid


def _teaching(seed, index, palette):
    rng = _rng(seed, f"demo:{index}")
    if index == 0:
        line = rng.randint(6, 8)
        h, w = line + rng.randint(8, 10), rng.randint(16, 20)
        main = {(r, c) for r in (0, 1, 3, 4, 5) for c in (0, 1)}
        secondary = {(0, c) for c in range(5)} | {(r, c) for r in (1, 2) for c in (0, 4)}
        mc = rng.randint(5, w - 6)
        origins = ((line + 1, mc),
                   (rng.randint(line + 2, h - 3), rng.randint(0, mc - 5)))
        colors = (palette[1], palette[0])
    else:
        line = rng.randint(6, 8)
        h, w = line + rng.randint(7, 10), rng.randint(17, 21)
        # Equal heights force count-based selection; the minority appears first
        # and has the larger box, rejecting both stable-height and height/area
        # selectors without increasing the two-demonstration minimum.
        main = {(r, c) for r in range(4) for c in range(3)} - {(2, 2)}
        secondary = {(0, 0), (0, 3), (1, 0), (3, 1), (3, 3)}
        mc = rng.randint(3, w - 9)
        origins = ((rng.randint(line + 2, h - 4), mc), (line + 1, w - 4))
        colors = (palette[0], palette[1])
    return _grid(h, w, line, main, secondary, origins, colors)


def _mask(rng, h, w, count, split=False):
    gap = h // 2 if split and h >= 4 else None
    pool = {(r, c) for r in range(h) for c in range(w) if r != gap}
    required = {(0, 0), (0, w - 1), (h - 1, 0), (h - 1, w - 1)}
    count = min(max(count, len(required)), len(pool))
    return required | set(rng.sample(sorted(pool - required), count - len(required)))


def _place(rng, h, w, line, main, secondary, colors, main_col=None):
    mh, mw = 1 + max(r for r, _ in main), 1 + max(c for _, c in main)
    sh, sw = 1 + max(r for r, _ in secondary), 1 + max(c for _, c in secondary)
    low, high = sw - 1, w - mw - sw + 1
    columns = [c for c in range(low, high + 1) if c >= sw or c + mw + sw <= w]
    mc = rng.choice(columns) if main_col is None else main_col
    positions = list(range(max(0, mc - sw + 1)))
    positions += list(range(mc + mw, w - sw + 1))
    if not positions:
        raise ValueError("no nonoverlapping source placement")
    origins = ((rng.randint(line + 1, h - mh), mc),
               (rng.randint(line + 1, h - sh), rng.choice(positions)))
    return _grid(h, w, line, main, secondary, origins, colors)


def _random_scene(seed, stream, size):
    rng = _rng(seed, stream)
    colors = tuple(rng.sample(COLORS, 2))
    if size == "minimum":
        main = {(r, c) for r in range(3) for c in (0, 2)}
        secondary = {(0, 0), (0, 1)}
        return _place(rng, 8, 8, 3, main, secondary, colors)
    if size == "maximum":
        main = _mask(rng, 14, 9, rng.randint(78, 94), split=True)
        secondary = _mask(rng, 9, 10, rng.randint(40, 65))
        # Either exact output edge is reached; the input masks remain disjoint.
        return _place(rng, 30, 30, 15, main, secondary, colors, rng.choice((9, 12)))
    if size == "large":
        h, w = rng.randint(22, 26), rng.randint(23, 28)
    else:
        h, w = rng.randint(14, 19), rng.randint(16, 21)
    line = (h - 1) // 2
    mh = rng.randint(4, min(9, line, h - line - 1))
    mw = rng.randint(3, min(8, w // 3))
    split = rng.choice((False, True))
    capacity = (mh - int(split)) * mw
    main = _mask(rng, mh, mw, rng.randint(max(6, capacity // 2), capacity), split)
    sh, sw = rng.randint(1, mh), rng.randint(1, min(5, (w - mw + 2) // 2))
    maximum = min(sh * sw, len(main) - 1)
    secondary = _mask(rng, sh, sw, rng.randint(min(4, maximum), maximum))
    return _place(rng, h, w, line, main, secondary, colors)


def generate(seed, settings, demos, queries):
    _side(settings)
    for value, lo, hi, label in ((seed, 0, 2**63 - 1, "seed"),
                                 (demos, 2, 6, "demos"), (queries, 1, 4, "queries")):
        if type(value) is not int or not lo <= value <= hi:
            raise ValueError(f"{label} must be an exact integer in {lo}..{hi}")
    palette = sorted(_rng(seed, "palette").sample(COLORS, 2))
    train_inputs = [_teaching(seed, i, palette) for i in range(min(2, demos))]
    train_inputs += [_random_scene(seed, f"demo:{i}", "medium") for i in range(2, demos)]
    sizes = ("minimum", "medium", "large", "maximum")
    test_inputs = [_random_scene(seed, f"query:{i}", sizes[i]) for i in range(queries)]
    all_inputs = train_inputs + test_inputs
    if len({json.dumps(g, separators=(",", ":")) for g in all_inputs}) != len(all_inputs):
        raise ValueError("bounded sampler produced duplicate visible input")
    def pairs(grids):
        return [{"input": g, "output": mirror(g, settings)} for g in grids]
    return {"train": pairs(train_inputs), "test": pairs(test_inputs),
            "program_solution": program(settings)}


def _largest_component(binding, color):
    return (f"({binding} (map (lambda (p) (list (first p) (second p) {color})) "
            f"(obj-cells (pick-max (filter (lambda (o) (= (obj-color o) {color})) "
            "(objects g 7)) obj-size))))")


def rival_programs(settings):
    """Finite, total-on-grammar alternatives for demonstration-only self-audit."""
    side = _side(settings)
    p = " ".join(program(settings).split())
    anchor = LEFT_ANCHOR if side == "left" else "(target-c1 main-c2)"
    rivals = {"opposite_side": program({"attach_side": "right" if side == "left" else "left"})}
    rivals["disjoint_attachment"] = _replace(p, anchor,
        "(target-c1 (- main-c1 sec-w))" if side == "left" else "(target-c1 (+ main-c2 1))")
    center = "(target-r1 (quotient (- main-h sec-h) 2))"
    for name, expr in (("top_align", "0"), ("bottom_align", "(- main-h sec-h)"),
                       ("ceil_center", "(quotient (+ (- main-h sec-h) 1) 2)"),
                       ("center_in_upper_half", "(quotient (- line-row sec-h) 2)")):
        rivals[name] = _replace(p, center, f"(target-r1 {expr})")
    comparator = "(> (second a) (second b))"
    for name, expr in (("minority_main", "(< (second a) (second b))"),
                       ("lowest_color_main", "(< (first a) (first b))"),
                       ("highest_color_main", "(> (first a) (first b))")):
        rivals[name] = _replace(p, comparator, expr)
    def selected(color):
        return f"(filter (lambda (cc) (= (third cc) (first {color}))) cells-below)"
    def metric(color, kind):
        cs = selected(color)
        if kind == "height":
            return f"(let ((cs {cs})) (+ 1 (- (max-of first cs) (min-of first cs))))"
        if kind == "first":
            return f"(min-of (lambda (cc) (+ (* w (first cc)) (second cc))) {cs})"
        if kind == "bbox":
            return (f"(let ((cs {cs})) (* (+ 1 (- (max-of first cs) (min-of first cs))) "
                    "(+ 1 (- (max-of second cs) (min-of second cs)))))")
        return f"({'min-of' if kind == 'left' else 'max-of'} second {cs})"
    for name, kind, op in (("largest_bbox_main", "bbox", ">"),
                            ("leftmost_main", "left", "<"), ("rightmost_main", "right", ">"),
                            ("tallest_main", "height", ">"),
                            ("first_seen_main", "first", "<"), ("last_seen_main", "first", ">")):
        rivals[name] = _replace(p, comparator, f"({op} {metric('a', kind)} {metric('b', kind)})")
    height_then_bbox = (f"(if (= {metric('a', 'height')} {metric('b', 'height')}) "
                        f"(> {metric('a', 'bbox')} {metric('b', 'bbox')}) "
                        f"(> {metric('a', 'height')} {metric('b', 'height')}))")
    rivals["height_then_bbox_main"] = _replace(p, comparator, height_then_bbox)
    rivals["largest_main_component"] = _replace(p, MAIN_MASK, _largest_component("main-cells", "main-color"))
    rivals["largest_secondary_component"] = _replace(p, SEC_MASK, _largest_component("sec-cells", "sec-color"))
    rivals["main_overwrites_secondary"] = _replace(p, "(set-cell out nr nc sec-color)",
        "(if (= (at g-main nr nc) main-color) out (set-cell out nr nc sec-color))")
    horizontal = _replace(p, "(second cell) main-color)", "(- (+ main-c1 main-c2) (second cell)) main-color)")
    rivals["mirror_masks_horizontally"] = _replace(horizontal, "(nc (+ (second cell) sec-dc))",
        "(nc (+ (- (+ sec-c1 sec-c2) (second cell)) sec-dc))")
    vertical = _replace(p, "(- (first cell) main-r1)", "(- main-r2 (first cell))")
    rivals["mirror_masks_vertically"] = _replace(vertical, "(nr (+ (first cell) sec-dr))",
        "(nr (+ (- (+ sec-r1 sec-r2) (first cell)) sec-dr))")
    return rivals
