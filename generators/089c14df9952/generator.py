"""Generate accent-template copying under D4 transforms.

A yellow (4) skeleton appears in several 8-connected components.  Exactly one
component is the decorated base: it carries blue (1), red (2), and green (3)
accents.  Every other component is a transformed yellow copy, optionally with a
single red orientation hint.  The Racket authority finds the matching D4
orientation and stamps the complete base decoration, clipping at the board
edge.

The ordinary schedule deliberately alternates three identifiable branches:
plain asymmetric copies, red-disambiguated symmetric copies, and an edge copy
whose decoration is partly clipped.  Multi-target clip scenes mix hinted and
unhinted targets, preventing a scene-level "red means solve" cue.  Four
consecutive examples contain every branch and target counts 1, 2, and 3.
"""
from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
from functools import lru_cache
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "089c14df9952"
TASK_ID = GENERATOR_ID
VERSION = "4.1.0"
RULE_HASH = "1fa4f01a8b99"

SUMMARY = (
    "Find the unique yellow-4 component decorated with colors 1, 2, and 3. "
    "For each plain or red-hinted yellow twin, identify the D4 orientation of "
    "the base skeleton and stamp the complete blue/red/green decoration in "
    "that orientation; decoration cells outside the grid are clipped."
)

INVARIANTS = [
    "all nonzero cells belong to separated 8-connected components containing yellow-4",
    "exactly one base component has the three decoration colors 1, 2, and 3",
    "each target has the same yellow skeleton under a D4 transform and has either no decoration or one red-2 hint",
    "ordinary clip scenes with multiple targets contain both hinted and unhinted targets",
    "every target admits one output answer; a red hint resolves any symmetry that would otherwise change the answer",
    "ordinary draws always add at least one blue/green decoration cell",
]

AXES = {
    "grid_h": {"type": "int", "default": "band schedule", "valid": "11..20"},
    "grid_w": {"type": "int", "default": "band schedule", "valid": "12..20"},
    "target_count": {"type": "int", "default": "1|2|3 sliding schedule", "valid": "1..3"},
    "texture": {
        "type": "str",
        "default": "plain|hint|clip sliding schedule",
        "valid": "plain|hint|clip",
        "doc": (
            "plain uses an eight-way-asymmetric skeleton; hint uses a symmetric "
            "canonical skeleton whose red marker is answer-decisive; clip places "
            "one unhinted asymmetric target so at least one stamped accent leaves "
            "the grid and gives additional interior targets redundant red hints"
        ),
    },
}

HELPFUL_TEXTURES = ("plain", "hint", "clip")
DEGENERATE_TEXTURES: tuple[str, ...] = ()
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.35

Grid = list[list[int]]
Cell = tuple[int, int]
Shape = tuple[Cell, ...]
Accent = tuple[int, int, int]

# The same D4 order used by the canonical Racket rule.
_TRANSFORMS: tuple[Callable[[int, int], Cell], ...] = (
    lambda r, c: (r, c),
    lambda r, c: (c, -r),
    lambda r, c: (-r, -c),
    lambda r, c: (-c, r),
    lambda r, c: (r, -c),
    lambda r, c: (-c, -r),
    lambda r, c: (-r, c),
    lambda r, c: (c, r),
)

# Canonical base templates.  Each is symmetric in yellow alone, while the red
# accent reduces the surviving transforms to one answer-equivalent class.
_HINT_TEMPLATES: tuple[tuple[Shape, tuple[Accent, ...]], ...] = (
    (
        ((0, 0), (0, 1), (0, 2), (1, 2), (2, 2)),
        ((-1, 2, 2), (0, 3, 1), (2, 0, 3), (2, 1, 3), (2, 3, 3)),
    ),
    (
        ((0, 0), (0, 1), (0, 2), (0, 3), (0, 4)),
        ((-1, 1, 1), (-1, 3, 1), (-1, 4, 2), (1, 0, 3), (1, 2, 3), (1, 4, 3)),
    ),
    (
        ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1)),
        ((0, 2, 2), (1, -1, 1), (2, 0, 3), (3, 1, 1)),
    ),
    (
        ((0, 0), (0, 1), (1, 0), (1, 2), (2, 1), (2, 2)),
        ((-1, 0, 1), (-1, 1, 3), (0, 2, 2), (1, 3, 3), (2, 3, 1)),
    ),
)

_TEXTURE_SCHEDULE = ("hint", "plain", "clip", "hint")
_TARGET_SCHEDULE = (2, 1, 3, 3)
SCHEDULE_PROFILES = ("hint-2", "plain-1", "clip-mixed-3", "hint-3")
_CANONICAL_PROFILES = ((13, 13), (14, 15))
_BAND_SIZES = {
    "easy": ((11, 12), (12, 13), (13, 13), (13, 14)),
    "medium": ((13, 13), (14, 15), (15, 16), (16, 17)),
    "hard": ((13, 13), (14, 15), (17, 18), (18, 19), (20, 20)),
    None: ((13, 13), (14, 15), (15, 16), (16, 17)),
}


