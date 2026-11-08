"""Generator for ``3a0af56db83e`` — priority overlay of four 3-row masks.

The input is four 3-row monochrome masks stacked vertically.  At each projected
3xW coordinate, the output keeps the first nonzero cell in priority order
band 0 > band 1 > band 3 > band 2.  Generated scenes deliberately include
exclusive witnesses for every pairwise priority comparison, projected overlap
arities 0 through 4, a winning cell for each band, and mixed occupancy outside
the witnesses so the full rule is visible without a one-arity profile artifact.
"""
from __future__ import annotations

from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "3a0af56db83e"
TASK_ID = GENERATOR_ID
VERSION = "3.1.1"
# Re-pinned when the comment-preserving selected Racket authority is synchronized.
# The packet's current canonical source is 6ce410c8e50d; the task-scoped source
# synchronization patch updates canonical + selected target atomically.
RULE_HASH = "d5832237956b"
EXAMPLES_NEEDED = 2
MIN_STRICT_FRAC = 0.20

PRIORITY = (0, 1, 3, 2)
CANONICAL_BAND_COLORS = (5, 4, 2, 8)  # indexed by physical band 0,1,2,3
MASK_PROFILES = ("sparse", "canonical", "dense")
PALETTE_MODES = ("canonical", "varied")

SUMMARY = (
    "A 12xW zero-background input is four stacked 3-row monochrome masks. "
    "Project the four bands onto one 3xW frame and choose the first nonzero "
    "cell in priority order band 0, then band 1, then band 3, then band 2; "
    "emit 0 only when all four projected cells are 0. Band colors are distinct "
    "within a scene and may be reassigned across bands, so color identity is "
    "not a substitute for band priority."
)

INVARIANTS = [
    "input height is exactly 12, interpreted as four stacked 3-row bands",
    "each band is a nonempty monochrome mask on background 0",
    "the four nonzero band colors are distinct within a scene",
    "output is 3xW and uses priority band 0 > band 1 > band 3 > band 2",
    "ordinary generated draws expose every pairwise priority comparison",
    "ordinary generated draws contain projected overlap arities 0, 1, 2, 3, and 4",
    "free projected cells mix neighboring arities while preserving each profile's exact mean density",
    "every generated palette refutes choosing the numerically largest visible color",
    "ordinary generated draws let each band win somewhere and preserve at least one all-zero projected cell",
]

COUNTER_HYPOTHESES = [
    "copy only the first/top band",
    "use natural physical order 0 > 1 > 2 > 3",
    "reverse the band priority",
    "choose by the canonical colors 5 > 4 > 8 > 2 regardless of band position",
    "choose the numerically largest visible color",
    "fill all-zero projected cells with a fallback band color",
    "apply the intended priority except reverse it on three-way overlaps",
    "apply the intended priority except reverse it on four-way overlaps",
    "memorize fixed witness positions or one fixed width",
]

AXES = {
    "grid_w": {
        "type": "int",
        "default": "scheduled canonical anchor or difficulty-scaled width",
        "valid": "4..12",
    },
    "mask_profile": {
        "type": "enum",
        "default": "scheduled sparse|canonical|dense",
        "valid": MASK_PROFILES,
    },
    "palette_mode": {
        "type": "enum",
        "default": "scheduled canonical|varied band-color assignment",
        "valid": PALETTE_MODES,
    },
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []
_ALLOWED_OVERRIDES = frozenset(AXES)

SCHEDULE_PROFILES = (
    "canonical_anchor",
    "priority_varied",
    "sparse_varied",
    "dense_varied",
)

# Canonical per-band foreground-count extrema over all six train + one test input.
_CANONICAL_COUNT_RANGES = ((6, 13), (4, 11), (7, 15), (5, 12))

# Ten distinct projected coordinates are reserved in every generated draw.
# Six expose each unordered pair of bands, one exposes three-way priority, one
# exposes four-way priority, one lets the lowest-priority band win alone, and
# one is left empty.  Thus every scene covers projected arities 0..4.
_PAIR_ROLES = ((0, 1), (0, 3), (0, 2), (1, 3), (1, 2), (3, 2))
_TRIPLE_ROLES = ((1, 3, 2),)
_QUAD_ROLES = ((0, 1, 2, 3),)
_SINGLE_ROLES = ((2,),)
_RESERVED_ROLES = _PAIR_ROLES + _TRIPLE_ROLES + _QUAD_ROLES + _SINGLE_ROLES
_RESERVED_NONZERO_COUNT = sum(len(role) for role in _RESERVED_ROLES)  # 20
_RESERVED_COORD_COUNT = len(_RESERVED_ROLES) + 1  # 10


def _band(difficulty: Any) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return str(difficulty)
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - _ALLOWED_OVERRIDES)
    if unknown:
        raise TypeError(f"unknown override axis: {unknown[0]}")

    width = overrides.get("grid_w")
    if width is not None:
        if isinstance(width, bool) or not isinstance(width, int):
            raise TypeError("override 'grid_w' must be an integer")
        if not 4 <= width <= 12:
            raise ValueError(f"override 'grid_w'={width} outside [4, 12]")

    for name, options in {
        "mask_profile": MASK_PROFILES,
        "palette_mode": PALETTE_MODES,
    }.items():
        value = overrides.get(name)
        if value is not None and value not in options:
            raise ValueError(f"override {name!r}={value!r} not in {options}")


