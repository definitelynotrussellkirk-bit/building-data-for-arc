"""Generator for ARC task a5192bbc9e88: crop and stack a vertical mirror.

The input contains one padded, single-color, 4-connected object.  The Racket
rule crops that object to its tight bounding box, places the crop on top, and
places a top-to-bottom reflection directly underneath.

Version 3 replaces three mutually constrained numeric axes with one exact,
observable scene-profile axis.  Its four-phase schedule deliberately includes
vertical-symmetric, horizontal-symmetric, 180-degree-symmetric, and fully
asymmetric crops, so each four-demo lesson refutes crop-only, duplicate-crop,
horizontal-mirror, and uncropped-stack shortcuts while still accepting every
canonical input (including the two vertically symmetric canonical objects).
"""
from __future__ import annotations

from collections import deque
from typing import Callable, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "a5192bbc9e88"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "ecd28f55224a"

SUMMARY = (
    "Crop the unique padded nonzero object to its tight bounding box. Output "
    "the crop followed immediately by the same crop reflected top-to-bottom, "
    "so the output height is twice the crop height and the output width equals "
    "the crop width."
)

INVARIANTS = [
    "background is literal color 0",
    "exactly one nonzero color forms one 4-connected object",
    "the object's tight bbox has at least one zero row/column of outer padding",
    "the crop spans at least two rows and two columns and contains at least three cells",
    "the canvas profile determines an observable crop-symmetry branch",
]

EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0

# The order is semantic: every four consecutive sample indexes contain one
# profile from each symmetry class (vertical, horizontal, 180-degree, neither).
# That remains true across the cyclic boundary and for every lesson start.
SCENE_SPECS: dict[str, tuple[int, int, str]] = {
    "canonical_6x8_vertical": (6, 8, "vertical"),
    "canonical_7x7_horizontal": (7, 7, "horizontal"),
    "canonical_6x9_rot180": (6, 9, "rot180"),
    "medium_8x10_asymmetric": (8, 10, "asymmetric"),
    "canonical_7x8_vertical": (7, 8, "vertical"),
    "compact_5x7_horizontal": (5, 7, "horizontal"),
    "medium_8x9_rot180": (8, 9, "rot180"),
    "medium_9x11_asymmetric": (9, 11, "asymmetric"),
    "large_10x12_vertical": (10, 12, "vertical"),
    "large_11x10_horizontal": (11, 10, "horizontal"),
    "large_12x14_rot180": (12, 14, "rot180"),
    "large_14x13_asymmetric": (14, 13, "asymmetric"),
}
SCENE_PROFILES = (
    "canonical_6x8_vertical",
    "canonical_7x7_horizontal",
    "canonical_6x9_rot180",
    "medium_8x10_asymmetric",
    "canonical_7x8_vertical",
    "compact_5x7_horizontal",
    "medium_8x9_rot180",
    "medium_9x11_asymmetric",
    "large_10x12_vertical",
    "large_11x10_horizontal",
    "large_12x14_rot180",
    "large_14x13_asymmetric",
)
SCHEDULE_PROFILES = SCENE_PROFILES
CANONICAL_SCENE_PROFILES = frozenset(
    {
        "canonical_6x8_vertical",
        "canonical_7x7_horizontal",
        "canonical_6x9_rot180",
        "canonical_7x8_vertical",
    }
)

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "deterministic twelve-profile sample-index cycle",
        "valid": "|".join(SCENE_PROFILES),
    }
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[()] = ()

# Binary crops.  Rotations/reflections are generated at runtime and filtered by
# their exact symmetry class, giving shape variation without ever changing the
# declared scene profile.
_VERTICAL_TEMPLATES = (
    ((1, 0), (1, 1), (1, 0)),
    ((1, 1, 0), (0, 1, 0), (1, 1, 0)),
    ((0, 1, 0), (1, 1, 0), (0, 1, 0)),
    ((1, 0, 0), (1, 1, 0), (0, 1, 0), (1, 1, 0), (1, 0, 0)),
)
_ROT180_TEMPLATES = (
    ((1, 1, 0), (0, 1, 1)),
    ((1, 1, 0), (0, 1, 0), (0, 1, 1)),
    ((1, 0, 0), (1, 1, 0), (0, 1, 1), (0, 0, 1)),
)
_ASYMMETRIC_TEMPLATES = (
    ((1, 0), (1, 0), (1, 1)),
    ((1, 1, 1), (1, 0, 0)),
    ((1, 0, 0), (1, 1, 0), (0, 1, 1)),
    ((1, 1, 0), (1, 1, 0), (0, 1, 1)),
)


