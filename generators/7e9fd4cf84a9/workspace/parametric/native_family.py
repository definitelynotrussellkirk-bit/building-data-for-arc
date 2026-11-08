"""Native two-setting family for 7e9fd4cf84a9.

The input stream is matched across settings.  Step A identifies each holed
green rectangle and derives the selected rectangle set; Step B fills the hole
of every selected rectangle cyan while preserving unrelated distractors.
"""
from __future__ import annotations

from copy import deepcopy
import importlib.util
from pathlib import Path
import random

HERE = Path(__file__).resolve().parent
TASK_HOME = HERE.parents[1]

_SPEC = importlib.util.spec_from_file_location("_arc_7e9fd4cf84a9_base", TASK_HOME / "generator.py")
if _SPEC is None or _SPEC.loader is None:
    raise ImportError("cannot load task generator")
_BASE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_BASE)

SCOPES = ("all_rectangles", "largest_only")
SETTINGS = tuple({"fill_scope": scope} for scope in SCOPES)
RULE_PATHS = {
    "all_rectangles": HERE / "rules/all-rectangles.rkt",
    "largest_only": HERE / "rules/largest-only.rkt",
}
DISTRACTOR_COLORS = (1, 2, 4, 5, 6, 7, 9)
_NORMAL_SHAPES = ((6, 5), (5, 5), (6, 4), (5, 4), (4, 4), (3, 3))
_STRESS_SHAPES = ((9, 8), (8, 8), (9, 7), (8, 7), (7, 6), (6, 5))
_DEMO_LAYOUTS = ((20, 20, 3), (21, 22, 4), (22, 20, 5),
                 (24, 23, 6), (20, 24, 4), (23, 21, 5))
_QUERY_LAYOUTS = ((19, 23, 3), (24, 20, 4), (22, 25, 5), (30, 30, 6))


def _scope(settings) -> str:
    if (type(settings) is not dict or set(settings) != {"fill_scope"}
            or type(settings["fill_scope"]) is not str
            or settings["fill_scope"] not in SCOPES):
        raise ValueError("settings must be exactly fill_scope=all_rectangles or largest_only")
    return settings["fill_scope"]


def program(settings) -> str:
    return RULE_PATHS[_scope(settings)].read_bytes().decode("utf-8")


def _bands(length: int, count: int) -> list[tuple[int, int]]:
    usable = length - 2 - (count - 1)
    base, extra = divmod(usable, count)
    if base < 3:
        raise ValueError("layout too small")
    start = 1
    result = []
    for index in range(count):
        size = base + (1 if index < extra else 0)
        result.append((start, size))
        start += size + 1
    return result


def _scene(seed: int, index: int, *, query: bool) -> list[list[int]]:
    h, w, count = (_QUERY_LAYOUTS if query else _DEMO_LAYOUTS)[index]
    stress = query and index == 3
    shapes = list((_STRESS_SHAPES if stress else _NORMAL_SHAPES)[:count])
    rows = 1 if count <= 3 else 2
    cols = count if rows == 1 else (count + 1) // 2
    slots = [(r, c, bh, bw) for r, bh in _bands(h, rows) for c, bw in _bands(w, cols)][:count]
    rng = random.Random((seed << 24) ^ (0x7E9000 if query else 0x7E1000) ^ index * 10007)
    # The first two demonstrations deliberately place the unique largest
    # rectangle in different row-major positions, defeating a first-object
    # selector. Queries retain seed-dependent placement diversity.
    rotation = rng.randrange(count) if query else (3 * index) % count
    slots = slots[rotation:] + slots[:rotation]
    grid = [[0 for _ in range(w)] for _ in range(h)]
    boxes = []
    for (rh, rw), (band_r, band_c, band_h, band_w) in zip(shapes, slots):
        if rh > band_h or rw > band_w:
            raise RuntimeError("internal layout does not fit")
        r = band_r + rng.randrange(band_h - rh + 1)
        c = band_c + rng.randrange(band_w - rw + 1)
        for rr in range(r, r + rh):
            for cc in range(c, c + rw):
                grid[rr][cc] = 3
        hole = (rng.randrange(r + 1, r + rh - 1), rng.randrange(c + 1, c + rw - 1))
        grid[hole[0]][hole[1]] = 0
        boxes.append((r, c, r + rh - 1, c + rw - 1))

    forbidden = set()
    for r0, c0, r1, c1 in boxes:
        forbidden.update((r, c) for r in range(max(0, r0 - 1), min(h, r1 + 2))
                         for c in range(max(0, c0 - 1), min(w, c1 + 2)))
    candidates = [(r, c) for r in range(h) for c in range(w)
                  if grid[r][c] == 0 and (r, c) not in forbidden]
    rng.shuffle(candidates)
    distractors = 6 if stress else 2 + (index % 4)
    if len(candidates) < distractors:
        raise RuntimeError("internal scene lacks distractor space")
    colors = list(DISTRACTOR_COLORS)
    rng.shuffle(colors)
    for offset, (r, c) in enumerate(candidates[:distractors]):
        grid[r][c] = colors[offset % len(colors)]
    errors = _BASE.self_check(grid)
    if errors:
        raise RuntimeError("native scene failed base contract: " + "; ".join(errors))
    areas = [h0 * w0 for h0, w0 in _BASE.analyze_scene(grid)["rectangle_shapes"]]
    if areas.count(max(areas)) != 1:
        raise RuntimeError("native scene must have a unique largest rectangle")
    return grid


