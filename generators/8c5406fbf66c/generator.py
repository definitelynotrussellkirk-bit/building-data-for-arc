"""Source-bound generator for ``arc_puzzle_bank_next21:E13``.

Canonical rule: scan every solid same-color non-background 2x2 window and
recolor that window's top-left cell to 8. Windows are independent and may
overlap inside a solid 2xN, Nx2, or 3x3 region.

The three-step default lesson schedule deliberately mixes two obligations:
canonical-profile isolated blocks and an overlapping-window counterexample to
the old "only isolated four-cell components" shortcut.
"""
from __future__ import annotations

from collections import deque

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "8c5406fbf66c"
TASK_ID = "8c5406fbf66c"
RULE_HASH = "29d77c7080ca"
VERSION = "1.4.1"
SUMMARY = (
    "Mark the top-left cell of every solid same-color non-background 2x2 "
    "window, including overlapping windows."
)
INVARIANTS = [
    "background is 0 and marker color 8 is absent from normal inputs",
    "every nonzero input cell belongs to at least one active 2x2 window",
    "normal inputs contain exactly 2..4 active windows",
    "every three default samples include a canonical-profile scene and an overlap witness",
]

AXES = {
    "grid_h": {"type": "int", "default": "canonical schedule or rng 4..16", "valid": "4..16"},
    "grid_w": {"type": "int", "default": "canonical schedule or rng 4..16", "valid": "4..16"},
    "blocks": {"type": "int", "default": "difficulty schedule in 2..4", "valid": "2..4"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict] = []

DEGENERATE_TEXTURES = ("no_blocks", "blocks_already_have_8", "fragmented_blocks")
EXAMPLES_NEEDED = 3
LESSON_SCHEDULE_PERIOD = 3
SCHEDULE_PROFILES = ("canonical", "overlap")
MIN_STRICT_FRAC = 0.20

_NONZERO_COLORS = (1, 2, 3, 4, 5, 6, 7, 9)
_CANONICAL_PROFILES = {(5, 6, 3), (6, 8, 3), (6, 9, 4)}
_CANONICAL_LAYOUTS = {
    "easy": (5, 6, ((0, 1), (2, 3))),
    "medium": (6, 8, ((1, 2), (4, 3))),
    "hard": (6, 9, ((1, 1), (1, 6), (4, 3))),
}


def schedule_profile(seed, sample_index, difficulty=None):
    """One canonical anchor followed by two overlap witnesses per period."""
    del seed, difficulty
    return "canonical" if sample_index % LESSON_SCHEDULE_PERIOD == 0 else "overlap"


def _active_windows(grid):
    """Return ``(row, col, color)`` for every canonical 2x2 match."""
    if not grid or not grid[0]:
        return []
    h, w = len(grid), len(grid[0])
    windows = []
    for r in range(h - 1):
        for c in range(w - 1):
            value = grid[r][c]
            if (
                value != 0
                and grid[r][c + 1] == value
                and grid[r + 1][c] == value
                and grid[r + 1][c + 1] == value
            ):
                windows.append((r, c, value))
    return windows


def _active_anchors(grid):
    return [(r, c) for r, c, _color in _active_windows(grid)]


def observe_overrides(grid):
    """Recover every declared exact control from a returned grid."""
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "blocks": len(_active_windows(grid)),
    }


def _has_overlapping_windows(grid) -> bool:
    anchors = _active_anchors(grid)
    return any(
        abs(r1 - r2) + abs(c1 - c2) == 1
        for index, (r1, c1) in enumerate(anchors)
        for r2, c2 in anchors[index + 1 :]
    )


def _validate_call(seed, sample_index, difficulty, overrides):
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    if type(sample_index) is not int:
        raise TypeError("sample_index must be an integer (not bool)")
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")
    if difficulty is not None:
        if not isinstance(difficulty, str):
            raise TypeError("difficulty must be easy, medium, hard, or None")
        if difficulty not in {"easy", "medium", "hard"}:
            raise ValueError("difficulty must be easy, medium, hard, or None")
    unknown = set(overrides) - set(AXES) - {"texture"}
    if unknown:
        raise TypeError(f"unknown override(s): {sorted(unknown)}")
    if "texture" in overrides and overrides["texture"] not in (None, *DEGENERATE_TEXTURES):
        raise ValueError(f"unknown texture fixture: {overrides['texture']!r}")


def _draw_int_default(ctx, label, lo, hi, defaults):
    """Honor the full declared override range; defaults may use a curriculum."""
    if ctx.overrides.get(label) is not None:
        return ctx.draw_int_strict(label, lo, hi)
    return ctx.draw_choice(label, tuple(defaults))


