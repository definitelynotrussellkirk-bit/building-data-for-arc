"""Semantic generator for ARC task 17b682bce66f — keyed offset merge.

A single maroon 9 cell is the reference origin.  Cyan 8 cells define a cloud
of relative offsets around it.  Each anchor color is both a rotation command
and an output-color command: 2/3/4/5 mean 0/90/180/270 degrees and paint
4/5/6/7 respectively.  The output starts empty and processes anchors row-major:
write the anchor, stamp its rotated cloud, and max-merge paint at that turn.

The teaching distribution mixes ten retained, translation-varying witness
profiles with a procedural family.  The latter grows new connected asymmetric
clouds and independently places the reference and distinct anchors.  Dimensions
and relative layouts vary, not merely absolute translation.  Fixed profiles keep
all five official examples and collision/edge branches common.  Anchors are
written at their row-major turn, not protected from later paint.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "17b682bce66f"
TASK_ID = GENERATOR_ID
VERSION = "3.1.0"
RULE_HASH = "2e0efbc6319e"

SUMMARY = (
    "Choose one complete keyed-offset scene profile.  The grid contains one "
    "color-9 reference, a connected asymmetric color-8 offset cloud, and "
    "three or four distinct anchors from colors 2,3,4,5.  Anchor colors encode "
    "quarter-turn rotations 0/90/180/270 and paint colors 4/5/6/7.  The rule "
    "replays the rotated cloud at every anchor in row-major order and "
    "max-merges paint after writing each anchor. Five official and five branch "
    "witness profiles remain common; procedural connected clouds, dimensions, "
    "references and anchor layouts prevent a ten-template-only curriculum."
)

INVARIANTS = [
    "background is 0 and the only foreground colors are 2,3,4,5,8,9",
    "there is exactly one color-9 reference and four or five color-8 cloud cells",
    "the reference plus cloud is 4-connected, spans both axes, and is quarter-turn asymmetric",
    "there are three or four anchors with pairwise-distinct colors from 2,3,4,5",
    "every rotated cloud stamp is fully in bounds",
    "draws mix ten exact translated witnesses with novel procedural scenes",
]

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()


@dataclass(frozen=True)
class SceneSpec:
    height: int
    width: int
    cells: tuple[tuple[int, int, int], ...]
    allow_translation: bool = True


def _cells_from_rule_scene(
    reference: tuple[int, int],
    offsets: Iterable[tuple[int, int]],
    anchors: Iterable[tuple[int, int, int]],
) -> tuple[tuple[int, int, int], ...]:
    rr, rc = reference
    cells = [(rr, rc, 9)]
    cells.extend((rr + dr, rc + dc, 8) for dr, dc in offsets)
    cells.extend(anchors)
    return tuple(sorted(cells))


# Exact official input scenes.  Generation only translates the complete scene;
# tests derive the same normalized signatures from canonical train + held-out
# test inputs so these constants cannot silently drift.
_SCENES: dict[str, SceneSpec] = {
    "canonical_train_1": SceneSpec(
        11,
        11,
        (
            (1, 1, 9), (1, 2, 8), (2, 1, 8), (2, 2, 8),
            (3, 2, 8), (7, 4, 2), (7, 6, 3), (8, 5, 4),
        ),
    ),
    "canonical_train_2": SceneSpec(
        12,
        12,
        (
            (1, 2, 8), (2, 2, 9), (2, 3, 8), (3, 2, 8),
            (3, 3, 8), (3, 4, 8), (7, 5, 2), (7, 7, 5),
            (9, 6, 3),
        ),
    ),
    "canonical_train_3": SceneSpec(
        11,
        13,
        (
            (2, 1, 9), (2, 2, 8), (3, 1, 8), (3, 2, 8),
            (4, 2, 8), (6, 8, 4), (7, 9, 2), (8, 8, 5),
        ),
    ),
    "canonical_train_4": SceneSpec(
        12,
        12,
        (
            (1, 3, 8), (2, 2, 9), (2, 3, 8), (3, 2, 8),
            (3, 3, 8), (4, 3, 8), (8, 4, 3), (8, 6, 4),
            (9, 5, 2),
        ),
    ),
    "canonical_test_1": SceneSpec(
        12,
        12,
        (
            (1, 2, 8), (2, 2, 9), (2, 3, 8), (3, 2, 8),
            (3, 3, 8), (4, 3, 8), (7, 5, 2), (7, 7, 3),
            (9, 6, 5),
        ),
    ),
    "all_rotations": SceneSpec(
        13,
        13,
        _cells_from_rule_scene(
            (4, 4),
            ((-2, 0), (-1, 0), (0, 1), (1, 1), (1, 2)),
            ((3, 6, 2), (7, 5, 3), (7, 8, 4), (10, 3, 5)),
        ),
    ),
    "paint_overlap": SceneSpec(
        13,
        13,
        _cells_from_rule_scene(
            (3, 3),
            ((-1, 0), (0, 1), (1, 0), (1, 1), (2, 1)),
            ((6, 8, 2), (7, 7, 3), (5, 9, 5)),
        ),
    ),
    "anchor_overwrite": SceneSpec(
        12,
        14,
        _cells_from_rule_scene(
            (3, 3),
            ((0, 1), (1, 0), (1, 1), (2, 1)),
            ((6, 4, 2), (7, 5, 4), (8, 8, 5)),
        ),
    ),
    "edge_touch": SceneSpec(
        14,
        14,
        _cells_from_rule_scene(
            (5, 5),
            ((-2, 0), (-1, 0), (0, 1), (1, 1), (1, 2)),
            ((2, 3, 2), (4, 11, 3), (11, 3, 4), (9, 2, 5)),
        ),
        allow_translation=False,
    ),
    "wide_nonoverlap": SceneSpec(
        10,
        15,
        _cells_from_rule_scene(
            (3, 4),
            ((-1, -1), (-1, 0), (0, 1), (1, 1), (2, 1)),
            ((3, 10, 2), (5, 13, 3), (8, 7, 4), (2, 2, 5)),
        ),
    ),
}

FIXED_PROFILES = tuple(_SCENES)
SCENE_PROFILES = FIXED_PROFILES + ("procedural",)
CANONICAL_PROFILES = tuple(name for name in SCENE_PROFILES if name.startswith("canonical_"))
GENERALIZED_PROFILES = tuple(name for name in SCENE_PROFILES if name not in CANONICAL_PROFILES)

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "difficulty-weighted complete profile prior",
        "valid": (
            "canonical_train_1|canonical_train_2|canonical_train_3|"
            "canonical_train_4|canonical_test_1|all_rotations|paint_overlap|"
            "anchor_overwrite|edge_touch|wide_nonoverlap|procedural"
        ),
    }
}

# Mixture (canonical / fixed branch witnesses / procedural):
# easy 40/20/40%, medium 20/20/60%, hard 12.5/12.5/75%.
# Retain exact linked official profiles rather than weakening their predicate.
_FIXED_GENERALIZED = tuple(name for name in FIXED_PROFILES if name not in CANONICAL_PROFILES)
_PROFILE_POOLS = {
    "easy": CANONICAL_PROFILES * 2 + _FIXED_GENERALIZED + ("procedural",) * 10,
    "medium": CANONICAL_PROFILES + _FIXED_GENERALIZED + ("procedural",) * 15,
    "hard": CANONICAL_PROFILES + _FIXED_GENERALIZED + ("procedural",) * 30,
}


def _band(difficulty: Any) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return difficulty
    raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")


def _rotate_offset(color: int, dr: int, dc: int) -> tuple[int, int]:
    if color == 2:
        return dr, dc
    if color == 3:
        return dc, -dr
    if color == 4:
        return -dr, -dc
    if color == 5:
        return -dc, dr
    raise ValueError(f"anchor color must be one of 2,3,4,5; got {color}")


def _paint_color(color: int) -> int:
    return {2: 4, 3: 5, 4: 6, 5: 7}[color]


def _normalized_cells(
    height: int, width: int, cells: Iterable[tuple[int, int, int]]
) -> tuple[int, int, tuple[tuple[int, int, int], ...]]:
    ordered = tuple(sorted(cells))
    if not ordered:
        return height, width, ()
    row0 = min(row for row, _, _ in ordered)
    col0 = min(col for _, col, _ in ordered)
    return (
        height,
        width,
        tuple(sorted((row - row0, col - col0, color) for row, col, color in ordered)),
    )


def _spec_signature(spec: SceneSpec):
    return _normalized_cells(spec.height, spec.width, spec.cells)


_SIGNATURE_TO_PROFILE = {_spec_signature(spec): name for name, spec in _SCENES.items()}
if len(_SIGNATURE_TO_PROFILE) != len(_SCENES):
    raise RuntimeError("scene-profile signatures must be unique")

_CANONICAL_SIGNATURES = frozenset(
    _spec_signature(_SCENES[name]) for name in CANONICAL_PROFILES
)


def _validate_grid(grid: Any) -> tuple[list[str], int, int]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty list of rows"], 0, 0
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"], 0, 0
    height, width = len(grid), len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"], height, width
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return [f"cell {row},{col} must be an integer ARC color 0..9"], height, width
    return [], height, width


def _foreground_cells(grid) -> tuple[tuple[int, int, int], ...]:
    return tuple(
        (row, col, int(value))
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 0
    )


def _cloud_and_anchors(grid):
    references = []
    cloud_cells = []
    anchors = []
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value == 9:
                references.append((row, col))
            elif value == 8:
                cloud_cells.append((row, col))
            elif value in (2, 3, 4, 5):
                anchors.append((row, col, value))
    reference = references[0] if len(references) == 1 else None
    offsets = (
        tuple(sorted((row - reference[0], col - reference[1]) for row, col in cloud_cells))
        if reference is not None
        else ()
    )
    return references, cloud_cells, offsets, anchors


def _stamp_cells(anchor, offsets) -> frozenset[tuple[int, int]]:
    row, col, color = anchor
    return frozenset(
        (row + rotated_row, col + rotated_col)
        for dr, dc in offsets
        for rotated_row, rotated_col in [_rotate_offset(color, dr, dc)]
    )


def _is_four_connected(cells: set[tuple[int, int]]) -> bool:
    if not cells:
        return False
    seen = {next(iter(cells))}
    frontier = list(seen)
    while frontier:
        row, col = frontier.pop()
        for nxt in ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)):
            if nxt in cells and nxt not in seen:
                seen.add(nxt)
                frontier.append(nxt)
    return seen == cells


def _rotation_forms(offsets: tuple[tuple[int, int], ...]):
    forms = []
    current = tuple(sorted(offsets))
    for _ in range(4):
        forms.append(current)
        current = tuple(sorted((dc, -dr) for dr, dc in current))
    return tuple(forms)


def scene_observables(grid) -> dict[str, Any]:
    """Return task-linked structural observables for audits and focused tests."""
    basic_errors, height, width = _validate_grid(grid)
    if basic_errors:
        raise ValueError("; ".join(basic_errors))
    references, cloud_cells, offsets, anchors = _cloud_and_anchors(grid)
    if len(references) != 1:
        raise ValueError(f"expected exactly one color-9 reference, got {len(references)}")

    stamp_sets = [_stamp_cells(anchor, offsets) for anchor in anchors]
    overlap_pairs = 0
    overlap_cells: set[tuple[int, int]] = set()
    for left in range(len(stamp_sets)):
        for right in range(left + 1, len(stamp_sets)):
            shared = stamp_sets[left] & stamp_sets[right]
            if shared:
                overlap_pairs += 1
                overlap_cells.update(shared)
    anchor_hits = sum(
        (anchor[0], anchor[1]) in stamp_sets[other]
        for index, anchor in enumerate(anchors)
        for other in range(len(stamp_sets))
        if other != index
    )
    union = set().union(*stamp_sets) if stamp_sets else set()
    edge_touch = {
        "top": any(row == 0 for row, _ in union),
        "bottom": any(row == height - 1 for row, _ in union),
        "left": any(col == 0 for _, col in union),
        "right": any(col == width - 1 for _, col in union),
    }
    signature = _normalized_cells(height, width, _foreground_cells(grid))
    return {
        "height": height,
        "width": width,
        "scene_profile": _SIGNATURE_TO_PROFILE.get(signature, "procedural"),
        "reference": references[0],
        "cloud_count": len(cloud_cells),
        "cloud_offsets": offsets,
        "anchor_count": len(anchors),
        "anchor_colors": tuple(sorted(color for _, _, color in anchors)),
        "overlap_pair_count": overlap_pairs,
        "overlap_cell_count": len(overlap_cells),
        "anchor_hit_count": anchor_hits,
        "edge_touch": edge_touch,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the full keyed-offset lesson grammar, including bad impostors."""
    del difficulty
    errors, height, width = _validate_grid(grid)
    if errors:
        return errors

    if not 8 <= height <= 16 or not 8 <= width <= 16:
        errors.append(f"grid dimensions must each be in 8..16, got {height}x{width}")

    illegal = sorted(
        {
            value
            for row in grid
            for value in row
            if value not in (0, 2, 3, 4, 5, 8, 9)
        }
    )
    if illegal:
        errors.append(f"unexpected input colors: {illegal}")

    references, cloud_cells, offsets, anchors = _cloud_and_anchors(grid)
    if len(references) != 1:
        errors.append(f"expected exactly one color-9 reference, got {len(references)}")
        return errors
    reference = references[0]

    if not 4 <= len(cloud_cells) <= 5:
        errors.append(f"expected four or five color-8 cloud cells, got {len(cloud_cells)}")
    cloud_with_origin = {reference, *cloud_cells}
    if not _is_four_connected(cloud_with_origin):
        errors.append("reference plus color-8 cloud must be 4-connected")
    if offsets:
        if max(abs(dr) for dr, _ in offsets) > 3 or max(abs(dc) for _, dc in offsets) > 3:
            errors.append("cloud offsets must remain within three cells of the reference")
        if len({dr for dr, _ in offsets}) < 2 or len({dc for _, dc in offsets}) < 2:
            errors.append("cloud must span both row and column directions")
        if len(set(_rotation_forms(offsets))) < 4:
            errors.append("cloud must be asymmetric under quarter-turn rotations")

    if not 3 <= len(anchors) <= 4:
        errors.append(f"expected three or four anchors, got {len(anchors)}")
    anchor_colors = [color for _, _, color in anchors]
    if len(anchor_colors) != len(set(anchor_colors)):
        errors.append("anchor colors must be pairwise distinct")

    for anchor in anchors:
        stamp = _stamp_cells(anchor, offsets)
        outside = sorted(
            (row, col)
            for row, col in stamp
            if not (0 <= row < height and 0 <= col < width)
        )
        if outside:
            errors.append(
                f"anchor {anchor} would stamp {len(outside)} cloud cells out of bounds"
            )

    if not errors:
        try:
            if rule_mirror(grid) == [list(row) for row in grid]:
                errors.append("lesson must visibly change under the keyed-offset rule")
        except ValueError as exc:
            errors.append(str(exc))

    overrides = (meta or {}).get("overrides", {}) if isinstance(meta, dict) else {}
    if overrides and not errors:
        unknown = sorted(set(overrides) - set(AXES))
        if unknown:
            errors.append(f"unknown override(s): {unknown}")
        requested = overrides.get("scene_profile")
        if requested is not None:
            observed = scene_observables(grid)["scene_profile"]
            if observed != requested:
                errors.append(
                    f"requested scene_profile {requested!r}, observed {observed!r}"
                )
    return errors