def schedule_profile(seed, sample_index, difficulty=None) -> str:
    """Name the default schedule slot for semantic census tooling."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _is_arc_grid(grid: Any) -> bool:
    return bool(
        isinstance(grid, (list, tuple))
        and grid
        and isinstance(grid[0], (list, tuple))
        and grid[0]
        and all(
            isinstance(row, (list, tuple)) and len(row) == len(grid[0])
            for row in grid
        )
        and all(
            isinstance(value, int)
            and not isinstance(value, bool)
            and 0 <= value <= 9
            for row in grid
            for value in row
        )
    )


def _norm(cells: Iterable[Cell]) -> Shape:
    seq = tuple(sorted(set(cells)))
    if not seq:
        return ()
    min_r = min(r for r, _ in seq)
    min_c = min(c for _, c in seq)
    return tuple(sorted((r - min_r, c - min_c) for r, c in seq))


def _tf(cells: Iterable[Cell], index: int) -> tuple[Cell, ...]:
    fn = _TRANSFORMS[index]
    return tuple(fn(r, c) for r, c in cells)


def _transform_origin(yellow: Shape, index: int) -> Cell:
    raw_yellow = _tf(yellow, index)
    return min(r for r, _ in raw_yellow), min(c for _, c in raw_yellow)


def _rel_after(index: int, point: Cell, yellow: Shape) -> Cell:
    min_r, min_c = _transform_origin(yellow, index)
    raw_r, raw_c = _TRANSFORMS[index](*point)
    return raw_r - min_r, raw_c - min_c


def _transform_template(yellow: Shape, accents: Sequence[Accent], index: int) -> tuple[Shape, tuple[Accent, ...]]:
    raw_yellow = _tf(yellow, index)
    min_r = min(r for r, _ in raw_yellow)
    min_c = min(c for _, c in raw_yellow)
    transformed_yellow = tuple(sorted((r - min_r, c - min_c) for r, c in raw_yellow))
    transformed_accents = []
    for r, c, value in accents:
        raw_r, raw_c = _TRANSFORMS[index](r, c)
        transformed_accents.append((raw_r - min_r, raw_c - min_c, value))
    return transformed_yellow, tuple(sorted(transformed_accents))


def _grow(rng, size: int) -> Shape:
    cells: set[Cell] = {(0, 0)}
    while len(cells) < size:
        r, c = rng.choice(sorted(cells))
        dr, dc = rng.choice(((-1, 0), (1, 0), (0, -1), (0, 1)))
        cells.add((r + dr, c + dc))
        cells = set(_norm(cells))
    return _norm(cells)


def _asymmetric_shape(rng) -> Shape:
    for _ in range(512):
        shape = _grow(rng, rng.randint(4, 6))
        if len({_norm(_tf(shape, index)) for index in range(8)}) == 8:
            return shape
    return ((0, 0), (1, 0), (1, 1), (2, 1), (2, 2))


def _attach_accents(rng, yellow: Shape, count: int = 5) -> tuple[Accent, ...]:
    yellow_set = set(yellow)
    candidates = sorted(
        {
            (r + dr, c + dc)
            for r, c in yellow
            for dr in (-1, 0, 1)
            for dc in (-1, 0, 1)
            if (dr, dc) != (0, 0)
        }
        - yellow_set
    )
    rng.shuffle(candidates)
    colors = [2, 1, 3, 1, 3, 1]
    return tuple((r, c, colors[index]) for index, (r, c) in enumerate(candidates[:count]))


def _shape_matches(yellow: Shape, target_yellow: Shape) -> tuple[int, ...]:
    return tuple(
        index
        for index in range(8)
        if _norm(_tf(yellow, index)) == target_yellow
    )


def _relative_stamp(yellow: Shape, accents: Sequence[Accent], index: int) -> tuple[Accent, ...]:
    min_r, min_c = _transform_origin(yellow, index)
    transform = _TRANSFORMS[index]
    return tuple(
        sorted(
            (
                transform(r, c)[0] - min_r,
                transform(r, c)[1] - min_c,
                value,
            )
            for r, c, value in accents
        )
    )


def _hint_decisive_indices(yellow: Shape, accents: Sequence[Accent]) -> tuple[int, ...]:
    red_points = tuple((r, c) for r, c, value in accents if value == 2)
    if len(red_points) != 1:
        return ()
    red = red_points[0]
    decisive: list[int] = []
    for intended in range(8):
        target_yellow = _norm(_tf(yellow, intended))
        matches = _shape_matches(yellow, target_yellow)
        no_hint_answers = {_relative_stamp(yellow, accents, index) for index in matches}
        red_target = _rel_after(intended, red, yellow)
        hinted = tuple(index for index in matches if _rel_after(index, red, yellow) == red_target)
        hinted_answers = {_relative_stamp(yellow, accents, index) for index in hinted}
        if len(no_hint_answers) > 1 and len(hinted_answers) == 1:
            decisive.append(intended)
    return tuple(decisive)


def _nonzero_components(grid: Grid) -> list[list[Cell]]:
    h, w = len(grid), len(grid[0])
    seen: set[Cell] = set()
    components: list[list[Cell]] = []
    for start_r in range(h):
        for start_c in range(w):
            if grid[start_r][start_c] == 0 or (start_r, start_c) in seen:
                continue
            stack = [(start_r, start_c)]
            seen.add((start_r, start_c))
            component: list[Cell] = []
            while stack:
                r, c = stack.pop()
                component.append((r, c))
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        nr, nc = r + dr, c + dc
                        if (
                            0 <= nr < h
                            and 0 <= nc < w
                            and grid[nr][nc] != 0
                            and (nr, nc) not in seen
                        ):
                            seen.add((nr, nc))
                            stack.append((nr, nc))
            components.append(sorted(component))
    return components


def _target_answer(
    grid: Grid,
    yellow: Shape,
    accents: Sequence[Accent],
    anchor_r: int,
    anchor_c: int,
    index: int,
) -> tuple[Accent, ...]:
    h, w = len(grid), len(grid[0])
    stamped: list[Accent] = []
    for r, c, value in accents:
        rel_r, rel_c = _rel_after(index, (r, c), yellow)
        out_r, out_c = anchor_r + rel_r, anchor_c + rel_c
        if 0 <= out_r < h and 0 <= out_c < w:
            stamped.append((out_r, out_c, value))
    return tuple(sorted(stamped))


def _analyze_uncached(grid: Any) -> dict[str, Any]:
    facts: dict[str, Any] = {"errors": []}
    errors: list[str] = facts["errors"]
    if not _is_arc_grid(grid):
        errors.append("grid must be a nonempty rectangular ARC grid")
        return facts

    h, w = len(grid), len(grid[0])
    facts.update(grid_h=h, grid_w=w)
    if not 11 <= h <= 20 or not 12 <= w <= 20:
        errors.append(f"grid dimensions {h}x{w} outside 11..20 by 12..20")

    palette = {value for row in grid for value in row}
    facts["palette"] = tuple(sorted(palette))
    if palette != {0, 1, 2, 3, 4}:
        errors.append(f"expected exact canonical palette {{0,1,2,3,4}}, found {sorted(palette)}")

    components = _nonzero_components(grid)
    if any(not any(grid[r][c] == 4 for r, c in comp) for comp in components):
        errors.append("every nonzero component must contain yellow-4")
    yellow_components = [comp for comp in components if any(grid[r][c] == 4 for r, c in comp)]
    if len(yellow_components) < 2:
        errors.append("need one decorated base and at least one target component")
        return facts

    def decoration_colors(component: Sequence[Cell]) -> tuple[int, ...]:
        return tuple(sorted({grid[r][c] for r, c in component if grid[r][c] != 4}))

    color_counts = [len(decoration_colors(comp)) for comp in yellow_components]
    maximum = max(color_counts)
    base_indices = [index for index, count in enumerate(color_counts) if count == maximum]
    if maximum < 2:
        errors.append("no component has at least two distinct decoration colors")
        return facts
    if len(base_indices) != 1:
        errors.append(f"base selection is ambiguous: {len(base_indices)} components tie at {maximum} decoration colors")
        return facts

    base_index = base_indices[0]
    base = yellow_components[base_index]
    base_colors = decoration_colors(base)
    if base_colors != (1, 2, 3):
        errors.append(f"base decoration colors must be exactly 1,2,3; found {base_colors}")

    base_yellow_abs = [(r, c) for r, c in base if grid[r][c] == 4]
    base_r0 = min(r for r, _ in base_yellow_abs)
    base_c0 = min(c for _, c in base_yellow_abs)
    base_yellow = tuple(sorted((r - base_r0, c - base_c0) for r, c in base_yellow_abs))
    base_accents = tuple(
        sorted(
            (r - base_r0, c - base_c0, grid[r][c])
            for r, c in base
            if grid[r][c] != 4
        )
    )
    if sum(value == 2 for _, _, value in base_accents) != 1:
        errors.append("base must contain exactly one red-2 orientation accent")
    target_facts: list[dict[str, Any]] = []
    any_change = False
    for component_index, component in enumerate(yellow_components):
        if component_index == base_index:
            continue
        colors = decoration_colors(component)
        if colors not in ((), (2,)):
            errors.append(f"target decoration colors must be empty or red-2 only; found {colors}")
            continue
        yellow_abs = [(r, c) for r, c in component if grid[r][c] == 4]
        target_r0 = min(r for r, _ in yellow_abs)
        target_c0 = min(c for _, c in yellow_abs)
        target_yellow = tuple(sorted((r - target_r0, c - target_c0) for r, c in yellow_abs))
        target_red = tuple(
            sorted(
                (r - target_r0, c - target_c0)
                for r, c in component
                if grid[r][c] == 2
            )
        )
        if len(target_red) > 1:
            errors.append("a target may contain at most one red-2 hint")
            continue
        if target_red and not any(
            abs(target_red[0][0] - yr) <= 1 and abs(target_red[0][1] - yc) <= 1
            for yr, yc in target_yellow
        ):
            errors.append("target red hint must be 8-adjacent to its yellow skeleton")
            continue

        shape_matches = _shape_matches(base_yellow, target_yellow)
        if not shape_matches:
            errors.append("target yellow skeleton is not D4-equivalent to the base skeleton")
            continue
        base_red = tuple((r, c) for r, c, value in base_accents if value == 2)
        accepted = tuple(
            index
            for index in shape_matches
            if not target_red
            or any(_rel_after(index, red, base_yellow) in target_red for red in base_red)
        )
        if not accepted:
            errors.append("target red hint is incompatible with every matching D4 orientation")
            continue

        all_answers = {
            _target_answer(grid, base_yellow, base_accents, target_r0, target_c0, index)
            for index in shape_matches
        }
        accepted_answers = {
            _target_answer(grid, base_yellow, base_accents, target_r0, target_c0, index)
            for index in accepted
        }
        if len(accepted_answers) != 1:
            errors.append("target admits multiple different output answers after applying its available cues")
            continue

        chosen = accepted[0]
        answer = next(iter(accepted_answers))
        changed_cells = tuple(
            (r, c, value)
            for r, c, value in answer
            if grid[r][c] != value
        )
        if not changed_cells:
            errors.append("target would not receive any new decoration cell")
            continue
        any_change = True
        relative_full = _relative_stamp(base_yellow, base_accents, chosen)
        clipped_count = sum(
            not (0 <= target_r0 + r < h and 0 <= target_c0 + c < w)
            for r, c, _ in relative_full
        )
        target_facts.append(
            {
                "anchor": (target_r0, target_c0),
                "yellow": target_yellow,
                "red": target_red,
                "shape_matches": shape_matches,
                "accepted_matches": accepted,
                "shape_answer_variants": len(all_answers),
                "accepted_answer_variants": len(accepted_answers),
                "chosen_index": chosen,
                "answer": answer,
                "changed_cells": changed_cells,
                "clipped_count": clipped_count,
            }
        )

    if not any_change:
        errors.append("rule output would be identical to the input")
    facts.update(
        components=yellow_components,
        base=base,
        base_yellow=base_yellow,
        base_accents=base_accents,
        yellow_orbit=len({_norm(_tf(base_yellow, index)) for index in range(8)}),
        targets=target_facts,
        target_count=len(target_facts),
    )
    if len(target_facts) != len(yellow_components) - 1:
        errors.append("one or more target components failed structural analysis")
    if not 1 <= len(target_facts) <= 3:
        errors.append(f"target count {len(target_facts)} outside 1..3")
    return facts


@lru_cache(maxsize=1024)
def _analyze_frozen(grid: tuple[tuple[int, ...], ...]) -> dict[str, Any]:
    """Analyze immutable grid content so replay/observer checks share work."""
    return _analyze_uncached(grid)


def _analyze(grid: Any) -> dict[str, Any]:
    if not _is_arc_grid(grid):
        return _analyze_uncached(grid)
    frozen = tuple(tuple(row) for row in grid)
    return _analyze_frozen(frozen)


def _analysis_cache_clear() -> None:
    """Clear analysis memoization for tests and long-lived diagnostic tools."""
    _analyze_frozen.cache_clear()


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the complete task grammar, including answer uniqueness."""
    del difficulty, meta
    return list(_analyze(grid)["errors"])


