"""Generator for H9 — decode a two-row recoloring legend, then drop it.

Rows 0 and 1 contain aligned source/destination color pairs.  The output is
formed from the body below row 1: each source color is replaced once by its
paired destination, all unmapped cells are preserved, and the two legend rows
are removed.

The six-slot ordinary schedule anchors all three canonical size/palette
profiles while repeatedly exposing non-even legend columns, source/destination
palette overlap, and an unmapped destination-color witness.  Those controls
refute fixed-column, iterative/cascading, drop-only, and recolor-everything
shortcuts in every three-example lesson window.
"""
from __future__ import annotations

from collections.abc import Callable
from itertools import combinations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "17018eeb34da"
TASK_ID = "17018eeb34da"
VERSION = "2.0.0"
RULE_HASH = "0ce6913875ad"
EXAMPLES_NEEDED = 3

SUMMARY = (
    "Rows 0 and 1 are an aligned source-to-destination color legend. Remove "
    "those rows and recolor each body source cell exactly once; body colors "
    "that are not legend sources remain unchanged. Ordinary lessons vary key "
    "columns and sparse body geometry, and regularly include a destination "
    "that is also another source so iterative remapping is visibly wrong."
)

INVARIANTS = [
    "background is color 0",
    "the first two rows contain 2..4 aligned nonzero source/destination pairs",
    "legend sources are unique, legend destinations are unique, and no pair is identity",
    "at most one destination is also a different source, creating an acyclic one-step chain",
    "every legend source occurs in the sparse body below row 1",
    "body colors are limited to legend sources plus at most one destination-only unchanged witness",
    "the output drops exactly the first two rows and applies the mapping once",
]

LEGEND_LAYOUTS = ("canonical_even", "shifted_even", "scattered")
MAPPING_OVERLAPS = ("disjoint", "chain")

# Every declared axis is keyed, boundary-valid, and recoverable from the grid
# by observe_overrides().  Body morphology and palette identity intentionally
# vary outside AXES because they are nuisance diversity, not exact contracts.
AXES = {
    "grid_h": {"type": "int", "default": "six-slot canonical/difficulty schedule", "valid": "7..10"},
    "grid_w": {"type": "int", "default": "six-slot canonical/difficulty schedule", "valid": "7..10"},
    "n_pairs": {"type": "int", "default": "six-slot schedule", "valid": "2..4"},
    "source_uses": {"type": "int", "default": "2 or 3 uses per source", "valid": "2..3"},
    "unchanged_targets": {"type": "int", "default": "scheduled absent/present witness", "valid": "0..1"},
    "legend_layout": {"type": "enum", "default": "scheduled key geometry", "valid": LEGEND_LAYOUTS},
    "mapping_overlap": {"type": "enum", "default": "scheduled disjoint/one-step chain", "valid": MAPPING_OVERLAPS},
}

INCOMPATIBLE_OVERRIDE_COMBINATIONS = [
    {"legend_layout": "shifted_even", "n_pairs": 4, "grid_w": 7},
]

MIN_STRICT_FRAC = 0.95
SCHEDULE_PROFILES = tuple(range(6))

# These three profiles match the canonical (height, width, full-palette-size)
# envelope: 7x7 with 6 colors, 7x7 with 5 colors, and 8x8 with 7 colors.
_CANONICAL_PROFILES = {
    0: {
        "grid_h": 7,
        "grid_w": 7,
        "n_pairs": 3,
        "source_uses": 2,
        "unchanged_targets": 0,
        "legend_layout": "scattered",
        "mapping_overlap": "chain",
        "sources": (2, 4, 6),
        "destinations": (7, 6, 8),
    },
    1: {
        "grid_h": 7,
        "grid_w": 7,
        "n_pairs": 2,
        "source_uses": 3,
        "unchanged_targets": 1,
        "legend_layout": "canonical_even",
        "mapping_overlap": "disjoint",
        "sources": (3, 5),
        "destinations": (9, 7),
    },
    2: {
        "grid_h": 8,
        "grid_w": 8,
        "n_pairs": 3,
        "source_uses": 2,
        "unchanged_targets": 0,
        "legend_layout": "scattered",
        "mapping_overlap": "disjoint",
        "sources": (2, 3, 5),
        "destinations": (6, 8, 7),
    },
}


