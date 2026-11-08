"""Semantic generator for ARC task 5f9a2df57599.

Treat gray (5) as walls and find every orthogonally connected zero region.
Paint a region yellow (4) only when the complete rows immediately above and
below its bounding box are gray and the complete columns immediately left and
right are gray.  The left and right canvas edges count as walls; the top and
bottom edges do not.  A multi-cell vertical region confined to column zero is
explicitly excluded.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "5f9a2df57599"
TASK_ID = "5f9a2df57599"
VERSION = "2.0.0"
RULE_HASH = "5b73d3931a5c"
SUMMARY = "Paint each zero region yellow when all four bounding-box sides are gray walls, with vertical side boundaries allowed and the column-zero vertical exception preserved."
INVARIANTS = [
    "inputs contain only black zero regions and gray (5) walls",
    "zero regions are evaluated as orthogonally connected objects",
    "top and bottom walls must exist inside the canvas and be completely gray across the region bounding-box width",
    "left and right walls may be complete gray columns or the corresponding canvas edge",
    "a multi-row region whose bounding box is only column zero remains black despite otherwise complete walls",
    "only cells belonging to qualifying zero regions become yellow (4); every gray wall and rejected zero region is unchanged",
]

PUBLIC_PROFILES = ("public_1", "public_2", "public_3", "public_4")
GENERAL_PROFILES = (
    "rect_n1", "rect_n2", "rect_n3",
    "irregular_n1", "irregular_n2", "irregular_n3",
    "left_n1",
    "right_n1",
    "mixed_n2", "mixed_n3",
)
SCENE_PROFILES = PUBLIC_PROFILES + GENERAL_PROFILES
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "four exact-public and ten recoverable region/wall lessons",
        "valid": "public_1|public_2|public_3|public_4|rect_n1|rect_n2|rect_n3|irregular_n1|irregular_n2|irregular_n3|left_n1|right_n1|mixed_n2|mixed_n3",
    }
}

_PUBLIC_ROWS = (
    "0000050000050000/0000050000050000/0000050000050000/0000050000050000/0005555500050055/0005000500050050/0005000555555550/0005000500000050/0005555500000055/0000050000000000/0000050000000000/5555550000000000/0000050000000000",
    "0000000000000500055/5500055550000500050/0555550055555555550/5500050050000500050/0000050050000500055/0000050050055550000/0000050050050050000/0000055550050055555/0000005000055550000/0000005000000500000/0000005000000500000/0000005000000500000",
    "00000500000000000/00000500000555550/55555555555500050/00000500000500055/00055550000500050/55550050000555550/00050050000050000/00050050000050000/00055550000050000/00000500000050000/00000500005555000/55555555555005000/00000500005005000/00000500005555000/00000500000050000",
    "000000050000000000/000000050000000000/555000050000000000/005555555555555555/555000050000005000/000000050000005000/000000050000005000/000000050000055550/000005555500050050/555555000555550055/050005000500050050/050005555500055550/050000050000000000/555000050000000000/505000050000000000/555000050000000000",
)
_ORTHOGONAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _decode(text):
    return [[int(value) for value in row] for row in text.split("/")]


_PUBLIC_INPUTS = {name: _decode(text) for name, text in zip(PUBLIC_PROFILES, _PUBLIC_ROWS)}
_PUBLIC_SIGNATURES = {tuple(map(tuple, grid)): profile for profile, grid in _PUBLIC_INPUTS.items()}


def _valid_grid(grid):
    if not isinstance(grid, (list, tuple)) or not 8 <= len(grid) <= 30:
        return ["input must contain eight through thirty rows"]
    if not isinstance(grid[0], (list, tuple)) or not 8 <= len(grid[0]) <= 30:
        return ["input must contain eight through thirty columns"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["input must be rectangular"]
    if any(isinstance(value, bool) or not isinstance(value, int) or value not in (0, 5) for row in grid for value in row):
        return ["input cells must be literal black (0) or gray (5) integers"]
    return []


def _zero_components(grid):
    height, width = len(grid), len(grid[0])
    remaining = {(row, col) for row in range(height) for col in range(width) if grid[row][col] == 0}
    components = []
    while remaining:
        start = remaining.pop()
        reached = {start}
        frontier = [start]
        while frontier:
            row, col = frontier.pop()
            for delta_row, delta_col in _ORTHOGONAL:
                neighbour = row + delta_row, col + delta_col
                if neighbour in remaining:
                    remaining.remove(neighbour)
                    reached.add(neighbour)
                    frontier.append(neighbour)
        components.append(reached)
    return sorted(components, key=lambda cells: (min(row for row, _ in cells), min(col for _, col in cells)))


def _region_facts(grid, cells):
    height, width = len(grid), len(grid[0])
    row0, row1 = min(row for row, _ in cells), max(row for row, _ in cells)
    col0, col1 = min(col for _, col in cells), max(col for _, col in cells)
    top_wall = row0 > 0 and all(grid[row0 - 1][col] == 5 for col in range(col0, col1 + 1))
    bottom_wall = row1 < height - 1 and all(grid[row1 + 1][col] == 5 for col in range(col0, col1 + 1))
    left_wall = col0 == 0 or all(grid[row][col0 - 1] == 5 for row in range(row0, row1 + 1))
    right_wall = col1 == width - 1 or all(grid[row][col1 + 1] == 5 for row in range(row0, row1 + 1))
    excluded_left_vertical = col0 == 0 and col1 == 0 and row1 > row0
    eligible = top_wall and bottom_wall and left_wall and right_wall and not excluded_left_vertical
    rectangle = len(cells) == (row1 - row0 + 1) * (col1 - col0 + 1)
    edge = "left" if col0 == 0 else "right" if col1 == width - 1 else "interior"
    return {
        "cells": tuple(sorted(cells)),
        "bbox": (row0, col0, row1, col1),
        "shape": (row1 - row0 + 1, col1 - col0 + 1),
        "size": len(cells),
        "rectangle": rectangle,
        "edge": edge,
        "top_wall": top_wall,
        "bottom_wall": bottom_wall,
        "left_wall": left_wall,
        "right_wall": right_wall,
        "excluded_left_vertical": excluded_left_vertical,
        "eligible": eligible,
    }


def rule_mirror(grid):
    """Exact Python mirror of the canonical zero-object wall predicate."""
    errors = _valid_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    output = [list(row) for row in grid]
    for cells in _zero_components(grid):
        if _region_facts(grid, cells)["eligible"]:
            for row, col in cells:
                output[row][col] = 4
    return output


def _profile_for(grid, eligible):
    public = _PUBLIC_SIGNATURES.get(tuple(map(tuple, grid)))
    if public:
        return public
    count = len(eligible)
    edges = {facts["edge"] for facts in eligible}
    if edges == {"interior"}:
        stem = "rect" if all(facts["rectangle"] for facts in eligible) else "irregular"
    elif edges == {"left"}:
        stem = "left"
    elif edges == {"right"}:
        stem = "right"
    else:
        stem = "mixed"
    candidate = f"{stem}_n{count}"
    return candidate if candidate in GENERAL_PROFILES else None


def _analysis(grid):
    errors = _valid_grid(grid)
    if errors:
        return {"errors": errors, "scene_profile": None, "facts": None, "output": None}
    regions = tuple(_region_facts(grid, cells) for cells in _zero_components(grid))
    eligible = tuple(facts for facts in regions if facts["eligible"])
    rejected = tuple(facts for facts in regions if not facts["eligible"])
    if not eligible:
        errors.append("at least one zero region must satisfy the four-wall predicate")
    if not rejected:
        errors.append("at least one rejected zero region is required to contrast the selection rule")
    profile = _profile_for(grid, eligible)
    if profile not in SCENE_PROFILES:
        errors.append("grid does not match a declared region-shape/count/edge profile")
    output = rule_mirror(grid)
    changed = {(row, col) for row in range(len(grid)) for col in range(len(grid[0])) if output[row][col] == 4}
    expected = {cell for facts in eligible for cell in facts["cells"]}
    if changed != expected:
        errors.append("yellow output cells do not exactly equal eligible zero-object cells")
    facts = {
        "regions": regions,
        "eligible": eligible,
        "rejected": rejected,
        "eligible_count": len(eligible),
        "changed_count": len(changed),
        "special_exclusions": sum(facts["excluded_left_vertical"] for facts in rejected),
        "scene_profile": profile,
    }
    return {"errors": errors, "scene_profile": profile, "facts": facts, "output": output}


def self_check(grid, *, difficulty=None, meta=None):
    return _analysis(grid)["errors"]


def canonical_profile_signature(grid):
    return _PUBLIC_SIGNATURES.get(tuple(map(tuple, grid)))


def observe_overrides(grid):
    analysis = _analysis(grid)
    return {"scene_profile": analysis["scene_profile"]} if not analysis["errors"] else {}


def _dimension_limits(difficulty):
    if difficulty == "easy":
        return 12, 16
    if difficulty == "hard":
        return 18, 24
    if difficulty == "medium":
        return 14, 20
    return 14, 22


def _tight_connected_shape(height, width, irregular, rng):
    if not irregular:
        return {(row, col) for row in range(height) for col in range(width)}
    minimum = height + width - 1
    for _ in range(100):
        target = rng.randint(minimum, max(minimum, height * width - 1))
        cells = {(rng.randrange(height), rng.randrange(width))}
        while len(cells) < target:
            candidates = []
            for row, col in cells:
                for delta_row, delta_col in _ORTHOGONAL:
                    neighbour = row + delta_row, col + delta_col
                    if 0 <= neighbour[0] < height and 0 <= neighbour[1] < width and neighbour not in cells:
                        candidates.append(neighbour)
            if not candidates:
                break
            cells.add(rng.choice(candidates))
        if (
            len(cells) == target
            and len(cells) < height * width
            and {row for row, _ in cells} == set(range(height))
            and {col for _, col in cells} == set(range(width))
        ):
            return cells
    raise AssertionError("could not build a tight irregular region")


def _separated(box, occupied):
    row0, col0, row1, col1 = box
    return all(
        row1 + 1 < other0 or other2 + 1 < row0 or col1 + 1 < other1 or other3 + 1 < col0
        for other0, other1, other2, other3 in occupied
    )


def _place_room(grid, edge, irregular, occupied, rng):
    height, width = len(grid), len(grid[0])
    for _ in range(150):
        inner_height = rng.randint(1 if not irregular else 2, 4)
        inner_width = rng.randint(2 if edge in ("left", "right") else (2 if irregular else 1), 4)
        if edge == "interior":
            top = rng.randint(1, height - inner_height - 2)
            left = rng.randint(1, width - inner_width - 2)
            box = (top - 1, left - 1, top + inner_height, left + inner_width)
        elif edge == "left":
            top = rng.randint(1, height - inner_height - 2)
            left = 0
            box = (top - 1, 0, top + inner_height, inner_width)
        else:
            top = rng.randint(1, height - inner_height - 2)
            left = width - inner_width
            box = (top - 1, left - 1, top + inner_height, width - 1)
        if not _separated(box, occupied):
            continue
        for row in range(box[0], box[2] + 1):
            for col in range(box[1], box[3] + 1):
                grid[row][col] = 5
        shape = _tight_connected_shape(inner_height, inner_width, irregular, rng)
        for local_row, local_col in shape:
            grid[top + local_row][left + local_col] = 0
        occupied.append(box)
        return True
    return False


def _place_special_exclusion(grid, occupied, rng):
    height = len(grid)
    for _ in range(100):
        inner_height = rng.randint(2, 4)
        top = rng.randint(1, height - inner_height - 2)
        box = (top - 1, 0, top + inner_height, 1)
        if not _separated(box, occupied):
            continue
        for row in range(box[0], box[2] + 1):
            for col in range(0, 2):
                grid[row][col] = 5
        for row in range(top, top + inner_height):
            grid[row][0] = 0
        occupied.append(box)
        return True
    return False


def _place_partial_line(grid, occupied, rng):
    height, width = len(grid), len(grid[0])
    for _ in range(100):
        horizontal = rng.choice((True, False))
        length = rng.randint(2, 6)
        if horizontal:
            row, col = rng.randrange(height), rng.randrange(width - length + 1)
            cells = [(row, value) for value in range(col, col + length)]
        else:
            row, col = rng.randrange(height - length + 1), rng.randrange(width)
            cells = [(value, col) for value in range(row, row + length)]
        if any(grid[row][col] != 0 for row, col in cells):
            continue
        if any(any(box[0] - 1 <= row <= box[2] + 1 and box[1] - 1 <= col <= box[3] + 1 for box in occupied) for row, col in cells):
            continue
        for row, col in cells:
            grid[row][col] = 5
        return True
    return False


def _gray_components(grid):
    height, width = len(grid), len(grid[0])
    remaining = {(row, col) for row in range(height) for col in range(width) if grid[row][col] == 5}
    components = []
    while remaining:
        start = remaining.pop()
        reached = {start}
        frontier = [start]
        while frontier:
            row, col = frontier.pop()
            for delta_row, delta_col in _ORTHOGONAL:
                neighbour = row + delta_row, col + delta_col
                if neighbour in remaining:
                    remaining.remove(neighbour)
                    reached.add(neighbour)
                    frontier.append(neighbour)
        components.append(reached)
    return components


def _connect_gray_network(grid, occupied):
    """Join every wall component to a top-row backbone without touching rooms intentionally."""
    height, width = len(grid), len(grid[0])
    components = _gray_components(grid)
    protected = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 0
        and any(box[0] <= row <= box[2] and box[1] <= col <= box[3] for box in occupied)
    }
    for col in range(width):
        grid[0][col] = 5
    for cells in components:
        frontier = list(cells)
        parents = {cell: None for cell in cells}
        target = None
        cursor = 0
        while cursor < len(frontier):
            row, col = frontier[cursor]
            cursor += 1
            if row == 0:
                target = row, col
                break
            for delta_row, delta_col in _ORTHOGONAL:
                neighbour = row + delta_row, col + delta_col
                if (
                    0 <= neighbour[0] < height
                    and 0 <= neighbour[1] < width
                    and neighbour not in protected
                    and neighbour not in parents
                ):
                    parents[neighbour] = row, col
                    frontier.append(neighbour)
        if target is None:
            return False
        while target is not None:
            grid[target[0]][target[1]] = 5
            target = parents[target]
    return True


def _general_scene(profile, difficulty, rng):
    stem, count_text = profile.rsplit("_n", 1)
    count = int(count_text)
    low, high = _dimension_limits(difficulty)
    for _ in range(500):
        height, width = rng.randint(low, high), rng.randint(low, high)
        grid = [[0 for _ in range(width)] for _ in range(height)]
        occupied = []
        if stem == "left":
            plan = [("left", False)] * count
        elif stem == "right":
            plan = [("right", False)] * count
        elif stem == "mixed":
            plan = [(rng.choice(("left", "right")), False)] + [("interior", rng.random() < 0.5) for _ in range(count - 1)]
        elif stem == "irregular":
            plan = [("interior", index == 0 or rng.random() < 0.5) for index in range(count)]
        else:
            plan = [("interior", False)] * count
        if not all(_place_room(grid, edge, irregular, occupied, rng) for edge, irregular in plan):
            continue
        if difficulty == "hard" and not _place_special_exclusion(grid, occupied, rng):
            continue
        line_count = 1 if difficulty == "easy" else 2 if difficulty in (None, "medium") else 4
        for _ in range(line_count):
            _place_partial_line(grid, occupied, rng)
        if not _connect_gray_network(grid, occupied):
            continue
        analysis = _analysis(grid)
        if not analysis["errors"] and analysis["scene_profile"] == profile and len(_gray_components(grid)) == 1:
            if difficulty != "hard" or analysis["facts"]["special_exclusions"] >= 1:
                return grid
    raise AssertionError(f"could not construct scene profile {profile}")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = sorted(set(overrides) - {"scene_profile"})
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = ctx.draw_choice("scene_profile", PUBLIC_PROFILES * 2 + GENERAL_PROFILES * 5)
    if profile not in SCENE_PROFILES:
        raise ValueError(f"unknown scene_profile: {profile!r}")
    if profile in PUBLIC_PROFILES:
        return [row[:] for row in _PUBLIC_INPUTS[profile]]
    return _general_scene(profile, difficulty, ctx.draw_rng("scene"))