def observe_overrides(grid) -> dict[str, str]:
    errors = self_check(grid)
    if errors:
        raise ValueError("cannot observe invalid scene: " + "; ".join(errors))
    profile = scene_observables(grid)["scene_profile"]
    return {"scene_profile": profile}


def canonical_profile_signature(grid):
    """Strict linked empirical-manifold signature, including relative layout."""
    if self_check(grid):
        return None
    signature = _normalized_cells(len(grid), len(grid[0]), _foreground_cells(grid))
    return signature if signature in _CANONICAL_SIGNATURES else None


def is_canonical_profile(grid) -> bool:
    return canonical_profile_signature(grid) is not None


def strict_canonical_like(grid) -> bool:
    """Expose the existing exact linked predicate to the shared semantic gate."""
    return is_canonical_profile(grid)


def rule_mirror(grid):
    """Exact Python test mirror; the Racket program remains output authority."""
    basic_errors, height, width = _validate_grid(grid)
    if basic_errors:
        raise ValueError("; ".join(basic_errors))
    references, _, offsets, anchors = _cloud_and_anchors(grid)
    if len(references) != 1:
        raise ValueError("rule requires exactly one color-9 reference")

    output = full_grid(height, width, 0)
    # grid-cells is row-major, so preserve the Racket rule's anchor-overwrite
    # ordering before max-merging each anchor's rotated paint cloud.
    for row, col, color in sorted(anchors):
        output[row][col] = color
        paint = _paint_color(color)
        for dr, dc in offsets:
            rotated_row, rotated_col = _rotate_offset(color, dr, dc)
            rr, cc = row + rotated_row, col + rotated_col
            if 0 <= rr < height and 0 <= cc < width:
                output[rr][cc] = max(output[rr][cc], paint)
    return output


