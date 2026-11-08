"""Cross creatures move opposite their tail, swap arms, and carry the tail.

Seven exact controls describe dimensions, count, first-lane direction, first-lane
stem length/branching, and total palette size. Explicit direction/length/branch
pins apply to every creature; otherwise later lanes vary independently. Three
consecutive unpinned draws teach canonical tails and two kinds of counterexample.
"""
from __future__ import annotations

from functools import lru_cache
from itertools import product

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "0d1deab2505c"
RULE_HASH = "a0364ffd781c"
VERSION = "2.0.0"
TASK_ID = GENERATOR_ID
SUMMARY = (
    "One to four cross-bodied creatures independently move opposite their blue "
    "tails to the wall; opposite body colors swap and each observed tail moves intact."
)
INVARIANTS = [
    "background 8; complete color-4 centers with four distinct non-{1,4,8} arms",
    "exactly one cardinal tail root two cells from each center",
    "nonempty 8-connected color-1 tails are distinct and own all blue cells",
    "every non-background input cell belongs to exactly one creature",
    "whole body-plus-tail bounding boxes move opposite the tail to a wall",
    "translated creatures do not overlap; body colors swap opposite arms",
]
DIRECTIONS = ("up", "down", "left", "right")
_DELTA = {"up": (-1, 0), "down": (1, 0), "left": (0, -1), "right": (0, 1)}
_OPPOSITE = {"up": "down", "down": "up", "left": "right", "right": "left"}
_ARM_DELTAS = ((-1, 0), (1, 0), (0, -1), (0, 1))
_BODY_COLORS = (0, 2, 3, 5, 6, 7, 9)
AXES = {
    "grid_h": {"type": "int", "default": "conditional 5..24", "valid": "5..24"},
    "grid_w": {"type": "int", "default": "conditional 5..24", "valid": "5..24"},
    "creature_count": {"type": "int", "default": "scheduled 1..4", "valid": "1..4"},
    "tail_direction": {
        "type": "str", "default": "first lane; later lanes vary",
        "valid": "up|down|left|right",
    },
    "tail_length": {
        "type": "int", "default": "first lane: scheduled 1..5", "valid": "1..5",
    },
    "tail_branch": {
        "type": "bool", "default": "first lane: scheduled fork or straight",
        "valid": "true|false",
    },
    "palette_size": {"type": "int", "default": "conditional 7..10", "valid": "7..10"},
}
# Invalid diagnostic fixtures are deliberately outside the ordinary AXES domain.
DEGENERATE_TEXTURES = ("no_creature", "no_tail", "full_grid")
# Opt into strict rejection classification. Each actual refusal names its pins.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
EXAMPLES_NEEDED = 3
LESSON_SCHEDULE_PERIOD = 3
SCHEDULE_PROFILES = tuple(range(LESSON_SCHEDULE_PERIOD))
MIN_STRICT_FRAC = 1.0


class OverrideConflict(ValueError):
    """A valid individual pin tuple has no collision-free lane construction."""

    def __init__(self, message, axes):
        super().__init__(message)
        self.incompatible_axes = tuple(sorted(axes))


def schedule_profile(seed, sample_index, difficulty=None):
    """0=canonical shapes; 1=short tails; 2=long tails. Seed varies the geometry."""
    return sample_index % LESSON_SCHEDULE_PERIOD


def _validate_overrides(overrides):
    unknown = set(overrides) - set(AXES) - {"texture"}
    if unknown:
        raise ValueError("unknown override keys: " + ", ".join(sorted(unknown)))
    pins = {key: value for key, value in overrides.items() if value is not None}
    for name, bounds in (
        ("grid_h", (5, 24)), ("grid_w", (5, 24)),
        ("creature_count", (1, 4)), ("tail_length", (1, 5)),
        ("palette_size", (7, 10)),
    ):
        if name in pins:
            value = pins[name]
            if type(value) is not int or not bounds[0] <= value <= bounds[1]:
                raise ValueError(f"{name} must be an integer in {bounds[0]}..{bounds[1]}")
    if "tail_branch" in pins and type(pins["tail_branch"]) is not bool:
        raise ValueError("tail_branch must be a bool")
    if "tail_direction" in pins and pins["tail_direction"] not in DIRECTIONS:
        raise ValueError("tail_direction must be up, down, left or right")
    if "texture" in pins and pins["texture"] not in DEGENERATE_TEXTURES:
        raise ValueError("texture is only available for named negative fixtures")
    return pins


