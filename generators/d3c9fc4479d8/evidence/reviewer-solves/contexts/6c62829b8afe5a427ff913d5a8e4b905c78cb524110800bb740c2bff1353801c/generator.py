"""Generator for ``d3c9fc4479d8`` — apply a top-row color legend.

The first row is a compact sequence of adjacent ``source -> target`` pairs.
The output drops that row and applies the mapping once to every body cell,
preserving colors that are not source keys.

This sampler keeps two exact canonical shape/palette anchors in every band and
adds three counterexample branches that the public examples do not supply:
shifted legends, one-step mapping chains, and preserved unmapped controls.
"""
from __future__ import annotations

from collections import deque
from typing import Any, Callable, Sequence

from puzzle_generators.base import gen_ctx, stable_rng
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "d3c9fc4479d8"
TASK_ID = GENERATOR_ID
RULE_HASH = "08068e7e2317"
VERSION = "2.0.0"
SUMMARY = (
    "Read row 0 as adjacent old->new color pairs, drop the legend row, and "
    "replace each body source color once while preserving unmapped cells."
)

INVARIANTS = [
    "row 0 contains exactly two or three compact adjacent source->target pairs",
    "source keys and target values are individually distinct and never identity pairs",
    "every source appears in one 8-connected body component of two to four cells",
    "the body contains at most one unmapped control cell",
]

AXES = {
    "grid_h": {"type": "int", "default": "four-slot curriculum; 4..10", "valid": "4..10"},
    "grid_w": {"type": "int", "default": "four-slot curriculum; 7..14", "valid": "7..14"},
    "n_pairs": {"type": "int", "default": "scheduled 2 or 3", "valid": "2..3"},
    "source_uses": {"type": "int", "default": "scheduled 2..4", "valid": "2..4"},
    "legend_offset": {"type": "int", "default": "scheduled 0 or 1", "valid": "0..1"},
    "mapping_overlap": {
        "type": "str",
        "default": "scheduled disjoint or one-step chain",
        "valid": "disjoint|chain",
    },
    "control_kind": {
        "type": "str",
        "default": "scheduled preserved target or neutral cell",
        "valid": "none|target|neutral",
    },
}

# Every Cartesian combination of the exact axes above is constructible.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []

SCHEDULE_PROFILES = (
    "canonical_two_with_control",
    "chain_two_shifted",
    "canonical_three_with_control",
    "chain_three_shifted",
)
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

_INT_BOUNDS = {
    "grid_h": (4, 10),
    "grid_w": (7, 14),
    "n_pairs": (2, 3),
    "source_uses": (2, 4),
    "legend_offset": (0, 1),
}
_ENUMS = {
    "mapping_overlap": ("disjoint", "chain"),
    "control_kind": ("none", "target", "neutral"),
}


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Return the four-slot curriculum profile for this sample index."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _band(difficulty) -> str:
    if difficulty is None:
        return "medium"
    if difficulty not in ("easy", "medium", "hard"):
        raise ValueError(
            "difficulty must be one of None, 'easy', 'medium', or 'hard'; "
            f"got {difficulty!r}"
        )
    return difficulty


def _profile_defaults(seed: int, sample_index: int, difficulty) -> dict[str, object]:
    """Exact scheduled defaults; explicit caller overrides are layered on top."""
    band = _band(difficulty)
    profile = schedule_profile(seed, sample_index, band)
    rng = stable_rng(
        int(seed),
        f"{TASK_ID}|{int(sample_index)}|scheduled-dimensions|{band}",
        VERSION,
    )
    broad_ranges = {
        "easy": ((5, 6), (9, 10)),
        "medium": ((6, 8), (10, 12)),
        "hard": ((8, 10), (12, 14)),
    }
    (h_lo, h_hi), (w_lo, w_hi) = broad_ranges[band]
    broad_h = rng.randint(h_lo, h_hi)
    broad_w = rng.randint(w_lo, w_hi)
    table: dict[str, dict[str, object]] = {
        # Exact canonical coarse profiles: (h,w,palette)=(4,7,5) and (4,8,7).
        "canonical_two_with_control": {
            "grid_h": 4,
            "grid_w": 7,
            "n_pairs": 2,
            "source_uses": 3,
            "legend_offset": 0,
            "mapping_overlap": "disjoint",
            "control_kind": "target",
        },
        "chain_two_shifted": {
            "grid_h": broad_h,
            "grid_w": broad_w,
            "n_pairs": 2,
            "source_uses": 4,
            "legend_offset": 1,
            "mapping_overlap": "chain",
            "control_kind": "neutral",
        },
        "canonical_three_with_control": {
            "grid_h": 4,
            "grid_w": 8,
            "n_pairs": 3,
            "source_uses": 2,
            "legend_offset": 0,
            "mapping_overlap": "disjoint",
            "control_kind": "target",
        },
        "chain_three_shifted": {
            "grid_h": broad_h,
            "grid_w": broad_w,
            "n_pairs": 3,
            "source_uses": 3,
            "legend_offset": 1,
            "mapping_overlap": "chain",
            "control_kind": "target",
        },
    }
    return table[profile]