def _translated_grid(spec: SceneSpec, rng) -> list[list[int]]:
    reference = next((row, col) for row, col, color in spec.cells if color == 9)
    offsets = tuple(
        (row - reference[0], col - reference[1])
        for row, col, color in spec.cells
        if color == 8
    )
    anchors = tuple(
        (row, col, color)
        for row, col, color in spec.cells
        if color in (2, 3, 4, 5)
    )
    # A legal translation must keep both the visible input and every output
    # stamp in bounds.  Using only the input bbox silently breaks canonical
    # scenes whose rotated cloud extends beyond their anchor positions.
    footprint = {(row, col) for row, col, _ in spec.cells}
    for anchor in anchors:
        footprint.update(_stamp_cells(anchor, offsets))
    min_row = min(row for row, _ in footprint)
    max_row = max(row for row, _ in footprint)
    min_col = min(col for _, col in footprint)
    max_col = max(col for _, col in footprint)
    row_shifts = range(-min_row, spec.height - max_row)
    col_shifts = range(-min_col, spec.width - max_col)
    if spec.allow_translation:
        row_shift = rng.choice(tuple(row_shifts))
        col_shift = rng.choice(tuple(col_shifts))
    else:
        row_shift = 0
        col_shift = 0

    grid = full_grid(spec.height, spec.width, 0)
    for row, col, color in spec.cells:
        rr, cc = row + row_shift, col + col_shift
        if grid[rr][cc] != 0:
            raise RuntimeError(f"scene profile contains overlapping input cells at {rr},{cc}")
        grid[rr][cc] = color
    return grid


