"""Portable input construction for occluded rectangular room partitions.

The reference computes output labels.  This module owns input construction and
its geometric grammar; it imports no task workspace or reference at runtime.
"""
RULE_TASK_ID = 'ee_89565ca0'

from puzzle_generators import gen_ctx


GENERATOR_ID = "public_eval_89565ca0"
TASK_ID = GENERATOR_ID
VERSION = "1.0.0"
RULE_HASH = "db2bfcdb28cc"
SUMMARY = "Recover colored rectangular partitions through noise and overlap, count rooms, and rank their color bars."
INVARIANTS = [
    "Exact-list rectangular integer grids have colors 0..9 and dimensions at most 30 by 30.",
    "Exactly one nonzero color has an observed pixel off its adjacent-pair-supported axes; it is noise.",
    "Two through eight structural colors each describe one rectangular frame with rectangular enclosed rooms.",
    "Consecutive supported axes are at least two cells apart; own-color pixels lie on the restored network.",
    "Elementary wall intervals require an own-color interior witness; the outer perimeter is complete.",
    "Every restored wall pixel is nonzero, so corruption and overlap replace wall colors without deleting walls.",
    "Every structural color has one through thirty four-connected rectangular rooms.",
    "Final inputs preserve the exact latent wall sets, bounding boxes, and room counts after all occlusions.",
]
AXES = {
    "noise_budget": {
        "type": "int", "valid": "8..32",
        "description": "Exact total number of noise-colored cells in the input, including required damage witnesses.",
    },
}
DIVERSITY = {
    "palette": "per-scene permutation, with teaching ties deliberately opposing numeric color order",
    "topology": "recursive rectangular splits, partial T junctions, grids, and unequal room areas",
    "placement": "overlapping frames, separated tie positions, and shared-left tie positions",
    "damage": "scattered background noise and wall occlusions that preserve latent geometry",
    "scale": "small inputs through a 30 by 30 canvas with a thirty-room five-by-six partition",
}


def _shape(grid):
    if type(grid) is not list or not 1 <= len(grid) <= 30:
        raise ValueError("Grid must contain 1..30 exact-list rows")
    if type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30:
        raise ValueError("Grid must contain 1..30 columns")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width for row in grid):
        raise ValueError("Grid rows must be exact lists of equal length")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("Colors must be exact integers in 0..9")
    return len(grid), width


def _perimeter(box):
    top, left, bottom, right = box
    return ({(top, c) for c in range(left, right + 1)}
            | {(bottom, c) for c in range(left, right + 1)}
            | {(r, left) for r in range(top, bottom + 1)}
            | {(r, right) for r in range(top, bottom + 1)})


def _region_areas(walls):
    height, width = len(walls), len(walls[0])
    seen = set()
    areas = []
    for row in range(1, height - 1):
        for col in range(1, width - 1):
            if walls[row][col] or (row, col) in seen:
                continue
            cells = [(row, col)]
            seen.add((row, col))
            for r, c in cells:
                for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                    if (0 < nr < height - 1 and 0 < nc < width - 1
                            and not walls[nr][nc] and (nr, nc) not in seen):
                        seen.add((nr, nc))
                        cells.append((nr, nc))
            top, bottom = min(r for r, c in cells), max(r for r, c in cells)
            left, right = min(c for r, c in cells), max(c for r, c in cells)
            if len(cells) != (bottom - top + 1) * (right - left + 1):
                raise ValueError("Every enclosed room must be rectangular")
            areas.append(len(cells))
    if not 1 <= len(areas) <= 30:
        raise ValueError("Each structure must enclose 1..30 rooms")
    return areas


