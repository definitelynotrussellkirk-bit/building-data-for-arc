"""Native hole-count packing with an episode-fixed painted-area tie break.

The default program is the exact selected canonical rule. Python labels are
claims, independently replayed by protected Racket in audit and qualification.
The opt-in sampler extends the original three-object grammar to six objects
and meaningful 30x30 scenes without modifying the canonical generator.
"""
from __future__ import annotations

from functools import lru_cache
from itertools import permutations
from pathlib import Path
import random

from reviewer_support import find_root, load_selected_generator, public_challenge_bytes


TASK_ID = "73d82a9cacf6"
AREA_ORDERS = ("larger_first", "smaller_first")
HOME = Path(__file__).resolve().parent
DEMO_CANVASES = ((18, 24), (20, 26), (19, 25), (21, 27), (20, 28), (22, 29))
QUERY_CANVASES = ((10, 16), (22, 26), (26, 28), (30, 30))


def _settings(settings):
    if (type(settings) is not dict or set(settings) != {"area_order"}
            or type(settings["area_order"]) is not str
            or settings["area_order"] not in AREA_ORDERS):
        raise ValueError("settings must be exactly area_order=larger_first or smaller_first")
    return settings["area_order"]


def _integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")


@lru_cache(maxsize=1)
def _canonical():
    return (HOME / "canonical.rkt").read_text(encoding="utf-8")


def program(settings):
    order = _settings(settings)
    canonical = _canonical()
    if order == "larger_first":
        return canonical
    needle = "(- (obj-size obj))"
    if canonical.count(needle) != 1:
        raise ValueError("canonical area key changed; review the smaller-first adapter")
    return canonical.replace(needle, "(obj-size obj)")


@lru_cache(maxsize=1)
def _source():
    return load_selected_generator(TASK_ID, root=find_root(__file__))[0]


def _objects(grid):
    """Validate the extended grammar before relying on source crop helpers.

    Disjoint bounding boxes matter: the canonical crop reads the original
    input rectangle, whereas its hole count is computed from object cells.
    An object nested inside another object's box would break that equivalence.
    """
    if (type(grid) is not list or not 1 <= len(grid) <= 30
            or any(type(row) is not list for row in grid)):
        raise ValueError("grid must have 1..30 list rows")
    width = len(grid[0])
    if not 1 <= width <= 30 or any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular with width 1..30")
    if any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row):
        raise ValueError("grid cells must be exact integer ARC colors 0..9")
    if not any(v == 0 for row in grid for v in row):
        raise ValueError("black background must be present")
    gen = _source()
    objects = gen._objects(grid)
    if not 3 <= len(objects) <= 6:
        raise ValueError("extended grammar requires 3..6 objects")
    if len({o["color"] for o in objects}) != len(objects):
        raise ValueError("each disconnected object must have a distinct color")
    for i, a in enumerate(objects):
        for b in objects[i + 1:]:
            if not (a["bottom"] < b["top"] or b["bottom"] < a["top"]
                    or a["right"] < b["left"] or b["right"] < a["left"]):
                raise ValueError("object bounding boxes must be pairwise disjoint")
    if gen._touching_object_pairs(objects):
        raise ValueError("objects must not touch, including diagonally")
    if sum(o["width"] for o in objects) + len(objects) - 1 > 30:
        raise ValueError("packed crops and one-column gaps must fit width 30")
    return objects


def predict(grid, settings):
    """Validated Python label claim; native Racket is the answer authority."""
    order = _settings(settings)
    sign = -1 if order == "larger_first" else 1
    objects = _objects(grid)
    objects.sort(key=lambda o: (o["holes"], sign * o["area"], o["color"]))
    return _source()._pack_objects(objects)


def _solid(height, width, missing=()):
    missing = set(missing)
    return tuple(tuple(int((r, c) not in missing) for c in range(width))
                 for r in range(height))


def _frame(height, width):
    return tuple(tuple(int(r in (0, height - 1) or c in (0, width - 1))
                       for c in range(width)) for r in range(height))


def _u_shape(height, width):
    return tuple(tuple(int(r == height - 1 or c in (0, width - 1))
                       for c in range(width)) for r in range(height))


