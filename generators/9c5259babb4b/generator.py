"""Semantic generator for ARC task 9c5259babb4b (source a09f6c25).

Use the modal color as background and find same-color 8-connected objects.
Delete singleton objects.  Recolor every larger object blue when its normalized
shape is top-bottom symmetric, green when it is only left-right symmetric, and
magenta otherwise.  Top-bottom symmetry has precedence when both hold.
"""
from __future__ import annotations

from collections import Counter

from puzzle_generators.base import gen_ctx


GENERATOR_ID = "9c5259babb4b"
TASK_ID = "9c5259babb4b"
VERSION = "3.1.0"
RULE_HASH = "6a2cfe9a66b0"
SUMMARY = "Remove singleton noise and recolor each 8-connected object by top-bottom, left-right-only, or asymmetric shape class."
INVARIANTS = [
    "the modal background is one of the three demonstrated nonzero colors",
    "calibrated source objects use color 2 and 8-connectivity",
    "singleton source objects disappear into the background",
    "top-bottom symmetric objects become 1, including shapes symmetric on both axes",
    "left-right-only symmetric objects become 3 and asymmetric objects become 6",
]

PUBLIC_PROFILES = ("public_1", "public_2", "public_3", "public_4", "public_5")
GENERAL_PROFILES = ("class_balanced", "no_asymmetry", "dense_mixed", "precedence_both")
SCENE_PROFILES = PUBLIC_PROFILES + GENERAL_PROFILES
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "five complete official families plus four symmetry-class contrasts",
        "valid": "|".join(SCENE_PROFILES),
    }
}

_PUBLIC_ROWS = {
    "public_1": (
        "7772777777777777777", "7722277777777772777", "7222777777777777777",
        "2227777277777777777", "7277777227777277777", "7777772222222277777",
        "7777777227777277777", "7777777277777777777", "7777777777277777777",
        "7772777777777777727", "7722277777777777222", "7722277777777777727",
        "7222227777277777727", "7772777722277777777", "7772777727222277777",
        "7777777722277777777", "7777777777277777777", "7777777777777777277",
        "7777777777777777777",
    ),
    "public_2": (
        "8888888888888888888", "8888888888888888888", "8888888222882888888",
        "8828822282222288888", "8888888222882888888", "8888888888888888888",
        "8888888888888888888", "8888888888888888882", "8888888888888888888",
        "8882888888228888888", "8822288882288888888", "8882888882222228888",
        "8822288882288888888", "8828288888228888888", "8822288888888888888",
        "8828288888888888828", "8888888888828888888", "8888888888888888888",
        "8888888888888888888",
    ),
    "public_3": (
        "4444444444444444444", "4444424444444444444", "4444224244444444444",
        "4442222224444222444", "4444224244444222444", "4444424444444424444",
        "4444444444444424444", "4444444444444444444", "4444444444444444442",
        "4444424444444444444", "4444444444424244444", "4444444444222224444",
        "4224444444422244444", "2222244444442444444", "4224444444444444444",
        "4444444444444444444", "4444444424444444444",
    ),
    "public_4": (
        "888888888888888888888888888", "888888888888888882888888888",
        "888888888888888888888888288", "888282882228288888888888888",
        "882222222822288888828888888", "888282882228288882222288888",
        "888888888888888888828888888", "888888888888888888222888888",
        "888888888888888882282288888", "888888888288888882888288888",
        "888822888888888882888288888", "888222228882888822282228888",
        "888228828888888882888288888", "888828822288888888888888888",
        "888822288288888888888888888", "888888288228882888888888288",
        "888888222228888888888888888", "888888882288888888828888888",
        "888888888888888888222888888", "882888888888888888282888888",
        "888888888888888888282888888", "888888888888888888222888888",
        "888882888888888888282888888", "888882222288888888888888888",
        "888882888888828888888888288", "828888888888888888888222228",
        "888888888888888888888888288", "888888888888888888888888888",
    ),
    "public_5": (
        "444444442444444444444444444", "442424422244444444444444444",
        "442222224244444222444444444", "442424422244444242224424444",
        "444444442444442242422224444", "444444444444444242224424444",
        "444442444444444222444444444", "444444444444444444444444444",
        "444444444222444444444444444", "444444444242444444244442444",
        "442424444222224444444444444", "422222444442424444444444444",
        "444244444442224444242424444", "442224444444444444222224444",
        "422222444444444444424244444", "444244444444444444422244444",
        "444244444444444444222224444", "442224444444444444424244444",
        "442424444424444444422244444", "442424444444444444444444422",
        "444444444444444444444442222", "444444442224422224444442424",
        "444444442422224222444422224", "424444442224422224444422444",
        "444444444444444444444444444", "444444444444444444444444444",
    ),
}
_PUBLIC_INPUTS = {
    profile: [[int(value) for value in row] for row in rows]
    for profile, rows in _PUBLIC_ROWS.items()
}
_PUBLIC_SIGNATURES = {tuple(map(tuple, grid)): profile for profile, grid in _PUBLIC_INPUTS.items()}


