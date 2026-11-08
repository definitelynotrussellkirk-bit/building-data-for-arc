"""Semantic generator for ARC task ``dcb4d769d19d``.

Every red(2) 4-connected component of size one blooms into a yellow(4)
cardinal cross.  Larger red components and all non-red distractors are copied
unchanged.  The scheduled profiles deliberately mirror the canonical scale,
palette size, target counts, and component-count envelope while varying the
actual geometry deterministically by seed.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Any, Callable, Iterable, Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "dcb4d769d19d"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "05d00f5c5804"

SUMMARY = (
    "Find every singleton red(2) component. Replace its center and four "
    "cardinal neighbors with yellow(4), while preserving larger red "
    "components and all differently colored distractor objects."
)

INVARIANTS = [
    "background is color 0 and yellow 4 is absent from the input",
    "the input uses red 2 plus exactly two non-red distractor colors",
    "there are two or four interior singleton red target components",
    "every target is interior and target crosses do not overlap",
    "at least two larger red components remain visible as negative examples",
    "the scheduled curriculum includes non-red singleton and occupied-arm witnesses",
]

EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0

# A single categorical axis is intentional.  Each value names a complete,
# recoverable scene signature rather than exposing independent knobs whose
# Cartesian product would include impossible or semantically weak lessons.
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "four-profile deterministic curriculum per difficulty band",
        "valid": (
            "easy_canon_two_a|easy_canon_two_b|easy_canon_four_a|easy_canon_four_b|"
            "medium_dense_four|medium_mixed_two|medium_mixed_four|medium_sparse_two|"
            "hard_dense_four|hard_varied_two|hard_varied_four|hard_dense_two"
        ),
    }
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()

# (band, height, width, singleton_count, non-singleton red sizes,
#  ((distractor color, component sizes), ...)).  These signatures are unique,
# so ``observe_overrides`` can recover the exact selected profile from the
# returned grid without hidden metadata.
_PROFILE_ROWS = (
    (
        "easy_canon_two_a", "easy", 11, 12, 2, (2, 2, 3, 4),
        ((5, (1,)), (7, (1,))),
    ),
    (
        "easy_canon_two_b", "easy", 11, 11, 2, (2, 3, 3, 4),
        ((8, (3,)), (9, (3,))),
    ),
    (
        "easy_canon_four_a", "easy", 12, 12, 4, (3, 4),
        ((7, (1,)), (8, (3,))),
    ),
    (
        "easy_canon_four_b", "easy", 11, 11, 4, (4, 7),
        ((6, (2, 3)), (8, (3,))),
    ),
    (
        "medium_dense_four", "medium", 11, 12, 4, (4, 4, 4, 4),
        ((6, (3, 4)), (7, (1,))),
    ),
    (
        "medium_mixed_two", "medium", 11, 12, 2, (2, 3, 4, 5),
        ((6, (1, 2)), (9, (3,))),
    ),
    (
        "medium_mixed_four", "medium", 12, 12, 4, (2, 4, 5),
        ((5, (1,)), (8, (2, 3))),
    ),
    (
        "medium_sparse_two", "medium", 11, 11, 2, (3, 4, 6),
        ((7, (1, 2)), (9, (4,))),
    ),
    (
        "hard_dense_four", "hard", 11, 12, 4, (2, 3, 4, 5),
        ((5, (1,)), (8, (2, 4))),
    ),
    (
        "hard_varied_two", "hard", 12, 12, 2, (2, 2, 4, 7),
        ((6, (1, 3)), (9, (2,))),
    ),
    (
        "hard_varied_four", "hard", 11, 11, 4, (3, 3, 4),
        ((5, (1,)), (7, (2, 3))),
    ),
    (
        "hard_dense_two", "hard", 12, 12, 2, (2, 3, 5, 6),
        ((8, (1, 2)), (9, (3,))),
    ),
)

SCENE_PROFILES = tuple(row[0] for row in _PROFILE_ROWS)
SCHEDULE_PROFILES = SCENE_PROFILES
_PROFILE_BY_NAME = {
    name: {
        "band": band,
        "height": height,
        "width": width,
        "singletons": singletons,
        "red_sizes": tuple(red_sizes),
        "distractors": tuple((color, tuple(sizes)) for color, sizes in distractors),
    }
    for name, band, height, width, singletons, red_sizes, distractors in _PROFILE_ROWS
}
_PROFILES_BY_BAND = {
    band: tuple(row[0] for row in _PROFILE_ROWS if row[1] == band)
    for band in ("easy", "medium", "hard")
}
_DIRS4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
_CANONICAL_DIMS = {(11, 11), (11, 12), (12, 12)}


def _band(difficulty: Any) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return str(difficulty)
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> str:
    """Cycle through all four branch-complete profiles in the chosen band."""
    del seed
    profiles = _PROFILES_BY_BAND[_band(difficulty)]
    return profiles[int(sample_index) % len(profiles)]


def _validate_grid(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return [f"cell ({r},{c}) must be an ARC integer color 0..9"]
    return []


def _components_by_color(grid: Sequence[Sequence[int]]) -> dict[int, list[tuple[tuple[int, int], ...]]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: dict[int, list[tuple[tuple[int, int], ...]]] = defaultdict(list)
    for r in range(height):
        for c in range(width):
            color = int(grid[r][c])
            if color == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells: list[tuple[int, int]] = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in _DIRS4:
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            result[color].append(tuple(sorted(cells)))
    for color in result:
        result[color].sort(key=lambda cells: (len(cells), cells))
    return dict(result)


def _scene_signature(grid: Sequence[Sequence[int]]) -> tuple[Any, ...]:
    components = _components_by_color(grid)
    red = components.get(2, [])
    distractors = tuple(
        (color, tuple(sorted(len(component) for component in groups)))
        for color, groups in sorted(components.items())
        if color != 2
    )
    return (
        len(grid),
        len(grid[0]),
        sum(len(component) == 1 for component in red),
        tuple(sorted(len(component) for component in red if len(component) > 1)),
        distractors,
    )


def _profile_signature(profile: dict[str, Any]) -> tuple[Any, ...]:
    return (
        profile["height"],
        profile["width"],
        profile["singletons"],
        tuple(sorted(profile["red_sizes"])),
        tuple(
            (color, tuple(sorted(sizes)))
            for color, sizes in sorted(profile["distractors"])
        ),
    )


_PROFILE_BY_SIGNATURE = {
    _profile_signature(profile): name for name, profile in _PROFILE_BY_NAME.items()
}
if len(_PROFILE_BY_SIGNATURE) != len(_PROFILE_BY_NAME):
    raise RuntimeError("scene profile signatures must be unique")


def observe_overrides(grid) -> dict[str, str | None]:
    """Recover the exact public axis value from the returned grid."""
    if _validate_grid(grid):
        return {"scene_profile": None}
    return {"scene_profile": _PROFILE_BY_SIGNATURE.get(_scene_signature(grid))}


def _normalize_shape(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    points = tuple(cells)
    min_r = min(r for r, _ in points)
    min_c = min(c for _, c in points)
    return tuple(sorted((r - min_r, c - min_c) for r, c in points))


def _random_polyomino(size: int, rng) -> tuple[tuple[int, int], ...]:
    cells = {(0, 0)}
    while len(cells) < size:
        boundary = sorted({
            (r + dr, c + dc)
            for r, c in cells
            for dr, dc in _DIRS4
            if (r + dr, c + dc) not in cells
        })
        cells.add(rng.choice(boundary))
    shape = _normalize_shape(cells)
    # Random D4 transform increases geometry diversity without changing the
    # profile signature or semantic rule.
    turns = rng.randrange(4)
    reflect = bool(rng.randrange(2))
    transformed = []
    for r, c in shape:
        x, y = r, -c if reflect else c
        for _ in range(turns):
            x, y = y, -x
        transformed.append((x, y))
    return _normalize_shape(transformed)


def _cross(center: tuple[int, int]) -> set[tuple[int, int]]:
    r, c = center
    return {(r, c), (r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)}


def _render_profile(profile: dict[str, Any], rng) -> list[list[int]]:
    height, width = profile["height"], profile["width"]

    # Place the multi-cell scene first, then choose target cells.  This mirrors
    # canonical examples where a yellow cross can overwrite a differently
    # colored neighbor while still guaranteeing that the red center is a true
    # size-one component.
    for _scene_attempt in range(300):
        grid = full_grid(height, width, 0)
        components: list[tuple[int, int]] = [
            (2, size) for size in sorted(profile["red_sizes"], reverse=True)
        ]
        for color, sizes in profile["distractors"]:
            components.extend((color, size) for size in sorted(sizes, reverse=True))
        components.sort(key=lambda item: (-item[1], item[0]))

        placement_failed = False
        for color, size in components:
            placed = False
            for _component_attempt in range(1200):
                shape = _random_polyomino(size, rng)
                shape_h = max(r for r, _ in shape) + 1
                shape_w = max(c for _, c in shape) + 1
                if shape_h > height or shape_w > width:
                    continue
                origin_r = rng.randrange(height - shape_h + 1)
                origin_c = rng.randrange(width - shape_w + 1)
                cells = {(origin_r + r, origin_c + c) for r, c in shape}
                if any(grid[r][c] != 0 for r, c in cells):
                    continue
                if any(
                    0 <= r + dr < height
                    and 0 <= c + dc < width
                    and grid[r + dr][c + dc] == color
                    for r, c in cells
                    for dr, dc in _DIRS4
                    if (r + dr, c + dc) not in cells
                ):
                    continue
                for r, c in cells:
                    grid[r][c] = color
                placed = True
                break
            if not placed:
                placement_failed = True
                break
        if placement_failed:
            continue

        candidates = []
        overwrite_candidates = []
        for r in range(1, height - 1):
            for c in range(1, width - 1):
                if grid[r][c] != 0:
                    continue
                if any(grid[r + dr][c + dc] == 2 for dr, dc in _DIRS4):
                    continue
                candidates.append((r, c))
                if any(grid[r + dr][c + dc] not in (0, 2) for dr, dc in _DIRS4):
                    overwrite_candidates.append((r, c))
        rng.shuffle(candidates)
        rng.shuffle(overwrite_candidates)
        if not overwrite_candidates:
            continue

        chosen = [overwrite_candidates[0]]
        occupied_crosses = _cross(chosen[0])
        for center in candidates:
            if center in chosen or _cross(center) & occupied_crosses:
                continue
            chosen.append(center)
            occupied_crosses.update(_cross(center))
            if len(chosen) == profile["singletons"]:
                break
        if len(chosen) != profile["singletons"]:
            continue
        for r, c in chosen:
            grid[r][c] = 2
        if not self_check(grid):
            return grid
    raise RuntimeError("failed to place a lawful singleton-cross scene")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")
    band = _band(difficulty)
    requested = overrides.get("scene_profile")
    if requested is not None and requested not in _PROFILE_BY_NAME:
        raise ValueError(f"unknown scene_profile: {requested!r}")
    selected = requested or schedule_profile(seed, sample_index, band)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    profile_name = ctx.draw_choice("scene_profile", [selected])
    return _render_profile(_PROFILE_BY_NAME[profile_name], ctx.draw_rng("placement"))


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed, answer-leaking, or shortcut-hiding inputs."""
    del difficulty, meta
    errors = _validate_grid(grid)
    if errors:
        return errors
    height, width = len(grid), len(grid[0])
    if (height, width) not in _CANONICAL_DIMS:
        errors.append(f"dimensions {height}x{width} are outside the canonical envelope")

    colors = sorted({value for row in grid for value in row})
    if 0 not in colors or 2 not in colors:
        errors.append("input must contain background 0 and red target color 2")
    if 4 in colors:
        errors.append("yellow 4 must be absent from the input to prevent answer leakage")
    if len(colors) != 4:
        errors.append(f"input must use exactly four colors, found {colors}")
    distractor_colors = [color for color in colors if color not in (0, 2)]
    if len(distractor_colors) != 2:
        errors.append(f"expected exactly two non-red distractor colors, found {distractor_colors}")
    if sum(value == 0 for row in grid for value in row) * 2 <= height * width:
        errors.append("background 0 must occupy a strict majority of the grid")

    components = _components_by_color(grid)
    red_components = components.get(2, [])
    singletons = [component[0] for component in red_components if len(component) == 1]
    larger = [component for component in red_components if len(component) > 1]
    if len(singletons) not in (2, 4):
        errors.append(f"expected two or four singleton red targets, found {len(singletons)}")
    if len(larger) < 2:
        errors.append(f"need at least two larger red distractor components, found {len(larger)}")
    if any(len(component) > 7 for component in larger):
        errors.append("larger red component size must stay within canonical maximum 7")

    occupied_crosses: set[tuple[int, int]] = set()
    for r, c in singletons:
        if r in (0, height - 1) or c in (0, width - 1):
            errors.append(f"singleton red target {(r, c)} must be interior")
            continue
        cells = _cross((r, c))
        if occupied_crosses & cells:
            errors.append("singleton target crosses overlap")
        occupied_crosses.update(cells)
    nonred_components = [
        component
        for color, groups in components.items()
        if color != 2
        for component in groups
    ]
    if not nonred_components:
        errors.append("need non-red distractor objects")
    object_count = sum(len(groups) for groups in components.values())
    if not 8 <= object_count <= 12:
        errors.append(f"object count {object_count} is outside canonical-like range 8..12")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """All ordinary draws are intentionally canonical-scale lessons."""
    return self_check(grid)


