"""Reviewed parametric prototype for cyclic shape continuation.

The canonical ``next`` setting returns the authoritative Racket bytes exactly.
The alternate ``densest_index`` setting first finds the unique largest shape in
the first band, uses its zero-based section index as an input-dependent cyclic
shift, and applies that shift to the final band while preserving section colors.
"""
from __future__ import annotations

from functools import lru_cache
import hashlib
import itertools
import json
import random


TASK_ID = "f65b8464b007"
SETTINGS = ("next", "densest_index")
RIVAL_NAMES = (
    "next",
    "densest_index",
    "no_shift",
    "fixed_two",
    "fixed_three",
    "right_one",
    "sparsest_index",
    "densest_count_mod",
)
CANONICAL_PROGRAM = '(rule! (lambda (g)\n         (let* ((h (rows g))\n                (w (cols g)))\n           (let* ((sw (find-first (lambda (c)\n                                    (all? (lambda (r) (zero? (at g r c))) (range 0 h)))\n                                  (range 1 w)))\n                  (stride (+ sw 1))\n                  (n-shapes (/ (+ w 1) stride))\n                  (starts (map (lambda (i) (* i stride)) (range 0 n-shapes)))\n                  (sep-rows (filter (lambda (r)\n                                      (all? (lambda (c) (zero? (at g r c))) (range 0 w)))\n                                    (range 0 h)))\n                  (last-start (+ 1 (nth sep-rows (- (length sep-rows) 2))))\n                  (first-start (+ 1 (first sep-rows)))\n                  (colors (map (lambda (si)\n                                 (let* ((sc (nth starts si))\n                                        (vals (filter (lambda (v) (!= v 0))\n                                                      (flatmap (lambda (r)\n                                                                 (map (lambda (c)\n                                                                        (at g r c))\n                                                                      (range sc\n                                                                             (+ sc sw))))\n                                                               (range first-start\n                                                                      (+ first-start 3))))))\n                                   (first vals)))\n                               (range 0 n-shapes))))\n             (build-grid 3\n                         w\n                         (r c)\n                         (let* ((si (/ c stride))\n                                (lc (mod c stride)))\n                           (if (or (>= si n-shapes) (>= lc sw))\n                               0\n                               (let* ((src-si (mod (+ si 1) n-shapes))\n                                      (src-sc (nth starts src-si))\n                                      (src-val (at g (+ last-start r) (+ src-sc lc))))\n                                 (if (!= src-val 0) (nth colors si) 0)))))))))'

# The first two demonstrations deliberately use different selector-derived
# shifts, so the two-demo minimum rejects every fixed-shift shortcut below.
_DEMO_PROFILES = (
    (3, 4, 1, 2),
    (4, 5, 2, 3),
    (3, 5, 3, 4),
    (5, 4, 4, 2),
    (4, 4, 5, 3),
    (5, 5, 6, 4),
)
_QUERY_PROFILES = (
    (3, 3, 2, 2),   # 9 x 11 ordinary transfer
    (4, 4, 3, 3),   # 13 x 19 wider sections
    (5, 5, 4, 2),   # 17 x 29 boundary-width case
    (5, 5, 7, 4),   # 29 x 29 maximum square under the grammar
)


def _integer(value, name, low, high):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an integer in {low}..{high}; bool is forbidden")
    return value


def _settings(value):
    if type(value) is not dict or set(value) != {"shift_rule"}:
        raise ValueError("Declare exactly shift_rule=next|densest_index")
    if value["shift_rule"] not in SETTINGS:
        raise ValueError("shift_rule must be next or densest_index")
    return {"shift_rule": value["shift_rule"]}


def _rng(seed, role, index, salt=0):
    payload = f"f65b8464b007-parametric-v1:{seed}:{role}:{index}:{salt}".encode()
    return random.Random(int.from_bytes(hashlib.sha256(payload).digest(), "big"))