def _valid_grid(grid):
    if not isinstance(grid, (list, tuple)) or not 3 <= len(grid) <= 30:
        return ["input must contain three through thirty rows"]
    if not isinstance(grid[0], (list, tuple)) or not 3 <= len(grid[0]) <= 30:
        return ["input must contain three through thirty columns"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["input must be rectangular"]
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid for value in row
    ):
        return ["input cells must be literal ARC color integers from zero through nine"]
    return []


def _mode(grid):
    counts = Counter(value for row in grid for value in row if value != 0)
    if not counts:
        return 0
    return max(counts, key=lambda value: (counts[value], -value))


def _objects8(grid, background):
    height, width = len(grid), len(grid[0])
    seen, components = set(), []
    for row in range(height):
        for col in range(width):
            if (row, col) in seen or grid[row][col] == background:
                continue
            color = grid[row][col]
            queue = [(row, col)]
            seen.add((row, col))
            cells = []
            for current_row, current_col in queue:
                cells.append((current_row, current_col))
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        other = current_row + dr, current_col + dc
                        if not (dr or dc) or other in seen:
                            continue
                        if not (0 <= other[0] < height and 0 <= other[1] < width):
                            continue
                        if grid[other[0]][other[1]] != color:
                            continue
                        seen.add(other)
                        queue.append(other)
            components.append({"color": color, "cells": cells})
    return components


def _normalize(cells):
    row0 = min(row for row, _ in cells)
    col0 = min(col for _, col in cells)
    return tuple(sorted((row - row0, col - col0) for row, col in cells))


def _symmetry(norm):
    cells = set(norm)
    height = max(row for row, _ in cells) + 1
    width = max(col for _, col in cells) + 1
    horizontal = {(height - 1 - row, col) for row, col in cells} == cells
    vertical = {(row, width - 1 - col) for row, col in cells} == cells
    kind = "both" if horizontal and vertical else "h" if horizontal else "v" if vertical else "a"
    color = 1 if horizontal else 3 if vertical else 6
    return kind, color, height, width


def _shape_variants(norm):
    kind, _, height, width = _symmetry(norm)
    del kind
    cells = set(norm)
    variants = {
        tuple(sorted(cells)),
        tuple(sorted((height - 1 - row, col) for row, col in cells)),
        tuple(sorted((row, width - 1 - col) for row, col in cells)),
        tuple(sorted((height - 1 - row, width - 1 - col) for row, col in cells)),
    }
    return tuple(sorted(variants))


def _shape_family_key(norm):
    kind, _, height, width = _symmetry(norm)
    return kind, len(norm), height, width, min(_shape_variants(norm))


def _connected8(norm):
    cells = set(norm)
    seen = {next(iter(cells))}
    queue = list(seen)
    for row, col in queue:
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                other = row + dr, col + dc
                if (dr or dc) and other in cells and other not in seen:
                    seen.add(other)
                    queue.append(other)
    return seen == cells


def _connected4(norm):
    cells = set(norm)
    seen = {next(iter(cells))}
    queue = list(seen)
    for row, col in queue:
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            other = row + dr, col + dc
            if other in cells and other not in seen:
                seen.add(other)
                queue.append(other)
    return seen == cells