def strict_canonical_like(grid) -> list[str]:
    """Accept the canonical size/palette/cue manifold."""
    facts = _analyze(grid)
    errors = list(facts["errors"])
    if errors:
        return errors
    if (facts["grid_h"], facts["grid_w"]) not in _CANONICAL_PROFILES:
        errors.append("dimensions are outside the canonical 13x13 or 14x15 profiles")
    if facts["yellow_orbit"] >= 8:
        errors.append("canonical examples use a yellow skeleton with nontrivial D4 symmetry")
    if facts["target_count"] not in (2, 3):
        errors.append("canonical examples contain two or three targets")
    if any(not target["red"] for target in facts["targets"]):
        errors.append("every canonical target carries a red-2 orientation hint")
    if any(target["clipped_count"] for target in facts["targets"]):
        errors.append("canonical decorations fit fully inside the grid")
    return errors


def _valid_facts(grid: Grid) -> dict[str, Any] | None:
    facts = _analyze(grid)
    return None if facts["errors"] else facts


def _observed_overrides_from_facts(facts: dict[str, Any]) -> dict[str, object]:
    if any(target["clipped_count"] for target in facts["targets"]):
        texture = "clip"
    elif any(target["red"] for target in facts["targets"]):
        texture = "hint"
    else:
        texture = "plain"
    return {
        "grid_h": facts["grid_h"],
        "grid_w": facts["grid_w"],
        "target_count": facts["target_count"],
        "texture": texture,
    }


