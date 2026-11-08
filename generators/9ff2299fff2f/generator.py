"""Generator for ``9ff2299fff2f`` — translate payload by the 8→9 vector.

The unique cyan (8) and maroon (9) cells define a displacement.  The output is
an empty grid containing every other nonzero input cell translated by exactly
that displacement.  Both guide markers are removed.

The canonical examples only use a down/right vector and one connected payload,
so generated lessons deliberately include negative/axis-aligned vectors,
multiple payload components, and multiple payload colors.  Four consecutive
``sample_index`` values cover all shortcut-rebuttal profiles.
"""
from __future__ import annotations

from collections import deque
from functools import lru_cache
from typing import Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "9ff2299fff2f"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "66a18d96f7a1"

SUMMARY = (
    "Find the unique color-8 source marker and unique color-9 destination "
    "marker. Translate every non-{0,8,9} payload cell by the exact 8→9 "
    "vector onto a fresh background grid. Remove both markers and clear every "
    "original payload position. Scheduled lessons include negative and "
    "axis-aligned vectors, disconnected payloads, and multicolor payloads so "
    "positive-only, first-component-only, modal-color-only, marker-preserving, "
    "and fixed-vector shortcuts are contradicted."
)

INVARIANTS = [
    "background is color 0 and the grid is rectangular",
    "exactly one color-8 marker and one color-9 marker define a supported nonzero vector",
    "there are 3..8 payload cells in 1..3 four-connected components",
    "payload uses 1..3 colors drawn from {1,2,3,4,5,6,7}",
    "every translated payload cell stays in bounds and avoids both guide markers",
    "the Racket oracle alone owns output construction and removes both markers",
]

AXES = {
    "grid_h": {"type": "int", "default": "scheduled 8..12", "valid": "8..12"},
    "grid_w": {"type": "int", "default": "scheduled 8..12", "valid": "8..12"},
    "vector": {
        "type": "str",
        "default": "scheduled semantic profile",
        "valid": (
            "2,2|1,3|3,1|-2,2|2,-2|-2,-2|-3,1|1,-3|"
            "0,2|0,-2|2,0|-2,0"
        ),
    },
    "payload_cells": {
        "type": "int",
        "default": "scheduled 3..8",
        "valid": "3..8",
    },
    "payload_components": {
        "type": "int",
        "default": "scheduled 1..3",
        "valid": "1..3",
    },
    "palette_size": {
        "type": "int",
        "default": "scheduled 1..3",
        "valid": "1..3",
    },
}

# Every boundary combination above is constructible, including 8x8 with the
# largest vector, eight payload cells, three components, and three colors.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []

_VECTOR_VALUES = tuple(AXES["vector"]["valid"].split("|"))
_VECTOR_MAP = {
    text: tuple(int(part) for part in text.split(","))
    for text in _VECTOR_VALUES
}
_CANONICAL_VECTORS = {(2, 2), (1, 3)}
_CANONICAL_DIMS = {(8, 8), (9, 9)}
_CARDINAL = ((1, 0), (-1, 0), (0, 1), (0, -1))
_PROFILE_NAMES = (
    "canonical_anchor",
    "negative_vector",
    "multiple_components",
    "axis_aligned_multicolor",
)
SCHEDULE_PROFILES = _PROFILE_NAMES
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.20


def schedule_profile(seed, sample_index, difficulty=None):
    """Four consecutive draws expose every decisive semantic branch."""
    del seed, difficulty
    return _PROFILE_NAMES[int(sample_index) % len(_PROFILE_NAMES)]