def selected_holes(grid, settings) -> list[tuple[int, int]]:
    scope = _scope(settings)
    rectangles = _BASE.analyze_scene(grid)["rectangles"]
    if not rectangles:
        return []
    if scope == "largest_only":
        maximum = max(item["shape"][0] * item["shape"][1] for item in rectangles)
        rectangles = [item for item in rectangles
                      if item["shape"][0] * item["shape"][1] == maximum]
    return [tuple(hole) for item in rectangles for hole in item["holes"]]


def solve(grid, settings):
    _scope(settings)
    out = deepcopy(grid)
    for r, c in selected_holes(grid, settings):
        out[r][c] = 8
    return out


def rival_outputs(grid, settings):
    """Named finite authoring rivals; not a universal uniqueness claim."""
    scope = _scope(settings)
    analysis = _BASE.analyze_scene(grid)
    holes = [tuple(p) for p in analysis["hole_cells"]]
    out = {
        "other_setting": solve(grid, {"fill_scope": "largest_only" if scope == "all_rectangles" else "all_rectangles"}),
        "identity": deepcopy(grid),
    }
    first = deepcopy(grid)
    if holes:
        first[holes[0][0]][holes[0][1]] = 8
    out["first_rectangle_only"] = first
    erased = solve(grid, settings)
    for r, c, _ in analysis["distractor_cells"]:
        erased[r][c] = 0
    out["erase_distractors"] = erased
    return out


def teaching_survivors(grids, settings):
    survivors = None
    for grid in grids:
        expected = solve(grid, settings)
        fits = {name for name, output in rival_outputs(grid, settings).items() if output == expected}
        survivors = fits if survivors is None else survivors & fits
    return sorted(survivors or ())


def generate(seed, settings, demos=2, queries=4):
    _scope(settings)
    if type(seed) is not int or not 0 <= seed <= 2**63 - 1:
        raise TypeError("seed must be an exact integer in 0..2**63-1")
    if type(demos) is not int or not 2 <= demos <= 6:
        raise ValueError("demos must be an exact integer in 2..6")
    if type(queries) is not int or queries != 4:
        raise ValueError("queries must be exactly 4")
    demo_bank = [_scene(seed, index, query=False) for index in range(6)]
    query_bank = [_scene(seed, index, query=True) for index in range(4)]
    if teaching_survivors(demo_bank[:2], settings):
        raise RuntimeError("two-demo teaching set leaves a declared rival")

    def pair(grid):
        return {"input": deepcopy(grid), "output": solve(grid, settings)}

    return {
        "train": [pair(grid) for grid in demo_bank[:demos]],
        "test": [pair(grid) for grid in query_bank],
        "program_solution": program(settings),
    }