def observe_overrides(grid) -> dict[str, object]:
    """Recover every declared axis from the returned input grid."""
    facts = _valid_facts(grid)
    if facts is None:
        raise ValueError(f"cannot observe invalid grid: {self_check(grid)}")
    return _observed_overrides_from_facts(facts)


def _expanded(cells: Iterable[Cell]) -> set[Cell]:
    return {
        (r + dr, c + dc)
        for r, c in cells
        for dr in (-1, 0, 1)
        for dc in (-1, 0, 1)
    }


def _base_candidates(yellow: Shape, accents: Sequence[Accent], h: int, w: int) -> list[dict[str, Any]]:
    rel_cells = [(r, c, 4) for r, c in yellow] + list(accents)
    min_r = min(r for r, _, _ in rel_cells)
    max_r = max(r for r, _, _ in rel_cells)
    min_c = min(c for _, c, _ in rel_cells)
    max_c = max(c for _, c, _ in rel_cells)
    candidates = []
    for anchor_r in range(-min_r, h - max_r):
        for anchor_c in range(-min_c, w - max_c):
            values = tuple((anchor_r + r, anchor_c + c, value) for r, c, value in rel_cells)
            cells = {(r, c) for r, c, _ in values}
            candidates.append({"values": values, "input_cells": cells, "output_cells": cells})
    return candidates


