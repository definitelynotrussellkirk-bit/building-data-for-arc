"""Matched-input symmetry reconstruction and largest recovered object.

Python labels are claims: native qualification/export re-executes exact Racket.
The sampler restricts the recovered patch to a unique largest four-component.
All searches are bounded and fail explicitly rather than emit short lessons.
"""
from __future__ import annotations

from copy import deepcopy
from collections import Counter
from functools import lru_cache
from pathlib import Path
import hashlib
import json
import random

from reviewer_support import find_root, load_selected_generator
from puzzle_generators.rule_wrap import strip_rule_wrapper

TASK_ID = "f283b8535697"
HERE = Path(__file__).resolve().parent
ROOT = find_root(__file__)
CANONICAL = (HERE / "canonical.rkt").read_text()
MODES = ("patch", "largest_object")
MAX_CANDIDATES = 256
DEMO_PROFILES = ((16, 20, "band_v"), (20, 16, "band_h"),
                 (24, 24, "corner"), (12, 16, "band_v"),
                 (28, 20, "band_h"), (30, 30, "corner"))
QUERY_PROFILES = ((24, 24, "corner"), (20, 28, "band_v"),
                  (26, 30, "band_h"), (30, 30, "corner"))


@lru_cache(maxsize=1)
def _base():
    return load_selected_generator(TASK_ID, root=ROOT)[0]


def _integer(value, lo, hi, name):
    if type(value) is not int or not lo <= value <= hi:
        raise ValueError(f"{name} must be an exact integer in {lo}..{hi}")
    return value


def _mode(settings):
    if type(settings) is not dict or set(settings) != {"output_mode"}:
        raise ValueError("settings must name exactly output_mode")
    mode = settings["output_mode"]
    if type(mode) is not str or mode not in MODES:
        raise ValueError("output_mode must be patch or largest_object")
    return mode


def _seed(seed, *parts):
    raw = json.dumps([seed, *parts], separators=(",", ":")).encode()
    return int.from_bytes(hashlib.sha256(raw).digest()[:8], "big") & ((1 << 63) - 1)


def components(patch, *, diagonal=False, multicolor=False):
    """Same-color four-components, in row-major discovery order."""
    h, w = len(patch), len(patch[0])
    seen, result = set(), []
    deltas = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    if diagonal:
        deltas += [(1, 1), (1, -1), (-1, 1), (-1, -1)]
    for r in range(h):
        for c in range(w):
            if not patch[r][c] or (r, c) in seen:
                continue
            todo, cells = [(r, c)], []
            seen.add((r, c))
            while todo:
                y, x = todo.pop()
                cells.append((y, x))
                for dy, dx in deltas:
                    a, b = y + dy, x + dx
                    if (0 <= a < h and 0 <= b < w and (a, b) not in seen
                            and patch[a][b] != 0
                            and (multicolor or patch[a][b] == patch[y][x])):
                        seen.add((a, b))
                        todo.append((a, b))
            result.append(cells)
    return result


def _crop(patch, cells, *, isolate=True):
    if not cells:
        return [[0]]
    r0, r1 = min(r for r, _ in cells), max(r for r, _ in cells)
    c0, c1 = min(c for _, c in cells), max(c for _, c in cells)
    occupied = set(cells)
    return [[patch[r][c] if not isolate or (r, c) in occupied else 0
             for c in range(c0, c1 + 1)] for r in range(r0, r1 + 1)]


def extract_largest(patch):
    items = components(patch)
    return _crop(patch, max(items, key=len)) if items else [[0]]


def reconstructed_patch(grid):
    return _base().rule_mirror(grid)


def predict(grid, mode):
    if mode not in MODES:
        raise ValueError("unknown output mode")
    patch = reconstructed_patch(grid)
    return patch if mode == "patch" else extract_largest(patch)


def validate_input(grid):
    if type(grid) is not list or not grid or any(type(r) is not list for r in grid):
        return ["grid must be a nonempty list of rows"]
    errors = _base().self_check(grid)
    if errors:
        return errors
    sizes = sorted(map(len, components(reconstructed_patch(grid))), reverse=True)
    if not sizes or (len(sizes) > 1 and sizes[0] == sizes[1]):
        return ["recovered patch needs a unique largest foreground component"]
    return []


