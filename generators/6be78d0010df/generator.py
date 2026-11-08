"""Input sampler for H98 color-analogy transfer (task 6be78d0010df).

Two full-height color-1 columns split the input into three square panels.  The
cropped objects in panels A and B have the same mask; their paired colors define
an injective A->B recoloring.  Apply that map to the cropped object in panel C.

The generator deliberately varies two tempting shortcuts that the canonical
examples alone do not fully rule out: A/B objects can have independent panel
offsets, and the color correspondence can be non-monotone.
"""
from __future__ import annotations

from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "6be78d0010df"
TASK_ID = GENERATOR_ID
RULE_HASH = "20d652a9b458"
VERSION = "3.0.0"

SUMMARY = (
    "Two color-1 divider columns make three equal square panels.  Crop the "
    "colored objects in A and B, infer their consistent one-to-one color map, "
    "then recolor the cropped C object with that map.  A and B may be placed "
    "at different offsets, and the palette mapping need not preserve order."
)

INVARIANTS = [
    "a 4..7 by (3n+2) grid has exactly two full-height color-1 dividers at n and 2n+1",
    "A and B are nonempty crops with identical masks and a consistent injective recoloring",
    "source and target palettes are disjoint; C is nonempty and uses every source color",
    "all four advertised controls are recoverable from the returned pixels",
    "every four consecutive default draws contain a canonical-profile case and both shortcut witnesses",
]

EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.20
LESSON_SCHEDULE_PERIOD = 4

ALIGNMENTS = ("aligned", "shifted")
MAPPING_ORDERS = ("monotone", "nonmonotone")
SCHEDULE_PROFILES = (
    "canonical_shifted_nonmonotone",
    "band_aligned_monotone",
    "band_shifted_monotone",
    "band_aligned_nonmonotone",
)

AXES = {
    "panel_n": {
        "type": "int",
        "default": "6 on schedule anchor; otherwise difficulty-banded",
        "valid": "4..7",
    },
    "n_colors_used": {
        "type": "int",
        "default": "2 on schedule anchor; otherwise difficulty-banded",
        "valid": "2..4",
    },
    "analogy_alignment": {
        "type": "str",
        "default": "scheduled aligned/shifted",
        "valid": "aligned|shifted",
    },
    "mapping_order": {
        "type": "str",
        "default": "scheduled monotone/nonmonotone",
        "valid": "monotone|nonmonotone",
    },
}

INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()


def _band(difficulty: Any) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return difficulty
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def _validate_call(seed: Any, sample_index: Any, overrides: dict[str, Any]) -> None:
    if type(seed) is not int:
        raise ValueError(f"seed must be an integer, not {type(seed).__name__}")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a non-negative integer")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name in ("panel_n", "n_colors_used"):
        value = overrides.get(name)
        if value is not None and type(value) is not int:
            raise ValueError(f"{name} must be an integer, not {type(value).__name__}")
    for name, options in (
        ("analogy_alignment", ALIGNMENTS),
        ("mapping_order", MAPPING_ORDERS),
    ):
        value = overrides.get(name)
        if value is not None and (type(value) is not str or value not in options):
            raise ValueError(f"{name} must be one of {options}, got {value!r}")


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> str:
    """Return the four-state cyclic teaching profile for a default draw."""
    if type(seed) is not int:
        raise ValueError(f"seed must be an integer, not {type(seed).__name__}")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a non-negative integer")
    _band(difficulty)
    return SCHEDULE_PROFILES[sample_index % LESSON_SCHEDULE_PERIOD]


def _draw_int_axis(ctx, name: str, lo: int, hi: int, choices: tuple[int, ...], overrides: dict[str, Any]) -> int:
    if overrides.get(name) is not None:
        return ctx.draw_int_strict(name, lo, hi)
    return ctx.draw_choice(name, choices)


def _draw_choice_axis(ctx, name: str, options: tuple[str, ...], scheduled: str, overrides: dict[str, Any]) -> str:
    if overrides.get(name) is not None:
        return ctx.draw_choice(name, options)
    return ctx.draw_choice(name, (scheduled,))


def _axis_values(ctx, sample_index: int, band: str, overrides: dict[str, Any]) -> tuple[int, int, str, str]:
    phase = sample_index % LESSON_SCHEDULE_PERIOD
    if phase == 0:
        panel_choices = (6,)
        color_choices = (2,)
    else:
        panel_choices = {
            "easy": (4, 5),
            "medium": (5, 6),
            "hard": (6, 7),
        }[band]
        color_choices = {
            "easy": (2,),
            "medium": (2, 3),
            "hard": (3, 4),
        }[band]
    scheduled_alignment = ("shifted", "aligned", "shifted", "aligned")[phase]
    scheduled_order = ("nonmonotone", "monotone", "monotone", "nonmonotone")[phase]
    panel_n = _draw_int_axis(ctx, "panel_n", 4, 7, panel_choices, overrides)
    n_colors = _draw_int_axis(ctx, "n_colors_used", 2, 4, color_choices, overrides)
    alignment = _draw_choice_axis(ctx, "analogy_alignment", ALIGNMENTS, scheduled_alignment, overrides)
    mapping_order = _draw_choice_axis(ctx, "mapping_order", MAPPING_ORDERS, scheduled_order, overrides)
    return panel_n, n_colors, alignment, mapping_order


