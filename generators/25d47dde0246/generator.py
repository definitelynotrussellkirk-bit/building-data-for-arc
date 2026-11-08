"""Semantic generator for ARC task 25d47dde0246.

The output is the tight rectangular crop spanning every nonzero input cell.
Zeros inside that bounding box are retained, while padding outside it is
discarded.  The exact oracle also defines the canonical empty-input fallback,
but generated training scenes contain substantial task content.
"""
from __future__ import annotations

from collections import deque
from typing import Callable

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "25d47dde0246"
TASK_ID = "25d47dde0246"
VERSION = "3.1.0"
RULE_HASH = "88475e062f41"
SUMMARY = (
    "Crop the input to the tight bounding box of all nonzero cells, preserving "
    "every cell inside that rectangle; scheduled disconnected witnesses teach "
    "that every component contributes to the crop."
)
INVARIANTS = [
    "every nonzero cell contributes to one joint bounding box",
    "zeros inside the bounding box are preserved",
    "only rows and columns strictly outside the joint bounding box are removed",
    "ordinary generated lessons contain at least four nonzero cells",
    "every three consecutive default samples include a disconnected joint-bbox witness",
    "every four consecutive default samples include an exact canonical-profile input",
]

PUBLIC_PROFILES = tuple(f"public_{index}" for index in range(1, 6))
GENERAL_PROFILES = (
    "monochrome_connected",
    "multicolor_connected",
    "disconnected_objects",
    "sparse_bbox",
    "internal_hole",
    "narrow_row",
    "narrow_col",
    "touches_horizontal_edge",
    "touches_vertical_edge",
    "full_palette",
)
SCENE_PROFILES = PUBLIC_PROFILES + GENERAL_PROFILES

EXAMPLES_NEEDED = 3
LESSON_SCHEDULE_PERIOD = 4
TEACHING_WITNESS_PERIOD = 2
TEACHING_WITNESS_OFFSET = 1
TEACHING_WITNESS_PROFILE = "disconnected_objects"
CANONICAL_SUPPORT_OFFSET = 2
SCHEDULE_PROFILES = ("ordinary_mix", "joint_bbox_witness", "canonical_support")
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "disconnected witness every other sample, exact-public support once per four samples, otherwise generalized joint-bbox lessons",
        "valid": "public_1|public_2|public_3|public_4|public_5|monochrome_connected|multicolor_connected|disconnected_objects|sparse_bbox|internal_hole|narrow_row|narrow_col|touches_horizontal_edge|touches_vertical_edge|full_palette",
    }
}

_PUBLIC_ROWS = (
    "0000000000/0000000000/0000333000/0000030000/0000000000/0000000000/0000000000/0000000000",
    "00000000000/00000000000/00000000000/00000000000/00000000000/07000000000/07700000000/00000000000/00000000000",
    "000000000/000004000/000004400/000000440/000000000/000000000/000000000",
    "0000000000/0000000000/0000000000/0000000000/0000000000/0000000000/0006060000/0006660000/0000000000/0000000000",
    "000000000000/000000000000/000000000000/000000000200/000000002220/000000000200/000000000000/000000000000",
)


def _decode(text):
    return [[int(value) for value in row] for row in text.split("/")]


_PUBLIC_INPUTS = {name: _decode(text) for name, text in zip(PUBLIC_PROFILES, _PUBLIC_ROWS)}
_PUBLIC_SIGNATURES = {tuple(map(tuple, grid)): profile for profile, grid in _PUBLIC_INPUTS.items()}
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def schedule_profile(seed, sample_index, difficulty=None):
    """Expose semantic-witness and canonical-support lanes for default sampling."""
    del seed, difficulty
    sample_index = int(sample_index)
    if sample_index % TEACHING_WITNESS_PERIOD == TEACHING_WITNESS_OFFSET:
        return "joint_bbox_witness"
    if sample_index % LESSON_SCHEDULE_PERIOD == CANONICAL_SUPPORT_OFFSET:
        return "canonical_support"
    return "ordinary_mix"


