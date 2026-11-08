"""Generator for ``e1e7c467196f`` — a two-row color-substitution legend.

The non-zero prefix of row 0 contains source colors and the aligned prefix of
row 1 contains their target colors.  Rows 2 onward are the body.  The output
clears both legend rows, replaces each body source color with its aligned
target, and leaves every unmapped body color unchanged.

The canonical test contains a target-color body distractor that must remain
unchanged. Ordinary lessons therefore schedule both value-colored and neutral
unmapped distractors. Pairing profiles also cover aligned, arbitrary, and
noncyclic source→target bijections while preserving the public shape envelope.
"""
from __future__ import annotations

from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "e1e7c467196f"
TASK_ID = GENERATOR_ID
VERSION = "2.1.0"
RULE_HASH = "b5790be780c4"

SUMMARY = (
    "Rows 0-1 hold a contiguous top-left source→target color legend with "
    "2..4 distinct, disjoint pairs spanning aligned, crossed, and noncyclic "
    "rank pairings. Rows 2 onward contain 4..10 source-color "
    "cells (every source appears) and 0..4 unmapped value/neutral distractor "
    "cells. Output clears the legend, applies the aligned substitutions, and "
    "preserves unmapped body colors in place."
)

INVARIANTS = [
    "background is 0 and all grids are rectangular ARC grids",
    "the first K columns of rows 0 and 1 are non-zero aligned legend pairs; every later legend cell is 0",
    "K is 2..4; source colors are distinct; target colors are distinct; source and target sets are disjoint",
    "the body contains 4..10 mapped source cells and every source color occurs at least once",
    "the body contains 0..4 unmapped cells, which may use target colors or a neutral color and remain unchanged",
    "the official output has the same dimensions, clears rows 0-1, recolors only source colors, and preserves positions",
]

# Every three consecutive default draws contain at least one ``both_controls``
# scene and at least one crossed pairing, so each sliding three-demo lesson
# witnesses both unchanged-body branches and refutes sorted-color pairing.
# The K=2 aligned and K=3 reverse anchors reproduce canonical pairing regimes;
# the uniform profile fills in the remaining legal bijections.
SCHEDULE_PROFILES = (
    "canonical_k2",
    "both_controls_a",
    "both_controls_b",
    "canonical_k3_value",
)
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

AXES = {
    "grid_h": {"type": "int", "default": "scheduled anchor or band rng", "valid": "5..14"},
    "grid_w": {"type": "int", "default": "scheduled anchor or band rng", "valid": "5..14"},
    "K": {"type": "int", "default": "scheduled anchor or band rng", "valid": "2..4"},
    "n_markers": {"type": "int", "default": "scheduled anchor or band rng", "valid": "4..10"},
    "n_unmapped": {"type": "int", "default": "scheduled anchor or band rng", "valid": "0..4"},
}

# All declared axis combinations are intentionally supported.  Declaring the
# empty strict list makes an unexpected multi-axis ValueError a real failure
# rather than a legacy warning in the override checker.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, Any], ...] = ()
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()


def _band(difficulty: Any) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return str(difficulty)
    raise ValueError(
        "difficulty must be None, 'easy', 'medium', or 'hard'"
    )


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Return the deterministic four-slot curriculum profile."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> None:
    _band(difficulty)
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    for name in AXES:
        value = overrides.get(name)
        if value is not None and (isinstance(value, bool) or type(value) is not int):
            raise ValueError(f"{name} must be an integer")


def _banded_int(ctx, overrides, label, lo, hi, valid_lo, valid_hi) -> int:
    """Use band-shaped defaults but honor the full declared override range."""
    if overrides.get(label) is not None:
        return ctx.draw_int(label, valid_lo, valid_hi)
    return ctx.draw_int(label, lo, hi)


