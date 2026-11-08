"""Generator for ``6afe10b621e4`` (largest component of each fixed color).

The canonical rule independently selects the unique largest 4-connected red
(2) component and green (3) component.  It paints the red winner yellow (4),
the green winner blue (1), and clears every other cell.

Normal lessons deliberately defeat the tempting "take the two globally largest
objects" shortcut: one decoy of the color with the larger winner is itself
larger than the other color's winner.  Correct prediction therefore requires
per-color ranking, not global ranking, total color frequency, or position.
"""
from __future__ import annotations

from collections import defaultdict, deque
from typing import Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.shape import normalize

GENERATOR_ID = "6afe10b621e4"
TASK_ID = "6afe10b621e4"
VERSION = "2.0.1"
RULE_HASH = "44f12ccc51c2"

SUMMARY = (
    "Select the unique largest red(2) and green(3) 4-connected components "
    "independently, recolor them to 4 and 1, and erase all decoys."
)

INVARIANTS = [
    "background is 0; red 2 and green 3 are the two required source colors",
    "each required color has 2..4 separated 4-connected components",
    "each required color has one unique largest component and at least one removable decoy",
    "normal lessons make a global two-largest-object shortcut fail",
    "optional distractor color 8 is a single isolated cell and is always erased",
    "all component placements are exact-or-loud; no requested object is silently dropped",
]

LARGER_COLORS = ("red", "green")
AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-aware 7..18",
        "valid": "7..18",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-aware 7..18",
        "valid": "7..18",
    },
    "n_red_objs": {
        "type": "int",
        "default": "difficulty-aware 2..4",
        "valid": "2..4",
    },
    "n_green_objs": {
        "type": "int",
        "default": "difficulty-aware 2..4",
        "valid": "2..4",
    },
    "winner_size_small": {
        "type": "int",
        "default": "difficulty-aware 3..6",
        "valid": "3..6",
    },
    "winner_size_gap": {
        "type": "int",
        "default": "rng 2..3",
        "valid": "2..3",
    },
    "larger_color": {
        "type": "str",
        "default": "rng",
        "valid": "|".join(LARGER_COLORS),
    },
    "include_distractor": {
        "type": "bool",
        "default": "rng",
        "valid": "true|false",
    },
}

_NEIGHBORS = ((-1, 0), (1, 0), (0, -1), (0, 1))
_SOURCE_COLORS = (2, 3)
_DISTRACTOR_COLOR = 8


def _grid_errors(grid) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a nonempty row sequence"]
    if not all(isinstance(row, (list, tuple)) and row for row in grid):
        return ["every row must be a nonempty sequence"]
    widths = {len(row) for row in grid}
    if len(widths) != 1:
        return ["grid must be rectangular"]
    errors = []
    for row in grid:
        for value in row:
            if (
                isinstance(value, bool)
                or not isinstance(value, int)
                or not 0 <= value <= 9
            ):
                errors.append("cells must be literal ARC color integers 0..9")
                return errors
    return errors


def _components_by_color(grid) -> dict[int, list[set[tuple[int, int]]]]:
    """Return 4-connected components grouped by their own nonzero color."""
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