def _validate_grid(grid) -> tuple[int, int, list[str]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return 0, 0, ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return len(grid), 0, ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return len(grid), width, ["grid must be rectangular"]
    errors: list[str] = []
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                errors.append(f"cell ({r},{c}) is not a literal ARC color 0..9: {value!r}")
                return len(grid), width, errors
    return len(grid), width, errors


def _cells(grid, predicate) -> list[tuple[int, int]]:
    return [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if predicate(value)
    ]


def _payload_cells(grid) -> list[tuple[int, int]]:
    return _cells(grid, lambda value: value not in (0, 8, 9))


def _marker_vector(grid) -> tuple[int, int] | None:
    eights = _cells(grid, lambda value: value == 8)
    nines = _cells(grid, lambda value: value == 9)
    if len(eights) != 1 or len(nines) != 1:
        return None
    return nines[0][0] - eights[0][0], nines[0][1] - eights[0][1]


def _components(cells: Iterable[tuple[int, int]]) -> list[tuple[tuple[int, int], ...]]:
    unseen = set(cells)
    found: list[tuple[tuple[int, int], ...]] = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        queue = deque([start])
        component = [start]
        while queue:
            r, c = queue.popleft()
            for dr, dc in _CARDINAL:
                neighbor = (r + dr, c + dc)
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    queue.append(neighbor)
                    component.append(neighbor)
        found.append(tuple(sorted(component)))
    found.sort(key=lambda component: component[0])
    return found


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed, ambiguous, clipped, and rule-hiding input scenes."""
    del difficulty, meta
    height, width, errors = _validate_grid(grid)
    if errors:
        return errors
    if not (8 <= height <= 12):
        errors.append(f"height {height} outside 8..12")
    if not (8 <= width <= 12):
        errors.append(f"width {width} outside 8..12")

    eights = _cells(grid, lambda value: value == 8)
    nines = _cells(grid, lambda value: value == 9)
    if len(eights) != 1:
        errors.append(f"expected exactly one color-8 source marker, found {len(eights)}")
    if len(nines) != 1:
        errors.append(f"expected exactly one color-9 destination marker, found {len(nines)}")
    if errors:
        return errors

    vector = (nines[0][0] - eights[0][0], nines[0][1] - eights[0][1])
    if vector not in set(_VECTOR_MAP.values()):
        errors.append(f"unsupported or zero 8→9 vector {vector}")

    payload = _payload_cells(grid)
    if not (3 <= len(payload) <= 8):
        errors.append(f"expected 3..8 payload cells, found {len(payload)}")
    payload_colors = {grid[r][c] for r, c in payload}
    if any(color not in {1, 2, 3, 4, 5, 6, 7} for color in payload_colors):
        errors.append(f"payload colors must be drawn from 1..7, found {sorted(payload_colors)}")
    if not (1 <= len(payload_colors) <= 3):
        errors.append(f"expected 1..3 payload colors, found {len(payload_colors)}")

    component_count = len(_components(payload))
    if not (1 <= component_count <= 3):
        errors.append(f"expected 1..3 payload components, found {component_count}")

    dr, dc = vector
    translated = {(r + dr, c + dc) for r, c in payload}
    if any(not (0 <= r < height and 0 <= c < width) for r, c in translated):
        errors.append("at least one translated payload cell leaves the grid")
    if eights[0] in translated or nines[0] in translated:
        errors.append("translated payload may not overlap either guide marker")
    if len(translated) != len(payload):
        errors.append("translation must preserve one-to-one payload positions")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Narrow manifold shared by all three canonical train/test inputs."""
    reasons = list(self_check(grid))
    if reasons:
        return reasons
    height, width = len(grid), len(grid[0])
    if (height, width) not in _CANONICAL_DIMS:
        reasons.append(f"canonical dimensions are 8x8 or 9x9, found {height}x{width}")
    vector = _marker_vector(grid)
    if vector not in _CANONICAL_VECTORS:
        reasons.append(f"canonical vector must be (2,2) or (1,3), found {vector}")
    payload = _payload_cells(grid)
    if len(payload) != 3:
        reasons.append(f"canonical payload has exactly 3 cells, found {len(payload)}")
    if len(_components(payload)) != 1:
        reasons.append("canonical payload is one four-connected component")
    palette_size = len({grid[r][c] for r, c in payload})
    if palette_size not in (1, 2):
        reasons.append(f"canonical payload uses one or two colors, found {palette_size}")
    return reasons


def observe_overrides(grid) -> dict[str, object]:
    vector = _marker_vector(grid)
    payload = _payload_cells(grid)
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "vector": f"{vector[0]},{vector[1]}" if vector is not None else "invalid",
        "payload_cells": len(payload),
        "payload_components": len(_components(payload)),
        "palette_size": len({grid[r][c] for r, c in payload}),
    }


def _translate_payload(
    grid,
    vector: tuple[int, int],
    *,
    allowed_cells: set[tuple[int, int]] | None = None,
    allowed_colors: set[int] | None = None,
    preserve_markers: bool = False,
):
    height, width = len(grid), len(grid[0])
    output = full_grid(height, width, 0)
    if preserve_markers:
        for r, c in _cells(grid, lambda value: value in (8, 9)):
            output[r][c] = grid[r][c]
    dr, dc = vector
    for r, c in _payload_cells(grid):
        if allowed_cells is not None and (r, c) not in allowed_cells:
            continue
        value = grid[r][c]
        if allowed_colors is not None and value not in allowed_colors:
            continue
        rr, cc = r + dr, c + dc
        if 0 <= rr < height and 0 <= cc < width:
            output[rr][cc] = value
    return output