def _random_offsets(rng) -> tuple[tuple[int, int], ...]:
    """Grow a rooted 5/6-cell polyomino; keep the existing lesson grammar.

    Sorted frontiers make replay independent of hash randomization.  Rejection
    is bounded and visible: never silently fall back to a fixed witness.
    """
    count = rng.choice((4, 5))
    for _attempt in range(128):
        cells = {(0, 0)}
        while len(cells) < count + 1:
            frontier = sorted({
                (r + dr, c + dc)
                for r, c in cells
                for dr, dc in ((-1, 0), (0, -1), (0, 1), (1, 0))
                if -3 <= r + dr <= 3 and -3 <= c + dc <= 3
                and (r + dr, c + dc) not in cells
            })
            cells.add(rng.choice(frontier))
        offsets = tuple(sorted(cells - {(0, 0)}))
        if (len({r for r, _ in offsets}) >= 2
                and len({c for _, c in offsets}) >= 2
                and len(set(_rotation_forms(offsets))) == 4):
            return offsets
    raise RuntimeError("procedural cloud rejection budget exhausted (128 attempts)")


def _legal_centres(height, width, offsets):
    """Every centre whose origin AND complete stamp fit; no clipping."""
    rows = [0, *(r for r, _ in offsets)]
    cols = [0, *(c for _, c in offsets)]
    return [(r, c)
            for r in range(-min(rows), height - max(rows))
            for c in range(-min(cols), width - max(cols))]