def _cross_color_touches(grid) -> list[tuple[tuple[int, int], tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    touches = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0:
                continue
            for dr, dc in ((1, 0), (0, 1)):
                nr, nc = r + dr, c + dc
                if 0 <= nr < h and 0 <= nc < w:
                    other = grid[nr][nc]
                    if other != 0 and other != color:
                        touches.append(((r, c), (nr, nc)))
    return touches


def rule_mirror(grid):
    """Exact Python mirror for tests only; the Racket program remains authority."""
    if _grid_errors(grid):
        raise ValueError("rule_mirror requires a rectangular ARC grid")
    grouped = _components_by_color(grid)
    if not grouped.get(2) or not grouped.get(3):
        raise ValueError("rule_mirror requires both red and green components")
    out = full_grid(len(grid), len(grid[0]), 0)
    for color, output_color in ((2, 4), (3, 1)):
        winner = max(grouped[color], key=len)
        for r, c in winner:
            out[r][c] = output_color
    return out


def _analysis(grid, *, generated: bool = False) -> dict:
    errors = _grid_errors(grid)
    if errors:
        return {"errors": errors, "facts": None}

    h, w = len(grid), len(grid[0])
    grouped = _components_by_color(grid)
    palette = set(grouped)
    extras = sorted(palette - set(_SOURCE_COLORS))

    for color, name in ((2, "red"), (3, "green")):
        parts = grouped.get(color, [])
        if len(parts) < 2:
            errors.append(f"{name} must have at least two components, got {len(parts)}")
        sizes = sorted((len(part) for part in parts), reverse=True)
        if sizes and sizes.count(sizes[0]) != 1:
            errors.append(f"{name} must have a unique largest component, got sizes {sizes}")
        if sizes and sizes[0] < 3:
            errors.append(f"{name} winner must contain at least three cells")

    if extras:
        if extras != [_DISTRACTOR_COLOR]:
            errors.append(f"only optional distractor color 8 is allowed, got {extras}")
        else:
            distractors = grouped[_DISTRACTOR_COLOR]
            if len(distractors) != 1 or len(distractors[0]) != 1:
                errors.append("optional distractor color 8 must be one isolated cell")

    touches = _cross_color_touches(grid)
    if touches:
        errors.append(f"different-colored components must not touch edge-to-edge ({len(touches)} contacts)")

    sizes_by_color = {
        color: sorted((len(part) for part in grouped.get(color, [])), reverse=True)
        for color in _SOURCE_COLORS
    }
    red_sizes = sizes_by_color[2]
    green_sizes = sizes_by_color[3]
    red_max = red_sizes[0] if red_sizes else 0
    green_max = green_sizes[0] if green_sizes else 0
    larger_color = (
        "red" if red_max > green_max else "green" if green_max > red_max else "tie"
    )
    global_rank_trap = False
    if red_sizes and green_sizes and larger_color != "tie":
        if larger_color == "red":
            global_rank_trap = len(red_sizes) >= 2 and red_sizes[1] > green_max
        else:
            global_rank_trap = len(green_sizes) >= 2 and green_sizes[1] > red_max

    if generated:
        if not (7 <= h <= 18 and 7 <= w <= 18):
            errors.append(f"generated dimensions must be 7..18, got {h}x{w}")
        for color, name in ((2, "red"), (3, "green")):
            count = len(grouped.get(color, []))
            if not 2 <= count <= 4:
                errors.append(f"generated {name} component count must be 2..4, got {count}")
        if not global_rank_trap:
            errors.append("normal lesson must defeat the global two-largest-object shortcut")

    output = None
    if grouped.get(2) and grouped.get(3):
        try:
            output = rule_mirror(grid)
        except ValueError:
            output = None
        if output == [list(row) for row in grid]:
            errors.append("the rule must visibly change the input")

    facts = {
        "height": h,
        "width": w,
        "palette": sorted(palette),
        "components": grouped,
        "sizes_by_color": sizes_by_color,
        "red_winner_size": red_max,
        "green_winner_size": green_max,
        "winner_size_small": min(red_max, green_max) if red_max and green_max else 0,
        "winner_size_gap": abs(red_max - green_max),
        "larger_color": larger_color,
        "include_distractor": bool(extras),
        "global_rank_trap": global_rank_trap,
        "output": output,
    }
    return {"errors": errors, "facts": facts}


def observe_overrides(grid):
    """Expose every exact semantic axis recoverable from a returned scene."""
    analysis = _analysis(grid, generated=False)
    facts = analysis["facts"]
    if facts is None:
        return {}
    return {
        "grid_h": facts["height"],
        "grid_w": facts["width"],
        "n_red_objs": len(facts["components"].get(2, [])),
        "n_green_objs": len(facts["components"].get(3, [])),
        "winner_size_small": facts["winner_size_small"],
        "winner_size_gap": facts["winner_size_gap"],
        "larger_color": facts["larger_color"],
        "include_distractor": facts["include_distractor"],
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate canonical semantics and the stronger generated curriculum."""
    generated = difficulty in ("easy", "medium", "hard")
    analysis = _analysis(grid, generated=generated)
    errors = list(analysis["errors"])
    facts = analysis["facts"]

    requested = {}
    if isinstance(meta, dict):
        nested = meta.get("overrides")
        if isinstance(nested, dict):
            requested.update(nested)
        requested.update({key: value for key, value in meta.items() if key in AXES})
    if facts is not None and requested:
        observed = observe_overrides(grid)
        for axis, expected in requested.items():
            if axis in observed and observed[axis] != expected:
                errors.append(
                    f"override {axis} requested {expected!r}, observed {observed[axis]!r}"
                )
    return errors


def _connected_shape(size: int, rng) -> list[tuple[int, int]]:
    """Grow an exact-size connected polyomino; never silently return fewer cells."""
    cells = {(0, 0)}
    while len(cells) < size:
        frontier = sorted({
            (r + dr, c + dc)
            for r, c in cells
            for dr, dc in _NEIGHBORS
            if (r + dr, c + dc) not in cells
        })
        # Prefer reasonably compact growth while retaining shape diversity.
        scored = []
        for candidate in frontier:
            trial = cells | {candidate}
            rs = [r for r, _ in trial]
            cs = [c for _, c in trial]
            span = (max(rs) - min(rs) + 1) + (max(cs) - min(cs) + 1)
            scored.append((span, candidate))
        best_span = min(score for score, _ in scored)
        choices = [cell for score, cell in scored if score <= best_span + 1]
        cells.add(rng.choice(choices))
    return normalize(sorted(cells))


def _halo(cells: Iterable[tuple[int, int]], h: int, w: int) -> set[tuple[int, int]]:
    out = set(cells)
    for r, c in cells:
        for dr, dc in _NEIGHBORS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < h and 0 <= nc < w:
                out.add((nr, nc))
    return out


def _place_exact(
    grid,
    shape: list[tuple[int, int]],
    color: int,
    reserved: set[tuple[int, int]],
    rng,
) -> set[tuple[int, int]] | None:
    h, w = len(grid), len(grid[0])
    sh = max(r for r, _ in shape) + 1
    sw = max(c for _, c in shape) + 1
    candidates = []
    for rr in range(h - sh + 1):
        for cc in range(w - sw + 1):
            placed = {(rr + r, cc + c) for r, c in shape}
            if placed.isdisjoint(reserved):
                candidates.append(placed)
    if not candidates:
        return None
    chosen = rng.choice(candidates)
    for r, c in chosen:
        grid[r][c] = color
    return chosen


def _size_plan(
    rng,
    *,
    n_red: int,
    n_green: int,
    winner_size_small: int,
    winner_size_gap: int,
    larger_color: str,
) -> dict[int, list[int]]:
    small = winner_size_small
    large = small + winner_size_gap
    larger_value = 2 if larger_color == "red" else 3
    smaller_value = 3 if larger_value == 2 else 2

    plan = {
        larger_value: [large, small + 1],
        smaller_value: [small, rng.randint(1, small - 1)],
    }
    wanted = {2: n_red, 3: n_green}
    for color in _SOURCE_COLORS:
        winner = plan[color][0]
        while len(plan[color]) < wanted[color]:
            # Additional decoys add object-count variety without turning small
            # canonical-scale canvases into accidental packing puzzles.
            plan[color].append(rng.randint(1, min(3, winner - 1)))
        plan[color].sort(reverse=True)
    return plan


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty {difficulty!r}")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {unknown}")
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    h = ctx.draw_int_diff("grid_h", 7, 18)
    w = ctx.draw_int_diff("grid_w", 7, 18)
    n_red = ctx.draw_int_diff("n_red_objs", 2, 4)
    n_green = ctx.draw_int_diff("n_green_objs", 2, 4)
    winner_size_small = ctx.draw_int_diff("winner_size_small", 3, 6)
    winner_size_gap = ctx.draw_int("winner_size_gap", 2, 3)
    larger_color = ctx.draw_choice("larger_color", LARGER_COLORS)
    include_distractor = ctx.draw_choice("include_distractor", (False, True))
    rng = ctx.draw_rng("layout")

    size_plan = _size_plan(
        rng,
        n_red=n_red,
        n_green=n_green,
        winner_size_small=winner_size_small,
        winner_size_gap=winner_size_gap,
        larger_color=larger_color,
    )

    specs = [
        (size, color)
        for color in _SOURCE_COLORS
        for size in size_plan[color]
    ]
    specs.sort(reverse=True)  # largest, hardest-to-place components first
    if include_distractor:
        specs.append((1, _DISTRACTOR_COLOR))

    # A single semantic override must not become invalid merely because the
    # independent default size draw happened to choose a cramped canvas.  Keep
    # explicitly requested dimensions exact, but deterministically widen any
    # unrequested dimension until the exact scene fits.  The effective draw is
    # recorded so provenance and observe_overrides remain truthful.
    h_values = [h] if "grid_h" in overrides else [h] + [x for x in range(h + 1, 19)]
    w_values = [w] if "grid_w" in overrides else [w] + [x for x in range(w + 1, 19)]
    dimensions = sorted(
        {(hh, ww) for hh in h_values for ww in w_values},
        key=lambda pair: (
            pair[0] * pair[1] - h * w,
            abs((pair[0] - pair[1]) - (h - w)),
            pair,
        ),
    )

    for hh, ww in dimensions:
        for _attempt in range(80):
            grid = full_grid(hh, ww, 0)
            reserved: set[tuple[int, int]] = set()
            success = True
            for size, color in specs:
                shape = _connected_shape(size, rng)
                placed = _place_exact(grid, shape, color, reserved, rng)
                if placed is None:
                    success = False
                    break
                reserved.update(_halo(placed, hh, ww))
            if not success:
                continue
            ctx._drawn["grid_h"] = hh
            ctx._drawn["grid_w"] = ww
            errors = self_check(
                grid,
                difficulty=difficulty if difficulty in ("easy", "medium", "hard") else "medium",
                meta={"overrides": ctx._drawn},
            )
            if not errors:
                return grid

    raise ValueError(
        "incompatible exact generator configuration: could not place "
        f"grid={h}x{w}, counts=({n_red},{n_green}), "
        f"winner_size_small={winner_size_small}, winner_size_gap={winner_size_gap}, "
        f"larger_color={larger_color}, distractor={include_distractor}"
    )