def _canonical_band(difficulty, sample_index):
    if difficulty in _CANONICAL_LAYOUTS:
        return difficulty
    return ("easy", "medium", "hard")[(sample_index // LESSON_SCHEDULE_PERIOD) % 3]


def _draw_canonical_profile(ctx, difficulty):
    band = _canonical_band(difficulty, ctx.sample_index)
    h, w, anchors = _CANONICAL_LAYOUTS[band]
    # Even fixed canonical branches must record all exact-axis provenance so
    # the override checker can compare the draw ledger with the returned grid.
    h = ctx.draw_choice("grid_h", (h,))
    w = ctx.draw_choice("grid_w", (w,))
    target = ctx.draw_choice("blocks", (len(anchors),))
    if target != len(anchors):  # singleton draw: retained as an explicit invariant
        raise AssertionError("canonical block-count provenance drifted")
    rng = ctx.draw_rng("canonical_layout")
    colors = rng.sample(list(_NONZERO_COLORS), len(anchors))
    grid = full_grid(h, w, 0)
    for (row, col), color in zip(anchors, colors):
        for dr in (0, 1):
            for dc in (0, 1):
                grid[row + dr][col + dc] = color
    return grid


def _motif_shapes(target):
    if target == 2:
        return ((2, 3), (3, 2))
    if target == 3:
        return ((2, 4), (4, 2))
    if target == 4:
        # 3x3 always fits the declared 4x4 minimum and has exactly four
        # overlapping windows. 2x5/5x2 add elongated variants when possible.
        return ((2, 5), (5, 2), (3, 3))
    raise ValueError(f"unsupported active-window count: {target}")


def _draw_overlap_profile(ctx, difficulty):
    h = ctx.draw_int_strict("grid_h", 4, 16)
    w = ctx.draw_int_strict("grid_w", 4, 16)
    if difficulty == "easy":
        defaults = (2,)
    elif difficulty == "hard":
        defaults = (3, 4)
    else:
        defaults = (2, 3, 4)
    target = _draw_int_default(ctx, "blocks", 2, 4, defaults)

    fitting = [shape for shape in _motif_shapes(target) if shape[0] <= h and shape[1] <= w]
    if not fitting:  # impossible under 4x4 minimum, retained as a loud invariant
        raise ValueError(f"cannot fit {target} active windows in {h}x{w}")
    rng = ctx.draw_rng("overlap_layout")
    # Residues 1 and 2 prefer horizontal and vertical lessons respectively;
    # exact overrides still retain deterministic fallback among fitting shapes.
    preferred_tall = ctx.sample_index % LESSON_SCHEDULE_PERIOD == 2
    preferred = [shape for shape in fitting if (shape[0] > shape[1]) == preferred_tall]
    motif_h, motif_w = rng.choice(preferred or fitting)
    row0 = rng.randrange(h - motif_h + 1)
    col0 = rng.randrange(w - motif_w + 1)
    color = rng.choice(_NONZERO_COLORS)

    grid = full_grid(h, w, 0)
    for row in range(row0, row0 + motif_h):
        for col in range(col0, col0 + motif_w):
            grid[row][col] = color
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(seed, sample_index, difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    texture = overrides.get("texture")
    if texture in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(texture)

    controlled = any(overrides.get(name) is not None for name in AXES)
    if not controlled and schedule_profile(seed, sample_index, difficulty) == "canonical":
        return _draw_canonical_profile(ctx, difficulty)
    return _draw_overlap_profile(ctx, difficulty)


def _draw_from_degenerate(name):
    h, w = 7, 8
    grid = full_grid(h, w, 0)
    if name == "no_blocks":
        return grid
    if name == "blocks_already_have_8":
        for row0, col0 in ((1, 1), (4, 5)):
            for dr in (0, 1):
                for dc in (0, 1):
                    grid[row0 + dr][col0 + dc] = 8
        return grid
    if name == "fragmented_blocks":
        grid[1][1] = 4
        grid[1][2] = 4
        grid[2][1] = 4
        grid[4][5] = 6
        grid[5][5] = 6
        grid[5][6] = 6
        return grid
    raise ValueError(name)


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    errors = []
    if not grid or not grid[0]:
        return ["empty grid"]
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return ["ragged grid"]
    # The generator's declared controls use 4..16, but the canonical rule is
    # meaningful on any ARC-sized grid with room for a 2x2 window. Retained
    # counterexamples such as the minimal 2x3 overlap witness must remain
    # valid inputs to the semantic contract.
    if not (2 <= len(grid) <= 30 and 2 <= width <= 30):
        errors.append("grid dimensions must each be in 2..30")
    if any(type(value) is not int or value < 0 or value > 9 for row in grid for value in row):
        errors.append("grid has non-ARC color values")
        return errors
    if any(value == 8 for row in grid for value in row):
        errors.append("normal input windows must not already contain color 8")

    windows = _active_windows(grid)
    covered = {
        (row + dr, col + dc)
        for row, col, _color in windows
        for dr in (0, 1)
        for dc in (0, 1)
    }
    uncovered = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 0 and (row, col) not in covered
    ]
    if uncovered:
        errors.append(
            "every nonzero cell must be covered by an active 2x2 window; "
            f"uncovered={uncovered[:4]}"
        )
    if not 2 <= len(windows) <= 4:
        errors.append(f"expected 2..4 active 2x2 windows, got {len(windows)}")
    return errors


def rule_mirror(grid):
    """Pure Python mirror used only by executable semantic contracts/tests."""
    output = [list(row) for row in grid]
    for row, col, _color in _active_windows(grid):
        output[row][col] = 8
    return output


def _same_color_components(grid):
    seen = set()
    for row in range(len(grid)):
        for col in range(len(grid[0])):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            component = set()
            queue = deque([(row, col)])
            seen.add((row, col))
            while queue:
                current = queue.popleft()
                component.add(current)
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    point = current[0] + dr, current[1] + dc
                    if (
                        0 <= point[0] < len(grid)
                        and 0 <= point[1] < len(grid[0])
                        and point not in seen
                        and grid[point[0]][point[1]] == color
                    ):
                        seen.add(point)
                        queue.append(point)
            yield color, component


def _isolated_components_only(grid):
    """The pre-repair shortcut: only mark components that are exactly 2x2."""
    output = [list(row) for row in grid]
    for _color, component in _same_color_components(grid):
        rows = [point[0] for point in component]
        cols = [point[1] for point in component]
        row0, row1 = min(rows), max(rows)
        col0, col1 = min(cols), max(cols)
        if len(component) == 4 and row1 - row0 == 1 and col1 - col0 == 1:
            output[row0][col0] = 8
    return output


def strict_canonical_like(grid):
    profile = (
        len(grid) if isinstance(grid, list) else -1,
        len(grid[0]) if isinstance(grid, list) and grid and isinstance(grid[0], list) else -1,
        len({value for row in grid for value in row})
        if isinstance(grid, list) and grid and all(isinstance(row, list) for row in grid)
        else -1,
    )
    if profile not in _CANONICAL_PROFILES:
        return [f"profile {profile} is not one of the three canonical profiles"]
    errors = self_check(grid)
    if errors:
        return errors
    if _has_overlapping_windows(grid):
        return ["canonical source inputs use isolated 2x2 components"]
    return []


def _canonical_profile_witness(grid):
    return strict_canonical_like(grid) == []


SEMANTIC_RIVALS = {"isolated_components_only": _isolated_components_only}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
SEMANTIC_WITNESSES = {
    "overlapping_windows": _has_overlapping_windows,
    "canonical_profile": _canonical_profile_witness,
}
WITNESS_RIVALS = {"overlapping_windows": ["isolated_components_only"]}
BRANCH_WITNESSES = ("canonical_profile",)


def _pair_errors(name, pair):
    if not isinstance(pair, dict) or set(pair) < {"input", "output"}:
        return [f"{name} must contain input and output grids"]
    errors = self_check(pair["input"])
    if errors:
        return [f"{name} input is invalid: {errors[0]}"]
    if pair["output"] != rule_mirror(pair["input"]):
        return [f"{name} output disagrees with the canonical rule mirror"]
    return []


def lesson_identifiable(demos, query):
    """Finite-rival lesson contract for the retained overlap defect."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} labeled demonstrations are required"]
    reasons = []
    for index, pair in enumerate(demos):
        reasons.extend(_pair_errors(f"demo {index}", pair))
    reasons.extend(_pair_errors("query", query))
    if reasons:
        return reasons
    if not any(_has_overlapping_windows(pair["input"]) for pair in demos):
        reasons.append("demonstrations do not refute isolated_components_only")
    rival = LESSON_COMPETITORS["isolated_components_only"]
    if all(rival(pair["input"]) == pair["output"] for pair in demos):
        if rival(query["input"]) != query["output"]:
            reasons.append("isolated_components_only fits all demonstrations but changes the query")
    return reasons