def _selection_expression(selector):
    if selector == "foreground_bbox":
        return "(crop-to-content p 0)"
    objects = "objects-8" if selector == "largest_8" else (
        "objects-multicolor" if selector == "multicolor_8" else "objects")
    choose = {
        "first_object": "(car os)",
        "last_object": "(nth os (- (length os) 1))",
        "smallest_object": "(pick-min os obj-size)",
        "largest_bbox_area": "(pick-max os (lambda (o) (* (obj-h o) (obj-w o))))",
        "modal_color_largest": (
            "(let* ((colors (remove-duplicates (map obj-color os))) "
            "(color (pick-max colors (lambda (c) (apply + "
            "(map obj-size (filter (lambda (o) (= (obj-color o) c)) os))))))) "
            "(pick-max (filter (lambda (o) (= (obj-color o) color)) os) obj-size))"),
    }.get(selector, "(pick-max os obj-size)")
    cell = "(at p (+ (obj-r1 o) r) (+ (obj-c1 o) c))"
    if selector != "raw_largest_bbox":
        cell = ("(if (member (list (+ (obj-r1 o) r) (+ (obj-c1 o) c)) (obj-cells o)) "
                + cell + " 0)")
    return (f"(let ((os ({objects} p 0))) (if (null? os) '((0)) "
            f"(let ((o {choose})) (build-grid (obj-h o) (obj-w o) (r c) {cell}))))")


def _compose(reconstruction, selector="largest_object"):
    fn = strip_rule_wrapper(reconstruction)
    return ("(rule! (lambda (g) (let ((p (" + fn + " g))) "
            + _selection_expression(selector) + ")))" )


def program(settings):
    mode = _mode(settings)
    return CANONICAL if mode == "patch" else _compose(CANONICAL)


def _mirror_program(kind):
    target = "(get-pixel (+ r1 i) (+ c1 j))"
    expressions = {
        "skip_reconstruction": "(at g (+ r1 i) (+ c1 j))",
        "lr_only": "(at g (+ r1 i) (- w 1 (+ c1 j)))",
        "ud_only": "(at g (- h 1 (+ r1 i)) (+ c1 j))",
        "unflipped_180": "(at g (+ (- h 1 r2) i) (+ (- w 1 c2) j))",
    }
    if kind.endswith("_zero"):
        expression = expressions[kind.replace("_zero", "_only")]
        expression = f"(let ((v {expression})) (if (= v 1) 0 v))"
    else:
        expression = expressions[kind]
    if CANONICAL.count(target) != 1:
        raise ValueError("canonical call site changed; review rival construction")
    return CANONICAL.replace(target, expression)


def rival_programs(mode):
    if mode not in MODES:
        raise ValueError("unknown output mode")
    result = {"other_setting": program({"output_mode": MODES[1 - MODES.index(mode)]})}
    for name in ("skip_reconstruction", "lr_only", "ud_only", "lr_zero", "ud_zero", "unflipped_180"):
        raw = _mirror_program(name)
        result[name] = raw if mode == "patch" else _compose(raw)
    if mode == "largest_object":
        for name in ("first_object", "last_object", "smallest_object", "foreground_bbox",
                     "raw_largest_bbox", "largest_8", "multicolor_8",
                     "modal_color_largest", "largest_bbox_area"):
            result[name] = _compose(CANONICAL, name)
    return result


def _wrong_patch(grid, kind):
    marker = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 1]
    r0, c0 = min(r for r, _ in marker), min(c for _, c in marker)
    h, w = len(grid), len(grid[0])
    out = []
    for i in range(5):
        row = []
        for j in range(5):
            r, c = r0 + i, c0 + j
            if kind.startswith("lr_"):
                c = w - 1 - c
            elif kind.startswith("ud_"):
                r = h - 1 - r
            elif kind == "unflipped_180":
                r, c = h - r0 - 5 + i, w - c0 - 5 + j
            v = grid[r][c]
            row.append(0 if kind.endswith("_zero") and v == 1 else v)
        out.append(row)
    return out


def rival_outputs(grid, mode):
    patch = reconstructed_patch(grid)
    result = {"other_setting": extract_largest(patch) if mode == "patch" else patch}
    for name in ("skip_reconstruction", "lr_only", "ud_only", "lr_zero", "ud_zero", "unflipped_180"):
        p = _wrong_patch(grid, name)
        result[name] = p if mode == "patch" else extract_largest(p)
    if mode == "largest_object":
        items = components(patch)
        result.update(first_object=_crop(patch, items[0]),
                      last_object=_crop(patch, items[-1]),
                      smallest_object=_crop(patch, min(items, key=len)),
                      foreground_bbox=_crop(patch, [x for ob in items for x in ob]),
                      raw_largest_bbox=_crop(patch, max(items, key=len), isolate=False))
        counts = Counter(v for row in patch for v in row if v != 0)
        modal = max(counts, key=counts.get)
        modal_items = [o for o in items if patch[o[0][0]][o[0][1]] == modal]
        result["modal_color_largest"] = _crop(patch, max(modal_items, key=len))
        area = lambda o: ((max(r for r, _ in o) - min(r for r, _ in o) + 1)
                          * (max(c for _, c in o) - min(c for _, c in o) + 1))
        result["largest_bbox_area"] = _crop(patch, max(items, key=area))
        for name, mixed in (("largest_8", False), ("multicolor_8", True)):
            items8 = components(patch, diagonal=True, multicolor=mixed)
            result[name] = _crop(patch, max(items8, key=len))
    return result


