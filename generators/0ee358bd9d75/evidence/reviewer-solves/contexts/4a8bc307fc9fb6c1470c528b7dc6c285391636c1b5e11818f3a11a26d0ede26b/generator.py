"""Generator for ARC task 780d0b14.

Full zero rows and columns partition the input into rectangular sections.
The output is the matrix of each section's unique most-frequent nonzero
color.  Official inputs contain one nonzero color per section; generalized
draws sometimes add lower-frequency distractor colors so that a learner must
use the mode rather than merely copy the first colored cell.

The four official inputs have linked canvas dimensions, divider positions,
and output-color equality patterns.  Default draws cycle through one whole
official structural profile and two mixed-color frequency witnesses.  This
retains canonical support while teaching the frequency rule in three-example
lessons, including every single-query holdout from four consecutive draws.
Explicit controls retain the broader single-color/dominant-noise distribution.
"""
from __future__ import annotations

from collections import Counter

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "0ee358bd9d75"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "bd52339e94ff"
EXAMPLES_NEEDED = 3
LESSON_SCHEDULE_PERIOD = 3
SCHEDULE_PROFILES = ("canonical", "frequency_witness")
SUMMARY = (
    "Zero divider rows/columns form rectangular sections; emit a compact "
    "grid containing the unique dominant nonzero color of every section."
)

INVARIANTS = [
    "canvas is 8..30 by 8..30 and uses ARC colors 0..9",
    "one to three non-edge, non-adjacent full-zero divider rows and columns",
    "every section is at least 2x2 and contains both zero and nonzero cells",
    "every section has a unique most-frequent nonzero color",
    "every local section row and column contains a nonzero cell",
]

SECTION_STYLES = ("single_color", "dominant_noise")
DEGENERATE_TEXTURES: tuple[str, ...] = ()
HELPFUL_TEXTURES: tuple[str, ...] = ()

AXES = {
    "grid_h": {
        "type": "int",
        "default": "band rng 12..18 easy, 16..24 medium, 22..30 hard; "
        "one-in-three whole-profile anchor uses official 18/20/23",
        "valid": "8..30",
    },
    "grid_w": {
        "type": "int",
        "default": "band rng 12..18 easy, 16..24 medium, 22..30 hard; "
        "one-in-three whole-profile anchor includes official width 28",
        "valid": "8..30",
    },
    "row_divider_count": {
        "type": "int",
        "default": "difficulty-weighted feasible draw",
        "valid": "1..3",
    },
    "col_divider_count": {
        "type": "int",
        "default": "difficulty-weighted feasible draw",
        "valid": "1..3",
    },
    "n_output_colors": {
        "type": "int",
        "default": "band/section-count aware draw",
        "valid": "1..9",
    },
    "section_style": {
        "type": "str",
        "default": "canonical anchor then two dominant_noise witnesses; weighted with overrides",
        "valid": "|".join(SECTION_STYLES),
    },
    "fill_density": {
        "type": "float",
        "default": "band rng 0.30..0.82",
        "valid": "0.25..0.82",
    },
}

_H_LO, _H_HI = 8, 30
_W_LO, _W_HI = 8, 30
_STRICT_DENSITY_LO = 0.53
_STRICT_DENSITY_HI = 0.88
INCOMPATIBLE_OVERRIDE_COMBINATIONS = [
    {"grid_h": (8, 9, 10), "row_divider_count": 3},
    {"grid_w": (8, 9, 10), "col_divider_count": 3},
]

# (height, width, row-section sizes, column-section sizes,
#  normalized row-major output-color pattern).  These are executable
# extractions from all three train inputs plus the held-out test input.
_CANONICAL_PROFILES = (
    (18, 22, (7, 10), (6, 6, 8), (0, 1, 2, 3, 4, 1)),
    (20, 20, (8, 11), (8, 11), (0, 1, 2, 0)),
    (23, 17, (6, 9, 6), (7, 9), (0, 1, 2, 3, 4, 5)),
    (23, 28, (4, 14, 3), (7, 7, 12), (0, 1, 2, 3, 3, 4, 5, 0, 1)),
)
_CANONICAL_SIGNATURES = frozenset(_CANONICAL_PROFILES)


def _bounds(length: int, dividers: list[int]) -> list[tuple[int, int]]:
    """Half-open non-divider spans between ordered divider indices."""
    edges = [-1, *dividers, length]
    return [(left + 1, right) for left, right in zip(edges, edges[1:])]