def _coerce_grid(grid: Any) -> tuple[list[list[int]] | None, list[str]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return None, ["grid must be a non-empty sequence of rows"]
    first = grid[0]
    if not isinstance(first, (list, tuple, str)) or len(first) == 0:
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


def _legend(grid: list[list[int]]) -> tuple[list[int], list[int], list[str]]:
    """Parse the contiguous aligned legend prefix."""
    if len(grid) < 2:
        return [], [], ["grid needs two legend rows"]
    width = len(grid[0])
    k = 0
    while k < width and grid[0][k] != 0 and grid[1][k] != 0:
        k += 1
    errors: list[str] = []
    for col in range(k, width):
        if grid[0][col] != 0 or grid[1][col] != 0:
            errors.append(
                "legend must be one contiguous aligned non-zero prefix in rows 0-1"
            )
            break
    return list(grid[0][:k]), list(grid[1][:k]), errors


def _analysis(grid: Any) -> dict[str, Any]:
    g, errors = _coerce_grid(grid)
    if errors:
        return {"errors": errors}
    assert g is not None
    height, width = len(g), len(g[0])
    keys, values, legend_errors = _legend(g)
    errors.extend(legend_errors)
    key_set = set(keys)
    body = [value for row in g[2:] for value in row if value != 0]
    mapped = [value for value in body if value in key_set]
    unmapped = [value for value in body if value not in key_set]
    counts = {key: mapped.count(key) for key in keys}
    return {
        "errors": errors,
        "grid": g,
        "height": height,
        "width": width,
        "keys": keys,
        "values": values,
        "mapping": dict(zip(keys, values)),
        "mapped": mapped,
        "unmapped": unmapped,
        "counts": counts,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the task-local input grammar and reject structural impostors."""
    del difficulty, meta
    analysis = _analysis(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors
    height = analysis["height"]
    width = analysis["width"]
    keys = analysis["keys"]
    values = analysis["values"]
    mapped = analysis["mapped"]
    unmapped = analysis["unmapped"]
    counts = analysis["counts"]

    if not 5 <= height <= 14:
        errors.append(f"height {height} outside declared range 5..14")
    if not 5 <= width <= 14:
        errors.append(f"width {width} outside declared range 5..14")
    if not 2 <= len(keys) <= 4:
        errors.append(f"legend has {len(keys)} pairs; expected 2..4")
    if len(set(keys)) != len(keys):
        errors.append("legend source colors must be distinct")
    if len(set(values)) != len(values):
        errors.append("legend target colors must be distinct")
    if set(keys) & set(values):
        errors.append("legend source and target color sets must be disjoint")
    if not 4 <= len(mapped) <= 10:
        errors.append(
            f"body has {len(mapped)} mapped source cells; expected 4..10"
        )
    if not 0 <= len(unmapped) <= 4:
        errors.append(
            f"body has {len(unmapped)} unmapped cells; expected 0..4"
        )
    missing = [key for key in keys if counts.get(key, 0) == 0]
    if missing:
        errors.append(f"body omits legend source color(s): {missing}")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """The generated grammar is the canonical cell-wise legend manifold."""
    return self_check(grid)


def observe_overrides(grid) -> dict[str, int]:
    """Recover every exact declared axis from the returned grid."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError(f"cannot observe malformed grid: {analysis['errors']}")
    return {
        "grid_h": analysis["height"],
        "grid_w": analysis["width"],
        "K": len(analysis["keys"]),
        "n_markers": len(analysis["mapped"]),
        "n_unmapped": len(analysis["unmapped"]),
    }


def rule_mirror(grid) -> list[list[int]]:
    """Python spelling of the selected Racket rule for semantic witnesses."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError(f"malformed legend grid: {analysis['errors']}")
    g = analysis["grid"]
    mapping = analysis["mapping"]
    return [
        [
            0 if row < 2 else mapping.get(g[row][col], g[row][col])
            for col in range(analysis["width"])
        ]
        for row in range(analysis["height"])
    ]


def _sorted_pairing_rival(grid) -> list[list[int]]:
    """Wrong shortcut: sort both legend rows before pairing their colors."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        return [list(row) for row in grid]
    mapping = dict(zip(sorted(analysis["keys"]), sorted(analysis["values"])))
    g = analysis["grid"]
    return [
        [0 if row < 2 else mapping.get(g[row][col], g[row][col])
         for col in range(analysis["width"])]
        for row in range(analysis["height"])
    ]


def _reverse_value_rival(grid) -> list[list[int]]:
    """Wrong shortcut: apply the legend as a bidirectional substitution."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        return [list(row) for row in grid]
    mapping = dict(analysis["mapping"])
    mapping.update(dict(zip(analysis["values"], analysis["keys"])))
    g = analysis["grid"]
    return [
        [0 if row < 2 else mapping.get(g[row][col], g[row][col])
         for col in range(analysis["width"])]
        for row in range(analysis["height"])
    ]


def _erase_unmapped_rival(grid) -> list[list[int]]:
    """Wrong shortcut: erase every body color that is not a legend source."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        return [list(row) for row in grid]
    mapping = analysis["mapping"]
    g = analysis["grid"]
    return [
        [
            0 if row < 2 or g[row][col] not in mapping
            else mapping[g[row][col]]
            for col in range(analysis["width"])
        ]
        for row in range(analysis["height"])
    ]


def _first_pair_only_rival(grid) -> list[list[int]]:
    """Wrong shortcut: apply only the first visible legend pair."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        return [list(row) for row in grid]
    mapping = {analysis["keys"][0]: analysis["values"][0]}
    g = analysis["grid"]
    return [
        [0 if row < 2 else mapping.get(g[row][col], g[row][col])
         for col in range(analysis["width"])]
        for row in range(analysis["height"])]


def _keep_legend_rival(grid) -> list[list[int]]:
    """Wrong shortcut: recolor the body but retain the two legend rows."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        return [list(row) for row in grid]
    out = rule_mirror(grid)
    out[0] = list(analysis["grid"][0])
    out[1] = list(analysis["grid"][1])
    return out


def _nonzero_cyclic_rank_rival(grid) -> list[list[int]]:
    """Wrong shortcut: infer a nonzero cyclic rank shift from one legend pair."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        return [list(row) for row in grid]
    sorted_keys = sorted(analysis["keys"])
    sorted_values = sorted(analysis["values"])
    key_rank = {value: index for index, value in enumerate(sorted_keys)}
    value_rank = {value: index for index, value in enumerate(sorted_values)}
    first_key = analysis["keys"][0]
    first_value = analysis["values"][0]
    shift = (value_rank[first_value] - key_rank[first_key]) % len(sorted_keys)
    if shift == 0:
        shift = 1
    mapping = {
        key: sorted_values[(index + shift) % len(sorted_values)]
        for index, key in enumerate(sorted_keys)
    }
    g = analysis["grid"]
    return [
        [
            0 if row < 2 else mapping.get(g[row][col], g[row][col])
            for col in range(analysis["width"])
        ]
        for row in range(analysis["height"])
    ]


SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "pair_sorted_colors": _sorted_pairing_rival,
    "substitute_both_directions": _reverse_value_rival,
    "erase_unmapped_body_colors": _erase_unmapped_rival,
    "apply_first_legend_pair_only": _first_pair_only_rival,
    "retain_legend_rows": _keep_legend_rival,
    "infer_nonzero_cyclic_rank_pairing": _nonzero_cyclic_rank_rival,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def _crossed_pairing(grid) -> bool:
    analysis = _analysis(grid)
    return (
        not analysis["errors"]
        and _sorted_pairing_rival(grid) != rule_mirror(grid)
    )


def _has_value_distractor(grid) -> bool:
    analysis = _analysis(grid)
    return (
        not analysis["errors"]
        and any(value in set(analysis["values"]) for value in analysis["unmapped"])
    )


def _has_neutral_distractor(grid) -> bool:
    analysis = _analysis(grid)
    if analysis["errors"]:
        return False
    legend_colors = set(analysis["keys"]) | set(analysis["values"])
    return any(value not in legend_colors for value in analysis["unmapped"])


def _pairing_signature(grid) -> tuple[int, ...] | None:
    """Return target ranks indexed by sorted source-color rank."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        return None
    sorted_values = sorted(analysis["values"])
    value_rank = {value: index for index, value in enumerate(sorted_values)}
    return tuple(
        value_rank[analysis["mapping"][key]]
        for key in sorted(analysis["keys"])
    )


def _has_rank_aligned_pairing(grid) -> bool:
    signature = _pairing_signature(grid)
    return signature is not None and signature == tuple(range(len(signature)))


def _has_noncyclic_pairing(grid) -> bool:
    signature = _pairing_signature(grid)
    if signature is None:
        return False
    k = len(signature)
    cyclic = {
        tuple((index + shift) % k for index in range(k))
        for shift in range(k)
    }
    return signature not in cyclic


SEMANTIC_WITNESSES: dict[str, Callable[[Any], bool]] = {
    "column_alignment_beats_sorted_pairing": _crossed_pairing,
    "value_colored_body_cell_stays_unchanged": _has_value_distractor,
    "neutral_body_color_stays_unchanged": _has_neutral_distractor,
    "rank_aligned_pairing_is_supported": _has_rank_aligned_pairing,
    "noncyclic_pairing_is_supported": _has_noncyclic_pairing,
    "all_legend_sources_are_exercised": lambda grid: (
        not _analysis(grid)["errors"]
        and all(_analysis(grid)["counts"].values())
    ),
    "legend_rows_are_cleared": lambda grid: any(
        value != 0 for row in list(grid)[:2] for value in row
    ),
}
WITNESS_RIVALS = {
    "column_alignment_beats_sorted_pairing": ["pair_sorted_colors"],
    "value_colored_body_cell_stays_unchanged": [
        "substitute_both_directions",
        "erase_unmapped_body_colors",
    ],
    "neutral_body_color_stays_unchanged": ["erase_unmapped_body_colors"],
    "rank_aligned_pairing_is_supported": [
        "infer_nonzero_cyclic_rank_pairing"
    ],
    "noncyclic_pairing_is_supported": [
        "infer_nonzero_cyclic_rank_pairing"
    ],
    "all_legend_sources_are_exercised": ["apply_first_legend_pair_only"],
    "legend_rows_are_cleared": ["retain_legend_rows"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons that leave a named shortcut compatible with the demos."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    reasons: list[str] = []
    pairs = [*demos, query]
    for index, pair in enumerate(pairs):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"pair {index} must contain input and output")
            continue
        try:
            expected = rule_mirror(pair["input"])
        except Exception as exc:  # surfaced as a counted semantic-gate error
            reasons.append(f"pair {index} input is malformed: {exc}")
            continue
        if expected != pair["output"]:
            reasons.append(f"pair {index} output disagrees with the legend rule")
    if reasons:
        return reasons

    if not any(_crossed_pairing(pair["input"]) for pair in demos):
        reasons.append("demonstrations never refute sorted-color pairing")
    if not any(_has_value_distractor(pair["input"]) for pair in demos):
        reasons.append("demonstrations omit the unchanged target-color branch")
    if not any(_has_neutral_distractor(pair["input"]) for pair in demos):
        reasons.append("demonstrations omit the unchanged neutral-color branch")

    for name, rival in LESSON_COMPETITORS.items():
        survives = all(
            rival(pair["input"]) == pair["output"] for pair in demos
        )
        if survives and rival(query["input"]) != query["output"]:
            reasons.append(f"demonstrations do not falsify rival: {name}")
    return reasons


PAIRING_MODE_BY_PROFILE = {
    "canonical_k2": "aligned",
    "both_controls_a": "crossed",
    "both_controls_b": "uniform",
    "canonical_k3_value": "reverse",
}


def _palette(
    rng, k: int, *, pairing_mode: str = "uniform"
) -> tuple[list[int], list[int], int]:
    """Choose disjoint colors and a rank-pairing permutation."""
    selected = rng.sample(list(range(1, 10)), 2 * k)
    sorted_keys = sorted(selected[:k])
    sorted_values = sorted(selected[k:])
    identity = list(range(k))
    ranks = list(identity)
    if pairing_mode == "aligned":
        pass
    elif pairing_mode == "reverse":
        ranks.reverse()
    elif pairing_mode == "uniform":
        rng.shuffle(ranks)
    elif pairing_mode == "crossed":
        while ranks == identity:
            rng.shuffle(ranks)
    else:
        raise ValueError(f"unknown pairing mode: {pairing_mode}")

    official = {
        key: sorted_values[ranks[index]]
        for index, key in enumerate(sorted_keys)
    }
    keys = list(sorted_keys)
    rng.shuffle(keys)
    values = [official[key] for key in keys]
    neutral = next(
        color for color in range(1, 10)
        if color not in set(keys) | set(values)
    )
    return keys, values, neutral


def _default_parameters(ctx, overrides, profile: str, difficulty: Any):
    if profile == "canonical_k2":
        return (
            ctx.draw_int("grid_h", 6, 6),
            ctx.draw_int("grid_w", 6, 6),
            ctx.draw_int("K", 2, 2),
            ctx.draw_int("n_markers", 5, 5),
            ctx.draw_int("n_unmapped", 0, 0),
        )
    if profile == "canonical_k3_value":
        return (
            ctx.draw_int("grid_h", 6, 6),
            ctx.draw_int("grid_w", 8, 8),
            ctx.draw_int("K", 3, 3),
            ctx.draw_int("n_markers", 8, 8),
            ctx.draw_int("n_unmapped", 1, 1),
        )

    band = _band(difficulty)
    if band == "easy":
        ranges = ((5, 7), (5, 8), (2, 3), (4, 6), (2, 2))
    elif band == "hard":
        ranges = ((10, 14), (10, 14), (3, 4), (8, 10), (3, 4))
    else:
        ranges = ((7, 10), (7, 11), (2, 4), (6, 8), (2, 3))
    return tuple(
        _banded_int(ctx, overrides, label, lo, hi, valid_lo, valid_hi)
        for (label, (lo, hi), valid_lo, valid_hi) in zip(
            ("grid_h", "grid_w", "K", "n_markers", "n_unmapped"),
            ranges,
            (5, 5, 2, 4, 0),
            (14, 14, 4, 10, 4),
        )
    )


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
    default_draw = not any(value is not None for value in overrides.values())

    if default_draw:
        h, w, k, n_markers, n_unmapped = _default_parameters(
            ctx, overrides, profile, difficulty
        )
    else:
        band = _band(difficulty)
        if band == "easy":
            ranges = ((5, 7), (5, 8), (2, 3), (4, 6), (0, 2))
        elif band == "hard":
            ranges = ((10, 14), (10, 14), (3, 4), (8, 10), (0, 4))
        else:
            ranges = ((7, 10), (7, 11), (2, 4), (6, 8), (0, 3))
        h, w, k, n_markers, n_unmapped = tuple(
            _banded_int(ctx, overrides, label, lo, hi, valid_lo, valid_hi)
            for (label, (lo, hi), valid_lo, valid_hi) in zip(
                ("grid_h", "grid_w", "K", "n_markers", "n_unmapped"),
                ranges,
                (5, 5, 2, 4, 0),
                (14, 14, 4, 10, 4),
            )
        )

    pairing_mode = (
        PAIRING_MODE_BY_PROFILE[profile] if default_draw else "uniform"
    )
    keys, values, neutral = _palette(rng, k, pairing_mode=pairing_mode)
    grid = full_grid(h, w, 0)
    for col, (source, target) in enumerate(zip(keys, values)):
        grid[0][col] = source
        grid[1][col] = target

    marker_colors = list(keys)
    marker_colors.extend(rng.choice(keys) for _ in range(n_markers - k))
    rng.shuffle(marker_colors)

    if profile in ("both_controls_a", "both_controls_b") and default_draw:
        unmapped_colors = [rng.choice(values), neutral]
        unmapped_colors.extend(
            rng.choice([*values, neutral])
            for _ in range(n_unmapped - 2)
        )
    elif profile == "canonical_k3_value" and default_draw:
        unmapped_colors = [rng.choice(values)]
    else:
        unmapped_colors = []
        if n_unmapped:
            unmapped_colors.append(rng.choice(values))
        if n_unmapped >= 2:
            unmapped_colors.append(neutral)
        unmapped_colors.extend(
            rng.choice([*values, neutral])
            for _ in range(n_unmapped - len(unmapped_colors))
        )
    rng.shuffle(unmapped_colors)

    body_positions = [(row, col) for row in range(2, h) for col in range(w)]
    rng.shuffle(body_positions)
    colors = [*marker_colors, *unmapped_colors]
    if len(colors) > len(body_positions):
        raise ValueError(
            f"requested {len(colors)} body cells but only {len(body_positions)} fit"
        )
    for (row, col), color in zip(body_positions, colors):
        grid[row][col] = color

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise AssertionError(f"generated grid failed self_check: {errors}")
    return grid