def _paired_colored_shape(rng, panel_n: int, palette: tuple[int, ...]) -> dict[tuple[int, int], int]:
    """Build a connected snake whose every palette role owns an adjacent pair.

    Canonical inputs contain either zero or two singleton nonzero components.
    Giving each generated color an explicit adjacent pair keeps the sampler in
    that observed structural support instead of creating accidental markers.
    """
    minimum_cells = 2 * len(palette)
    boxes = [
        (height, width)
        for height in range(2, panel_n)
        for width in range(2, panel_n)
        if height * width >= minimum_cells
    ]
    if not boxes:
        raise RuntimeError("panel cannot fit paired palette roles")
    box_h, box_w = rng.choice(boxes)
    snake: list[tuple[int, int]] = []
    for r in range(box_h):
        columns = range(box_w) if r % 2 == 0 else range(box_w - 1, -1, -1)
        snake.extend((r, c) for c in columns)

    max_pairs = min(len(snake) // 2, len(palette) + 2)
    total_pairs = rng.randint(len(palette), max_pairs)
    count = 2 * total_pairs
    start = rng.randint(0, len(snake) - count)
    path = snake[start : start + count]
    r0 = min(r for r, _ in path)
    c0 = min(c for _, c in path)
    path = [(r - r0, c - c0) for r, c in path]

    pair_colors = list(palette)
    rng.shuffle(pair_colors)
    while len(pair_colors) < total_pairs:
        pair_colors.append(rng.choice(palette))
    colored: dict[tuple[int, int], int] = {}
    for index, color in enumerate(pair_colors):
        colored[path[2 * index]] = color
        colored[path[2 * index + 1]] = color
    return colored

def _offsets(panel_n: int, shape: tuple[tuple[int, int], ...]) -> tuple[tuple[int, int], ...]:
    shape_h = max(r for r, _ in shape) + 1
    shape_w = max(c for _, c in shape) + 1
    return tuple(
        (r, c)
        for r in range(panel_n - shape_h + 1)
        for c in range(panel_n - shape_w + 1)
    )


def _place(panel: list[list[int]], colored: dict[tuple[int, int], int], offset: tuple[int, int]) -> None:
    ro, co = offset
    for (r, c), color in colored.items():
        panel[ro + r][co + c] = color


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(seed, sample_index, overrides)
    band = _band(difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    panel_n, n_colors, alignment, mapping_order = _axis_values(ctx, sample_index, band, overrides)

    palette_rng = ctx.draw_rng("palettes")
    palette = palette_rng.sample(tuple(range(2, 10)), 2 * n_colors)
    source = tuple(sorted(palette[:n_colors]))
    targets = sorted(palette[n_colors:])
    if mapping_order == "nonmonotone":
        targets = targets[1:] + targets[:1]
    target = tuple(targets)
    color_map = dict(zip(source, target))

    analogy_colors = _paired_colored_shape(ctx.draw_rng("analogy_shape"), panel_n, source)
    analogy_shape = tuple(analogy_colors)
    placements = _offsets(panel_n, analogy_shape)
    placement_rng = ctx.draw_rng("analogy_placement")
    a_offset = placement_rng.choice(placements)
    if alignment == "aligned":
        b_offset = a_offset
    else:
        alternatives = [offset for offset in placements if offset != a_offset]
        if not alternatives:
            raise RuntimeError("shifted alignment requested but no second placement exists")
        b_offset = placement_rng.choice(alternatives)

    query_colors = _paired_colored_shape(ctx.draw_rng("query_shape"), panel_n, source)
    query_shape = tuple(query_colors)
    query_offset = ctx.draw_rng("query_placement").choice(_offsets(panel_n, query_shape))

    a_panel = full_grid(panel_n, panel_n, 0)
    b_panel = full_grid(panel_n, panel_n, 0)
    c_panel = full_grid(panel_n, panel_n, 0)
    _place(a_panel, analogy_colors, a_offset)
    _place(b_panel, {cell: color_map[color] for cell, color in analogy_colors.items()}, b_offset)
    _place(c_panel, query_colors, query_offset)

    width = 3 * panel_n + 2
    grid = full_grid(panel_n, width, 0)
    d1, d2 = panel_n, 2 * panel_n + 1
    for r in range(panel_n):
        grid[r][d1] = 1
        grid[r][d2] = 1
        grid[r][:d1] = a_panel[r]
        grid[r][d1 + 1 : d2] = b_panel[r]
        grid[r][d2 + 1 :] = c_panel[r]
    return grid


def _crop(panel: list[list[int]]) -> tuple[list[list[int]], tuple[int, int]]:
    cells = [
        (r, c)
        for r, row in enumerate(panel)
        for c, value in enumerate(row)
        if value != 0
    ]
    if not cells:
        raise ValueError("panel object must be nonempty")
    r0 = min(r for r, _ in cells)
    r1 = max(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    c1 = max(c for _, c in cells)
    return [row[c0 : c1 + 1] for row in panel[r0 : r1 + 1]], (r0, c0)


def _analyse(grid: Any) -> tuple[dict[str, Any], list[str]]:
    info: dict[str, Any] = {}
    if not isinstance(grid, (list, tuple)) or not grid:
        return info, ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return info, ["expected nonempty grid rows"]
    h, w = len(grid), len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != w for row in grid):
        return info, ["grid must be rectangular"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return info, ["cells must be integer ARC colors 0..9 (not bool)"]

    errors: list[str] = []
    if not 4 <= h <= 7:
        errors.append(f"panel height must be 4..7, got {h}")
    if w != 3 * h + 2:
        errors.append(f"width must equal 3*height+2, got {h}x{w}")
    if errors:
        return info, errors

    d1, d2 = h, 2 * h + 1
    full_dividers = [c for c in range(w) if all(grid[r][c] == 1 for r in range(h))]
    if full_dividers != [d1, d2]:
        errors.append(f"full-height color-1 dividers must be exactly [{d1}, {d2}], got {full_dividers}")
    if any(grid[r][c] == 1 for r in range(h) for c in range(w) if c not in (d1, d2)):
        errors.append("color 1 may appear only in the two divider columns")
    if errors:
        return info, errors

    a_panel = [list(row[:d1]) for row in grid]
    b_panel = [list(row[d1 + 1 : d2]) for row in grid]
    c_panel = [list(row[d2 + 1 :]) for row in grid]
    try:
        a_crop, a_offset = _crop(a_panel)
        b_crop, b_offset = _crop(b_panel)
        c_crop, c_offset = _crop(c_panel)
    except ValueError as exc:
        return info, [str(exc)]

    if (len(a_crop), len(a_crop[0])) != (len(b_crop), len(b_crop[0])):
        errors.append("A and B crops must have identical dimensions")
        return info, errors

    mapping: dict[int, int] = {}
    reverse: dict[int, int] = {}
    for r in range(len(a_crop)):
        for c in range(len(a_crop[0])):
            av, bv = a_crop[r][c], b_crop[r][c]
            if (av == 0) != (bv == 0):
                errors.append("A and B crops must have identical nonzero masks")
                continue
            if av == 0:
                continue
            prior = mapping.get(av)
            if prior is not None and prior != bv:
                errors.append(f"source color {av} maps inconsistently to {prior} and {bv}")
            mapped_source = reverse.get(bv)
            if mapped_source is not None and mapped_source != av:
                errors.append(f"target color {bv} is shared by source colors {mapped_source} and {av}")
            mapping[av] = bv
            reverse[bv] = av

    source_colors = set(mapping)
    target_colors = set(mapping.values())
    if not source_colors:
        errors.append("A/B analogy must define at least one color mapping")
    if source_colors & target_colors:
        errors.append("source and target palettes must be disjoint")
    query_colors = {value for row in c_crop for value in row if value != 0}
    foreign = query_colors - source_colors
    if foreign:
        errors.append(f"C contains unmapped source color(s): {sorted(foreign)}")
    if query_colors != source_colors:
        errors.append(
            f"C must use every source color; expected {sorted(source_colors)}, got {sorted(query_colors)}"
        )

    info.update(
        {
            "panel_n": h,
            "dividers": (d1, d2),
            "a_panel": a_panel,
            "b_panel": b_panel,
            "c_panel": c_panel,
            "a_crop": a_crop,
            "b_crop": b_crop,
            "c_crop": c_crop,
            "a_offset": a_offset,
            "b_offset": b_offset,
            "c_offset": c_offset,
            "mapping": mapping,
            "source_colors": source_colors,
            "target_colors": target_colors,
        }
    )
    return info, errors


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    return _analyse(grid)[1]


def observe_overrides(grid: Any) -> dict[str, Any]:
    info, errors = _analyse(grid)
    if errors:
        raise ValueError("; ".join(errors))
    source = sorted(info["mapping"])
    mapped = [info["mapping"][color] for color in source]
    return {
        "panel_n": info["panel_n"],
        "n_colors_used": len(source),
        "analogy_alignment": "aligned" if info["a_offset"] == info["b_offset"] else "shifted",
        "mapping_order": "monotone" if mapped == sorted(mapped) else "nonmonotone",
    }


def rule_mirror(grid: Any) -> list[list[int]]:
    """Independent Python mirror of the pinned Racket authority."""
    info, errors = _analyse(grid)
    if errors:
        raise ValueError("; ".join(errors))
    mapping = info["mapping"]
    return [
        [0 if value == 0 else mapping[value] for value in row]
        for row in info["c_crop"]
    ]


def strict_canonical_like(grid: Any) -> list[str]:
    """Recognize the exact canonical input envelope, not merely a marginal shape."""
    info, errors = _analyse(grid)
    if errors:
        return errors
    reasons: list[str] = []
    if info["panel_n"] != 6:
        reasons.append("canonical panels are 6x6")
    palette_size = len({value for row in grid for value in row})
    if palette_size not in (4, 6):
        reasons.append(f"canonical palette size is 4 or 6, got {palette_size}")
    return reasons


def _sorted_palette_mapping(grid: Any) -> list[list[int]]:
    """Rival: map sorted source colors to sorted target colors."""
    info, errors = _analyse(grid)
    if errors:
        raise ValueError("; ".join(errors))
    mapping = dict(zip(sorted(info["source_colors"]), sorted(info["target_colors"])))
    return [[0 if value == 0 else mapping[value] for value in row] for row in info["c_crop"]]


def _aligned_panels_only(grid: Any) -> list[list[int]]:
    """Rival: infer the analogy only when A and B occupy the same panel offset."""
    info, errors = _analyse(grid)
    if errors:
        raise ValueError("; ".join(errors))
    if info["a_offset"] != info["b_offset"]:
        return [list(row) for row in info["c_crop"]]
    return rule_mirror(grid)


def _has_nonmonotone_mapping(grid: Any) -> bool:
    try:
        return observe_overrides(grid)["mapping_order"] == "nonmonotone"
    except ValueError:
        return False


def _has_independent_panel_offsets(grid: Any) -> bool:
    try:
        return observe_overrides(grid)["analogy_alignment"] == "shifted"
    except ValueError:
        return False


SEMANTIC_WITNESSES: dict[str, Callable[[Any], bool]] = {
    "nonmonotone_mapping": _has_nonmonotone_mapping,
    "independent_panel_offsets": _has_independent_panel_offsets,
}
SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "sorted_palette_mapping": _sorted_palette_mapping,
    "aligned_panels_only": _aligned_panels_only,
}
WITNESS_RIVALS = {
    "nonmonotone_mapping": ["sorted_palette_mapping"],
    "independent_panel_offsets": ["aligned_panels_only"],
}
CANONICAL_SHORTCUTS = {"aligned_panels_only": _aligned_panels_only}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def _validate_labeled_pair(pair: Any, label: str) -> tuple[list[str], list[list[int]] | None]:
    reasons: list[str] = []
    if not isinstance(pair, dict) or "input" not in pair:
        return [f"{label} is not an input/output pair"], None
    errors = self_check(pair["input"])
    if errors:
        return [f"{label} malformed: {errors[0]}"], None
    expected = rule_mirror(pair["input"])
    if "output" not in pair:
        reasons.append(f"{label} has no output label")
    elif pair["output"] != expected:
        reasons.append(f"{label} output does not match the authoritative color analogy")
    return reasons, expected


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons on which a declared shortcut fits all demos but changes the query."""
    if not isinstance(demos, (list, tuple)):
        return ["demonstrations must be a sequence"]
    reasons: list[str] = []
    if len(demos) < EXAMPLES_NEEDED:
        reasons.append(f"need at least {EXAMPLES_NEEDED} demonstrations")

    valid_demos: list[dict[str, Any]] = []
    for index, pair in enumerate(demos):
        pair_reasons, _ = _validate_labeled_pair(pair, f"demo {index}")
        reasons.extend(pair_reasons)
        if not pair_reasons:
            valid_demos.append(pair)

    query_reasons, query_expected = _validate_labeled_pair(query, "query")
    reasons.extend(query_reasons)
    if reasons or query_expected is None or len(valid_demos) != len(demos):
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        try:
            fits_demos = all(competitor(pair["input"]) == pair["output"] for pair in valid_demos)
            changes_query = competitor(query["input"]) != query_expected
        except Exception as exc:
            reasons.append(f"{name} competitor failed: {type(exc).__name__}: {exc}")
            continue
        if fits_demos and changes_query:
            reasons.append(f"{name} fits every demonstration but predicts a different query output")
    return reasons
