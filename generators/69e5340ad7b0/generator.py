"""Generator for ``arc_additional_puzzles_21_set5:M33``.

The top-left cell is a command: blue (1) mirrors the remaining pattern across
its vertical axis, while red (2) mirrors it across its horizontal axis.  The
source pattern remains in place and the command cell is preserved.

Every four consecutive examples cover both commands, connected and split
source patterns, and a case where the command color also appears inside the
pattern.  That schedule makes command-blind, one-component, color-blind, and
"move instead of overlay" shortcuts observable at lesson level.
"""
from __future__ import annotations

from collections import deque
from typing import Any, Callable

from puzzle_generators.base import gen_ctx, stable_rng
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "69e5340ad7b0"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "11100ad09fdb"
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "Read the command at (0,0). Command 1 overlays a left-right reflection of "
    "every other nonzero cell; command 2 overlays an up-down reflection. "
    "Preserve the source pattern, every cell color, and the command cell."
)

INVARIANTS = [
    "the grid is rectangular and uses ARC colors 0..9",
    "cell (0,0) is command 1 or 2 and is preserved by the rule",
    "a 6..12-cell, 2..4-color source pattern lies strictly on the command-selected source side",
    "the source pattern has one or two cardinal components and spans at least three rows and columns",
    "every reflected target is in-bounds, empty, and disjoint from the source pattern",
]

SCENE_PROFILES = (
    "cmd1_connected_cmdcolor",
    "cmd2_split_no_cmdcolor",
    "cmd1_split_no_cmdcolor",
    "cmd2_connected_no_cmdcolor",
)
SCHEDULE_PROFILES = SCENE_PROFILES
CANONICAL_PROFILES = (
    (8, 10, 3),
    (9, 11, 4),
    (10, 12, 4),
    (8, 9, 4),
    (10, 11, 4),
)
DIFFICULTIES = {None, "default", "easy", "medium", "hard"}

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "four-example semantic schedule",
        "valid": "|".join(SCENE_PROFILES),
        "doc": "command, source component count, and command-color recurrence",
    },
    "grid_h": {
        "type": "int",
        "default": "difficulty-aware with scheduled canonical anchors",
        "valid": "8..14",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-aware with scheduled canonical anchors",
        "valid": "9..16",
    },
    "motif_cells": {
        "type": "int",
        "default": "difficulty-aware",
        "valid": "6..12",
    },
    "motif_colors": {
        "type": "int",
        "default": "difficulty-aware",
        "valid": "2..4",
    },
}