def rule_mirror(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    """Independent Python mirror used only for tests and semantic rivals."""
    output = [list(row) for row in grid]
    components = _components_by_color(grid)
    for component in components.get(2, []):
        if len(component) != 1:
            continue
        r, c = component[0]
        for rr, cc in _cross((r, c)):
            if 0 <= rr < len(output) and 0 <= cc < len(output[0]):
                output[rr][cc] = 4
    return output


def _rival_centers_only(grid):
    output = [list(row) for row in grid]
    for component in _components_by_color(grid).get(2, []):
        if len(component) == 1:
            r, c = component[0]
            output[r][c] = 4
    return output


def _rival_arms_only(grid):
    output = [list(row) for row in grid]
    for component in _components_by_color(grid).get(2, []):
        if len(component) == 1:
            r, c = component[0]
            for rr, cc in _cross((r, c)) - {(r, c)}:
                if 0 <= rr < len(output) and 0 <= cc < len(output[0]):
                    output[rr][cc] = 4
    return output


def _rival_expand_all_red_cells(grid):
    output = [list(row) for row in grid]
    red_cells = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 2
    ]
    for r, c in red_cells:
        for rr, cc in _cross((r, c)):
            if 0 <= rr < len(output) and 0 <= cc < len(output[0]):
                output[rr][cc] = 4
    return output