@lru_cache(maxsize=None)
def _masks(shape_width, count):
    masks = []
    for occupied in itertools.combinations(range(3 * shape_width), count):
        cells = set(occupied)
        if any(not any(row * shape_width + col in cells for col in range(shape_width))
               for row in range(3)):
            continue
        if any(not any(row * shape_width + col in cells for row in range(3))
               for col in range(shape_width)):
            continue
        masks.append("".join("1" if index in cells else "0"
                             for index in range(3 * shape_width)))
    if not masks:
        raise ValueError(f"No spanning masks for width={shape_width}, count={count}")
    return tuple(masks)


def _counts(shape_width, n_sections, densest_index):
    maximum = 3 * shape_width - 1
    minimum = shape_width
    sparsest_index = (densest_index + 1) % n_sections
    counts = [None] * n_sections
    counts[densest_index] = maximum
    counts[sparsest_index] = minimum
    next_count = minimum + 1
    for index in range(n_sections):
        if counts[index] is None:
            counts[index] = next_count
            next_count += 1
    if not all(minimum <= count <= maximum for count in counts):
        raise AssertionError("profile requests more distinct count levels than available")
    return tuple(counts)


def _build_scene(seed, role, index, profile, salt=0):
    shape_width, n_sections, n_bands, densest_index = profile
    if not (3 <= shape_width <= 5 and 3 <= n_sections <= 5
            and 1 <= n_bands <= 7 and 2 <= densest_index < n_sections):
        raise AssertionError("invalid fixed profile")
    rng = _rng(seed, role, index, salt)
    counts = _counts(shape_width, n_sections, densest_index)
    base = []
    for section, count in enumerate(counts):
        choices = _masks(shape_width, count)
        base.append(choices[rng.randrange(len(choices))])
    if len(set(base)) != n_sections:
        raise AssertionError("count schedule should make first-band masks distinct")
    colors = rng.sample(range(1, 10), n_sections)
    patterns = tuple(
        tuple(base[(section + band) % n_sections] for section in range(n_sections))
        for band in range(n_bands)
    )
    height = 4 * n_bands + 1
    width = n_sections * (shape_width + 1) - 1
    grid = [[0 for _ in range(width)] for _ in range(height)]
    for band, band_patterns in enumerate(patterns):
        top = 1 + 4 * band
        for section, mask in enumerate(band_patterns):
            left = section * (shape_width + 1)
            color = colors[section]
            for offset, occupied in enumerate(mask):
                if occupied == "1":
                    grid[top + offset // shape_width][left + offset % shape_width] = color
    analysis = analyze(grid)
    if analysis["densest_index"] != densest_index:
        raise AssertionError("constructed densest selector changed")
    return grid


def analyze(grid):
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        raise ValueError("grid must be a nonempty list of nonempty rows")
    width = len(grid[0])
    if not 1 <= len(grid) <= 30 or not 1 <= width <= 30:
        raise ValueError("grid dimensions must be within ARC's 1..30 bound")
    if any(type(row) is not list or len(row) != width
           or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
           for row in grid):
        raise ValueError("grid must be rectangular with exact integer ARC colors")
    height = len(grid)
    try:
        shape_width = next(
            col for col in range(1, width)
            if all(grid[row][col] == 0 for row in range(height))
        )
    except StopIteration as error:
        raise ValueError("no all-zero separator column") from error
    stride = shape_width + 1
    if (width + 1) % stride:
        raise ValueError("section width does not tile the grid")
    n_sections = (width + 1) // stride
    separator_rows = [row for row in range(height) if not any(grid[row])]
    if len(separator_rows) < 2 or separator_rows[0] != 0 or separator_rows[-1] != height - 1:
        raise ValueError("bands need blank boundary rows")
    if any(b - a != 4 for a, b in zip(separator_rows, separator_rows[1:])):
        raise ValueError("bands must contain exactly three content rows")
    n_bands = len(separator_rows) - 1
    if not 1 <= n_bands <= 7:
        raise ValueError("one through seven bands are supported")
    if any(grid[row][section * stride + shape_width] != 0
           for section in range(n_sections - 1) for row in range(height)):
        raise ValueError("section separators must remain blank")

    colors = []
    patterns = []
    for band in range(n_bands):
        top = separator_rows[band] + 1
        current = []
        for section in range(n_sections):
            left = section * stride
            cells = [grid[top + row][left + col]
                     for row in range(3) for col in range(shape_width)]
            nonzero = [value for value in cells if value]
            if not nonzero or len(set(nonzero)) != 1:
                raise ValueError("each band-section needs one nonzero color")
            color = nonzero[0]
            if band == 0:
                colors.append(color)
            elif color != colors[section]:
                raise ValueError("section colors must stay fixed")
            mask = "".join("1" if value else "0" for value in cells)
            if any(not any(mask[row * shape_width + col] == "1"
                           for col in range(shape_width)) for row in range(3)):
                raise ValueError("every shape must span all three rows")
            if any(not any(mask[row * shape_width + col] == "1" for row in range(3))
                   for col in range(shape_width)):
                raise ValueError("every shape must span its full section width")
            current.append(mask)
        patterns.append(tuple(current))
    if len(set(colors)) != n_sections:
        raise ValueError("section colors must be distinct")
    if len(set(patterns[0])) != n_sections:
        raise ValueError("first-band shapes must be distinct")
    for index in range(1, n_bands):
        previous = patterns[index - 1]
        expected = tuple(previous[(section + 1) % n_sections]
                         for section in range(n_sections))
        if patterns[index] != expected:
            raise ValueError("input bands must shift left one section")
    counts = tuple(mask.count("1") for mask in patterns[0])
    maximum = max(counts)
    minimum = min(counts)
    if counts.count(maximum) != 1 or counts.count(minimum) != 1:
        raise ValueError("densest and sparsest selectors must be unique")
    return {
        "height": height,
        "width": width,
        "shape_width": shape_width,
        "stride": stride,
        "n_sections": n_sections,
        "n_bands": n_bands,
        "colors": tuple(colors),
        "patterns": tuple(patterns),
        "counts": counts,
        "densest_index": counts.index(maximum),
        "sparsest_index": counts.index(minimum),
    }


def _shift(name, analysis):
    n = analysis["n_sections"]
    if name == "next":
        return 1
    if name == "densest_index":
        return analysis["densest_index"]
    if name == "no_shift":
        return 0
    if name == "fixed_two":
        return 2 % n
    if name == "fixed_three":
        return 3 % n
    if name == "right_one":
        return (n - 1) % n
    if name == "sparsest_index":
        return analysis["sparsest_index"]
    if name == "densest_count_mod":
        return max(analysis["counts"]) % n
    raise ValueError(f"unknown rival {name}")


def transform(grid, settings):
    selected = _settings(settings)
    return transform_rival(grid, selected["shift_rule"])


def transform_rival(grid, name):
    if name not in RIVAL_NAMES:
        raise ValueError(f"unknown rival {name}")
    info = analyze(grid)
    shift = _shift(name, info)
    output = [[0 for _ in range(info["width"])] for _ in range(3)]
    final = info["patterns"][-1]
    for section in range(info["n_sections"]):
        source = final[(section + shift) % info["n_sections"]]
        left = section * info["stride"]
        color = info["colors"][section]
        for offset, occupied in enumerate(source):
            if occupied == "1":
                output[offset // info["shape_width"]][left + offset % info["shape_width"]] = color
    return output


def _program_with_shift(shift_expression):
    return f"""(rule! (lambda (g)
  (let* ((h (rows g))
         (w (cols g)))
    (let* ((sw (find-first (lambda (c)
                             (all? (lambda (r) (zero? (at g r c)))
                                   (range 0 h)))
                           (range 1 w)))
           (stride (+ sw 1))
           (n-shapes (/ (+ w 1) stride))
           (starts (map (lambda (i) (* i stride)) (range 0 n-shapes)))
           (sep-rows (filter (lambda (r)
                               (all? (lambda (c) (zero? (at g r c)))
                                     (range 0 w)))
                             (range 0 h)))
           (last-start (+ 1 (nth sep-rows (- (length sep-rows) 2))))
           (first-start (+ 1 (first sep-rows)))
           (colors (map (lambda (si)
                          (let* ((sc (nth starts si))
                                 (vals (filter (lambda (v) (!= v 0))
                                               (flatmap (lambda (r)
                                                          (map (lambda (c) (at g r c))
                                                               (range sc (+ sc sw))))
                                                        (range first-start (+ first-start 3))))))
                            (first vals)))
                        (range 0 n-shapes)))
           (counts (map (lambda (si)
                          (let* ((sc (nth starts si)))
                            (length (filter (lambda (v) (!= v 0))
                                            (flatmap (lambda (r)
                                                       (map (lambda (c) (at g r c))
                                                            (range sc (+ sc sw))))
                                                     (range first-start (+ first-start 3)))))))
                        (range 0 n-shapes)))
           (shift {shift_expression}))
      (build-grid 3
                  w
                  (r c)
                  (let* ((si (/ c stride))
                         (lc (mod c stride)))
                    (if (or (>= si n-shapes) (>= lc sw))
                        0
                        (let* ((src-si (mod (+ si shift) n-shapes))
                               (src-sc (nth starts src-si))
                               (src-val (at g (+ last-start r) (+ src-sc lc))))
                          (if (!= src-val 0) (nth colors si) 0)))))))))"""


_SHIFT_EXPRESSIONS = {
    "densest_index": "(find-first (lambda (si) (= (nth counts si) (max-list counts))) (range 0 n-shapes))",
    "no_shift": "0",
    "fixed_two": "2",
    "fixed_three": "3",
    "right_one": "(- n-shapes 1)",
    "sparsest_index": "(find-first (lambda (si) (= (nth counts si) (min-list counts))) (range 0 n-shapes))",
    "densest_count_mod": "(mod (max-list counts) n-shapes)",
}


def program(settings):
    selected = _settings(settings)["shift_rule"]
    return CANONICAL_PROGRAM if selected == "next" else _program_with_shift(_SHIFT_EXPRESSIONS[selected])


def rival_program(name):
    if name == "next":
        return CANONICAL_PROGRAM
    if name not in _SHIFT_EXPRESSIONS:
        raise ValueError(f"unknown rival {name}")
    return _program_with_shift(_SHIFT_EXPRESSIONS[name])


def _grid_key(grid):
    return json.dumps(grid, sort_keys=True, separators=(",", ":"))


def generate_episode(seed, *, shift_rule, demos, queries):
    _integer(seed, "seed", 0, 2**63 - 1)
    _integer(demos, "demos", 2, 6)
    _integer(queries, "queries", 4, 4)
    selected = _settings({"shift_rule": shift_rule})
    seen = set()
    pairs = []
    schedules = (("demo", _DEMO_PROFILES[:demos]), ("query", _QUERY_PROFILES))
    for role, profiles in schedules:
        for index, profile in enumerate(profiles):
            for salt in range(32):
                grid = _build_scene(seed, role, index, profile, salt)
                key = _grid_key(grid)
                if key not in seen:
                    break
            else:
                raise RuntimeError("distinct input budget exhausted; no partial episode emitted")
            seen.add(key)
            pairs.append({"input": grid, "output": transform(grid, selected)})
    episode = {
        "train": pairs[:demos],
        "test": pairs[demos:],
        "program_solution": program(selected),
    }
    certificate = lesson_certificate(episode)
    if certificate["survivors"] != [shift_rule] or not certificate["identifiable"]:
        raise ValueError("demonstrations do not identify the selected rule among finite rivals")
    return episode


def lesson_certificate(episode):
    if type(episode) is not dict or type(episode.get("train")) is not list             or type(episode.get("test")) is not list:
        raise ValueError("episode needs train and test lists")
    train = episode["train"]
    test = episode["test"]
    survivors = [
        name for name in RIVAL_NAMES
        if all(transform_rival(pair["input"], name) == pair["output"] for pair in train)
    ]
    if len(survivors) == 1:
        selected = survivors[0]
        query_disagreements = {
            name: any(transform_rival(pair["input"], name) != pair["output"] for pair in test)
            for name in RIVAL_NAMES if name != selected
        }
    else:
        query_disagreements = {}
    return {
        "rivals": list(RIVAL_NAMES),
        "survivors": survivors,
        "query_disagreements": query_disagreements,
        "identifiable": len(survivors) == 1 and bool(query_disagreements)
                        and all(query_disagreements.values()),
    }