def _target_candidates(
    yellow: Shape,
    accents: Sequence[Accent],
    transform_index: int,
    h: int,
    w: int,
    *,
    hint: bool,
    require_clip: bool,
) -> dict[str, Any]:
    """Return a shuffled-ready pool with lightweight anchors only.

    Full cell sets are created lazily by ``_materialize_target_candidate``
    when the backtracking search actually examines an anchor.  Boundary
    audits enumerate tens of thousands of scenes, so eagerly allocating every
    candidate dominated the complete review battery even though the search
    normally accepts one of its first few anchors.
    """
    target_yellow = _norm(_tf(yellow, transform_index))
    max_r = max(r for r, _ in target_yellow)
    max_c = max(c for _, c in target_yellow)
    landings = _relative_stamp(yellow, accents, transform_index)
    red_landings = tuple((r, c, value) for r, c, value in landings if value == 2)
    anchors: list[tuple[int, int, int]] = []
    for anchor_r in range(0, h - max_r):
        for anchor_c in range(0, w - max_c):
            in_bounds_count = 0
            has_visible_blue_or_green = False
            for r, c, value in landings:
                if 0 <= anchor_r + r < h and 0 <= anchor_c + c < w:
                    in_bounds_count += 1
                    if value in (1, 3):
                        has_visible_blue_or_green = True
            clipped = len(landings) - in_bounds_count
            if require_clip:
                if clipped == 0 or not has_visible_blue_or_green:
                    continue
            elif clipped:
                continue
            if hint:
                if len(red_landings) != 1:
                    continue
                red_r, red_c, _ = red_landings[0]
                abs_r, abs_c = anchor_r + red_r, anchor_c + red_c
                if not (0 <= abs_r < h and 0 <= abs_c < w):
                    continue
            anchors.append((anchor_r, anchor_c, clipped))
    return {
        "target_yellow": target_yellow,
        "landings": landings,
        "red_landings": red_landings,
        "hint": hint,
        "h": h,
        "w": w,
        "anchors": anchors,
    }


