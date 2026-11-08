"""Semantic generator for ARC task c2a1ba1a45fd (source 1da012fc).

The gray cells delimit a legend rectangle.  The most frequent nonzero color
outside that rectangle is the source color.  Non-source colored legend cells
and external 8-connected source-color objects are independently sorted in
row-major order, then paired and recolored up to the shorter list.
"""
from __future__ import annotations

from collections import deque

from puzzle_generators.base import gen_ctx


GENERATOR_ID = "c2a1ba1a45fd"
TASK_ID = "c2a1ba1a45fd"
VERSION = "3.0.0"
RULE_HASH = "35ba3ac2fe27"
SUMMARY = "Use the gray legend's ordered colored cells to recolor ordered external objects of the outside-dominant source color."
INVARIANTS = [
    "all gray cells jointly define the inclusive legend bounding rectangle",
    "the source color is the first color 1..9 attaining the largest count outside the legend rectangle",
    "source objects use same-color 8-connectivity and exclude any object touching the legend rectangle",
    "legend dots exclude zero, gray 5, and the selected source color and are sorted row-major",
    "external source objects are sorted by their row-major top-left cell and paired with dots up to the shorter count",
    "the legend, background, distractors, and every unpaired dot or source object remain unchanged",
]

PUBLIC_PROFILES = ("public_1", "public_2", "public_3")
GENERAL_PROFILES = (
    "ordered_shapes",
    "diagonal_object",
    "source_frequency",
    "extra_dot",
    "extra_object",
    "source_dot_ignored",
    "repeated_dot_color",
)
SCENE_PROFILES = PUBLIC_PROFILES + GENERAL_PROFILES
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "three complete official families plus seven labeled ordering and selection contrasts",
        "valid": "|".join(SCENE_PROFILES),
    }
}

NON_SPECIAL_COLORS = (1, 2, 3, 4, 6, 7, 8, 9)
DELTAS_8 = tuple(
    (row_delta, col_delta)
    for row_delta in (-1, 0, 1)
    for col_delta in (-1, 0, 1)
    if (row_delta, col_delta) != (0, 0)
)
DELTAS_4 = ((-1, 0), (1, 0), (0, -1), (0, 1))

_PUBLIC_ROWS = {
    "public_1": (
        "00000000000000000000", "00000000011110000000", "00000000001100000000",
        "00000000000000000000", "00000000000000101000", "00000000000001111100",
        "05255550000000101000", "05555550000000000000", "05554550000000000000",
        "05555550011000000100", "05655350111100001110", "05555550011000000100",
        "00000000000000000000", "00000000000000000000",
    ),
    "public_2": (
        "0000000000000000555555", "0888888000000000525555", "0088880000000000555555",
        "0880088000000000555555", "0000000000000000555355", "0000000000000000555555",
        "0000000008880000555555", "0000000088888000545555", "0000000088888000555555",
        "0000000008080000000000", "0000000000000000000000", "0000000000000000000000",
        "0000000000000000000000", "0008000800000000000000", "0008888800000000000000",
        "0000888000000000000000", "0008808800000000000000", "0000000000000000000000",
        "0000000000000000000000",
    ),
    "public_3": (
        "0000000000000000000000000", "0002200002220000000000000", "0022220020202000000000000",
        "0002200000200000000000000", "0000000000000000000000000", "0000000000000000000000000",
        "0000000000000000000000000", "0000002220000000000000000", "0000022022000000000000000",
        "0000002220000000555555550", "0000000000000000535554550", "0000000000000000555555550",
        "0000000000000000555555550", "0002000000200200555855550", "0022200002222220555555550",
        "0002000000022000555555550", "0000000000000000515556550", "0000000000000000555555550",
        "0000000000000000555555550",
    ),
}
_PUBLIC_INPUTS = {
    profile: [[int(value) for value in row] for row in rows]
    for profile, rows in _PUBLIC_ROWS.items()
}
_PUBLIC_EXACT = {
    tuple(map(tuple, grid)): profile for profile, grid in _PUBLIC_INPUTS.items()
}