def _procedural_grid(rng) -> list[list[int]]:
    height, width = rng.randint(8, 16), rng.randint(8, 16)
    offsets = _random_offsets(rng)
    rr, rc = rng.choice(_legal_centres(height, width, offsets))
    grid = full_grid(height, width, 0)
    grid[rr][rc] = 9
    for dr, dc in offsets:
        grid[rr + dr][rc + dc] = 8
    # Source and anchors cannot occupy the same input cell.  Paint overlap,
    # adjacency and all row-major overwrite orders are otherwise allowed.
    colors = rng.sample((2, 3, 4, 5), rng.choice((3, 4)))
    for color in colors:
        rotated = tuple(_rotate_offset(color, dr, dc) for dr, dc in offsets)
        candidates = [(r, c) for r, c in _legal_centres(height, width, rotated)
                      if grid[r][c] == 0]
        if not candidates:
            raise RuntimeError("procedural anchor placement has no legal centre")
        r, c = rng.choice(candidates)
        grid[r][c] = color
    # Fixed witnesses have priority in the observable classifier.  Never claim
    # the procedural override was honored if a rare draw hits one exactly.
    signature = _normalized_cells(height, width, _foreground_cells(grid))
    if signature in _SIGNATURE_TO_PROFILE:
        raise RuntimeError("procedural draw unexpectedly matched a fixed witness")
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    band = _band(difficulty)
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    requested = overrides.get("scene_profile")
    if requested is not None and requested not in SCENE_PROFILES:
        raise ValueError(f"unknown scene_profile: {requested!r}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = ctx.draw_choice("scene_profile", _PROFILE_POOLS[band])
    if profile == "procedural":
        grid = _procedural_grid(ctx.draw_rng("procedural_scene"))
    else:
        grid = _translated_grid(_SCENES[profile], ctx.draw_rng(f"translation|{profile}"))

    errors = self_check(grid)
    if errors:
        raise AssertionError("generated invalid keyed-offset scene: " + "; ".join(errors))
    observed = observe_overrides(grid)
    if observed != {"scene_profile": profile}:
        raise AssertionError(f"profile construction mismatch: {profile!r} -> {observed!r}")
    return grid
