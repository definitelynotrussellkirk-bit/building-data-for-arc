"""Generator for 8c6fbfbe20d4 — nonzero-list color legend + body recolor.

The selected Racket rule reads every non-zero value of row 0 from left to
right as ``sources`` and every non-zero value of row 1 as ``targets``.  It
pairs the first ``min(len(sources), len(targets))`` list entries, removes both
legend rows, recolors body cells through that map, and preserves every
unmapped body value.

The canonical examples are deliberately easy to misread as a positional
column legend.  Their two header rows contain holes, the holes are not aligned,
and the target list has one extra color.  Ordinary lessons below therefore
vary list lengths, header positions, and unmapped body controls so the data
identifies non-zero *list order* rather than same-column or sorted-color
shortcuts.
"""
from __future__ import annotations

from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "8c6fbfbe20d4"
TASK_ID = GENERATOR_ID
VERSION = "3.1.0"
RULE_HASH = "27daa6126c50"

SUMMARY = (
    "Rows 0 and 1 are independent sparse color lists: scan each row left-to-"
    "right and discard zeros. Pair the first min(source_count, target_count) "
    "entries. Rows 2+ are the body. The output removes both header rows, "
    "recolors paired source values, and preserves zeros, unpaired sources, "
    "target-colored distractors, and other unmapped body values."
)

INVARIANTS = [
    "background is 0 and the input is a rectangular 5..12 by 5..14 ARC grid",
    "row 0 has 2..4 distinct non-zero source colors; row 1 has 2..5 distinct non-zero target colors",
    "source and target color sets are disjoint; header non-zero positions are independent and may contain gaps",
    "the body contains every row-0 source at least once, including any source left unpaired by a shorter target list",
    "the body has at most four non-zero cells outside the row-0 source set; those values are preserved by the rule",
    "the output is exactly rows 2+ with one-step source→target substitution over the paired non-zero lists",
]

EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0

# Four consecutive samples cover all profiles, which makes every four-demo
# lesson exercise both unequal-list branches plus an unmapped-body control.
SCHEDULE_PROFILES = (
    "canonical_extra_target",
    "equal_gapped_controls",
    "source_extra_preserved",
    "target_extra_controls",
)

AXES = {
    "N": {
        "type": "int",
        "default": "scheduled/band draw",
        "valid": "2..4",
        "doc": "Number of non-zero source entries in row 0.",
    },
    "target_n": {
        "type": "int",
        "default": "scheduled near N",
        "valid": "2..5",
        "doc": "Number of non-zero target entries in row 1.",
    },
    "body_h": {
        "type": "int",
        "default": "scheduled/band draw",
        "valid": "3..10",
        "doc": "Body height; total input height is body_h + 2.",
    },
    "grid_w": {
        "type": "int",
        "default": "scheduled/band draw",
        "valid": "5..14",
        "doc": "Input/output width. Both sparse header lists fit independently.",
    },
    "n_unmapped": {
        "type": "int",
        "default": "scheduled/band draw",
        "valid": "0..4",
        "doc": "Number of non-zero body cells whose colors are outside the row-0 source set.",
    },
}

# Every Cartesian boundary combination of the five declared axes is supported.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, Any], ...] = ()
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()


def _band(difficulty: Any) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return str(difficulty)
    raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Return the deterministic four-slot semantic curriculum profile."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> None:
    _band(difficulty)
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    for name, value in overrides.items():
        if value is None:
            continue
        if isinstance(value, bool) or type(value) is not int:
            raise ValueError(f"{name} must be an integer")


def _draw_axis(ctx, overrides, label: str, default_lo: int, default_hi: int,
               valid_lo: int, valid_hi: int) -> int:
    """Honor the full declared domain for overrides, band shape for defaults."""
    if overrides.get(label) is not None:
        return ctx.draw_int(label, valid_lo, valid_hi)
    return ctx.draw_int(label, default_lo, default_hi)