def _valid_grid(grid):
    if not isinstance(grid, (list, tuple)) or not 1 <= len(grid) <= 30:
        return ["input must contain one through thirty rows"]
    if not isinstance(grid[0], (list, tuple)) or not 1 <= len(grid[0]) <= 30:
        return ["input must contain one through thirty columns"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["input must be rectangular"]
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid for value in row
    ):
        return ["input cells must be literal ARC color integers from zero through nine"]
    return []


def _objects_8(grid, background=0):
    """Same-color 8-connected objects in row-major discovery order."""
    height, width = len(grid), len(grid[0])
    seen = set()
    found = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] == background or (row, col) in seen:
                continue
            color = grid[row][col]
            queue = deque([(row, col)])
            seen.add((row, col))
            cells = []
            while queue:
                here = queue.popleft()
                cells.append(here)
                for row_delta, col_delta in DELTAS_8:
                    neighbor = (here[0] + row_delta, here[1] + col_delta)
                    if (
                        0 <= neighbor[0] < height
                        and 0 <= neighbor[1] < width
                        and neighbor not in seen
                        and grid[neighbor[0]][neighbor[1]] == color
                    ):
                        seen.add(neighbor)
                        queue.append(neighbor)
            cells = tuple(sorted(cells))
            found.append({
                "color": color,
                "cells": cells,
                "size": len(cells),
                "top_left": min(cells),
            })
    return found


def _legend_bbox(grid):
    gray = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 5
    ]
    if not gray:
        raise ValueError("legend rule requires at least one gray cell")
    return (
        min(row for row, _ in gray),
        min(col for _, col in gray),
        max(row for row, _ in gray),
        max(col for _, col in gray),
    )


def _inside(cell, bbox):
    return bbox[0] <= cell[0] <= bbox[2] and bbox[1] <= cell[1] <= bbox[3]


def _rule_facts(grid):
    bbox = _legend_bbox(grid)
    outside_counts = {}
    for color in range(1, 10):
        outside_counts[color] = sum(
            value == color and not _inside((row, col), bbox)
            for row, values in enumerate(grid)
            for col, value in enumerate(values)
        )
    source_color, source_count = 0, 0
    for color in range(1, 10):
        if outside_counts[color] > source_count:
            source_color, source_count = color, outside_counts[color]
    dots = tuple(
        (row, col, grid[row][col])
        for row in range(bbox[0], bbox[2] + 1)
        for col in range(bbox[1], bbox[3] + 1)
        if grid[row][col] not in (0, 5, source_color)
    )
    source_objects = tuple(sorted(
        (
            item for item in _objects_8(grid, background=0)
            if item["color"] == source_color
            and not any(_inside(cell, bbox) for cell in item["cells"])
        ),
        key=lambda item: item["top_left"],
    ))
    return {
        "legend_bbox": bbox,
        "outside_counts": outside_counts,
        "source_color": source_color,
        "source_count": source_count,
        "dots": dots,
        "source_objects": source_objects,
    }


def rule_mirror(grid):
    """Broad, input-pure mirror of the complete canonical Racket rule."""
    errors = _valid_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    facts = _rule_facts(grid)
    output = [list(row) for row in grid]
    pair_count = min(len(facts["dots"]), len(facts["source_objects"]))
    for index in range(pair_count):
        color = facts["dots"][index][2]
        for row, col in facts["source_objects"][index]["cells"]:
            output[row][col] = color
    return output


def _normalize_colored(cells):
    row0 = min(row for row, _, _ in cells)
    col0 = min(col for _, col, _ in cells)
    return tuple(sorted((row - row0, col - col0, value) for row, col, value in cells))


def _canonicalize_colors(cells):
    mapping = {5: 5}
    next_label = 10
    normalized = []
    for row, col, value in sorted(cells):
        if value not in mapping:
            mapping[value] = next_label
            next_label += 1
        normalized.append((row, col, mapping[value]))
    return tuple(normalized)


def _nonzero_signature(grid):
    cells = tuple(
        (row, col, value)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 0
    )
    return _normalize_colored(cells)


def _family_key(grid):
    return _canonicalize_colors(_nonzero_signature(grid))


_PUBLIC_FAMILY_KEYS = {
    _family_key(grid): profile for profile, grid in _PUBLIC_INPUTS.items()
}
if len(_PUBLIC_FAMILY_KEYS) != len(PUBLIC_PROFILES):
    raise AssertionError("official foreground families must be distinct")


