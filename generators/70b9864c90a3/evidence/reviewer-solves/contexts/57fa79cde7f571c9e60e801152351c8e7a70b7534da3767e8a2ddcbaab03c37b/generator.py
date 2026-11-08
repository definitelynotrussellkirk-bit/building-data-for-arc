"""Generator for ``70b9864c90a3`` — diagonal-cross center completion.

The authoritative rule fills a black center only when all four diagonal
neighbors share one nonzero color.  Ordinary generated lessons contain
multiple positive crosses plus one controlled negative distractor.  Motifs are
packed at varied coordinates, color reuse is deliberately de-correlated from
distractor type, and one example per three-sample window adds an irrelevant
orthogonal context pair.  Together those branches distinguish the real rule
from count-, context-, color-, and fixed-layout shortcuts that fit the
canonical examples.
"""
from __future__ import annotations

from collections import Counter
from typing import Iterable

from puzzle_generators.base import gen_ctx, stable_rng
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "70b9864c90a3"
TASK_ID = "70b9864c90a3"
VERSION = "3.1.0"
RULE_HASH = "3de95ecac741"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "A 0-background grid contains two or three blank centers whose four "
    "diagonal neighbors share one nonzero color. The output fills every such "
    "center with that color and preserves all other cells. Each generated "
    "lesson also contains one controlled non-answer: either only three "
    "matching diagonals, four nonzero but mismatched diagonals, or a nonzero "
    "center surrounded by four matching diagonals. Positive motifs move across "
    "the grid, two of every three examples reuse one color, and one example "
    "adds a symmetric orthogonal context pair that must not block the fill."
)

INVARIANTS = [
    "background is 0 and the grid is rectangular with literal ARC colors",
    "two or three blank centers have four equal nonzero diagonal neighbors",
    "positive centers use either one shared color or pairwise-distinct colors",
    "ordinary generated grids contain exactly one controlled negative distractor",
    "at most one active center has one equal-color opposite orthogonal context pair",
    "recognized 3x3 motif footprints are disjoint and cover every nonzero cell",
]

TEXTURES = (
    "mismatched_diagonals",
    "partial_diagonals",
    "blocked_center",
)
HELPFUL_TEXTURES = TEXTURES
COLOR_MODES = ("distinct", "shared")

AXES = {
    "grid_h": {"type": "int", "default": "difficulty-aware 7..17", "valid": "7..17"},
    "grid_w": {"type": "int", "default": "difficulty-aware 7..17", "valid": "7..17"},
    "cross_count": {"type": "int", "default": "2 easy / 2-3 otherwise", "valid": "2..3"},
    "color_mode": {"type": "str", "default": "3-step lesson schedule", "valid": "distinct|shared"},
    "texture": {
        "type": "str",
        "default": "3-step lesson schedule",
        "valid": "mismatched_diagonals|partial_diagonals|blocked_center",
    },
}

SCHEDULE_PROFILES = tuple(
    (texture, color_mode)
    for texture in TEXTURES
    for color_mode in COLOR_MODES
)

_DIAGONALS = ((-1, -1), (-1, 1), (1, -1), (1, 1))
_ORTHOGONALS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _copy_grid(grid):
    return [list(row) for row in grid]


def _grid_errors(grid) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    for row in grid:
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return ["cells must be literal ARC integers 0..9"]
    return []


def _footprint(row: int, col: int) -> set[tuple[int, int]]:
    return {
        (rr, cc)
        for rr in range(row - 1, row + 2)
        for cc in range(col - 1, col + 2)
    }


def _diag_values(grid, row: int, col: int) -> tuple[int, int, int, int]:
    return tuple(grid[row + dr][col + dc] for dr, dc in _DIAGONALS)


def _classify_centers(grid) -> dict[str, list[tuple]]:
    """Return every local predicate-shaped center, including negative controls."""
    height, width = len(grid), len(grid[0])
    found: dict[str, list[tuple]] = {
        "active": [],
        "partial_diagonals": [],
        "mismatched_diagonals": [],
        "blocked_center": [],
    }
    for row in range(1, height - 1):
        for col in range(1, width - 1):
            center = grid[row][col]
            vals = _diag_values(grid, row, col)
            counts = Counter(value for value in vals if value != 0)
            if center == 0 and vals[0] != 0 and all(value == vals[0] for value in vals):
                found["active"].append((row, col, vals[0]))
            elif center == 0 and len(counts) == 1 and sum(counts.values()) == 3 and vals.count(0) == 1:
                color = next(iter(counts))
                found["partial_diagonals"].append((row, col, color))
            elif center == 0 and all(value != 0 for value in vals) and len(set(vals)) > 1:
                found["mismatched_diagonals"].append((row, col, vals))
            elif center != 0 and vals[0] != 0 and all(value == vals[0] for value in vals) and center != vals[0]:
                found["blocked_center"].append((row, col, center, vals[0]))
    return found