def _minimum_dims(direction, count, length, branch):
    # A stem occupies distances 2..length+1. Fork tips extend one step farther.
    # One spare axial cell guarantees positive movement, including small grids.
    axial = length + 4 + int(branch)
    perpendicular = max(5, 4 * count - 1)
    return (axial, perpendicular) if direction in ("up", "down") else (perpendicular, axial)


@lru_cache(maxsize=128)
def _feasible_configs(pin_items):
    pins = dict(pin_items)
    domains = [
        (pins[name],) if name in pins else values
        for name, values in (
            ("tail_direction", DIRECTIONS),
            ("creature_count", range(1, 5)),
            ("tail_length", range(1, 6)),
            ("tail_branch", (False, True)),
            ("palette_size", range(7, 11)),
        )
    ]
    configurations = []
    for direction, count, length, branch, palette in product(*domains):
        if palette - 3 > 4 * count:
            continue
        min_h, min_w = _minimum_dims(direction, count, length, branch)
        if min_h > pins.get("grid_h", 24) or min_w > pins.get("grid_w", 24):
            continue
        configurations.append((direction, count, length, branch, palette))
    return tuple(configurations)


def _parameters(ctx, pins, phase, difficulty):
    if pins:
        # Feasibility is resolved BEFORE recording draws. Nothing requested or
        # already drawn is ever clamped, changed, or silently retried.
        candidates = list(_feasible_configs(tuple(sorted(pins.items()))))
        if not candidates:
            raise OverrideConflict(
                "incompatible overrides: need a free movement cell, isolated "
                "three-cell lanes, and enough distinct arm slots for the palette",
                pins,
            )
        values = {}
        labels = ("tail_direction", "creature_count", "tail_length", "tail_branch", "palette_size")
        for index, label in enumerate(labels):
            options = sorted({candidate[index] for candidate in candidates})
            values[label] = ctx.draw_choice(label, options)
            candidates = [candidate for candidate in candidates if candidate[index] == values[label]]
        direction, count, length, branch, palette = (values[label] for label in labels)
        min_h, min_w = _minimum_dims(direction, count, length, branch)
        h = ctx.draw_int_strict("grid_h", max(5, min_h), 24)
        w = ctx.draw_int_strict("grid_w", max(5, min_w), 24)
        return h, w, count, direction, length, branch, palette

    if phase == 0:
        # These are SIZE/FAMILY supports, never stored grids or stored answers.
        h0, w0, count0, orientation = ctx.draw_choice(
            "canonical_family",
            ((8, 5, 1, "vertical"), (8, 8, 2, "horizontal"),
             (9, 13, 3, "vertical"), (18, 17, 4, "horizontal")),
        )
        count = ctx.draw_choice("creature_count", (count0,))
        direction = ctx.draw_choice(
            "tail_direction", ("up", "down") if orientation == "vertical" else ("left", "right")
        )
        length = ctx.draw_choice("tail_length", (2,))
        branch = ctx.draw_choice("tail_branch", (True,))
        h = ctx.draw_int_strict("grid_h", h0, h0)
        w = ctx.draw_int_strict("grid_w", w0, w0)
    else:
        counts = (2, 2, 3, 4) if difficulty == "easy" else (
            (2, 3, 4, 4) if difficulty == "hard" else (2, 3, 4)
        )
        count = ctx.draw_choice("creature_count", counts)
        direction = ctx.draw_choice("tail_direction", DIRECTIONS)
        length = ctx.draw_choice("tail_length", (1,) if phase == 1 else (3, 4, 5))
        branch = ctx.draw_choice("tail_branch", (True,) if phase == 1 else (False, True))
        min_h, min_w = _minimum_dims(direction, count, length, branch)
        upper = {"easy": 18, "medium": 22, "hard": 24, None: 22}[difficulty]
        h = ctx.draw_int_strict("grid_h", max(5, min_h), upper)
        w = ctx.draw_int_strict("grid_w", max(5, min_w), upper)
    palette = ctx.draw_choice("palette_size", (7,) if count == 1 else (7, 8, 9, 10, 10))
    return h, w, count, direction, length, branch, palette