def _validate_call_arguments(seed: int, sample_index: int) -> None:
    """Reject scalar lookalikes before indexing or constructing RNG state."""
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    if type(sample_index) is not int:
        raise TypeError("sample_index must be an integer (not bool)")
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Cycle a four-slot curriculum; every two-slot window includes a varied palette."""
    _validate_call_arguments(seed, sample_index)
    del seed, difficulty
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def _scheduled_defaults(sample_index: int, band: str) -> dict[str, Any]:
    profile = schedule_profile(0, sample_index, band)
    widths = {
        "easy": {
            "canonical_anchor": 6,
            "priority_varied": 4,
            "sparse_varied": 5,
            "dense_varied": 7,
        },
        "medium": {
            "canonical_anchor": 6,
            "priority_varied": 8,
            "sparse_varied": 7,
            "dense_varied": 10,
        },
        "hard": {
            "canonical_anchor": 6,
            "priority_varied": 12,
            "sparse_varied": 10,
            "dense_varied": 12,
        },
    }
    return {
        "grid_w": widths[band][profile],
        "mask_profile": {
            "canonical_anchor": "canonical",
            "priority_varied": "canonical",
            "sparse_varied": "sparse",
            "dense_varied": "dense",
        }[profile],
        "palette_mode": "canonical" if profile == "canonical_anchor" else "varied",
    }


def _draw_int_axis(ctx, overrides, label: str, default: int, lo: int, hi: int) -> int:
    if label in overrides and overrides[label] is not None:
        return ctx.draw_int(label, lo, hi)
    return ctx.draw_int(label, default, default)


def _draw_choice_axis(ctx, overrides, label: str, default: str, options) -> str:
    if label in overrides and overrides[label] is not None:
        return ctx.draw_choice(label, options)
    return ctx.draw_choice(label, (default,))


def _palette(ctx, mode: str) -> tuple[int, int, int, int]:
    if mode == "canonical":
        return CANONICAL_BAND_COLORS
    rng = ctx.draw_rng("palette")
    colors = list(CANONICAL_BAND_COLORS)
    # Pick one of the 23 non-identity permutations.  Keeping the canonical set
    # while changing its band assignment gives a direct counterexample to the
    # canonical color-priority shortcut without introducing a new color cue.
    # Reject the one assignment (8,5,2,4) whose numeric descending order agrees
    # with physical priority, so every scene also refutes max-color overlay.
    while True:
        rng.shuffle(colors)
        candidate = tuple(colors)
        priority_colors = tuple(candidate[band] for band in PRIORITY)
        max_aligned = priority_colors == tuple(sorted(priority_colors, reverse=True))
        if candidate != CANONICAL_BAND_COLORS and not max_aligned:
            return candidate


def _profile_free_arity(profile: str) -> int:
    return {"sparse": 1, "canonical": 2, "dense": 3}[profile]


def _mixed_free_arities(profile: str, count: int, rng) -> list[int]:
    """Mix adjacent arities while preserving the profile's exact mean density."""
    target = _profile_free_arity(profile)
    arities = [target] * count
    for index in range(0, count - 1, 2):
        arities[index] = target - 1
        arities[index + 1] = target + 1
    rng.shuffle(arities)
    return arities


