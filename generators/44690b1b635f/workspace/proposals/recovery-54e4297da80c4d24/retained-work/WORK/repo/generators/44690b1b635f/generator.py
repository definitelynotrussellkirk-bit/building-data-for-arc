"""Semantic generator for ARC task 44690b1b635f.

Colors other than 0 and 8 are markers.  The marker color occurring exactly
once selects the BFS origin; the other marker color supplies the odd-distance
checkerboard color.  Traverse every 4-connected cell that is not wall color
8.  Fill only reachable 0-cells, alternating the singleton and arm colors by
distance parity.  Preserve walls, markers, and unreachable 0-cells.
"""
from __future__ import annotations

from collections import deque

from puzzle_generators.base import gen_ctx


GENERATOR_ID = "44690b1b635f"
TASK_ID = GENERATOR_ID
VERSION = "3.1.0"
RULE_HASH = "72a0e00e932b"
SUMMARY = (
    "BFS-fill reachable zero cells around a singleton marker with alternating "
    "marker colors; wall 8 blocks traversal."
)

INVARIANTS = [
    "background cells are 0 and walls are 8",
    "exactly two non-wall marker colors occur",
    "exactly one marker color occurs once and selects the BFS origin",
    "the other marker color occurs at least twice and supplies odd-distance fills",
    "4-neighbor BFS crosses markers and zeros but never walls",
    "only reachable zeros change; walls, markers, and unreachable zeros are preserved",
]

PUBLIC_PROFILES = ("public_train_1", "public_train_2", "public_test_1")
FIXED_GENERAL_PROFILES = (
    "open_field",
    "offcenter_seed",
    "edge_seed",
    "many_arm_markers",
    "parity_conflict",
    "split_gate",
    "disconnected_regions",
    "sealed_chamber",
    "labyrinth",
    "narrow_corridor",
    "wall_islands",
    "boundary_walls",
    "multiple_chambers",
)
PROCEDURAL_PROFILES = ("procedural_maze",)
GENERAL_PROFILES = FIXED_GENERAL_PROFILES + PROCEDURAL_PROFILES
SCENE_PROFILES = PUBLIC_PROFILES + GENERAL_PROFILES
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
AXES = {
    "scene_profile": {
        "type": "str",
        "default": (
            "uniform rng over three linked public, thirteen fixed semantic, "
            "and one procedural-maze lesson"
        ),
        "valid": "|".join(SCENE_PROFILES),
    }
}


_PUBLIC_MASKS = {
    "public_train_1": (
        "00080008000008",
        "88088808088808",
        "08000808080888",
        "08888808080000",
        "00000008088808",
        "88888808000808",
        "80000808880808",
        "88880800080800",
        "0008a888880880",
        "8808ca00000080",
        "0808a888888880",
        "08880800000000",
        "00000808888888",
    ),
    "public_train_2": (
        "800000888888088808808880",
        "008880000008000808008080",
        "888080888808880808888080",
        "800080800800080800000080",
        "808880880808880880888880",
        "808000080808000080800000",
        "80888888080888888a888880",
        "8000000008000000aca00080",
        "88088808880888888a888080",
        "080808080008000080808080",
        "088808880888088088808880",
    ),
    "public_test_1": (
        "880800800000000",
        "0808888a8888888",
        "080000ac8000008",
        "0888888a8880888",
        "000000800080800",
        "888880888080808",
        "000080008080808",
        "888088808080888",
        "008000808080000",
        "808880888088808",
        "800080000000808",
        "888080888888808",
        "008080800000008",
        "808880808888888",
        "800000808000000",
    ),
}

_DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))
_SUPPORTED_DIMENSIONS = {(10, 12), (13, 16), (16, 24)}


def _band(difficulty):
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return difficulty
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def _dimensions(band):
    return {"easy": (10, 12), "medium": (13, 16), "hard": (16, 24)}[band]


def _blank_roles(height, width):
    return [["0" for _ in range(width)] for _ in range(height)]


def _put_markers(grid, center, arms):
    cr, cc = center
    if grid[cr][cc] == "8":
        raise RuntimeError("center marker overlaps a wall")
    grid[cr][cc] = "c"
    for row, col in arms:
        if grid[row][col] == "8" or (row, col) == center:
            raise RuntimeError("arm marker overlaps a wall or center")
        grid[row][col] = "a"