def _classify_orthogonal_context(grid, active) -> tuple[list[tuple], list[tuple]]:
    """Return valid opposite context pairs and malformed active-center context.

    A valid context pair occupies north/south or west/east around one active
    center, uses one nonzero color, and differs from the diagonal ring color.
    The pair is deliberately recognizable so a single stray-cell mutation does
    not become valid merely because context variation is supported.
    """
    valid: list[tuple] = []
    invalid: list[tuple] = []
    for row, col, active_color in active:
        values = tuple(grid[row + dr][col + dc] for dr, dc in _ORTHOGONALS)
        nonzero = tuple(index for index, value in enumerate(values) if value != 0)
        if not nonzero:
            continue
        if (
            nonzero in ((0, 1), (2, 3))
            and values[nonzero[0]] == values[nonzero[1]]
            and values[nonzero[0]] != active_color
        ):
            cells = tuple(
                (row + _ORTHOGONALS[index][0], col + _ORTHOGONALS[index][1])
                for index in nonzero
            )
            axis = "vertical" if nonzero == (0, 1) else "horizontal"
            valid.append((row, col, values[nonzero[0]], axis, cells))
        else:
            invalid.append((row, col, values))
    return valid, invalid


def _recognized_nonzero_cells(
    found: dict[str, list[tuple]], context_pairs: Iterable[tuple] = ()
) -> set[tuple[int, int]]:
    covered: set[tuple[int, int]] = set()
    for kind, centers in found.items():
        for entry in centers:
            row, col = entry[0], entry[1]
            for dr, dc in _DIAGONALS:
                covered.add((row + dr, col + dc))
            if kind == "blocked_center":
                covered.add((row, col))
    for entry in context_pairs:
        covered.update(entry[4])
    return covered


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed or shortcut-hiding scenes while accepting canonical inputs."""
    errors = _grid_errors(grid)
    if errors:
        return errors
    height, width = len(grid), len(grid[0])
    if not (7 <= height <= 17 and 7 <= width <= 17):
        errors.append(f"expected dimensions in 7..17, found {height}x{width}")

    found = _classify_centers(grid)
    active = found["active"]
    if not (2 <= len(active) <= 3):
        errors.append(f"expected 2 or 3 active diagonal crosses, found {len(active)}")

    active_colors = [entry[2] for entry in active]
    if active_colors:
        shared = len(set(active_colors)) == 1
        distinct = len(set(active_colors)) == len(active_colors)
        if not (shared or distinct):
            errors.append("active colors must be all shared or pairwise distinct")

    context_pairs, malformed_context = _classify_orthogonal_context(grid, active)
    if malformed_context:
        preview = malformed_context[:2]
        errors.append(f"malformed orthogonal context around active center(s): {preview}")
    if len(context_pairs) > 1:
        errors.append(f"expected at most one orthogonal context pair, found {len(context_pairs)}")

    negative_count = sum(len(found[name]) for name in TEXTURES)
    if negative_count > 1:
        errors.append(f"expected at most one controlled negative distractor, found {negative_count}")

    centers = [entry[:2] for values in found.values() for entry in values]
    footprints: list[set[tuple[int, int]]] = []
    for row, col in centers:
        footprint = _footprint(row, col)
        if any(footprint & previous for previous in footprints):
            errors.append("recognized motif footprints overlap")
            break
        footprints.append(footprint)

    actual_nonzero = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] != 0
    }
    uncovered = actual_nonzero - _recognized_nonzero_cells(found, context_pairs)
    if uncovered:
        preview = sorted(uncovered)[:4]
        errors.append(f"nonzero cells outside recognized motif grammar: {preview}")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Canonical and generated inputs share this exact local-motif grammar."""
    return self_check(grid)


