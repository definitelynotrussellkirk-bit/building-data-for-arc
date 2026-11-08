"""Input sampler for per-band 2x2 D4 transform and color-map inference.

Each two-row band contains A, B, and C blocks.  The selected authority searches
all eight D4 transforms, keeps transforms for which transformed A functionally
maps to B, maximizes exact A/B color matches, and breaks score ties by transform
index.  It then applies that transform and learned color map to C.

This sampler constructs A/B pairs against that *actual* selection procedure.
In particular, it never labels a transform merely because B was produced from
it: every generated band's intended transform is reselected by the authority
mirror, including the four branches absent from the public examples.
"""
from __future__ import annotations

from itertools import product
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "4c26a1072222"
TASK_ID = GENERATOR_ID
RULE_HASH = "a86a18b84011"
VERSION = "2.1.0"
SUMMARY = (
    "Three or four two-row A/B/C bands.  In each band, the authority selects "
    "the highest-exact-score consistent 2x2 D4 transform from A to B, learns "
    "its color map, and applies both independently to C."
)
EXAMPLES_NEEDED = 4

TRANSFORM_NAMES = (
    "identity",
    "flip_lr",
    "flip_ud",
    "rotate_180",
    "rotate_cw",
    "rotate_ccw",
    "transpose",
    "anti_transpose",
)
_TRANSFORM_INDEX = {name: index for index, name in enumerate(TRANSFORM_NAMES)}
_CANONICAL_TRANSFORMS = frozenset({0, 1, 4, 5})

INVARIANTS = [
    "width is 9 and height is 8 or 11 (three or four two-row bands)",
    "bands are separated by all-zero rows and use A/B/C columns 0-1/3-4/7-8",
    "each A/B relation is a functional color map after one authority-selected D4 transform",
    "the complete input uses exactly eight nonzero colors",
]