_DIAGONAL_ASYMMETRIC_BASE = ((0, 0), (0, 1), (1, 1), (2, 2), (2, 3), (3, 3))


def _diagonal_asymmetric_shape(rng):
    """Return an asymmetric object whose connectivity genuinely needs diagonals."""
    variants = _shape_variants(_DIAGONAL_ASYMMETRIC_BASE)
    norm = rng.choice(variants)
    assert _symmetry(norm)[0] == "a"
    assert _connected8(norm) and not _connected4(norm)
    return norm


def rule_mirror(grid):
    """Exact Python mirror of the broad executable Racket program."""
    errors = _valid_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    background = _mode(grid)
    output = [[background] * len(grid[0]) for _ in grid]
    for obj in _objects8(grid, background):
        if len(obj["cells"]) <= 1:
            continue
        _, color, _, _ = _symmetry(_normalize(obj["cells"]))
        for row, col in obj["cells"]:
            output[row][col] = color
    return output


def canonical_profile_signature(grid):
    try:
        return _PUBLIC_SIGNATURES.get(tuple(tuple(row) for row in grid))
    except TypeError:
        return None


def _strict_facts(grid):
    errors = _valid_grid(grid)
    if errors:
        return errors, None
    height, width = len(grid), len(grid[0])
    if not 12 <= height <= 30 or not 12 <= width <= 30:
        errors.append("calibrated canvases must be twelve through thirty cells on each side")
    background = _mode(grid)
    if background not in (4, 7, 8):
        errors.append("calibrated background must be one of the demonstrated colors 4, 7, or 8")
    if any(value not in (background, 2) for row in grid for value in row):
        errors.append("calibrated inputs may contain only background and source color 2")
    components = _objects8(grid, background)
    singles = [obj for obj in components if len(obj["cells"]) == 1]
    kept = []
    for obj in components:
        if len(obj["cells"]) <= 1:
            continue
        norm = _normalize(obj["cells"])
        kind, output_color, object_height, object_width = _symmetry(norm)
        kept.append({
            **obj,
            "norm": norm,
            "kind": kind,
            "output_color": output_color,
            "height": object_height,
            "width": object_width,
            "size": len(norm),
            "family_key": _shape_family_key(norm),
            "row0": min(row for row, _ in obj["cells"]),
            "col0": min(col for _, col in obj["cells"]),
        })
    if not 3 <= len(singles) <= 10:
        errors.append("calibrated scenes require three through ten singleton distractors")
    if not 3 <= len(kept) <= 8:
        errors.append("calibrated scenes require three through eight retained objects")
    if any(not 6 <= obj["size"] <= 30 for obj in kept):
        errors.append("retained object sizes must be six through thirty cells")
    if any(min(obj["height"], obj["width"]) < 3 or max(obj["height"], obj["width"]) > 11 for obj in kept):
        errors.append("retained object bounding sides must lie between three and eleven cells")
    class_counts = Counter(obj["kind"] for obj in kept)
    if class_counts["h"] + class_counts["both"] < 1 or class_counts["v"] < 1:
        errors.append("every calibrated scene must contrast top-bottom and left-right-only symmetry")
    output = rule_mirror(grid)
    if output == [list(row) for row in grid]:
        errors.append("singleton removal and symmetry recoloring must visibly change the lesson")
    facts = {
        "height": height,
        "width": width,
        "background": background,
        "components": components,
        "singles": singles,
        "singleton_count": len(singles),
        "kept": kept,
        "kept_count": len(kept),
        "class_counts": class_counts,
        "output": output,
    }
    return errors, facts


def _public_family_key(facts):
    return (
        facts["background"],
        facts["singleton_count"],
        tuple(sorted(obj["family_key"] for obj in facts["kept"])),
    )


_PUBLIC_FACTS = {}
_PUBLIC_FAMILY_KEYS = {}
for _profile, _grid in _PUBLIC_INPUTS.items():
    _errors, _facts = _strict_facts(_grid)
    if _errors:
        raise AssertionError((_profile, _errors))
    _PUBLIC_FACTS[_profile] = _facts
    _PUBLIC_FAMILY_KEYS[_public_family_key(_facts)] = _profile