def _default_parameters(ctx, overrides, profile: str, difficulty: Any):
    """Draw exact axes without making difficulty shrink the override domain."""
    # Canonical-scale anchors are present in every difficulty band. Their
    # palette is exactly {0} + 3 sources + 4 targets = 8 colors, matching both
    # canonical coarse profiles (5x6x8 and 5x7x8).
    if profile == "canonical_extra_target":
        n = _draw_axis(ctx, overrides, "N", 3, 3, 2, 4)
        target_n = _draw_axis(ctx, overrides, "target_n", 4, 4, 2, 5)
        body_h = _draw_axis(ctx, overrides, "body_h", 3, 3, 3, 10)
        width_default = 6 + (int(ctx.sample_index) & 1)
        grid_w = _draw_axis(
            ctx, overrides, "grid_w", width_default, width_default, 5, 14
        )
        n_unmapped = _draw_axis(ctx, overrides, "n_unmapped", 0, 0, 0, 4)
        return n, target_n, body_h, grid_w, n_unmapped

    band = _band(difficulty)
    if band == "easy":
        n_range = (2, 3)
        body_range = (3, 5)
        width_range = (5, 8)
        unmapped_range = (1, 2)
    elif band == "hard":
        n_range = (3, 4)
        body_range = (6, 10)
        width_range = (9, 14)
        unmapped_range = (2, 4)
    else:
        n_range = (2, 4)
        body_range = (4, 7)
        width_range = (6, 11)
        unmapped_range = (1, 3)

    if profile == "source_extra_preserved":
        # This scheduled branch must actually contain an unpaired source in
        # every band, so its default source list starts at three entries.
        profile_n_range = (max(3, n_range[0]), max(3, n_range[1]))
    else:
        profile_n_range = n_range
    n = _draw_axis(ctx, overrides, "N", *profile_n_range, 2, 4)

    if profile == "source_extra_preserved":
        default_target_lo = default_target_hi = max(2, n - 1)
    elif profile == "target_extra_controls":
        default_target_lo = default_target_hi = min(5, n + 1)
    else:  # equal_gapped_controls
        default_target_lo = default_target_hi = n
    target_n = _draw_axis(
        ctx, overrides, "target_n",
        default_target_lo, default_target_hi, 2, 5,
    )
    body_h = _draw_axis(ctx, overrides, "body_h", *body_range, 3, 10)

    # Default width leaves room for at least one zero in both headers. An
    # explicit width=5 remains valid even when target_n=5; that is a lawful
    # non-gapped override edge and is intentionally observable.
    min_default_w = max(width_range[0], n + 1, target_n + 1)
    max_default_w = max(min_default_w, width_range[1])
    grid_w = _draw_axis(
        ctx, overrides, "grid_w", min_default_w, max_default_w, 5, 14
    )

    if profile == "source_extra_preserved":
        default_unmapped = max(1, unmapped_range[0])
        n_unmapped = _draw_axis(
            ctx, overrides, "n_unmapped",
            default_unmapped, min(default_unmapped + 1, unmapped_range[1]),
            0, 4,
        )
    elif profile == "equal_gapped_controls":
        # A complete four-profile lesson must distinguish the intended rule
        # from the stronger legend-union shortcut that preserves source and
        # target colors but erases values absent from both headers.  Two
        # controls let this profile carry one target-colored distractor and
        # one truly neutral distractor in every default draw.
        lo = max(2, unmapped_range[0])
        hi = max(lo, unmapped_range[1])
        n_unmapped = _draw_axis(
            ctx, overrides, "n_unmapped", lo, hi, 0, 4
        )
    elif profile == "target_extra_controls":
        lo = max(1, unmapped_range[0])
        n_unmapped = _draw_axis(
            ctx, overrides, "n_unmapped", lo, unmapped_range[1], 0, 4
        )
    else:
        n_unmapped = _draw_axis(
            ctx, overrides, "n_unmapped", *unmapped_range, 0, 4
        )
    return n, target_n, body_h, grid_w, n_unmapped