def _tail_cells(center, direction, length, branch):
    cr, cc = center
    dr, dc = _DELTA[direction]
    cells = {(cr + dr * k, cc + dc * k) for k in range(2, length + 2)}
    if branch:
        k = length + 2
        for side in (-1, 1):
            cells.add((cr + dr * k - dc * side, cc + dc * k + dr * side))
    return cells


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    if type(sample_index) is not int:
        raise TypeError("sample_index must be an integer (not bool)")
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be easy, medium, hard, or None")
    pins = _validate_overrides(overrides)
    if "texture" in pins:
        if len(pins) > 1:
            raise OverrideConflict("negative texture fixtures cannot combine with ordinary axes", pins)
        return _draw_from_degenerate(pins["texture"])
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=pins)
    phase = schedule_profile(seed, sample_index, difficulty)
    h, w, count, direction, length, branch, palette_size = _parameters(ctx, pins, phase, difficulty)
    grid = full_grid(h, w, 8)
    vertical = direction in ("up", "down")
    axial_size, perpendicular_size = (h, w) if vertical else (w, h)
    layout_rng = ctx.draw_rng("layout")
    extra = perpendicular_size - (4 * count - 1)
    gaps = [0] * (count + 1)
    for _ in range(extra):
        gaps[layout_rng.randrange(count + 1)] += 1
    lane_centers = []
    lane_start = gaps[0]
    for index in range(count):
        lane_centers.append(lane_start + 1)
        lane_start += 4 + gaps[index + 1]

    palette = ctx.draw_distinct_colors("body_palette", n=palette_size - 3, exclude={1, 4, 8})
    for index, lane_center in enumerate(lane_centers):
        current_direction = direction
        if index and "tail_direction" not in pins:
            current_direction = ctx.draw_choice(
                f"creature_{index}.direction", (direction, _OPPOSITE[direction])
            )
        current_length, current_branch = length, branch
        if index and (pins or phase != 0):
            shapes = [
                (stem, fork) for stem in range(1, 6) for fork in (False, True)
                if stem + 4 + int(fork) <= axial_size
                and ("tail_length" not in pins or stem == pins["tail_length"])
                and ("tail_branch" not in pins or fork == pins["tail_branch"])
            ]
            # Both noncanonical phases contain an observed second tail that
            # differs from the first. This refutes a copy-first-tail shortcut.
            if index == 1 and not pins:
                shapes = [shape for shape in shapes if shape != (length, branch)]
            current_length, current_branch = ctx.draw_choice(f"creature_{index}.tail_shape", shapes)
        reach = current_length + 1 + int(current_branch)
        if current_direction in ("down", "right"):
            axial_center = layout_rng.randint(2, axial_size - 1 - reach)
        else:
            axial_center = layout_rng.randint(reach, axial_size - 3)
        center = (axial_center, lane_center) if vertical else (lane_center, axial_center)
        cr, cc = center
        grid[cr][cc] = 4
        arm_colors = [palette[(4 * index + arm) % len(palette)] for arm in range(4)]
        ctx.draw_rng(f"creature_{index}.arm_permutation").shuffle(arm_colors)
        for (dr, dc), color in zip(_ARM_DELTAS, arm_colors):
            grid[cr + dr][cc + dc] = color
        for tr, tc in _tail_cells(center, current_direction, current_length, current_branch):
            grid[tr][tc] = 1
    return grid


