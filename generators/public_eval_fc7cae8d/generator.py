"""Portable input sampler for the public fc7cae8d orientation-crop family.

The shared generator runtime supplies domain-separated keyed random streams.
The reference, rather than this module, computes labels.  No task-workspace
module is required by this portable input sampler.
"""
RULE_TASK_ID = 'ee_fc7cae8d'

from puzzle_generators import gen_ctx


GENERATOR_ID = "public_eval_fc7cae8d"
TASK_ID = GENERATOR_ID
VERSION = "1.0.0"
RULE_HASH = "cf1726a5b800"
SUMMARY = (
    "Orient an isolated picture by matching its two adjacent colored side bars "
    "to the corresponding noisy canvas edges, then discard the bars."
)
INVARIANTS = [
    "One interior nonzero 4-connected component is separated from the canvas frame.",
    "Two distinct reserved colors mark adjacent inner and outer sides.",
    "The inner bars are one cell thick and omit their shared corner.",
    "The payload is at least 3 by 3, connected, and asymmetric under all eight D4 maps.",
    "All exterior nonzero cells are connected to an edge; zero notches remain in the crop.",
    "Inputs are integer grids with colors 0 through 9 and dimensions at most 30 by 30.",
]
AXES = {
    "max_frame_depth": {
        "type": "int", "valid": "1..3",
        "description": "Upper bound on inward frame depth, counting the boundary cell as one.",
    },
}
DIVERSITY = {
    "orientation": "all eight D4 alignments; independent absolute side positions",
    "palette": "per-scene permutation with disjoint frame and payload colors",
    "geometry": "payload dimensions, canvas dimensions, and translated inner placement",
    "payload": "paths, rectangles, repeated marks, asymmetric accents, and edge notches",
    "frame": "sparse distractors, overlapping corners, and connected inward protrusions",
}

# Height, width, picture height, picture width.  Query roles are shuffled only
# after the complete bank exists, so every supported prefix shares its inputs.
_DEMO_SHAPES = (
    (16, 19, 7, 10), (16, 19, 7, 10), (18, 18, 8, 8),
    (21, 25, 12, 16), (14, 21, 5, 11), (25, 25, 15, 15),
)
_QUERY_SHAPES = ((9, 10, 3, 4), (17, 22, 8, 13), (24, 29, 16, 20), (30, 30, 23, 23))


def _validate_seed(seed):
    if type(seed) is not int:
        raise TypeError("seed must be an exact integer")
    if not 0 <= seed < 2**63:
        raise ValueError("seed must be between 0 and 2**63 - 1")


def _orientation(seed, sample_index):
    """Return ordered source sides and their ordered target sides (N,E,S,W)."""
    episode = gen_ctx(seed=seed, sample_index=0, version=VERSION, task_id=TASK_ID).draw_rng(
        "episode-teaching-orientations"
    )
    first_side = episode.randrange(4)
    # Axis reflection plus quarter-turn teaches forward versus inverse under
    # both marker correspondences. A diagonal reflection could make the swap
    # lesson self-inverse, as could a half-turn in the matching lesson.
    reflection_turns = episode.choice((0, 2))
    first_targets = frozenset(
        (reflection_turns - side) % 4 for side in (first_side, (first_side + 1) % 4)
    )
    if sample_index == 0:
        side, reflected, turns = first_side, True, reflection_turns
    elif sample_index == 1:
        side, reflected = (first_side + 1) % 4, False
        choices = [
            turn for turn in (1, 3)
            if frozenset(((side + turn) % 4, (side + 1 + turn) % 4)) != first_targets
        ]
        turns = episode.choice(choices)
    else:
        rng = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION, task_id=TASK_ID).draw_rng(
            "orientation"
        )
        side = rng.randrange(4)
        if 2 <= sample_index < 6:
            reflected, turns = ((False, 0), (False, 2), (False, 3), (True, (reflection_turns + 2) % 4))[sample_index - 2]
        else:
            reflected, turns = bool(rng.randrange(2)), rng.randrange(4)
    sources = (side, (side + 1) % 4)
    targets = tuple(((-value if reflected else value) + turns) % 4 for value in sources)
    return sources, targets


