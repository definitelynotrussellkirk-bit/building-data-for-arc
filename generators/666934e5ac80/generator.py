"""Generator for M50 — keep the largest 4-connected component per color.

The normal curriculum always contains both semantic branches witnessed by the
canonical task: at least one color has smaller components that must be removed,
and at least one other color already has a single component that must survive.
Tied maxima are deliberately excluded from normal draws because the natural-
language task is singular even though the executable rule keeps every tied max.
"""
from __future__ import annotations

from collections import defaultdict, deque
from typing import Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "666934e5ac80"
TASK_ID = "666934e5ac80"
VERSION = "2.0.0"
RULE_HASH = "821bfb26a1d2"

SUMMARY = (
    "For each of 2-3 colors, keep its unique largest 4-connected component; "
    "normal scenes include removable decoys and an already-single-component color."
)

INVARIANTS = [
    "background is 0 and every nonzero cell is an ARC color 1..9",
    "2 or 3 colors are drawn from one declared disjoint palette family",
    "same- and different-color components are separated by background in 4-neighborhoods",
    "every color has one unique largest component",
    "at least one color has smaller removable components and at least one color has only one component",
    "the scene has exactly 1..3 removable components and the oracle changes the input",
    "a surviving singleton-color component overlaps decoy sizes, blocking a global size-threshold shortcut",
]

PALETTE_FAMILIES = ("low", "middle", "high")
PALETTE_POOLS = {
    "low": (1, 2, 3),
    "middle": (4, 5, 6),
    "high": (7, 8, 9),
}

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-aware 8..14",
        "valid": "8..14",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-aware 9..16",
        "valid": "9..16",
    },
    "palette_family": {
        "type": "str",
        "default": "rng",
        "valid": "|".join(PALETTE_FAMILIES),
    },
    "n_colors": {
        "type": "int",
        "default": "difficulty-aware 2..3",
        "valid": "2..3",
    },
    "n_decoy_components": {
        "type": "int",
        "default": "difficulty-aware 1..3",
        "valid": "1..3",
    },
}