def _public_family(grid):
    try:
        return _PUBLIC_FAMILY_KEYS.get(_family_key(grid))
    except (TypeError, ValueError):
        return None


def _cardinal_component_count(cells):
    remaining = set(cells)
    count = 0
    while remaining:
        count += 1
        queue = [remaining.pop()]
        while queue:
            row, col = queue.pop()
            for row_delta, col_delta in DELTAS_4:
                neighbor = (row + row_delta, col + col_delta)
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    queue.append(neighbor)
    return count


def _general_profile(grid, facts):
    dots = facts["dots"]
    source_items = facts["source_objects"]
    bbox = facts["legend_bbox"]
    source = facts["source_color"]
    if len(dots) > len(source_items):
        return "extra_dot"
    if len(source_items) > len(dots):
        return "extra_object"
    if any(
        grid[row][col] == source
        for row in range(bbox[0], bbox[2] + 1)
        for col in range(bbox[1], bbox[3] + 1)
    ):
        return "source_dot_ignored"
    if any(_cardinal_component_count(item["cells"]) > 1 for item in source_items):
        return "diagonal_object"
    if any(
        value not in (0, 5, source)
        and not _inside((row, col), bbox)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
    ):
        return "source_frequency"
    if len({value for _, _, value in dots}) < len(dots):
        return "repeated_dot_color"
    return "ordered_shapes"


def _analysis(grid):
    errors = _valid_grid(grid)
    if errors:
        return {"errors": errors, "scene_profile": None, "facts": {}, "output": None}
    height, width = len(grid), len(grid[0])
    if not 8 <= height <= 30 or not 8 <= width <= 30:
        errors.append("curriculum grids must be between eight and thirty cells per side")
    try:
        facts = _rule_facts(grid)
    except ValueError as exc:
        errors.append(str(exc))
        return {"errors": errors, "scene_profile": None, "facts": {}, "output": None}
    bbox = facts["legend_bbox"]
    legend_height = bbox[2] - bbox[0] + 1
    legend_width = bbox[3] - bbox[1] + 1
    gray_count = sum(value == 5 for row in grid for value in row)
    palette = {value for row in grid for value in row}
    outside_counts = facts["outside_counts"]
    source = facts["source_color"]
    source_count = facts["source_count"]
    competing_max = max((count for color, count in outside_counts.items() if color != source), default=0)
    dots = facts["dots"]
    source_items = facts["source_objects"]
    pair_count = min(len(dots), len(source_items))
    if 0 not in palette:
        errors.append("curriculum scenes require visible zero background")
    if not 4 <= len(palette) <= 10:
        errors.append("curriculum scenes require four through ten colors")
    if gray_count < 10 or not 4 <= legend_height <= 12 or not 4 <= legend_width <= 12:
        errors.append("gray cells must define a substantial four-to-twelve-cell legend rectangle")
    if any(
        grid[row][col] == 0
        for row in range(bbox[0], bbox[2] + 1)
        for col in range(bbox[1], bbox[3] + 1)
    ):
        errors.append("the calibrated legend rectangle may not contain zero holes")
    if source == 0 or source_count <= competing_max:
        errors.append("the outside source color must be the unique positive frequency maximum")
    if not 2 <= len(dots) <= 7 or not 2 <= len(source_items) <= 7:
        errors.append("curriculum scenes require two through seven dots and source objects")
    if abs(len(dots) - len(source_items)) > 1:
        errors.append("dot and source-object counts may differ by at most one")
    if pair_count < 2:
        errors.append("at least two dot/object mappings must fire")
    if any(not 4 <= item["size"] <= 24 for item in source_items):
        errors.append("source objects must contain four through twenty-four cells")
    output = rule_mirror(grid)
    changed = sum(
        before != after
        for before_row, after_row in zip(grid, output)
        for before, after in zip(before_row, after_row)
    )
    expected_changed = sum(source_items[index]["size"] for index in range(pair_count))
    if changed != expected_changed or changed == 0:
        errors.append("exactly the mapped source-object cells must visibly recolor")
    public = _public_family(grid)
    profile = public or _general_profile(grid, facts)
    if profile not in SCENE_PROFILES:
        errors.append("scene does not match a declared semantic profile")
    facts = dict(facts)
    facts.update({
        "legend_shape": (legend_height, legend_width),
        "gray_count": gray_count,
        "palette": tuple(sorted(palette)),
        "dot_count": len(dots),
        "object_count": len(source_items),
        "object_sizes": tuple(item["size"] for item in source_items),
        "pair_count": pair_count,
        "changed": changed,
    })
    return {"errors": errors, "scene_profile": profile, "facts": facts, "output": output}