def canonical_family_signature(grid):
    errors, facts = _strict_facts(grid)
    if errors:
        return None
    return _PUBLIC_FAMILY_KEYS.get(_public_family_key(facts))


def _general_profile(facts):
    counts = facts["class_counts"]
    signature = counts["h"], counts["v"], counts["a"], counts["both"]
    if signature == (2, 2, 1, 0):
        return "class_balanced"
    if signature == (2, 2, 0, 0):
        return "no_asymmetry"
    if signature == (3, 2, 2, 0):
        return "dense_mixed"
    if signature == (2, 2, 1, 1):
        return "precedence_both"
    return None


def _analysis(grid):
    errors, facts = _strict_facts(grid)
    if errors:
        return {"errors": errors, "scene_profile": None, "facts": facts, "output": None}
    profile = canonical_profile_signature(grid)
    if profile is None:
        profile = _PUBLIC_FAMILY_KEYS.get(_public_family_key(facts))
    if profile is None:
        profile = _general_profile(facts)
    if profile not in SCENE_PROFILES:
        errors.append("scene does not match a complete official or generalized symmetry profile")
    return {
        "errors": errors,
        "scene_profile": profile,
        "facts": facts,
        "output": None if errors else facts["output"],
    }


def self_check(grid, *, difficulty=None, meta=None):
    return _analysis(grid)["errors"]


def observe_overrides(grid):
    analysis = _analysis(grid)
    return {"scene_profile": analysis["scene_profile"]} if not analysis["errors"] else {}


def _empty(height, width, background):
    return [[background] * width for _ in range(height)]


def _far_from(cells, occupied):
    return all(
        abs(row - other_row) > 1 or abs(col - other_col) > 1
        for row, col in cells for other_row, other_col in occupied
    )


def _add_singletons(grid, count, occupied, rng):
    height, width = len(grid), len(grid[0])
    candidates = [(row, col) for row in range(height) for col in range(width)]
    rng.shuffle(candidates)
    placed = []
    for cell in candidates:
        if cell in occupied or not _far_from([cell], occupied | set(placed)):
            continue
        grid[cell[0]][cell[1]] = 2
        placed.append(cell)
        if len(placed) == count:
            return placed
    raise AssertionError("could not place isolated singleton distractors")


def _flip_grid(grid, horizontal, vertical):
    result = [row[:] for row in grid]
    if horizontal:
        result = list(reversed(result))
    if vertical:
        result = [list(reversed(row)) for row in result]
    return result


def _public_nuisance(profile, rng):
    source = _PUBLIC_INPUTS[profile]
    source_facts = _PUBLIC_FACTS[profile]
    height, width = len(source), len(source[0])
    for _ in range(120):
        shapes = [rng.choice(_shape_variants(obj["norm"])) for obj in source_facts["kept"]]
        try:
            grid = _place_shapes(
                height,
                width,
                shapes,
                source_facts["background"],
                source_facts["singleton_count"],
                rng,
            )
        except AssertionError:
            continue
        grid = _flip_grid(grid, rng.choice((False, True)), rng.choice((False, True)))
        analysis = _analysis(grid)
        if not analysis["errors"] and analysis["scene_profile"] == profile and canonical_profile_signature(grid) is None:
            return grid
    raise AssertionError(f"could not construct nonliteral public-family profile {profile!r}")