def analyze(grid):
    """Recover supported wall networks from values, without using any labels."""
    height, width = _shape(grid)
    colors = sorted({value for row in grid for value in row} - {0})
    descriptions = []
    for color in colors:
        points = {(r, c) for r in range(height) for c in range(width) if grid[r][c] == color}
        top, bottom = min(r for r, c in points), max(r for r, c in points)
        left, right = min(c for r, c in points), max(c for r, c in points)
        rows = sorted({top, bottom} | {
            r for r in range(top, bottom + 1)
            if any(grid[r][c] == grid[r][c + 1] == color for c in range(left, right))
        })
        cols = sorted({left, right} | {
            c for c in range(left, right + 1)
            if any(grid[r][c] == grid[r + 1][c] == color for r in range(top, bottom))
        })
        descriptions.append({"color": color, "bbox": [top, left, bottom, right],
                             "rows": rows, "cols": cols, "points": points,
                             "off_axis": any(r not in rows and c not in cols for r, c in points)})
    noise = [info for info in descriptions if info["off_axis"]]
    if len(noise) != 1:
        raise ValueError("Exactly one nonzero color must have off-axis noise pixels")
    noise_color = noise[0]["color"]
    structures = [info for info in descriptions if info["color"] != noise_color]
    if not 2 <= len(structures) <= 8:
        raise ValueError("The input must contain 2..8 structural colors")
    records = []
    for info in structures:
        color, box = info["color"], info["bbox"]
        top, left, bottom, right = box
        rows, cols = info["rows"], info["cols"]
        if (len(rows) < 2 or len(cols) < 2
                or any(b - a < 2 for a, b in zip(rows, rows[1:]))
                or any(b - a < 2 for a, b in zip(cols, cols[1:]))):
            raise ValueError("Consecutive structural axes must be at least two cells apart")
        horizontal = [[r, a, b] for r in rows for a, b in zip(cols, cols[1:])
                      if any(grid[r][c] == color for c in range(a + 1, b))]
        vertical = [[c, a, b] for c in cols for a, b in zip(rows, rows[1:])
                    if any(grid[r][c] == color for r in range(a + 1, b))]
        points = _perimeter(box)
        for r, a, b in horizontal:
            points.update((r, c) for c in range(a, b + 1))
        for c, a, b in vertical:
            points.update((r, c) for r in range(a, b + 1))
        if not info["points"] <= points:
            raise ValueError("Every observed structural pixel must lie on a supported wall")
        if any(grid[r][c] == 0 for r, c in points):
            raise ValueError("A reconstructed wall cannot cross raw background")
        walls = [[int((r, c) in points) for c in range(left, right + 1)]
                 for r in range(top, bottom + 1)]
        areas = _region_areas(walls)
        records.append({"color": color, "bbox": box, "rows": rows, "cols": cols,
                        "horizontal": horizontal, "vertical": vertical, "walls": walls,
                        "rooms": len(areas), "room_areas": areas})
    return {"noise_color": noise_color, "objects": records}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Return input-grammar violations; never compute a rendered label."""
    try:
        analyze(grid)
    except (TypeError, ValueError) as exc:
        return [str(exc)]
    return []


def observe_overrides(grid):
    """Measure the exact realized axis from input cells, without provenance."""
    noise_color = analyze(grid)["noise_color"]
    return {"noise_budget": sum(value == noise_color for row in grid for value in row)}


def _frame(color, box, horizontal=(), vertical=(), rooms=1):
    points = _perimeter(box)
    for row, start, stop in horizontal:
        points.update((row, col) for col in range(start, stop + 1))
    for col, start, stop in vertical:
        points.update((row, col) for row in range(start, stop + 1))
    return {"color": color, "bbox": list(box), "points": points, "rooms": rooms}


def _partition(color, box, count, rng):
    """Construct a latent rectangular subdivision by count-increasing splits."""
    top, left, bottom, right = box
    for _ in range(32):
        regions = [box]
        horizontal, vertical = [], []
        row_axes, col_axes = {top, bottom}, {left, right}
        while len(regions) < count:
            options = []
            for index, (t, l, b, r) in enumerate(regions):
                for cut in range(t + 2, b - 1):
                    if all(abs(cut - existing) >= 2 for existing in row_axes):
                        options.append((index, True, cut))
                for cut in range(l + 2, r - 1):
                    if all(abs(cut - existing) >= 2 for existing in col_axes):
                        options.append((index, False, cut))
            if not options:
                break
            index, across, cut = rng.choice(options)
            t, l, b, r = regions.pop(index)
            if across:
                horizontal.append((cut, l, r))
                row_axes.add(cut)
                regions.extend(((t, l, cut, r), (cut, l, b, r)))
            else:
                vertical.append((cut, t, b))
                col_axes.add(cut)
                regions.extend(((t, l, b, cut), (t, cut, b, r)))
        if len(regions) == count:
            return _frame(color, box, horizontal, vertical, count)
    raise RuntimeError("Could not construct the requested latent partition within 32 attempts")


def _scene(role, palette, rng):
    """Return latent walls and counts before any overlap or noise is painted."""
    first, second = max(palette[:2]), min(palette[:2])
    third = palette[2]
    forced, protected = [], set()
    if role == 0:
        height, width = 24, 28
        records = [
            _frame(first, (10, 1, 21, 13), [(16, 1, 7)], [(7, 10, 21)], 3),
            _frame(second, (1, 15, 12, 26), [(7, 20, 26)], [(20, 1, 12)], 3),
            _frame(third, (8, 12, 10, 14)),
        ]
        # The tiny one-room frame remains a visible rectangle, with one noisy
        # corner. Its seven surviving cells are fewer than every legal noise
        # budget; frequency cannot identify the noise color in this first demo.
        forced = [(8, 12)]
        protected = records[2]["points"] - set(forced)
    elif role == 1:
        height, width = 29, 30
        records = [
            _frame(first, (1, 1, 10, 14), [(5, 1, 5)], [(5, 1, 10), (9, 1, 10)], 4),
            _frame(second, (14, 1, 27, 14), [(20, 1, 14)], [(7, 14, 27)], 4),
            # Its top edge fills the first frame's absent H=5, x=9..14
            # interval. Left=8 avoids erasing either frame's true V=9/V=7.
            _frame(third, (5, 8, 24, 28), vertical=[(19, 5, 24)], rooms=2),
        ]
    elif role == 103:
        height = width = 30
        records = [
            _frame(palette[0], (2, 2, 22, 26),
                   [(r, 2, 26) for r in (6, 10, 14, 18)],
                   [(c, 2, 22) for c in (6, 10, 14, 18, 22)], 30),
            _frame(palette[1], (0, 0, 8, 8)),
            _frame(palette[2], (1, 15, 9, 29), vertical=[(21, 1, 9)], rooms=2),
        ]
    else:
        profiles = {
            2: (18, 25, [((2, 2, 16, 18), (4, 6)), ((0, 12, 8, 24), (1, 2))]),
            3: (25, 26, [((3, 3, 22, 22), (6, 9)), ((0, 0, 10, 11), (1, 3)),
                         ((12, 17, 24, 25), (2, 3))]),
            4: (20, 30, [((2, 2, 17, 26), (5, 8)), ((0, 18, 9, 29), (1, 3)),
                         ((9, 0, 19, 12), (2, 4))]),
            5: (28, 27, [((2, 2, 24, 23), (9, 12)), ((0, 14, 10, 26), (2, 4)),
                         ((16, 0, 27, 11), (1, 3))]),
            100: (12, 15, [((1, 1, 8, 8), (1, 1)), ((5, 6, 10, 13), (2, 3))]),
            101: (19, 23, [((2, 2, 16, 19), (4, 7)), ((0, 13, 8, 22), (1, 3)),
                           ((10, 0, 18, 9), (2, 3))]),
            102: (26, 29, [((2, 2, 22, 25), (10, 16)), ((0, 16, 10, 28), (2, 4)),
                           ((15, 0, 25, 11), (3, 5))]),
        }
        height, width, definitions = profiles[role]
        records = [_partition(palette[index], box, rng.randint(*counts), rng)
                   for index, (box, counts) in enumerate(definitions)]
    if role not in (0, 1):
        flip_rows, flip_cols = rng.randrange(2), rng.randrange(2)
        for record in records:
            record["points"] = {
                (height - 1 - r if flip_rows else r, width - 1 - c if flip_cols else c)
                for r, c in record["points"]
            }
            points = record["points"]
            record["bbox"] = [min(r for r, c in points), min(c for r, c in points),
                              max(r for r, c in points), max(c for r, c in points)]
        if role == 103:
            # The thirty-room network itself must need foreign-wall recovery.
            # Keep it underneath the two smaller overlapping frames.
            tail = records[1:]
            rng.shuffle(tail)
            records = [records[0]] + tail
        else:
            rng.shuffle(records)
    return height, width, records, forced, protected


def _matches_latent(grid, expected, noise_color):
    """Reject damaged truth even if a different inferred count looks lawful."""
    try:
        info = analyze(grid)
    except (TypeError, ValueError):
        return False
    if info["noise_color"] != noise_color or len(info["objects"]) != len(expected):
        return False
    observed = {record["color"]: record for record in info["objects"]}
    for latent in expected:
        record = observed.get(latent["color"])
        if record is None or record["bbox"] != latent["bbox"] or record["rooms"] != latent["rooms"]:
            return False
        top, left, _, _ = record["bbox"]
        points = {(top + r, left + c) for r, row in enumerate(record["walls"])
                  for c, value in enumerate(row) if value}
        if points != latent["points"]:
            return False
    return True


def _paint_and_damage(height, width, latent, noise_color, budget, forced, protected, rng):
    grid = [[0] * width for _ in range(height)]
    for record in latent:
        for row, col in record["points"]:
            grid[row][col] = record["color"]
    # A genuine foreign-wall occlusion must survive before noise is added.
    if not any(grid[r][c] != record["color"] for record in latent for r, c in record["points"]):
        return None
    mandatory = {(0, 0), (height - 1, width - 1)} | set(forced)
    interior_empty = [(r, c) for r in range(1, height - 1) for c in range(1, width - 1)
                      if grid[r][c] == 0 and (r, c) not in protected]
    rng.shuffle(interior_empty)
    if not interior_empty:
        return None
    # The interior isolated point is off the bbox sides even when no adjacent
    # noise pairs yet exist. Later edits retain the unique off-axis detector.
    mandatory.add(interior_empty[0])
    for row, col in mandatory:
        grid[row][col] = noise_color
    if not _matches_latent(grid, latent, noise_color):
        return None
    wall_points = set().union(*(record["points"] for record in latent))
    if not any(grid[r][c] == noise_color for r, c in wall_points):
        choices = sorted(wall_points - protected - mandatory)
        rng.shuffle(choices)
        damaged = False
        for row, col in choices:
            old = grid[row][col]
            grid[row][col] = noise_color
            if _matches_latent(grid, latent, noise_color):
                mandatory.add((row, col))
                damaged = True
                break
            grid[row][col] = old
        if not damaged:
            return None
    count = len(mandatory)
    selected = None
    choices = [(r, c) for r in range(height) for c in range(width)
               if (r, c) not in protected and grid[r][c] != noise_color]
    rng.shuffle(choices)
    for row, col in choices:
        if count == 32:
            break
        old = grid[row][col]
        grid[row][col] = noise_color
        if _matches_latent(grid, latent, noise_color):
            count += 1
            if count == budget:
                selected = [values[:] for values in grid]
        else:
            grid[row][col] = old
    # Complete the maximum legal damage bank before selecting a prefix.
    # Geometry resampling is therefore independent of the noise override.
    if count != 32 or selected is None:
        return None
    if not any(grid[r][c] not in (record["color"], noise_color)
               for record in latent for r, c in record["points"]):
        return None
    for record in latent:
        if record["rooms"] == 30 and not any(
                grid[r][c] not in (record["color"], noise_color) for r, c in record["points"]):
            return None
    return selected


def _validate_seed(seed):
    if type(seed) is not int:
        raise TypeError("seed must be an exact integer")
    if not 0 <= seed < 2**63:
        raise ValueError("seed must be between 0 and 2**63 - 1")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Generate fresh inputs; 0..5 teach, 100..103 are four query roles.

    Other indices are unbounded nonnegative integers. The noise override is
    sampled on its own keyed stream and cannot change palette or latent layout.
    """
    _validate_seed(seed)
    if type(sample_index) is not int:
        raise TypeError("sample_index must be an exact integer")
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")
    if difficulty is not None and (type(difficulty) is not str or difficulty not in ("easy", "medium", "hard")):
        raise ValueError("difficulty must be None, easy, medium, or hard")
    unknown = set(overrides) - {"noise_budget"}
    if unknown:
        raise TypeError("Unknown generator overrides: " + ", ".join(sorted(unknown)))
    if "noise_budget" in overrides and type(overrides["noise_budget"]) is not int:
        raise TypeError("noise_budget must be an exact integer")
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    noise_budget = ctx.draw_int_strict("noise_budget", 8, 32)
    if difficulty == "easy":
        role = 100
    elif difficulty == "hard":
        role = 103
    elif 0 <= sample_index < 6 or 100 <= sample_index < 104:
        role = sample_index
    else:
        role = ctx.draw_rng("scene-role").choice((2, 3, 4, 5, 100, 101, 102, 103))
    palette = list(range(1, 10))
    ctx.draw_rng("palette").shuffle(palette)
    noise_color = palette[-1]
    for attempt in range(96):
        geometry_rng = ctx.draw_rng(f"latent-geometry-{attempt}")
        height, width, latent, forced, protected = _scene(role, palette, geometry_rng)
        grid = _paint_and_damage(height, width, latent, noise_color, noise_budget,
                                 forced, protected, ctx.draw_rng(f"damage-{attempt}"))
        if grid is not None:
            return grid
    raise RuntimeError("Could not preserve latent partitions within the bounded 96-scene draw budget")
