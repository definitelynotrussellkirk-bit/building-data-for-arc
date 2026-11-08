"""Teaching sampler for ``Turn vertical trios into horizontal trios``.

The canonical Racket program is the sole label authority.  This module samples
inputs that make its exact filter observable: each ordinary grid contains
convertible interior length-3 runs plus one interior length-2 run, one interior
length-4 run, and one edge length-3 run.  The authority writes onto a blank
canvas, so every non-target run disappears rather than being preserved.
"""
from __future__ import annotations

from collections import deque

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "857238219e77"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "fc2cfb863af5"
SUMMARY = (
    "On a blank output, convert only interior vertical monochrome runs of "
    "exactly length 3 into same-colour horizontal trios centered on the old "
    "middle cell; discard short, long, and edge runs."
)
EXAMPLES_NEEDED = 3
INVARIANTS = [
    "background is 0 and all cells are integer colours 0..9",
    "1..5 interior length-3 target runs have pairwise-disjoint outputs",
    "ordinary samples also contain one length-2, one length-4, and one edge trio",
    "2..4 nonzero colours occur and every requested colour is visible",
]
AXES = {
    "grid_h": {"type": "int", "default": "canonical profiles recur; otherwise difficulty-weighted", "valid": "6..15"},
    "grid_w": {"type": "int", "default": "canonical profiles recur; otherwise difficulty-weighted", "valid": "8..17"},
    "target_count": {"type": "int", "default": "difficulty-weighted", "valid": "1..5"},
    "n_distinct_colors": {"type": "int", "default": "2..4", "valid": "2..4"},
    "edge_side": {"type": "str", "default": "left|right", "valid": "left|right"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []

_HEIGHTS = tuple(range(6, 16))
_WIDTHS = tuple(range(8, 18))
_TARGET_COUNTS = tuple(range(1, 6))
_COLOR_COUNTS = (2, 3, 4)
_EDGE_SIDES = ("left", "right")
_CANONICAL_SHAPES = ((7, 9), (6, 10), (8, 8))


def _controls(overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    active = {name: value for name, value in overrides.items() if value is not None}
    for name in ("grid_h", "grid_w", "target_count", "n_distinct_colors"):
        if name in active and type(active[name]) is not int:
            raise TypeError(f"{name} must be an integer (not bool)")
    if "grid_h" in active and active["grid_h"] not in _HEIGHTS:
        raise ValueError("grid_h must be in 6..15")
    if "grid_w" in active and active["grid_w"] not in _WIDTHS:
        raise ValueError("grid_w must be in 8..17")
    if "target_count" in active and active["target_count"] not in _TARGET_COUNTS:
        raise ValueError("target_count must be in 1..5")
    if ("n_distinct_colors" in active
            and active["n_distinct_colors"] not in _COLOR_COUNTS):
        raise ValueError("n_distinct_colors must be in 2..4")
    if "edge_side" in active:
        if type(active["edge_side"]) is not str or active["edge_side"] not in _EDGE_SIDES:
            raise ValueError("edge_side must be 'left' or 'right'")
    return active


def _weighted(values, preferred):
    """Keep the full legal domain while weighting only the default draw."""
    values = list(values)
    return values + [value for value in preferred if value in values] * 4


def _draw_shape(ctx, active, sample_index, difficulty):
    # The first three residues recur the public shape profiles without replaying
    # any public positions or colours.  Explicit dimension controls always win.
    scheduled = _CANONICAL_SHAPES[sample_index % len(_CANONICAL_SHAPES)]
    use_profile = sample_index % 10 < 3 and not ({"grid_h", "grid_w"} & set(active))
    if use_profile:
        return (ctx.draw_choice("grid_h", (scheduled[0],)),
                ctx.draw_choice("grid_w", (scheduled[1],)))
    preferred_h = {
        "easy": range(6, 10), "medium": range(8, 13), "hard": range(11, 16),
    }.get(difficulty, range(7, 13))
    preferred_w = {
        "easy": range(8, 12), "medium": range(10, 15), "hard": range(13, 18),
    }.get(difficulty, range(9, 15))
    return (ctx.draw_choice("grid_h", _weighted(_HEIGHTS, preferred_h)),
            ctx.draw_choice("grid_w", _weighted(_WIDTHS, preferred_w)))


def _placement_cells(item):
    return {(r, item["c"]) for r in range(item["r0"], item["r0"] + item["length"])}


def _target_output_cells(item):
    if item["kind"] != "target":
        return set()
    row = item["r0"] + 1
    return {(row, item["c"] - 1), (row, item["c"]), (row, item["c"] + 1)}


def _place_placements(ctx, h, w, target_count, edge_side):
    """Deterministic backtracking over at most eight small vertical placements."""
    specs = [("long", 4), ("edge", 3)]
    specs += [("target", 3)] * target_count
    specs += [("short", 2)]
    edge_column = 0 if edge_side == "left" else w - 1
    rng = ctx.draw_rng("layout")
    candidate_sets = []
    for kind, length in specs:
        columns = (edge_column,) if kind == "edge" else tuple(range(1, w - 1))
        candidates = [
            {"kind": kind, "length": length, "r0": r0, "c": c}
            for c in columns for r0 in range(h - length + 1)
        ]
        rng.shuffle(candidates)
        candidate_sets.append(candidates)

    occupied = set()
    target_inputs = set()
    target_outputs = set()
    edge_rival_outputs = set()
    chosen = []

    def search(index):
        if index == len(specs):
            return True
        for item in candidate_sets[index]:
            cells = _placement_cells(item)
            r0, c, length = item["r0"], item["c"], item["length"]
            if cells & occupied:
                continue
            # A zero row must separate two runs in one column, irrespective of colour.
            if (r0 - 1, c) in occupied or (r0 + length, c) in occupied:
                continue
            output_cells = _target_output_cells(item)
            if item["kind"] == "target":
                # Target inputs and outputs remain geometrically unambiguous.  A
                # distractor may sit under an output cell because labels are
                # drawn on a fresh blank canvas; that overlap is itself harmless.
                if cells & target_outputs:
                    continue
                if output_cells & (target_outputs | target_inputs | edge_rival_outputs):
                    continue
            edge_output_cells = set()
            if item["kind"] == "edge":
                middle = item["r0"] + 1
                edge_output_cells = {
                    (middle, cc)
                    for cc in range(max(0, item["c"] - 1), min(w, item["c"] + 2))
                }
            occupied.update(cells)
            edge_rival_outputs.update(edge_output_cells)
            if item["kind"] == "target":
                target_inputs.update(cells)
                target_outputs.update(output_cells)
            chosen.append(item)
            if search(index + 1):
                return True
            chosen.pop()
            occupied.difference_update(cells)
            edge_rival_outputs.difference_update(edge_output_cells)
            if item["kind"] == "target":
                target_inputs.difference_update(cells)
                target_outputs.difference_update(output_cells)
        return False

    if not search(0):
        raise RuntimeError(
            f"could not place teaching placements for {h}x{w}, "
            f"targets={target_count}, edge={edge_side}"
        )
    return [dict(item) for item in chosen]


def _horizontal_adjacency_graph(placements):
    cells = [_placement_cells(item) for item in placements]
    graph = [set() for _ in placements]
    for i, left in enumerate(cells):
        for j in range(i + 1, len(cells)):
            right = cells[j]
            if any((r, c - 1) in right or (r, c + 1) in right for r, c in left):
                graph[i].add(j)
                graph[j].add(i)
    return graph


def _colour_placements(ctx, placements, n_colours):
    """Properly colour horizontal contacts and use every selected colour."""
    palette = list(ctx.draw_distinct_colors("palette", n=n_colours, exclude={0}))
    graph = _horizontal_adjacency_graph(placements)
    assignments = [None] * len(placements)

    # The contact graph is bipartite because every edge joins neighbouring
    # columns.  Colour each component, then ensure both base colours are visible.
    for start in range(len(placements)):
        if assignments[start] is not None:
            continue
        assignments[start] = 0
        queue = deque([start])
        while queue:
            node = queue.popleft()
            for neighbor in graph[node]:
                wanted = 1 - assignments[node]
                if assignments[neighbor] is None:
                    assignments[neighbor] = wanted
                    queue.append(neighbor)
                elif assignments[neighbor] != wanted:
                    raise RuntimeError("horizontal contact graph unexpectedly non-bipartite")
    if 1 not in assignments:
        assignments[1] = 1

    # Extra palette colours are each assigned to one vertex.  Recolour only a
    # base class with spare membership so colours 0 and 1 remain represented.
    order = list(range(len(placements)))
    ctx.draw_rng("colour_assignment").shuffle(order)
    for colour_index in range(2, n_colours):
        candidate = next(
            i for i in order
            if assignments.count(assignments[i]) > 1 and assignments[i] < 2
        )
        assignments[candidate] = colour_index
        order.remove(candidate)

    for item, colour_index in zip(placements, assignments):
        item["color"] = palette[colour_index]
    return placements


def generate(seed, sample_index, *, difficulty=None, **overrides):
    active = _controls(overrides)
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=active)
    h, w = _draw_shape(ctx, active, sample_index, difficulty)
    target_preference = {
        "easy": (1, 2), "medium": (2, 3, 4), "hard": (4, 5),
    }.get(difficulty, (2, 3, 4))
    target_count = ctx.draw_choice(
        "target_count", _weighted(_TARGET_COUNTS, target_preference))
    n_colours = ctx.draw_choice(
        "n_distinct_colors", _weighted(_COLOR_COUNTS, (3,)))
    edge_side = ctx.draw_choice("edge_side", _EDGE_SIDES)
    placements = _place_placements(ctx, h, w, target_count, edge_side)
    _colour_placements(ctx, placements, n_colours)
    grid = full_grid(h, w, 0)
    for item in placements:
        for r, c in _placement_cells(item):
            grid[r][c] = item["color"]
    return grid


def _vertical_runs(grid):
    h, w = len(grid), len(grid[0])
    runs = []
    for c in range(w):
        r = 0
        while r < h:
            colour = grid[r][c]
            if colour == 0:
                r += 1
                continue
            end = r + 1
            while end < h and grid[end][c] == colour:
                end += 1
            runs.append({"color": colour, "r0": r, "r1": end - 1,
                         "c": c, "length": end - r})
            r = end
    return runs


def observe_overrides(grid):
    runs = _vertical_runs(grid)
    width = len(grid[0])
    edges = [run for run in runs
             if run["length"] == 3 and run["c"] in (0, width - 1)]
    edge_side = None
    if len(edges) == 1:
        edge_side = "left" if edges[0]["c"] == 0 else "right"
    return {
        "grid_h": len(grid),
        "grid_w": width,
        "target_count": sum(
            run["length"] == 3 and 0 < run["c"] < width - 1 for run in runs),
        "n_distinct_colors": len({value for row in grid for value in row if value}),
        "edge_side": edge_side,
    }


def self_check(grid, *, difficulty=None, meta=None):
    if (not isinstance(grid, (list, tuple)) or not grid
            or not isinstance(grid[0], (list, tuple)) or not grid[0]):
        return ["grid must be nonempty and rectangular"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(type(value) is not int or not 0 <= value <= 9
           for row in grid for value in row):
        return ["cells must be integer colours 0..9 (not booleans)"]
    h, w = len(grid), width
    errors = []
    if h not in _HEIGHTS or w not in _WIDTHS:
        errors.append("dimensions must be grid_h 6..15 and grid_w 8..17")
    colours = {value for row in grid for value in row if value}
    if not 2 <= len(colours) <= 4:
        errors.append("input must use 2..4 nonzero colours")
    # Same-colour horizontal contact would make a non-vertical monochrome object.
    if any(grid[r][c] and grid[r][c] == grid[r][c + 1]
           for r in range(h) for c in range(w - 1)):
        errors.append("same-colour placements must not touch horizontally")
    # Differently-coloured runs must not be packed without a separating zero.
    if any(grid[r][c] and grid[r + 1][c]
           and grid[r][c] != grid[r + 1][c]
           for r in range(h - 1) for c in range(w)):
        errors.append("vertical runs must be separated by background")

    runs = _vertical_runs(grid)
    for run in runs:
        if run["length"] not in (2, 3, 4):
            errors.append(
                f"color {run['color']} run length {run['length']} is outside 2..4")
        if run["c"] in (0, w - 1) and run["length"] != 3:
            errors.append("edge distractors must be length-3 runs")
    targets = [run for run in runs
               if run["length"] == 3 and 0 < run["c"] < w - 1]
    if not 1 <= len(targets) <= 5:
        errors.append(f"expected 1..5 interior length-3 targets, got {len(targets)}")
    edge_runs = [run for run in runs
                 if run["length"] == 3 and run["c"] in (0, w - 1)]
    if len(edge_runs) > 1:
        errors.append("at most one edge trio is allowed")
    if sum(run["length"] == 2 for run in runs) > 1:
        errors.append("at most one length-2 distractor is allowed")
    if sum(run["length"] == 4 for run in runs) > 1:
        errors.append("at most one length-4 distractor is allowed")
    output_cells = []
    for run in targets:
        row = run["r0"] + 1
        output_cells.extend((row, c) for c in range(run["c"] - 1, run["c"] + 2))
    if len(output_cells) != len(set(output_cells)):
        errors.append("target horizontal outputs must not overlap")
    return errors


def strict_canonical_like(grid):
    """Lawful task-domain membership, including generated counterexamples."""
    return self_check(grid)


def _blank(grid):
    return [[0 for _ in row] for row in grid]


def _paint_horizontal(out, row, column, colour):
    for c in range(column - 1, column + 2):
        if 0 <= row < len(out) and 0 <= c < len(out[0]):
            out[row][c] = colour


def _authoritative_shape(grid):
    out = _blank(grid)
    w = len(grid[0])
    for run in _vertical_runs(grid):
        if run["length"] == 3 and 0 < run["c"] < w - 1:
            _paint_horizontal(out, run["r0"] + 1, run["c"], run["color"])
    return out


def _rotate_every_interior_run(grid):
    """RIVAL: ignores the exact-length filter."""
    out = _blank(grid)
    w = len(grid[0])
    for run in _vertical_runs(grid):
        if 0 < run["c"] < w - 1:
            _paint_horizontal(
                out, run["r0"] + run["length"] // 2, run["c"], run["color"])
    return out


def _convert_edge_trios_too(grid):
    """RIVAL: clips and converts length-3 runs even on side edges."""
    out = _blank(grid)
    for run in _vertical_runs(grid):
        if run["length"] == 3:
            _paint_horizontal(out, run["r0"] + 1, run["c"], run["color"])
    return out


def _preserve_non_targets(grid):
    """RIVAL: converts targets but incorrectly copies rejected runs through."""
    out = _authoritative_shape(grid)
    w = len(grid[0])
    for run in _vertical_runs(grid):
        if run["length"] == 3 and 0 < run["c"] < w - 1:
            continue
        for r in range(run["r0"], run["r1"] + 1):
            out[r][run["c"]] = run["color"]
    return out


def _identity(grid):
    return [list(row) for row in grid]


def _has_short(grid):
    w = len(grid[0])
    return any(run["length"] == 2 and 0 < run["c"] < w - 1
               for run in _vertical_runs(grid))


def _has_long(grid):
    w = len(grid[0])
    return any(run["length"] == 4 and 0 < run["c"] < w - 1
               for run in _vertical_runs(grid))


def _has_edge_trio(grid):
    w = len(grid[0])
    return any(run["length"] == 3 and run["c"] in (0, w - 1)
               for run in _vertical_runs(grid))


def _has_discarded_run(grid):
    w = len(grid[0])
    return any(not (run["length"] == 3 and 0 < run["c"] < w - 1)
               for run in _vertical_runs(grid))


SEMANTIC_WITNESSES = {
    "short_run_discarded": _has_short,
    "long_run_discarded": _has_long,
    "edge_trio_discarded": _has_edge_trio,
    "non_targets_not_preserved": _has_discarded_run,
}
SEMANTIC_RIVALS = {
    "rotate_every_interior_run": _rotate_every_interior_run,
    "convert_edge_trios_too": _convert_edge_trios_too,
    "preserve_non_targets": _preserve_non_targets,
}
WITNESS_RIVALS = {
    "short_run_discarded": ["rotate_every_interior_run", "preserve_non_targets"],
    "long_run_discarded": ["rotate_every_interior_run", "preserve_non_targets"],
    "edge_trio_discarded": ["convert_edge_trios_too", "preserve_non_targets"],
    "non_targets_not_preserved": ["preserve_non_targets"],
}
# Every canonical input contains targets only, so these wrong rules reproduce all
# public pairs.  Generated counterexamples are therefore a data requirement.
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = {
    **SEMANTIC_RIVALS,
    "identity": _identity,
}


def lesson_identifiable(demos, query):
    """Finite declared-rival check; [] makes no universal uniqueness claim."""
    reasons = []
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            reasons.append(f"demonstrations do not distinguish declared rival {name}")
    return reasons