def schedule_profile(seed: int, sample_index: int, difficulty: str | None = None) -> int:
    """Expose the deterministic six-way lesson schedule to the semantic gate."""
    del seed, difficulty
    return int(sample_index) % 6


def _incompatible(message: str, *axes: str) -> ValueError:
    exc = ValueError(message)
    exc.incompatible_axes = tuple(axes)
    return exc


def _draw_exact_int(ctx, label: str, lo: int, hi: int, scheduled: int) -> int:
    if ctx.overrides.get(label) is not None:
        return ctx.draw_int(label, lo, hi)
    return ctx.draw_choice(label, (scheduled,))


def _draw_exact_choice(ctx, label: str, options: tuple[str, ...], scheduled: str) -> str:
    if ctx.overrides.get(label) is not None:
        return ctx.draw_choice(label, options)
    return ctx.draw_choice(label, (scheduled,))


def _scheduled_defaults(profile: int, difficulty: str | None) -> dict[str, int | str]:
    if profile in _CANONICAL_PROFILES:
        return {k: v for k, v in _CANONICAL_PROFILES[profile].items() if k not in {"sources", "destinations"}}

    band = difficulty if difficulty in {"easy", "medium", "hard"} else "medium"
    table = {
        "easy": {
            3: (7, 8, 3, 2, 1, "scattered", "chain"),
            4: (7, 7, 2, 3, 0, "shifted_even", "disjoint"),
            5: (8, 8, 3, 2, 1, "scattered", "chain"),
        },
        "medium": {
            3: (8, 9, 4, 2, 1, "scattered", "chain"),
            4: (9, 8, 3, 3, 0, "shifted_even", "disjoint"),
            5: (9, 9, 3, 3, 1, "scattered", "chain"),
        },
        "hard": {
            3: (10, 10, 4, 3, 1, "scattered", "chain"),
            4: (9, 10, 4, 3, 0, "shifted_even", "disjoint"),
            5: (10, 9, 4, 3, 1, "scattered", "chain"),
        },
    }
    h, w, n, uses, unchanged, layout, overlap = table[band][profile]
    return {
        "grid_h": h,
        "grid_w": w,
        "n_pairs": n,
        "source_uses": uses,
        "unchanged_targets": unchanged,
        "legend_layout": layout,
        "mapping_overlap": overlap,
    }


def _legend_columns(rng, width: int, n_pairs: int, layout: str) -> list[int]:
    canonical = tuple(range(0, 2 * n_pairs, 2))
    shifted = tuple(range(1, 1 + 2 * n_pairs, 2))
    if layout == "canonical_even":
        if canonical[-1] >= width:
            raise _incompatible("grid_w cannot fit canonical-even legend columns", "grid_w", "n_pairs", "legend_layout")
        return list(canonical)
    if layout == "shifted_even":
        if shifted[-1] >= width:
            raise _incompatible("grid_w cannot fit shifted-even legend columns", "grid_w", "n_pairs", "legend_layout")
        return list(shifted)

    fixed_even = {0, 2, 4, 6}
    candidates = [
        combo
        for combo in combinations(range(width), n_pairs)
        if combo != canonical
        and combo != shifted
        and not set(combo).issubset(fixed_even)
    ]
    if not candidates:
        raise _incompatible("grid_w leaves no shortcut-rebutting scattered legend layout", "grid_w", "n_pairs", "legend_layout")
    return list(rng.choice(candidates))


def _draw_palette(ctx, n_pairs: int, overlap: str, canonical: dict | None) -> tuple[list[int], list[int]]:
    if canonical is not None:
        return list(canonical["sources"]), list(canonical["destinations"])

    if overlap == "disjoint":
        colors = list(ctx.draw_distinct_colors("palette", n=2 * n_pairs, exclude={0}))
        return colors[:n_pairs], colors[n_pairs:]

    colors = list(ctx.draw_distinct_colors("palette", n=2 * n_pairs - 1, exclude={0}))
    sources = colors[:n_pairs]
    destinations = [sources[1], *colors[n_pairs:]]
    # destinations has n_pairs entries and exactly one overlap with sources.
    return sources, destinations