def _validate_overrides(overrides: dict[str, object]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override axis/axes: " + ", ".join(unknown))
    for name, (lo, hi) in _INT_BOUNDS.items():
        value = overrides.get(name)
        if value is None:
            continue
        if isinstance(value, bool) or type(value) is not int:
            raise ValueError(f"{name} must be an integer, not {type(value).__name__}")
        if not lo <= value <= hi:
            raise ValueError(f"{name}={value} outside [{lo}, {hi}]")
    for name, options in _ENUMS.items():
        value = overrides.get(name)
        if value is None:
            continue
        if type(value) is not str or value not in options:
            raise ValueError(f"{name}={value!r} must be one of {options}")


def _shape(size: int, orientation: int) -> tuple[tuple[int, int], ...]:
    if size == 2:
        options = (
            ((0, 0), (0, 1)),
            ((1, 0), (1, 1)),
            ((0, 0), (1, 0)),
            ((0, 1), (1, 1)),
        )
    elif size == 3:
        square = {(0, 0), (0, 1), (1, 0), (1, 1)}
        options = tuple(tuple(sorted(square - {missing})) for missing in sorted(square))
    elif size == 4:
        options = (((0, 0), (0, 1), (1, 0), (1, 1)),)
    else:  # guarded by exact axis validation
        raise ValueError(f"unsupported source_uses={size}")
    return options[orientation % len(options)]


def _mapping_colors(ctx, n_pairs: int, overlap: str):
    colors = list(range(1, 10))
    ctx.draw_rng("palette").shuffle(colors)
    sources = colors[:n_pairs]
    cursor = n_pairs
    if overlap == "disjoint":
        targets = colors[cursor : cursor + n_pairs]
        cursor += n_pairs
    else:
        # a->b and b->d is an acyclic one-step chain; remaining pairs stay disjoint
        targets = [sources[1], *colors[cursor : cursor + n_pairs - 1]]
        cursor += n_pairs - 1
    neutral = colors[cursor]
    return sources, targets, neutral


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Generate one deterministic lawful input; labels remain Racket-owned."""
    _validate_overrides(overrides)
    defaults = _profile_defaults(int(seed), int(sample_index), difficulty)
    effective = dict(defaults)
    effective.update({name: value for name, value in overrides.items() if value is not None})
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective,
    )
    height = ctx.draw_int("grid_h", 4, 10)
    width = ctx.draw_int("grid_w", 7, 14)
    n_pairs = ctx.draw_int("n_pairs", 2, 3)
    source_uses = ctx.draw_int("source_uses", 2, 4)
    legend_offset = ctx.draw_int("legend_offset", 0, 1)
    overlap = ctx.draw_choice("mapping_overlap", _ENUMS["mapping_overlap"])
    control = ctx.draw_choice("control_kind", _ENUMS["control_kind"])

    grid = full_grid(height, width, 0)
    sources, targets, neutral = _mapping_colors(ctx, n_pairs, overlap)
    for index, (source, target) in enumerate(zip(sources, targets)):
        column = legend_offset + 2 * index
        grid[0][column] = source
        grid[0][column + 1] = target

    layout_rng = ctx.draw_rng("source-layout")
    slot_start = layout_rng.randint(0, width - 2 * n_pairs)
    top_row = layout_rng.randint(1, height - 2)
    slots = list(range(n_pairs))
    layout_rng.shuffle(slots)
    for source, slot in zip(sources, slots):
        base_column = slot_start + 2 * slot
        orientation = layout_rng.randrange(4)
        for dr, dc in _shape(source_uses, orientation):
            grid[top_row + dr][base_column + dc] = source

    if control != "none":
        control_color = targets[-1] if control == "target" else neutral
        candidates = [
            (r, c)
            for r in range(1, height)
            for c in range(width)
            if grid[r][c] == 0
        ]
        r, c = ctx.draw_rng("control-position").choice(candidates)
        grid[r][c] = control_color

    errors = self_check(grid)
    if errors:
        raise RuntimeError("internal generator invariant failed: " + "; ".join(errors))
    observed = observe_overrides(grid)
    requested = {
        "grid_h": height,
        "grid_w": width,
        "n_pairs": n_pairs,
        "source_uses": source_uses,
        "legend_offset": legend_offset,
        "mapping_overlap": overlap,
        "control_kind": control,
    }
    if observed != requested:
        raise RuntimeError(f"realized exact axes {observed} disagree with {requested}")
    return grid


def _grid_error(grid: Any) -> str | None:
    if not isinstance(grid, (list, tuple)) or not grid:
        return "expected a nonempty grid"
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return "expected nonempty rows"
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return "grid must be rectangular"
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if isinstance(value, bool) or type(value) is not int or not 0 <= value <= 9:
                return f"cell ({r},{c}) must be an integer ARC color 0..9"
    return None


def _parse_legend(grid: Sequence[Sequence[int]]):
    """Mirror the canonical Racket scanner and retain consumed columns."""
    row = grid[0]
    pairs: list[tuple[int, int]] = []
    starts: list[int] = []
    consumed: set[int] = set()
    column = 0
    while column + 1 < len(row):
        left, right = row[column], row[column + 1]
        if left != 0 and right != 0:
            pairs.append((int(left), int(right)))
            starts.append(column)
            consumed.update((column, column + 1))
            column += 2
        else:
            column += 1
    isolated = [column for column, value in enumerate(row) if value != 0 and column not in consumed]
    return pairs, starts, isolated


def _connected(points: set[tuple[int, int]]) -> bool:
    if not points:
        return False
    seen = {next(iter(points))}
    queue = deque(seen)
    while queue:
        r, c = queue.popleft()
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                neighbor = (r + dr, c + dc)
                if neighbor in points and neighbor not in seen:
                    seen.add(neighbor)
                    queue.append(neighbor)
    return seen == points


def _analysis(grid: Any) -> tuple[list[str], dict[str, object]]:
    error = _grid_error(grid)
    if error:
        return [error], {}
    height, width = len(grid), len(grid[0])
    errors: list[str] = []
    if not 4 <= height <= 10:
        errors.append(f"input height {height} outside 4..10")
    # Width 6 is retained for the third canonical pair; generated exact axes start at 7.
    if not 6 <= width <= 14:
        errors.append(f"input width {width} outside 6..14")

    pairs, starts, isolated = _parse_legend(grid)
    if isolated:
        errors.append(f"legend has isolated nonzero columns {isolated}")
    if not 2 <= len(pairs) <= 3:
        errors.append(f"expected exactly 2 or 3 legend pairs, found {len(pairs)}")
    if starts:
        offset = starts[0]
        expected_starts = list(range(offset, offset + 2 * len(pairs), 2))
        if offset not in (0, 1) or starts != expected_starts:
            errors.append(
                "legend pairs must be compact and start at column 0 or 1; "
                f"found starts {starts}"
            )
    else:
        offset = -1

    sources = [source for source, _ in pairs]
    targets = [target for _, target in pairs]
    if len(set(sources)) != len(sources):
        errors.append("legend source keys must be distinct")
    if len(set(targets)) != len(targets):
        errors.append("legend target values must be distinct")
    if any(source == target for source, target in pairs):
        errors.append("legend may not contain identity mappings")

    overlap = set(sources) & set(targets)
    if not overlap:
        overlap_kind = "disjoint"
    elif (
        len(sources) >= 2
        and overlap == {sources[1]}
        and targets
        and targets[0] == sources[1]
    ):
        overlap_kind = "chain"
    else:
        overlap_kind = "invalid"
        errors.append(
            "source/target overlap must be empty or the one-step chain "
            "target[0] == source[1]"
        )

    counts: list[int] = []
    source_set = set(sources)
    for source in sources:
        points = {
            (r, c)
            for r in range(1, height)
            for c, value in enumerate(grid[r])
            if value == source
        }
        counts.append(len(points))
        if not 2 <= len(points) <= 4:
            errors.append(f"source color {source} must occur 2..4 times; found {len(points)}")
        elif not _connected(points):
            errors.append(f"source color {source} must form one 8-connected component")

    controls = [
        (r, c, value)
        for r in range(1, height)
        for c, value in enumerate(grid[r])
        if value != 0 and value not in source_set
    ]
    if len(controls) > 1:
        errors.append(f"body may contain at most one unmapped control cell; found {len(controls)}")
    if not controls:
        control_kind = "none"
    else:
        control_value = controls[0][2]
        target_only = set(targets) - source_set
        control_kind = "target" if control_value in target_only else "neutral"

    uniform_uses: int | None
    uniform_uses = counts[0] if counts and len(set(counts)) == 1 else None
    facts: dict[str, object] = {
        "grid_h": height,
        "grid_w": width,
        "n_pairs": len(pairs),
        "source_uses": uniform_uses,
        "legend_offset": offset,
        "mapping_overlap": overlap_kind,
        "control_kind": control_kind,
        "pairs": pairs,
        "sources": sources,
        "targets": targets,
        "controls": controls,
    }
    return errors, facts


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the task-lawful sampler manifold and canonical examples."""
    del difficulty, meta
    return _analysis(grid)[0]


def strict_canonical_like(grid) -> list[str]:
    """All ordinary draws are on the task's strict structural manifold."""
    return self_check(grid)


def observe_overrides(grid) -> dict[str, object]:
    errors, facts = _analysis(grid)
    if errors or facts.get("source_uses") is None:
        return {}
    return {name: facts[name] for name in AXES}


def _mapping(grid: Sequence[Sequence[int]]) -> dict[int, int]:
    return {source: target for source, target in _parse_legend(grid)[0]}


def rule_mirror(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    """Pure Python mirror of the pinned canonical Racket rule."""
    mapping = _mapping(grid)
    return [[mapping.get(int(value), int(value)) for value in row] for row in grid[1:]]


def _drop_without_recoloring(grid):
    return [list(row) for row in grid[1:]]


def _reverse_pairs(grid):
    reverse = {target: source for source, target in _parse_legend(grid)[0]}
    return [[reverse.get(int(value), int(value)) for value in row] for row in grid[1:]]


def _keep_legend(grid):
    return [list(grid[0]), *rule_mirror(grid)]


def _fixed_origin_pairs(grid):
    mapping: dict[int, int] = {}
    for column in range(0, len(grid[0]) - 1, 2):
        source, target = grid[0][column], grid[0][column + 1]
        if source != 0 and target != 0:
            mapping[int(source)] = int(target)
    return [[mapping.get(int(value), int(value)) for value in row] for row in grid[1:]]


def _cascade_mapping(grid):
    mapping = _mapping(grid)
    output: list[list[int]] = []
    for row in grid[1:]:
        result = []
        for raw in row:
            value = int(raw)
            seen: set[int] = set()
            while value in mapping and value not in seen:
                seen.add(value)
                value = mapping[value]
            result.append(value)
        output.append(result)
    return output


def _erase_unmapped(grid):
    mapping = _mapping(grid)
    return [
        [mapping[value] if value in mapping else 0 for value in row]
        for row in grid[1:]
    ]


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "drop_without_recoloring": _drop_without_recoloring,
    "reverse_pairs": _reverse_pairs,
    "keep_legend": _keep_legend,
    "fixed_origin_pairs": _fixed_origin_pairs,
    "cascade_mapping": _cascade_mapping,
    "erase_unmapped": _erase_unmapped,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS
CANONICAL_SHORTCUTS = {
    "fixed_origin_pairs": _fixed_origin_pairs,
    "cascade_mapping": _cascade_mapping,
    "erase_unmapped": _erase_unmapped,
}


def _has_shifted_legend(grid) -> bool:
    errors, facts = _analysis(grid)
    return not errors and facts["legend_offset"] == 1


def _has_mapping_chain(grid) -> bool:
    errors, facts = _analysis(grid)
    return not errors and facts["mapping_overlap"] == "chain"


def _has_preserved_control(grid) -> bool:
    errors, facts = _analysis(grid)
    return not errors and facts["control_kind"] != "none"


SEMANTIC_WITNESSES = {
    "shifted_legend": _has_shifted_legend,
    "mapping_chain": _has_mapping_chain,
    "preserved_unmapped_control": _has_preserved_control,
}
WITNESS_RIVALS = {
    "shifted_legend": ["fixed_origin_pairs"],
    "mapping_chain": ["cascade_mapping"],
    "preserved_unmapped_control": ["erase_unmapped"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Name every declared rival that survives demos but flips the query."""
    reasons: list[str] = []
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            if rival(query["input"]) != query["output"]:
                reasons.append(f"{name} fits every demonstration but disagrees on the query")
    return reasons