def _general_roles(profile, band):
    height, width = _dimensions(band)
    grid = _blank_roles(height, width)
    mid_r, mid_c = height // 2, width // 2

    if profile == "open_field":
        center = (mid_r, mid_c)
        arms = ((mid_r - 1, mid_c), (mid_r + 1, mid_c), (mid_r, mid_c + 1))
    elif profile == "offcenter_seed":
        center = (2, 3)
        arms = ((1, 3), (2, 2), (3, 3))
    elif profile == "edge_seed":
        center = (0, 2)
        arms = ((0, 1), (0, 3), (1, 2))
    elif profile == "many_arm_markers":
        center = (mid_r, mid_c)
        arms = tuple(
            (mid_r + dr, mid_c + dc)
            for dr, dc in (
                (-2, 0),
                (-1, -1),
                (-1, 1),
                (0, -2),
                (0, 2),
                (1, -1),
                (1, 1),
                (2, 0),
            )
        )
    elif profile == "parity_conflict":
        center = (mid_r, mid_c)
        arms = ((mid_r - 2, mid_c), (mid_r, mid_c - 2), (mid_r + 2, mid_c))
    elif profile == "split_gate":
        wall_col = mid_c
        for row in range(height):
            if row != mid_r:
                grid[row][wall_col] = "8"
        center = (mid_r, wall_col - 2)
        arms = (
            (mid_r - 1, wall_col - 2),
            (mid_r + 1, wall_col - 2),
            (mid_r, wall_col + 2),
        )
    elif profile == "disconnected_regions":
        wall_col = mid_c
        for row in range(height):
            grid[row][wall_col] = "8"
        center = (mid_r, wall_col - 2)
        arms = (
            (mid_r - 1, wall_col - 2),
            (mid_r + 1, wall_col - 2),
            (mid_r, wall_col - 3),
        )
    elif profile == "sealed_chamber":
        top, left = 2, 2
        bottom, right = min(height - 3, 8), min(width - 3, 10)
        for col in range(left, right + 1):
            grid[top][col] = grid[bottom][col] = "8"
        for row in range(top, bottom + 1):
            grid[row][left] = grid[row][right] = "8"
        center = (top + 2, left + 2)
        arms = (
            (top + 1, left + 2),
            (top + 2, left + 1),
            (top + 3, left + 2),
        )
    elif profile == "labyrinth":
        columns = (3, 7, 11) if width >= 16 else (3, 7)
        for index, col in enumerate(columns):
            gate = 1 if index % 2 == 0 else height - 2
            for row in range(height):
                if row != gate:
                    grid[row][col] = "8"
        center = (1, 1)
        arms = ((2, 1), (1, 2), (height - 2, width - 2))
    elif profile == "narrow_corridor":
        for row in range(height):
            for col in range(width):
                grid[row][col] = "8"
        path = []
        for row in range(1, height - 1):
            if row % 2:
                cols = range(1, width - 1)
            else:
                cols = (width - 2,) if ((row // 2) % 2) else (1,)
            for col in cols:
                grid[row][col] = "0"
                path.append((row, col))
        center = path[0]
        arms = (path[min(2, len(path) - 1)], path[len(path) // 2], path[-1])
    elif profile == "wall_islands":
        for row in range(2, height - 1, 3):
            for col in range(2, width - 1, 4):
                grid[row][col] = "8"
                if col + 1 < width - 1:
                    grid[row][col + 1] = "8"
        center = (mid_r, mid_c)
        while grid[center[0]][center[1]] == "8":
            center = (center[0] + 1, center[1])
        arms = ((0, 0), (height - 1, 0), (height - 1, width - 1))
    elif profile == "boundary_walls":
        for row in range(height):
            grid[row][0] = grid[row][width - 1] = "8"
        for col in range(width):
            grid[0][col] = grid[height - 1][col] = "8"
        center = (mid_r, mid_c)
        arms = ((mid_r - 1, mid_c), (mid_r, mid_c - 1), (mid_r + 1, mid_c))
    elif profile == "multiple_chambers":
        for col, gate in ((width // 3, 2), (2 * width // 3, height - 3)):
            for row in range(height):
                if row != gate:
                    grid[row][col] = "8"
        center = (2, 1)
        arms = ((1, 1), (3, 1), (height - 3, width - 2))
    else:
        raise ValueError(f"unknown scene_profile: {profile!r}")

    _put_markers(grid, center, arms)
    return tuple("".join(row) for row in grid)


def _procedural_maze_roles(context, band):
    """Build a deterministic perfect maze on the task's 4-neighbor lattice.

    Odd/odd interior cells are maze rooms.  A randomized depth-first spanning
    tree opens exactly one connector for each tree edge, leaving the perimeter
    and every even/even cell as wall 8.  The result is connected and acyclic,
    so wall topology—not just marker color—varies with the keyed draw.
    """
    height, width = _dimensions(band)
    grid = [["8" for _ in range(width)] for _ in range(height)]
    rooms = [
        (row, col)
        for row in range(1, height - 1, 2)
        for col in range(1, width - 1, 2)
    ]
    for row, col in rooms:
        grid[row][col] = "0"

    rng = context.draw_rng("procedural_maze_topology")
    start = rng.choice(rooms)
    visited = {start}
    stack = [start]
    while stack:
        row, col = stack[-1]
        neighbors = [
            (row + dr, col + dc)
            for dr, dc in ((-2, 0), (2, 0), (0, -2), (0, 2))
            if 1 <= row + dr < height - 1
            and 1 <= col + dc < width - 1
            and (row + dr, col + dc) not in visited
        ]
        if not neighbors:
            stack.pop()
            continue
        next_row, next_col = rng.choice(neighbors)
        grid[(row + next_row) // 2][(col + next_col) // 2] = "0"
        visited.add((next_row, next_col))
        stack.append((next_row, next_col))

    open_cells = [
        (row, col)
        for row in range(1, height - 1)
        for col in range(1, width - 1)
        if grid[row][col] == "0"
    ]
    center, *arms = rng.sample(open_cells, 4)
    _put_markers(grid, center, tuple(arms))
    return tuple("".join(row) for row in grid)


def _is_procedural_maze_signature(signature):
    """Recognize the bounded perfect-maze grammar without trusting provenance."""
    height = len(signature)
    width = len(signature[0]) if signature else 0
    if (height, width) not in _SUPPORTED_DIMENSIONS:
        return False
    if any(
        len(row) != width or set(row) - {"0", "8", "c", "a"}
        for row in signature
    ):
        return False
    if sum(row.count("c") for row in signature) != 1:
        return False
    if sum(row.count("a") for row in signature) != 3:
        return False
    if any(
        signature[row][col] != "8"
        for row in range(height)
        for col in range(width)
        if row in (0, height - 1) or col in (0, width - 1)
    ):
        return False

    traversable = set()
    for row in range(1, height - 1):
        for col in range(1, width - 1):
            value = signature[row][col]
            if row % 2 == 1 and col % 2 == 1 and value == "8":
                return False
            if row % 2 == 0 and col % 2 == 0 and value != "8":
                return False
            if value != "8":
                traversable.add((row, col))
    if not traversable:
        return False

    start = next(iter(traversable))
    seen = {start}
    frontier = deque([start])
    while frontier:
        row, col = frontier.popleft()
        for dr, dc in _DIRS:
            neighbor = (row + dr, col + dc)
            if neighbor in traversable and neighbor not in seen:
                seen.add(neighbor)
                frontier.append(neighbor)
    if seen != traversable:
        return False

    edge_count = sum(
        (row + dr, col + dc) in traversable
        for row, col in traversable
        for dr, dc in ((1, 0), (0, 1))
    )
    return edge_count == len(traversable) - 1


_PUBLIC_SIGNATURES = {mask: profile for profile, mask in _PUBLIC_MASKS.items()}
_GENERAL_SIGNATURES = {
    _general_roles(profile, band): profile
    for profile in FIXED_GENERAL_PROFILES
    for band in ("easy", "medium", "hard")
}
if len(_GENERAL_SIGNATURES) != 3 * len(FIXED_GENERAL_PROFILES):
    raise RuntimeError("general scene signatures must be unique across profiles and bands")


def _validate_grid(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be non-empty"], 0, 0
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid must have non-empty rows"], 0, 0
    height, width = len(grid), len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"], height, width
    for row in grid:
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return ["cells must be integer ARC colors 0..9"], height, width
    return [], height, width


def _semantic_signature(grid, center_color, arm_color):
    return tuple(
        "".join(
            "0"
            if value == 0
            else "8"
            if value == 8
            else "c"
            if value == center_color
            else "a"
            for value in row
        )
        for row in grid
    )


def _analysis(grid):
    errors, height, width = _validate_grid(grid)
    result = {
        "errors": errors,
        "height": height,
        "width": width,
        "scene_profile": None,
    }
    if errors:
        return result

    marker_positions = {}
    for row in range(height):
        for col in range(width):
            value = grid[row][col]
            if value not in (0, 8):
                marker_positions.setdefault(value, []).append((row, col))
    if len(marker_positions) != 2:
        errors.append(
            f"expected exactly two non-wall marker colors, got {sorted(marker_positions)}"
        )
        return result
    singleton_colors = [
        color for color, cells in marker_positions.items() if len(cells) == 1
    ]
    if len(singleton_colors) != 1:
        errors.append("expected exactly one marker color to occur once")
        return result
    center_color = singleton_colors[0]
    arm_color = next(color for color in marker_positions if color != center_color)
    if len(marker_positions[arm_color]) < 2:
        errors.append("arm marker color must occur at least twice")
        return result

    start = marker_positions[center_color][0]
    distances = {start: 0}
    frontier = deque([start])
    while frontier:
        row, col = frontier.popleft()
        for dr, dc in _DIRS:
            nr, nc = row + dr, col + dc
            if (
                0 <= nr < height
                and 0 <= nc < width
                and grid[nr][nc] != 8
                and (nr, nc) not in distances
            ):
                distances[(nr, nc)] = distances[(row, col)] + 1
                frontier.append((nr, nc))

    output = [list(row) for row in grid]
    reachable_zeros = []
    for (row, col), distance in distances.items():
        if grid[row][col] == 0:
            output[row][col] = center_color if distance % 2 == 0 else arm_color
            reachable_zeros.append((row, col))
    unreachable_zeros = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 0 and (row, col) not in distances
    ]
    signature = _semantic_signature(grid, center_color, arm_color)
    profile = _PUBLIC_SIGNATURES.get(signature) or _GENERAL_SIGNATURES.get(signature)
    if profile is None and _is_procedural_maze_signature(signature):
        profile = "procedural_maze"
    if profile not in SCENE_PROFILES:
        errors.append("grid does not match a declared semantic lesson")
    if not reachable_zeros:
        errors.append("lesson must contain at least one reachable zero cell to fill")
    arm_even_parity = sum(
        distances.get(cell, 1) % 2 == 0 for cell in marker_positions[arm_color]
    )
    result.update(
        {
            "errors": errors,
            "scene_profile": profile,
            "center_color": center_color,
            "arm_color": arm_color,
            "center": start,
            "arm_positions": tuple(marker_positions[arm_color]),
            "distances": distances,
            "reachable_zeros": tuple(reachable_zeros),
            "unreachable_zeros": tuple(unreachable_zeros),
            "wall_count": sum(value == 8 for row in grid for value in row),
            "arm_even_parity": arm_even_parity,
            "output": output,
        }
    )
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


def _render_roles(mask, center_color, arm_color):
    mapping = {"0": 0, "8": 8, "c": center_color, "a": arm_color}
    return [[mapping[role] for role in row] for row in mask]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - {"scene_profile"}
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)}")
    requested = overrides.get("scene_profile")
    if requested is not None and requested not in SCENE_PROFILES:
        raise ValueError(f"unknown scene_profile: {requested!r}")
    context = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = context.draw_choice("scene_profile", list(SCENE_PROFILES))
    center_color, arm_color = context.draw_distinct_colors(
        "marker_colors", n=2, exclude={0, 8}
    )
    if profile in PUBLIC_PROFILES:
        mask = _PUBLIC_MASKS[profile]
    elif profile == "procedural_maze":
        mask = _procedural_maze_roles(context, _band(difficulty))
    else:
        mask = _general_roles(profile, _band(difficulty))
    grid = _render_roles(mask, center_color, arm_color)
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
            errors.append(
                f"requested scene_profile {requested}, observed {info['scene_profile']}"
            )
    return errors
