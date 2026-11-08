"""Generator for ARC task 84551f4c / content task eb373570e72b.

The canonical task has two related input grammars.

* Non-staggered inputs are full-height marker columns. Markers spaced three
  columns apart form a chain, except that a red(2) -> blue(1) handoff starts a
  new chain. A blue-starting chain lies down as three-cell floor runs; an
  all-red chain remains a vertical column.
* Staggered inputs choose the first near-busiest row as the active row. Chains
  use pure three-column connectivity; any blue marker makes that chain lie
  down. All-red chains fall from their first observed row, loose blue suffixes
  below the active row become floor runs, and isolated one-cell gaps between
  red floor runs close.

Normal draws are always lawful, visibly transforming lessons. The exact axes
are deliberately small and recoverable from the returned grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "eb373570e72b"
TASK_ID = "eb373570e72b"
RULE_HASH = "73b10de4ceaa"
VERSION = "4.0.0"  # canonical-domain rebuild: staggered branch, honest axes,
# canonical-accepting mutation-sensitive self_check, and exact override replay.

SUMMARY = (
    "Three-spaced marker chains either lie down as colored three-cell floor "
    "runs or remain/fall as vertical columns. In staggered scenes the first "
    "near-busiest row supplies the active markers, earlier red evidence sets "
    "column starts, loose lower blue cells make floor runs, and isolated red "
    "floor gaps close."
)

INVARIANTS = [
    "background is color 0 and marker colors are exactly blue 1 and red 2",
    "non-staggered scenes contain full-height marker columns and at least one "
    "blue-starting horizontal chain",
    "staggered scenes have a non-top active row, at least one horizontal and "
    "one all-red vertical chain, and one or more loose blue suffix columns "
    "strictly below the active row",
    "marker chains are internally spaced by exactly three columns; neighboring "
    "chains use a gap of four or more except for the canonical non-staggered "
    "red-to-blue spacing-three handoff",
    "staggered mode requires grid_h >= 6 and n_chains >= 2; incompatible exact "
    "override combinations reject explicitly",
]

PALETTE_KINDS: tuple[str, ...] = ()
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
SCENE_MODES = ("nonstaggered", "staggered")

AXES = {
    "grid_h": {
        "type": "int",
        "default": "band/mode-aware keyed draw",
        "valid": "3..9",
    },
    "grid_w": {
        "type": "int",
        "default": "band/count-aware keyed draw",
        "valid": "7..30",
    },
    "n_chains": {
        "type": "int",
        "default": "2..5 by difficulty (1 allowed only for nonstaggered overrides)",
        "valid": "1..5",
    },
    "scene_mode": {
        "type": "str",
        "default": "difficulty-weighted keyed choice",
        "valid": "nonstaggered|staggered",
    },
}

_H_MIN, _H_MAX = 3, 9
_W_MIN, _W_MAX = 7, 30
_N_MIN, _N_MAX = 1, 5


def _row_markers(grid: list[list[int]], row: int) -> list[int]:
    return [col for col, value in enumerate(grid[row]) if value != 0]


def _rule_chains(
    grid: list[list[int]], active_row: int, *, staggered: bool
) -> list[list[int]]:
    """Partition active markers exactly as the canonical rule does."""
    markers = _row_markers(grid, active_row)
    chains: list[list[int]] = []
    for col in markers:
        if not chains:
            chains.append([col])
            continue
        prev = chains[-1][-1]
        handoff = (
            not staggered
            and col == prev + 3
            and grid[active_row][prev] == 2
            and grid[active_row][col] == 1
        )
        if col != prev + 3 or handoff:
            chains.append([col])
        else:
            chains[-1].append(col)
    return chains


def _horizontal_chain(
    grid: list[list[int]], active_row: int, chain: list[int], *, staggered: bool
) -> bool:
    if staggered:
        return any(grid[active_row][col] == 1 for col in chain)
    return grid[active_row][chain[0]] == 1


def _suffix_start(grid: list[list[int]], col: int) -> int | None:
    rows = [row for row in range(len(grid)) if grid[row][col] != 0]
    return min(rows) if rows else None


def _analysis(grid: list[list[int]]) -> dict:
    errors: list[str] = []
    if not isinstance(grid, list) or not grid:
        return {"errors": ["grid must be a non-empty list"], "facts": None}
    if not isinstance(grid[0], list) or not grid[0]:
        return {"errors": ["grid rows must be non-empty lists"], "facts": None}
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return {"errors": ["ragged grid"], "facts": None}

    height = len(grid)
    if not (_H_MIN <= height <= _H_MAX and _W_MIN <= width <= _W_MAX):
        errors.append(
            f"grid {height}x{width} outside declared "
            f"{_H_MIN}..{_H_MAX} x {_W_MIN}..{_W_MAX} envelope"
        )
    bad_values = sorted(
        {
            value
            for row in grid
            for value in row
            if isinstance(value, bool)
            or not isinstance(value, int)
            or value not in (0, 1, 2)
        },
        key=repr,
    )
    if bad_values:
        errors.append(f"cells must be literal 0, 1, or 2; found {bad_values}")

    nonzero_rows = [row for row in range(height) if _row_markers(grid, row)]
    if not nonzero_rows:
        errors.append("at least one marker is required")
        return {"errors": errors, "facts": None}

    max_count = max(len(_row_markers(grid, row)) for row in nonzero_rows)
    active_row = next(
        row
        for row in nonzero_rows
        if len(_row_markers(grid, row)) >= max_count - 1
    )
    markers = _row_markers(grid, active_row)
    if any(grid[active_row][col] not in (1, 2) for col in markers):
        errors.append("active-row markers must use colors 1 or 2")

    staggered = active_row > 0
    marker_gaps = [right - left for left, right in zip(markers, markers[1:])]
    if any(gap < 3 for gap in marker_gaps):
        errors.append("active markers must be separated by at least three columns")
    chains = _rule_chains(grid, active_row, staggered=staggered)
    if len(chains) > _N_MAX:
        errors.append(f"scene has {len(chains)} chains; declared maximum is {_N_MAX}")
    handoffs = [
        (left, right)
        for left, right in zip(markers, markers[1:])
        if (
            not staggered
            and right == left + 3
            and grid[active_row][left] == 2
            and grid[active_row][right] == 1
        )
    ]
    horizontal = [
        chain
        for chain in chains
        if _horizontal_chain(grid, active_row, chain, staggered=staggered)
    ]
    vertical = [chain for chain in chains if chain not in horizontal]
    marker_set = set(markers)
    loose_blue_cols: list[int] = []

    if not staggered:
        if active_row != 0:
            errors.append("non-staggered scene must select row 0")
        for col in range(width):
            column = [grid[row][col] for row in range(height)]
            if all(value == 0 for value in column):
                continue
            if column[0] not in (1, 2) or any(value != column[0] for value in column):
                errors.append(
                    f"non-staggered marker column {col} must be full-height "
                    "and single-colored"
                )
        if not horizontal:
            errors.append("non-staggered lesson needs a blue-starting horizontal chain")
    else:
        if active_row >= height - 1:
            errors.append("staggered active row must leave at least one lower row")
        for col in markers:
            start = _suffix_start(grid, col)
            color = grid[active_row][col]
            rows = [row for row in range(height) if grid[row][col] != 0]
            if start is None or start > active_row:
                errors.append(f"active marker column {col} has no evidence at active row")
                continue
            if rows != list(range(start, height)):
                errors.append(f"active marker column {col} is not a contiguous suffix")
            if any(grid[row][col] != color for row in rows):
                errors.append(f"active marker column {col} changes color down its suffix")
        for col in range(width):
            if col in marker_set:
                continue
            rows = [row for row in range(height) if grid[row][col] != 0]
            if not rows:
                continue
            start = min(rows)
            if start <= active_row:
                errors.append(
                    f"non-marker column {col} has evidence at/above the active row"
                )
            if rows != list(range(start, height)):
                errors.append(f"loose column {col} is not a contiguous lower suffix")
            if any(grid[row][col] != 1 for row in rows):
                errors.append(f"loose column {col} must be blue (1)")
            loose_blue_cols.append(col)
        if not horizontal:
            errors.append("staggered lesson needs a chain containing blue")
        if not vertical:
            errors.append("staggered lesson needs an all-red vertical chain")
        if not loose_blue_cols:
            errors.append("staggered lesson needs a loose lower blue suffix")

    facts = {
        "height": height,
        "width": width,
        "active_row": active_row,
        "scene_mode": "staggered" if staggered else "nonstaggered",
        "markers": markers,
        "chains": chains,
        "horizontal_chains": horizontal,
        "vertical_chains": vertical,
        "loose_blue_cols": loose_blue_cols,
        "handoffs": handoffs,
        "n_chains": len(chains),
    }
    return {"errors": sorted(set(errors)), "facts": facts}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed lessons, including canonical-looking palette impostors."""
    del difficulty, meta
    return _analysis(grid)["errors"]


