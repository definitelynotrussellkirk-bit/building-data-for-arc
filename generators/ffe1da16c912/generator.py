"""Generator for ``arc_puzzle_bank_nineteenth21:H131``.

The first three 3x3 panels are a library of shape families.  The fourth panel
is a rotated/reflected and recolored copy of exactly one library shape.  The
answer is that library exemplar in its displayed orientation, tightly cropped
and recolored with the query color.

Version 3 turns the former probabilistic distribution into an observable
teaching curriculum.  Every three consecutive examples exercise all three
library positions; every 24 exercise the full position x D4 transform product.
All three prototypes have the same area, so area-only selection cannot solve an
example, and the matched prototype is chosen from a full eight-image D4 orbit,
so the requested transform is observable without metadata.
"""
from __future__ import annotations

from itertools import combinations
from typing import Any, Callable, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "ffe1da16c912"
TASK_ID = "ffe1da16c912"
VERSION = "3.0.0"
RULE_HASH = "c4020b613ba0"
SUMMARY = "Match a transformed query support to one of three prototype panels."

INVARIANTS = [
    "the input has four 3x3 panels separated by solid color-5 columns",
    "the first three monochrome prototypes are pairwise D4-distinct",
    "the query is a D4 transform of exactly one prototype",
    "the output is the displayed matched prototype, cropped and recolored by the query",
]

_CODES = ("id", "r1", "r2", "r3", "fh", "fv", "tr", "atr")
# Interleave proper rotations and reflections.  Thus every length-three lesson
# contains a reflection, while the 24-step joint schedule covers 3 x 8.
_SCHEDULE_CODES = ("id", "fh", "r1", "fv", "r2", "tr", "r3", "atr")
_REFLECTION_CODES = frozenset(("fh", "fv", "tr", "atr"))
_ROTATION_CODES = ("id", "r1", "r2", "r3")
_PALETTE = (1, 2, 3, 4, 6, 7, 8, 9)
_BAND_CELL_COUNTS = {None: 5, "easy": 4, "medium": 5, "hard": 6}

AXES = {
    "cell_count": {
        "type": "int",
        "default": "4 easy, 5 medium/default, 6 hard",
        "valid": "4..6",
    },
    "match_index": {
        "type": "int",
        "default": "sample_index mod 3",
        "valid": "0..2",
    },
    "transform": {
        "type": "enum",
        "default": "8-step curriculum",
        "valid": "id|r1|r2|r3|fh|fv|tr|atr",
    },
}
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []


def _normalize(cells: Iterable[tuple[int, int]]) -> list[tuple[int, int]]:
    cells = list(cells)
    if not cells:
        return []
    min_r = min(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    return sorted((r - min_r, c - min_c) for r, c in cells)


def _dims(cells: Iterable[tuple[int, int]]) -> tuple[int, int]:
    cells = list(cells)
    return max(r for r, _ in cells) + 1, max(c for _, c in cells) + 1


def _xform(cells: Iterable[tuple[int, int]], code: str) -> list[tuple[int, int]]:
    cells = _normalize(cells)
    if code not in _CODES:
        raise ValueError(f"unknown transform: {code!r}")
    h, w = _dims(cells)
    if code == "id":
        raw = cells
    elif code == "r1":
        raw = [(c, h - 1 - r) for r, c in cells]
    elif code == "r2":
        raw = [(h - 1 - r, w - 1 - c) for r, c in cells]
    elif code == "r3":
        raw = [(w - 1 - c, r) for r, c in cells]
    elif code == "fh":
        raw = [(r, w - 1 - c) for r, c in cells]
    elif code == "fv":
        raw = [(h - 1 - r, c) for r, c in cells]
    elif code == "tr":
        raw = [(c, r) for r, c in cells]
    else:  # anti-transpose = rotate-180(transpose(cells))
        raw = [(w - 1 - c, h - 1 - r) for r, c in cells]
    return _normalize(raw)


def _orbit(cells: Iterable[tuple[int, int]]) -> tuple[tuple[tuple[int, int], ...], ...]:
    return tuple(sorted({tuple(_xform(cells, code)) for code in _CODES}))


def _dihedral_canon(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    return min(_orbit(cells))


def _connected(cells: Iterable[tuple[int, int]]) -> bool:
    remaining = set(cells)
    if not remaining:
        return False
    stack = [next(iter(remaining))]
    seen: set[tuple[int, int]] = set()
    while stack:
        cell = stack.pop()
        if cell in seen:
            continue
        seen.add(cell)
        r, c = cell
        for neighbor in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
            if neighbor in remaining and neighbor not in seen:
                stack.append(neighbor)
    return seen == remaining


def _enumerate_families(cell_count: int) -> tuple[tuple[tuple[int, int], ...], ...]:
    """All connected D4 classes of ``cell_count`` cells in a 3x3 panel."""
    by_canon: dict[tuple[tuple[int, int], ...], tuple[tuple[int, int], ...]] = {}
    positions = tuple((r, c) for r in range(3) for c in range(3))
    for subset in combinations(positions, cell_count):
        if not _connected(subset):
            continue
        normalized = tuple(_normalize(subset))
        canon = _dihedral_canon(normalized)
        by_canon.setdefault(canon, normalized)
    return tuple(sorted(by_canon))


_FAMILIES = {count: _enumerate_families(count) for count in (4, 5, 6)}
_FULL_ORBIT_FAMILIES = {
    count: tuple(shape for shape in families if len(_orbit(shape)) == 8)
    for count, families in _FAMILIES.items()
}
if any(len(_FAMILIES[count]) < 3 or not _FULL_ORBIT_FAMILIES[count] for count in (4, 5, 6)):
    raise AssertionError("3x3 shape census cannot support the declared curriculum")


def schedule_profile(seed: int, sample_index: int, difficulty: str | None = None) -> tuple[int, str]:
    """Return the deterministic joint semantic profile for an example."""
    del seed, difficulty
    return sample_index % 3, _SCHEDULE_CODES[sample_index % len(_SCHEDULE_CODES)]


SCHEDULE_PROFILES = tuple((index, code) for index in range(3) for code in _CODES)


def _choose_prototypes(rng, cell_count: int, match_index: int) -> list[list[tuple[int, int]]]:
    matched_family = rng.choice(_FULL_ORBIT_FAMILIES[cell_count])
    distractor_pool = [
        shape for shape in _FAMILIES[cell_count]
        if _dihedral_canon(shape) != _dihedral_canon(matched_family)
    ]
    distractors = rng.sample(distractor_pool, 2)
    families: list[tuple[tuple[int, int], ...] | None] = [None, None, None]
    families[match_index] = matched_family
    cursor = 0
    for index in range(3):
        if families[index] is None:
            families[index] = distractors[cursor]
            cursor += 1
    return [
        _xform(shape, rng.choice(_CODES))
        for shape in families
        if shape is not None
    ]


def _paint_panel(grid: list[list[int]], panel: int, cells: Iterable[tuple[int, int]], color: int) -> None:
    left = panel * 4
    for r, c in cells:
        grid[r][left + c] = color


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in _BAND_CELL_COUNTS:
        raise ValueError(f"unknown difficulty: {difficulty!r}; expected easy, medium, hard, or None")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))

    scheduled_index, scheduled_transform = schedule_profile(seed, sample_index, difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    # Consume each axis exactly once.  Explicit overrides see the whole
    # declared domain; natural draws see the one scheduled curriculum point.
    if "match_index" in overrides:
        match_index = ctx.draw_int("match_index", 0, 2)
    else:
        match_index = ctx.draw_choice("match_index", (scheduled_index,))
    if "transform" in overrides:
        transform = ctx.draw_choice("transform", _CODES)
    else:
        transform = ctx.draw_choice("transform", (scheduled_transform,))
    if "cell_count" in overrides:
        cell_count = ctx.draw_int("cell_count", 4, 6)
    else:
        cell_count = ctx.draw_choice("cell_count", (_BAND_CELL_COUNTS[difficulty],))

    shape_rng = ctx.draw_rng("prototype_families")
    prototypes = _choose_prototypes(shape_rng, cell_count, match_index)
    colors = list(ctx.draw_distinct_colors("panel_colors", n=4, exclude=(0, 5)))

    grid = full_grid(3, 15, 0)
    for separator in (3, 7, 11):
        for row in range(3):
            grid[row][separator] = 5
    for index, shape in enumerate(prototypes):
        _paint_panel(grid, index, shape, colors[index])
    _paint_panel(grid, 3, _xform(prototypes[match_index], transform), colors[3])

    requested = {
        "cell_count": cell_count,
        "match_index": match_index,
        "transform": transform,
    }
    errors = self_check(grid, difficulty=difficulty, meta={"overrides": requested})
    if errors:
        raise AssertionError(f"internal invalid generation: {errors}")
    return grid


def _grid_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or len(grid) != 3:
        return ["expected exactly 3 rows"]
    if any(not isinstance(row, (list, tuple)) or len(row) != 15 for row in grid):
        return ["expected exactly 15 columns in every row"]
    errors: list[str] = []
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                errors.append(f"cell ({r},{c}) is not an ARC color integer")
    return errors


def _panel_data(grid: Any, panel: int) -> dict[str, Any]:
    left = panel * 4
    cells: list[tuple[int, int]] = []
    colors: set[int] = set()
    for r in range(3):
        for c in range(3):
            value = grid[r][left + c]
            if value != 0:
                cells.append((r, c))
                colors.add(value)
    normalized = _normalize(cells)
    return {
        "cells": normalized,
        "raw_cells": sorted(cells),
        "colors": tuple(sorted(colors)),
        "color": next(iter(colors)) if len(colors) == 1 else None,
        "count": len(cells),
        "connected": _connected(normalized),
    }


def _analysis(grid: Any) -> dict[str, Any]:
    errors = _grid_errors(grid)
    result: dict[str, Any] = {"errors": errors}
    if errors:
        return result

    for separator in (3, 7, 11):
        if any(grid[row][separator] != 5 for row in range(3)):
            errors.append(f"separator column {separator} is not solid color 5")
    for r in range(3):
        for c in range(15):
            if c not in (3, 7, 11) and grid[r][c] == 5:
                errors.append(f"color 5 leaked into panel cell ({r},{c})")

    panels = [_panel_data(grid, panel) for panel in range(4)]
    for panel, data in enumerate(panels):
        label = "query" if panel == 3 else f"prototype panel {panel}"
        if not data["cells"]:
            errors.append(f"{label} is empty")
        if len(data["colors"]) != 1:
            errors.append(f"{label} has {len(data['colors'])} colors, expected 1")
        if data["cells"] and not data["connected"]:
            errors.append(f"{label} is not 4-connected")
        if not 3 <= data["count"] <= 6:
            errors.append(f"{label} has {data['count']} cells, expected 3..6")

    prototypes = panels[:3]
    query = panels[3]
    if all(proto["cells"] for proto in prototypes):
        canons = [_dihedral_canon(proto["cells"]) for proto in prototypes]
        if len(set(canons)) != 3:
            errors.append("prototype shapes are not pairwise D4-distinct")

    matches: list[tuple[int, tuple[str, ...]]] = []
    if query["cells"]:
        for index, prototype in enumerate(prototypes):
            codes = tuple(
                code for code in _CODES
                if _xform(prototype["cells"], code) == query["cells"]
            )
            if codes:
                matches.append((index, codes))
    if len(matches) != 1:
        errors.append(f"query shape matches {len(matches)} prototypes under D4, expected 1")

    counts = tuple(int(proto["count"]) for proto in prototypes)
    matched_index = matches[0][0] if len(matches) == 1 else None
    matched_codes = matches[0][1] if len(matches) == 1 else ()
    cell_count = (
        counts[0]
        if len(set(counts + (query["count"],))) == 1
        else None
    )
    result.update(
        {
            "errors": errors,
            "panels": panels,
            "prototype_cells": tuple(tuple(proto["cells"]) for proto in prototypes),
            "prototype_counts": counts,
            "prototype_colors": tuple(proto["color"] for proto in prototypes),
            "query_cells": tuple(query["cells"]),
            "query_count": query["count"],
            "query_color": query["color"],
            "matched_index": matched_index,
            "matched_codes": matched_codes,
            "matched_transform_count": len(matched_codes),
            "transform": matched_codes[0] if len(matched_codes) == 1 else None,
            "cell_count": cell_count,
        }
    )
    return result


def semantic_observables(grid: Any) -> dict[str, Any]:
    """Expose rule-relevant facts without hidden generator metadata."""
    return _analysis(grid)


def observe_overrides(grid: Any) -> dict[str, int | str]:
    facts = _analysis(grid)
    if facts["errors"]:
        raise ValueError("; ".join(facts["errors"]))
    if facts["cell_count"] is None:
        raise ValueError("cell_count is not uniquely observable")
    if facts["matched_index"] is None:
        raise ValueError("match_index is not uniquely observable")
    if facts["transform"] is None:
        raise ValueError("transform is not uniquely observable")
    return {
        "cell_count": int(facts["cell_count"]),
        "match_index": int(facts["matched_index"]),
        "transform": str(facts["transform"]),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty
    facts = _analysis(grid)
    errors = list(facts["errors"])
    if errors:
        return errors
    if meta and isinstance(meta, dict) and isinstance(meta.get("overrides"), dict):
        requested = meta["overrides"]
        try:
            observed = observe_overrides(grid)
        except ValueError as exc:
            errors.append(str(exc))
        else:
            for key, expected in requested.items():
                if key in AXES and observed.get(key) != expected:
                    errors.append(
                        f"override {key}={expected!r} realized as {observed.get(key)!r}"
                    )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """The selected rule's complete input grammar for this fixed panel layout."""
    return self_check(grid)


def _support_grid(cells: Iterable[tuple[int, int]], color: int) -> list[list[int]]:
    normalized = _normalize(cells)
    if not normalized:
        return [[0]]
    height, width = _dims(normalized)
    output = full_grid(height, width, 0)
    for r, c in normalized:
        output[r][c] = color
    return output


def rule_mirror(grid: Any) -> list[list[int]]:
    """Pure Python mirror of the selected Racket authority."""
    facts = _analysis(grid)
    if facts["errors"]:
        raise ValueError("; ".join(facts["errors"]))
    index = int(facts["matched_index"])
    return _support_grid(facts["prototype_cells"][index], int(facts["query_color"]))


def _panel_output(grid: Any, index: int, *, use_query_color: bool = True) -> list[list[int]]:
    facts = _analysis(grid)
    if facts["errors"]:
        raise ValueError("; ".join(facts["errors"]))
    color = facts["query_color"] if use_query_color else facts["prototype_colors"][index]
    return _support_grid(facts["prototype_cells"][index], int(color))


def _rival_panel(index: int) -> Callable[[Any], list[list[int]]]:
    return lambda grid: _panel_output(grid, index)


def _rival_same_count_leftmost(grid: Any) -> list[list[int]]:
    facts = _analysis(grid)
    if facts["errors"]:
        raise ValueError("; ".join(facts["errors"]))
    query_count = int(facts["query_count"])
    index = next(
        (i for i, count in enumerate(facts["prototype_counts"]) if count == query_count),
        0,
    )
    return _panel_output(grid, index)


def _rival_rotations_only_then_query(grid: Any) -> list[list[int]]:
    facts = _analysis(grid)
    if facts["errors"]:
        raise ValueError("; ".join(facts["errors"]))
    query = list(facts["query_cells"])
    for index, prototype in enumerate(facts["prototype_cells"]):
        if any(_xform(prototype, code) == query for code in _ROTATION_CODES):
            return _panel_output(grid, index)
    return _support_grid(query, int(facts["query_color"]))


def _rival_copy_query_orientation(grid: Any) -> list[list[int]]:
    facts = _analysis(grid)
    if facts["errors"]:
        raise ValueError("; ".join(facts["errors"]))
    return _support_grid(facts["query_cells"], int(facts["query_color"]))


def _rival_keep_prototype_color(grid: Any) -> list[list[int]]:
    facts = _analysis(grid)
    if facts["errors"]:
        raise ValueError("; ".join(facts["errors"]))
    return _panel_output(grid, int(facts["matched_index"]), use_query_color=False)


SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "always_panel_0": _rival_panel(0),
    "always_panel_1": _rival_panel(1),
    "always_panel_2": _rival_panel(2),
    "same_count_leftmost": _rival_same_count_leftmost,
    "rotations_only_then_query": _rival_rotations_only_then_query,
    "copy_query_orientation": _rival_copy_query_orientation,
    "keep_prototype_color": _rival_keep_prototype_color,
}
CANONICAL_SHORTCUTS = {"same_count_leftmost": _rival_same_count_leftmost}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def _fact(grid: Any, key: str, default: Any = None) -> Any:
    return semantic_observables(grid).get(key, default)


SEMANTIC_WITNESSES: dict[str, Callable[[Any], bool]] = {
    # These two broad obligations keep the authoritative-oracle cost bounded:
    # each firing is checked against several named rivals in one bridge call.
    "selection_shortcuts_refuted": lambda grid: not bool(_fact(grid, "errors", ["invalid"])),
    "transform_and_color_shortcuts_refuted": lambda grid: not bool(
        _fact(grid, "errors", ["invalid"])
    ),
}
WITNESS_RIVALS = {
    "selection_shortcuts_refuted": (
        "always_panel_0",
        "always_panel_1",
        "always_panel_2",
        "same_count_leftmost",
    ),
    "transform_and_color_shortcuts_refuted": (
        "rotations_only_then_query",
        "copy_query_orientation",
        "keep_prototype_color",
    ),
}

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0


def _pair_errors(pair: Any, label: str) -> list[str]:
    if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
        return [f"{label} is malformed"]
    errors = self_check(pair["input"])
    if errors:
        return [f"{label} input invalid: {errors[0]}"]
    try:
        official = rule_mirror(pair["input"])
    except ValueError as exc:
        return [f"{label} mirror failed: {exc}"]
    if official != pair["output"]:
        return [f"{label} output does not follow the selected rule"]
    return []


def lesson_identifiable(demos, query) -> list[str]:
    """Require a three-example lesson to falsify the declared rival rules."""
    if not isinstance(demos, list) or len(demos) < EXAMPLES_NEEDED:
        return [f"lesson needs at least {EXAMPLES_NEEDED} demonstrations"]
    errors: list[str] = []
    for index, pair in enumerate(demos):
        errors.extend(_pair_errors(pair, f"demo {index}"))
    errors.extend(_pair_errors(query, "query"))
    if errors:
        return errors

    match_indices = {
        int(semantic_observables(pair["input"])["matched_index"])
        for pair in demos
    }
    if match_indices != {0, 1, 2}:
        errors.append("demonstrations must cover all three prototype positions")

    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            errors.append(f"surviving lesson shortcut: {name}")
    return errors


def mutation_fixtures() -> list[tuple[str, list[list[int]]]]:
    """Task-local near-misses that the validator must reject."""
    grid = generate(991, 0, difficulty="easy")
    broken_separator = [list(row) for row in grid]
    broken_separator[0][3] = 0

    duplicate_prototype = [list(row) for row in grid]
    for r in range(3):
        for c in range(3):
            duplicate_prototype[r][4 + c] = duplicate_prototype[r][c]

    return [
        ("broken_separator", broken_separator),
        ("duplicate_prototype", duplicate_prototype),
    ]