def _random_shape(target, difficulty, rng):
    side_high = 5 if difficulty == "easy" else 7 if difficulty == "medium" else 9
    for _ in range(1200):
        height, width = rng.randint(3, side_high), rng.randint(3, side_high)
        if target == "a":
            desired = rng.randint(6, min(28, height * width - 1))
            cells = {(rng.randrange(height), rng.randrange(width))}
            while len(cells) < desired:
                row, col = rng.choice(tuple(cells))
                candidates = [
                    (row + dr, col + dc)
                    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))
                    if 0 <= row + dr < height and 0 <= col + dc < width
                ]
                cells.add(rng.choice(candidates))
        else:
            probability = rng.uniform(0.3, 0.7)
            cells = {
                (row, col)
                for row in range(height) for col in range(width)
                if rng.random() < probability
            }
            if target in ("h", "both"):
                cells |= {(height - 1 - row, col) for row, col in cells}
            if target in ("v", "both"):
                cells |= {(row, width - 1 - col) for row, col in cells}
        if not cells:
            continue
        norm = _normalize(cells)
        kind, _, object_height, object_width = _symmetry(norm)
        if kind != target or not _connected8(norm):
            continue
        if not 6 <= len(norm) <= 28 or min(object_height, object_width) < 3:
            continue
        return norm
    raise AssertionError(f"could not synthesize symmetry class {target!r}")


def _place_shapes(height, width, shapes, background, singleton_count, rng):
    indexed = list(enumerate(shapes))
    indexed.sort(key=lambda item: len(item[1]), reverse=True)
    grid = _empty(height, width, background)
    occupied, placements = set(), {}
    for index, shape in indexed:
        _, _, shape_height, shape_width = _symmetry(shape)
        candidates = [
            (row0, col0)
            for row0 in range(height - shape_height + 1)
            for col0 in range(width - shape_width + 1)
        ]
        rng.shuffle(candidates)
        for row0, col0 in candidates:
            cells = {(row0 + row, col0 + col) for row, col in shape}
            if not _far_from(cells, occupied):
                continue
            placements[index] = cells
            occupied.update(cells)
            break
        else:
            raise AssertionError("could not pack symmetry objects with 8-connect separation")
    for cells in placements.values():
        for row, col in cells:
            grid[row][col] = 2
    _add_singletons(grid, singleton_count, occupied, rng)
    return grid


def _limits(difficulty):
    if difficulty == "easy":
        return 18, 21, 3, 5
    if difficulty == "medium":
        return 22, 26, 4, 7
    if difficulty == "hard":
        return 27, 30, 6, 10
    return 19, 28, 4, 8


_PROFILE_CLASSES = {
    "class_balanced": ("h", "h", "v", "v", "a"),
    "no_asymmetry": ("h", "h", "v", "v"),
    "dense_mixed": ("h", "h", "h", "v", "v", "a", "a"),
    "precedence_both": ("h", "h", "v", "v", "a", "both"),
}


def _general_scene(profile, difficulty, rng):
    low, high, singleton_low, singleton_high = _limits(difficulty)
    for _ in range(160):
        height, width = rng.randint(low, high), rng.randint(low, high)
        background = rng.choice((4, 4, 7, 8, 8))
        try:
            shapes = []
            diagonal_witness_used = False
            for kind in _PROFILE_CLASSES[profile]:
                if kind == "a" and not diagonal_witness_used:
                    shapes.append(_diagonal_asymmetric_shape(rng))
                    diagonal_witness_used = True
                else:
                    shapes.append(_random_shape(kind, difficulty, rng))
            grid = _place_shapes(
                height,
                width,
                shapes,
                background,
                rng.randint(singleton_low, singleton_high),
                rng,
            )
        except AssertionError:
            continue
        analysis = _analysis(grid)
        if not analysis["errors"] and analysis["scene_profile"] == profile:
            return grid
    raise AssertionError(f"could not construct symmetry profile {profile!r}")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = set(overrides) - {"scene_profile"}
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)!r}")
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = ctx.draw_choice("scene_profile", list(PUBLIC_PROFILES) * 2 + list(GENERAL_PROFILES) * 3)
    if profile not in SCENE_PROFILES:
        raise ValueError(f"unknown scene_profile: {profile!r}")
    if profile in PUBLIC_PROFILES:
        if overrides.get("scene_profile") is not None:
            return [row[:] for row in _PUBLIC_INPUTS[profile]]
        grid = _public_nuisance(profile, ctx.draw_rng("public_nuisance"))
    else:
        grid = _general_scene(profile, difficulty, ctx.draw_rng("scene"))
    errors = self_check(grid)
    if errors:
        raise AssertionError("generated invalid symmetry lesson: " + "; ".join(errors))
    return grid