def _shape(ctx, sample_index, difficulty):
    if difficulty == "easy":
        return (11, 14, 4, 7)
    if difficulty == "hard":
        return (30, 30, 23, 23)
    if sample_index < len(_DEMO_SHAPES):
        return _DEMO_SHAPES[sample_index]
    if 100 <= sample_index < 104:
        return _QUERY_SHAPES[sample_index - 100]
    rng = ctx.draw_rng("geometry")
    height, width = rng.randint(10, 30), rng.randint(10, 30)
    return height, width, rng.randint(3, height - 5), rng.randint(3, width - 5)


def _distinct_d4(picture):
    variants = set()
    for reflected in (False, True):
        value = [row[::-1] for row in picture] if reflected else [row[:] for row in picture]
        for _ in range(4):
            variants.add(tuple(tuple(row) for row in value))
            value = [list(row) for row in zip(*value[::-1])]
    return len(variants) == 8


def _picture(height, width, colors, rng):
    background, *accents = colors
    ink = accents[:3]
    beacon_a, beacon_b = accents[-2:]
    for _ in range(64):
        grid = [[background for _ in range(width)] for _ in range(height)]

        # Repeated bent marks provide distributed structure in the largest
        # payloads; additional connected paths and boxes change their layout.
        phase_r, phase_c = rng.randrange(5), rng.randrange(7)
        for row in range(1, height - 1):
            for col in range(1, width - 1):
                if (row + phase_r) % 5 == 0 and col % 3:
                    grid[row][col] = ink[0]
                elif (col + phase_c) % 7 == 0 and row % 4:
                    grid[row][col] = ink[1]

        for motif in range(3 + height * width // 50):
            r0, r1 = sorted((rng.randrange(1, height - 1), rng.randrange(1, height - 1)))
            c0, c1 = sorted((rng.randrange(1, width - 1), rng.randrange(1, width - 1)))
            color = ink[motif % len(ink)]
            for col in range(c0, c1 + 1):
                grid[r0][col] = color
            for row in range(r0, r1 + 1):
                grid[row][c1] = color
            if motif % 3 == 0:
                for col in range(c0, c1 + 1):
                    grid[r1][col] = color
                for row in range(r0, r1 + 1):
                    grid[row][c0] = color
            elif motif % 3 == 1 and c1 + 1 < width - 1:
                for row in range(r0, r1 + 1):
                    grid[row][c1 + 1] = color

        # Notches are confined to the perimeter.  The solid nonzero inner
        # rectangle remains a connected scaffold even for the smallest role.
        grid[0][0] = 0
        for _ in range(1 + (height + width) // 10):
            side = rng.randrange(4)
            length = width if side in (0, 2) else height
            start = rng.randrange(1, length - 1)
            for position in range(start, min(length - 1, start + rng.randint(1, 3))):
                if side == 0:
                    grid[0][position] = 0
                elif side == 1:
                    grid[position][-1] = 0
                elif side == 2:
                    grid[-1][position] = 0
                else:
                    grid[position][0] = 0

        first = (1, 1) if height > 3 else (0, 1)
        second = (1, 2) if height > 3 else (1, 1)
        grid[first[0]][first[1]] = beacon_a
        grid[second[0]][second[1]] = beacon_b
        # A boundary corner is the only perimeter cell without a direct
        # neighbor in the solid inner scaffold.  If both edge neighbors were
        # notched, include that corner in the notch rather than emit an island.
        for row, col in ((0, 0), (0, width - 1), (height - 1, 0), (height - 1, width - 1)):
            neighbor_row = 1 if row == 0 else height - 2
            neighbor_col = 1 if col == 0 else width - 2
            if grid[neighbor_row][col] == 0 and grid[row][neighbor_col] == 0:
                grid[row][col] = 0
        if _distinct_d4(grid):
            return grid
    raise RuntimeError("Could not construct an asymmetric payload within the bounded draw budget")


def _frame(grid, bounds, target_sides, marker_colors, distractor, rng, max_depth):
    height, width = len(grid), len(grid[0])
    r0, r1, c0, c1 = bounds
    target_colors = dict(zip(target_sides, marker_colors))

    def allowed(row, col):
        return not (r0 - 1 <= row <= r1 + 1 and c0 - 1 <= col <= c1 + 1)

    # Dotted sides are painted first.  Marker edges then remain continuous;
    # the latter marker may overlap a few cells near its neighbor's corner.
    sides = [side for side in range(4) if side not in target_colors] + list(target_sides)
    for side in sides:
        color = target_colors.get(side, distractor)
        length = width if side in (0, 2) else height
        positions = []
        for position in range(length):
            if side in target_colors or position == length // 2 or rng.random() < 0.54:
                positions.append(position)
        if side not in target_colors:
            # Preserve a visible gap away from corners and a definite dot.
            gap = 1 if length // 2 != 1 else 2
            positions = [position for position in positions if position != gap]
        for position in positions:
            depth = min(max_depth, rng.choice((1, 1, 1, 2, 2, 3)))
            for inward in range(depth):
                if side == 0:
                    row, col = inward, position
                elif side == 1:
                    row, col = position, width - 1 - inward
                elif side == 2:
                    row, col = height - 1 - inward, position
                else:
                    row, col = position, inward
                if not allowed(row, col):
                    break
                grid[row][col] = color


def _misleading_edge_samples(grid, target_sides, marker_colors, distractor):
    """Teach whole-side counting with misleading first, last and middle cells."""
    height, width = len(grid), len(grid[0])
    samples = (
        ((0, 1), (0, width // 2), (0, width - 2)),
        ((1, width - 1), (height // 2, width - 1), (height - 2, width - 1)),
        ((height - 1, 1), (height - 1, width // 2), (height - 1, width - 2)),
        ((1, 0), (height // 2, 0), (height - 2, 0)),
    )
    for points in samples:
        for row, col in points:
            grid[row][col] = distractor
    for side, color in zip(target_sides, marker_colors):
        for row, col in samples[(side + 2) % 4]:
            grid[row][col] = color
    # Replacing the guaranteed center dot must not erase the only distractor
    # on a sparse side.  Reserve a different, unsampled edge position for it.
    dots = ((0, width // 3), (height // 3, width - 1),
            (height - 1, width // 3), (height // 3, 0))
    for side in range(4):
        if side not in target_sides:
            row, col = dots[side]
            grid[row][col] = distractor


def _nonzero_components(grid):
    height, width = len(grid), len(grid[0])
    seen, result = set(), []
    for row in range(height):
        for col in range(width):
            if not grid[row][col] or (row, col) in seen:
                continue
            cells = [(row, col)]
            seen.add((row, col))
            for r, c in cells:
                for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                    if 0 <= nr < height and 0 <= nc < width and grid[nr][nc] and (nr, nc) not in seen:
                        seen.add((nr, nc))
                        cells.append((nr, nc))
            result.append(cells)
    return result


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Check the input grammar without solving or importing task workspaces."""
    if type(grid) is not list or not 1 <= len(grid) <= 30:
        return ["Grid must contain 1..30 exact-list rows"]
    if type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30:
        return ["Grid must contain 1..30 columns"]
    height, width = len(grid), len(grid[0])
    if any(type(row) is not list or len(row) != width for row in grid):
        return ["Grid rows must be exact lists of equal length"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["Colors must be exact integers in 0..9"]
    interiors = [
        cells for cells in _nonzero_components(grid)
        if all(0 < row < height - 1 and 0 < col < width - 1 for row, col in cells)
    ]
    if len(interiors) != 1:
        return ["Expected exactly one nonzero component separated from the canvas edges"]
    cells = interiors[0]
    r0, r1 = min(r for r, c in cells), max(r for r, c in cells)
    c0, c1 = min(c for r, c in cells), max(c for r, c in cells)
    cell_set = set(cells)
    if any(grid[r][c] and (r, c) not in cell_set for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)):
        return ["An exterior frame component intrudes into the central component's box"]
    edges = (
        grid[0][1:-1], [row[-1] for row in grid[1:-1]],
        grid[-1][1:-1], [row[0] for row in grid[1:-1]],
    )
    frame_colors = {value for edge in edges for value in edge if value}
    if len(frame_colors) != 3 or not all(any(edge) for edge in edges):
        return ["All four edges must carry the two markers and one distractor color"]
    markers = sorted(frame_colors & {grid[row][col] for row, col in cells})
    if len(markers) != 2:
        return ["The central frame must share exactly two reserved colors with the canvas frame"]
    inner, outer, positions = [], [], []
    for color in markers:
        points = {(row, col) for row, col in cells if grid[row][col] == color}
        sides = []
        if all(row == r0 for row, col in points):
            sides.append(0)
        if all(col == c1 for row, col in points):
            sides.append(1)
        if all(row == r1 for row, col in points):
            sides.append(2)
        if all(col == c0 for row, col in points):
            sides.append(3)
        if len(sides) != 1:
            return ["Each inner marker must occupy one unambiguous straight side bar"]
        counts = [edge.count(color) for edge in edges]
        if max(counts) < 2 or counts.count(max(counts)) != 1:
            return ["Each marker must have one uniquely dominant canvas side"]
        inner.append(sides[0])
        outer.append(counts.index(max(counts)))
        positions.append(points)
    if (inner[0] - inner[1]) % 2 != 1 or (outer[0] - outer[1]) % 2 != 1:
        return ["The inner marker pair and outer marker pair must each occupy adjacent sides"]
    top, bottom = r0 + (0 in inner), r1 - (2 in inner)
    left, right = c0 + (3 in inner), c1 - (1 in inner)
    if bottom - top + 1 < 3 or right - left + 1 < 3:
        return ["The rectangular payload must be at least 3 by 3"]
    for side, points in zip(inner, positions):
        if side in (0, 2):
            expected = {(r0 if side == 0 else r1, col) for col in range(left, right + 1)}
        else:
            expected = {(row, c1 if side == 1 else c0) for row in range(top, bottom + 1)}
        if points != expected:
            return ["Each inner bar must fill its complete side, excluding the shared corner"]
    corner = (r0 if 0 in inner else r1, c0 if 3 in inner else c1)
    if grid[corner[0]][corner[1]] != 0:
        return ["The adjacent inner bars must have an empty shared corner"]
    picture = [row[left:right + 1] for row in grid[top:bottom + 1]]
    if any(value in frame_colors for row in picture for value in row):
        return ["Frame colors are reserved outside the payload"]
    if len(_nonzero_components(picture)) != 1:
        return ["The nonzero payload must remain connected"]
    if not _distinct_d4(picture):
        return ["Payload orientation must be distinguishable under all eight D4 transforms"]
    distractor = (frame_colors - set(markers)).pop()
    if any(distractor not in edges[side] for side in range(4) if side not in outer):
        return ["The two remaining canvas sides must carry the distractor color"]
    return []


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return a fresh lawful input; sample indices are arbitrary nonnegative ints.

    Indices 0..5 are the stable teaching bank, and 100..103 are the four query
    roles.  Other indices draw new dimensions.  ``easy`` and ``hard`` override
    the size band only; ``None`` and ``medium`` keep the native role sizes.
    """
    _validate_seed(seed)
    if type(sample_index) is not int:
        raise TypeError("sample_index must be an exact integer")
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")
    if difficulty is not None and difficulty not in ("easy", "medium", "hard"):
        raise ValueError("difficulty must be None, easy, medium, or hard")
    unknown = set(overrides) - {"max_frame_depth"}
    if unknown:
        raise TypeError("Unknown generator overrides: " + ", ".join(sorted(unknown)))
    if "max_frame_depth" in overrides and type(overrides["max_frame_depth"]) is not int:
        raise TypeError("max_frame_depth must be an exact integer")

    sources, targets = _orientation(seed, sample_index)
    ctx = gen_ctx(
        seed=seed, sample_index=sample_index, version=VERSION, task_id=TASK_ID,
        difficulty=difficulty, overrides=overrides,
    )
    max_depth = ctx.draw_int_strict("max_frame_depth", 1, 3)
    height, width, ph, pw = _shape(ctx, sample_index, difficulty)
    palette = list(range(1, 10))
    ctx.draw_rng("palette").shuffle(palette)
    markers, distractor = palette[:2], palette[2]
    picture = _picture(ph, pw, palette[3:], ctx.draw_rng("payload"))
    placement = ctx.draw_rng("placement")
    r0 = placement.randint(2, height - (ph + 1) - 2)
    c0 = placement.randint(2, width - (pw + 1) - 2)
    r1, c1 = r0 + ph, c0 + pw
    picture_r0, picture_c0 = r0 + (0 in sources), c0 + (3 in sources)
    grid = [[0 for _ in range(width)] for _ in range(height)]
    _frame(grid, (r0, r1, c0, c1), targets, markers, distractor, ctx.draw_rng("frame"), max_depth)
    if sample_index == 0:
        _misleading_edge_samples(grid, targets, markers, distractor)

    for row, cells in enumerate(picture):
        grid[picture_r0 + row][picture_c0:picture_c0 + pw] = cells[:]
    for side, color in zip(sources, markers):
        if side in (0, 2):
            row = r0 if side == 0 else r1
            for col in range(picture_c0, picture_c0 + pw):
                grid[row][col] = color
        else:
            col = c1 if side == 1 else c0
            for row in range(picture_r0, picture_r0 + ph):
                grid[row][col] = color
    return grid
