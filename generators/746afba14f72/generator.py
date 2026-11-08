"""Generator for arc_puzzle_bank_seventeenth21:E117.

Rule: fill every zero cell whose up, down, left, and right neighbours are the
same non-zero colour.  Corner cells and surrounding object texture are
irrelevant.

The teaching distribution deliberately mixes three lawful positive textures
with three near-miss distractors.  Consecutive sample indexes cover every
positive texture and every distractor kind, while the seed changes their
pairing so texture cannot become a proxy for the predicate.
"""
from __future__ import annotations

from collections import Counter
from collections.abc import Callable, Sequence
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

Grid = list[list[int]]
Cell = tuple[int, int]

GENERATOR_ID = "746afba14f72"
VERSION = "2.0.0"
TASK_ID = "746afba14f72"
RULE_HASH = "7da5ba3f320f"

SUMMARY = (
    "Fill each zero cell only when all four cardinal neighbours share one "
    "non-zero colour; ignore diagonals and surrounding texture."
)

INVARIANTS = [
    "background is 0 and every non-background value is an ARC colour 1..9",
    "every returned lesson contains at least two true cardinal cavities",
    "true cavity arms share one non-zero colour",
    "positive texture varies independently of the cardinal predicate",
    "one explicit near-miss distractor remains unchanged by the rule",
]

TEXTURES = ("plus", "ring", "side_band")
DISTRACTOR_KINDS = ("partial", "mismatch", "diagonal")
COLOR_RELATIONS = ("shared", "varied")
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.20
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, Any], ...] = ()

AXES = {
    "grid_h": {"type": "int", "default": "rng 9..12", "valid": "8..16"},
    "grid_w": {"type": "int", "default": "rng 9..12", "valid": "7..16"},
    "cavities": {"type": "int", "default": "rng 2..3", "valid": "2..3"},
    "n_colors": {"type": "int", "default": "rng 2..4", "valid": "2..4"},
    "texture": {
        "type": "str",
        "default": "scheduled",
        "valid": "|".join(TEXTURES),
    },
    "distractor_kind": {
        "type": "str",
        "default": "scheduled",
        "valid": "|".join(DISTRACTOR_KINDS),
    },
    "color_relation": {
        "type": "str",
        "default": "scheduled",
        "valid": "|".join(COLOR_RELATIONS),
    },
}

_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
_DIAGONAL = ((-1, -1), (-1, 1), (1, -1), (1, 1))
_SIDE_BANDS = (
    ((-1, -1), (-1, 1)),
    ((1, -1), (1, 1)),
    ((-1, -1), (1, -1)),
    ((-1, 1), (1, 1)),
)
_CANONICAL_PROFILES = ((8, 7), (8, 8))