def rule_mirror(grid):
    """Independent Python mirror for tests; canonical Racket remains authority."""
    vector = _marker_vector(grid)
    if vector is None:
        raise ValueError("rule requires exactly one 8 marker and one 9 marker")
    return _translate_payload(grid, vector)


def _rival_absolute_vector(grid):
    vector = _marker_vector(grid)
    if vector is None:
        return full_grid(len(grid), len(grid[0]), 0)
    return _translate_payload(grid, (abs(vector[0]), abs(vector[1])))


def _rival_first_component_only(grid):
    vector = _marker_vector(grid)
    if vector is None:
        return full_grid(len(grid), len(grid[0]), 0)
    components = _components(_payload_cells(grid))
    allowed = set(components[0]) if components else set()
    return _translate_payload(grid, vector, allowed_cells=allowed)


def _rival_modal_color_only(grid):
    vector = _marker_vector(grid)
    if vector is None:
        return full_grid(len(grid), len(grid[0]), 0)
    counts: dict[int, int] = {}
    for r, c in _payload_cells(grid):
        value = grid[r][c]
        counts[value] = counts.get(value, 0) + 1
    if not counts:
        return full_grid(len(grid), len(grid[0]), 0)
    modal = min(counts, key=lambda color: (-counts[color], color))
    return _translate_payload(grid, vector, allowed_colors={modal})


def _rival_force_diagonal(grid):
    vector = _marker_vector(grid)
    if vector is None:
        return full_grid(len(grid), len(grid[0]), 0)
    dr, dc = vector
    rival = (dr if dr else 2, dc if dc else 2)
    return _translate_payload(grid, rival)


def _rival_preserve_markers(grid):
    vector = _marker_vector(grid)
    if vector is None:
        return [list(row) for row in grid]
    return _translate_payload(grid, vector, preserve_markers=True)


def _witness_negative_component(grid) -> bool:
    vector = _marker_vector(grid)
    return vector is not None and (vector[0] < 0 or vector[1] < 0)


def _witness_multiple_components(grid) -> bool:
    return not self_check(grid) and len(_components(_payload_cells(grid))) > 1


def _witness_multicolor(grid) -> bool:
    payload = _payload_cells(grid)
    return not self_check(grid) and len({grid[r][c] for r, c in payload}) > 1


def _witness_axis_aligned(grid) -> bool:
    vector = _marker_vector(grid)
    return (
        not self_check(grid)
        and vector is not None
        and ((vector[0] == 0) ^ (vector[1] == 0))
    )


SEMANTIC_WITNESSES = {
    "negative_component_refutes_absolute_vector": _witness_negative_component,
    "multiple_components_refute_first_component_only": _witness_multiple_components,
    "multicolor_refutes_modal_color_only": _witness_multicolor,
    "axis_aligned_refutes_forced_diagonal": _witness_axis_aligned,
}

SEMANTIC_RIVALS = {
    "absolute_guide_vector": _rival_absolute_vector,
    "first_component_only": _rival_first_component_only,
    "modal_payload_color_only": _rival_modal_color_only,
    "force_diagonal_vector": _rival_force_diagonal,
}

WITNESS_RIVALS = {
    "negative_component_refutes_absolute_vector": ["absolute_guide_vector"],
    "multiple_components_refute_first_component_only": ["first_component_only"],
    "multicolor_refutes_modal_color_only": ["modal_payload_color_only"],
    "axis_aligned_refutes_forced_diagonal": ["force_diagonal_vector"],
}

LESSON_COMPETITORS = {
    **SEMANTIC_RIVALS,
    "preserve_guide_markers": _rival_preserve_markers,
}