_NEIGHBORS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _valid_cells(grid) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a nonempty row sequence"]
    if not all(isinstance(row, (list, tuple)) and row for row in grid):
        return ["every row must be a nonempty sequence"]
    widths = {len(row) for row in grid}
    if len(widths) != 1:
        return ["grid must be rectangular"]
    h, w = len(grid), next(iter(widths))
    errors = []
    if not 8 <= h <= 14:
        errors.append(f"grid height must be 8..14, got {h}")
    if not 9 <= w <= 16:
        errors.append(f"grid width must be 9..16, got {w}")
    if any(
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("cells must be literal ARC color integers 0..9")
    return errors


def _components_by_color(grid) -> dict[int, list[set[tuple[int, int]]]]:
    """Return 4-connected nonzero components grouped by their own color."""
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    grouped: dict[int, list[set[tuple[int, int]]]] = defaultdict(list)
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            component = {(r, c)}
            seen.add((r, c))
            queue = deque([(r, c)])
            while queue:
                rr, cc = queue.popleft()
                for dr, dc in _NEIGHBORS:
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        component.add((nr, nc))
                        queue.append((nr, nc))
            grouped[color].append(component)
    return dict(grouped)


def _palette_family(colors: Iterable[int]) -> str | None:
    color_set = set(colors)
    matches = [
        name for name, pool in PALETTE_POOLS.items()
        if color_set and color_set <= set(pool)
    ]
    return matches[0] if len(matches) == 1 else None


def _analysis(grid) -> dict:
    errors = _valid_cells(grid)
    if errors:
        return {"errors": errors, "facts": None}

    h, w = len(grid), len(grid[0])
    grouped = _components_by_color(grid)
    colors = sorted(grouped)
    family = _palette_family(colors)
    if not 2 <= len(colors) <= 3:
        errors.append(f"scene must use 2 or 3 nonzero colors, got {len(colors)}")
    if family is None:
        errors.append("all nonzero colors must belong to one declared palette family")

    # The generator separates every object, even across colors. This keeps the
    # grouping cue visual rather than allowing touching colors to look like one object.
    touching_pairs = set()
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if not color:
                continue
            for dr, dc in ((1, 0), (0, 1)):
                nr, nc = r + dr, c + dc
                if 0 <= nr < h and 0 <= nc < w:
                    other = grid[nr][nc]
                    if other and other != color:
                        touching_pairs.add(tuple(sorted((color, other))))
    if touching_pairs:
        errors.append(f"different-color components 4-touch: {sorted(touching_pairs)}")

    sizes_by_color = {
        color: sorted((len(component) for component in components), reverse=True)
        for color, components in grouped.items()
    }
    multi_colors = []
    singleton_colors = []
    decoy_sizes = []
    survivor_sizes = {}
    for color, sizes in sizes_by_color.items():
        if not sizes:
            continue
        survivor_sizes[color] = sizes[0]
        if sizes.count(sizes[0]) != 1:
            errors.append(f"color {color} must have a unique largest component, got sizes {sizes}")
        if len(sizes) == 1:
            singleton_colors.append(color)
        else:
            multi_colors.append(color)
            if sizes[0] < 3:
                errors.append(f"filtered color {color} needs a largest component of size at least 3")
            decoy_sizes.extend(sizes[1:])

    n_decoys = sum(max(0, len(sizes) - 1) for sizes in sizes_by_color.values())
    if not multi_colors:
        errors.append("at least one color must contain a removable smaller component")
    if not singleton_colors:
        errors.append("at least one color must exercise the already-single-component branch")
    if not 1 <= n_decoys <= 3:
        errors.append(f"scene must contain 1..3 removable components, got {n_decoys}")
    if decoy_sizes and singleton_colors:
        smallest_singleton_survivor = min(survivor_sizes[color] for color in singleton_colors)
        largest_decoy = max(decoy_sizes)
        if smallest_singleton_survivor > largest_decoy:
            errors.append(
                "a singleton-color survivor must be no larger than a decoy so a global size threshold cannot solve the scene"
            )

    output = None
    if grouped:
        output = rule_mirror(grid)
        if output == [list(row) for row in grid]:
            errors.append("largest-component rule must visibly remove at least one component")

    facts = {
        "height": h,
        "width": w,
        "colors": colors,
        "palette_family": family,
        "components_by_color": grouped,
        "sizes_by_color": sizes_by_color,
        "multi_colors": sorted(multi_colors),
        "singleton_colors": sorted(singleton_colors),
        "n_decoy_components": n_decoys,
        "decoy_sizes": sorted(decoy_sizes),
        "survivor_sizes": survivor_sizes,
        "output": output,
    }
    return {"errors": errors, "facts": facts}


def rule_mirror(grid):
    """Exact Python mirror used only for structural tests; Racket remains oracle."""
    if _valid_cells(grid):
        raise ValueError("rule_mirror requires a valid calibrated grid")
    grouped = _components_by_color(grid)
    out = full_grid(len(grid), len(grid[0]), 0)
    for color, components in grouped.items():
        best = max(len(component) for component in components)
        for component in components:
            if len(component) == best:
                for r, c in component:
                    out[r][c] = color
    return out


def observe_overrides(grid):
    """Expose exact semantic controls recoverable from a returned grid."""
    if _valid_cells(grid):
        return {}
    grouped = _components_by_color(grid)
    colors = sorted(grouped)
    return {
        "palette_family": _palette_family(colors),
        "n_colors": len(colors),
        "n_decoy_components": sum(max(0, len(parts) - 1) for parts in grouped.values()),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    analysis = _analysis(grid)
    errors = list(analysis["errors"])
    facts = analysis["facts"]
    if facts is not None and difficulty in ("medium", "hard"):
        if facts["decoy_sizes"] and max(facts["decoy_sizes"]) < 2:
            errors.append(f"{difficulty} scenes must include a non-singleton decoy component")

    # The override-contract gate passes requested values in meta. Comparing them
    # here makes exact-or-loud behavior independently visible to focused tests.
    requested = {}
    if isinstance(meta, dict):
        if isinstance(meta.get("overrides"), dict):
            requested.update(meta["overrides"])
        requested.update({key: value for key, value in meta.items() if key in AXES})
    if facts is not None and requested:
        observed = {
            "grid_h": facts["height"],
            "grid_w": facts["width"],
            "palette_family": facts["palette_family"],
            "n_colors": len(facts["colors"]),
            "n_decoy_components": facts["n_decoy_components"],
        }
        for axis, expected in requested.items():
            if axis in observed and observed[axis] != expected:
                errors.append(
                    f"override {axis} requested {expected!r}, observed {observed[axis]!r}"
                )
    return errors


def _neighbors(cell: tuple[int, int], h: int, w: int):
    r, c = cell
    for dr, dc in _NEIGHBORS:
        nr, nc = r + dr, c + dc
        if 0 <= nr < h and 0 <= nc < w:
            yield nr, nc


def _place_component(rng, h, w, reserved: set[tuple[int, int]], size: int):
    """Grow one connected polyomino without touching any previous component."""
    starts = [(r, c) for r in range(h) for c in range(w) if (r, c) not in reserved]
    rng.shuffle(starts)
    for start in starts[: min(len(starts), 96)]:
        cells = {start}
        while len(cells) < size:
            frontier = sorted({
                neighbor
                for cell in cells
                for neighbor in _neighbors(cell, h, w)
                if neighbor not in cells and neighbor not in reserved
            })
            if not frontier:
                break
            cells.add(rng.choice(frontier))
        if len(cells) == size:
            return cells
    return None


def _reserve(cells: set[tuple[int, int]], h: int, w: int):
    halo = set(cells)
    for cell in cells:
        halo.update(_neighbors(cell, h, w))
    return halo


def _size_plan(rng, colors, n_decoys, difficulty):
    """Build one survivor/decoy plan with cross-role size overlap."""
    shuffled = list(colors)
    rng.shuffle(shuffled)
    filtered_colors = shuffled[:-1]

    allocation = {color: 0 for color in colors}
    required_filtered = min(len(filtered_colors), n_decoys)
    active = filtered_colors[:required_filtered]
    for color in active:
        allocation[color] += 1
    for _ in range(n_decoys - required_filtered):
        allocation[rng.choice(active)] += 1

    if difficulty == "easy":
        large_lo, large_hi = 3, 5
    elif difficulty == "hard":
        large_lo, large_hi = 5, 7
    else:
        large_lo, large_hi = 4, 6

    decoys = {}
    survivors = {}
    for color in colors:
        if allocation[color]:
            survivors[color] = rng.randint(large_lo, large_hi)
            decoys[color] = [
                rng.randint(1, min(3, survivors[color] - 1))
                for _ in range(allocation[color])
            ]
        else:
            decoys[color] = []

    all_decoys = [size for sizes in decoys.values() for size in sizes]
    if difficulty in ("medium", "hard") and max(all_decoys) < 2:
        chosen = rng.choice(active)
        decoys[chosen][0] = min(2, survivors[chosen] - 1)
        all_decoys = [size for sizes in decoys.values() for size in sizes]

    # Deliberately overlap every already-single-component survivor with the
    # decoy-size range. A solver cannot delete every component below one global
    # threshold and remain correct.
    for color in colors:
        if allocation[color] == 0:
            survivors[color] = rng.randint(1, max(all_decoys))
    return survivors, decoys


def _draw_scene(rng, h, w, colors, n_decoys, difficulty):
    for _ in range(320):
        survivors, decoys = _size_plan(rng, colors, n_decoys, difficulty)
        plans = []
        for color in colors:
            plans.append((survivors[color], color, "survivor"))
            plans.extend((size, color, "decoy") for size in decoys[color])
        # Large components go first; ties are randomized so no color/position role
        # is stable across seeds.
        rng.shuffle(plans)
        plans.sort(key=lambda item: item[0], reverse=True)

        reserved: set[tuple[int, int]] = set()
        placed = []
        failed = False
        for size, color, role in plans:
            cells = _place_component(rng, h, w, reserved, size)
            if cells is None:
                failed = True
                break
            placed.append((color, role, cells))
            reserved.update(_reserve(cells, h, w))
        if failed:
            continue

        grid = full_grid(h, w, 0)
        for color, _role, cells in placed:
            for r, c in cells:
                grid[r][c] = color
        if not self_check(grid, difficulty=difficulty):
            return grid
    raise AssertionError(
        f"could not place a lawful largest-component scene in {h}x{w} "
        f"for {len(colors)} colors and {n_decoys} decoys"
    )


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {unknown!r}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    h = ctx.draw_int_diff("grid_h", 8, 14)
    w = ctx.draw_int_diff("grid_w", 9, 16)
    family = ctx.draw_choice("palette_family", PALETTE_FAMILIES)
    n_colors = ctx.draw_int_diff("n_colors", 2, 3)
    n_decoys = ctx.draw_int_diff("n_decoy_components", 1, 3)

    palette_rng = ctx.draw_rng("palette")
    colors = palette_rng.sample(list(PALETTE_POOLS[family]), n_colors)
    return _draw_scene(ctx.draw_rng("layout"), h, w, colors, n_decoys, difficulty)