def _apply_rule(grid):
    """Pure Python rendering of the selected Racket rule, used only for rivals/tests."""
    out = _copy_grid(grid)
    height, width = len(grid), len(grid[0])
    for row in range(1, height - 1):
        for col in range(1, width - 1):
            vals = _diag_values(grid, row, col)
            if grid[row][col] == 0 and vals[0] != 0 and all(value == vals[0] for value in vals):
                out[row][col] = vals[0]
    return out


def _rival_first_center_only(grid):
    """Fill only the first valid center in row-major order."""
    out = _copy_grid(grid)
    height, width = len(grid), len(grid[0])
    for row in range(1, height - 1):
        for col in range(1, width - 1):
            vals = _diag_values(grid, row, col)
            if grid[row][col] == 0 and vals[0] != 0 and all(value == vals[0] for value in vals):
                out[row][col] = vals[0]
                return out
    return out


def _rival_one_center_per_color(grid):
    """Shortcut fitting canonical: fill only the first valid center of each color."""
    out = _copy_grid(grid)
    seen: set[int] = set()
    height, width = len(grid), len(grid[0])
    for row in range(1, height - 1):
        for col in range(1, width - 1):
            vals = _diag_values(grid, row, col)
            color = vals[0]
            if (
                grid[row][col] == 0
                and color != 0
                and all(value == color for value in vals)
                and color not in seen
            ):
                out[row][col] = color
                seen.add(color)
    return out


def _rival_ignore_color_equality(grid):
    """Fill any blank center with four nonzero diagonal neighbors."""
    out = _copy_grid(grid)
    height, width = len(grid), len(grid[0])
    for row in range(1, height - 1):
        for col in range(1, width - 1):
            vals = _diag_values(grid, row, col)
            if grid[row][col] == 0 and all(value != 0 for value in vals):
                out[row][col] = vals[0]
    return out


def _rival_three_of_four(grid):
    """Fill when any nonzero color appears on at least three diagonals."""
    out = _copy_grid(grid)
    height, width = len(grid), len(grid[0])
    for row in range(1, height - 1):
        for col in range(1, width - 1):
            if grid[row][col] != 0:
                continue
            counts = Counter(value for value in _diag_values(grid, row, col) if value != 0)
            if counts:
                color, count = counts.most_common(1)[0]
                if count >= 3:
                    out[row][col] = color
    return out


def _rival_overwrite_nonzero_center(grid):
    """Ignore the blank-center condition and overwrite any matching center."""
    out = _copy_grid(grid)
    height, width = len(grid), len(grid[0])
    for row in range(1, height - 1):
        for col in range(1, width - 1):
            vals = _diag_values(grid, row, col)
            if vals[0] != 0 and all(value == vals[0] for value in vals):
                out[row][col] = vals[0]
    return out


def _rival_require_blank_orthogonals(grid):
    """Fill a valid diagonal center only when all four orthogonals are blank."""
    out = _copy_grid(grid)
    height, width = len(grid), len(grid[0])
    for row in range(1, height - 1):
        for col in range(1, width - 1):
            vals = _diag_values(grid, row, col)
            orthogonals = tuple(grid[row + dr][col + dc] for dr, dc in _ORTHOGONALS)
            if (
                grid[row][col] == 0
                and vals[0] != 0
                and all(value == vals[0] for value in vals)
                and all(value == 0 for value in orthogonals)
            ):
                out[row][col] = vals[0]
    return out


def _rival_reuse_only_with_texture(grid, texture: str):
    """Allow repeated-color fills only when one distractor kind is present."""
    if _classify_centers(grid)[texture]:
        return _apply_rule(grid)
    return _rival_one_center_per_color(grid)


def _rival_reuse_only_with_mismatched_distractor(grid):
    return _rival_reuse_only_with_texture(grid, "mismatched_diagonals")


def _rival_reuse_only_with_partial_distractor(grid):
    return _rival_reuse_only_with_texture(grid, "partial_diagonals")


def _rival_reuse_only_with_blocked_distractor(grid):
    return _rival_reuse_only_with_texture(grid, "blocked_center")


def _has_multiple_active(grid) -> bool:
    return len(_classify_centers(grid)["active"]) >= 2


def _has_repeated_color_multiple_centers(grid) -> bool:
    colors = [entry[2] for entry in _classify_centers(grid)["active"]]
    return len(colors) >= 2 and len(set(colors)) < len(colors)