def _field(seed, index, h, w, family):
    return _base().generate(_seed(seed, "field", index, h, w, family), 0,
                            grid_h=h, grid_w=w, marker_position=family,
                            n_distinct_colors=3, sym_density=0.45)


def _injected_candidates(seed, index, h, w, family):
    base = _field(seed, index, h, w, family)
    marker = [(r, c) for r, row in enumerate(base) for c, v in enumerate(row) if v == 1]
    orbit_keys = sorted({(min(r, h - 1 - r), min(c, w - 1 - c)) for r, c in marker})
    colors = sorted({v for row in base for v in row} - {0, 1})
    rng = random.Random(_seed(seed, "patch", index, h, w, family))
    for attempt in range(MAX_CANDIDATES):
        g = deepcopy(base)
        palette = rng.sample(colors, len(colors))
        for r, c in orbit_keys:
            v = rng.choices([0, *palette], weights=[4, 3, 2, 1][:1 + len(palette)])[0]
            for y, x in ((r, c), (h - 1 - r, c), (r, w - 1 - c), (h - 1 - r, w - 1 - c)):
                g[y][x] = v
        for r, c in marker:
            g[r][c] = 1
        if validate_input(g):
            continue
        patch = reconstructed_patch(g)
        objects = components(patch)
        if (len(objects) < 2 or max(map(len, objects)) < 3
                or len({v for row in patch for v in row} - {0}) < 2):
            continue
        yield g, attempt + 1


def sample_input(seed, index, h, w, family, *, mixed=True):
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(index, 0, 2**63 - 1, "index")
    for value in (h, w):
        _integer(value, 10, 30, "side")
        if value % 2:
            raise ValueError("sides must be even")
    if family not in ("corner", "band_v", "band_h"):
        raise ValueError("unknown marker family")
    if mixed:
        for grid, _ in _injected_candidates(seed, index, h, w, family):
            return grid
    else:
        for attempt in range(MAX_CANDIDATES):
            grid = _field(_seed(seed, "anchor", attempt), index, h, w, family)
            if not validate_input(grid):
                return grid
    raise RuntimeError("bounded lawful input sampler exhausted")


def _coverage(grid):
    return frozenset((mode, name) for mode in MODES
                     for name, out in rival_outputs(grid, mode).items()
                     if out != predict(grid, mode))


@lru_cache(maxsize=32)
def _teaching_pair(seed):
    goal = frozenset((m, name) for m in MODES for name in rival_programs(m))
    pools = ({}, {})
    streams = [iter(_injected_candidates(seed, i, *DEMO_PROFILES[i])) for i in (0, 1)]
    counts = [0, 0]
    for _ in range(MAX_CANDIDATES):
        progressed = False
        for side in (0, 1):
            try:
                grid, counts[side] = next(streams[side])
            except StopIteration:
                continue
            progressed = True
            covered = _coverage(grid)
            required_mirror = "lr" if side == 0 else "ud"
            required = {(m, required_mirror + tail) for m in MODES for tail in ("_only", "_zero")}
            if not required <= covered:
                continue
            pools[side].setdefault(covered, grid)
            for opposite, other in pools[1 - side].items():
                if covered | opposite == goal:
                    grids = (grid, other) if side == 0 else (other, grid)
                    return grids, tuple(counts)
        if not progressed:
            break
    raise RuntimeError("bounded two-demo rival cover exhausted; no lesson emitted")


def generate(seed, settings, demos=3, queries=4):
    mode = _mode(settings)
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    pair, attempts = _teaching_pair(seed)
    inputs = [deepcopy(grid) for grid in pair]
    for i in range(2, demos):
        inputs.append(sample_input(seed, i, *DEMO_PROFILES[i], mixed=(i != 2)))
    tests = [sample_input(_seed(seed, "queries"), i, *QUERY_PROFILES[i], mixed=(i != 0))
             for i in range(queries)]
    flat = inputs + tests
    if len({json.dumps(g) for g in flat}) != len(flat):
        raise RuntimeError("duplicate input; no lesson emitted")
    pairs = lambda grids: [{"input": g, "output": predict(g, mode)} for g in grids]
    return {"train": pairs(inputs), "test": pairs(tests), "program_solution": program(settings),
            "private_sampling": {"demo_patch_attempts": list(attempts), "candidate_cap_per_band": MAX_CANDIDATES}}