def _valid_grid(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be non-empty"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if not 1 <= len(grid) <= 30 or not 1 <= width <= 30:
        return ["grid dimensions must be within 1..30"]
    if any(isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be literal ARC integers 0..9"]
    return []


def _bbox(grid):
    cells = [(row, col) for row in range(len(grid)) for col in range(len(grid[0])) if grid[row][col] != 0]
    if not cells:
        return None
    top = min(row for row, _ in cells)
    bottom = max(row for row, _ in cells)
    left = min(col for _, col in cells)
    right = max(col for _, col in cells)
    return top, left, bottom - top + 1, right - left + 1


def rule_mirror(grid):
    errors = _valid_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    box = _bbox(grid)
    if box is None:
        return [[0]]
    top, left, height, width = box
    return [list(row[left:left + width]) for row in grid[top:top + height]]


def _components(grid):
    height, width = len(grid), len(grid[0])
    unseen = {(row, col) for row in range(height) for col in range(width) if grid[row][col] != 0}
    components = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        queue, cells = deque([start]), []
        while queue:
            row, col = queue.popleft()
            cells.append((row, col))
            for dr, dc in _CARDINAL:
                neighbor = row + dr, col + dc
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    queue.append(neighbor)
        components.append(sorted(cells))
    return sorted(components, key=lambda cells: cells[0])


def _largest_component_crop(grid):
    """Canonical-fitting rival: crop only one largest nonzero component."""
    errors = _valid_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    components = _components(grid)
    if not components:
        return [[0]]
    component = min(components, key=lambda cells: (-len(cells), cells[0]))
    top = min(row for row, _ in component)
    bottom = max(row for row, _ in component)
    left = min(col for _, col in component)
    right = max(col for _, col in component)
    return [list(row[left:right + 1]) for row in grid[top:bottom + 1]]


SEMANTIC_RIVALS: dict[str, Callable] = {
    "largest_component_only": _largest_component_crop,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def _witness_joint_bbox_uses_all_components(grid):
    return not self_check(grid) and _largest_component_crop(grid) != rule_mirror(grid)


SEMANTIC_WITNESSES = {
    "joint_bbox_uses_all_components": _witness_joint_bbox_uses_all_components,
}
WITNESS_RIVALS = {
    "joint_bbox_uses_all_components": ["largest_component_only"],
}


def lesson_identifiable(demos, query):
    """Require exact demonstrations that falsify every declared shortcut."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]

    reasons = []
    if not isinstance(query, dict) or "input" not in query:
        reasons.append("query must contain an input grid")
    else:
        query_errors = self_check(query["input"])
        if query_errors:
            reasons.append(f"query input is invalid: {query_errors[0]}")

    refuted = {name: False for name in LESSON_COMPETITORS}
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        errors = self_check(demo["input"])
        if errors:
            reasons.append(f"demo {index} input is invalid: {errors[0]}")
            continue
        expected = rule_mirror(demo["input"])
        if demo["output"] != expected:
            reasons.append(f"demo {index} output is not the exact joint nonzero bbox crop")
        for name, rival in LESSON_COMPETITORS.items():
            refuted[name] = refuted[name] or rival(demo["input"]) != expected

    for name, was_refuted in refuted.items():
        if not was_refuted:
            reasons.append(f"demonstrations do not refute rival {name}")
    return reasons


def _has_internal_hole(grid, box):
    if box is None:
        return False
    top, left, height, width = box
    if height < 3 or width < 3:
        return False
    zeros = {
        (row, col)
        for row in range(top, top + height)
        for col in range(left, left + width)
        if grid[row][col] == 0
    }
    boundary = {
        cell
        for cell in zeros
        if cell[0] in {top, top + height - 1} or cell[1] in {left, left + width - 1}
    }
    queue = deque(boundary)
    reachable = set(boundary)
    while queue:
        row, col = queue.popleft()
        for dr, dc in _CARDINAL:
            neighbor = row + dr, col + dc
            if neighbor in zeros and neighbor not in reachable:
                reachable.add(neighbor)
                queue.append(neighbor)
    return bool(zeros - reachable)


def _profile_for(grid, facts):
    public = _PUBLIC_SIGNATURES.get(tuple(map(tuple, grid)))
    if public:
        return public
    box = facts["bbox"]
    if box is None:
        return None
    touches = facts["touches"]
    if touches in ({"top"}, {"bottom"}):
        return "touches_horizontal_edge"
    if touches in ({"left"}, {"right"}):
        return "touches_vertical_edge"
    if touches:
        return None
    if box[2] == 1:
        return "narrow_row"
    if box[3] == 1:
        return "narrow_col"
    if len(facts["palette"]) >= 6:
        return "full_palette"
    if facts["internal_hole"]:
        return "internal_hole"
    if facts["bbox_area"] >= 25 and facts["density"] <= 0.2:
        return "sparse_bbox"
    if facts["component_count"] >= 2:
        return "disconnected_objects"
    if facts["component_count"] == 1 and len(facts["palette"]) >= 2:
        return "multicolor_connected"
    if facts["component_count"] == 1 and len(facts["palette"]) == 1:
        return "monochrome_connected"
    return None


def _extract_facts(grid):
    box = _bbox(grid)
    nonzero = [(row, col, value) for row, values in enumerate(grid) for col, value in enumerate(values) if value != 0]
    components = _components(grid)
    touches = set()
    if box is not None:
        top, left, box_h, box_w = box
        if top == 0:
            touches.add("top")
        if left == 0:
            touches.add("left")
        if top + box_h == len(grid):
            touches.add("bottom")
        if left + box_w == len(grid[0]):
            touches.add("right")
    area = box[2] * box[3] if box else 0
    facts = {
        "height": len(grid),
        "width": len(grid[0]),
        "bbox": box,
        "bbox_area": area,
        "nonzero_count": len(nonzero),
        "palette": sorted({value for _, _, value in nonzero}),
        "components": components,
        "component_count": len(components),
        "touches": touches,
        "density": len(nonzero) / area if area else 0.0,
        "internal_hole": _has_internal_hole(grid, box),
        "output": rule_mirror(grid),
    }
    facts["scene_profile"] = _profile_for(grid, facts)
    return facts


def _profile_errors(facts):
    profile, box = facts["scene_profile"], facts["bbox"]
    if profile in PUBLIC_PROFILES:
        return []
    errors = []
    if facts["nonzero_count"] < 4:
        errors.append("generated training scenes require at least four nonzero cells")
    if profile in {"monochrome_connected", "multicolor_connected"} and (box is None or min(box[2:]) < 2):
        errors.append("connected profiles require a genuinely two-dimensional crop")
    if profile == "monochrome_connected" and facts["density"] >= 1.0:
        errors.append("monochrome_connected must retain at least one zero inside its crop")
    if profile == "disconnected_objects" and (facts["component_count"] != 2 or facts["density"] <= 0.2):
        errors.append("disconnected_objects requires exactly two substantial objects")
    if profile == "sparse_bbox" and (facts["component_count"] < 2 or facts["bbox_area"] < 25 or facts["density"] > 0.2):
        errors.append("sparse_bbox requires separated sparse cells spanning area at least 25")
    if profile == "internal_hole" and (not facts["internal_hole"] or box is None or min(box[2:]) < 5):
        errors.append("internal_hole requires a substantial enclosed zero region")
    if profile in {"narrow_row", "narrow_col"} and facts["nonzero_count"] < 5:
        errors.append("narrow lessons require length at least five")
    if profile and profile.startswith("touches_") and facts["nonzero_count"] < 6:
        errors.append("single-edge lessons require substantial content")
    if profile == "full_palette" and len(facts["palette"]) < 6:
        errors.append("full_palette requires at least six nonzero colors")
    return errors


def _analysis(grid):
    errors = _valid_grid(grid)
    if errors:
        return {"errors": errors, "facts": None, "scene_profile": None, "output": None}
    facts = _extract_facts(grid)
    if facts["scene_profile"] not in SCENE_PROFILES:
        errors.append("grid does not match a declared nondegenerate scene profile")
    else:
        errors.extend(_profile_errors(facts))
    return {"errors": errors, "facts": facts, "scene_profile": facts["scene_profile"], "output": facts["output"]}


def self_check(grid, *, difficulty=None, meta=None):
    return _analysis(grid)["errors"]


def canonical_profile_signature(grid):
    return _PUBLIC_SIGNATURES.get(tuple(map(tuple, grid)))


def observe_overrides(grid):
    analysis = _analysis(grid)
    return {"scene_profile": analysis["scene_profile"]} if not analysis["errors"] else {}


def _size_range(difficulty):
    if difficulty == "easy":
        return (7, 11), (8, 12)
    if difficulty == "medium":
        return (9, 15), (10, 17)
    if difficulty == "hard":
        return (12, 21), (13, 23)
    return (8, 17), (9, 19)


def _blank(height, width):
    return [[0 for _ in range(width)] for _ in range(height)]


def _normalize(cells):
    top = min(row for row, _ in cells)
    left = min(col for _, col in cells)
    return sorted((row - top, col - left) for row, col in cells)


def _random_poly(rng, count):
    cells = {(0, 0)}
    while len(cells) < count:
        row, col = rng.choice(tuple(cells))
        dr, dc = rng.choice(_CARDINAL)
        cells.add((row + dr, col + dc))
    return _normalize(cells)


def _paint(grid, cells, top, left, colors):
    for index, (row, col) in enumerate(cells):
        grid[top + row][left + col] = colors[index % len(colors)]


def _place_interior(grid, cells, rng, colors):
    shape_h = max(row for row, _ in cells) + 1
    shape_w = max(col for _, col in cells) + 1
    top = rng.randint(1, len(grid) - shape_h - 1)
    left = rng.randint(1, len(grid[0]) - shape_w - 1)
    _paint(grid, cells, top, left, colors)


def _candidate_scene(difficulty, profile, rng):
    (h_low, h_high), (w_low, w_high) = _size_range(difficulty)
    height, width = rng.randint(h_low, h_high), rng.randint(w_low, w_high)
    height, width = max(height, 7), max(width, 8)
    grid = _blank(height, width)
    colors = [1, 2, 3, 4, 5, 6, 7, 8, 9]

    if profile == "monochrome_connected":
        cells = _random_poly(rng, rng.randint(4, 12))
        _place_interior(grid, cells, rng, [rng.choice(colors)])
    elif profile == "multicolor_connected":
        cells = _random_poly(rng, rng.randint(6, 18))
        palette = rng.sample(colors, rng.randint(2, 5))
        _place_interior(grid, cells, rng, palette)
    elif profile == "disconnected_objects":
        height, width = max(height, 9), max(width, 12)
        grid = _blank(height, width)
        first = [(row, col) for row in range(3) for col in range(3)]
        second = [(row, col) for row in range(3) for col in range(3)]
        _paint(grid, first, 2, 1, [rng.choice(colors)])
        _paint(grid, second, 2, 6, [rng.choice(colors)])
    elif profile == "sparse_bbox":
        height, width = max(height, 9), max(width, 10)
        grid = _blank(height, width)
        top, left, bottom, right = 1, 1, height - 2, width - 2
        for index, (row, col) in enumerate(((top, left), (top, right), (bottom, left), (bottom, right))):
            grid[row][col] = colors[(rng.randrange(len(colors)) + index) % len(colors)]
    elif profile == "internal_hole":
        box_h, box_w = rng.randint(5, min(8, height - 2)), rng.randint(5, min(8, width - 2))
        top, left = rng.randint(1, height - box_h - 1), rng.randint(1, width - box_w - 1)
        color = rng.choice(colors)
        for row in range(top, top + box_h):
            for col in range(left, left + box_w):
                grid[row][col] = color
        hole_h = rng.randint(1, box_h - 2)
        hole_w = rng.randint(1, box_w - 2)
        hole_top = top + rng.randint(1, box_h - hole_h - 1)
        hole_left = left + rng.randint(1, box_w - hole_w - 1)
        for row in range(hole_top, hole_top + hole_h):
            for col in range(hole_left, hole_left + hole_w):
                grid[row][col] = 0
    elif profile == "narrow_row":
        length = rng.randint(5, min(10, width - 2))
        row, left = rng.randint(1, height - 2), rng.randint(1, width - length - 1)
        first, second = rng.sample(colors, 2)
        for index, col in enumerate(range(left, left + length)):
            grid[row][col] = first if index % 3 else second
    elif profile == "narrow_col":
        length = rng.randint(5, min(10, height - 2))
        top, col = rng.randint(1, height - length - 1), rng.randint(1, width - 2)
        first, second = rng.sample(colors, 2)
        for index, row in enumerate(range(top, top + length)):
            grid[row][col] = first if index % 3 else second
    elif profile in {"touches_horizontal_edge", "touches_vertical_edge"}:
        if profile == "touches_horizontal_edge":
            box_h = rng.randint(3, min(6, height - 1))
            box_w = rng.randint(4, min(8, width - 2))
            top = rng.choice((0, height - box_h))
            left = rng.randint(1, width - box_w - 1)
        else:
            box_h = rng.randint(4, min(8, height - 2))
            box_w = rng.randint(3, min(6, width - 1))
            top = rng.randint(1, height - box_h - 1)
            left = rng.choice((0, width - box_w))
        color = rng.choice(colors)
        for row in range(top, top + box_h):
            for col in range(left, left + box_w):
                grid[row][col] = color
        interior = [(row, col) for row in range(top + 1, top + box_h - 1) for col in range(left + 1, left + box_w - 1)]
        rng.shuffle(interior)
        for row, col in interior[:rng.randint(1, min(4, len(interior)))]:
            grid[row][col] = 0
    elif profile == "full_palette":
        cells = [(row, col) for row in range(3) for col in range(3)]
        palette = colors[:]
        rng.shuffle(palette)
        _place_interior(grid, cells, rng, palette)
    else:
        raise ValueError(f"unknown scene_profile: {profile!r}")
    return grid


def _general_scene(difficulty, profile, rng):
    for _ in range(200):
        try:
            grid = _candidate_scene(difficulty, profile, rng)
        except ValueError:
            continue
        analysis = _analysis(grid)
        if not analysis["errors"] and analysis["scene_profile"] == profile:
            return grid
    raise AssertionError(f"could not construct {profile}")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = sorted(set(overrides) - {"scene_profile"})
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION, task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    ordinary_profiles = (
        PUBLIC_PROFILES
        + ("monochrome_connected",) * 20
        + ("internal_hole",) * 10
        + ("narrow_row", "narrow_col") * 5
        + ("touches_horizontal_edge", "touches_vertical_edge") * 10
        + ("multicolor_connected", "disconnected_objects", "sparse_bbox", "full_palette") * 2
    )
    if overrides.get("scene_profile") is not None:
        profile = ctx.draw_choice("scene_profile", SCENE_PROFILES)
    else:
        lane = schedule_profile(seed, sample_index, difficulty)
        if lane == "joint_bbox_witness":
            profile = ctx.draw_choice("scene_profile", (TEACHING_WITNESS_PROFILE,))
        elif lane == "canonical_support":
            profile = ctx.draw_choice("scene_profile", PUBLIC_PROFILES)
        else:
            profile = ctx.draw_choice("scene_profile", ordinary_profiles)
    if profile not in SCENE_PROFILES:
        raise ValueError(f"unknown scene_profile: {profile!r}")
    if profile in PUBLIC_PROFILES:
        return [row[:] for row in _PUBLIC_INPUTS[profile]]
    return _general_scene(difficulty, profile, ctx.draw_rng("geometry"))