def _coerce_grid(grid: Any) -> tuple[list[list[int]] | None, list[str]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return None, ["grid must be a non-empty sequence of rows"]
    first = grid[0]
    if not isinstance(first, (list, tuple, str)) or not first:
        return None, ["grid rows must be non-empty sequences"]
    width = len(first)
    out: list[list[int]] = []
    for row in grid:
        if not isinstance(row, (list, tuple, str)) or len(row) != width:
            return None, ["grid must be rectangular"]
        out_row: list[int] = []
        for value in row:
            if isinstance(value, bool):
                return None, ["cells must be literal ARC integers 0..9"]
            if isinstance(value, int):
                parsed = value
            elif isinstance(value, str) and len(value) == 1 and value.isdigit():
                parsed = int(value)
            else:
                return None, [f"non-integer cell value {value!r}"]
            if not 0 <= parsed <= 9:
                return None, [f"cell value {parsed} outside ARC palette 0..9"]
            out_row.append(parsed)
        out.append(out_row)
    return out, []


def _analysis(grid: Any) -> dict[str, Any]:
    g, errors = _coerce_grid(grid)
    if errors:
        return {"errors": errors}
    assert g is not None
    height, width = len(g), len(g[0])
    if height < 2:
        return {"errors": ["grid needs two header rows"]}
    sources = [value for value in g[0] if value != 0]
    targets = [value for value in g[1] if value != 0]
    pair_n = min(len(sources), len(targets))
    mapping = dict(zip(sources[:pair_n], targets[:pair_n]))
    source_set = set(sources)
    body_nonzero = [value for row in g[2:] for value in row if value != 0]
    source_counts = {source: body_nonzero.count(source) for source in sources}
    unmapped_outside_sources = [
        value for value in body_nonzero if value not in source_set
    ]
    return {
        "errors": [],
        "grid": g,
        "height": height,
        "width": width,
        "sources": sources,
        "targets": targets,
        "pair_n": pair_n,
        "mapping": mapping,
        "body_nonzero": body_nonzero,
        "source_counts": source_counts,
        "unmapped_outside_sources": unmapped_outside_sources,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the full teaching grammar while accepting every canonical input."""
    del difficulty, meta
    analysis = _analysis(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors

    height = analysis["height"]
    width = analysis["width"]
    sources = analysis["sources"]
    targets = analysis["targets"]
    source_counts = analysis["source_counts"]
    unmapped = analysis["unmapped_outside_sources"]

    if not 5 <= height <= 12:
        errors.append(f"height {height} outside 5..12")
    if not 5 <= width <= 14:
        errors.append(f"width {width} outside 5..14")
    if not 2 <= len(sources) <= 4:
        errors.append(f"row 0 has {len(sources)} source colors; expected 2..4")
    if not 2 <= len(targets) <= 5:
        errors.append(f"row 1 has {len(targets)} target colors; expected 2..5")
    if len(set(sources)) != len(sources):
        errors.append("source colors in row 0 must be distinct")
    if len(set(targets)) != len(targets):
        errors.append("target colors in row 1 must be distinct")
    if set(sources) & set(targets):
        errors.append("source and target color sets must be disjoint")
    missing = [source for source, count in source_counts.items() if count == 0]
    if missing:
        errors.append(f"body must contain every source color; missing {missing}")
    if len(unmapped) > 4:
        errors.append(
            f"body has {len(unmapped)} cells outside the source set; expected at most 4"
        )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Recognize the canonical semantic manifold, not merely coarse dimensions."""
    errors = self_check(grid)
    if errors:
        return errors
    analysis = _analysis(grid)
    sources = analysis["sources"]
    targets = analysis["targets"]
    g = analysis["grid"]
    if abs(len(sources) - len(targets)) > 1:
        errors.append("canonical-like lessons keep source/target list lengths within one")
    if 0 not in g[0] or 0 not in g[1]:
        errors.append("canonical-like headers retain at least one zero separator/background cell")
    return errors


def observe_overrides(grid) -> dict[str, int]:
    """Recover every declared exact axis from the returned input grid."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError(f"cannot observe malformed grid: {analysis['errors']}")
    return {
        "N": len(analysis["sources"]),
        "target_n": len(analysis["targets"]),
        "body_h": analysis["height"] - 2,
        "grid_w": analysis["width"],
        "n_unmapped": len(analysis["unmapped_outside_sources"]),
    }


def rule_mirror(grid) -> list[list[int]]:
    """Pure Python spelling of the selected Racket rule for semantic probes."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError(f"malformed legend grid: {analysis['errors']}")
    g = analysis["grid"]
    mapping = analysis["mapping"]
    return [
        [mapping.get(value, value) for value in row]
        for row in g[2:]
    ]


def _same_column_rival(grid) -> list[list[int]]:
    """Wrong rule: pair only non-zero header values occupying the same column."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        return []
    g = analysis["grid"]
    mapping = {
        g[0][col]: g[1][col]
        for col in range(analysis["width"])
        if g[0][col] != 0 and g[1][col] != 0
    }
    return [[mapping.get(value, value) for value in row] for row in g[2:]]


def _sorted_rank_rival(grid) -> list[list[int]]:
    """Wrong rule: sort source/target colors before pairing by numeric rank."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        return []
    sources = sorted(analysis["sources"])
    targets = sorted(analysis["targets"])
    mapping = dict(zip(sources, targets))
    return [
        [mapping.get(value, value) for value in row]
        for row in analysis["grid"][2:]
    ]


def _right_aligned_rival(grid) -> list[list[int]]:
    """Wrong rule: align unequal non-zero header lists from their right ends."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        return []
    sources = analysis["sources"]
    targets = analysis["targets"]
    n = min(len(sources), len(targets))
    mapping = dict(zip(sources[-n:], targets[-n:]))
    return [
        [mapping.get(value, value) for value in row]
        for row in analysis["grid"][2:]
    ]


def _erase_unmapped_rival(grid) -> list[list[int]]:
    """Wrong rule: recolor paired sources but erase every other non-zero body cell."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        return []
    mapping = analysis["mapping"]
    return [
        [0 if value != 0 and value not in mapping else mapping.get(value, value)
         for value in row]
        for row in analysis["grid"][2:]
    ]


def _erase_neutral_rival(grid) -> list[list[int]]:
    """Wrong rule: preserve only body colors named in either header list."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        return []
    mentioned = set(analysis["sources"]) | set(analysis["targets"])
    mapping = analysis["mapping"]
    return [
        [
            mapping.get(value, value)
            if value == 0 or value in mentioned
            else 0
            for value in row
        ]
        for row in analysis["grid"][2:]
    ]


def _retain_headers_rival(grid) -> list[list[int]]:
    """Wrong rule: recolor the body but keep the two legend rows in the output."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        return []
    return [list(row) for row in analysis["grid"][:2]] + rule_mirror(grid)


SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "same_column_pairing": _same_column_rival,
    "sorted_color_rank_pairing": _sorted_rank_rival,
    "right_align_unequal_lists": _right_aligned_rival,
    "erase_unmapped_body": _erase_unmapped_rival,
    "erase_body_colors_absent_from_headers": _erase_neutral_rival,
    "retain_header_rows": _retain_headers_rival,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)

# The public pairs contain only paired source colors in the body.  Both
# erasing every unmapped value and the stronger legend-union filter are thus
# answer-equivalent on all three canonical examples.  Generated target-colored
# and truly neutral controls are required to falsify both shortcuts.
CANONICAL_SHORTCUTS = {
    "erase_unmapped_body": _erase_unmapped_rival,
    "erase_body_colors_absent_from_headers": _erase_neutral_rival,
}


def _source_columns(grid) -> tuple[int, ...]:
    return tuple(i for i, value in enumerate(grid[0]) if value != 0)


def _target_columns(grid) -> tuple[int, ...]:
    return tuple(i for i, value in enumerate(grid[1]) if value != 0)


def _has_unpaired_source(grid) -> bool:
    analysis = _analysis(grid)
    if analysis["errors"] or len(analysis["sources"]) <= len(analysis["targets"]):
        return False
    unpaired = set(analysis["sources"][analysis["pair_n"]:])
    return any(value in unpaired for value in analysis["body_nonzero"])


def _has_outside_source_control(grid) -> bool:
    analysis = _analysis(grid)
    return bool(not analysis["errors"] and analysis["unmapped_outside_sources"])


def _has_neutral_control(grid) -> bool:
    analysis = _analysis(grid)
    if analysis["errors"]:
        return False
    mentioned = set(analysis["sources"]) | set(analysis["targets"])
    return any(
        value != 0 and value not in mentioned
        for value in analysis["body_nonzero"]
    )


SEMANTIC_WITNESSES: dict[str, Callable[[Any], bool]] = {
    "independent_header_positions_refute_same_column": lambda grid: (
        _source_columns(grid) != _target_columns(grid)
        and _same_column_rival(grid) != rule_mirror(grid)
    ),
    "list_order_refutes_sorted_color_rank": lambda grid: (
        _sorted_rank_rival(grid) != rule_mirror(grid)
    ),
    "extra_target_refutes_right_alignment": lambda grid: (
        len(_analysis(grid).get("targets", ())) > len(_analysis(grid).get("sources", ()))
        and _right_aligned_rival(grid) != rule_mirror(grid)
    ),
    "unpaired_source_is_preserved": lambda grid: (
        _has_unpaired_source(grid) and _erase_unmapped_rival(grid) != rule_mirror(grid)
    ),
    "unmapped_body_value_is_preserved": lambda grid: (
        _has_outside_source_control(grid)
        and _erase_unmapped_rival(grid) != rule_mirror(grid)
    ),
    "neutral_body_value_is_preserved": lambda grid: (
        _has_neutral_control(grid)
        and _erase_neutral_rival(grid) != rule_mirror(grid)
    ),
    "header_rows_are_removed": lambda grid: (
        _retain_headers_rival(grid) != rule_mirror(grid)
    ),
}

WITNESS_RIVALS = {
    "independent_header_positions_refute_same_column": ["same_column_pairing"],
    "list_order_refutes_sorted_color_rank": ["sorted_color_rank_pairing"],
    "extra_target_refutes_right_alignment": ["right_align_unequal_lists"],
    "unpaired_source_is_preserved": ["erase_unmapped_body"],
    "unmapped_body_value_is_preserved": ["erase_unmapped_body"],
    "neutral_body_value_is_preserved": [
        "erase_body_colors_absent_from_headers"
    ],
    "header_rows_are_removed": ["retain_header_rows"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require demonstrations to falsify every named shortcut on the query task."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    reasons: list[str] = []
    for index, pair in enumerate([*demos, query]):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"pair {index} must contain input and output")
            continue
        try:
            expected = rule_mirror(pair["input"])
        except Exception as exc:
            reasons.append(f"pair {index} input malformed: {exc}")
            continue
        if expected != pair["output"]:
            reasons.append(f"pair {index} output disagrees with the selected rule")
    if reasons:
        return reasons

    for name, rival in LESSON_COMPETITORS.items():
        survives = all(rival(pair["input"]) == pair["output"] for pair in demos)
        if survives:
            reasons.append(f"demonstrations do not falsify rival: {name}")
    return reasons


def _header_columns(rng, width: int, count: int) -> list[int]:
    return sorted(rng.sample(range(width), count))


def _independent_header_columns(rng, width: int, n: int, target_n: int):
    source_cols = _header_columns(rng, width, n)
    target_cols = _header_columns(rng, width, target_n)
    if n == target_n and source_cols == target_cols and n < width:
        # Force one positional disagreement without changing list order.
        available = [col for col in range(width) if col not in target_cols]
        replacement = rng.choice(available)
        target_cols[-1] = replacement
        target_cols.sort()
    return source_cols, target_cols


def _crossed_colors(rng, n: int, target_n: int) -> tuple[list[int], list[int]]:
    """Choose disjoint lists whose official mapping is not sorted-rank pairing."""
    colors = rng.sample(list(range(1, 10)), n + target_n)
    sources = colors[:n]
    target_pool = colors[n:]
    rng.shuffle(sources)
    targets = list(target_pool)
    for _ in range(24):
        rng.shuffle(targets)
        k = min(n, target_n)
        official = dict(zip(sources[:k], targets[:k]))
        sorted_rival = dict(zip(sorted(sources), sorted(targets)))
        if any(
            source in official and sorted_rival.get(source) != official[source]
            for source in official
        ):
            return sources, targets
    # Deterministic fallback: rotate the targets. k>=2 under the declared axes.
    targets = targets[1:] + targets[:1]
    return sources, targets


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    rng = ctx.draw_rng("layout")
    profile = schedule_profile(seed, sample_index, difficulty)
    n, target_n, body_h, width, n_unmapped = _default_parameters(
        ctx, overrides, profile, difficulty
    )
    height = body_h + 2

    sources, targets = _crossed_colors(rng, n, target_n)
    source_cols, target_cols = _independent_header_columns(
        rng, width, n, target_n
    )

    grid = full_grid(height, width, 0)
    for col, source in zip(source_cols, sources):
        grid[0][col] = source
    for col, target in zip(target_cols, targets):
        grid[1][col] = target

    # Every source appears at least once. This intentionally includes sources
    # past min(N, target_n), making the preserve-unpaired-source branch visible.
    mapped_colors = list(sources)
    body_capacity = body_h * width
    max_extra_mapped = body_capacity - n - n_unmapped
    extra_mapped = rng.randint(n, min(2 * n, max_extra_mapped))
    mapped_colors.extend(rng.choice(sources) for _ in range(extra_mapped))

    # n_unmapped is an exact count of cells outside the entire row-0 source set.
    # The first such cell uses a target color (when present), specifically
    # teaching that appearing in the VALUE row does not make a body cell a key.
    distractor_colors: list[int] = []
    if n_unmapped:
        distractor_colors.append(rng.choice(targets))
    neutral_pool = [
        color for color in range(1, 10)
        if color not in set(sources) and color not in set(targets)
    ]
    if n_unmapped >= 2 and neutral_pool:
        # Guarantee a body value absent from both headers whenever the exact
        # control count has room for it.  This kills a stronger canonical-
        # equivalent shortcut than erase-all-unmapped: keep the union of both
        # legend palettes and erase only truly neutral values.
        distractor_colors.append(rng.choice(neutral_pool))
    while len(distractor_colors) < n_unmapped:
        choices = list(targets) + neutral_pool
        distractor_colors.append(rng.choice(choices))

    body_positions = [
        (row, col)
        for row in range(2, height)
        for col in range(width)
    ]
    rng.shuffle(body_positions)
    colors_to_place = mapped_colors + distractor_colors
    if len(colors_to_place) > len(body_positions):
        raise ValueError(
            f"requested {len(colors_to_place)} body cells but only "
            f"{len(body_positions)} positions fit"
        )
    rng.shuffle(colors_to_place)
    for (row, col), color in zip(body_positions, colors_to_place):
        grid[row][col] = color

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise AssertionError(f"generated grid failed self_check: {errors}")
    return grid