def canonical_profile_signature(grid):
    try:
        return _PUBLIC_EXACT.get(tuple(tuple(row) for row in grid))
    except TypeError:
        return None


def canonical_family_signature(grid):
    analysis = _analysis(grid)
    profile = analysis["scene_profile"]
    return profile if profile in PUBLIC_PROFILES and not analysis["errors"] else None


def observe_overrides(grid):
    analysis = _analysis(grid)
    return {"scene_profile": analysis["scene_profile"]} if not analysis["errors"] else {}


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    return _analysis(grid)["errors"]


def _embed_public(profile, rng):
    signature = _nonzero_signature(_PUBLIC_INPUTS[profile])
    source_colors = sorted({value for _, _, value in signature if value != 5})
    replacement = rng.sample(NON_SPECIAL_COLORS, len(source_colors))
    color_map = dict(zip(source_colors, replacement))
    transformed = tuple(
        (row, col, 5 if value == 5 else color_map[value])
        for row, col, value in signature
    )
    motif_height = max(row for row, _, _ in transformed) + 1
    motif_width = max(col for _, col, _ in transformed) + 1
    extra_height = rng.randint(2, min(10, 30 - motif_height))
    extra_width = rng.randint(2, min(10, 30 - motif_width))
    row0 = rng.randint(0, extra_height)
    col0 = rng.randint(0, extra_width)
    grid = [[0] * (motif_width + extra_width) for _ in range(motif_height + extra_height)]
    for row, col, value in transformed:
        grid[row0 + row][col0 + col] = value
    return grid


def _normalize_tokens(tokens):
    row0 = min(row for row, _ in tokens)
    col0 = min(col for _, col in tokens)
    return tuple(sorted((row - row0, col - col0) for row, col in set(tokens)))


def _polyomino(rng, target):
    cells = {(0, 0)}
    while len(cells) < target:
        row, col = rng.choice(tuple(sorted(cells)))
        row_delta, col_delta = rng.choice(DELTAS_4)
        cells.add((row + row_delta, col + col_delta))
    return _normalize_tokens(cells)