def _rival_expand_all_singletons(grid):
    output = [list(row) for row in grid]
    for groups in _components_by_color(grid).values():
        for component in groups:
            if len(component) != 1:
                continue
            r, c = component[0]
            for rr, cc in _cross((r, c)):
                if 0 <= rr < len(output) and 0 <= cc < len(output[0]):
                    output[rr][cc] = 4
    return output


def _rival_preserve_nonzero_cross_arms(grid):
    output = [list(row) for row in grid]
    for component in _components_by_color(grid).get(2, []):
        if len(component) != 1:
            continue
        r, c = component[0]
        output[r][c] = 4
        for rr, cc in _cross((r, c)) - {(r, c)}:
            if 0 <= rr < len(output) and 0 <= cc < len(output[0]) and grid[rr][cc] == 0:
                output[rr][cc] = 4
    return output


def _rival_first_two_targets(grid):
    output = [list(row) for row in grid]
    targets = sorted(
        component[0]
        for component in _components_by_color(grid).get(2, [])
        if len(component) == 1
    )
    for r, c in targets[:2]:
        for rr, cc in _cross((r, c)):
            if 0 <= rr < len(output) and 0 <= cc < len(output[0]):
                output[rr][cc] = 4
    return output


def _rival_four_target_scenes_only(grid):
    targets = [
        component
        for component in _components_by_color(grid).get(2, [])
        if len(component) == 1
    ]
    return rule_mirror(grid) if len(targets) == 4 else [list(row) for row in grid]