AXES = {
    "n_bands": {
        "type": "int",
        "default": "alternates by sample index",
        "valid": "3..4",
    },
    "first_transform": {
        "type": "str",
        "default": "cycles through all eight D4 transforms",
        "valid": "|".join(TRANSFORM_NAMES),
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []
SCHEDULE_PROFILES = ("three_bands", "four_bands")


# The authority's source-coordinate table.  `_transform(block, t)[r][c]`
# returns block[src(t,r,c)], matching the selected Racket rule exactly.
def _source_position(transform: int, row: int, col: int) -> tuple[int, int]:
    if transform == 0:
        return row, col
    if transform == 1:
        return row, 1 - col
    if transform == 2:
        return 1 - row, col
    if transform == 3:
        return 1 - row, 1 - col
    if transform == 4:
        return 1 - col, row
    if transform == 5:
        return col, 1 - row
    if transform == 6:
        return col, row
    return 1 - col, 1 - row


def _transform(block: list[list[int]], transform: int) -> list[list[int]]:
    return [
        [
            block[_source_position(transform, row, col)[0]][
                _source_position(transform, row, col)[1]
            ]
            for col in range(2)
        ]
        for row in range(2)
    ]


def _relation_candidates(a_block: list[list[int]], b_block: list[list[int]]):
    candidates = []
    for transform in range(8):
        transformed = _transform(a_block, transform)
        mapping: dict[int, int] = {}
        consistent = True
        for row in range(2):
            for col in range(2):
                source = transformed[row][col]
                target = b_block[row][col]
                previous = mapping.get(source)
                if previous is not None and previous != target:
                    consistent = False
                    break
                mapping[source] = target
            if not consistent:
                break
        if consistent:
            score = sum(
                transformed[row][col] == b_block[row][col]
                for row in range(2)
                for col in range(2)
            )
            candidates.append(
                {
                    "transform": transform,
                    "score": score,
                    "mapping": mapping,
                }
            )
    return candidates


def _select_relation(a_block: list[list[int]], b_block: list[list[int]]):
    candidates = _relation_candidates(a_block, b_block)
    if not candidates:
        raise ValueError("A/B block has no functional D4 transform/color map")
    return min(candidates, key=lambda item: (-item["score"], item["transform"]))


def _restricted_growth_patterns(n_colors: int):
    """Canonical 2x2 equality patterns using exactly n_colors labels."""
    for flat in product(range(n_colors), repeat=4):
        if flat[0] != 0 or set(flat) != set(range(n_colors)):
            continue
        maximum = 0
        valid = True
        for value in flat[1:]:
            if value > maximum + 1:
                valid = False
                break
            maximum = max(maximum, value)
        if valid:
            yield [list(flat[:2]), list(flat[2:])]


def _pattern_bank() -> dict[tuple[int, int, str], tuple[list[list[int]], ...]]:
    """Build tiny, immutable-by-convention templates verified by selection.

    `partial` changes the highest source label to a fresh destination label.
    Three-color templates are additionally required to have a unique maximum
    exact score, so all eight D4 branches are geometrically identifiable rather
    than surviving only through a score tie.
    """
    bank: dict[tuple[int, int, str], tuple[list[list[int]], ...]] = {}
    for n_colors in (2, 3):
        for transform in range(8):
            for mode in ("identity", "partial"):
                accepted = []
                for pattern in _restricted_growth_patterns(n_colors):
                    symbolic_map = {value: value for value in range(n_colors)}
                    if mode == "partial":
                        symbolic_map[n_colors - 1] = n_colors
                    b_block = [
                        [symbolic_map[value] for value in row]
                        for row in _transform(pattern, transform)
                    ]
                    candidates = _relation_candidates(pattern, b_block)
                    selected = min(
                        candidates,
                        key=lambda item: (-item["score"], item["transform"]),
                    )
                    if selected["transform"] != transform:
                        continue
                    if n_colors == 3:
                        maximum = max(item["score"] for item in candidates)
                        if sum(item["score"] == maximum for item in candidates) != 1:
                            continue
                    accepted.append(pattern)
                bank[(n_colors, transform, mode)] = tuple(accepted)
    return bank


_PATTERN_BANK = _pattern_bank()
for _transform_index in range(8):
    if not _PATTERN_BANK[(3, _transform_index, "identity")]:
        raise RuntimeError(f"no constructive identity template for transform {_transform_index}")
    if not _PATTERN_BANK[(3, _transform_index, "partial")]:
        raise RuntimeError(f"no constructive recolor template for transform {_transform_index}")


def _difficulty_offset(difficulty) -> int:
    return {None: 0, "easy": 0, "medium": 1, "hard": 2}.get(difficulty, 0)


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    del seed
    effective_index = sample_index + _difficulty_offset(difficulty)
    return SCHEDULE_PROFILES[effective_index % len(SCHEDULE_PROFILES)]


def _draw_axis(ctx, name: str, scheduled: Any, legal: tuple[Any, ...], overrides: dict):
    # A singleton default makes the curriculum schedule exact.  An explicit
    # override sees the complete legal domain and is still recorded by GenCtx.
    options = legal if overrides.get(name) is not None else (scheduled,)
    return ctx.draw_choice(name, options)


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    n_bands = overrides.get("n_bands")
    if n_bands is not None and (type(n_bands) is not int or n_bands not in (3, 4)):
        raise ValueError("n_bands must be integer 3 or 4")
    first = overrides.get("first_transform")
    if first is not None and (type(first) is not str or first not in TRANSFORM_NAMES):
        raise ValueError(f"first_transform must be one of {TRANSFORM_NAMES}")


def _scheduled_transforms(first: int, n_bands: int, sample_index: int) -> list[int]:
    transforms = [first]
    # Every grid includes one of the transpose branches (6/7), which are absent
    # from the canonical examples and require a three-color source to identify.
    outside = (6, 7) if sample_index % 2 == 0 else (7, 6)
    transforms.append(next(value for value in outside if value not in transforms))
    rotation = sample_index % 6
    remainder = (2, 3, 4, 5, 0, 1)
    ordered = remainder[rotation:] + remainder[:rotation] + tuple(range(8))
    for candidate in ordered:
        if len(transforms) >= n_bands:
            break
        if candidate not in transforms:
            transforms.append(candidate)
    return transforms


def _scheduled_source_color_counts(transforms: list[int]) -> list[int]:
    """Decorrelate source-color count from transpose-family membership.

    The transpose branches require three colors to be authority-selectable.  One
    non-transpose band also uses a verified three-color template, while remaining
    non-transpose bands stay at the canonical two-color scale.
    """
    counts = [3 if transform in (6, 7) else 2 for transform in transforms]
    for band, transform in enumerate(transforms):
        if transform not in (0, 6, 7):
            counts[band] = 3
            return counts
    for band, transform in enumerate(transforms):
        if transform == 0:
            counts[band] = 3
            return counts
    raise RuntimeError("scheduled lesson has no non-transpose band")


def _band_blocks(
    ctx,
    palette: tuple[int, ...],
    band: int,
    transform: int,
    mode: str,
    n_colors: int,
):
    pattern_options = _PATTERN_BANK[(n_colors, transform, mode)]
    pattern = ctx.draw_rng(f"a_pattern_{band}").choice(pattern_options)

    source_colors = [palette[(2 * band + offset) % 8] for offset in range(n_colors)]
    values = {
        symbolic: source_colors[symbolic]
        for symbolic in range(n_colors)
    }
    a_block = [[values[value] for value in row] for row in pattern]

    mapping = {color: color for color in source_colors}
    if mode == "partial":
        destination = palette[(2 * band + 3) % 8]
        if destination in source_colors:
            raise RuntimeError("constructive recolor destination collided with source")
        mapping[source_colors[-1]] = destination
    b_block = [
        [mapping[value] for value in row]
        for row in _transform(a_block, transform)
    ]

    # Canonical C blocks use repeated colors rather than four isolated
    # singletons.  A three-plus-one L pattern keeps component density in the
    # public 18..24-object neighborhood while still moving under the selected
    # non-identity transform.  Band 0 carries palette colors 6/7 so every
    # three-band input still realizes all eight nonzero colors; recolor bands
    # include their changed source color so the map remains semantically active.
    if band == 0:
        primary, secondary = palette[6], palette[7]
    else:
        primary, secondary = source_colors[0], source_colors[-1]
    c_candidates = []
    for singleton in range(4):
        flat = [primary] * 4
        flat[singleton] = secondary
        candidate = [flat[:2], flat[2:]]
        if transform == 0 or _transform(candidate, transform) != candidate:
            c_candidates.append(candidate)
    if not c_candidates:
        raise RuntimeError(f"no asymmetric C pattern for transform {transform}")
    c_block = ctx.draw_rng(f"c_pattern_{band}").choice(c_candidates)

    selected = _select_relation(a_block, b_block)
    if selected["transform"] != transform:
        raise RuntimeError(
            f"constructive template drifted: intended {transform}, selected "
            f"{selected['transform']}"
        )
    return a_block, b_block, c_block


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_overrides(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    effective_index = sample_index + _difficulty_offset(difficulty)
    n_bands = _draw_axis(
        ctx,
        "n_bands",
        3 + (effective_index % 2),
        (3, 4),
        overrides,
    )
    first_name = _draw_axis(
        ctx,
        "first_transform",
        TRANSFORM_NAMES[effective_index % 8],
        TRANSFORM_NAMES,
        overrides,
    )
    transforms = _scheduled_transforms(
        _TRANSFORM_INDEX[first_name], n_bands, effective_index
    )
    source_color_counts = _scheduled_source_color_counts(transforms)
    palette = ctx.draw_distinct_colors("palette", n=8, exclude={0})
    grid = full_grid(3 * n_bands - 1, 9, 0)

    for band, transform in enumerate(transforms):
        decorrelation_band = (
            source_color_counts[band] == 3 and transform not in (6, 7)
        )
        mode = (
            "partial"
            if band % 2 or (decorrelation_band and transform == 0)
            else "identity"
        )
        a_block, b_block, c_block = _band_blocks(
            ctx,
            palette,
            band,
            transform,
            mode,
            source_color_counts[band],
        )
        row0 = 3 * band
        for row in range(2):
            for col in range(2):
                grid[row0 + row][col] = a_block[row][col]
                grid[row0 + row][3 + col] = b_block[row][col]
                grid[row0 + row][7 + col] = c_block[row][col]
    return grid


def _block(grid: Any, row0: int, col0: int) -> list[list[int]]:
    return [
        [grid[row0 + row][col0 + col] for col in range(2)]
        for row in range(2)
    ]


def _analyze(grid: Any) -> tuple[dict[str, Any], list[str]]:
    info: dict[str, Any] = {}
    errors: list[str] = []
    if not isinstance(grid, (list, tuple)) or not grid:
        return info, ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return info, ["expected a nonempty rectangular grid"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return info, ["ragged grid"]
    if any(
        type(value) is not int or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return info, ["cells must be integer ARC colors 0..9"]

    height = len(grid)
    info.update({"height": height, "width": width})
    if width != 9:
        errors.append(f"expected width 9, got {width}")
    if height not in (8, 11):
        errors.append(f"expected canonical height 8 or 11, got {height}")
    if errors:
        return info, errors

    n_bands = (height + 1) // 3
    info["n_bands"] = n_bands
    for separator in range(2, height, 3):
        if any(grid[separator][col] != 0 for col in range(width)):
            errors.append(f"separator row {separator} must be all zero")

    block_columns = {0, 1, 3, 4, 7, 8}
    active_rows = [row for band in range(n_bands) for row in (3 * band, 3 * band + 1)]
    for row in active_rows:
        for col in range(width):
            value = grid[row][col]
            if col in block_columns and value == 0:
                errors.append(f"A/B/C cell ({row},{col}) must be nonzero")
            if col not in block_columns and value != 0:
                errors.append(f"structural cell ({row},{col}) must be zero")

    nonzero = {value for row in grid for value in row if value != 0}
    info["nonzero_palette"] = frozenset(nonzero)
    if len(nonzero) != 8:
        errors.append(f"expected exactly 8 nonzero colors, found {len(nonzero)}")

    bands = []
    for band in range(n_bands):
        row0 = 3 * band
        a_block = _block(grid, row0, 0)
        b_block = _block(grid, row0, 3)
        c_block = _block(grid, row0, 7)
        n_source_colors = len({value for row in a_block for value in row})
        if n_source_colors not in (2, 3):
            errors.append(
                f"band {band} A must use 2 or 3 colors, found {n_source_colors}"
            )
        try:
            relation = _select_relation(a_block, b_block)
        except ValueError as exc:
            errors.append(f"band {band}: {exc}")
            continue
        bands.append(
            {
                "index": band,
                "row0": row0,
                "a": a_block,
                "b": b_block,
                "c": c_block,
                "source_color_count": n_source_colors,
                **relation,
            }
        )
    info["bands"] = tuple(bands)
    if len(bands) != n_bands:
        errors.append("not every band has a selectable relation")
    return info, errors


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    _info, errors = _analyze(grid)
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Validate the complete lawful sampler manifold, including public inputs."""
    return self_check(grid)


def observe_overrides(grid) -> dict[str, Any]:
    info, errors = _analyze(grid)
    if errors:
        raise ValueError("; ".join(errors))
    first = info["bands"][0]["transform"]
    return {
        "n_bands": info["n_bands"],
        "first_transform": TRANSFORM_NAMES[first],
    }


def _render_band(
    output: list[list[int]],
    band: dict[str, Any],
    transform: int,
    mapping: dict[int, int],
) -> None:
    transformed = _transform(band["c"], transform)
    row0 = band["row0"]
    for row in range(2):
        for col in range(2):
            value = transformed[row][col]
            output[row0 + row][col] = mapping.get(value, value)


def rule_mirror(grid) -> list[list[int]]:
    """Pure Python parity mirror; the selected Racket rule remains authority."""
    info, errors = _analyze(grid)
    if errors:
        raise ValueError("; ".join(errors))
    output = full_grid(info["height"], 2, 0)
    for band in info["bands"]:
        _render_band(output, band, band["transform"], band["mapping"])
    return output


def semantic_signature(grid) -> dict[str, Any]:
    info, errors = _analyze(grid)
    if errors:
        raise ValueError("; ".join(errors))
    relations = tuple(
        (
            TRANSFORM_NAMES[band["transform"]],
            tuple(sorted(band["mapping"].items())),
        )
        for band in info["bands"]
    )
    return {
        "n_bands": info["n_bands"],
        "transforms": tuple(
            TRANSFORM_NAMES[band["transform"]] for band in info["bands"]
        ),
        "source_color_counts": tuple(
            band["source_color_count"] for band in info["bands"]
        ),
        "recolored_bands": sum(
            any(source != target for source, target in band["mapping"].items())
            for band in info["bands"]
        ),
        "relations": relations,
        "palette_size": len(info["nonzero_palette"]) + 1,
    }


def _safe_predicate(predicate: Callable[[dict[str, Any]], bool]):
    def wrapped(grid) -> bool:
        info, errors = _analyze(grid)
        return not errors and bool(predicate(info))

    return wrapped


def _rival_canonical_transform_subset(grid):
    """Wrong shortcut: public examples never require transforms 2,3,6,7."""
    info, errors = _analyze(grid)
    if errors:
        raise ValueError("; ".join(errors))
    output = full_grid(info["height"], 2, 0)
    for band in info["bands"]:
        if band["transform"] in _CANONICAL_TRANSFORMS:
            _render_band(output, band, band["transform"], band["mapping"])
        else:
            _render_band(output, band, 0, {})
    return output


def _rival_two_color_sources_only(grid):
    """Wrong shortcut: every public A block happens to use exactly two colors."""
    info, errors = _analyze(grid)
    if errors:
        raise ValueError("; ".join(errors))
    output = full_grid(info["height"], 2, 0)
    for band in info["bands"]:
        if band["source_color_count"] <= 2:
            _render_band(output, band, band["transform"], band["mapping"])
        else:
            _render_band(output, band, 0, {})
    return output


def _rival_source_count_transform_gate(grid):
    """Wrong shortcut: source-color count predicts transpose-family membership."""
    info, errors = _analyze(grid)
    if errors:
        raise ValueError("; ".join(errors))
    output = full_grid(info["height"], 2, 0)
    for band in info["bands"]:
        cue_says_transpose = band["source_color_count"] == 3
        selected_is_transpose = band["transform"] in (6, 7)
        if cue_says_transpose == selected_is_transpose:
            _render_band(output, band, band["transform"], band["mapping"])
        else:
            _render_band(output, band, 0, {})
    return output


def _rival_no_recolor(grid):
    info, errors = _analyze(grid)
    if errors:
        raise ValueError("; ".join(errors))
    output = full_grid(info["height"], 2, 0)
    for band in info["bands"]:
        _render_band(output, band, band["transform"], {})
    return output


def _rival_one_global_relation(grid):
    info, errors = _analyze(grid)
    if errors:
        raise ValueError("; ".join(errors))
    output = full_grid(info["height"], 2, 0)
    first = info["bands"][0]
    for band in info["bands"]:
        _render_band(output, band, first["transform"], first["mapping"])
    return output


SEMANTIC_RIVALS = {
    "canonical_transform_subset": _rival_canonical_transform_subset,
    "two_color_sources_only": _rival_two_color_sources_only,
    "source_count_transform_gate": _rival_source_count_transform_gate,
    "transform_without_recolor": _rival_no_recolor,
    "one_global_relation": _rival_one_global_relation,
}
CANONICAL_SHORTCUTS = {
    "canonical_transform_subset": _rival_canonical_transform_subset,
    "two_color_sources_only": _rival_two_color_sources_only,
    "source_count_transform_gate": _rival_source_count_transform_gate,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)

SEMANTIC_WITNESSES = {
    "noncanonical_transform": _safe_predicate(
        lambda info: any(
            band["transform"] not in _CANONICAL_TRANSFORMS
            for band in info["bands"]
        )
    ),
    "three_color_source": _safe_predicate(
        lambda info: any(
            band["source_color_count"] == 3 for band in info["bands"]
        )
    ),
    "source_count_decorrelation": _safe_predicate(
        lambda info: any(
            band["source_color_count"] == 3 and band["transform"] not in (6, 7)
            for band in info["bands"]
        )
    ),
    "active_recolor": _safe_predicate(
        lambda info: any(
            any(source != target for source, target in band["mapping"].items())
            and any(
                value in {
                    source
                    for source, target in band["mapping"].items()
                    if source != target
                }
                for row in band["c"]
                for value in row
            )
            for band in info["bands"]
        )
    ),
    "different_band_relations": _safe_predicate(
        lambda info: len(
            {
                (
                    band["transform"],
                    tuple(sorted(band["mapping"].items())),
                )
                for band in info["bands"]
            }
        )
        > 1
    ),
}
WITNESS_RIVALS = {
    "noncanonical_transform": ["canonical_transform_subset"],
    "three_color_source": ["two_color_sources_only"],
    "source_count_decorrelation": ["source_count_transform_gate"],
    "active_recolor": ["transform_without_recolor"],
    "different_band_relations": ["one_global_relation"],
}


def _pair_errors(pair: Any, label: str) -> list[str]:
    if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
        return [f"{label} must contain input and output grids"]
    errors = self_check(pair["input"])
    if errors:
        return [f"{label} input: {reason}" for reason in errors]
    try:
        expected = rule_mirror(pair["input"])
    except ValueError as exc:
        return [f"{label} mirror failed: {exc}"]
    if pair["output"] != expected:
        return [f"{label} output does not match the D4/color-map rule"]
    return []


def lesson_identifiable(demos, query) -> list[str]:
    """Require enough valid demonstrations to eliminate all named rivals."""
    if not isinstance(demos, (list, tuple)):
        return ["demonstrations must be a list"]
    reasons: list[str] = []
    if len(demos) < EXAMPLES_NEEDED:
        reasons.append(
            f"need at least {EXAMPLES_NEEDED} demonstrations, got {len(demos)}"
        )
    for index, pair in enumerate(demos):
        reasons.extend(_pair_errors(pair, f"demo {index}"))
    reasons.extend(_pair_errors(query, "query"))
    if reasons:
        return reasons

    for witness_name, predicate in SEMANTIC_WITNESSES.items():
        if not any(predicate(pair["input"]) for pair in demos):
            reasons.append(f"semantic witness {witness_name!r} is absent")
    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(pair["input"]) == pair["output"] for pair in demos):
            reasons.append(f"named competitor {name!r} survives every demonstration")
    return reasons