@lru_cache(maxsize=4)
def _profile(name):
    """Construct diagnostic topologies; no stochastic retry or short batch.

    Thin large frames and dense smaller boxes oppose painted area to bbox
    area/perimeter. Diagonally adjacent pockets are distinct 4-connected
    holes but one 8-connected pocket. Their painted areas interleave with
    the one-hole group, exposing that shortcut in both orders. The larger
    two-hole object is less dense, separating raw area from painted density.
    """
    hole_2x2 = ((1, 1), (1, 2), (2, 1), (2, 2))
    if name == "A":
        return (_solid(5, 2), _frame(8, 6), _solid(5, 6, hole_2x2),
                _solid(4, 4, ((1, 1), (2, 2))),
                _solid(8, 4, ((2, 1), (3, 1), (4, 2), (5, 2), (6, 2))))
    if name == "B":
        return (_u_shape(5, 4), _frame(7, 5), _solid(5, 5, hole_2x2),
                _solid(4, 4, ((1, 1), (2, 2))),
                _solid(7, 4, ((1, 1), (2, 1), (3, 2), (4, 2), (5, 2))))
    if name == "C":
        return (_u_shape(6, 4), _frame(11, 6), _solid(7, 6, hole_2x2),
                _solid(5, 4, ((1, 1), (2, 2))),
                _solid(11, 4, ((3, 1), (4, 1), (5, 2), (6, 2), (7, 2))))
    if name == "D":
        interior_hole = tuple((r, 2) for r in range(2, 7))
        return (_solid(13, 1), _frame(13, 6), _solid(10, 6, interior_hole),
                _solid(13, 4, ((4, 1), (5, 1), (6, 2), (7, 2), (8, 2))),
                _solid(11, 3, ((3, 1), (7, 1))),
                _solid(13, 5, ((2, 1), (6, 2), (10, 3))))
    raise ValueError("unknown teaching profile")


@lru_cache(maxsize=4)
def _layout_choices(profile):
    shapes = _profile(profile)
    facts = [(i, _source()._hole_count(shape), sum(map(sum, shape)))
             for i, shape in enumerate(shapes)]
    correct = {tuple(f[0] for f in sorted(facts, key=lambda f: (f[1], sign * f[2])))
               for sign in (-1, 1)}
    # Merely scrambling the whole scan order leaves hole-then-scan sorting
    # alive when the relative order inside each tied group happens to agree.
    # Use opposite area directions in the two tied groups. Applying this same
    # pool to colors also refutes hole-then-color sorting in either setting.
    choices = tuple(p for p in permutations(range(len(shapes)))
                    if tuple(f[0] for f in sorted(facts, key=lambda f: (f[1], p.index(f[0]))))
                    not in correct)
    if not choices:
        raise ValueError("profile no longer supports diagnostic within-group orders")
    return choices


def _scene(seed, role, profile, height, width):
    rng = random.Random(f"{TASK_ID}:hole-order-inputs:{seed}:{role}")
    shapes = _profile(profile)
    n = len(shapes)
    choices = _layout_choices(profile)
    placement = rng.choice(choices)
    color_order = rng.choice(choices)
    palette = sorted(rng.sample(range(1, 10), n))
    colors = dict(zip(color_order, palette))
    max_height = max(len(shape) for shape in shapes)
    if height < 2 * max_height + 1 or width < 20:
        raise ValueError("canvas cannot hold disjoint teaching slots")
    grid = [[0] * width for _ in range(height)]
    for slot, shape_index in enumerate(placement):
        shape = shapes[shape_index]
        shape_width = len(shape[0])
        row_band, column_band = divmod(slot, 3)
        # Shared top coordinates preserve the selected scan-order permutation.
        top = 0 if row_band == 0 else height - max_height
        left = (0 if column_band == 0 else width - shape_width if column_band == 2
                else (width - 6) // 2 + rng.randrange(7 - shape_width))
        for r, row in enumerate(shape):
            for c, painted in enumerate(row):
                if painted:
                    grid[top + r][left + c] = colors[shape_index]
    _objects(grid)
    return grid


def generate(seed, settings, demos, queries):
    """Return deterministic private labels and independently adjustable counts.

    All inputs are fixed by seed and role, independent of setting and counts.
    Every demo teaches both the primary hole key and the secondary area key.
    Ten distinct canvas dimensions guarantee input novelty without rejection.
    """
    _settings(settings)
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    demo_inputs = [_scene(seed, f"demo-{i}", "A" if i % 2 == 0 else "B", h, w)
                   for i, (h, w) in enumerate(DEMO_CANVASES)]
    small = _source().generate(seed, 0, scene_profile="area_tie", canvas_profile="10x16")
    query_inputs = [small] + [
        _scene(seed, f"query-{i}", profile, *QUERY_CANVASES[i])
        for i, profile in enumerate(("A", "C", "D"), start=1)]

    def pair(grid):
        return {"input": grid, "output": predict(grid, settings)}

    return {"train": [pair(grid) for grid in demo_inputs[:demos]],
            "test": [pair(grid) for grid in query_inputs[:queries]],
            "program_solution": program(settings),
            "settings": dict(settings)}


def public_turn(episode, query_index):
    """Exact solver-visible bytes: fixed demos and this query input only."""
    if type(episode) is not dict:
        raise ValueError("episode must be a controller-side record")
    tests = episode.get("test")
    if type(tests) is not list or not tests:
        raise ValueError("episode needs controller-side queries")
    _integer(query_index, 0, len(tests) - 1, "query_index")
    return public_challenge_bytes({"train": episode["train"],
                                   "test": [tests[query_index]]})