def _materialize_target_candidate(
    pool: dict[str, Any], anchor: tuple[int, int, int]
) -> dict[str, Any]:
    """Expand one candidate anchor into the collision-search representation."""
    anchor_r, anchor_c, clipped = anchor
    h, w = pool["h"], pool["w"]
    yellow_values = tuple(
        (anchor_r + r, anchor_c + c, 4)
        for r, c in pool["target_yellow"]
    )
    in_bounds = tuple(
        (anchor_r + r, anchor_c + c, value)
        for r, c, value in pool["landings"]
        if 0 <= anchor_r + r < h and 0 <= anchor_c + c < w
    )
    hint_values: tuple[tuple[int, int, int], ...] = ()
    if pool["hint"]:
        red_r, red_c, red_value = pool["red_landings"][0]
        hint_values = ((anchor_r + red_r, anchor_c + red_c, red_value),)
    input_values = yellow_values + hint_values
    return {
        "values": input_values,
        "input_cells": {(r, c) for r, c, _ in input_values},
        "output_cells": {(r, c) for r, c, _ in yellow_values + in_bounds},
        "clipped": clipped,
    }


def _place_scene(
    rng,
    yellow: Shape,
    accents: Sequence[Accent],
    transforms: Sequence[int],
    h: int,
    w: int,
    texture: str,
) -> Grid | None:
    bases = _base_candidates(yellow, accents, h, w)
    rng.shuffle(bases)
    target_sets = []
    for index, transform_index in enumerate(transforms):
        hint = texture == "hint" or (texture == "clip" and index > 0)
        pool = _target_candidates(
            yellow,
            accents,
            transform_index,
            h,
            w,
            hint=hint,
            require_clip=texture == "clip" and index == 0,
        )
        rng.shuffle(pool["anchors"])
        target_sets.append(pool)
    if any(not pool["anchors"] for pool in target_sets):
        return None

    def search(
        target_index: int,
        input_forbidden: set[Cell],
        output_occupied: set[Cell],
        chosen: list[dict[str, Any]],
    ) -> list[dict[str, Any]] | None:
        if target_index == len(target_sets):
            return list(chosen)
        pool = target_sets[target_index]
        for anchor in pool["anchors"]:
            candidate = _materialize_target_candidate(pool, anchor)
            if candidate["input_cells"] & input_forbidden:
                continue
            if candidate["input_cells"] & output_occupied:
                continue
            if candidate["output_cells"] & output_occupied:
                continue
            chosen.append(candidate)
            result = search(
                target_index + 1,
                input_forbidden | _expanded(candidate["input_cells"]),
                output_occupied | candidate["output_cells"],
                chosen,
            )
            if result is not None:
                return result
            chosen.pop()
        return None

    for base in bases:
        targets = search(0, _expanded(base["input_cells"]), set(base["output_cells"]), [])
        if targets is None:
            continue
        grid = full_grid(h, w, 0)
        for item in (base, *targets):
            for r, c, value in item["values"]:
                grid[r][c] = value
        return grid
    return None