def _grid_shape(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("grid must be a nonempty rectangular sequence")
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        raise ValueError("grid rows must be nonempty sequences")
    h, w = len(grid), len(grid[0])
    if h > 30 or w > 30:
        raise ValueError("grid dimensions exceed ARC bounds")
    if any(not isinstance(row, (list, tuple)) or len(row) != w for row in grid):
        raise ValueError("grid is ragged")
    if any(type(cell) is not int or not 0 <= cell <= 9 for row in grid for cell in row):
        raise ValueError("grid cells must be integer colors 0..9, excluding bool")
    return h, w


def parse_creatures(grid):
    """Parse the rule's broad structural domain; independent of lane generation.

    Returns dictionaries with center, direction, body (position->color), tail
    (sorted positions), and shift. Arbitrarily winding 8-connected tails are
    permitted. Parallel scenes use lane order; mixed-axis scenes use row order.
    """
    h, w = _grid_shape(grid)
    foreground = {(r, c) for r in range(h) for c in range(w) if grid[r][c] != 8}
    if len(foreground) == h * w:
        raise ValueError("background 8 is absent")
    centers = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 4]
    if not centers:
        raise ValueError("no color-4 creature center")
    creatures, owned = [], set()
    for cr, cc in centers:
        if not (1 <= cr < h - 1 and 1 <= cc < w - 1):
            raise ValueError("a center lacks an in-bounds complete body")
        arms = [(cr + dr, cc + dc) for dr, dc in _ARM_DELTAS]
        colors = [grid[r][c] for r, c in arms]
        if len(set(colors)) != 4 or any(color not in _BODY_COLORS for color in colors):
            raise ValueError("body arms must be four distinct non-{1,4,8} colors")
        roots = [
            (name, (cr + 2 * dr, cc + 2 * dc))
            for name, (dr, dc) in _DELTA.items()
            if 0 <= cr + 2 * dr < h and 0 <= cc + 2 * dc < w
            and grid[cr + 2 * dr][cc + 2 * dc] == 1
        ]
        if len(roots) != 1:
            raise ValueError("a creature must have exactly one cardinal tail root")
        direction, root = roots[0]
        tail, pending = {root}, [root]
        while pending:
            r, c = pending.pop()
            for dr, dc in product((-1, 0, 1), repeat=2):
                point = (r + dr, c + dc)
                if (dr or dc) and 0 <= point[0] < h and 0 <= point[1] < w:
                    if point not in tail and grid[point[0]][point[1]] == 1:
                        tail.add(point)
                        pending.append(point)
        body = {(cr, cc): 4, **{point: grid[point[0]][point[1]] for point in arms}}
        cells = set(body) | tail
        if owned & cells:
            raise ValueError("creatures overlap or share an 8-connected tail")
        owned.update(cells)
        min_r = min(r for r, _ in cells)
        max_r = max(r for r, _ in cells)
        min_c = min(c for _, c in cells)
        max_c = max(c for _, c in cells)
        shift = {
            "down": (-min_r, 0), "up": (h - 1 - max_r, 0),
            "right": (0, -min_c), "left": (0, w - 1 - max_c),
        }[direction]
        creatures.append({
            "center": (cr, cc), "direction": direction, "body": body,
            "tail": tuple(sorted(tail)), "shift": shift,
        })
    if owned != foreground:
        raise ValueError("stray foreground cells do not belong to a creature")
    destination = set()
    for creature in creatures:
        dr, dc = creature["shift"]
        moved = {(r + dr, c + dc) for r, c in set(creature["body"]) | set(creature["tail"])}
        if moved & destination:
            raise ValueError("translated creatures collide")
        if any(not (0 <= r < h and 0 <= c < w) for r, c in moved):
            raise ValueError("translated creature leaves the grid")
        destination.update(moved)
    directions = {creature["direction"] for creature in creatures}
    if directions <= {"up", "down"}:
        creatures.sort(key=lambda creature: (creature["center"][1], creature["center"][0]))
    else:
        creatures.sort(key=lambda creature: creature["center"])
    return creatures


def _tail_coordinates(creature):
    cr, cc = creature["center"]
    dr, dc = _DELTA[creature["direction"]]
    return {(dr * (r - cr) + dc * (c - cc), -dc * (r - cr) + dr * (c - cc))
            for r, c in creature["tail"]}


def observe_overrides(grid):
    """Read exact first-lane values from pixels; no seed/provenance lookup."""
    creatures = parse_creatures(grid)
    primary = creatures[0]
    coordinates = _tail_coordinates(primary)
    stem = 0
    while (stem + 2, 0) in coordinates:
        stem += 1
    return {
        "grid_h": len(grid), "grid_w": len(grid[0]),
        "creature_count": len(creatures), "tail_direction": primary["direction"],
        "tail_length": stem, "tail_branch": any(side != 0 for _, side in coordinates),
        "palette_size": len({cell for row in grid for cell in row}),
    }


def self_check(grid, *, difficulty=None, meta=None):
    try:
        parse_creatures(grid)
    except (ValueError, TypeError) as exc:
        return [str(exc)]
    return []


def strict_canonical_like(grid):
    """The task's complete, noncolliding structural domain (not fixed tail art)."""
    return self_check(grid)