def _copy_grid(grid: Iterable[Iterable[int]]) -> list[list[int]]:
    return [list(row) for row in grid]


def _flip_ud(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in reversed(grid)]


def _flip_lr(grid: list[list[int]]) -> list[list[int]]:
    return [list(reversed(row)) for row in grid]


def _rotate_cw(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid[::-1])]


def _rotate_180(grid: list[list[int]]) -> list[list[int]]:
    return _flip_lr(_flip_ud(grid))


def _dihedral_views(template: Iterable[Iterable[int]]) -> list[list[list[int]]]:
    base = _copy_grid(template)
    views: list[list[list[int]]] = []
    current = base
    for _ in range(4):
        for candidate in (current, _flip_lr(current)):
            if candidate not in views:
                views.append(candidate)
        current = _rotate_cw(current)
    return views


def _symmetry_class(crop: list[list[int]]) -> str:
    vertical = crop == _flip_ud(crop)
    horizontal = crop == _flip_lr(crop)
    rot180 = crop == _rotate_180(crop)
    if vertical and not horizontal:
        return "vertical"
    if horizontal and not vertical:
        return "horizontal"
    if rot180 and not vertical and not horizontal:
        return "rot180"
    if not vertical and not horizontal and not rot180:
        return "asymmetric"
    return "over_symmetric"


def _templates_for(symmetry: str) -> tuple[tuple[tuple[int, ...], ...], ...]:
    if symmetry == "vertical":
        return _VERTICAL_TEMPLATES
    if symmetry == "horizontal":
        return tuple(tuple(zip(*template)) for template in _VERTICAL_TEMPLATES)
    if symmetry == "rot180":
        return _ROT180_TEMPLATES
    if symmetry == "asymmetric":
        return _ASYMMETRIC_TEMPLATES
    raise ValueError(f"unknown symmetry class {symmetry!r}")


