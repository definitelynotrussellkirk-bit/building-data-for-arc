"""Native parametric family for 17b0b2791dd2.

``exact_vertical3`` is the byte-exact canonical rule: recolor exact blue
vertical triples red.  ``nearest_horizontal3`` keeps those exact vertical
triples as selectors.  Each selector chooses the exact horizontal triple with
minimum cell-to-cell Manhattan distance (reading order breaks ties), and the
union of selected horizontal triples is recolored red.

Inputs are matched across settings.  Python labels are deterministic claims;
native qualification re-executes every selected program through protected
Racket.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import random
from typing import Iterable, Sequence

TASK_ID = "17b0b2791dd2"
POLICIES = ("exact_vertical3", "nearest_horizontal3")
HERE = Path(__file__).resolve().parent
CANONICAL = (HERE / "canonical.rkt").read_text(encoding="utf-8")

NEAREST_HORIZONTAL3 = r"""(rule! (let ((dummy 0))
  (define (objs-of color)
    (filter (lambda (obj) (= (obj-color obj) color)) (objects g 0)))
  (define (reading< a b)
    (or (< (obj-r1 a) (obj-r1 b))
        (and (= (obj-r1 a) (obj-r1 b)) (< (obj-c1 a) (obj-c1 b)))))
  (define (v3? obj)
    (equal? (normalize-cells (obj-cells obj))
            (list (list 0 0) (list 1 0) (list 2 0))))
  (define (h3? obj)
    (equal? (normalize-cells (obj-cells obj))
            (list (list 0 0) (list 0 1) (list 0 2))))
  (define (cell-distance a b)
    (+ (abs (- (first a) (first b)))
       (abs (- (second a) (second b)))))
  (define (object-distance a b)
    (apply min
      (map (lambda (pa)
             (apply min
               (map (lambda (pb) (cell-distance pa pb)) (obj-cells b))))
           (obj-cells a))))
  (define selectors (sort (filter v3? (objs-of 1)) reading<))
  (define candidates (sort (filter h3? (objs-of 1)) reading<))
  (define (nearest selector)
    (for/fold ((best (first candidates))) ((candidate (in-list (rest candidates))))
      (let ((dc (object-distance selector candidate))
            (db (object-distance selector best)))
        (if (or (< dc db) (and (= dc db) (reading< candidate best)))
            candidate
            best))))
  (define selected (map nearest selectors))
  (for/fold ((out g)) ((obj (in-list selected)))
    (paint-cells out (obj-cells obj) 2))))"""

Cell = tuple[int, int]
Shape = tuple[Cell, ...]
Grid = list[list[int]]

V3: Shape = ((0, 0), (1, 0), (2, 0))
H3: Shape = ((0, 0), (0, 1), (0, 2))
V4: Shape = ((0, 0), (1, 0), (2, 0), (3, 0))
H4: Shape = ((0, 0), (0, 1), (0, 2), (0, 3))
SQUARE4: Shape = ((0, 0), (0, 1), (1, 0), (1, 1))
L5: Shape = ((0, 0), (1, 0), (2, 0), (2, 1), (2, 2))
T5: Shape = ((0, 0), (0, 1), (0, 2), (1, 1), (2, 1))
Z5: Shape = ((0, 0), (0, 1), (1, 1), (2, 1), (2, 2))
U7: Shape = ((0, 0), (1, 0), (2, 0), (2, 1), (2, 2), (1, 2), (0, 2))
DISTRACTOR_SHAPES = (V4, H4, SQUARE4, L5, T5, Z5, U7)
DIRS4 = ((-1, 0), (1, 0), (0, -1), (0, 1))

# height, width, selector count, horizontal-candidate count, distractor count
DEMO_PROFILES = (
    (12, 12, 2, 4, 3),
    (13, 15, 2, 4, 4),
    (14, 16, 3, 5, 4),
    (16, 18, 3, 5, 5),
    (18, 20, 4, 6, 5),
    (20, 22, 4, 6, 6),
)
QUERY_PROFILES = (
    (14, 16, 2, 5, 5),
    (18, 20, 3, 6, 6),
    (24, 26, 4, 7, 7),
    (30, 30, 5, 8, 8),
)


def _exact_int(name: str, value, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _policy(settings) -> str:
    if (
        type(settings) is not dict
        or set(settings) != {"target_policy"}
        or type(settings["target_policy"]) is not str
        or settings["target_policy"] not in POLICIES
    ):
        raise ValueError("settings must contain exactly one declared target_policy")
    return settings["target_policy"]


def program(settings) -> str:
    return CANONICAL if _policy(settings) == POLICIES[0] else NEAREST_HORIZONTAL3


def _validate_grid(grid) -> tuple[int, int]:
    if (
        type(grid) is not list
        or not grid
        or type(grid[0]) is not list
        or not grid[0]
        or not 1 <= len(grid) <= 30
        or not 1 <= len(grid[0]) <= 30
    ):
        raise ValueError("grid must be a nonempty rectangular grid no larger than 30x30")
    width = len(grid[0])
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(value) is not int or not 0 <= value <= 9 for value in row)
        for row in grid
    ):
        raise ValueError("grid must contain exact integer ARC colors 0..9")
    return len(grid), width


def _components(grid: Sequence[Sequence[int]]) -> list[list[Cell]]:
    height, width = _validate_grid(grid)
    seen: set[Cell] = set()
    result: list[list[Cell]] = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] != 1 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells: list[Cell] = []
            while stack:
                current = stack.pop()
                cells.append(current)
                for dr, dc in DIRS4:
                    neighbor = (current[0] + dr, current[1] + dc)
                    if (
                        0 <= neighbor[0] < height
                        and 0 <= neighbor[1] < width
                        and grid[neighbor[0]][neighbor[1]] == 1
                        and neighbor not in seen
                    ):
                        seen.add(neighbor)
                        stack.append(neighbor)
            result.append(sorted(cells))
    return result


def _normalize(cells: Iterable[Cell]) -> Shape:
    cells = tuple(cells)
    top = min(row for row, _ in cells)
    left = min(col for _, col in cells)
    return tuple(sorted((row - top, col - left) for row, col in cells))


def _reading_key(cells: Sequence[Cell]) -> tuple[int, int]:
    return min(cells)


def _object_distance(left: Sequence[Cell], right: Sequence[Cell]) -> int:
    return min(
        abs(lr - rr) + abs(lc - rc)
        for lr, lc in left
        for rr, rc in right
    )


def _scene_objects(grid):
    objects = _components(grid)
    selectors = sorted((cells for cells in objects if _normalize(cells) == V3), key=_reading_key)
    candidates = sorted((cells for cells in objects if _normalize(cells) == H3), key=_reading_key)
    if not selectors or not candidates:
        raise ValueError("input needs at least one exact vertical triple and horizontal triple")
    return objects, selectors, candidates


def observables(grid) -> dict:
    objects, selectors, candidates = _scene_objects(grid)
    rows = []
    selected: list[int] = []
    all_unique = True
    for selector_index, selector in enumerate(selectors):
        distances = [_object_distance(selector, candidate) for candidate in candidates]
        best = min(distances)
        nearest = [index for index, value in enumerate(distances) if value == best]
        all_unique &= len(nearest) == 1
        chosen = nearest[0]
        selected.append(chosen)
        rows.append(
            {
                "selector_index": selector_index,
                "distances": distances,
                "nearest_candidate_indices": nearest,
                "selected_candidate_index": chosen,
            }
        )
    unique_selected = list(dict.fromkeys(selected))
    return {
        "object_count": len(objects),
        "selector_count": len(selectors),
        "candidate_count": len(candidates),
        "selector_rows": rows,
        "selected_candidate_indices": selected,
        "unique_selected_candidate_indices": unique_selected,
        "selected_candidate_count": len(unique_selected),
        "all_nearest_unique": bool(all_unique),
    }


def solve(grid, settings):
    policy = _policy(settings)
    _validate_grid(grid)
    output = [list(row) for row in grid]
    _objects, selectors, candidates = _scene_objects(grid)
    if policy == POLICIES[0]:
        targets = selectors
    else:
        targets = []
        for selector in selectors:
            distances = [_object_distance(selector, candidate) for candidate in candidates]
            best = min(distances)
            # Candidates are reading-order sorted, so first minimum is the tie break.
            targets.append(candidates[distances.index(best)])
    for cells in targets:
        for row, col in cells:
            output[row][col] = 2
    return output


def _rng(seed: int, stream: str, index: int = 0) -> random.Random:
    material = f"17b0-parametric-v1:{seed}:{stream}:{index}".encode("ascii")
    return random.Random(int.from_bytes(hashlib.sha256(material).digest(), "big"))


def _shape_size(shape: Shape) -> tuple[int, int]:
    return max(row for row, _ in shape) + 1, max(col for _, col in shape) + 1


def _rotate(shape: Shape) -> Shape:
    height, _width = _shape_size(shape)
    return _normalize((col, height - 1 - row) for row, col in shape)


def _transform(shape: Shape, rng: random.Random) -> Shape:
    transformed = shape
    for _ in range(rng.randrange(4)):
        transformed = _rotate(transformed)
    if rng.randrange(2):
        width = _shape_size(transformed)[1]
        transformed = _normalize((row, width - 1 - col) for row, col in transformed)
    return transformed


def _translated(shape: Shape, top: int, left: int) -> frozenset[Cell]:
    return frozenset((top + row, left + col) for row, col in shape)


def _guard(cells: Iterable[Cell], height: int, width: int) -> frozenset[Cell]:
    guarded = set(cells)
    for row, col in tuple(guarded):
        for dr, dc in DIRS4:
            rr, cc = row + dr, col + dc
            if 0 <= rr < height and 0 <= cc < width:
                guarded.add((rr, cc))
    return frozenset(guarded)


def _placements(shape: Shape, height: int, width: int, *, boundary: bool = False):
    shape_h, shape_w = _shape_size(shape)
    for top in range(height - shape_h + 1):
        for left in range(width - shape_w + 1):
            cells = _translated(shape, top, left)
            if boundary and not any(
                row in (0, height - 1) or col in (0, width - 1) for row, col in cells
            ):
                continue
            yield cells, _guard(cells, height, width)


def _place_many(
    shapes: Sequence[Shape],
    height: int,
    width: int,
    rng: random.Random,
    *,
    first_boundary: bool = False,
) -> list[frozenset[Cell]] | None:
    placed: list[frozenset[Cell]] = []
    blocked: frozenset[Cell] = frozenset()
    for index, shape in enumerate(shapes):
        options = list(
            _placements(
                shape,
                height,
                width,
                boundary=first_boundary and index == 0,
            )
        )
        rng.shuffle(options)
        chosen = next(
            ((cells, guarded) for cells, guarded in options if cells.isdisjoint(blocked)),
            None,
        )
        if chosen is None:
            return None
        cells, guarded = chosen
        placed.append(cells)
        blocked = blocked | guarded
    return placed


def _render(height: int, width: int, objects: Sequence[Iterable[Cell]]) -> Grid:
    grid = [[0] * width for _ in range(height)]
    for cells in objects:
        for row, col in cells:
            if grid[row][col] != 0:
                raise RuntimeError("constructed objects overlap")
            grid[row][col] = 1
    return grid


def _relation_is_teachable(facts: dict) -> bool:
    selector_count = facts["selector_count"]
    selected = facts["unique_selected_candidate_indices"]
    candidate_count = facts["candidate_count"]
    if not facts["all_nearest_unique"]:
        return False
    if not 2 <= len(selected) < candidate_count:
        return False
    prefix = list(range(min(selector_count, candidate_count)))
    suffix = list(range(max(0, candidate_count - selector_count), candidate_count))
    selected_set = set(selected)
    if len(selected) == selector_count and selected_set in (set(prefix), set(suffix)):
        return False
    return True


def _build_scene(seed: int, stream: str, index: int, profile) -> Grid:
    height, width, selector_count, candidate_count, distractor_count = profile
    rng = _rng(seed, stream, index)
    for attempt in range(512):
        local = random.Random(rng.getrandbits(256) ^ attempt)
        relation_shapes = [H3] * candidate_count + [V3] * selector_count
        relation_objects = _place_many(
            relation_shapes,
            height,
            width,
            local,
            first_boundary=True,
        )
        if relation_objects is None:
            continue
        relation_grid = _render(height, width, relation_objects)
        facts = observables(relation_grid)
        if not _relation_is_teachable(facts):
            continue

        # Rebuild with the accepted relation fixed, then place non-target objects
        # around it.  The guard is recomputed so no distractor can merge with a
        # selector or candidate.
        objects = list(relation_objects)
        blocked: set[Cell] = set()
        for cells in objects:
            blocked.update(_guard(cells, height, width))
        ok = True
        for distractor_index in range(distractor_count):
            shape = _transform(
                DISTRACTOR_SHAPES[distractor_index % len(DISTRACTOR_SHAPES)], local
            )
            if shape in (V3, H3):
                raise RuntimeError("distractor transform collapsed into a target shape")
            options = list(_placements(shape, height, width))
            local.shuffle(options)
            chosen = next(
                ((cells, guarded) for cells, guarded in options if cells.isdisjoint(blocked)),
                None,
            )
            if chosen is None:
                ok = False
                break
            cells, guarded = chosen
            objects.append(cells)
            blocked.update(guarded)
        if not ok:
            continue
        grid = _render(height, width, objects)
        final = observables(grid)
        relation_keys = (
            "selector_count",
            "candidate_count",
            "selector_rows",
            "selected_candidate_indices",
            "unique_selected_candidate_indices",
            "selected_candidate_count",
            "all_nearest_unique",
        )
        if any(final[key] != facts[key] for key in relation_keys):
            # Distractors must not alter the selector/candidate relation.
            continue
        if solve(grid, {"target_policy": POLICIES[0]}) == solve(
            grid, {"target_policy": POLICIES[1]}
        ):
            continue
        return grid
    raise RuntimeError(f"profile could not construct a teachable scene: {profile}")


def _grid_bytes(grid) -> bytes:
    return json.dumps(grid, separators=(",", ":")).encode("utf-8")


def generate(seed, settings, demos=3, queries=4):
    _exact_int("seed", seed, 0, 2**63 - 1)
    _exact_int("demos", demos, 2, 6)
    _exact_int("queries", queries, 1, 4)
    _policy(settings)
    training = [
        _build_scene(seed, "demos", index, DEMO_PROFILES[index])
        for index in range(demos)
    ]
    query_profiles = list(QUERY_PROFILES)
    _rng(seed, "query-order").shuffle(query_profiles)
    tests = [
        _build_scene(seed, "queries", index, query_profiles[index])
        for index in range(queries)
    ]
    grids = training + tests
    if len({_grid_bytes(grid) for grid in grids}) != len(grids):
        raise RuntimeError("sampler produced duplicate inputs")

    def pairs(inputs):
        return [{"input": grid, "output": solve(grid, settings)} for grid in inputs]

    return {
        "train": pairs(training),
        "test": pairs(tests),
        "program_solution": program(settings),
        "settings": dict(settings),
        "seed": seed,
    }


def _public_helpers():
    path = HERE.parents[3] / "shared" / "runtime" / "reviewer_support.py"
    name = "_p17b0_public_" + hashlib.sha256(str(path).encode()).hexdigest()
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:  # pragma: no cover
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def public_challenge(episode, query_index=0):
    _exact_int("query_index", query_index, 0, len(episode["test"]) - 1)
    projection = {
        "train": episode["train"],
        "test": [{"input": episode["test"][query_index]["input"]}],
    }
    return json.loads(_public_helpers().public_challenge_bytes(projection))


def public_id(episode, query_index=0):
    return _public_helpers().public_challenge_id(public_challenge(episode, query_index))