def _has_partial_distractor(grid) -> bool:
    return bool(_classify_centers(grid)["partial_diagonals"])


def _has_mismatched_distractor(grid) -> bool:
    return bool(_classify_centers(grid)["mismatched_diagonals"])


def _has_blocked_center_distractor(grid) -> bool:
    return bool(_classify_centers(grid)["blocked_center"])


def _has_orthogonal_context_pair(grid) -> bool:
    found = _classify_centers(grid)
    valid, invalid = _classify_orthogonal_context(grid, found["active"])
    return bool(valid) and not invalid


def _has_repeated_color_without_texture(grid, texture: str) -> bool:
    found = _classify_centers(grid)
    colors = [entry[2] for entry in found["active"]]
    return len(colors) >= 2 and len(set(colors)) < len(colors) and not found[texture]


def _has_repeated_color_without_mismatched(grid) -> bool:
    return _has_repeated_color_without_texture(grid, "mismatched_diagonals")


def _has_repeated_color_without_partial(grid) -> bool:
    return _has_repeated_color_without_texture(grid, "partial_diagonals")


def _has_repeated_color_without_blocked(grid) -> bool:
    return _has_repeated_color_without_texture(grid, "blocked_center")


SEMANTIC_WITNESSES = {
    "multiple_positive_centers": _has_multiple_active,
    "repeated_color_multiple_centers": _has_repeated_color_multiple_centers,
    "partial_diagonal_distractor": _has_partial_distractor,
    "mismatched_diagonal_distractor": _has_mismatched_distractor,
    "blocked_nonzero_center_distractor": _has_blocked_center_distractor,
    "orthogonal_context_pair": _has_orthogonal_context_pair,
    "repeated_color_without_mismatched": _has_repeated_color_without_mismatched,
    "repeated_color_without_partial": _has_repeated_color_without_partial,
    "repeated_color_without_blocked": _has_repeated_color_without_blocked,
}

SEMANTIC_RIVALS = {
    "first_center_only": _rival_first_center_only,
    "one_center_per_color": _rival_one_center_per_color,
    "ignore_diagonal_color_equality": _rival_ignore_color_equality,
    "three_of_four_diagonals": _rival_three_of_four,
    "overwrite_nonzero_center": _rival_overwrite_nonzero_center,
    "require_blank_orthogonals": _rival_require_blank_orthogonals,
    "reuse_only_with_mismatched_distractor": _rival_reuse_only_with_mismatched_distractor,
    "reuse_only_with_partial_distractor": _rival_reuse_only_with_partial_distractor,
    "reuse_only_with_blocked_distractor": _rival_reuse_only_with_blocked_distractor,
}

WITNESS_RIVALS = {
    "multiple_positive_centers": ["first_center_only"],
    "repeated_color_multiple_centers": ["one_center_per_color"],
    "mismatched_diagonal_distractor": ["ignore_diagonal_color_equality"],
    "partial_diagonal_distractor": ["three_of_four_diagonals"],
    "blocked_nonzero_center_distractor": ["overwrite_nonzero_center"],
    "orthogonal_context_pair": ["require_blank_orthogonals"],
    "repeated_color_without_mismatched": ["reuse_only_with_mismatched_distractor"],
    "repeated_color_without_partial": ["reuse_only_with_partial_distractor"],
    "repeated_color_without_blocked": ["reuse_only_with_blocked_distractor"],
}

LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "one_center_per_color": _rival_one_center_per_color,
    "require_blank_orthogonals": _rival_require_blank_orthogonals,
    "reuse_only_with_mismatched_distractor": _rival_reuse_only_with_mismatched_distractor,
    "reuse_only_with_partial_distractor": _rival_reuse_only_with_partial_distractor,
    "reuse_only_with_blocked_distractor": _rival_reuse_only_with_blocked_distractor,
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require three demos to falsify every named shortcut before the query."""
    if not isinstance(demos, (list, tuple)) or not demos:
        return ["at least one demonstration is required"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]

    errors: list[str] = []
    survivors = set(LESSON_COMPETITORS)
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            errors.append(f"demo {index} must contain input and output grids")
            continue
        grid = demo["input"]
        if self_check(grid):
            errors.append(f"demo {index} input is outside the teaching grammar")
            continue
        authoritative = _apply_rule(grid)
        if demo["output"] != authoritative:
            errors.append(f"demo {index} output disagrees with the selected rule")
            continue
        for name, competitor in LESSON_COMPETITORS.items():
            if competitor(grid) != authoritative:
                survivors.discard(name)

    query_grid = query["input"]
    if self_check(query_grid):
        errors.append("query input is outside the teaching grammar")
    if "output" in query and query["output"] != _apply_rule(query_grid):
        errors.append("query output disagrees with the selected rule")
    if survivors:
        errors.append("demonstrations leave rival rule(s) alive: " + ", ".join(sorted(survivors)))
    return errors


def schedule_profile(seed, sample_index, difficulty=None):
    """Cover every distractor and two reuse witnesses in any three-sample window."""
    residue = sample_index % len(TEXTURES)
    texture = TEXTURES[residue]
    distinct_slot = _schedule_slot(seed, "distinct-color")
    color_mode = "distinct" if residue == distinct_slot else "shared"
    return texture, color_mode


def _schedule_slot(seed: int, label: str) -> int:
    rng = stable_rng(seed, f"{TASK_ID}|schedule:{label}", VERSION)
    return rng.randrange(len(TEXTURES))


def _scheduled_orthogonal_context(seed: int, sample_index: int) -> bool:
    """Exactly one member of every three consecutive samples carries context."""
    return sample_index % len(TEXTURES) == _schedule_slot(seed, "orthogonal-context")


def observe_overrides(grid) -> dict[str, object]:
    found = _classify_centers(grid)
    active_colors = [entry[2] for entry in found["active"]]
    negative_kinds = [name for name in TEXTURES if found[name]]
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]) if grid else 0,
        "cross_count": len(found["active"]),
        "color_mode": "shared" if len(set(active_colors)) == 1 else "distinct",
        "texture": negative_kinds[0] if len(negative_kinds) == 1 else "ambiguous",
    }


def _band_range(difficulty) -> tuple[int, int]:
    if difficulty == "easy":
        return 7, 9
    if difficulty == "hard":
        return 11, 17
    if difficulty == "medium":
        return 8, 13
    return 7, 13


def _default_int(seed: int, sample_index: int, label: str, lo: int, hi: int) -> int:
    rng = stable_rng(seed, f"{TASK_ID}|{sample_index}|default:{label}", VERSION)
    return rng.randint(lo, hi)


def _pack_centers(height: int, width: int, count: int, rng) -> list[tuple[int, int]]:
    """Choose a randomized set of disjoint 3x3 motif footprints."""
    candidates = [
        (row, col)
        for row in range(1, height - 1)
        for col in range(1, width - 1)
    ]
    rng.shuffle(candidates)
    footprints = {center: _footprint(*center) for center in candidates}

    def search(start: int, chosen: list[tuple[int, int]], occupied: set[tuple[int, int]]):
        if len(chosen) == count:
            return list(chosen)
        needed = count - len(chosen)
        if len(candidates) - start < needed:
            return None
        for index in range(start, len(candidates)):
            center = candidates[index]
            footprint = footprints[center]
            if footprint & occupied:
                continue
            chosen.append(center)
            result = search(index + 1, chosen, occupied | footprint)
            if result is not None:
                return result
            chosen.pop()
        return None

    result = search(0, [], set())
    if result is None:
        raise ValueError(
            f"grid_h/grid_w cannot fit cross_count plus distractor: "
            f"{height}x{width} cannot pack {count} disjoint 3x3 motifs"
        )
    return result


def _place_active(grid, row: int, col: int, color: int) -> None:
    for dr, dc in _DIAGONALS:
        grid[row + dr][col + dc] = color


def _place_orthogonal_context(
    grid, row: int, col: int, active_color: int, context_color: int, rng
) -> None:
    if context_color == active_color:
        raise ValueError("orthogonal context color must differ from active color")
    pair = (_ORTHOGONALS[:2], _ORTHOGONALS[2:])[rng.randrange(2)]
    for dr, dc in pair:
        grid[row + dr][col + dc] = context_color


def _place_distractor(grid, row: int, col: int, texture: str, colors: Iterable[int], rng) -> None:
    colors = list(colors)
    if texture == "partial_diagonals":
        color = colors[0]
        missing = rng.randrange(4)
        for index, (dr, dc) in enumerate(_DIAGONALS):
            if index != missing:
                grid[row + dr][col + dc] = color
    elif texture == "mismatched_diagonals":
        a, b = colors[:2]
        assignments = [a, a, b, b]
        rng.shuffle(assignments)
        for (dr, dc), color in zip(_DIAGONALS, assignments):
            grid[row + dr][col + dc] = color
    elif texture == "blocked_center":
        ring, blocker = colors[:2]
        _place_active(grid, row, col, ring)
        grid[row][col] = blocker
    else:  # protected by draw_choice; kept loud for direct calls.
        raise ValueError(f"unsupported texture {texture!r}")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic, override-exact teaching input."""
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override axis(es): " + ", ".join(unknown))

    lo, hi = _band_range(difficulty)
    scheduled_texture, scheduled_color_mode = schedule_profile(seed, sample_index, difficulty)
    # Anchor every band to the three canonical scales on 60% of ordinary draws;
    # the remaining draws retain broader difficulty-aware dimensions.
    canonical_size = (7, 8, 9, None, None)[sample_index % 5]
    default_h = canonical_size if canonical_size is not None else _default_int(seed, sample_index, "grid_h", lo, hi)
    default_w = canonical_size if canonical_size is not None else _default_int(seed, sample_index, "grid_w", lo, hi)
    effective = dict(overrides)
    effective.setdefault("grid_h", default_h)
    effective.setdefault("grid_w", default_w)
    effective.setdefault("cross_count", 2 if difficulty == "easy" else 2 + (sample_index % 2))
    effective.setdefault("texture", scheduled_texture)
    effective.setdefault("color_mode", scheduled_color_mode)

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective,
    )
    height = ctx.draw_int("grid_h", 7, 17)
    width = ctx.draw_int("grid_w", 7, 17)
    cross_count = ctx.draw_int("cross_count", 2, 3)
    color_mode = ctx.draw_choice("color_mode", COLOR_MODES)
    texture = ctx.draw_choice("texture", TEXTURES)

    layout_rng = ctx.draw_rng("layout")
    color_rng = ctx.draw_rng("colors")
    palette = color_rng.sample(range(1, 10), 6)
    if color_mode == "shared":
        active_colors = [palette[0]] * cross_count
    else:
        active_colors = palette[:cross_count]

    extra_colors = [color for color in palette if color not in set(active_colors)]
    while len(extra_colors) < 2:
        extra_colors.append(next(color for color in range(1, 10) if color not in set(active_colors) | set(extra_colors)))
    unique_active = list(dict.fromkeys(active_colors))
    if texture == "partial_diagonals":
        # Shared positives plus one new distractor color produce canonical palette size 3.
        distractor_colors = [extra_colors[0], extra_colors[1]]
    elif len(unique_active) >= 2:
        # Reuse visible positive colors so negative controls do not inflate the palette.
        distractor_colors = unique_active[:2]
    else:
        distractor_colors = [unique_active[0], extra_colors[0]]
    expected = {
        "grid_h": height,
        "grid_w": width,
        "cross_count": cross_count,
        "color_mode": color_mode,
        "texture": texture,
    }
    add_context = _scheduled_orthogonal_context(seed, sample_index)
    last_error = "unknown construction failure"

    # Randomly packed motifs can very rarely form an accidental predicate at
    # the boundary between two disjoint footprints.  Build-and-validate keeps
    # those coincidences out while retaining deterministic generation.
    for _attempt in range(64):
        grid = full_grid(height, width, 0)
        centers = _pack_centers(height, width, cross_count + 1, layout_rng)

        for (row, col), color in zip(centers[:cross_count], active_colors):
            _place_active(grid, row, col, color)

        row, col = centers[cross_count]
        _place_distractor(grid, row, col, texture, distractor_colors, layout_rng)

        if add_context:
            active_index = layout_rng.randrange(cross_count)
            row, col = centers[active_index]
            active_color = active_colors[active_index]
            context_color = next(color for color in palette if color != active_color)
            _place_orthogonal_context(
                grid,
                row,
                col,
                active_color,
                context_color,
                layout_rng,
            )

        errors = self_check(grid, difficulty=difficulty)
        if errors:
            last_error = f"invalid instance: {errors}"
            continue
        observed = observe_overrides(grid)
        if observed != expected:
            last_error = f"override mismatch: expected {expected}, observed {observed}"
            continue
        return _copy_grid(grid)

    raise ValueError(f"could not construct generator instance after 64 attempts: {last_error}")
