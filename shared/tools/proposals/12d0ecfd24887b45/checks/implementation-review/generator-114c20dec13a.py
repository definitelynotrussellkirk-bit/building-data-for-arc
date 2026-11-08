"""Exact green X selector: small canonical scenes and contrastive lessons.

The unchanged Racket authority selects maximal monochromatic 8-components
whose color is 3 and whose normalized cells are exactly the five-cell 3x3 X.
This module generates inputs only. Rival predictors describe wrong hypotheses;
they never supply training labels.
"""
from __future__ import annotations

from functools import partial

from puzzle_generators.base import gen_ctx

GENERATOR_ID = TASK_ID = "70f97d6b605b"
VERSION = "2.0.0"
RULE_HASH = "76b666ea1233"
SUMMARY = "Recolor every exact five-cell green X component; preserve distractors."
EXAMPLES_NEEDED = 4
LESSON_SCHEDULE_PERIOD = 35
SCHEDULE_PROFILES = ("core", "mixed")

X3 = frozenset(((0, 0), (0, 2), (1, 1), (2, 0), (2, 2)))
PLUS3 = frozenset(((0, 1), (1, 0), (1, 1), (1, 2), (2, 1)))
X5 = frozenset({(i, i) for i in range(5)} | {(i, 4 - i) for i in range(5)})
HOLES = ((0, 1), (1, 0), (1, 2), (2, 1))
AUXILIARY_COLORS = (1, 4, 5, 6, 7, 8, 9)
INVARIANTS = [
    "0 background; maximal same-color 8-connected components define components",
    "only color-3 components with exactly the five offsets of a 3x3 X qualify",
    "core scenes retain small canonical profiles; mixed scenes expose named rivals",
]
AXES = {
    "n": {"type": "int", "default": "core 1..2; mixed 2..3", "valid": "1..3"},
    "padding": {"type": "int", "default": "core 0; mixed 0..2", "valid": "0..2"},
    "distractor_color": {"type": "int", "default": "core 4; mixed seven-color cycle",
                         "valid": "1|4|5|6|7|8|9"},
    "scene": {"type": "str", "default": "core,mixed,core,mixed,core cycle", "valid": "core|mixed"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []


def schedule_profile(seed, sample_index, difficulty=None):
    """Five draws contain two contrasts; scene/color schedule period is 35."""
    return "mixed" if sample_index % 5 in (1, 3) else "core"


def _validate_overrides(overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override keys: {sorted(unknown)}")
    for key, value in overrides.items():
        if value is None:
            continue
        if key == "scene":
            if type(value) is not str or value not in SCHEDULE_PROFILES:
                raise ValueError("scene must be core or mixed")
        elif type(value) is not int:
            raise TypeError(f"{key} must be an integer, not bool or a coerced value")
        elif key == "n" and not 1 <= value <= 3:
            raise ValueError("n must be in 1..3")
        elif key == "padding" and not 0 <= value <= 2:
            raise ValueError("padding must be in 0..2")
        elif key == "distractor_color" and value not in AUXILIARY_COLORS:
            raise ValueError("distractor_color must be one of 1,4,5,6,7,8,9")


def _stamp(grid, origin, shape, color):
    top, left = origin
    for r, c in shape:
        grid[top + r][left + c] = color


def _core_scene(rng, n, auxiliary):
    h, w = rng.choice(((7, 7), (7, 8), (8, 8)))
    grid = [[0] * w for _ in range(h)]
    slots = [(0, 0), (0, w - 3), (h - 3, 0), (h - 3, w - 3)]
    rng.shuffle(slots)
    for origin in slots[:n]:
        _stamp(grid, origin, X3, 3)
    _stamp(grid, slots[n], PLUS3, auxiliary)
    return grid


def _mixed_scene(rng, n, auxiliary, difficulty):
    gap = 2 if difficulty == "hard" else 1
    lower = 3 + (1 if difficulty == "easy" else rng.randint(1, 3))
    width = (n + 2) * 3 + (n + 1) * gap
    grid = [[0] * width for _ in range(lower + 5)]
    slots = [(0, j * (3 + gap)) for j in range(n + 2)]
    slots.append((lower + 1, width - 3))
    rng.shuffle(slots)
    # Two wrong-color Xs bracket green numerically in every mixed scene.
    modules = [(X3, 3)] * n + [(PLUS3, 3), (X3, 1),
                              (X3, auxiliary if auxiliary > 3 else 4)]
    for origin, (shape, color) in zip(slots, modules):
        _stamp(grid, origin, shape, color)
    top, left = slots[rng.randrange(n)]
    dr, dc = rng.choice(HOLES)
    grid[top + dr][left + dc] = auxiliary
    # Its central stencil is an X, but the whole nine-cell component is not X3.
    _stamp(grid, (lower, 0), X5, 3)
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_overrides(overrides)
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be easy, medium, hard, or None")
    active = {key for key, value in overrides.items() if value is not None}
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    scheduled = schedule_profile(seed, sample_index, difficulty)
    scene = ctx.draw_choice("scene", SCHEDULE_PROFILES if "scene" in active else (scheduled,))
    if "n" in active:
        n = ctx.draw_int_strict("n", 1, 3)
    elif scene == "core":
        n = ctx.draw_int_strict("n", 1, 2)
    else:
        n = ctx.draw_int_strict("n", 2, 3)
    if "padding" in active or scene == "mixed":
        padding = ctx.draw_int_strict("padding", 0, 2)
    else:
        padding = ctx.draw_int_strict("padding", 0, 0)
    contrast_index = 2 * (sample_index // 5) + int(sample_index % 5 >= 3)
    auxiliary_default = (4 if scene == "core" else
                         AUXILIARY_COLORS[(contrast_index + seed % 7) % 7])
    auxiliary = ctx.draw_choice("distractor_color", AUXILIARY_COLORS
                                if "distractor_color" in active else (auxiliary_default,))
    rng = ctx.draw_rng("layout")
    grid = (_core_scene(rng, n, auxiliary) if scene == "core" else
            _mixed_scene(rng, n, auxiliary, difficulty))
    for _ in range(rng.randrange(4)):
        grid = [list(row) for row in zip(*grid[::-1])]
    if rng.randrange(2):
        grid = [row[::-1] for row in grid]
    if padding:
        width = len(grid[0]) + 2 * padding
        grid = ([[0] * width for _ in range(padding)] +
                [[0] * padding + row + [0] * padding for row in grid] +
                [[0] * width for _ in range(padding)])
    return grid


def _grid_errors(grid):
    if type(grid) is not list or not grid:
        return ["expected a nonempty list of row lists"]
    if any(type(row) is not list or not row for row in grid):
        return ["expected nonempty row lists"]
    if any(len(row) != len(grid[0]) for row in grid):
        return ["rows must have equal length"]
    if any(type(color) is not int or not 0 <= color <= 9 for row in grid for color in row):
        return ["cells must be integers in 0..9; bool is not a color"]
    if len(grid) > 30 or len(grid[0]) > 30:
        return ["grid exceeds the supported 30 by 30 domain"]
    return []


def _components(grid):
    """Maximal same-color 8-components, in row-major first-cell order."""
    h, w = len(grid), len(grid[0])
    seen = set()
    result = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            cells, pending = {(r, c)}, [(r, c)]
            seen.add((r, c))
            while pending:
                rr, cc = pending.pop()
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        point = (rr + dr, cc + dc)
                        if (0 <= point[0] < h and 0 <= point[1] < w
                                and point not in seen and grid[point[0]][point[1]] == color):
                            cells.add(point)
                            seen.add(point)
                            pending.append(point)
            top = min(rr for rr, cc in cells)
            left = min(cc for rr, cc in cells)
            shape = frozenset((rr - top, cc - left) for rr, cc in cells)
            result.append((color, cells, shape, top, left))
    return result


def _is_attached_x(shape):
    if len(shape) != 6:
        return False
    return any({(r + dr, c + dc) for dr, dc in X3} <= shape
               for r in range(max(rr for rr, cc in shape) - 1)
               for c in range(max(cc for rr, cc in shape) - 1))


def self_check(grid, *, difficulty=None, meta=None):
    """Validate the declared motif domain, including lawful identity witnesses.

    This is narrower than all inputs on which the reference can run. It accepts
    X3, plus3, X5, a green X with one attached green cell, and foreign singletons.
    Foreign singletons must accompany a motif. A positive target count and
    zero-valued X holes are not required.
    """
    errors = _grid_errors(grid)
    if errors:
        return errors
    components = _components(grid)
    if not components or not any(len(cells) > 1 for _, cells, _, _, _ in components):
        return ["expected at least one foreground motif"]
    for color, cells, shape, top, left in components:
        accepted = shape in (X3, PLUS3, X5)
        accepted |= color == 3 and _is_attached_x(shape)
        accepted |= color != 3 and len(cells) == 1
        if not accepted:
            errors.append(f"unsupported color-{color} component at ({top},{left}), size {len(cells)}")
    return errors


def strict_canonical_like(grid):
    errors = _grid_errors(grid)
    if errors:
        return errors
    if (len(grid), len(grid[0])) not in ((7, 7), (7, 8), (8, 7), (8, 8)):
        return ["outside the small canonical canvas family"]
    components = _components(grid)
    targets = sum(color == 3 and shape == X3 for color, _, shape, _, _ in components)
    pluses = sum(color == 4 and shape == PLUS3 for color, _, shape, _, _ in components)
    if not (1 <= targets <= 2 and pluses == 1 and len(components) == targets + pluses):
        return ["expected one or two green Xs and one yellow plus"]
    return []


def observe_overrides(grid):
    components = _components(grid)
    targets = [obj for obj in components if obj[0] == 3 and obj[2] == X3]
    mixed = any(color == 3 and shape == X5 for color, _, shape, _, _ in components)
    if mixed:
        colors = {grid[top + r][left + c] for _, _, _, top, left in targets
                  for r, c in HOLES if grid[top + r][left + c] != 0}
    else:
        colors = {color for color, _, _, _, _ in components if color != 3}
    foreground = [(r, c) for r, row in enumerate(grid) for c, color in enumerate(row) if color]
    padding = min(min(r for r, c in foreground), min(c for r, c in foreground),
                  len(grid) - 1 - max(r for r, c in foreground),
                  len(grid[0]) - 1 - max(c for r, c in foreground))
    if len(colors) != 1:
        raise ValueError("not an observable generated scene: auxiliary color is not unique")
    return {"n": len(targets), "padding": padding, "distractor_color": next(iter(colors)),
            "scene": "mixed" if mixed else "core"}


def _rival(grid, *, mode):
    """Counterfactual predictions for finite evidence, never authoritative labels."""
    output = [row[:] for row in grid]
    if mode in ("all_green", "all_nonzero"):
        for r, row in enumerate(grid):
            for c, color in enumerate(row):
                if (color == 3 if mode == "all_green" else color != 0):
                    output[r][c] = 2
        return output
    if mode in ("local_x", "zero_hole_bitmap"):
        for top in range(len(grid) - 2):
            for left in range(len(grid[0]) - 2):
                if all(grid[top + r][left + c] == 3 for r, c in X3):
                    if mode == "zero_hole_bitmap" and any(grid[top + r][left + c] for r, c in HOLES):
                        continue
                    _stamp(output, (top, left), X3, 2)
        return output
    components = _components(grid)
    x_colors = [color for color, _, shape, _, _ in components if shape == X3]
    color_choice = ((min(x_colors) if mode == "minimum_x_color" else max(x_colors))
                    if x_colors else None)
    selected_first = False
    for color, cells, shape, top, left in components:
        selected = color == 3 and shape == X3
        if mode == "any_color_x":
            selected = shape == X3
        elif mode in ("minimum_x_color", "maximum_x_color"):
            selected = color == color_choice and shape == X3
        elif mode == "green_size_five":
            selected = color == 3 and len(cells) == 5
        elif mode == "green_bbox_three":
            selected = color == 3 and max(r for r, c in shape) == 2 and max(c for r, c in shape) == 2
        elif mode == "zero_hole_component":
            selected = selected and all(grid[top + r][left + c] == 0 for r, c in HOLES)
        elif mode == "any_odd_size_x":
            size = max(r for r, c in shape) + 1
            selected = (color == 3 and size >= 3 and size % 2 == 1 and
                        shape == ({(i, i) for i in range(size)} | {(i, size - 1 - i) for i in range(size)}))
        elif mode == "first_x":
            selected = selected and not selected_first
        if selected:
            selected_first = True
            for r, c in cells:
                output[r][c] = 2
    return output


_CANONICAL_RIVAL_NAMES = (
    "all_green", "any_color_x", "green_size_five", "green_bbox_three", "local_x",
    "zero_hole_bitmap", "zero_hole_component", "any_odd_size_x",
    "minimum_x_color", "maximum_x_color",
)
SEMANTIC_RIVALS = {name: partial(_rival, mode=name) for name in
                   _CANONICAL_RIVAL_NAMES + ("first_x", "all_nonzero")}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {name: SEMANTIC_RIVALS[name] for name in _CANONICAL_RIVAL_NAMES}


def _complete_contrast_scene(grid):
    if _grid_errors(grid):
        return False
    components = _components(grid)
    targets = [obj for obj in components if obj[0] == 3 and obj[2] == X3]
    return (len(targets) >= 2
            and any(color == 3 and shape == PLUS3 for color, _, shape, _, _ in components)
            and any(color == 3 and shape == X5 for color, _, shape, _, _ in components)
            and any(color < 3 and shape == X3 for color, _, shape, _, _ in components)
            and any(color > 3 and shape == X3 for color, _, shape, _, _ in components)
            and any(grid[top + r][left + c] not in (0, 3)
                    for _, _, _, top, left in targets for r, c in HOLES))


SEMANTIC_WITNESSES = {"complete_contrast_scene": _complete_contrast_scene}
WITNESS_RIVALS = {"complete_contrast_scene": list(SEMANTIC_RIVALS)}