def _shape_tokens(kind, rng):
    if kind == "diagonal":
        return tuple(
            [(row, col) for row in range(2) for col in range(2)]
            + [(row + 2, col + 2) for row in range(2) for col in range(2)]
        )
    if kind == "solid":
        height, width = rng.randint(2, 4), rng.randint(2, 5)
        return tuple((row, col) for row in range(height) for col in range(width))
    if kind == "hollow":
        height, width = rng.randint(3, 5), rng.randint(3, 5)
        return tuple(
            (row, col)
            for row in range(height) for col in range(width)
            if row in (0, height - 1) or col in (0, width - 1)
        )
    if kind == "cross":
        height, width = rng.choice((3, 5)), rng.choice((3, 5))
        return tuple(sorted(
            {(height // 2, col) for col in range(width)}
            | {(row, width // 2) for row in range(height)}
        ))
    return _polyomino(rng, rng.randint(5, 18))


def _can_place(grid, tokens, clearance=1):
    height, width = len(grid), len(grid[0])
    cells = set(tokens)
    if any(not (0 <= row < height and 0 <= col < width) for row, col in cells):
        return False
    if any(grid[row][col] != 0 for row, col in cells):
        return False
    return not any(
        grid[row][col] != 0
        for token_row, token_col in cells
        for row in range(max(0, token_row - clearance), min(height, token_row + clearance + 1))
        for col in range(max(0, token_col - clearance), min(width, token_col + clearance + 1))
    )


def _place_shape(grid, base_tokens, color, rng, clearance=1):
    base_tokens = _normalize_tokens(base_tokens)
    motif_height = max(row for row, _ in base_tokens) + 1
    motif_width = max(col for _, col in base_tokens) + 1
    if motif_height > len(grid) or motif_width > len(grid[0]):
        return None
    for _ in range(250):
        row0 = rng.randint(0, len(grid) - motif_height)
        col0 = rng.randint(0, len(grid[0]) - motif_width)
        tokens = tuple((row + row0, col + col0) for row, col in base_tokens)
        if _can_place(grid, tokens, clearance=clearance):
            for row, col in tokens:
                grid[row][col] = color
            return tokens
    return None


def _canvas_for(difficulty, rng):
    low, high = {
        "easy": (14, 19),
        "hard": (24, 30),
    }.get(difficulty, (18, 25))
    return rng.randint(low, high), rng.randint(min(18, low), high)


def _random_general(profile, difficulty, rng):
    for _ in range(400):
        height, width = _canvas_for(difficulty, rng)
        grid = [[0] * width for _ in range(height)]
        object_count = (
            rng.randint(2, 3) if difficulty == "easy"
            else rng.randint(4, 6) if difficulty == "hard"
            else rng.randint(3, 5)
        )
        dot_count = object_count
        if profile == "extra_dot":
            dot_count += 1
        elif profile == "extra_object":
            dot_count -= 1
        legend_height = rng.randint(max(5, (dot_count + 1) // 2 + 2), min(10, height - 4))
        legend_width = rng.randint(6, min(10, width - 4))
        legend_row = rng.randint(0, height - legend_height)
        legend_col = rng.randint(0, width - legend_width)
        for row in range(legend_row, legend_row + legend_height):
            for col in range(legend_col, legend_col + legend_width):
                grid[row][col] = 5
        source_color = rng.choice(NON_SPECIAL_COLORS)
        available = [color for color in NON_SPECIAL_COLORS if color != source_color]
        interior = [
            (row, col)
            for row in range(legend_row + 1, legend_row + legend_height - 1)
            for col in range(legend_col + 1, legend_col + legend_width - 1)
        ]
        rng.shuffle(interior)
        if len(interior) < dot_count + (profile == "source_dot_ignored"):
            continue
        if profile == "repeated_dot_color":
            dot_colors = [rng.choice(available) for _ in range(dot_count)]
            dot_colors[1] = dot_colors[0]
        else:
            dot_colors = rng.sample(available, dot_count)
        for (row, col), color in zip(interior, dot_colors):
            grid[row][col] = color
        if profile == "source_dot_ignored":
            row, col = interior[dot_count]
            grid[row][col] = source_color
        success = True
        for index in range(object_count):
            kind = "diagonal" if profile == "diagonal_object" and index == 0 else rng.choice(
                ("solid", "hollow", "cross", "polyomino")
            )
            if _place_shape(grid, _shape_tokens(kind, rng), source_color, rng) is None:
                success = False
                break
        if not success:
            continue
        if profile == "source_frequency":
            distractor_colors = rng.sample(available, rng.randint(1, min(2, len(available))))
            for color in distractor_colors:
                tokens = _polyomino(rng, rng.randint(3, 7))
                if _place_shape(grid, tokens, color, rng) is None:
                    success = False
                    break
        if not success:
            continue
        analysis = _analysis(grid)
        if not analysis["errors"] and analysis["scene_profile"] == profile:
            return grid
    raise AssertionError(f"could not construct legend lesson {profile!r}")


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
    profile = ctx.draw_choice(
        "scene_profile",
        list(PUBLIC_PROFILES) * 2 + list(GENERAL_PROFILES),
    )
    if profile not in SCENE_PROFILES:
        raise ValueError(f"unknown scene_profile: {profile!r}")
    if profile in PUBLIC_PROFILES and overrides.get("scene_profile") is not None:
        return [row[:] for row in _PUBLIC_INPUTS[profile]]
    rng = ctx.draw_rng("scene")
    grid = _embed_public(profile, rng) if profile in PUBLIC_PROFILES else _random_general(
        profile, difficulty, rng
    )
    errors = self_check(grid)
    if errors:
        raise AssertionError("generated invalid legend lesson: " + "; ".join(errors))
    return grid
