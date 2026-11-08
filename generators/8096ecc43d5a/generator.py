"""Input sampler for Apply the Transform Script.

Read row-0 codes left to right and compose them on ONE cropped motif:
1 = clockwise quarter-turn, 2 = left/right reflection, 3 = half-turn,
4 = up/down reflection. Only the unchanged Racket authority supplies labels.
The Python transforms below are authoring rivals and witness diagnostics.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "8096ecc43d5a"
TASK_ID = "8096ecc43d5a"
VERSION = "3.0.0"
RULE_HASH = "04788c0240d6"
SUMMARY = (
    "Sequentially apply row-0 transform codes to the cropped connected, "
    "monochrome motif below a blank separator. Codes 1/2/3/4 mean clockwise "
    "quarter-turn / left-right reflection / half-turn / up-down reflection. "
    "Return one final crop. Code order and multiplicity matter; zero gaps "
    "are ignored. Motif color has no instruction meaning."
)
INVARIANTS = [
    "integer colors 0..9; background 0; row 1 is a blank separator",
    "row 0 contains 1..6 instruction cells from 1..4; zeros are ignored",
    "one four-connected monochrome motif of 3..12 cells lies below row 1",
    "motif colors 1..9 may overlap instruction colors; positions vary",
    "default four-pair windows contain singleton, two rich scripts, and a free script",
]
AXES = {
    "grid_h": {"type": "int", "default": "canonical-weighted 7..14", "valid": "7..14"},
    "grid_w": {"type": "int", "default": "canonical-weighted 8..16", "valid": "8..16"},
    "n_codes": {"type": "int", "default": "scheduled 1..6", "valid": "1..6"},
    "motif_color": {"type": "int", "default": "uniform 1..9", "valid": "1..9"},
    "motif_size": {"type": "int", "default": "5 favored; 3..12", "valid": "3..12"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
LESSON_SCHEDULE_PERIOD = 4
SCHEDULE_PROFILES = ("singleton", "rich_a", "rich_b", "free")
MIN_STRICT_FRAC = 1.0

# Masks refer to the three alternate code maps in _ALTERNATE_MAPS order.
# Every rich word also refutes sorting, deduplication, first/last-only,
# reverse order, ignore-script, first-three-only, and adjacent-collapse.
# These are input words, not precomputed output grids. The task-local
# workspace/analyze_script_maps.py independently regenerates their properties.
_RICH_WORDS = {
    3: ((3, 4, 1, 1, 1), (2, 2, 3, 4, 1)),
    5: ((2, 2, 4, 1), (4, 1, 1, 1),
        (1, 1, 1, 1, 4, 1), (1, 1, 2, 1, 2, 4)),
    6: ((2, 1, 1, 1), (2, 1, 3, 3),
        (1, 1, 2, 1, 3, 3), (1, 1, 1, 1, 2, 1)),
}
_ALTERNATE_MAPS = {
    "map_cw_v_id_h": (1, 4, 0, 2),
    "map_ccw_h_id_h": (5, 2, 0, 2),
    "map_ccw_v_180_v": (5, 4, 3, 4),
}


def _schedule(seed, difficulty=None):
    # Fixed across the entire seed, including windows crossing a period boundary.
    ctx = gen_ctx(seed=seed, sample_index=0, version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty)
    return ctx.draw_int("lesson_offset", 0, 3), ctx.draw_int("singleton_instruction", 1, 4)


def schedule_profile(seed, sample_index, difficulty=None):
    offset, _ = _schedule(seed, difficulty)
    return SCHEDULE_PROFILES[(sample_index + offset) % LESSON_SCHEDULE_PERIOD]


def _normalize(cells):
    r0, c0 = min(r for r, _ in cells), min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def _orbit_size(cells):
    shapes = set()
    for _ in range(4):
        shapes.add(_normalize(cells))
        shapes.add(_normalize([(r, -c) for r, c in cells]))
        cells = [(c, -r) for r, c in cells]
    return len(shapes)


def _motif_cells(rng, size, height, width, asymmetric):
    for _ in range(128):
        cells = {(0, 0)}
        for _ in range(size - 1):
            frontier = {(r + dr, c + dc) for r, c in cells
                        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))} - cells
            cells.add(rng.choice(sorted(frontier)))
        normalized = _normalize(cells)
        if (max(r for r, _ in normalized) < height
                and max(c for _, c in normalized) < width
                and (not asymmetric or _orbit_size(normalized) == 8)):
            return normalized
    # Constructive finite fallback: every size fits within 4x4 and each
    # size >=4 has eight distinct orientations. It cannot shorten a request.
    path = ((0, 0), (1, 0), (2, 0), (2, 1), (1, 1), (3, 0),
            (3, 1), (3, 2), (2, 2), (1, 2), (0, 1), (3, 3))
    if size == 6:
        return _normalize(path[:5] + ((1, 2),))
    return _normalize(path[:size])


def _weighted(ctx, name, lo, hi, favored):
    # The entire exact override domain stays legal in every difficulty band.
    return ctx.draw_choice(name, tuple(range(lo, hi + 1)) + tuple(favored))


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if type(seed) is not int:
        raise ValueError("seed must be an integer (not bool)")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer (not bool)")
    if difficulty is not None and (type(difficulty) is not str or difficulty not in ("easy", "medium", "hard")):
        raise ValueError("difficulty must be None, easy, medium, or hard")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is not None and type(value) is not int:
            raise ValueError(f"{name} must be an integer, not {type(value).__name__}")
    offset, singleton = _schedule(seed, difficulty)
    role = SCHEDULE_PROFILES[(sample_index + offset) % LESSON_SCHEDULE_PERIOD]
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    scripted = overrides.get("n_codes") is None
    word_rng = ctx.draw_rng("instruction_word")
    if scripted and role == "singleton":
        codes = [singleton]
    elif scripted and role in ("rich_a", "rich_b"):
        singleton_mask = {1: 3, 2: 5, 3: 6, 4: 6}[singleton]
        other_masks = [mask for mask in (3, 5, 6) if mask != singleton_mask]
        mask = other_masks[role == "rich_b"]
        codes = list(word_rng.choice(_RICH_WORDS[mask]))
    else:
        favored = (1, 2, 2, 3) if difficulty == "easy" else (
            (4, 5, 6, 6) if difficulty == "hard" else (2, 3, 4))
        count = _weighted(ctx, "n_codes", 1, 6, favored)
        codes = [word_rng.randint(1, 4) for _ in range(count)]
    if scripted and role != "free":
        ctx.draw_choice("n_codes", (len(codes),))

    color = ctx.draw_int_strict("motif_color", 1, 9)
    palette_count = len(set(codes) | {0, color})
    core = ctx.draw_choice("shape_profile", ("core", "core", "broad")) == "core"
    profiles = {3: ((8, 8),), 4: ((8, 9), (9, 9)), 5: ((9, 10),)}
    anchor = ctx.draw_rng("canonical_profile").choice(profiles.get(palette_count, ((9, 10),)))
    h = _weighted(ctx, "grid_h", 7, 14, [anchor[0]] * 100 if core else ())
    w = _weighted(ctx, "grid_w", 8, 16, [anchor[1]] * 100 if core else ())

    asymmetric = scripted and role != "free" and overrides.get("motif_size") is None
    low = 4 if asymmetric else 3
    favored_size = [5] * 30 if core else ([4, 5, 6] if difficulty == "easy" else
                    [8, 9, 10, 11, 12] if difficulty == "hard" else [5, 6, 7])
    size = _weighted(ctx, "motif_size", low, 12, favored_size)
    cells = _motif_cells(ctx.draw_rng("motif_growth"), size, h - 2, w, asymmetric)
    mh, mw = max(r for r, _ in cells) + 1, max(c for _, c in cells) + 1
    place_rng = ctx.draw_rng("motif_position")
    r0, c0 = place_rng.randint(2, h - mh), place_rng.randint(0, w - mw)
    grid = full_grid(h, w, 0)
    for r, c in cells:
        grid[r0 + r][c0 + c] = color

    # Rich rows include leading padding; zeros anywhere are separators, not HALT.
    first_column = 1 if scripted and role in ("rich_a", "rich_b") else 0
    cols = sorted(ctx.draw_rng("instruction_positions").sample(range(first_column, w), len(codes)))
    for column, code in zip(cols, codes):
        grid[0][column] = code
    return grid


def self_check(grid, *, difficulty=None, meta=None):
    if not isinstance(grid, (list, tuple)) or not grid or not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected a nonempty rectangular grid"]
    if any(not isinstance(row, (list, tuple)) or len(row) != len(grid[0]) for row in grid):
        return ["ragged grid"]
    if not 3 <= len(grid) <= 30 or not 1 <= len(grid[0]) <= 30:
        return ["grid outside the 3..30 by 1..30 validator domain"]
    if any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row):
        return ["cells must be integer colors 0..9 (not bool)"]
    errors = []
    codes = [v for v in grid[0] if v]
    if not 1 <= len(codes) <= 6:
        errors.append("row 0 must contain 1..6 instruction cells")
    if any(v not in (1, 2, 3, 4) for v in codes):
        errors.append("instruction colors must be 1..4")
    if any(grid[1]):
        errors.append("row 1 must be a blank separator")
    cells = {(r, c) for r in range(2, len(grid)) for c, v in enumerate(grid[r]) if v}
    if not 3 <= len(cells) <= 12:
        errors.append("motif must contain 3..12 nonzero cells")
    if len({grid[r][c] for r, c in cells}) != 1:
        errors.append("motif must be nonempty and monochrome")
    if cells:
        reached = {min(cells)}
        todo = list(reached)
        while todo:
            r, c = todo.pop()
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                neighbor = (r + dr, c + dc)
                if neighbor in cells and neighbor not in reached:
                    reached.add(neighbor)
                    todo.append(neighbor)
        if reached != cells:
            errors.append("motif must be four-connected")
    return errors


def strict_canonical_like(grid):
    """The declared semantic manifold; coarse canonical support is checked separately."""
    return self_check(grid)


def observe_overrides(grid):
    colors = [v for row in grid[2:] for v in row if v]
    return {"grid_h": len(grid), "grid_w": len(grid[0]),
            "n_codes": sum(v != 0 for v in grid[0]),
            "motif_color": colors[0], "motif_size": len(colors)}


def _body(grid):
    cells = [(r, c) for r in range(1, len(grid)) for c, value in enumerate(grid[r]) if value]
    r0, r1 = min(r for r, _ in cells), max(r for r, _ in cells)
    c0, c1 = min(c for _, c in cells), max(c for _, c in cells)
    return [list(row[c0:c1 + 1]) for row in grid[r0:r1 + 1]]


def _diagnostic_action(grid, action):
    # Pure authoring diagnostics, never returned as generator labels.
    if action == 1:
        return [list(row) for row in zip(*grid[::-1])]
    if action == 2:
        return [list(row[::-1]) for row in grid]
    if action == 3:
        return [list(row[::-1]) for row in grid[::-1]]
    if action == 4:
        return [list(row) for row in grid[::-1]]
    if action == 5:
        return [list(row) for row in zip(*grid)][::-1]
    return [list(row) for row in grid]


def _prediction(grid, mode="normal"):
    codes = [v for v in grid[0] if v]
    if mode == "sorted_codes":
        codes = sorted(codes)
    elif mode == "deduplicate_codes":
        codes = list(dict.fromkeys(codes))
    elif mode == "collapse_adjacent_codes":
        codes = [v for index, v in enumerate(codes) if index == 0 or codes[index - 1] != v]
    elif mode == "stop_at_first_zero":
        codes = []
        for value in grid[0]:
            if value == 0:
                break
            codes.append(value)
    elif mode == "first_three_only":
        codes = codes[:3]
    elif mode == "first_only":
        codes = codes[:1]
    elif mode == "last_only":
        codes = codes[-1:]
    elif mode == "reverse_codes":
        codes = codes[::-1]
    elif mode == "ignore_script":
        codes = []
    mapping = _ALTERNATE_MAPS.get(mode, (1, 2, 3, 4))
    result = _body(grid)
    for code in codes:
        result = _diagnostic_action(result, mapping[code - 1])
    return result


def _make_rival(mode):
    def rival(grid):
        return _prediction(grid, mode)
    return rival


def _make_witness(rival):
    def witness(grid):
        return _prediction(grid) != rival(grid)
    return witness


_SHORTCUT_NAMES = tuple(_ALTERNATE_MAPS) + (
    "sorted_codes", "deduplicate_codes", "collapse_adjacent_codes",
    "stop_at_first_zero", "first_three_only",
)
_OTHER_RIVALS = ("first_only", "last_only", "reverse_codes", "ignore_script")
SEMANTIC_RIVALS = {name: _make_rival(name) for name in _SHORTCUT_NAMES + _OTHER_RIVALS}
CANONICAL_SHORTCUTS = {name: SEMANTIC_RIVALS[name] for name in _SHORTCUT_NAMES}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
SEMANTIC_WITNESSES = {"refutes_" + name: _make_witness(rival)
                      for name, rival in SEMANTIC_RIVALS.items()}
WITNESS_RIVALS = {"refutes_" + name: [name] for name in SEMANTIC_RIVALS}