_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _normalize_grid(grid: Any) -> tuple[list[list[int]] | None, list[str]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return None, ["grid must be a nonempty row sequence"]
    if not all(isinstance(row, (list, tuple)) and row for row in grid):
        return None, ["rows must be nonempty sequences"]
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return None, ["grid must be rectangular"]
    copied = [list(row) for row in grid]
    if any(
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 0 <= value <= 9
        for row in copied
        for value in row
    ):
        return None, ["cells must be integer ARC colors 0..9"]
    return copied, []


def _neighbors(cell: tuple[int, int]) -> tuple[tuple[int, int], ...]:
    row, col = cell
    return tuple((row + dr, col + dc) for dr, dc in _CARDINAL)


def _components(cells: set[tuple[int, int]]) -> list[set[tuple[int, int]]]:
    remaining = set(cells)
    result: list[set[tuple[int, int]]] = []
    while remaining:
        root = min(remaining)
        remaining.remove(root)
        component = {root}
        queue = deque([root])
        while queue:
            cell = queue.popleft()
            for neighbor in _neighbors(cell):
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    component.add(neighbor)
                    queue.append(neighbor)
        result.append(component)
    return sorted(result, key=lambda component: min(component))


def _profile_facts(profile: str) -> tuple[int, int, bool]:
    if profile not in SCENE_PROFILES:
        raise ValueError(f"unknown scene profile {profile!r}")
    command = 1 if profile.startswith("cmd1_") else 2
    component_count = 2 if "_split_" in profile else 1
    command_in_motif = profile.endswith("_cmdcolor") and not profile.endswith("_no_cmdcolor")
    return command, component_count, command_in_motif


def _scene_profile(command: int, component_count: int, command_in_motif: bool) -> str | None:
    candidate = (
        f"cmd{command}_"
        f"{'split' if component_count == 2 else 'connected'}_"
        f"{'cmdcolor' if command_in_motif else 'no_cmdcolor'}"
    )
    return candidate if candidate in SCENE_PROFILES else None


def _source_domain(height: int, width: int, command: int) -> set[tuple[int, int]]:
    if command == 1:
        domain = {(row, col) for row in range(height) for col in range(width // 2)}
    else:
        domain = {(row, col) for row in range(height // 2) for col in range(width)}
    domain.discard((0, 0))
    return domain


def _mirror_cell(
    cell: tuple[int, int], height: int, width: int, command: int
) -> tuple[int, int]:
    row, col = cell
    return (row, width - 1 - col) if command == 1 else (height - 1 - row, col)


def _bbox_spans(cells: set[tuple[int, int]]) -> tuple[int, int]:
    rows = [row for row, _ in cells]
    cols = [col for _, col in cells]
    return max(rows) - min(rows) + 1, max(cols) - min(cols) + 1


def _analyze(grid: Any) -> dict[str, Any]:
    normalized, errors = _normalize_grid(grid)
    result: dict[str, Any] = {"errors": errors, "facts": None}
    if normalized is None:
        return result

    height = len(normalized)
    width = len(normalized[0])
    if not 8 <= height <= 14:
        errors.append(f"grid height must be in 8..14, got {height}")
    if not 9 <= width <= 16:
        errors.append(f"grid width must be in 9..16, got {width}")

    command = normalized[0][0]
    if command not in (1, 2):
        errors.append(f"cell (0,0) must be command 1 or 2, got {command}")

    motif = {
        (row, col)
        for row, values in enumerate(normalized)
        for col, value in enumerate(values)
        if value != 0 and (row, col) != (0, 0)
    }
    motif_colors = {
        normalized[row][col]
        for row, col in motif
    }
    if not 6 <= len(motif) <= 12:
        errors.append(f"source pattern must contain 6..12 cells, got {len(motif)}")
    if not 2 <= len(motif_colors) <= 4:
        errors.append(
            f"source pattern must use 2..4 colors, got {len(motif_colors)}"
        )

    components = _components(motif) if motif else []
    if len(components) not in (1, 2):
        errors.append(
            f"source pattern must have one or two cardinal components, got {len(components)}"
        )
    if len(components) == 2 and any(len(component) < 3 for component in components):
        errors.append("each split source component must contain at least three cells")

    if motif:
        row_span, col_span = _bbox_spans(motif)
        if row_span < 3 or col_span < 3:
            errors.append(
                f"source pattern must span at least three rows and columns, got {row_span}x{col_span}"
            )

    if command in (1, 2):
        legal_domain = _source_domain(height, width, command)
        off_side = sorted(motif - legal_domain)
        if off_side:
            errors.append(
                f"source cell {off_side[0]} is not strictly on the command-selected source side"
            )
        for cell in sorted(motif):
            mirror = _mirror_cell(cell, height, width, command)
            mr, mc = mirror
            if not (0 <= mr < height and 0 <= mc < width):
                errors.append(f"mirror target {mirror} is out of bounds")
                break
            if normalized[mr][mc] != 0:
                errors.append(f"mirror target {mirror} is already occupied")
                break

    command_in_motif = command in motif_colors if command in (1, 2) else False
    profile = (
        _scene_profile(command, len(components), command_in_motif)
        if command in (1, 2) and len(components) in (1, 2)
        else None
    )
    if motif and profile is None:
        errors.append(
            "command/component/command-color combination is outside the declared scene profiles"
        )

    if not errors:
        result["facts"] = {
            "height": height,
            "width": width,
            "command": command,
            "motif": frozenset(motif),
            "motif_cells": len(motif),
            "motif_colors": frozenset(motif_colors),
            "motif_color_count": len(motif_colors),
            "components": tuple(frozenset(component) for component in components),
            "component_count": len(components),
            "command_in_motif": command_in_motif,
            "scene_profile": profile,
        }
    return result


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed, ambiguous, or shortcut-hiding source scenes."""
    del difficulty, meta
    return list(_analyze(grid)["errors"])


def strict_canonical_like(grid) -> list[str]:
    """Task-linked manifold shared by canonical and generated examples."""
    return list(_analyze(grid)["errors"])


def observe_overrides(grid: Any) -> dict[str, Any]:
    """Recover every declared exact axis from the returned grid."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("cannot observe axes: " + "; ".join(analysis["errors"]))
    facts = analysis["facts"]
    return {
        "scene_profile": facts["scene_profile"],
        "grid_h": facts["height"],
        "grid_w": facts["width"],
        "motif_cells": facts["motif_cells"],
        "motif_colors": facts["motif_color_count"],
    }


def rule_mirror(grid: Any, *, forced_command: int | None = None) -> list[list[int]]:
    """Python diagnostic mirror; canonical Racket remains output authority."""
    normalized, errors = _normalize_grid(grid)
    if normalized is None or errors:
        raise ValueError("; ".join(errors))
    height = len(normalized)
    width = len(normalized[0])
    command = normalized[0][0] if forced_command is None else forced_command
    if command not in (1, 2):
        raise ValueError(f"invalid mirror command {command!r}")
    output = [row[:] for row in normalized]
    output[0][0] = 0
    for row in range(height):
        for col in range(width):
            value = normalized[row][col]
            if (row, col) == (0, 0) or value == 0:
                continue
            mr, mc = _mirror_cell((row, col), height, width, command)
            output[mr][mc] = value
    output[0][0] = normalized[0][0]
    return output


def _identity(grid: Any) -> list[list[int]]:
    normalized, errors = _normalize_grid(grid)
    if normalized is None or errors:
        raise ValueError("; ".join(errors))
    return [row[:] for row in normalized]


def _mirror_subset(
    grid: Any,
    predicate: Callable[[int, int, int, dict[str, Any]], bool],
) -> list[list[int]]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    normalized, _ = _normalize_grid(grid)
    assert normalized is not None
    facts = analysis["facts"]
    output = [row[:] for row in normalized]
    for row, col in facts["motif"]:
        value = normalized[row][col]
        if predicate(row, col, value, facts):
            mr, mc = _mirror_cell(
                (row, col), facts["height"], facts["width"], facts["command"]
            )
            output[mr][mc] = value
    return output


def _first_component_only(grid: Any) -> list[list[int]]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    first = set(analysis["facts"]["components"][0])
    return _mirror_subset(grid, lambda row, col, value, facts: (row, col) in first)


def _first_color_only(grid: Any) -> list[list[int]]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    first = min(analysis["facts"]["motif_colors"])
    return _mirror_subset(grid, lambda row, col, value, facts: value == first)


def _skip_command_color(grid: Any) -> list[list[int]]:
    return _mirror_subset(
        grid, lambda row, col, value, facts: value != facts["command"]
    )


def _recolor_mirror_with_command(grid: Any) -> list[list[int]]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    normalized, _ = _normalize_grid(grid)
    assert normalized is not None
    facts = analysis["facts"]
    output = [row[:] for row in normalized]
    for cell in facts["motif"]:
        mr, mc = _mirror_cell(
            cell, facts["height"], facts["width"], facts["command"]
        )
        output[mr][mc] = facts["command"]
    return output


def _move_instead_of_overlay(grid: Any) -> list[list[int]]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    normalized, _ = _normalize_grid(grid)
    assert normalized is not None
    facts = analysis["facts"]
    output = [row[:] for row in normalized]
    for row, col in facts["motif"]:
        output[row][col] = 0
    for row, col in facts["motif"]:
        mr, mc = _mirror_cell(
            (row, col), facts["height"], facts["width"], facts["command"]
        )
        output[mr][mc] = normalized[row][col]
    return output


def _drop_command_cell(grid: Any) -> list[list[int]]:
    output = rule_mirror(grid)
    output[0][0] = 0
    return output


def _mirror_bbox(grid: Any) -> list[list[int]]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    normalized, _ = _normalize_grid(grid)
    assert normalized is not None
    facts = analysis["facts"]
    output = [row[:] for row in normalized]
    rows = [row for row, _ in facts["motif"]]
    cols = [col for _, col in facts["motif"]]
    fill = min(facts["motif_colors"])
    for row in range(min(rows), max(rows) + 1):
        for col in range(min(cols), max(cols) + 1):
            mr, mc = _mirror_cell(
                (row, col), facts["height"], facts["width"], facts["command"]
            )
            output[mr][mc] = fill
    return output


SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "identity": _identity,
    "always_left_right": lambda grid: rule_mirror(grid, forced_command=1),
    "always_up_down": lambda grid: rule_mirror(grid, forced_command=2),
    "first_component_only": _first_component_only,
    "first_color_only": _first_color_only,
    "skip_command_color_inside_pattern": _skip_command_color,
    "recolor_mirror_with_command": _recolor_mirror_with_command,
    "move_instead_of_overlay": _move_instead_of_overlay,
    "drop_command_cell": _drop_command_cell,
    "mirror_filled_bounding_box": _mirror_bbox,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def _fact_predicate(name: str, expected: Any) -> Callable[[Any], bool]:
    def predicate(grid: Any) -> bool:
        analysis = _analyze(grid)
        return bool(
            not analysis["errors"]
            and analysis["facts"].get(name) == expected
        )

    return predicate


def _visible_multicolor_overlay(grid: Any) -> bool:
    analysis = _analyze(grid)
    if analysis["errors"]:
        return False
    return (
        analysis["facts"]["motif_color_count"] >= 2
        and rule_mirror(grid) != _identity(grid)
    )


SEMANTIC_WITNESSES = {
    "command_1_left_right": _fact_predicate("command", 1),
    "command_2_up_down": _fact_predicate("command", 2),
    "connected_source_pattern": _fact_predicate("component_count", 1),
    "split_source_pattern": _fact_predicate("component_count", 2),
    "command_color_reused_in_pattern": _fact_predicate("command_in_motif", True),
    "visible_multicolor_overlay": _visible_multicolor_overlay,
}

WITNESS_RIVALS = {
    "command_1_left_right": ["always_up_down"],
    "command_2_up_down": ["always_left_right"],
    "connected_source_pattern": ["first_color_only", "mirror_filled_bounding_box"],
    "split_source_pattern": ["first_component_only"],
    "command_color_reused_in_pattern": ["skip_command_color_inside_pattern"],
    "visible_multicolor_overlay": [
        "identity",
        "recolor_mirror_with_command",
        "move_instead_of_overlay",
        "drop_command_cell",
    ],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject a lesson when a named shortcut survives all demonstrations."""
    reasons: list[str] = []
    for index, pair in enumerate([*demos, query]):
        role = f"demo {index}" if index < len(demos) else "query"
        if not isinstance(pair, dict) or "input" not in pair:
            reasons.append(f"{role} is missing an input grid")
            continue
        errors = strict_canonical_like(pair["input"])
        if errors:
            reasons.append(f"{role} input is not canonical-like: {errors[0]}")
            continue
        expected = rule_mirror(pair["input"])
        if pair.get("output", expected) != expected:
            reasons.append(f"{role} output does not match command-selected mirror overlay")

    for name, competitor in LESSON_COMPETITORS.items():
        survives = True
        for demo in demos:
            try:
                prediction = competitor(demo["input"])
            except Exception:
                survives = False
                break
            if prediction != demo["output"]:
                survives = False
                break
        if survives:
            try:
                query_prediction = competitor(query["input"])
                query_expected = query.get("output", rule_mirror(query["input"]))
            except Exception:
                continue
            if query_prediction != query_expected:
                reasons.append(
                    f"named rival {name!r} matches every demo but changes the query answer"
                )
    return reasons


def schedule_profile(seed, sample_index, difficulty=None):
    del seed, difficulty
    return SCENE_PROFILES[int(sample_index) % len(SCENE_PROFILES)]


def _difficulty_band(difficulty: Any) -> str:
    band = "medium" if difficulty in (None, "default") else difficulty
    if band not in {"easy", "medium", "hard"}:
        raise ValueError(f"unknown difficulty {difficulty!r}")
    return band


def _ordinary_defaults(seed: int, sample_index: int, band: str) -> dict[str, Any]:
    profile = schedule_profile(seed, sample_index, band)
    command, component_count, command_in_motif = _profile_facts(profile)
    del command, component_count

    # Every four consecutive sample indexes contain one exact canonical
    # (height, width, palette-size) anchor, in every difficulty band.
    if sample_index % EXAMPLES_NEEDED == 0:
        anchor_rng = stable_rng(
            seed,
            f"{TASK_ID}|{sample_index}|canonical-profile",
            VERSION,
        )
        height, width, total_palette = anchor_rng.choice(CANONICAL_PROFILES)
        motif_colors = total_palette - (1 if command_in_motif else 2)
        motif_colors = max(2, min(4, motif_colors))
        motif_cells = anchor_rng.choice((6, 7, 8))
        return {
            "scene_profile": profile,
            "grid_h": height,
            "grid_w": width,
            "motif_cells": motif_cells,
            "motif_colors": motif_colors,
        }

    rng = stable_rng(seed, f"{TASK_ID}|{sample_index}|defaults|{band}", VERSION)
    ranges = {
        "easy": ((8, 10), (9, 12), (6, 8), (2, 2)),
        "medium": ((9, 12), (10, 14), (7, 10), (2, 3)),
        "hard": ((10, 14), (11, 16), (9, 12), (3, 4)),
    }
    (h_lo, h_hi), (w_lo, w_hi), (n_lo, n_hi), (c_lo, c_hi) = ranges[band]
    return {
        "scene_profile": profile,
        "grid_h": rng.randint(h_lo, h_hi),
        "grid_w": rng.randint(w_lo, w_hi),
        "motif_cells": rng.randint(n_lo, n_hi),
        "motif_colors": rng.randint(c_lo, c_hi),
    }


def _partition_sizes(total: int, component_count: int, rng) -> tuple[int, ...]:
    if component_count == 1:
        return (total,)
    first = rng.randint(3, total - 3)
    return (first, total - first)


def _grow_component(
    rng,
    allowed: set[tuple[int, int]],
    size: int,
) -> set[tuple[int, int]] | None:
    if len(allowed) < size:
        return None
    seed = rng.choice(sorted(allowed))
    component = {seed}
    while len(component) < size:
        frontier = sorted(
            {
                neighbor
                for cell in component
                for neighbor in _neighbors(cell)
                if neighbor in allowed and neighbor not in component
            }
        )
        if not frontier:
            return None
        component.add(rng.choice(frontier))
    return component


def _construct_components(
    rng,
    height: int,
    width: int,
    command: int,
    motif_cells: int,
    component_count: int,
) -> tuple[set[tuple[int, int]], ...]:
    domain = _source_domain(height, width, command)
    sizes = _partition_sizes(motif_cells, component_count, rng)
    for _attempt in range(500):
        components: list[set[tuple[int, int]]] = []
        failed = False
        for size in sizes:
            forbidden: set[tuple[int, int]] = set()
            for prior in components:
                forbidden.update(prior)
                for cell in prior:
                    forbidden.update(_neighbors(cell))
            component = _grow_component(rng, domain - forbidden, size)
            if component is None:
                failed = True
                break
            components.append(component)
        if failed:
            continue
        cells = set().union(*components)
        row_span, col_span = _bbox_spans(cells)
        if row_span < 3 or col_span < 3:
            continue
        lr = {_mirror_cell(cell, height, width, 1) for cell in cells}
        ud = {_mirror_cell(cell, height, width, 2) for cell in cells}
        if lr == ud:
            continue
        return tuple(components)
    raise ValueError(
        f"could not construct {component_count} component(s) with {motif_cells} cells in {height}x{width}"
    )


def _paint_components(
    grid: list[list[int]],
    components: tuple[set[tuple[int, int]], ...],
    *,
    command: int,
    motif_color_count: int,
    command_in_motif: bool,
    rng,
) -> None:
    legal = list(range(1, 10))
    if command_in_motif:
        others = [color for color in legal if color != command]
        palette = [command, *rng.sample(others, motif_color_count - 1)]
    else:
        palette = rng.sample(
            [color for color in legal if color != command], motif_color_count
        )

    cells = sorted(set().union(*components))
    rng.shuffle(cells)
    assignments = list(palette)
    assignments.extend(rng.choice(palette) for _ in range(len(cells) - len(palette)))
    rng.shuffle(assignments)
    for cell, color in zip(cells, assignments):
        row, col = cell
        grid[row][col] = color


def _validate_override_keys(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_override_keys(overrides)
    band = _difficulty_band(difficulty)
    explicit = any(value is not None for value in overrides.values())
    defaults = _ordinary_defaults(int(seed), int(sample_index), band)
    effective = dict(defaults)
    effective.update({key: value for key, value in overrides.items() if value is not None})

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=effective,
    )
    scene_profile = ctx.draw_choice("scene_profile", SCENE_PROFILES)
    height = ctx.draw_int("grid_h", 8, 14)
    width = ctx.draw_int("grid_w", 9, 16)
    motif_cells = ctx.draw_int("motif_cells", 6, 12)
    motif_colors = ctx.draw_int("motif_colors", 2, 4)
    command, component_count, command_in_motif = _profile_facts(scene_profile)

    layout_rng = ctx.draw_rng("layout")
    components = _construct_components(
        layout_rng,
        height,
        width,
        command,
        motif_cells,
        component_count,
    )
    grid = full_grid(height, width, 0)
    grid[0][0] = command
    _paint_components(
        grid,
        components,
        command=command,
        motif_color_count=motif_colors,
        command_in_motif=command_in_motif,
        rng=ctx.draw_rng("palette"),
    )

    errors = self_check(grid, difficulty=band)
    if errors:
        qualifier = "explicit override" if explicit else "ordinary draw"
        raise AssertionError(
            f"{qualifier} constructed invalid scene: " + "; ".join(errors)
        )
    return [row[:] for row in grid]


def mutation_fixtures() -> list[tuple[str, list[list[int]]]]:
    """Task-linked malformed scenes that the teaching grammar must reject."""
    no_command = full_grid(8, 10, 0)
    for row, col, color in ((2, 1, 3), (2, 2, 4), (3, 1, 3), (3, 2, 4), (4, 1, 3), (4, 2, 4)):
        no_command[row][col] = color

    no_pattern = full_grid(8, 10, 0)
    no_pattern[0][0] = 1

    occupied_target = full_grid(8, 10, 0)
    occupied_target[0][0] = 1
    for row, col, color in ((2, 1, 3), (2, 2, 4), (3, 1, 3), (3, 2, 4), (4, 1, 3), (4, 2, 4)):
        occupied_target[row][col] = color
    occupied_target[2][8] = 7

    wrong_side = full_grid(8, 10, 0)
    wrong_side[0][0] = 1
    for row, col, color in ((2, 6, 3), (2, 7, 4), (3, 6, 3), (3, 7, 4), (4, 6, 3), (4, 7, 4)):
        wrong_side[row][col] = color

    solid_2x2 = full_grid(8, 10, 0)
    solid_2x2[0][0] = 1
    for row, col, color in ((2, 1, 3), (2, 2, 4), (3, 1, 3), (3, 2, 4)):
        solid_2x2[row][col] = color

    centerline = full_grid(9, 11, 0)
    centerline[0][0] = 1
    for row, col, color in ((2, 2, 3), (2, 3, 4), (3, 2, 3), (3, 3, 4), (4, 2, 3), (4, 5, 4)):
        centerline[row][col] = color

    return [
        ("missing_command", no_command),
        ("missing_source_pattern", no_pattern),
        ("occupied_mirror_target", occupied_target),
        ("pattern_on_wrong_side", wrong_side),
        ("undersized_solid_2x2", solid_2x2),
        ("self_mirroring_centerline_cell", centerline),
    ]