def _bands_for_arity(arity: int, index: int, offset: int) -> tuple[int, ...]:
    if arity == 0:
        return ()
    if arity == 1:
        return ((index + offset) % 4,)
    if arity == 2:
        return _PAIR_ROLES[(index + offset) % len(_PAIR_ROLES)]
    if arity == 3:
        omitted = (index + offset) % 4
        return tuple(band for band in range(4) if band != omitted)
    if arity == 4:
        return (0, 1, 2, 3)
    raise ValueError(f"projected arity must be 0..4, got {arity}")


def _mask_profile_from_count(width: int, total_nonzero: int) -> str | None:
    free = 3 * width - _RESERVED_COORD_COUNT
    expected = {
        profile: _RESERVED_NONZERO_COUNT + _profile_free_arity(profile) * free
        for profile in MASK_PROFILES
    }
    matches = [profile for profile, count in expected.items() if count == total_nonzero]
    return matches[0] if len(matches) == 1 else None


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call_arguments(seed, sample_index)
    _validate_overrides(overrides)
    band = _band(difficulty)
    defaults = _scheduled_defaults(sample_index, band)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    width = _draw_int_axis(ctx, overrides, "grid_w", defaults["grid_w"], 4, 12)
    mask_profile = _draw_choice_axis(
        ctx, overrides, "mask_profile", defaults["mask_profile"], MASK_PROFILES
    )
    palette_mode = _draw_choice_axis(
        ctx, overrides, "palette_mode", defaults["palette_mode"], PALETTE_MODES
    )

    coords = [(row, col) for row in range(3) for col in range(width)]
    rng = ctx.draw_rng("mask-layout")
    rng.shuffle(coords)
    reserved = coords[:_RESERVED_COORD_COUNT]
    free_coords = coords[_RESERVED_COORD_COUNT:]

    active: dict[tuple[int, int], tuple[int, ...]] = {}
    cursor = 0
    for role in _RESERVED_ROLES:
        active[reserved[cursor]] = role
        cursor += 1
    active[reserved[cursor]] = ()  # explicit all-zero projected witness

    free_arities = _mixed_free_arities(mask_profile, len(free_coords), rng)
    offset = rng.randrange(12)
    for index, (coord, arity) in enumerate(zip(free_coords, free_arities)):
        active[coord] = _bands_for_arity(arity, index, offset)

    colors = _palette(ctx, palette_mode)
    grid = full_grid(12, width, 0)
    for (row, col), bands in active.items():
        for physical_band in bands:
            grid[physical_band * 3 + row][col] = colors[physical_band]

    errors = self_check(
        grid,
        difficulty=band,
        meta={
            "grid_w": width,
            "mask_profile": mask_profile,
            "palette_mode": palette_mode,
        },
    )
    if errors:
        raise RuntimeError("constructed invalid four-band scene: " + "; ".join(errors))

    observed = observe_overrides(grid)
    expected = {name: ctx.axis_value(name) for name in AXES}
    if observed != expected:
        raise RuntimeError(
            f"returned grid lost keyed axis values: expected {expected}, observed {observed}"
        )
    return grid