def _validate_override_keys(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")


def _scheduled_choice(ctx, label: str, scheduled: Any, options: Sequence[Any]) -> Any:
    if ctx.overrides.get(label) is not None:
        return ctx.draw_choice(label, options)
    return ctx.draw_choice(label, (scheduled,))


def _scheduled_int(ctx, label: str, scheduled: int, lo: int, hi: int) -> int:
    if ctx.overrides.get(label) is not None:
        return ctx.draw_int_strict(label, lo, hi)
    return ctx.draw_int_strict(label, scheduled, scheduled)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    if type(sample_index) is not int:
        raise TypeError("sample_index must be an integer (not bool)")
    if sample_index < 0:
        raise ValueError("sample_index must be non-negative")
    _validate_override_keys(overrides)
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty {difficulty!r}")
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    slot = int(sample_index) % len(_TEXTURE_SCHEDULE)
    texture = _scheduled_choice(ctx, "texture", _TEXTURE_SCHEDULE[slot], HELPFUL_TEXTURES)
    target_count = _scheduled_int(ctx, "target_count", _TARGET_SCHEDULE[slot], 1, 3)

    if texture == "hint" and overrides.get("grid_h") is None and overrides.get("grid_w") is None:
        profile = _CANONICAL_PROFILES[(int(seed) + int(sample_index) // 4) % len(_CANONICAL_PROFILES)]
        h = ctx.draw_int("grid_h", profile[0], profile[0])
        w = ctx.draw_int("grid_w", profile[1], profile[1])
    else:
        size_options = _BAND_SIZES[difficulty]
        scheduled_size = size_options[(int(seed) + int(sample_index)) % len(size_options)]
        h = _scheduled_int(ctx, "grid_h", scheduled_size[0], 11, 20)
        w = _scheduled_int(ctx, "grid_w", scheduled_size[1], 12, 20)

    # If exactly one dimension is overridden on a hint draw, the other axis was
    # already scheduled above; all declared combinations remain legal.
    rng = ctx.draw_rng("scene")
    for attempt in range(192):
        if texture == "hint":
            template_indices = list(range(len(_HINT_TEMPLATES)))
            if h * w < 150 or target_count == 3:
                template_indices = [0, 2, 3, 1]
            template_index = template_indices[(attempt + int(seed) + int(sample_index)) % len(template_indices)]
            yellow, accents = _HINT_TEMPLATES[template_index]
            yellow, accents = _transform_template(yellow, accents, rng.randrange(8))
            decisive = _hint_decisive_indices(yellow, accents)
            if not decisive:
                continue
            transforms = tuple(
                decisive[(int(seed) + 3 * int(sample_index) + 5 * index + attempt) % len(decisive)]
                for index in range(target_count)
            )
        else:
            yellow = _asymmetric_shape(rng)
            accents = _attach_accents(rng, yellow, count=5)
            if {value for _, _, value in accents} != {1, 2, 3}:
                continue
            yellow, accents = _transform_template(yellow, accents, rng.randrange(8))
            transforms = tuple(
                (int(seed) + 3 * int(sample_index) + 5 * index + attempt) % 8
                for index in range(target_count)
            )

        grid = _place_scene(rng, yellow, accents, transforms, h, w, texture)
        if grid is None:
            continue
        facts = _analyze(grid)
        if facts["errors"]:
            continue
        observed = _observed_overrides_from_facts(facts)
        expected = {
            "grid_h": h,
            "grid_w": w,
            "target_count": target_count,
            "texture": texture,
        }
        if observed != expected:
            raise AssertionError(f"axis observer mismatch: observed={observed}, expected={expected}")
        return grid
    raise ValueError(
        f"could not realize {texture} scene on {h}x{w} with {target_count} target(s)"
    )


def rule_mirror(grid: Grid) -> Grid:
    """Diagnostic Python mirror of the Racket authority; never output authority."""
    facts = _analyze(grid)
    if facts["errors"]:
        raise ValueError(f"invalid task input: {facts['errors']}")
    out = [row[:] for row in grid]
    for target in facts["targets"]:
        for r, c, value in target["answer"]:
            out[r][c] = value
    return out


def _apply_competitor(grid: Grid, selector: Callable[[dict[str, Any]], int | None], *, colors: set[int] | None = None) -> Grid:
    facts = _analyze(grid)
    if facts["errors"]:
        return [row[:] for row in grid]
    out = [row[:] for row in grid]
    for target in facts["targets"]:
        index = selector(target)
        if index is None:
            continue
        anchor_r, anchor_c = target["anchor"]
        answer = _target_answer(grid, facts["base_yellow"], facts["base_accents"], anchor_r, anchor_c, index)
        for r, c, value in answer:
            if colors is None or value in colors:
                out[r][c] = value
    return out


def _identity(grid: Grid) -> Grid:
    return [row[:] for row in grid]


def _geometry_only(grid: Grid) -> Grid:
    return _apply_competitor(grid, lambda target: target["shape_matches"][0])


def _untransformed(grid: Grid) -> Grid:
    return _apply_competitor(grid, lambda target: 0)


def _red_only(grid: Grid) -> Grid:
    return _apply_competitor(grid, lambda target: target["accepted_matches"][0], colors={2})


def _hinted_targets_only(grid: Grid) -> Grid:
    return _apply_competitor(
        grid,
        lambda target: target["accepted_matches"][0] if target["red"] else None,
    )


def _scene_uniform_hint_policy(grid: Grid) -> Grid:
    facts = _analyze(grid)
    if facts["errors"]:
        return [row[:] for row in grid]
    solve_only_hinted = any(target["red"] for target in facts["targets"])
    return _apply_competitor(
        grid,
        lambda target: (
            target["accepted_matches"][0]
            if not solve_only_hinted or target["red"]
            else None
        ),
    )


def _skip_clipped(grid: Grid) -> Grid:
    return _apply_competitor(
        grid,
        lambda target: None if target["clipped_count"] else target["accepted_matches"][0],
    )


def _fixed_transform(index: int) -> Callable[[Grid], Grid]:
    return lambda grid: _apply_competitor(grid, lambda target: index)


SEMANTIC_RIVALS: dict[str, Callable[[Grid], Grid]] = {
    "hinted_targets_only": _hinted_targets_only,
    "scene_uniform_hint_policy": _scene_uniform_hint_policy,
    "copy_only_red_marker": _red_only,
    "skip_clipped_targets": _skip_clipped,
}

CANONICAL_SHORTCUTS: dict[str, Callable[[Grid], Grid]] = {
    name: SEMANTIC_RIVALS[name]
    for name in (
        "hinted_targets_only",
        "scene_uniform_hint_policy",
        "skip_clipped_targets",
    )
}

LESSON_COMPETITORS: dict[str, Callable[[Grid], Grid]] = {
    "leave every target unchanged": _identity,
    "stamp the base decoration without transforming it": _untransformed,
    "ignore red hints and choose the first yellow-shape match": _geometry_only,
    **SEMANTIC_RIVALS,
    **{f"always use D4 transform {index}": _fixed_transform(index) for index in range(8)},
}

# Backward-compatible private name used by older local probes.
_LESSON_COMPETITORS = LESSON_COMPETITORS


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons where a named shortcut fits all demos but changes query."""
    reasons: list[str] = []
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    items = [*demos, query]
    for index, item in enumerate(items):
        label = f"demo {index}" if index < len(demos) else "query"
        if not isinstance(item, dict) or "input" not in item or "output" not in item:
            reasons.append(f"{label} must contain input and output grids")
            continue
        errors = self_check(item["input"])
        if errors:
            reasons.append(f"{label} input is outside the task grammar: {errors}")
            continue
        if rule_mirror(item["input"]) != item["output"]:
            reasons.append(f"{label} output does not match the accent-copy rule")
    if reasons:
        return reasons

    demo_textures = {observe_overrides(item["input"])["texture"] for item in demos}
    if demo_textures != set(HELPFUL_TEXTURES):
        reasons.append(f"demonstrations do not cover plain, hint, and clip branches: {sorted(demo_textures)}")
    demo_counts = {observe_overrides(item["input"])["target_count"] for item in demos}
    if demo_counts != {1, 2, 3}:
        reasons.append(f"demonstrations do not cover target counts 1, 2, and 3: {sorted(demo_counts)}")

    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(item["input"]) == item["output"] for item in demos):
            if competitor(query["input"]) != query["output"]:
                reasons.append(f"competing rule '{name}' fits every demo but changes the query answer")
    return reasons


def _witness_texture(name: str) -> Callable[[Grid], bool]:
    def witness(grid: Grid) -> bool:
        facts = _valid_facts(grid)
        return bool(facts and observe_overrides(grid)["texture"] == name)

    return witness


def _witness_target_count(count: int) -> Callable[[Grid], bool]:
    def witness(grid: Grid) -> bool:
        facts = _valid_facts(grid)
        return bool(facts and facts["target_count"] == count)

    return witness


def _hint_is_decisive(grid: Grid) -> bool:
    facts = _valid_facts(grid)
    return bool(
        facts
        and observe_overrides(grid)["texture"] == "hint"
        and all(target["shape_answer_variants"] > 1 for target in facts["targets"])
        and all(target["accepted_answer_variants"] == 1 for target in facts["targets"])
    )


def _clip_is_partial(grid: Grid) -> bool:
    facts = _valid_facts(grid)
    return bool(
        facts
        and observe_overrides(grid)["texture"] == "clip"
        and any(target["clipped_count"] > 0 for target in facts["targets"])
        and all(target["changed_cells"] for target in facts["targets"])
    )


def _mixed_target_cues(grid: Grid) -> bool:
    facts = _valid_facts(grid)
    return bool(
        facts
        and {bool(target["red"]) for target in facts["targets"]}
        == {False, True}
    )


def _has_rotation(grid: Grid) -> bool:
    facts = _valid_facts(grid)
    return bool(facts and any(target["chosen_index"] in (1, 2, 3) for target in facts["targets"]))


def _has_reflection(grid: Grid) -> bool:
    facts = _valid_facts(grid)
    return bool(facts and any(target["chosen_index"] >= 4 for target in facts["targets"]))


def _all_answers_unique(grid: Grid) -> bool:
    facts = _valid_facts(grid)
    return bool(facts and all(target["accepted_answer_variants"] == 1 for target in facts["targets"]))


SEMANTIC_WITNESSES: dict[str, Callable[[Grid], bool]] = {
    "canonical_symmetric_hint_profile": lambda grid: not strict_canonical_like(grid),
    "plain_unique_shape_match": _witness_texture("plain"),
    "red_hint_answer_decisive": _hint_is_decisive,
    "partial_edge_clipping": _clip_is_partial,
    "mixed_target_cues": _mixed_target_cues,
    "one_target": _witness_target_count(1),
    "two_targets": _witness_target_count(2),
    "three_targets": _witness_target_count(3),
    "rotation_used": _has_rotation,
    "reflection_used": _has_reflection,
    "all_targets_have_one_answer": _all_answers_unique,
}

WITNESS_RIVALS: dict[str, list[str]] = {
    "plain_unique_shape_match": ["hinted_targets_only"],
    "red_hint_answer_decisive": ["copy_only_red_marker"],
    "partial_edge_clipping": ["skip_clipped_targets"],
    "mixed_target_cues": ["scene_uniform_hint_policy"],
}

BRANCH_WITNESSES = (
    "canonical_symmetric_hint_profile",
    "one_target",
    "two_targets",
    "three_targets",
    "rotation_used",
    "reflection_used",
    "all_targets_have_one_answer",
)