def _body_positions(height: int, width: int, style: int, rng) -> list[tuple[int, int]]:
    cells = [(r, c) for r in range(2, height) for c in range(width)]
    if style == 0:
        # Column-major order spreads even the smallest legal body over rows.
        ordered = [(r, c) for c in range(width) for r in range(2, height)]
    elif style == 1:
        # Diagonal order also spreads early cells over multiple rows.
        ordered = sorted(cells, key=lambda p: ((p[0] - 2 + p[1]) % (height - 2), p[1], p[0]))
    else:
        ordered = list(cells)
        rng.shuffle(ordered)
    # A rotation preserves deterministic replay while making canonical-profile
    # draws vary across seeds instead of becoming fixed templates.
    shift = rng.randrange(len(ordered))
    return ordered[shift:] + ordered[:shift]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic input grid; the Racket rule is output authority."""
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = schedule_profile(seed, sample_index, difficulty)
    defaults = _scheduled_defaults(profile, difficulty)

    h = _draw_exact_int(ctx, "grid_h", 7, 10, int(defaults["grid_h"]))
    scheduled_n = int(defaults["n_pairs"])
    if (
        overrides.get("n_pairs") is None
        and overrides.get("legend_layout") == "shifted_even"
        and overrides.get("grid_w") is not None
        and int(overrides["grid_w"]) == 7
    ):
        scheduled_n = min(scheduled_n, 3)
    n_pairs = _draw_exact_int(ctx, "n_pairs", 2, 4, scheduled_n)
    scheduled_w = int(defaults["grid_w"])
    if (
        overrides.get("grid_w") is None
        and overrides.get("legend_layout") == "shifted_even"
        and n_pairs == 4
    ):
        scheduled_w = max(scheduled_w, 8)
    w = _draw_exact_int(ctx, "grid_w", 7, 10, scheduled_w)
    source_uses = _draw_exact_int(ctx, "source_uses", 2, 3, int(defaults["source_uses"]))
    unchanged_targets = _draw_exact_int(ctx, "unchanged_targets", 0, 1, int(defaults["unchanged_targets"]))
    overlap = _draw_exact_choice(ctx, "mapping_overlap", MAPPING_OVERLAPS, str(defaults["mapping_overlap"]))

    scheduled_layout = str(defaults["legend_layout"])
    if (
        overrides.get("legend_layout") is None
        and scheduled_layout == "shifted_even"
        and 2 * n_pairs > w
    ):
        scheduled_layout = "scattered"
    layout = _draw_exact_choice(ctx, "legend_layout", LEGEND_LAYOUTS, scheduled_layout)

    if layout == "shifted_even" and 2 * n_pairs > w:
        raise _incompatible("shifted-even legend does not fit requested width", "legend_layout", "n_pairs", "grid_w")

    canonical = _CANONICAL_PROFILES.get(profile) if not overrides else None
    sources, destinations = _draw_palette(ctx, n_pairs, overlap, canonical)
    grid = full_grid(h, w, 0)
    rng = ctx.draw_rng("layout")
    legend_cols = _legend_columns(rng, w, n_pairs, layout)
    for column, source, destination in zip(legend_cols, sources, destinations):
        grid[0][column] = source
        grid[1][column] = destination

    stream: list[int] = []
    for source in sources:
        stream.extend([source] * source_uses)
    rng.shuffle(stream)
    target_only = [color for color in destinations if color not in set(sources)]
    if unchanged_targets:
        if not target_only:
            raise _incompatible("no destination-only color is available for unchanged witness", "mapping_overlap", "unchanged_targets")
        stream.append(rng.choice(target_only))

    positions = _body_positions(h, w, profile % 3, rng)
    if len(stream) >= 2 and len({r for r, _ in positions[: len(stream)]}) < 2:
        replacement_index = next(
            index
            for index, (r, _) in enumerate(positions[len(stream):], start=len(stream))
            if r != positions[0][0]
        )
        positions[1], positions[replacement_index] = positions[replacement_index], positions[1]
    if len(stream) > len(positions):
        raise _incompatible("requested body witnesses exceed grid capacity", "grid_h", "grid_w", "n_pairs", "source_uses", "unchanged_targets")
    for color, (r, c) in zip(stream, positions):
        grid[r][c] = color
    return grid


def _legend(grid: list[list[int]]) -> tuple[list[int], list[int], list[int]]:
    width = len(grid[0])
    columns = [c for c in range(width) if grid[0][c] != 0 or grid[1][c] != 0]
    sources = [grid[0][c] for c in columns]
    destinations = [grid[1][c] for c in columns]
    return columns, sources, destinations


def _solve_grid(grid: list[list[int]]) -> list[list[int]]:
    _, sources, destinations = _legend(grid)
    mapping = dict(zip(sources, destinations))
    return [[mapping.get(value, value) for value in row] for row in grid[2:]]


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Small input-pure Python mirror used only for tests and adversarial probes."""
    return _solve_grid(grid)