def observe_overrides(grid) -> dict[str, int | str]:
    """Recover every exact semantic axis from the returned grid."""
    analysis = _analysis(grid)
    if analysis["errors"] or analysis["facts"] is None:
        return {}
    facts = analysis["facts"]
    return {
        "grid_h": facts["height"],
        "grid_w": facts["width"],
        "n_chains": facts["n_chains"],
        "scene_mode": facts["scene_mode"],
    }


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Independent Python mirror used only by focused tests and audits.

    The production generator/runner continues to use the canonical Racket rule
    as the sole output authority.
    """
    height, width = len(grid), len(grid[0])
    nonzero_rows = [row for row in range(height) if _row_markers(grid, row)]
    if not nonzero_rows:
        return full_grid(height, width, 0)
    max_count = max(len(_row_markers(grid, row)) for row in nonzero_rows)
    active_row = next(
        row
        for row in nonzero_rows
        if len(_row_markers(grid, row)) >= max_count - 1
    )
    markers = _row_markers(grid, active_row)
    staggered = active_row > 0
    chains = _rule_chains(grid, active_row, staggered=staggered)
    orientation: dict[int, bool] = {}
    for chain in chains:
        is_horizontal = _horizontal_chain(
            grid, active_row, chain, staggered=staggered
        )
        for col in chain:
            orientation[col] = is_horizontal
    vertical_cols = [col for col in markers if not orientation[col]]

    out = full_grid(height, width, 0)
    for col in markers:
        color = grid[active_row][col]
        if orientation[col]:
            for target_col in range(col, min(width, col + 3)):
                out[height - 1][target_col] = color
        else:
            start = active_row
            if staggered:
                hits = [row for row in nonzero_rows if grid[row][col] != 0]
                if hits:
                    start = hits[0]
            for row in range(start, height):
                out[row][col] = color

    if not staggered:
        return out

    marker_set = set(markers)
    for row in range(active_row + 1, height):
        for col in range(width):
            if grid[row][col] != 1 or col in marker_set:
                continue
            next_vertical = [vcol for vcol in vertical_cols if vcol > col]
            end_col = (
                min(width - 1, next_vertical[0] - 2)
                if next_vertical
                else min(width - 1, col + 2)
            )
            if end_col >= col:
                for target_col in range(col, end_col + 1):
                    out[height - 1][target_col] = 1

    for col in range(1, width - 1):
        if (
            out[height - 1][col] == 0
            and out[height - 1][col - 1] == 2
            and out[height - 1][col + 1] == 2
        ):
            out[height - 1][col] = 2
    return out


def _minimum_width(n_chains: int) -> int:
    return 4 * n_chains - 3


def _draw_mode(ctx, overrides: dict, difficulty: str | None) -> str:
    if overrides.get("scene_mode") is not None:
        return ctx.draw_choice("scene_mode", SCENE_MODES)

    pinned_h = overrides.get("grid_h")
    pinned_n = overrides.get("n_chains")
    if pinned_h is not None and int(pinned_h) < 6:
        chosen = "nonstaggered"
    elif pinned_n is not None and int(pinned_n) == 1:
        chosen = "nonstaggered"
    else:
        probability = {"easy": 0.25, "medium": 0.50, "hard": 0.80}.get(
            difficulty, 0.50
        )
        chosen = (
            "staggered"
            if ctx.draw_rng("scene_mode_probability").random() < probability
            else "nonstaggered"
        )
    return ctx.draw_choice("scene_mode", (chosen,))


def _draw_dimensions_and_count(ctx, overrides: dict, mode: str, difficulty: str | None):
    if overrides.get("grid_h") is not None:
        height = ctx.draw_int("grid_h", _H_MIN, _H_MAX)
    else:
        height_ranges = {
            ("nonstaggered", "easy"): (3, 5),
            ("nonstaggered", "medium"): (3, 7),
            ("nonstaggered", "hard"): (5, 9),
            ("staggered", "easy"): (6, 7),
            ("staggered", "medium"): (6, 8),
            ("staggered", "hard"): (7, 9),
        }
        lo, hi = height_ranges.get((mode, difficulty), (6, 9) if mode == "staggered" else (3, 9))
        height = ctx.draw_int("grid_h", lo, hi)
    if mode == "staggered" and height < 6:
        raise ValueError("scene_mode='staggered' requires grid_h >= 6")

    width_pinned = overrides.get("grid_w") is not None
    count_pinned = overrides.get("n_chains") is not None
    width = ctx.draw_int("grid_w", _W_MIN, _W_MAX) if width_pinned else None
    count = ctx.draw_int("n_chains", _N_MIN, _N_MAX) if count_pinned else None

    mode_min_count = 2 if mode == "staggered" else 1
    if count is not None and count < mode_min_count:
        raise ValueError("scene_mode='staggered' requires n_chains >= 2")

    default_count_range = {
        "easy": (2, 3),
        "medium": (2, 4),
        "hard": (3, 5),
    }.get(difficulty, (2, 5))

    if count is None:
        lo, hi = default_count_range
        lo = max(lo, mode_min_count)
        if width is not None:
            compatible_max = min(_N_MAX, (width + 3) // 4)
            if compatible_max < mode_min_count:
                raise ValueError(
                    f"grid_w={width} cannot fit the minimum {mode_min_count} chains"
                )
            hi = min(hi, compatible_max)
            if hi < lo:
                lo = hi = compatible_max
        count = ctx.draw_int("n_chains", lo, hi)

    required_width = _minimum_width(count)
    if width is None:
        width_range = {
            "easy": (7, 16),
            "medium": (12, 23),
            "hard": (18, 30),
        }.get(difficulty, (7, 30))
        lo = max(width_range[0], required_width)
        hi = max(lo, width_range[1])
        if hi > _W_MAX:
            raise ValueError(
                f"n_chains={count} cannot fit inside declared grid_w <= {_W_MAX}"
            )
        width = ctx.draw_int("grid_w", lo, hi)
    elif width < required_width:
        raise ValueError(
            f"grid_w={width} cannot fit n_chains={count}; minimum is {required_width}"
        )

    return height, width, count


def _normal_specs(n_chains: int, rng) -> list[dict]:
    if n_chains == 1:
        return [{"kind": "h", "colors": [1]}]
    kinds = ["h", "v"] + [rng.choice(("h", "v")) for _ in range(n_chains - 2)]
    rng.shuffle(kinds)
    return [
        {"kind": kind, "colors": [1] if kind == "h" else [2]}
        for kind in kinds
    ]


def _layout_specs(mode: str, n_chains: int, width: int, difficulty: str | None, rng):
    """Build chain specs plus the rule-significant gaps between them.

    A staggered red-gap-closure witness needs an exact four-column inter-chain
    marker gap. A non-staggered red->blue handoff needs an exact three-column
    gap: the canonical parser deliberately splits that otherwise-connected
    pair into two chains.
    """
    closure = (
        mode == "staggered"
        and n_chains >= 3
        and width >= 15
        and (difficulty == "hard" or rng.random() < 0.45)
    )
    handoff = (
        mode == "nonstaggered"
        and n_chains >= 2
        and (difficulty in ("medium", "hard") or rng.random() < 0.35)
        and rng.random() < 0.55
    )
    protected_gap: int | None = None
    protected_gap_size = 4

    if closure:
        blocks = [
            [
                {"kind": "h", "colors": [1, 2], "closure_side": "left"},
                {"kind": "h", "colors": [2, 1], "closure_side": "right"},
            ]
        ]
        remaining = n_chains - 2
        other_kinds = ["v"] + [rng.choice(("h", "v")) for _ in range(remaining - 1)]
        blocks.extend(
            [{"kind": kind, "colors": [1] if kind == "h" else [2]}]
            for kind in other_kinds
        )
        rng.shuffle(blocks)
        specs = [spec for block in blocks for spec in block]
        for index in range(len(specs) - 1):
            if (
                specs[index].get("closure_side") == "left"
                and specs[index + 1].get("closure_side") == "right"
            ):
                protected_gap = index
                break
    elif handoff:
        blocks = [
            [
                {"kind": "v", "colors": [2], "handoff_side": "left"},
                {"kind": "h", "colors": [1], "handoff_side": "right"},
            ]
        ]
        remaining = n_chains - 2
        blocks.extend(
            [{"kind": kind, "colors": [1] if kind == "h" else [2]}]
            for kind in (rng.choice(("h", "v")) for _ in range(remaining))
        )
        rng.shuffle(blocks)
        specs = [spec for block in blocks for spec in block]
        for index in range(len(specs) - 1):
            if (
                specs[index].get("handoff_side") == "left"
                and specs[index + 1].get("handoff_side") == "right"
            ):
                protected_gap = index
                protected_gap_size = 3
                break
    else:
        specs = _normal_specs(n_chains, rng)

    def base_gaps(spec_list):
        gaps = [4] * (len(spec_list) - 1)
        if protected_gap is not None and protected_gap < len(gaps):
            gaps[protected_gap] = protected_gap_size
        return gaps

    def required(spec_list):
        return 1 + sum(base_gaps(spec_list)) + sum(
            3 * (len(spec["colors"]) - 1) for spec in spec_list
        )

    if required(specs) > width:
        specs = _normal_specs(n_chains, rng)
        protected_gap = None
        protected_gap_size = 4

    budget = width - required(specs)
    while budget >= 3:
        expandable = [index for index, spec in enumerate(specs) if len(spec["colors"]) < 3]
        if not expandable:
            break
        index = rng.choice(expandable)
        specs[index]["colors"].append(2)
        budget -= 3

    gaps = base_gaps(specs)
    flexible_gaps = [index for index in range(len(gaps)) if index != protected_gap]
    rng.shuffle(flexible_gaps)
    for index in flexible_gaps:
        if budget <= 0:
            break
        gaps[index] = 5
        budget -= 1
    start = rng.randint(0, min(2, budget)) if budget else 0

    cursor = start
    for index, spec in enumerate(specs):
        spec["columns"] = [cursor + 3 * offset for offset in range(len(spec["colors"]))]
        cursor = spec["columns"][-1]
        if index < len(gaps):
            cursor += gaps[index]
    if cursor >= width:
        raise AssertionError(f"layout overflow: last marker {cursor} >= width {width}")
    return specs


def _paint_nonstaggered(height: int, width: int, specs: list[dict]) -> list[list[int]]:
    grid = full_grid(height, width, 0)
    for spec in specs:
        for col, color in zip(spec["columns"], spec["colors"]):
            for row in range(height):
                grid[row][col] = color
    return grid


def _paint_staggered(height: int, width: int, specs: list[dict], rng) -> list[list[int]]:
    grid = full_grid(height, width, 0)
    active_row = rng.randint(max(1, height - 4), height - 3)
    marker_cols: list[int] = []
    vertical_cols: list[int] = []
    for spec in specs:
        for col, color in zip(spec["columns"], spec["colors"]):
            marker_cols.append(col)
            if spec["kind"] == "v":
                vertical_cols.append(col)
            for row in range(active_row, height):
                grid[row][col] = color

    evidence_col = rng.choice(vertical_cols)
    evidence_start = max(0, active_row - rng.randint(1, min(2, active_row)))
    for row in range(evidence_start, active_row):
        grid[row][evidence_col] = 2

    marker_set = set(marker_cols)
    sorted_vertical = sorted(vertical_cols)
    clipped_candidates: list[int] = []
    for col in range(width):
        if col in marker_set:
            continue
        later_vertical = [vertical_col for vertical_col in sorted_vertical if vertical_col > col]
        if later_vertical and 2 <= later_vertical[0] - col <= 4:
            clipped_candidates.append(col)
    last_vertical = max(vertical_cols)
    free_candidates = [
        col for col in range(last_vertical + 1, width) if col not in marker_set
    ]
    if free_candidates and (not clipped_candidates or rng.random() < 0.50):
        candidates = free_candidates
    else:
        candidates = clipped_candidates
    if not candidates:
        candidates = [col for col in range(width) if col not in marker_set]
    if not candidates:
        raise AssertionError("staggered layout left no loose-blue column")
    loose_col = rng.choice(candidates)
    for row in range(active_row + 1, height):
        grid[row][loose_col] = 1
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    overrides = dict(overrides)
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    mode = _draw_mode(ctx, overrides, difficulty)
    height, width, n_chains = _draw_dimensions_and_count(
        ctx, overrides, mode, difficulty
    )
    rng = ctx.draw_rng("layout")
    specs = _layout_specs(mode, n_chains, width, difficulty, rng)
    grid = (
        _paint_staggered(height, width, specs, rng)
        if mode == "staggered"
        else _paint_nonstaggered(height, width, specs)
    )
    errors = self_check(grid)
    if errors:
        raise AssertionError("generated invalid lesson: " + "; ".join(errors))
    return grid