def _candidate_crops(symmetry: str, max_h: int, max_w: int) -> list[list[list[int]]]:
    candidates: list[list[list[int]]] = []
    for template in _templates_for(symmetry):
        for crop in _dihedral_views(template):
            if len(crop) <= max_h and len(crop[0]) <= max_w:
                if _symmetry_class(crop) == symmetry and crop not in candidates:
                    candidates.append(crop)
    if not candidates:
        raise ValueError(
            f"no {symmetry} crop fits interior {max_h}x{max_w}"
        )
    return candidates


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Return the deterministic profile used for an ordinary draw."""
    del seed
    band_offset = {"easy": 0, "medium": 4, "hard": 8}.get(difficulty, 0)
    return SCENE_PROFILES[(int(sample_index) + band_offset) % len(SCENE_PROFILES)]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    if "scene_profile" in overrides:
        profile = ctx.draw_choice("scene_profile", SCENE_PROFILES)
    else:
        profile = ctx.draw_choice(
            "scene_profile",
            (schedule_profile(seed, sample_index, difficulty),),
        )

    height, width, symmetry = SCENE_SPECS[profile]
    shape_rng = ctx.draw_rng("shape")
    crops = _candidate_crops(symmetry, height - 2, width - 2)
    crop = _copy_grid(shape_rng.choice(crops))
    crop_h, crop_w = len(crop), len(crop[0])

    top = shape_rng.randint(1, height - crop_h - 1)
    left = shape_rng.randint(1, width - crop_w - 1)
    color = shape_rng.choice(tuple(range(1, 10)))
    grid = full_grid(height, width, 0)
    for row in range(crop_h):
        for col in range(crop_w):
            if crop[row][col]:
                grid[top + row][left + col] = color
    return grid


def _grid_errors(grid) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if len(grid) > 30 or width > 30:
        return ["grid dimensions must not exceed 30"]
    for row in grid:
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return ["cells must be literal ARC integers 0..9"]
    return []


def _nonzero_cells(grid) -> list[tuple[int, int]]:
    return [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 0
    ]


def _crop_nonzero(grid) -> list[list[int]]:
    cells = _nonzero_cells(grid)
    if not cells:
        return []
    top = min(row for row, _ in cells)
    bottom = max(row for row, _ in cells)
    left = min(col for _, col in cells)
    right = max(col for _, col in cells)
    return [list(row[left : right + 1]) for row in grid[top : bottom + 1]]


def _is_connected(cells: Iterable[tuple[int, int]]) -> bool:
    occupied = set(cells)
    if not occupied:
        return False
    queue = deque([next(iter(occupied))])
    seen: set[tuple[int, int]] = set()
    while queue:
        row, col = queue.popleft()
        if (row, col) in seen:
            continue
        seen.add((row, col))
        for neighbor in (
            (row - 1, col),
            (row + 1, col),
            (row, col - 1),
            (row, col + 1),
        ):
            if neighbor in occupied and neighbor not in seen:
                queue.append(neighbor)
    return seen == occupied


def _profile_for_dimensions(height: int, width: int) -> str | None:
    matches = [
        name
        for name, (profile_h, profile_w, _symmetry) in SCENE_SPECS.items()
        if (profile_h, profile_w) == (height, width)
    ]
    return matches[0] if len(matches) == 1 else None


def _analyze(grid) -> tuple[dict, list[str]]:
    errors = _grid_errors(grid)
    if errors:
        return {}, errors

    height, width = len(grid), len(grid[0])
    profile = _profile_for_dimensions(height, width)
    if profile is None:
        errors.append(
            f"canvas {height}x{width} is not one of the declared scene profiles"
        )

    cells = _nonzero_cells(grid)
    if not cells:
        errors.append("expected one nonzero object, found none")
        return {"scene_profile": profile}, errors

    colors = {grid[row][col] for row, col in cells}
    if len(colors) != 1:
        errors.append(f"expected one object color, found {sorted(colors)}")
    if not _is_connected(cells):
        errors.append("nonzero cells must form one 4-connected object")

    top = min(row for row, _ in cells)
    bottom = max(row for row, _ in cells)
    left = min(col for _, col in cells)
    right = max(col for _, col in cells)
    if top == 0 or left == 0 or bottom == height - 1 or right == width - 1:
        errors.append("nonzero bbox must leave at least one zero-cell outer margin")

    crop = _crop_nonzero(grid)
    crop_h = len(crop)
    crop_w = len(crop[0]) if crop else 0
    if crop_h < 2 or crop_w < 2:
        errors.append(f"crop must span at least 2x2, got {crop_h}x{crop_w}")
    if len(cells) < 3:
        errors.append(f"object must contain at least three cells, got {len(cells)}")

    symmetry = _symmetry_class(crop) if crop else None
    if profile is not None:
        expected_symmetry = SCENE_SPECS[profile][2]
        if symmetry != expected_symmetry:
            errors.append(
                f"profile {profile!r} requires {expected_symmetry} crop symmetry, "
                f"observed {symmetry}"
            )

    facts = {
        "scene_profile": profile,
        "height": height,
        "width": width,
        "object_color": next(iter(colors)) if len(colors) == 1 else None,
        "cell_count": len(cells),
        "crop": crop,
        "crop_h": crop_h,
        "crop_w": crop_w,
        "symmetry": symmetry,
    }
    return facts, errors


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed, ambiguous, or profile-drifting teaching scenes."""
    del difficulty
    facts, errors = _analyze(grid)
    requested = None
    if isinstance(meta, dict):
        nested = meta.get("overrides")
        if isinstance(nested, dict):
            requested = nested.get("scene_profile")
        if requested is None:
            requested = meta.get("scene_profile")
    if requested is not None and facts.get("scene_profile") != requested:
        errors.append(
            f"scene_profile override requested {requested!r}, observed "
            f"{facts.get('scene_profile')!r}"
        )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """The declared distribution is the task's exact padded-object grammar."""
    return list(self_check(grid))