def _validate_override_keys(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")


def _draw_int_full_if_overridden(
    ctx,
    overrides: dict[str, Any],
    label: str,
    ordinary_lo: int,
    ordinary_hi: int,
    valid_lo: int,
    valid_hi: int,
) -> int:
    if overrides.get(label) is not None:
        return ctx.draw_int(label, valid_lo, valid_hi)
    return ctx.draw_int(label, ordinary_lo, ordinary_hi)


def _scheduled_choice(
    ctx,
    label: str,
    options: Sequence[str],
    desired: str,
) -> str:
    """Record a keyed choice while making the ordinary schedule exact.

    GenCtx constructs a fresh deterministic RNG for each label.  Reordering the
    option tuple so that the RNG-selected index contains ``desired`` preserves
    normal override semantics and full provenance without using untracked
    randomness.
    """
    ordered = list(options)
    selected_index = ctx.draw_rng(label).randrange(len(ordered))
    desired_index = ordered.index(desired)
    ordered[selected_index], ordered[desired_index] = (
        ordered[desired_index],
        ordered[selected_index],
    )
    return ctx.draw_choice(label, tuple(ordered))


def schedule_profile(seed: int, sample_index: int, difficulty=None):
    """Return the declared ordinary-draw semantic schedule profile."""
    texture = TEXTURES[(sample_index + seed) % len(TEXTURES)]
    distractor = DISTRACTOR_KINDS[
        (sample_index + seed // len(TEXTURES)) % len(DISTRACTOR_KINDS)
    ]
    color_relation = COLOR_RELATIONS[(sample_index + seed) % len(COLOR_RELATIONS)]
    return texture, distractor, color_relation


SCHEDULE_PROFILES = tuple(
    (texture, distractor, relation)
    for texture in TEXTURES
    for distractor in DISTRACTOR_KINDS
    for relation in COLOR_RELATIONS
)


def _slot_centers(h: int, w: int) -> list[Cell]:
    # Five-cell spacing leaves a two-cell moat between 3x3 motif footprints,
    # preventing neighboring motifs from accidentally synthesizing a second
    # distractor.  The canonical seven-column width uses columns 1 and 5;
    # vertical spacing is still five cells, so its four corner slots remain
    # independent even under the maximum cavity override.
    rows = list(range(1, h - 1, 5))
    columns = [1, 5] if w == 7 else list(range(1, w - 1, 5))
    return [(r, c) for r in rows for c in columns]


def _paint_positive(
    grid: Grid,
    center: Cell,
    color: int,
    texture: str,
    orientation: int,
) -> None:
    r, c = center
    for dr, dc in _CARDINAL:
        grid[r + dr][c + dc] = color
    if texture == "ring":
        for dr, dc in _DIAGONAL:
            grid[r + dr][c + dc] = color
    elif texture == "side_band":
        for dr, dc in _SIDE_BANDS[orientation % len(_SIDE_BANDS)]:
            grid[r + dr][c + dc] = color


def _paint_distractor(
    grid: Grid,
    center: Cell,
    kind: str,
    colors: Sequence[int],
) -> None:
    r, c = center
    first, second = colors[0], colors[1]
    if kind == "partial":
        for dr, dc in _CARDINAL[:3]:
            grid[r + dr][c + dc] = first
    elif kind == "mismatch":
        for (dr, dc), color in zip(_CARDINAL, (first, first, second, second)):
            grid[r + dr][c + dc] = color
    elif kind == "diagonal":
        for dr, dc in _DIAGONAL:
            grid[r + dr][c + dc] = first
    else:  # defensive: draw_choice already validates this
        raise ValueError(f"unknown distractor_kind {kind!r}")


def _add_missing_palette_swatches(
    grid: Grid,
    colors: Sequence[int],
    motif_centers: Sequence[Cell],
) -> None:
    """Expose otherwise-unused palette colors without touching any motif.

    Swatches are isolated from motif centers and from one another, so they
    cannot alter a positive texture or combine into an accidental near-miss.
    """
    present = {value for row in grid for value in row if value != 0}
    missing = [color for color in colors if color not in present]
    if not missing:
        return
    h, w = len(grid), len(grid[0])
    border = [
        (r, c)
        for r in range(h)
        for c in range(w)
        if r in (0, h - 1) or c in (0, w - 1)
    ]
    interior = [
        (r, c)
        for r in range(1, h - 1)
        for c in range(1, w - 1)
    ]
    placed: list[Cell] = []
    for color in missing:
        for r, c in [*border, *interior]:
            if grid[r][c] != 0:
                continue
            if any(max(abs(r - rr), abs(c - cc)) <= 1 for rr, cc in motif_centers):
                continue
            if any(max(abs(r - rr), abs(c - cc)) <= 2 for rr, cc in placed):
                continue
            grid[r][c] = color
            placed.append((r, c))
            break
        else:
            raise ValueError("no isolated cell available for palette swatch")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_override_keys(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    scheduled_texture, scheduled_distractor, scheduled_relation = schedule_profile(
        seed, sample_index, difficulty
    )
    texture = _scheduled_choice(ctx, "texture", TEXTURES, scheduled_texture)
    distractor_kind = _scheduled_choice(
        ctx, "distractor_kind", DISTRACTOR_KINDS, scheduled_distractor
    )
    color_relation = _scheduled_choice(
        ctx, "color_relation", COLOR_RELATIONS, scheduled_relation
    )

    explicit_shape_axis = any(
        overrides.get(name) is not None
        for name in ("grid_h", "grid_w", "cavities", "n_colors")
    )
    canonical_draw = (
        not explicit_shape_axis
        and ctx.draw_rng("canonical_prior").random() < 0.35
    )

    if canonical_draw:
        profile = ctx.draw_rng("canonical_profile").choice(_CANONICAL_PROFILES)
        h = ctx.draw_int("grid_h", profile[0], profile[0])
        w = ctx.draw_int("grid_w", profile[1], profile[1])
        cavities = ctx.draw_int("cavities", 2, 2)
        n_colors = ctx.draw_int("n_colors", 2, 2)
    else:
        band = difficulty or "medium"
        if band == "easy":
            h_bounds = (9, 10)
            w_bounds = (9, 10)
            cavity_bounds = (2, 2)
            color_bounds = (2, 3)
        elif band == "hard":
            h_bounds = (11, 16)
            w_bounds = (11, 16)
            cavity_bounds = (3, 3)
            color_bounds = (3, 4)
        else:
            h_bounds = (9, 12)
            w_bounds = (9, 12)
            cavity_bounds = (2, 3)
            color_bounds = (2, 4)
        h = _draw_int_full_if_overridden(
            ctx, overrides, "grid_h", *h_bounds, 8, 16
        )
        w = _draw_int_full_if_overridden(
            ctx, overrides, "grid_w", *w_bounds, 7, 16
        )
        cavities = _draw_int_full_if_overridden(
            ctx, overrides, "cavities", *cavity_bounds, 2, 3
        )
        n_colors = _draw_int_full_if_overridden(
            ctx, overrides, "n_colors", *color_bounds, 2, 4
        )

    slots = _slot_centers(h, w)
    required_slots = cavities + 1
    if len(slots) < required_slots:
        raise ValueError(
            f"grid {h}x{w} has {len(slots)} motif slots, needs {required_slots}"
        )

    layout_rng = ctx.draw_rng("layout")
    layout_rng.shuffle(slots)
    positive_slots = slots[:cavities]
    distractor_slot = slots[cavities]
    colors = ctx.draw_distinct_colors("palette", n=n_colors, exclude=(0,))

    grid = full_grid(h, w, 0)
    if color_relation == "shared":
        positive_colors = [colors[0]] * cavities
    else:
        positive_colors = [colors[index % min(2, n_colors)] for index in range(cavities)]

    for index, (center, color) in enumerate(zip(positive_slots, positive_colors)):
        _paint_positive(grid, center, color, texture, orientation=index + seed)
    _paint_distractor(grid, distractor_slot, distractor_kind, colors)
    _add_missing_palette_swatches(grid, colors, [*positive_slots, distractor_slot])

    # This assertion protects every future caller, not just the review gates:
    # a placement change may not silently alter any exact axis or create a
    # second unintended cavity.
    observed = observe_overrides(grid)
    expected = {
        "grid_h": h,
        "grid_w": w,
        "cavities": cavities,
        "n_colors": n_colors,
        "texture": texture,
        "distractor_kind": distractor_kind,
        "color_relation": color_relation,
    }
    if observed != expected:
        raise AssertionError(f"generated axis mismatch: expected {expected}, got {observed}")
    return grid


def _is_grid(grid: Any) -> bool:
    return (
        isinstance(grid, list)
        and bool(grid)
        and all(isinstance(row, list) and row for row in grid)
        and len({len(row) for row in grid}) == 1
        and all(
            isinstance(value, int) and not isinstance(value, bool) and 0 <= value <= 9
            for row in grid
            for value in row
        )
    )


def _cardinal_values(grid: Grid, r: int, c: int) -> list[int]:
    return [grid[r + dr][c + dc] for dr, dc in _CARDINAL]


def _diagonal_values(grid: Grid, r: int, c: int) -> list[int]:
    return [grid[r + dr][c + dc] for dr, dc in _DIAGONAL]


def _positive_centers(grid: Grid) -> list[Cell]:
    h, w = len(grid), len(grid[0])
    out: list[Cell] = []
    for r in range(1, h - 1):
        for c in range(1, w - 1):
            if grid[r][c] != 0:
                continue
            arms = _cardinal_values(grid, r, c)
            if arms[0] != 0 and len(set(arms)) == 1:
                out.append((r, c))
    return out


def _texture_at(grid: Grid, center: Cell) -> str:
    r, c = center
    color = _cardinal_values(grid, r, c)[0]
    diagonal_cells = [
        (dr, dc)
        for dr, dc in _DIAGONAL
        if grid[r + dr][c + dc] != 0
    ]
    if any(grid[r + dr][c + dc] != color for dr, dc in diagonal_cells):
        return "foreign_diagonal"
    diagonal_set = set(diagonal_cells)
    if not diagonal_set:
        return "plus"
    if diagonal_set == set(_DIAGONAL):
        return "ring"
    if any(diagonal_set == set(side) for side in _SIDE_BANDS):
        return "side_band"
    return "irregular"


def _negative_signatures(grid: Grid) -> dict[str, list[Cell]]:
    h, w = len(grid), len(grid[0])
    signatures = {name: [] for name in DISTRACTOR_KINDS}
    for r in range(1, h - 1):
        for c in range(1, w - 1):
            if grid[r][c] != 0:
                continue
            arms = _cardinal_values(grid, r, c)
            diagonals = _diagonal_values(grid, r, c)
            nonzero_arms = [value for value in arms if value != 0]
            if (
                len(nonzero_arms) == 3
                and len(set(nonzero_arms)) == 1
                and not any(diagonals)
            ):
                signatures["partial"].append((r, c))
            if (
                len(nonzero_arms) == 4
                and len(set(nonzero_arms)) > 1
                and not any(diagonals)
            ):
                signatures["mismatch"].append((r, c))
            if (
                not any(arms)
                and diagonals[0] != 0
                and len(set(diagonals)) == 1
            ):
                signatures["diagonal"].append((r, c))
    return signatures


def _filled_same_color_centers(grid: Grid) -> list[Cell]:
    h, w = len(grid), len(grid[0])
    centers: list[Cell] = []
    for r in range(1, h - 1):
        for c in range(1, w - 1):
            if grid[r][c] == 0:
                continue
            arms = _cardinal_values(grid, r, c)
            if arms[0] == grid[r][c] and len(set(arms)) == 1:
                centers.append((r, c))
    return centers


def _analyze(grid: Any) -> dict[str, Any]:
    facts: dict[str, Any] = {
        "errors": [],
        "grid_h": 0,
        "grid_w": 0,
        "cavities": 0,
        "n_colors": 0,
        "textures": [],
        "distractor_counts": {},
        "positive_colors": [],
    }
    errors: list[str] = facts["errors"]
    if not _is_grid(grid):
        errors.append("grid must be a non-empty rectangular ARC grid with values 0..9")
        return facts

    h, w = len(grid), len(grid[0])
    facts["grid_h"] = h
    facts["grid_w"] = w
    facts["n_colors"] = len({value for row in grid for value in row if value})
    if h < 5 or w < 5:
        errors.append("grid must be at least 5x5")
    if h > 30 or w > 30:
        errors.append("grid must not exceed 30x30")

    positives = _positive_centers(grid)
    facts["positive_centers"] = positives
    facts["cavities"] = len(positives)
    facts["positive_colors"] = [
        _cardinal_values(grid, r, c)[0] for r, c in positives
    ]
    facts["textures"] = [_texture_at(grid, center) for center in positives]
    if not positives:
        errors.append("no zero cell has four matching non-zero cardinal neighbours")
    bad_textures = [name for name in facts["textures"] if name not in TEXTURES]
    if bad_textures:
        errors.append(
            "positive cavity has unsupported or foreign-colour diagonal texture: "
            + ", ".join(sorted(set(bad_textures)))
        )
    for index, left in enumerate(positives):
        for right in positives[index + 1 :]:
            if max(abs(left[0] - right[0]), abs(left[1] - right[1])) < 3:
                errors.append("positive cavity centers must be separated by at least 3 cells")
                break

    signatures = _negative_signatures(grid)
    facts["negative_signatures"] = signatures
    facts["distractor_counts"] = {
        name: len(cells) for name, cells in signatures.items()
    }

    anchors = set(positives) | set(_filled_same_color_centers(grid))
    for cells in signatures.values():
        anchors.update(cells)
    covered: set[Cell] = set()
    for r, c in anchors:
        covered.update(
            (rr, cc)
            for rr in range(max(0, r - 1), min(h, r + 2))
            for cc in range(max(0, c - 1), min(w, c + 2))
        )
    unattached = [
        (r, c)
        for r in range(1, h - 1)
        for c in range(1, w - 1)
        if grid[r][c] != 0 and (r, c) not in covered
    ]
    if unattached:
        errors.append(
            f"{len(unattached)} interior colored cell(s) are outside recognized motifs"
        )
    return facts


def _canonical_scene_grammar(facts: dict[str, Any]) -> bool:
    """Recognize the three real canonical input layouts without hardcoding grids."""
    return (
        (facts["grid_h"], facts["grid_w"]) in _CANONICAL_PROFILES
        and facts["n_colors"] == 2
        and facts["cavities"] in (1, 2)
        and sum(facts["distractor_counts"].values()) == 0
        and set(facts["textures"]).issubset({"ring", "side_band"})
        and len({c for _, c in facts.get("positive_centers", [])}) <= 1
    )


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed, no-op, and rule-hiding inputs structurally."""
    facts = _analyze(grid)
    reasons = list(facts["errors"])
    if reasons:
        return reasons
    if _canonical_scene_grammar(facts):
        return []

    if facts["cavities"] < 2:
        reasons.append("teaching scenes must contain at least two true cavities")
    if len(set(facts["textures"])) != 1:
        reasons.append("teaching scenes must use one controlled positive texture")
    distractor_total = sum(facts["distractor_counts"].values())
    distractor_kinds = [
        name for name, count in facts["distractor_counts"].items() if count
    ]
    if distractor_total != 1 or len(distractor_kinds) != 1:
        reasons.append(
            "teaching scenes must contain exactly one recognized near-miss distractor"
        )
    return reasons


def strict_canonical_like(grid) -> list[str]:
    """Recognize the task's canonical size/palette/cavity envelope."""
    facts = _analyze(grid)
    reasons = list(facts["errors"])
    if reasons:
        return reasons
    if (facts["grid_h"], facts["grid_w"]) not in _CANONICAL_PROFILES:
        reasons.append("dimensions are outside the canonical 8x7/8x8 profiles")
    if facts["n_colors"] != 2:
        reasons.append("canonical inputs use exactly two non-background colors")
    if facts["cavities"] not in (1, 2):
        reasons.append("canonical inputs contain one or two fillable cavities")
    return reasons


def observe_overrides(grid) -> dict[str, Any]:
    """Recover every declared exact axis from a returned generated grid."""
    facts = _analyze(grid)
    if facts["errors"]:
        raise ValueError("; ".join(facts["errors"]))
    textures = set(facts["textures"])
    if len(textures) != 1:
        raise ValueError(f"expected one positive texture, found {sorted(textures)}")
    present_distractors = [
        name for name, count in facts["distractor_counts"].items() if count
    ]
    if len(present_distractors) != 1:
        raise ValueError(
            "expected exactly one distractor signature, found "
            + repr({name: facts["distractor_counts"][name] for name in DISTRACTOR_KINDS})
        )
    selected = present_distractors[0]
    if facts["distractor_counts"][selected] != 1:
        raise ValueError(
            f"expected exactly one {selected} distractor, found "
            f"{facts['distractor_counts'][selected]}"
        )
    positive_colors = set(facts["positive_colors"])
    return {
        "grid_h": facts["grid_h"],
        "grid_w": facts["grid_w"],
        "cavities": facts["cavities"],
        "n_colors": facts["n_colors"],
        "texture": next(iter(textures)),
        "distractor_kind": selected,
        "color_relation": "shared" if len(positive_colors) == 1 else "varied",
    }


def rule_mirror(grid: Grid) -> Grid:
    """Pure Python mirror for tests; canonical Racket remains output authority."""
    if not _is_grid(grid):
        raise ValueError("not an ARC grid")
    out = [row[:] for row in grid]
    for r, c in _positive_centers(grid):
        out[r][c] = _cardinal_values(grid, r, c)[0]
    return out


def _fill_partial_too(grid: Grid) -> Grid:
    out = rule_mirror(grid)
    h, w = len(grid), len(grid[0])
    for r in range(1, h - 1):
        for c in range(1, w - 1):
            if grid[r][c] != 0:
                continue
            arms = [value for value in _cardinal_values(grid, r, c) if value]
            if len(arms) >= 3 and len(set(arms)) == 1:
                out[r][c] = arms[0]
    return out


def _fill_any_four_nonzero(grid: Grid) -> Grid:
    out = rule_mirror(grid)
    h, w = len(grid), len(grid[0])
    for r in range(1, h - 1):
        for c in range(1, w - 1):
            if grid[r][c] == 0 and all(_cardinal_values(grid, r, c)):
                out[r][c] = _cardinal_values(grid, r, c)[0]
    return out


def _fill_diagonal_too(grid: Grid) -> Grid:
    out = rule_mirror(grid)
    h, w = len(grid), len(grid[0])
    for r in range(1, h - 1):
        for c in range(1, w - 1):
            if grid[r][c] != 0:
                continue
            diagonals = _diagonal_values(grid, r, c)
            if diagonals[0] != 0 and len(set(diagonals)) == 1:
                out[r][c] = diagonals[0]
    return out


def _fill_only_texture(grid: Grid, allowed: set[str]) -> Grid:
    out = [row[:] for row in grid]
    for center in _positive_centers(grid):
        if _texture_at(grid, center) in allowed:
            r, c = center
            out[r][c] = _cardinal_values(grid, r, c)[0]
    return out


def _fill_only_first_match(grid: Grid) -> Grid:
    out = [row[:] for row in grid]
    centers = _positive_centers(grid)
    if centers:
        r, c = centers[0]
        out[r][c] = _cardinal_values(grid, r, c)[0]
    return out


def _fill_at_most_one_per_color(grid: Grid) -> Grid:
    out = [row[:] for row in grid]
    seen: set[int] = set()
    for r, c in _positive_centers(grid):
        color = _cardinal_values(grid, r, c)[0]
        if color in seen:
            continue
        seen.add(color)
        out[r][c] = color
    return out


def _fill_modal_color_only(grid: Grid) -> Grid:
    counts = Counter(value for row in grid for value in row if value)
    if not counts:
        return [row[:] for row in grid]
    modal = min(counts, key=lambda color: (-counts[color], color))
    out = [row[:] for row in grid]
    for r, c in _positive_centers(grid):
        color = _cardinal_values(grid, r, c)[0]
        if color == modal:
            out[r][c] = color
    return out


def _fill_only_with_diagonal_context(grid: Grid) -> Grid:
    return _fill_only_texture(grid, {"ring", "side_band"})


SEMANTIC_RIVALS: dict[str, Callable[[Grid], Grid]] = {
    "fill_partial_three_arm_centers": _fill_partial_too,
    "fill_any_four_nonzero_arms": _fill_any_four_nonzero,
    "fill_matching_diagonals": _fill_diagonal_too,
    "fill_only_plus_texture": lambda grid: _fill_only_texture(grid, {"plus"}),
    "fill_only_ring_texture": lambda grid: _fill_only_texture(grid, {"ring"}),
    "fill_only_first_match": _fill_only_first_match,
    "fill_at_most_one_per_color": _fill_at_most_one_per_color,
    "fill_only_modal_color": _fill_modal_color_only,
    "require_some_diagonal_context": _fill_only_with_diagonal_context,
}

LESSON_COMPETITORS = {
    "identity": lambda grid: [row[:] for row in grid],
    **SEMANTIC_RIVALS,
}

CANONICAL_SHORTCUTS = {
    "require_some_diagonal_context": _fill_only_with_diagonal_context,
    "fill_at_most_one_per_color": _fill_at_most_one_per_color,
}


def _witness_texture(name: str):
    return lambda grid: not self_check(grid) and set(_analyze(grid)["textures"]) == {name}


def _witness_distractor(name: str):
    return lambda grid: (
        not self_check(grid)
        and _analyze(grid)["distractor_counts"].get(name, 0) > 0
    )


def _witness_multiple(grid: Grid) -> bool:
    return not self_check(grid) and _analyze(grid)["cavities"] >= 2


def _witness_shared(grid: Grid) -> bool:
    facts = _analyze(grid)
    return not facts["errors"] and len(set(facts["positive_colors"])) == 1


def _witness_varied(grid: Grid) -> bool:
    facts = _analyze(grid)
    return not facts["errors"] and len(set(facts["positive_colors"])) >= 2


SEMANTIC_WITNESSES = {
    "positive_plus_texture": _witness_texture("plus"),
    "positive_ring_texture": _witness_texture("ring"),
    "positive_side_band_texture": _witness_texture("side_band"),
    "partial_cardinal_distractor": _witness_distractor("partial"),
    "mismatched_cardinal_distractor": _witness_distractor("mismatch"),
    "diagonal_only_distractor": _witness_distractor("diagonal"),
    "multiple_positive_cavities": _witness_multiple,
    "shared_positive_color": _witness_shared,
    "varied_positive_colors": _witness_varied,
}

WITNESS_RIVALS = {
    "positive_plus_texture": ["fill_only_ring_texture", "require_some_diagonal_context"],
    "positive_ring_texture": ["fill_only_plus_texture"],
    "positive_side_band_texture": ["fill_only_plus_texture", "fill_only_ring_texture"],
    "partial_cardinal_distractor": ["fill_partial_three_arm_centers"],
    "mismatched_cardinal_distractor": ["fill_any_four_nonzero_arms"],
    "diagonal_only_distractor": ["fill_matching_diagonals"],
    "multiple_positive_cavities": ["fill_only_first_match"],
    "shared_positive_color": ["fill_at_most_one_per_color"],
    "varied_positive_colors": ["fill_only_modal_color"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject a lesson when a named plausible rival survives its demos."""
    reasons: list[str] = []
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"expected at least {EXAMPLES_NEEDED} demonstrations"]
    items = [*demos, query]
    for index, item in enumerate(items):
        label = f"demo {index}" if index < len(demos) else "query"
        if not isinstance(item, dict) or "input" not in item or "output" not in item:
            reasons.append(f"{label} must contain input and output grids")
            continue
        input_errors = self_check(item["input"])
        if input_errors:
            reasons.append(f"{label} input is outside the teaching grammar: {input_errors}")
            continue
        if rule_mirror(item["input"]) != item["output"]:
            reasons.append(f"{label} output disagrees with the cardinal-cavity rule")
    if reasons:
        return reasons

    demo_profiles = [observe_overrides(item["input"]) for item in demos]
    if {row["texture"] for row in demo_profiles} != set(TEXTURES):
        reasons.append("three consecutive demonstrations do not cover all positive textures")
    if {row["distractor_kind"] for row in demo_profiles} != set(DISTRACTOR_KINDS):
        reasons.append("three consecutive demonstrations do not cover all distractor kinds")
    if {row["color_relation"] for row in demo_profiles} != set(COLOR_RELATIONS):
        reasons.append("demonstrations do not vary shared versus varied positive colors")

    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(
            competitor(item["input"]) == item["output"] for item in demos
        )
        if survives and competitor(query["input"]) != query["output"]:
            reasons.append(
                f"competing rule {name!r} fits every demo but changes the query answer"
            )
    return reasons