SEMANTIC_RIVALS: dict[str, Callable[[Any], Any]] = {
    "recolor_singleton_centers_only": _rival_centers_only,
    "paint_cross_arms_but_leave_red_center": _rival_arms_only,
    "expand_every_red_cell": _rival_expand_all_red_cells,
    "expand_every_singleton_regardless_of_color": _rival_expand_all_singletons,
    "preserve_nonzero_cross_arms": _rival_preserve_nonzero_cross_arms,
    "transform_only_first_two_red_singletons": _rival_first_two_targets,
    "transform_only_four_target_scenes": _rival_four_target_scenes_only,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def _analysis(grid) -> dict[str, Any]:
    components = _components_by_color(grid)
    red = components.get(2, [])
    return {
        "target_count": sum(len(component) == 1 for component in red),
        "has_larger_red": any(len(component) > 1 for component in red),
        "has_occupied_arm": any(
            grid[r + dr][c + dc] not in (0, 2)
            for component in red
            if len(component) == 1
            for r, c in component
            for dr, dc in _DIRS4
        ),
        "has_nonred_singleton": any(
            len(component) == 1
            for color, groups in components.items()
            if color != 2
            for component in groups
        ),
    }


SEMANTIC_WITNESSES = {
    "two_target_scene": lambda grid: _analysis(grid)["target_count"] == 2,
    "four_target_scene": lambda grid: _analysis(grid)["target_count"] == 4,
    "larger_red_components_preserved": lambda grid: _analysis(grid)["has_larger_red"],
    "nonred_singleton_preserved": lambda grid: _analysis(grid)["has_nonred_singleton"],
    "occupied_cross_arm_overwritten": lambda grid: _analysis(grid)["has_occupied_arm"],
    "yellow_center_and_four_arms_required": lambda grid: bool(
        _components_by_color(grid).get(2, [])
    ),
}
WITNESS_RIVALS = {
    "two_target_scene": ["transform_only_four_target_scenes"],
    "four_target_scene": ["transform_only_first_two_red_singletons"],
    "larger_red_components_preserved": ["expand_every_red_cell"],
    "nonred_singleton_preserved": ["expand_every_singleton_regardless_of_color"],
    "occupied_cross_arm_overwritten": ["preserve_nonzero_cross_arms"],
    "yellow_center_and_four_arms_required": [
        "recolor_singleton_centers_only",
        "paint_cross_arms_but_leave_red_center",
    ],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons that still admit a named shortcut on the query."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and output"]

    reasons: list[str] = []
    target_counts: set[int] = set()
    shapes: set[tuple[int, int]] = set()
    for index, pair in enumerate([*demos, query]):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"pair {index} must contain input and output")
            continue
        if self_check(pair["input"]):
            reasons.append(f"pair {index} is outside the lawful input grammar")
            continue
        if rule_mirror(pair["input"]) != pair["output"]:
            reasons.append(f"pair {index} disagrees with the singleton-red cross rule")
        if index < len(demos):
            target_counts.add(_analysis(pair["input"])["target_count"])
            shapes.add((len(pair["input"]), len(pair["input"][0])))
    if reasons:
        return reasons
    if target_counts != {2, 4}:
        reasons.append("demonstrations must include both two-target and four-target scenes")
    if len(shapes) < 2:
        reasons.append("demonstrations must vary grid shape to refute fixed-position copying")

    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(competitor(pair["input"]) == pair["output"] for pair in demos)
        if survives:
            if competitor(query["input"]) != query["output"]:
                reasons.append(f"demonstrations do not falsify rival: {name}")
            else:
                reasons.append(
                    f"demonstrations leave rival answer-equivalent on this query: {name}"
                )
    return reasons