def observe_overrides(grid) -> dict[str, str]:
    facts, errors = _analyze(grid)
    if errors:
        raise ValueError("; ".join(errors))
    profile = facts.get("scene_profile")
    assert isinstance(profile, str)
    return {"scene_profile": profile}


def canonical_profile_signature(grid) -> str | None:
    profile = observe_overrides(grid).get("scene_profile")
    return profile if profile in CANONICAL_SCENE_PROFILES else None


def rule_mirror(grid) -> list[list[int]]:
    """Independent Python mirror for focused tests; Racket remains authority."""
    crop = _crop_nonzero(grid)
    if not crop:
        raise ValueError("cannot apply rule to an empty object")
    return _copy_grid(crop) + _flip_ud(crop)


def rival_duplicate_crop(grid) -> list[list[int]]:
    crop = _crop_nonzero(grid)
    return _copy_grid(crop) + _copy_grid(crop)


def rival_horizontal_mirror_stack(grid) -> list[list[int]]:
    crop = _crop_nonzero(grid)
    return _copy_grid(crop) + _flip_lr(crop)


def rival_uncropped_vertical_stack(grid) -> list[list[int]]:
    return _copy_grid(grid) + _flip_ud(_copy_grid(grid))


def rival_crop_only(grid) -> list[list[int]]:
    return _crop_nonzero(grid)


def _has_symmetry(grid, expected: str) -> bool:
    facts, errors = _analyze(grid)
    return not errors and facts.get("symmetry") == expected


SEMANTIC_WITNESSES: dict[str, Callable[[list[list[int]]], bool]] = {
    "vertical_symmetric_crop": lambda grid: _has_symmetry(grid, "vertical"),
    "horizontal_symmetric_crop": lambda grid: _has_symmetry(grid, "horizontal"),
    "rot180_only_crop": lambda grid: _has_symmetry(grid, "rot180"),
    "fully_asymmetric_crop": lambda grid: _has_symmetry(grid, "asymmetric"),
}

SEMANTIC_RIVALS = {
    "duplicate_crop": rival_duplicate_crop,
    "horizontal_mirror_stack": rival_horizontal_mirror_stack,
    "uncropped_vertical_stack": rival_uncropped_vertical_stack,
    "crop_only": rival_crop_only,
}

WITNESS_RIVALS = {
    "vertical_symmetric_crop": ["horizontal_mirror_stack"],
    "horizontal_symmetric_crop": ["duplicate_crop"],
    "rot180_only_crop": ["duplicate_crop"],
    "fully_asymmetric_crop": ["duplicate_crop", "horizontal_mirror_stack"],
}

LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "duplicate_crop": rival_duplicate_crop,
    "horizontal_mirror_stack": rival_horizontal_mirror_stack,
    "uncropped_vertical_stack": rival_uncropped_vertical_stack,
    "crop_only": rival_crop_only,
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons where a named plausible rival survives the demos."""
    errors: list[str] = []
    query_output = query.get("output") if isinstance(query, dict) else None
    if query_output is None:
        return ["query is missing its authoritative output"]
    for name, competitor in LESSON_COMPETITORS.items():
        survives = True
        for demo in demos:
            if competitor(demo["input"]) != demo["output"]:
                survives = False
                break
        if survives and competitor(query["input"]) != query_output:
            errors.append(
                f"competitor {name!r} fits every demonstration but changes the query answer"
            )
    return errors


# Import-time assertions keep the handwritten profile/template inventory honest.
if tuple(SCENE_SPECS) != SCENE_PROFILES:
    raise AssertionError("SCENE_PROFILES order must match SCENE_SPECS")
for _profile_name, (_height, _width, _symmetry) in SCENE_SPECS.items():
    if not _candidate_crops(_symmetry, _height - 2, _width - 2):
        raise AssertionError(f"profile {_profile_name} has no fitting crop")