def _analysis(grid) -> dict | None:
    """Recover rule-relevant structure from a returned grid without metadata."""
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return None
    h, w = len(grid), len(grid[0])
    if not w or any(not isinstance(row, list) or len(row) != w for row in grid):
        return None
    if any(
        not isinstance(value, int)
        or isinstance(value, bool)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return None

    zero_rows = [r for r in range(h) if all(value == 0 for value in grid[r])]
    zero_cols = [
        c for c in range(w) if all(grid[r][c] == 0 for r in range(h))
    ]
    row_spans = _bounds(h, zero_rows)
    col_spans = _bounds(w, zero_cols)
    sections = []
    for r0, r1 in row_spans:
        for c0, c1 in col_spans:
            cells = [
                grid[r][c]
                for r in range(r0, r1)
                for c in range(c0, c1)
            ]
            nonzero = Counter(value for value in cells if value != 0)
            ordered = sorted(nonzero.items(), key=lambda item: (-item[1], item[0]))
            unique_mode = bool(ordered) and (
                len(ordered) == 1 or ordered[0][1] > ordered[1][1]
            )
            sections.append(
                {
                    "span": (r0, r1, c0, c1),
                    "area": len(cells),
                    "zeros": cells.count(0),
                    "nonzero": nonzero,
                    "mode": ordered[0][0] if unique_mode else None,
                    "density": (sum(nonzero.values()) / len(cells)) if cells else 0.0,
                }
            )
    return {
        "h": h,
        "w": w,
        "zero_rows": zero_rows,
        "zero_cols": zero_cols,
        "row_spans": row_spans,
        "col_spans": col_spans,
        "row_sizes": tuple(end - start for start, end in row_spans),
        "col_sizes": tuple(end - start for start, end in col_spans),
        "sections": sections,
    }


def _normalized_pattern(values) -> tuple[int, ...]:
    labels: dict[int, int] = {}
    pattern = []
    for value in values:
        labels.setdefault(value, len(labels))
        pattern.append(labels[value])
    return tuple(pattern)


def profile_signature(grid):
    """Complete linked returned-grid signature used by the semantic audit.

    It couples dimensions, every section span, and the equality pattern of
    the answer-bearing modes.  Per-section morphology (nonzero-color count
    and density) is returned alongside the linked tuple rather than weakened
    into independent marginals.
    """
    info = _analysis(grid)
    if info is None or any(section["mode"] is None for section in info["sections"]):
        return None
    core = (
        info["h"],
        info["w"],
        info["row_sizes"],
        info["col_sizes"],
        _normalized_pattern(section["mode"] for section in info["sections"]),
    )
    return {
        "core": core,
        "nonzero_colors_per_section": tuple(
            len(section["nonzero"]) for section in info["sections"]
        ),
        "densities": tuple(section["density"] for section in info["sections"]),
    }


def canonical_profile_signature(grid):
    """Return the strict empirical-manifold signature, or ``None``.

    Exact cell locations are nuisance variation, but every official section
    has exactly one nonzero color and density 0.537..0.875.  Those universal
    facts stay in the strict predicate together with the whole linked layout
    and output-color equality pattern.
    """
    signature = profile_signature(grid)
    if signature is None:
        return None
    if any(count != 1 for count in signature["nonzero_colors_per_section"]):
        return None
    if any(
        not _STRICT_DENSITY_LO <= density <= _STRICT_DENSITY_HI
        for density in signature["densities"]
    ):
        return None
    return signature["core"]


def is_canonical_profile(grid) -> bool:
    return canonical_profile_signature(grid) in _CANONICAL_SIGNATURES


def strict_canonical_like(grid) -> bool:
    """Require both the lawful grammar and one complete canonical profile."""
    return not self_check(grid) and is_canonical_profile(grid)


def schedule_profile(seed, sample_index, difficulty=None):
    """Default semantic schedule; explicit overrides are diagnostic draws."""
    return "canonical" if sample_index % LESSON_SCHEDULE_PERIOD == 0 else "frequency_witness"


def rule_mirror(grid) -> list[list[int]]:
    """Independent Python mirror of the canonical Racket mode extraction."""
    info = _analysis(grid)
    if info is None:
        raise ValueError("invalid grid")
    modes = [section["mode"] for section in info["sections"]]
    if any(mode is None for mode in modes):
        raise ValueError("every section needs a unique nonzero mode")
    width = len(info["col_spans"])
    return [modes[start:start + width] for start in range(0, len(modes), width)]


def _rival_select(grid, selector):
    info = _analysis(grid)
    if info is None:
        raise ValueError("invalid grid")
    result = []
    for section in info["sections"]:
        r0, r1, c0, c1 = section["span"]
        values = [grid[r][c] for r in range(r0, r1) for c in range(c0, c1)
                  if grid[r][c] != 0]
        if not values:
            raise ValueError("empty section")
        if selector == "first":
            value = values[0]
        elif selector == "last":
            value = values[-1]
        elif selector == "min":
            value = min(values)
        elif selector == "max":
            value = max(values)
        else:
            counts = Counter(values)
            value = min(counts, key=lambda color: (counts[color], color))
        result.append(value)
    width = len(info["col_spans"])
    return [result[start:start + width] for start in range(0, len(result), width)]


def rival_first_nonzero(grid):
    return _rival_select(grid, "first")


def rival_last_nonzero(grid):
    return _rival_select(grid, "last")


def rival_minimum_color(grid):
    return _rival_select(grid, "min")


def rival_maximum_color(grid):
    return _rival_select(grid, "max")


def rival_least_frequent(grid):
    return _rival_select(grid, "rarest")


CANONICAL_SHORTCUTS = {
    "first_nonzero": rival_first_nonzero,
    "last_nonzero": rival_last_nonzero,
    "minimum_color": rival_minimum_color,
    "maximum_color": rival_maximum_color,
    "least_frequent": rival_least_frequent,
}
SEMANTIC_RIVALS = dict(CANONICAL_SHORTCUTS)
LESSON_COMPETITORS = dict(CANONICAL_SHORTCUTS)


def _frequency_witness(grid):
    if self_check(grid):
        return False
    intended = rule_mirror(grid)
    return all(rival(grid) != intended for rival in SEMANTIC_RIVALS.values())


SEMANTIC_WITNESSES = {"frequency_not_position_or_color_id": _frequency_witness}
WITNESS_RIVALS = {"frequency_not_position_or_color_id": list(SEMANTIC_RIVALS)}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the complete section grammar without mutating ``grid``."""
    info = _analysis(grid)
    if info is None:
        return ["grid must be a nonempty rectangular ARC-color matrix"]

    errors = []
    h, w = info["h"], info["w"]
    if not (_H_LO <= h <= _H_HI and _W_LO <= w <= _W_HI):
        errors.append(f"dims {h}x{w} outside {_H_LO}..{_H_HI}")

    for name, dividers, length in (
        ("row", info["zero_rows"], h),
        ("column", info["zero_cols"], w),
    ):
        if not 1 <= len(dividers) <= 3:
            errors.append(f"need 1..3 full-zero {name} dividers, found {len(dividers)}")
        if dividers and (dividers[0] == 0 or dividers[-1] == length - 1):
            errors.append(f"full-zero {name} divider may not lie on an edge")
        if any(right == left + 1 for left, right in zip(dividers, dividers[1:])):
            errors.append(f"adjacent full-zero {name} dividers create an empty section")

    if any(size < 2 for size in (*info["row_sizes"], *info["col_sizes"])):
        errors.append("every section side must be at least two cells")

    for index, section in enumerate(info["sections"]):
        r0, r1, c0, c1 = section["span"]
        if section["zeros"] == 0:
            errors.append(f"section {index} has no zero nuisance cells")
        if not section["nonzero"]:
            errors.append(f"section {index} has no nonzero answer color")
            continue
        if section["mode"] is None:
            errors.append(f"section {index} has a tied nonzero mode")
        if len(section["nonzero"]) > 3:
            errors.append(f"section {index} uses more than three nonzero colors")
        if any(
            all(grid[r][c] == 0 for c in range(c0, c1))
            for r in range(r0, r1)
        ):
            errors.append(f"section {index} has an empty local row")
        if any(
            all(grid[r][c] == 0 for r in range(r0, r1))
            for c in range(c0, c1)
        ):
            errors.append(f"section {index} has an empty local column")

    requested = (meta or {}).get("overrides", {}) if isinstance(meta, dict) else {}
    style = requested.get("section_style")
    if style == "single_color" and any(
        len(section["nonzero"]) != 1 for section in info["sections"]
    ):
        errors.append("section_style=single_color contains a distractor color")
    if style == "dominant_noise" and any(
        len(section["nonzero"]) < 2 for section in info["sections"]
    ):
        errors.append("section_style=dominant_noise lacks a distractor color")
    return errors


def observe_overrides(grid) -> dict:
    """Derive every exact non-dimension axis from the returned grid."""
    info = _analysis(grid)
    if info is None or any(section["mode"] is None for section in info["sections"]):
        return {}
    return {
        "row_divider_count": len(info["zero_rows"]),
        "col_divider_count": len(info["zero_cols"]),
        "n_output_colors": len({section["mode"] for section in info["sections"]}),
    }


def _banded_int(ctx, label, lo, hi, valid_lo, valid_hi):
    """Difficulty shapes defaults; explicit overrides use the global range."""
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_int(label, valid_lo, valid_hi)
    return ctx.draw_int(label, lo, hi)


def _draw_density(ctx, lo: float, hi: float) -> float:
    value = ctx.overrides.get("fill_density")
    if value is not None:
        if type(value) not in (int, float):
            raise ValueError("fill_density must be a finite number, not a coerced scalar")
        value = float(value)
        if not 0.25 <= value <= 0.82:
            raise ValueError(f"fill_density {value} outside [0.25, 0.82]")
        return value
    return ctx.draw_rng("fill_density").uniform(lo, hi)


def _minimum_length(n_dividers: int) -> int:
    return n_dividers + 2 * (n_dividers + 1)


def _choose_divider_pair(ctx, h: int, w: int, band: str, requested_colors):
    row_requested = ctx.overrides.get("row_divider_count")
    col_requested = ctx.overrides.get("col_divider_count")
    if row_requested is not None and not 1 <= int(row_requested) <= 3:
        raise ValueError("row_divider_count outside 1..3")
    if col_requested is not None and not 1 <= int(col_requested) <= 3:
        raise ValueError("col_divider_count outside 1..3")

    candidates = []
    for n_rows in range(1, 4):
        for n_cols in range(1, 4):
            if row_requested is not None and n_rows != int(row_requested):
                continue
            if col_requested is not None and n_cols != int(col_requested):
                continue
            if h < _minimum_length(n_rows) or w < _minimum_length(n_cols):
                continue
            if requested_colors is not None and (
                (n_rows + 1) * (n_cols + 1) < requested_colors
            ):
                continue
            # Keep all lawful pairs reachable.  Repetition only shapes the
            # semantic difficulty of default draws.
            total = n_rows + n_cols
            weight = (
                max(1, 7 - 2 * total)
                if band == "easy"
                else (2 if total in (4, 5) else 1)
                if band == "medium"
                else max(1, total - 2)
            )
            candidates.extend([(n_rows, n_cols)] * weight)
    if not candidates:
        error = ValueError(
            "requested dimensions/divider counts/output-color count are incompatible"
        )
        error.incompatible_axes = tuple(name for name in (
            "grid_h", "grid_w", "row_divider_count", "col_divider_count", "n_output_colors"
        ) if name in ctx.overrides)
        raise error
    chosen_rows, chosen_cols = ctx.draw_rng("divider_pair").choice(candidates)
    ctx.overrides.setdefault("row_divider_count", chosen_rows)
    ctx.overrides.setdefault("col_divider_count", chosen_cols)
    return (
        ctx.draw_int("row_divider_count", 1, 3),
        ctx.draw_int("col_divider_count", 1, 3),
    )


def _random_partition(length: int, n_dividers: int, rng) -> tuple[int, ...]:
    """Random section sizes >=2 whose sum leaves one cell per divider."""
    sizes = [2] * (n_dividers + 1)
    remaining = length - n_dividers - sum(sizes)
    if remaining < 0:
        raise ValueError(f"{n_dividers} dividers do not fit length {length}")
    for _ in range(remaining):
        sizes[rng.randrange(len(sizes))] += 1
    return tuple(sizes)


def _section_spans(sizes: tuple[int, ...]) -> list[tuple[int, int]]:
    spans = []
    cursor = 0
    for index, size in enumerate(sizes):
        spans.append((cursor, cursor + size))
        cursor += size
        if index + 1 < len(sizes):
            cursor += 1
    return spans


def _covered_cells(r0: int, r1: int, c0: int, c1: int, count: int, rng):
    """Choose ``count`` cells while covering every local row and column."""
    rows = list(range(r0, r1))
    cols = list(range(c0, c1))
    rng.shuffle(rows)
    rng.shuffle(cols)
    chosen = {
        (rows[index % len(rows)], cols[index % len(cols)])
        for index in range(max(len(rows), len(cols)))
    }
    remaining = [
        (r, c)
        for r in range(r0, r1)
        for c in range(c0, c1)
        if (r, c) not in chosen
    ]
    rng.shuffle(remaining)
    chosen.update(remaining[: max(0, count - len(chosen))])
    cells = list(chosen)
    rng.shuffle(cells)
    return cells


def _draw_sections(
    h: int,
    w: int,
    row_sizes: tuple[int, ...],
    col_sizes: tuple[int, ...],
    color_pattern: tuple[int, ...],
    palette: tuple[int, ...],
    style: str,
    density: float,
    rng,
    *,
    witness_edges: bool = False,
) -> list[list[int]]:
    grid = full_grid(h, w, 0)
    row_spans = _section_spans(row_sizes)
    col_spans = _section_spans(col_sizes)
    if len(color_pattern) != len(row_spans) * len(col_spans):
        raise ValueError("color pattern does not match section count")
    first_section, last_section = (
        rng.sample(range(len(color_pattern)), 2) if witness_edges else (-1, -1)
    )

    section_index = 0
    for r0, r1 in row_spans:
        for c0, c1 in col_spans:
            dominant = palette[color_pattern[section_index]]
            section_index += 1
            area = (r1 - r0) * (c1 - c0)
            minimum = max(r1 - r0, c1 - c0)
            if style == "dominant_noise":
                minimum = max(minimum, 3)
            painted = min(area - 1, max(minimum, round(area * density)))
            cells = _covered_cells(r0, r1, c0, c1, painted, rng)

            accent_count = 0
            accents: list[int] = []
            if style == "dominant_noise":
                accent_pool = [value for value in palette if value != dominant]
                if not accent_pool:
                    accent_pool = [value for value in range(1, 10) if value != dominant]
                rng.shuffle(accent_pool)
                accents = accent_pool[: min(2, len(accent_pool))]
                # Default lessons need minority evidence, not dense salt-and-
                # pepper color fragmentation. Explicit noise controls retain
                # their broader range for diagnostic coverage.
                accent_divisor = 12 if witness_edges else 5
                accent_count = min(max(1, painted // accent_divisor), (painted - 1) // 2)

            for index, (r, c) in enumerate(cells):
                if accent_count and index >= painted - accent_count:
                    grid[r][c] = accents[(index - (painted - accent_count)) % len(accents)]
                else:
                    grid[r][c] = dominant
            # Swap colors, never occupancy or counts. Separate sections make
            # both edge selectors fail even in a 2x2 section with one accent.
            if style == "dominant_noise" and section_index - 1 in (first_section, last_section):
                target = min(cells) if section_index - 1 == first_section else max(cells)
                if grid[target[0]][target[1]] == dominant:
                    donor = next((r, c) for r, c in cells if grid[r][c] != dominant)
                    grid[target[0]][target[1]], grid[donor[0]][donor[1]] = (
                        grid[donor[0]][donor[1]], grid[target[0]][target[1]]
                    )
    return grid


def _pattern_for_count(n_sections: int, n_colors: int, rng) -> tuple[int, ...]:
    if not 1 <= n_colors <= min(9, n_sections):
        raise ValueError(
            f"n_output_colors={n_colors} cannot fit {n_sections} sections"
        )
    pattern = list(range(n_colors))
    pattern.extend(rng.randrange(n_colors) for _ in range(n_sections - n_colors))
    rng.shuffle(pattern)
    return tuple(pattern)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if type(seed) is not int:
        raise ValueError("seed must be an integer")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer")
    overrides = {key: value for key, value in overrides.items() if value is not None}
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {unknown}")
    for name, value in overrides.items():
        if AXES[name]["type"] == "int" and type(value) is not int:
            raise ValueError(f"{name} must be an integer, not {type(value).__name__}")
    if difficulty is not None and type(difficulty) is not str:
        raise ValueError("difficulty must be easy, medium, hard, or None")
    band = "medium" if difficulty is None else difficulty
    if band not in ("easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty {difficulty!r}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=dict(overrides),
    )
    layout_rng = ctx.draw_rng("layout")

    # The canonical anchor is default-only. A complete profile is selected
    # first; no dimensions, divider positions, or color-equality roles are
    # recombined across official examples (KRF-0003).  Every declared exact
    # value is then recorded through its typed GenCtx label (KRF-0004).
    if not overrides and schedule_profile(seed, sample_index, band) == "canonical":
        profile = ctx.draw_rng("canonical_profile").choice(_CANONICAL_PROFILES)
        h, w, row_sizes, col_sizes, pattern = profile
        n_colors = max(pattern) + 1
        ctx.overrides.update(
            {
                "grid_h": h,
                "grid_w": w,
                "row_divider_count": len(row_sizes) - 1,
                "col_divider_count": len(col_sizes) - 1,
                "n_output_colors": n_colors,
                "section_style": "single_color",
            }
        )
        h = ctx.draw_int("grid_h", h, h)
        w = ctx.draw_int("grid_w", w, w)
        ctx.draw_int("row_divider_count", len(row_sizes) - 1, len(row_sizes) - 1)
        ctx.draw_int("col_divider_count", len(col_sizes) - 1, len(col_sizes) - 1)
        ctx.draw_int("n_output_colors", n_colors, n_colors)
        style = ctx.draw_choice("section_style", ("single_color",))
        density = ctx.draw_rng("fill_density").uniform(0.62, 0.82)
        palette = ctx.draw_distinct_colors("output_palette", n=n_colors, exclude={0})
        return _draw_sections(
            h, w, row_sizes, col_sizes, pattern, palette, style, density, layout_rng
        )

    if band == "easy":
        h_range, w_range = (12, 18), (12, 18)
        # Keep one-color outputs as an explicit boundary capability, not a
        # default training shortcut: every ordinary lesson needs at least two
        # answer colors so geometry, rather than a constant output, matters.
        color_range, density_range = (2, 4), (0.55, 0.75)
        style_options = ("single_color", "single_color", "single_color", "dominant_noise")
    elif band == "hard":
        h_range, w_range = (22, 30), (22, 30)
        color_range, density_range = (3, 9), (0.30, 0.82)
        style_options = ("single_color", "dominant_noise", "dominant_noise", "dominant_noise")
    else:
        h_range, w_range = (16, 24), (16, 24)
        color_range, density_range = (2, 6), (0.42, 0.78)
        style_options = ("single_color", "single_color", "dominant_noise", "dominant_noise")

    h = _banded_int(ctx, "grid_h", *h_range, _H_LO, _H_HI)
    w = _banded_int(ctx, "grid_w", *w_range, _W_LO, _W_HI)
    requested_colors = (
        int(ctx.overrides["n_output_colors"])
        if "n_output_colors" in ctx.overrides
        else None
    )
    if requested_colors is not None and not 1 <= requested_colors <= 9:
        raise ValueError("n_output_colors outside 1..9")
    n_row_dividers, n_col_dividers = _choose_divider_pair(
        ctx, h, w, band, requested_colors
    )
    n_sections = (n_row_dividers + 1) * (n_col_dividers + 1)
    if requested_colors is not None:
        n_colors = ctx.draw_int("n_output_colors", 1, min(9, n_sections))
    else:
        lo = min(color_range[0], n_sections)
        hi = min(color_range[1], n_sections, 9)
        n_colors = ctx.draw_int("n_output_colors", lo, hi)

    if "section_style" in ctx.overrides:
        style = ctx.draw_choice("section_style", SECTION_STYLES)
    elif not overrides:
        style = ctx.draw_choice("section_style", ("dominant_noise",))
    else:
        style = ctx.draw_choice("section_style", style_options)
    density = _draw_density(ctx, *density_range)
    row_sizes = _random_partition(h, n_row_dividers, ctx.draw_rng("row_partition"))
    col_sizes = _random_partition(w, n_col_dividers, ctx.draw_rng("col_partition"))
    pattern = _pattern_for_count(n_sections, n_colors, ctx.draw_rng("color_roles"))
    palette = ctx.draw_distinct_colors("output_palette", n=n_colors, exclude={0})
    return _draw_sections(
        h, w, row_sizes, col_sizes, pattern, palette, style, density, layout_rng,
        witness_edges=not overrides,
    )