def observe_overrides(grid) -> dict[str, int | str]:
    """Recover every exact AXES value from one returned grid."""
    columns, sources, destinations = _legend(grid)
    source_set = set(sources)
    destination_set = set(destinations)
    body = [value for row in grid[2:] for value in row]
    source_counts = [body.count(source) for source in sources]
    canonical = list(range(0, 2 * len(columns), 2))
    shifted = list(range(1, 1 + 2 * len(columns), 2))
    if columns == canonical:
        layout = "canonical_even"
    elif columns == shifted:
        layout = "shifted_even"
    else:
        layout = "scattered"
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_pairs": len(columns),
        "source_uses": min(source_counts) if source_counts else 0,
        "unchanged_targets": sum(value in (destination_set - source_set) for value in body),
        "legend_layout": layout,
        "mapping_overlap": "chain" if source_set & destination_set else "disjoint",
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the authority-compatible sparse two-row legend grammar."""
    del difficulty, meta
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return ["grid must be a non-empty 2D list"]
    h, w = len(grid), len(grid[0])
    if any(not isinstance(row, list) or len(row) != w for row in grid):
        return ["grid rows must be rectangular"]

    errors: list[str] = []
    if not (7 <= h <= 10 and 7 <= w <= 10):
        errors.append(f"expected canonical-scale dimensions 7..10x7..10, got {h}x{w}")
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 9:
                errors.append(f"cell ({r},{c}) has invalid ARC color {value!r}")
    if errors:
        return errors

    columns, sources, destinations = _legend(grid)
    if not (2 <= len(columns) <= 4):
        errors.append(f"expected 2..4 legend columns, got {len(columns)}")
    if any(source == 0 or destination == 0 for source, destination in zip(sources, destinations)):
        errors.append("every legend column must have nonzero source and destination")
    if len(set(sources)) != len(sources):
        errors.append("legend sources must be unique")
    if len(set(destinations)) != len(destinations):
        errors.append("legend destinations must be unique")
    if any(source == destination for source, destination in zip(sources, destinations)):
        errors.append("identity legend pairs hide whether recoloring fired")
    overlap = set(sources) & set(destinations)
    if len(overlap) > 1:
        errors.append(f"at most one source/destination overlap is allowed, got {sorted(overlap)}")

    body = [value for row in grid[2:] for value in row]
    body_nz = [value for value in body if value != 0]
    if not body_nz:
        errors.append("body has no cells to transform")
    allowed = set(sources) | set(destinations)
    unknown = sorted(set(body_nz) - allowed)
    if unknown:
        errors.append(f"body uses colors outside source/destination roles: {unknown}")
    missing_sources = [source for source in sources if source not in body_nz]
    if missing_sources:
        errors.append(f"body fails to exercise legend sources: {missing_sources}")
    unchanged_count = sum(value in (set(destinations) - set(sources)) for value in body)
    if unchanged_count > 1:
        errors.append(f"expected at most one destination-only unchanged witness, got {unchanged_count}")
    if len(body_nz) > 14:
        errors.append(f"body is too dense for the sparse canonical family: {len(body_nz)} nonzero cells")
    occupied_rows = {r for r in range(2, h) if any(grid[r][c] != 0 for c in range(w))}
    if len(occupied_rows) < 2:
        errors.append("body must occupy at least two rows to avoid a one-row template shortcut")
    return errors


def strict_canonical_like(grid) -> list[str]:
    return self_check(grid)


def _has_non_even_key(grid: list[list[int]]) -> bool:
    columns, _, _ = _legend(grid)
    return any(column % 2 for column in columns)


def _has_chain(grid: list[list[int]]) -> bool:
    _, sources, destinations = _legend(grid)
    return bool(set(sources) & set(destinations))


def _has_unchanged_target(grid: list[list[int]]) -> bool:
    return int(observe_overrides(grid)["unchanged_targets"]) == 1


SEMANTIC_WITNESSES: dict[str, Callable[[list[list[int]]], bool]] = {
    "two_pair_key": lambda grid: len(_legend(grid)[0]) == 2,
    "three_or_four_pair_key": lambda grid: len(_legend(grid)[0]) >= 3,
    "non_even_legend_column": _has_non_even_key,
    "one_step_chain_mapping": _has_chain,
    "disjoint_mapping_palette": lambda grid: not _has_chain(grid),
    "destination_only_unchanged_body_cell": _has_unchanged_target,
    "sparse_multiline_body": lambda grid: len({r for r in range(2, len(grid)) if any(grid[r])}) >= 2,
}


def _drop_only_rival(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in grid[2:]]


def _keep_legend_rival(grid: list[list[int]]) -> list[list[int]]:
    _, sources, destinations = _legend(grid)
    mapping = dict(zip(sources, destinations))
    return [[mapping.get(value, value) for value in row] for row in grid]


def _fixed_even_key_rival(grid: list[list[int]]) -> list[list[int]]:
    mapping = {
        grid[0][column]: grid[1][column]
        for column in range(0, len(grid[0]), 2)
        if grid[0][column] and grid[1][column]
    }
    return [[mapping.get(value, value) for value in row] for row in grid[2:]]


def _cascade_rival(grid: list[list[int]]) -> list[list[int]]:
    _, sources, destinations = _legend(grid)
    mapping = dict(zip(sources, destinations))

    def cascade(value: int) -> int:
        seen: set[int] = set()
        while value in mapping and value not in seen:
            seen.add(value)
            value = mapping[value]
        return value

    return [[cascade(value) for value in row] for row in grid[2:]]


def _recolor_all_nonzero_rival(grid: list[list[int]]) -> list[list[int]]:
    _, _, destinations = _legend(grid)
    target = destinations[0]
    return [[target if value else 0 for value in row] for row in grid[2:]]


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "drop_only": _drop_only_rival,
    "keep_legend": _keep_legend_rival,
    "fixed_even_key": _fixed_even_key_rival,
    "cascade_mapping": _cascade_rival,
    "recolor_all_nonzero": _recolor_all_nonzero_rival,
}

WITNESS_RIVALS = {
    "two_pair_key": ["keep_legend"],
    "three_or_four_pair_key": ["drop_only"],
    "non_even_legend_column": ["fixed_even_key"],
    "one_step_chain_mapping": ["cascade_mapping"],
    "disjoint_mapping_palette": ["drop_only"],
    "destination_only_unchanged_body_cell": ["recolor_all_nonzero"],
    "sparse_multiline_body": ["keep_legend"],
}

LESSON_COMPETITORS = SEMANTIC_RIVALS


def lesson_identifiable(demos, query) -> list[str]:
    """Reject a lesson when named plausible shortcuts survive its demos."""
    if not isinstance(demos, list) or not demos:
        return ["at least one demonstration is required"]
    reasons: list[str] = []
    pairs = [*demos, query]
    for index, pair in enumerate(pairs):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"pair {index} is missing input/output")
            continue
        if pair["output"] != _solve_grid(pair["input"]):
            reasons.append(f"pair {index} output disagrees with one-step legend recoloring")

    rivals: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
        "drop the first two rows without recoloring": _drop_only_rival,
        "recolor but keep the legend rows": _keep_legend_rival,
        "read only fixed even legend columns": _fixed_even_key_rival,
        "apply the mapping repeatedly until stable": _cascade_rival,
        "replace every nonzero body cell by one target": _recolor_all_nonzero_rival,
    }
    for name, rival in rivals.items():
        if all(rival(demo["input"]) == demo["output"] for demo in demos):
            if rival(query["input"]) != query["output"]:
                reasons.append(f"demonstrations do not refute rival: {name}")
    return reasons