def _coerce_grid(grid: Any) -> tuple[list[list[int]] | None, list[str]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return None, ["grid must be a nonempty sequence of rows"]
    rows: list[list[int]] = []
    width: int | None = None
    for row_index, row in enumerate(grid):
        if isinstance(row, str):
            try:
                values = [int(char) for char in row]
            except ValueError:
                return None, [f"row {row_index} is not a digit grid"]
        elif isinstance(row, (list, tuple)):
            values = list(row)
        else:
            return None, [f"row {row_index} is not a sequence"]
        if width is None:
            width = len(values)
            if width == 0:
                return None, ["grid rows must be nonempty"]
        if len(values) != width:
            return None, ["grid must be rectangular"]
        if any(
            isinstance(value, bool)
            or not isinstance(value, int)
            or not 0 <= value <= 9
            for value in values
        ):
            return None, ["all cells must be integer ARC colors 0..9"]
        rows.append(values)
    return rows, []


def _overlay(grid: list[list[int]], order=PRIORITY) -> list[list[int]]:
    width = len(grid[0])
    output = full_grid(3, width, 0)
    for row in range(3):
        for col in range(width):
            for band in order:
                value = grid[band * 3 + row][col]
                if value != 0:
                    output[row][col] = value
                    break
    return output


def _analyze(grid: Any) -> dict[str, Any]:
    normalized, errors = _coerce_grid(grid)
    if errors:
        return {"errors": errors}
    assert normalized is not None
    height, width = len(normalized), len(normalized[0])
    errors = []
    if height != 12:
        errors.append(f"expected exactly 12 rows (four 3-row bands), got {height}")
        return {"errors": errors, "grid": normalized, "height": height, "width": width}

    band_colors: list[int | None] = []
    band_counts: list[int] = []
    for band in range(4):
        cells = [
            normalized[band * 3 + row][col]
            for row in range(3)
            for col in range(width)
        ]
        nonzero = [value for value in cells if value != 0]
        colors = sorted(set(nonzero))
        band_counts.append(len(nonzero))
        if not nonzero:
            errors.append(f"band {band} is empty")
            band_colors.append(None)
        elif len(colors) != 1:
            errors.append(f"band {band} must be monochrome, found colors {colors}")
            band_colors.append(None)
        else:
            band_colors.append(colors[0])

    concrete_colors = [color for color in band_colors if color is not None]
    if len(concrete_colors) == 4 and len(set(concrete_colors)) != 4:
        errors.append("the four band colors must be distinct")

    output = _overlay(normalized) if not errors else None
    pair_counts: dict[tuple[int, int], int] = {tuple(sorted(pair)): 0 for pair in _PAIR_ROLES}
    winner_counts = {band: 0 for band in range(4)}
    zero_projected = 0
    multiplicities = {count: 0 for count in range(5)}
    for row in range(3):
        for col in range(width):
            present = tuple(
                band for band in range(4) if normalized[band * 3 + row][col] != 0
            )
            multiplicities[len(present)] += 1
            if not present:
                zero_projected += 1
                continue
            if len(present) == 2:
                pair_counts[tuple(sorted(present))] = pair_counts.get(tuple(sorted(present)), 0) + 1
            winner = next(band for band in PRIORITY if band in present)
            winner_counts[winner] += 1

    total_nonzero = sum(band_counts)
    palette_mode = (
        "canonical"
        if tuple(band_colors) == CANONICAL_BAND_COLORS
        else "varied"
        if len(concrete_colors) == 4 and len(set(concrete_colors)) == 4
        else None
    )
    mask_profile = _mask_profile_from_count(width, total_nonzero)
    return {
        "errors": errors,
        "grid": normalized,
        "height": height,
        "width": width,
        "band_colors": tuple(band_colors),
        "band_counts": tuple(band_counts),
        "total_nonzero": total_nonzero,
        "palette_mode": palette_mode,
        "mask_profile": mask_profile,
        "pair_counts": pair_counts,
        "winner_counts": winner_counts,
        "zero_projected": zero_projected,
        "multiplicities": multiplicities,
        "output": output,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Accept the four-band input grammar; keep curriculum-only witnesses separate."""
    del difficulty
    analysis = _analyze(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors
    if isinstance(meta, dict):
        observed = {
            "grid_w": analysis["width"],
            "mask_profile": analysis["mask_profile"],
            "palette_mode": analysis["palette_mode"],
        }
        for name, actual in observed.items():
            requested = meta.get(name)
            if requested is not None and requested != actual:
                errors.append(f"{name} requested {requested!r}, observed {actual!r}")
    return errors


def observe_overrides(grid: Any) -> dict[str, int | str]:
    analysis = _analyze(grid)
    errors = list(analysis["errors"])
    if errors:
        raise ValueError("cannot observe axes: " + "; ".join(errors))
    if analysis["mask_profile"] is None:
        raise ValueError(
            "cannot observe generated mask_profile from foreground count "
            f"{analysis['total_nonzero']} at width {analysis['width']}"
        )
    assert analysis["palette_mode"] in PALETTE_MODES
    return {
        "grid_w": analysis["width"],
        "mask_profile": analysis["mask_profile"],
        "palette_mode": analysis["palette_mode"],
    }


def strict_canonical_like(grid) -> list[str]:
    """Linked canonical manifold: exact width/colors plus canonical count envelope."""
    analysis = _analyze(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors
    if analysis["width"] != 6:
        return [f"canonical width is 6, got {analysis['width']}"]
    if analysis["band_colors"] != CANONICAL_BAND_COLORS:
        return [
            "canonical band colors are physical bands (5,4,2,8), got "
            f"{analysis['band_colors']}"
        ]
    for band, (count, bounds) in enumerate(zip(analysis["band_counts"], _CANONICAL_COUNT_RANGES)):
        lo, hi = bounds
        if not lo <= count <= hi:
            return [f"canonical band {band} foreground count is {lo}..{hi}, got {count}"]
    if not 30 <= analysis["total_nonzero"] <= 42:
        return [
            f"canonical total foreground count is 30..42, got {analysis['total_nonzero']}"
        ]
    return []


def canonical_profile_signature(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        return None
    return (
        analysis["height"],
        analysis["width"],
        analysis["band_colors"],
        analysis["band_counts"],
    )


def semantic_signature(grid) -> dict[str, Any]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return {
        "width": analysis["width"],
        "band_colors": analysis["band_colors"],
        "band_counts": analysis["band_counts"],
        "palette_mode": analysis["palette_mode"],
        "mask_profile": analysis["mask_profile"],
        "pair_counts": dict(analysis["pair_counts"]),
        "winner_counts": dict(analysis["winner_counts"]),
        "zero_projected": analysis["zero_projected"],
        "multiplicities": dict(analysis["multiplicities"]),
        "strict_canonical_like": not strict_canonical_like(grid),
    }


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return [list(row) for row in analysis["output"]]


def _top_band_only(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return [list(row) for row in analysis["grid"][:3]]


def _natural_band_order(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return _overlay(analysis["grid"], (0, 1, 2, 3))


def _band3_before_band1(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return _overlay(analysis["grid"], (0, 3, 1, 2))


def _reverse_priority(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return _overlay(analysis["grid"], tuple(reversed(PRIORITY)))


def _canonical_color_priority(grid):
    """Shortcut that fits canonical because colors are tied to physical bands there."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    ranking = (5, 4, 8, 2)
    output = full_grid(3, analysis["width"], 0)
    for row in range(3):
        for col in range(analysis["width"]):
            values = {
                analysis["grid"][band * 3 + row][col]
                for band in range(4)
                if analysis["grid"][band * 3 + row][col] != 0
            }
            for color in ranking:
                if color in values:
                    output[row][col] = color
                    break
            else:
                if values:
                    output[row][col] = min(values)
    return output


def _max_color_overlay(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    output = full_grid(3, analysis["width"], 0)
    for row in range(3):
        for col in range(analysis["width"]):
            values = [
                analysis["grid"][band * 3 + row][col]
                for band in range(4)
                if analysis["grid"][band * 3 + row][col] != 0
            ]
            output[row][col] = max(values) if values else 0
    return output


def _default_to_band2_color(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    output = rule_mirror(grid)
    fallback = analysis["band_colors"][2]
    for row in range(3):
        for col in range(analysis["width"]):
            if output[row][col] == 0:
                output[row][col] = fallback
    return output


def _reverse_priority_on_arity(grid, target_arity: int):
    """Rival: use the intended rule except on one overlap multiplicity."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    normalized = analysis["grid"]
    output = rule_mirror(normalized)
    for row in range(3):
        for col in range(analysis["width"]):
            present = [
                band for band in range(4) if normalized[band * 3 + row][col] != 0
            ]
            if len(present) == target_arity:
                loser = next(band for band in reversed(PRIORITY) if band in present)
                output[row][col] = normalized[loser * 3 + row][col]
    return output


def _reverse_on_three_way(grid):
    return _reverse_priority_on_arity(grid, 3)


def _reverse_on_four_way(grid):
    return _reverse_priority_on_arity(grid, 4)


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "top_band_only": _top_band_only,
    "natural_band_order_0_1_2_3": _natural_band_order,
    "band3_before_band1": _band3_before_band1,
    "reverse_priority": _reverse_priority,
    "canonical_color_priority": _canonical_color_priority,
    "max_color_overlay": _max_color_overlay,
    "default_to_band2_color": _default_to_band2_color,
    "reverse_on_three_way": _reverse_on_three_way,
    "reverse_on_four_way": _reverse_on_four_way,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS
CANONICAL_SHORTCUTS = {
    "canonical_color_priority": _canonical_color_priority,
}


def _valid_analysis(grid):
    analysis = _analyze(grid)
    return analysis if not analysis["errors"] else None


def _pair_witness(a: int, b: int):
    key = tuple(sorted((a, b)))
    return lambda grid: bool(
        (analysis := _valid_analysis(grid)) and analysis["pair_counts"].get(key, 0) > 0
    )


def _arity_witness(arity: int):
    return lambda grid: bool(
        (analysis := _valid_analysis(grid)) and analysis["multiplicities"].get(arity, 0) > 0
    )


SEMANTIC_WITNESSES = {
    "band0_beats_band1": _pair_witness(0, 1),
    "band0_beats_band3": _pair_witness(0, 3),
    "band0_beats_band2": _pair_witness(0, 2),
    "band1_beats_band3": _pair_witness(1, 3),
    "band1_beats_band2": _pair_witness(1, 2),
    "band3_beats_band2": _pair_witness(3, 2),
    "each_band_can_win": lambda grid: bool(
        (analysis := _valid_analysis(grid))
        and all(analysis["winner_counts"][band] > 0 for band in range(4))
    ),
    "empty_projection_stays_zero": lambda grid: bool(
        (analysis := _valid_analysis(grid)) and analysis["zero_projected"] > 0
    ),
    "three_way_priority": _arity_witness(3),
    "four_way_priority": _arity_witness(4),
    "varied_band_color_mapping": lambda grid: bool(
        (analysis := _valid_analysis(grid)) and analysis["palette_mode"] == "varied"
    ),
}

WITNESS_RIVALS = {
    "band0_beats_band1": ["reverse_priority"],
    "band0_beats_band3": ["reverse_priority", "max_color_overlay"],
    "band0_beats_band2": ["reverse_priority"],
    "band1_beats_band3": ["reverse_priority", "band3_before_band1"],
    "band1_beats_band2": ["reverse_priority"],
    "band3_beats_band2": ["reverse_priority", "natural_band_order_0_1_2_3"],
    "each_band_can_win": ["top_band_only"],
    "empty_projection_stays_zero": ["default_to_band2_color"],
    "three_way_priority": ["reverse_on_three_way"],
    "four_way_priority": ["reverse_on_four_way"],
    "varied_band_color_mapping": ["canonical_color_priority"],
}


def _pair_analysis(pair, label: str):
    if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
        return None, [f"{label} must contain input and output grids"]
    analysis = _analyze(pair["input"])
    if analysis["errors"]:
        return None, [f"{label}: {error}" for error in analysis["errors"]]
    if pair["output"] != analysis["output"]:
        return None, [f"{label} output does not follow band priority 0>1>3>2"]
    return analysis, []


def lesson_identifiable(demos, query) -> list[str]:
    """Reject a lesson whenever any named rival still fits all demonstrations."""
    if len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    reasons: list[str] = []
    valid_demos = []
    for index, pair in enumerate(demos):
        analysis, pair_errors = _pair_analysis(pair, f"demo {index}")
        reasons.extend(pair_errors)
        if analysis is not None:
            valid_demos.append(pair)
    _query_analysis, query_errors = _pair_analysis(query, "query")
    reasons.extend(query_errors)
    if reasons:
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(pair["input"]) == pair["output"] for pair in valid_demos):
            reasons.append(f"competitor {name!r} survives every demonstration")

    # The only canonical shortcut that survives the public examples is tied to
    # the fixed 5/4/8/2 color assignment.  Every two-step scheduled window must
    # therefore contain at least one varied assignment.
    if not any(_analyze(pair["input"])["palette_mode"] == "varied" for pair in valid_demos):
        reasons.append("demonstrations never break the canonical color-priority shortcut")
    return reasons