def diagnostic_transform(grid, *, turn_body=True, tail_mode="translate", first_only=False):
    """Independent Python diagnostic, never the generation label authority."""
    creatures = parse_creatures(grid)
    out = [list(row) for row in grid]
    selected = creatures[:1] if first_only else creatures
    for creature in selected:
        for r, c in set(creature["body"]) | set(creature["tail"]):
            out[r][c] = 8
    first_shape = _tail_coordinates(creatures[0])
    for creature in selected:
        cr, cc = creature["center"]
        dr, dc = creature["shift"]
        nr, nc = cr + dr, cc + dc
        if tail_mode == "canonical_template":
            tail = _tail_cells((nr, nc), creature["direction"], 2, True)
        elif tail_mode == "copy_first":
            tr, tc = _DELTA[creature["direction"]]
            tail = {(nr + tr * along - tc * side, nc + tc * along + tr * side)
                    for along, side in first_shape}
        elif tail_mode == "stationary":
            tail = set(creature["tail"])
        elif tail_mode == "translate":
            tail = {(r + dr, c + dc) for r, c in creature["tail"]}
        else:
            raise ValueError("unknown diagnostic tail_mode")
        for r, c in tail:
            # Wrong templates can exceed small grids. Clipping is an explicit
            # rival behavior, so its prediction remains a valid ARC grid.
            if 0 <= r < len(out) and 0 <= c < len(out[0]):
                out[r][c] = 1
        out[nr][nc] = 4
        for ar, ac in _ARM_DELTAS:
            sr, sc = (cr - ar, cc - ac) if turn_body else (cr + ar, cc + ac)
            out[nr + ar][nc + ac] = grid[sr][sc]
    return out


def canonical_tail_template(grid):
    return diagnostic_transform(grid, tail_mode="canonical_template")


def copy_first_tail(grid):
    return diagnostic_transform(grid, tail_mode="copy_first")


def move_without_turn(grid):
    return diagnostic_transform(grid, turn_body=False)


def leave_tail_behind(grid):
    return diagnostic_transform(grid, tail_mode="stationary")


def first_creature_only(grid):
    return diagnostic_transform(grid, first_only=True)


SEMANTIC_RIVALS = {
    "canonical_tail_template": canonical_tail_template,
    "copy_first_tail": copy_first_tail,
    "move_without_turn": move_without_turn,
    "leave_tail_behind": leave_tail_behind,
    "first_creature_only": first_creature_only,
}
CANONICAL_SHORTCUTS = {
    "canonical_tail_template": canonical_tail_template,
    "copy_first_tail": copy_first_tail,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def _refutes(grid, name):
    return SEMANTIC_RIVALS[name](grid) != diagnostic_transform(grid)


SEMANTIC_WITNESSES = {
    "observed_tail_shape": lambda grid: _refutes(grid, "canonical_tail_template"),
    "different_creature_tails": lambda grid: _refutes(grid, "copy_first_tail"),
    "opposite_arm_swap": lambda grid: _refutes(grid, "move_without_turn"),
    "tail_moves_with_body": lambda grid: _refutes(grid, "leave_tail_behind"),
    "every_creature_moves": lambda grid: _refutes(grid, "first_creature_only"),
}
WITNESS_RIVALS = {
    "observed_tail_shape": ["canonical_tail_template"],
    "different_creature_tails": ["copy_first_tail"],
    "opposite_arm_swap": ["move_without_turn"],
    "tail_moves_with_body": ["leave_tail_behind"],
    "every_creature_moves": ["first_creature_only"],
}


def lesson_identifiable(demos, query):
    """Flag a demo-surviving declared rival only when it changes the query.

    This is identifiability relative to the explicit five-rival family, not a
    claim of uniqueness among all programs. Query output is never consulted.
    A surviving rival that predicts the same query answer is redundant here.
    """
    reasons = []
    for index, pair in enumerate(demos):
        reasons.extend(f"demo {index}: {reason}" for reason in self_check(pair["input"]))
    query_grid = query["input"] if isinstance(query, dict) else query
    reasons.extend("query: " + reason for reason in self_check(query_grid))
    if reasons:
        return reasons
    expected_query = diagnostic_transform(query_grid)
    for name, rival in LESSON_COMPETITORS.items():
        if (all(rival(pair["input"]) == pair["output"] for pair in demos)
                and rival(query_grid) != expected_query):
            reasons.append("demo-surviving rival changes query: " + name)
    return reasons


def _draw_from_degenerate(name):
    grid = full_grid(13, 13, 8)
    if name == "no_creature":
        grid[6][9] = 1
    elif name == "no_tail":
        grid[6][6] = 4
        for (dr, dc), color in zip(_ARM_DELTAS, (3, 5, 6, 7)):
            grid[6 + dr][6 + dc] = color
    elif name == "full_grid":
        grid = full_grid(13, 13, 4)
    else:
        raise ValueError("unknown negative fixture")
    return grid