# Both wrong rules fit every canonical pair: all canonical vectors are positive,
# and every canonical payload is one connected component.  Generated witnesses
# above must therefore supply the counterexamples canonical data cannot.
CANONICAL_SHORTCUTS = {
    "absolute_guide_vector": _rival_absolute_vector,
    "first_component_only": _rival_first_component_only,
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require one four-demo schedule block that refutes every named rival."""
    reasons: list[str] = []
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]
    if self_check(query["input"]):
        reasons.append("query input is outside the lawful teaching grammar")

    witnessed = {name: False for name in SEMANTIC_WITNESSES}
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        errors = self_check(demo["input"])
        if errors:
            reasons.append(f"demo {index} input is invalid: {errors[0]}")
            continue
        if demo["output"] != rule_mirror(demo["input"]):
            reasons.append(f"demo {index} output does not match exact marker-removing translation")
        for name, predicate in SEMANTIC_WITNESSES.items():
            witnessed[name] = witnessed[name] or bool(predicate(demo["input"]))
    for name, fired in witnessed.items():
        if not fired:
            reasons.append(f"demonstrations omit semantic witness {name}")
    return reasons


def _scheduled_int(ctx, overrides, label: str, default: int, lo: int, hi: int) -> int:
    if label in overrides and overrides[label] is not None:
        return ctx.draw_int(label, lo, hi)
    return ctx.draw_int(label, default, default)


def _scheduled_choice(ctx, overrides, label: str, default: str, options) -> str:
    if label in overrides and overrides[label] is not None:
        return ctx.draw_choice(label, options)
    return ctx.draw_choice(label, (default,))


def _profile_defaults(seed: int, sample_index: int, difficulty) -> dict[str, object]:
    profile = schedule_profile(seed, sample_index, difficulty)
    ctx_seed = (int(seed) * 1315423911 + int(sample_index) * 2654435761) & 0xFFFFFFFF
    # This local arithmetic only selects scheduled defaults; all stochastic
    # layout and palette choices still use keyed GenCtx RNGs.
    selector = ctx_seed % 12
    if profile == "canonical_anchor":
        if selector % 3 == 0:
            return {
                "grid_h": 8,
                "grid_w": 8,
                "vector": "2,2",
                "payload_cells": 3,
                "payload_components": 1,
                "palette_size": 2,
            }
        return {
            "grid_h": 9,
            "grid_w": 9,
            "vector": "1,3" if selector % 2 else "2,2",
            "payload_cells": 3,
            "payload_components": 1,
            "palette_size": 1,
        }
    if profile == "negative_vector":
        vectors = ("-2,2", "2,-2", "-2,-2", "-3,1", "1,-3", "0,-2", "-2,0")
        return {
            "grid_h": 8 + (selector % (3 if difficulty == "easy" else 5)),
            "grid_w": 8 + ((selector // 2) % (3 if difficulty == "easy" else 5)),
            "vector": vectors[selector % len(vectors)],
            "payload_cells": 3 + (selector % (2 if difficulty == "easy" else 4)),
            "payload_components": 1,
            "palette_size": 1 + selector % 2,
        }
    if profile == "multiple_components":
        vectors = ("2,2", "1,3", "3,1", "-2,2", "2,-2")
        components = 2 + (selector % 2)
        minimum_cells = components
        target_cells = max(5, minimum_cells + (selector % 4))
        return {
            "grid_h": 8 + (selector % (3 if difficulty == "easy" else 5)),
            "grid_w": 8 + ((selector // 3) % (3 if difficulty == "easy" else 5)),
            "vector": vectors[selector % len(vectors)],
            "payload_cells": min(8, target_cells),
            "payload_components": components,
            "palette_size": 1 + selector % 2,
        }
    vectors = ("0,2", "0,-2", "2,0", "-2,0")
    return {
        "grid_h": 8 + (selector % (3 if difficulty == "easy" else 5)),
        "grid_w": 8 + ((selector // 4) % (3 if difficulty == "easy" else 5)),
        "vector": vectors[selector % len(vectors)],
        "payload_cells": 4 + (selector % (3 if difficulty == "easy" else 5)),
        "payload_components": 1 + (selector % 2),
        "palette_size": 3,
    }


def _base_shape(payload_cells: int, component_count: int) -> frozenset[tuple[int, int]]:
    sizes = [
        payload_cells // component_count + (1 if index < payload_cells % component_count else 0)
        for index in range(component_count)
    ]
    if component_count == 1:
        snake = (
            (0, 0), (0, 1), (0, 2), (1, 2),
            (1, 1), (1, 0), (2, 0), (2, 1),
        )
        return frozenset(snake[:payload_cells])
    cells = {
        (2 * component_index, col)
        for component_index, size in enumerate(sizes)
        for col in range(size)
    }
    return frozenset(cells)


def _normalize_shape(cells) -> frozenset[tuple[int, int]]:
    min_row = min(r for r, _ in cells)
    min_col = min(c for _, c in cells)
    return frozenset((r - min_row, c - min_col) for r, c in cells)


@lru_cache(maxsize=None)
def _shape_variants(payload_cells: int, component_count: int):
    current = set(_base_shape(payload_cells, component_count))
    variants: set[frozenset[tuple[int, int]]] = set()
    for _ in range(4):
        variants.add(_normalize_shape(current))
        variants.add(_normalize_shape({(r, -c) for r, c in current}))
        current = {(c, -r) for r, c in current}
    return tuple(sorted(variants, key=lambda shape: tuple(sorted(shape))))


def _construct_layout(height, width, vector, payload_cells, component_count, rng):
    dr, dc = vector
    row_lo, row_hi = max(0, -dr), min(height - 1, height - 1 - dr)
    col_lo, col_hi = max(0, -dc), min(width - 1, width - 1 - dc)
    variants = _shape_variants(payload_cells, component_count)
    shape = variants[rng.randrange(len(variants))]
    shape_h = max(r for r, _ in shape) + 1
    shape_w = max(c for _, c in shape) + 1
    top = rng.randint(row_lo, row_hi - shape_h + 1)
    left = rng.randint(col_lo, col_hi - shape_w + 1)
    payload = {(top + r, left + c) for r, c in shape}
    translated = {(r + dr, c + dc) for r, c in payload}

    marker_sources = [
        (r, c)
        for r in range(row_lo, row_hi + 1)
        for c in range(col_lo, col_hi + 1)
        if (r, c) not in payload
        and (r, c) not in translated
        and (r + dr, c + dc) not in payload
        and (r + dr, c + dc) not in translated
    ]
    if not marker_sources:
        raise ValueError("no marker placement remains for a valid payload layout")
    source = marker_sources[rng.randrange(len(marker_sources))]
    destination = source[0] + dr, source[1] + dc
    return payload, source, destination


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {unknown}; valid axes: {sorted(AXES)}")
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    defaults = _profile_defaults(seed, sample_index, difficulty)
    height = _scheduled_int(ctx, overrides, "grid_h", int(defaults["grid_h"]), 8, 12)
    width = _scheduled_int(ctx, overrides, "grid_w", int(defaults["grid_w"]), 8, 12)
    vector_text = _scheduled_choice(
        ctx, overrides, "vector", str(defaults["vector"]), _VECTOR_VALUES
    )
    payload_count = _scheduled_int(
        ctx, overrides, "payload_cells", int(defaults["payload_cells"]), 3, 8
    )
    component_count = _scheduled_int(
        ctx, overrides, "payload_components", int(defaults["payload_components"]), 1, 3
    )
    palette_size = _scheduled_int(
        ctx, overrides, "palette_size", int(defaults["palette_size"]), 1, 3
    )
    if component_count > payload_count:
        raise ValueError(
            f"payload_components={component_count} exceeds payload_cells={payload_count}"
        )
    if palette_size > payload_count:
        raise ValueError(f"palette_size={palette_size} exceeds payload_cells={payload_count}")

    layout_rng = ctx.draw_rng("layout")
    payload, source, destination = _construct_layout(
        height,
        width,
        _VECTOR_MAP[vector_text],
        payload_count,
        component_count,
        layout_rng,
    )
    colors = ctx.draw_distinct_colors(
        "payload_colors", n=palette_size, exclude={0, 8, 9}
    )
    ordered_payload = sorted(payload)
    color_rng = ctx.draw_rng("color_assignment")
    color_rng.shuffle(ordered_payload)

    grid = full_grid(height, width, 0)
    grid[source[0]][source[1]] = 8
    grid[destination[0]][destination[1]] = 9
    for index, (r, c) in enumerate(ordered_payload):
        grid[r][c] = colors[index % len(colors)]

    errors = self_check(grid)
    if errors:
        raise ValueError(f"constructed invalid generator instance: {errors}")
    observed = observe_overrides(grid)
    for axis in AXES:
        requested = ctx.axis_value(axis)
        if observed[axis] != requested:
            raise ValueError(
                f"realized axis {axis!r}={observed[axis]!r} does not match keyed draw {requested!r}"
            )
    return [row[:] for row in grid]
