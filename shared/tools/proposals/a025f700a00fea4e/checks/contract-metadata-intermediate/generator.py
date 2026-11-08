"""Semantic generator for ARC task 48283e01e8ab.

Find every 4-connected component of source color 6 and recolor it from its
cell count.  Sizes 6, 5, 4, and 2 become 5, 3, 8, and 9.  A size-3 straight
line becomes 2 while every other connected size-3 shape becomes 4.  All
other component sizes remain 6, and every non-6 cell is preserved.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx


GENERATOR_ID = "48283e01e8ab"
TASK_ID = GENERATOR_ID
VERSION = "3.1.0"
RULE_HASH = "79a3d3708716"
SUMMARY = "Recolor each 4-connected color-6 component by size, distinguishing straight and bent size-3 components."
EXAMPLES_NEEDED = 4
LESSON_SCHEDULE_PERIOD = 4
SCHEDULE_PROFILES = ("teaching_core", "general", "public")

INVARIANTS = [
    "canonical background is 7 and source components use color 6",
    "components are extracted with 4-connectivity",
    "sizes 6, 5, 4, and 2 map to colors 5, 3, 8, and 9",
    "straight size-3 components map to 2 and bent size-3 components map to 4",
    "unrecognized sizes stay color 6",
    "all cells not colored 6 are preserved exactly",
]

PUBLIC_PROFILES = ("public_train_1", "public_train_2", "public_test_1")
LEGACY_GENERAL_PROFILES = (
    "all_classes_once", "repeated_lines", "repeated_bends", "unknown_sizes_mixed",
    "size6_nonrect", "size5_nonplus", "size4_varied", "domino_orientations",
    "two_domino_plus_five", "edge_components", "foreign_preserved",
    "sparse_many", "mixed_repeats",
)
GENERAL_PROFILES = LEGACY_GENERAL_PROFILES + ("teaching_core",)
SCENE_PROFILES = PUBLIC_PROFILES + GENERAL_PROFILES
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "four-slot lesson schedule: teaching core, general, teaching core, public",
        "valid": "|".join(SCENE_PROFILES),
    }
}


_PUBLIC_INPUTS = {
    "public_train_1": (
        "667766777", "767776677", "777677776", "776667676", "767677676",
        "767777777", "767777766", "777766676", "777766677",
    ),
    "public_train_2": (
        "777777777", "767767777", "666767667", "767777767", "777777777",
        "777766777", "777776676", "766677776", "766677776",
    ),
    "public_test_1": (
        "767766777", "666776677", "767777776", "777666776", "777666776",
        "777777777", "667777766", "767776776", "777776777",
    ),
}
_PUBLIC_SIGNATURES = {
    tuple(tuple(int(value) for value in row) for row in mask): profile
    for profile, mask in _PUBLIC_INPUTS.items()
}

_DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))

DOMINO = ((0, 0), (1, 0))
LINE3 = ((0, 0), (0, 1), (0, 2))
BEND3 = ((0, 0), (1, 0), (1, 1))
T4 = ((0, 0), (0, 1), (0, 2), (1, 1))
S4 = ((0, 0), (1, 0), (1, 1), (2, 1))
L4 = ((0, 0), (1, 0), (2, 0), (2, 1))
PLUS5 = ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1))
L5 = ((0, 0), (1, 0), (2, 0), (3, 0), (3, 1))
P5 = ((0, 0), (0, 1), (1, 0), (1, 1), (2, 0))
LINE5 = ((0, 0), (0, 1), (0, 2), (0, 3), (0, 4))
RECT6 = ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2))
ZIG6 = ((0, 0), (1, 0), (1, 1), (2, 1), (2, 2), (3, 2))
T6 = ((0, 0), (0, 1), (0, 2), (0, 3), (1, 1), (2, 1))
SHAPE7 = ((0, 0), (0, 1), (0, 2), (1, 0), (2, 0), (2, 1), (2, 2))
RECT8 = ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 1), (1, 2), (1, 3))
SINGLETON = ((0, 0),)


def _band(difficulty):
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return difficulty
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def _dimensions(band):
    return {"easy": (9, 9), "medium": (9, 10), "hard": (10, 10)}[band]


def _validate_draw(seed, sample_index, difficulty):
    for name, value in (("seed", seed), ("sample_index", sample_index)):
        if type(value) is not int or value < 0:
            raise ValueError(f"{name} must be a nonnegative Python integer")
    return _band(difficulty)


def schedule_profile(seed, sample_index, difficulty=None):
    """Periodic lesson roles; random layouts and subprofiles remain seed keyed."""
    _validate_draw(seed, sample_index, difficulty)
    return ("teaching_core", "general", "teaching_core", "public")[sample_index % 4]


def _normalize(cells):
    min_row = min(row for row, _ in cells)
    min_col = min(col for _, col in cells)
    return tuple(sorted((row - min_row, col - min_col) for row, col in cells))


def _shape_variants(shape):
    variants = set()
    current = tuple(shape)
    for _ in range(4):
        variants.add(_normalize(current))
        variants.add(_normalize(tuple((row, -col) for row, col in current)))
        current = tuple((col, -row) for row, col in current)
    return tuple(sorted(variants))


def _blank(height, width, value=7):
    return [[value for _ in range(width)] for _ in range(height)]


def _can_place(cells, occupied, height, width):
    if any(not (0 <= row < height and 0 <= col < width) for row, col in cells):
        return False
    proposed = set(cells)
    if proposed & occupied:
        return False
    return not any((row + dr, col + dc) in occupied for row, col in proposed for dr, dc in _DIRS)


def _place_shapes(rng, height, width, shapes, *, edge_count=0):
    ordered = sorted(enumerate(shapes), key=lambda item: (-len(item[1]), item[0]))
    for _ in range(300):
        occupied, placed = set(), {}
        failed = False
        for order_index, (original_index, shape) in enumerate(ordered):
            variants = list(_shape_variants(shape))
            rng.shuffle(variants)
            candidates = []
            for variant in variants:
                shape_h = 1 + max(row for row, _ in variant)
                shape_w = 1 + max(col for _, col in variant)
                for top in range(height - shape_h + 1):
                    for left in range(width - shape_w + 1):
                        cells = tuple((top + row, left + col) for row, col in variant)
                        touches_edge = any(row in (0, height - 1) or col in (0, width - 1) for row, col in cells)
                        if order_index < edge_count and not touches_edge:
                            continue
                        if _can_place(cells, occupied, height, width):
                            candidates.append(cells)
            if not candidates:
                failed = True
                break
            cells = rng.choice(candidates)
            occupied.update(cells)
            placed[original_index] = cells
        if not failed:
            return [placed[index] for index in range(len(shapes))]
    raise RuntimeError(f"unable to place component lesson with sizes {[len(shape) for shape in shapes]}")


def _profile_shapes(profile):
    return {
        "all_classes_once": (RECT6, PLUS5, S4, LINE3, BEND3, DOMINO),
        "repeated_lines": (LINE3, LINE3, LINE3, LINE3),
        "repeated_bends": (BEND3, BEND3, BEND3, BEND3),
        "unknown_sizes_mixed": (SINGLETON, DOMINO, SHAPE7, RECT8),
        "size6_nonrect": (ZIG6, T6),
        "size5_nonplus": (L5, P5, LINE5),
        "size4_varied": (T4, S4, L4),
        "domino_orientations": (DOMINO, DOMINO, DOMINO, DOMINO),
        "two_domino_plus_five": (DOMINO, DOMINO, PLUS5),
        "edge_components": (RECT6, T4, DOMINO),
        "foreign_preserved": (T4, LINE3, DOMINO),
        "sparse_many": (DOMINO, DOMINO, DOMINO, DOMINO, DOMINO, DOMINO),
        "mixed_repeats": (PLUS5, L5, LINE3, LINE3, BEND3, BEND3),
        "teaching_core": (ZIG6, L5, T4, LINE3, BEND3, DOMINO, SINGLETON, SHAPE7, RECT8),
    }[profile]


def _components(grid):
    height, width = len(grid), len(grid[0])
    seen, components = set(), []
    for row in range(height):
        for col in range(width):
            if grid[row][col] != 6 or (row, col) in seen:
                continue
            stack, cells = [(row, col)], []
            seen.add((row, col))
            while stack:
                current = stack.pop()
                cells.append(current)
                for dr, dc in _DIRS:
                    neighbor = current[0] + dr, current[1] + dc
                    if 0 <= neighbor[0] < height and 0 <= neighbor[1] < width and grid[neighbor[0]][neighbor[1]] == 6 and neighbor not in seen:
                        seen.add(neighbor)
                        stack.append(neighbor)
            components.append(tuple(sorted(cells)))
    return tuple(components)


def _target_color(cells):
    size = len(cells)
    rows = [row for row, _ in cells]
    cols = [col for _, col in cells]
    shape_h, shape_w = max(rows) - min(rows) + 1, max(cols) - min(cols) + 1
    if size == 6:
        return 5
    if size == 5:
        return 3
    if size == 4:
        return 8
    if size == 3 and (shape_h == 1 or shape_w == 1):
        return 2
    if size == 3:
        return 4
    if size == 2:
        return 9
    return 6


def _validate_grid(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be non-empty"], 0, 0
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid must have non-empty rows"], 0, 0
    height, width = len(grid), len(grid[0])
    if height > 30 or width > 30:
        return ["ARC grids must fit within 30 rows and 30 columns"], height, width
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"], height, width
    for row in grid:
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return ["cells must be integer ARC colors 0..9"], height, width
    return [], height, width


def _classify_general(grid, components):
    sizes = tuple(sorted(len(cells) for cells in components))
    line3 = sum(len(cells) == 3 and _target_color(cells) == 2 for cells in components)
    bent3 = sum(len(cells) == 3 and _target_color(cells) == 4 for cells in components)
    foreign = sum(value not in (6, 7) for row in grid for value in row)
    edge_components = sum(any(row in (0, len(grid) - 1) or col in (0, len(grid[0]) - 1) for row, col in cells) for cells in components)
    if sizes == (1, 2, 3, 3, 4, 5, 6, 7, 8) and line3 == 1 and bent3 == 1 and foreign >= 3:
        return "teaching_core"
    if sizes == (2, 3, 3, 4, 5, 6) and line3 == 1 and bent3 == 1 and foreign == 0:
        return "all_classes_once"
    if sizes == (3, 3, 3, 3) and line3 == 4:
        return "repeated_lines"
    if sizes == (3, 3, 3, 3) and bent3 == 4:
        return "repeated_bends"
    if sizes == (1, 2, 7, 8):
        return "unknown_sizes_mixed"
    if sizes == (6, 6):
        return "size6_nonrect"
    if sizes == (5, 5, 5):
        return "size5_nonplus"
    if sizes == (4, 4, 4):
        return "size4_varied"
    if sizes == (2, 2, 2, 2):
        return "domino_orientations"
    if sizes == (2, 2, 5):
        return "two_domino_plus_five"
    if sizes == (2, 4, 6) and edge_components >= 2:
        return "edge_components"
    if sizes == (2, 3, 4) and foreign >= 3:
        return "foreign_preserved"
    if sizes == (2, 2, 2, 2, 2, 2):
        return "sparse_many"
    if sizes == (3, 3, 3, 3, 5, 5) and line3 == 2 and bent3 == 2:
        return "mixed_repeats"
    return None


def _analysis(grid):
    errors, height, width = _validate_grid(grid)
    result = {"errors": errors, "height": height, "width": width, "scene_profile": None}
    if errors:
        return result
    components = _components(grid)
    if not components:
        errors.append("at least one color-6 component is required")
        return result
    output = [list(row) for row in grid]
    infos = []
    for cells in components:
        color = _target_color(cells)
        for row, col in cells:
            output[row][col] = color
        rows = [row for row, _ in cells]
        cols = [col for _, col in cells]
        infos.append({
            "cells": cells, "size": len(cells), "target_color": color,
            "shape": _normalize(cells),
            "line3": len(cells) == 3 and (max(rows) == min(rows) or max(cols) == min(cols)),
            "touches_edge": any(row in (0, height - 1) or col in (0, width - 1) for row, col in cells),
        })
    signature = tuple(tuple(row) for row in grid)
    profile = _PUBLIC_SIGNATURES.get(signature) or _classify_general(grid, components)
    if profile not in SCENE_PROFILES:
        errors.append("grid does not match a declared component lesson")
    result.update({
        "errors": errors,
        "scene_profile": profile,
        "components": tuple(infos),
        "sizes": tuple(sorted(info["size"] for info in infos)),
        "target_colors": tuple(sorted(info["target_color"] for info in infos)),
        "foreign_cells": tuple(
            (row, col, grid[row][col])
            for row in range(height)
            for col in range(width)
            if grid[row][col] not in (6, 7)
        ),
        "output": output,
    })
    return result


def canonical_profile_signature(grid):
    info = _analysis(grid)
    profile = info.get("scene_profile")
    return profile if not info["errors"] and profile in PUBLIC_PROFILES else None


def observe_overrides(grid):
    info = _analysis(grid)
    if info["errors"]:
        raise ValueError("; ".join(info["errors"]))
    return {"scene_profile": info["scene_profile"]}


def rule_mirror(grid):
    info = _analysis(grid)
    if info["errors"]:
        raise ValueError("; ".join(info["errors"]))
    return [row[:] for row in info["output"]]


def _public_grid(profile):
    return [[int(value) for value in row] for row in _PUBLIC_INPUTS[profile]]


def _general_grid(rng, profile, band, preserved_colors):
    height, width = _dimensions(band)
    if profile == "teaching_core":
        height = width = {"easy": 12, "medium": 13, "hard": 14}[band]
    grid = _blank(height, width)
    edge_count = 2 if profile == "edge_components" else 0
    placements = _place_shapes(rng, height, width, _profile_shapes(profile), edge_count=edge_count)
    for cells in placements:
        for row, col in cells:
            grid[row][col] = 6
    if profile in ("foreign_preserved", "teaching_core"):
        candidates = [
            (row, col)
            for row in range(height)
            for col in range(width)
            if grid[row][col] == 7
            and all(not (0 <= row + dr < height and 0 <= col + dc < width and grid[row + dr][col + dc] == 6) for dr, dc in _DIRS)
        ]
        rng.shuffle(candidates)
        for index, (row, col) in enumerate(candidates[:5]):
            grid[row][col] = preserved_colors[index % len(preserved_colors)]
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    band = _validate_draw(seed, sample_index, difficulty)
    unknown = set(overrides) - {"scene_profile"}
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)}")
    requested = overrides.get("scene_profile")
    if requested is not None and requested not in SCENE_PROFILES:
        raise ValueError(f"unknown scene_profile: {requested!r}")
    context = gen_ctx(
        seed=seed, sample_index=sample_index, version=VERSION, task_id=TASK_ID,
        difficulty=difficulty, overrides=overrides,
    )
    if requested is not None:
        profile = context.draw_choice("scene_profile", list(SCENE_PROFILES))
    else:
        role = schedule_profile(seed, sample_index, difficulty)
        if role == "teaching_core":
            profile = role
        elif role == "general":
            profile = context.draw_choice("general_profile", list(LEGACY_GENERAL_PROFILES))
        else:
            profile = context.draw_choice("public_profile", list(PUBLIC_PROFILES))
    preserved_colors = context.draw_distinct_colors("preserved_colors", n=3, exclude={6, 7})
    rng = context.draw_rng("layout")
    grid = _public_grid(profile) if profile in PUBLIC_PROFILES else _general_grid(rng, profile, band, preserved_colors)
    observed = observe_overrides(grid)
    if observed != {"scene_profile": profile}:
        raise RuntimeError(f"profile construction mismatch: {profile!r} -> {observed!r}")
    return grid


def self_check(grid, *, difficulty=None, meta=None):
    info = _analysis(grid)
    errors = list(info["errors"])
    overrides = (meta or {}).get("overrides", {}) if isinstance(meta, dict) else {}
    if overrides:
        unknown = set(overrides) - {"scene_profile"}
        if unknown:
            errors.append(f"unknown override(s): {sorted(unknown)}")
        requested = overrides.get("scene_profile")
        if requested not in SCENE_PROFILES:
            errors.append(f"unknown scene_profile: {requested!r}")
        elif not errors and info["scene_profile"] != requested:
            errors.append(f"requested scene_profile {requested}, observed {info['scene_profile']}")
    return errors


def strict_canonical_like(grid):
    """The declared component-class manifold, including its canonical examples."""
    return self_check(grid)


_RECT6_VARIANTS = frozenset(_shape_variants(RECT6))
_PLUS5_VARIANTS = frozenset(_shape_variants(PLUS5))
_S4_VARIANTS = frozenset(_shape_variants(S4))
_CANONICAL_SHAPES = frozenset(
    variant
    for shape in (RECT6, PLUS5, S4, LINE3, BEND3, DOMINO)
    for variant in _shape_variants(shape)
)


def _rival_recolor(grid, choose_color):
    output = [list(row) for row in grid]
    for cells in _components(grid):
        color = choose_color(cells)
        for row, col in cells:
            output[row][col] = color
    return output


def _canonical_shapes_only(grid):
    """Rival: memorize dihedral copies of the six canonical shape templates."""
    return _rival_recolor(grid, lambda cells: _target_color(cells)
                          if _normalize(cells) in _CANONICAL_SHAPES else 6)


def _rectangles_only_at_six(grid):
    return _rival_recolor(grid, lambda cells: 6 if len(cells) == 6
                          and _normalize(cells) not in _RECT6_VARIANTS else _target_color(cells))


def _crosses_only_at_five(grid):
    return _rival_recolor(grid, lambda cells: 6 if len(cells) == 5
                          and _normalize(cells) not in _PLUS5_VARIANTS else _target_color(cells))


def _skew_only_at_four(grid):
    return _rival_recolor(grid, lambda cells: 6 if len(cells) == 4
                          and _normalize(cells) not in _S4_VARIANTS else _target_color(cells))


def _unknown_sizes_as_domino(grid):
    return _rival_recolor(grid, lambda cells: 9 if len(cells) not in (2, 3, 4, 5, 6)
                          else _target_color(cells))


def _erase_foreign_colors(grid):
    output = _rival_recolor(grid, _target_color)
    for row, values in enumerate(grid):
        for col, color in enumerate(values):
            if color not in (6, 7):
                output[row][col] = 7
    return output


def _all_threes_are_lines(grid):
    return _rival_recolor(grid, lambda cells: 2 if len(cells) == 3 else _target_color(cells))


CANONICAL_SHORTCUTS = {
    "canonical_shapes_only": _canonical_shapes_only,
    "rectangles_only_at_six": _rectangles_only_at_six,
    "crosses_only_at_five": _crosses_only_at_five,
    "skew_only_at_four": _skew_only_at_four,
    "unknown_sizes_as_domino": _unknown_sizes_as_domino,
    "erase_foreign_colors": _erase_foreign_colors,
}
LESSON_COMPETITORS = dict(CANONICAL_SHORTCUTS)
LESSON_COMPETITORS["all_threes_are_lines"] = _all_threes_are_lines
SEMANTIC_RIVALS = dict(LESSON_COMPETITORS)


def _has_nonrect_six(grid):
    return any(len(cells) == 6 and _normalize(cells) not in _RECT6_VARIANTS for cells in _components(grid))


def _has_nonplus_five(grid):
    return any(len(cells) == 5 and _normalize(cells) not in _PLUS5_VARIANTS for cells in _components(grid))


def _has_nonskew_four(grid):
    return any(len(cells) == 4 and _normalize(cells) not in _S4_VARIANTS for cells in _components(grid))


def _has_unknown_size(grid):
    return any(len(cells) not in (2, 3, 4, 5, 6) for cells in _components(grid))


def _has_foreign_color(grid):
    return any(value not in (6, 7) for row in grid for value in row)


def _has_bent_three(grid):
    return any(len(cells) == 3 and _target_color(cells) == 4 for cells in _components(grid))


SEMANTIC_WITNESSES = {
    "nonrect_six": _has_nonrect_six,
    "nonplus_five": _has_nonplus_five,
    "nonskew_four": _has_nonskew_four,
    "unknown_size": _has_unknown_size,
    "foreign_preserved": _has_foreign_color,
    "bent_three": _has_bent_three,
}
WITNESS_RIVALS = {
    "nonrect_six": ["rectangles_only_at_six"],
    "nonplus_five": ["crosses_only_at_five"],
    "nonskew_four": ["skew_only_at_four"],
    "unknown_size": ["unknown_sizes_as_domino"],
    "foreign_preserved": ["erase_foreign_colors"],
    "bent_three": ["all_threes_are_lines"],
}


def _class_key(cells):
    if len(cells) == 3:
        rows, cols = zip(*cells)
        return (3, "line" if min(rows) == max(rows) or min(cols) == max(cols) else "bend")
    return (len(cells), "any")


def lesson_identifiable(demos, query):
    """Check class-label support and these declared rivals, not universal induction."""
    learned = {}
    reasons = []
    for pair in demos:
        for cells in _components(pair["input"]):
            colors = {pair["output"][row][col] for row, col in cells}
            learned.setdefault(_class_key(cells), set()).update(colors)
    for cells in _components(query["input"]):
        key = _class_key(cells)
        colors = {query["output"][row][col] for row, col in cells}
        if len(colors) != 1 or learned.get(key) != colors:
            reasons.append(f"component class {key!r} lacks a consistent demonstrated label")
    if _has_foreign_color(query["input"]) and not any(_has_foreign_color(pair["input"]) for pair in demos):
        reasons.append("query has foreign colors without a preservation demonstration")
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            if rival(query["input"]) != query["output"]:
                reasons.append(f"{name} fits the demonstrations but changes the query")
    return sorted(set(reasons))
