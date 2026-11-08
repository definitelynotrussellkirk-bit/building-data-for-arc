"""Semantic generator for ARC task 5f8abe24cffe.

Find hollow blue (1) rectangular frames and sort them by top-left row, then
column.  Tightly crop the contents of the first three frames as A, B, and C.
Choose the first transform in identity, clockwise rotation, 180 rotation,
transpose, left-right reflection, up-down reflection order that maps A to B,
then apply that transform to C.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "5f8abe24cffe"
TASK_ID = "5f8abe24cffe"
VERSION = "3.0.0"
RULE_HASH = "634d31594fbf"
SUMMARY = "Infer the first dihedral transform mapping tightly cropped frame A to B, then apply it to cropped frame C."
INVARIANTS = [
    "zero is background and color 1 forms exactly three hollow rectangular frames",
    "frames are sorted by top-left row and then top-left column to obtain A, B, C",
    "each frame interior is cropped tightly before comparison or transformation",
    "A and B share two through four non-frame colors and C uses a nonempty subset of that palette",
    "the first matching code among identity, clockwise, 180, transpose, flip-left-right, and flip-up-down defines the analogy",
    "non-identity transforms visibly change C in generalized lessons",
]

PUBLIC_PROFILES = ("public_1", "public_2", "public_3", "public_4", "public_5")
GENERAL_PROFILES = tuple(f"code{code}" for code in range(1, 7))
SCENE_PROFILES = PUBLIC_PROFILES + GENERAL_PROFILES
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "five exact-public and six recoverable transform lessons with independent layouts",
        "valid": "public_1|public_2|public_3|public_4|public_5|code1|code2|code3|code4|code5|code6",
    }
}

_PUBLIC_ROWS = (
    "111110001111100/156010001005100/106010001766100/107710001700100/111110001111100/000000000000000/000000000000000/111110000000000/150010000000000/155010000000000/165010000000000/111110000000000/000000000000000",
    "0111110000111110/0150610000170010/0155610000165510/0100710000160510/0100010000100010/0111110000111110/0000000000000000/0111110000000000/0167010000000000/0107510000000000/0100510000000000/0111110000000000/0000000000000000",
    "111110001111100/150010001005100/156510001565100/107710001770100/111110001111100/000000000000000/000000000000000/111110000000000/157010000000000/165010000000000/155010000000000/111110000000000/000000000000000",
    "0111110000111110/0167010000160010/0107510000177010/0100510000105510/0100010000100010/0111110000111110/0000000000000000/0000000000000000/0111110000000000/0156010000000000/0106010000000000/0107710000000000/0111110000000000/0000000000000000",
    "111110001111100/157010001565100/165010001557100/155010001000100/111110001111100/000000000000000/000000000000000/111110000000000/150610000000000/155610000000000/100710000000000/111110000000000/000000000000000",
)
_PALETTE = (2, 3, 4, 5, 6, 7, 8, 9)
_ORTHOGONAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _decode(text):
    return [[int(value) for value in row] for row in text.split("/")]


_PUBLIC_INPUTS = {name: _decode(text) for name, text in zip(PUBLIC_PROFILES, _PUBLIC_ROWS)}
_PUBLIC_SIGNATURES = {tuple(map(tuple, grid)): profile for profile, grid in _PUBLIC_INPUTS.items()}


def _valid_grid(grid):
    if not isinstance(grid, (list, tuple)) or not 3 <= len(grid) <= 30:
        return ["grid must contain three through thirty rows"]
    if not isinstance(grid[0], (list, tuple)) or not 3 <= len(grid[0]) <= 30:
        return ["grid must contain three through thirty columns"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["cells must be literal integers from zero through nine"]
    return []


def _transform(grid, code):
    if code == 1:
        return [list(row) for row in grid]
    if code == 2:
        return [list(row) for row in zip(*grid[::-1])]
    if code == 3:
        return [list(reversed(row)) for row in reversed(grid)]
    if code == 4:
        return [list(row) for row in zip(*grid)]
    if code == 5:
        return [list(reversed(row)) for row in grid]
    if code == 6:
        return [list(row) for row in reversed(grid)]
    raise ValueError(f"unknown transform code: {code!r}")


def _first_transform(source, target):
    return next((code for code in range(1, 7) if _transform(source, code) == target), None)


def _crop_to_content(grid):
    cells = [(row, col) for row, values in enumerate(grid) for col, value in enumerate(values) if value != 0]
    if not cells:
        return []
    row0, row1 = min(row for row, _ in cells), max(row for row, _ in cells)
    col0, col1 = min(col for _, col in cells), max(col for _, col in cells)
    return [list(values[col0 : col1 + 1]) for values in grid[row0 : row1 + 1]]


def _color_one_components(grid):
    height, width = len(grid), len(grid[0])
    remaining = {(row, col) for row in range(height) for col in range(width) if grid[row][col] == 1}
    components = []
    while remaining:
        start = remaining.pop()
        reached = {start}
        frontier = [start]
        while frontier:
            row, col = frontier.pop()
            for delta_row, delta_col in _ORTHOGONAL:
                neighbour = row + delta_row, col + delta_col
                if neighbour in remaining:
                    remaining.remove(neighbour)
                    reached.add(neighbour)
                    frontier.append(neighbour)
        components.append(reached)
    return components


def _detect_frames(grid):
    frames = []
    for cells in _color_one_components(grid):
        row0, row1 = min(row for row, _ in cells), max(row for row, _ in cells)
        col0, col1 = min(col for _, col in cells), max(col for _, col in cells)
        height, width = row1 - row0 + 1, col1 - col0 + 1
        if height < 3 or width < 3:
            continue
        border = {
            (row, col)
            for row in range(row0, row1 + 1)
            for col in range(col0, col1 + 1)
            if row in (row0, row1) or col in (col0, col1)
        }
        if cells == border:
            frames.append((row0, col0, row1, col1))
    return sorted(frames, key=lambda frame: (frame[0], frame[1]))


def _inner_crop(grid, frame):
    row0, col0, row1, col1 = frame
    interior = [list(row[col0 + 1 : col1]) for row in grid[row0 + 1 : row1]]
    return _crop_to_content(interior)


def rule_mirror(grid):
    """Exact Python mirror of canonical frame filtering, cropping, and transform inference."""
    errors = _valid_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    frames = _detect_frames(grid)
    if len(frames) < 3:
        return [[0]]
    first, second, third = (_inner_crop(grid, frame) for frame in frames[:3])
    code = _first_transform(first, second) or 1
    return _transform(third, code)


def _layout_for(frames):
    if len(frames) != 3:
        return None
    if frames[0][0] == frames[1][0] == frames[2][0]:
        return "row"
    if frames[0][1] == frames[1][1] == frames[2][1]:
        return "column"
    if frames[0][0] == frames[1][0] and frames[2][0] > frames[1][0]:
        return "staircase"
    return None


def _connected_content(grid):
    cells = {(row, col) for row, values in enumerate(grid) for col, value in enumerate(values) if value != 0}
    if not cells:
        return False
    reached = {next(iter(cells))}
    frontier = list(reached)
    while frontier:
        row, col = frontier.pop()
        for delta_row, delta_col in _ORTHOGONAL:
            neighbour = row + delta_row, col + delta_col
            if neighbour in cells and neighbour not in reached:
                reached.add(neighbour)
                frontier.append(neighbour)
    return reached == cells


def _profile_for(grid, frames, code):
    public = _PUBLIC_SIGNATURES.get(tuple(map(tuple, grid)))
    if public:
        return public
    candidate = f"code{code}" if code and _layout_for(frames) else None
    return candidate if candidate in GENERAL_PROFILES else None


def _analysis(grid):
    errors = _valid_grid(grid)
    if errors:
        return {"errors": errors, "scene_profile": None, "facts": None, "output": None}
    frames = _detect_frames(grid)
    if len(frames) != 3:
        errors.append(f"exactly three hollow blue frames are required, got {len(frames)}")
    inner = [_inner_crop(grid, frame) for frame in frames[:3]]
    while len(inner) < 3:
        inner.append([])
    if any(not panel for panel in inner):
        errors.append("all three frame interiors must have nonempty tight crops")
    code = _first_transform(inner[0], inner[1]) if inner[0] and inner[1] else None
    if code is None:
        errors.append("no supported transform maps cropped A to cropped B")
    palettes = [
        {value for row in panel for value in row if value != 0}
        for panel in inner
    ]
    if any(1 in palette for palette in palettes):
        errors.append("blue (1) is reserved for frame borders")
    if (
        palettes[1] != palettes[0]
        or not 2 <= len(palettes[0]) <= 4
        or not palettes[2]
        or not palettes[2] <= palettes[0]
    ):
        errors.append("A and B must share two-through-four content colors and C must use a nonempty subset of that palette")
    profile = _profile_for(grid, frames, code)
    if profile not in SCENE_PROFILES:
        errors.append("grid does not match a declared transform/layout profile")
    if profile in GENERAL_PROFILES and any(not _connected_content(panel) for panel in inner):
        errors.append("each generalized tight-cropped content pattern must be orthogonally connected")
    if code not in (None, 1) and inner[2] and _transform(inner[2], code) == inner[2]:
        errors.append("non-identity transform must visibly change C")
    if frames:
        covered = set()
        for row0, col0, row1, col1 in frames:
            covered.update((row, col) for row in range(row0, row1 + 1) for col in range(col0, col1 + 1))
        if any(grid[row][col] != 0 and (row, col) not in covered for row in range(len(grid)) for col in range(len(grid[0]))):
            errors.append("nonzero cells outside the three framed panels are not allowed")
    output = _transform(inner[2], code) if code and inner[2] else None
    facts = {
        "frames": tuple(frames),
        "frame_shapes": tuple((row1 - row0 + 1, col1 - col0 + 1) for row0, col0, row1, col1 in frames),
        "inner": tuple(tuple(map(tuple, panel)) for panel in inner),
        "inner_shapes": tuple((len(panel), len(panel[0]) if panel else 0) for panel in inner),
        "palettes": tuple(tuple(sorted(palette)) for palette in palettes),
        "transform_code": code,
        "layout": _layout_for(frames),
        "scene_profile": profile,
    }
    return {"errors": errors, "scene_profile": profile, "facts": facts, "output": output}


def self_check(grid, *, difficulty=None, meta=None):
    return _analysis(grid)["errors"]


def canonical_profile_signature(grid):
    return _PUBLIC_SIGNATURES.get(tuple(map(tuple, grid)))


def observe_overrides(grid):
    analysis = _analysis(grid)
    return {"scene_profile": analysis["scene_profile"]} if not analysis["errors"] else {}


def _content_limits(difficulty):
    if difficulty == "easy":
        return (2, 3), 2
    if difficulty == "hard":
        return (3, 5), 4
    if difficulty == "medium":
        return (2, 4), 3
    return (2, 5), 3


def _random_content(rng, height, width, palette):
    minimum = max(len(palette), height + width - 1)
    maximum = min(height * width, minimum + max(2, height * width // 3))
    for _ in range(100):
        target = rng.randint(minimum, maximum)
        start = rng.randrange(height), rng.randrange(width)
        cells = {start}
        while len(cells) < target:
            candidates = []
            for row, col in cells:
                for delta_row, delta_col in _ORTHOGONAL:
                    neighbour = row + delta_row, col + delta_col
                    if 0 <= neighbour[0] < height and 0 <= neighbour[1] < width and neighbour not in cells:
                        candidates.append(neighbour)
            if not candidates:
                break
            cells.add(rng.choice(candidates))
        if len(cells) != target:
            continue
        if {row for row, _ in cells} != set(range(height)) or {col for _, col in cells} != set(range(width)):
            continue
        ordered = list(cells)
        rng.shuffle(ordered)
        values = list(palette)
        values.extend(rng.choice(palette) for _ in range(len(ordered) - len(palette)))
        rng.shuffle(values)
        grid = [[0 for _ in range(width)] for _ in range(height)]
        for (row, col), value in zip(ordered, values):
            grid[row][col] = value
        return grid
    raise AssertionError("could not construct tight connected content")


def _panel_spec(inner, rng):
    inner_height, inner_width = len(inner), len(inner[0])
    extra_height = rng.randint(0, min(1, 5 - inner_height))
    extra_width = rng.randint(0, min(1, 5 - inner_width))
    top_padding = rng.randint(0, extra_height)
    left_padding = rng.randint(0, extra_width)
    return {
        "inner": inner,
        "height": inner_height + extra_height + 2,
        "width": inner_width + extra_width + 2,
        "inner_row": top_padding + 1,
        "inner_col": left_padding + 1,
    }


def _positions(specs, layout, rng):
    margin_row, margin_col = rng.randint(0, 1), rng.randint(0, 1)
    gap1, gap2 = rng.randint(1, 3), rng.randint(1, 3)
    if layout == "row":
        positions = [
            (margin_row, margin_col),
            (margin_row, margin_col + specs[0]["width"] + gap1),
            (margin_row, margin_col + specs[0]["width"] + gap1 + specs[1]["width"] + gap2),
        ]
    elif layout == "column":
        positions = [
            (margin_row, margin_col),
            (margin_row + specs[0]["height"] + gap1, margin_col),
            (margin_row + specs[0]["height"] + gap1 + specs[1]["height"] + gap2, margin_col),
        ]
    else:
        top_height = max(specs[0]["height"], specs[1]["height"])
        second_col = margin_col + specs[0]["width"] + gap1
        width = max(second_col + specs[1]["width"], margin_col + specs[2]["width"])
        third_col = rng.randint(margin_col, width - specs[2]["width"])
        positions = [
            (margin_row, margin_col),
            (margin_row, second_col),
            (margin_row + top_height + gap2, third_col),
        ]
    return positions


def _draw_panels(specs, positions, rng):
    height = max(row + spec["height"] for spec, (row, col) in zip(specs, positions)) + rng.randint(0, 1)
    width = max(col + spec["width"] for spec, (row, col) in zip(specs, positions)) + rng.randint(0, 1)
    if height > 30 or width > 30:
        return None
    grid = [[0 for _ in range(width)] for _ in range(height)]
    for spec, (row0, col0) in zip(specs, positions):
        row1, col1 = row0 + spec["height"] - 1, col0 + spec["width"] - 1
        for col in range(col0, col1 + 1):
            grid[row0][col] = grid[row1][col] = 1
        for row in range(row0, row1 + 1):
            grid[row][col0] = grid[row][col1] = 1
        for row, values in enumerate(spec["inner"]):
            for col, value in enumerate(values):
                grid[row0 + spec["inner_row"] + row][col0 + spec["inner_col"] + col] = value
    return grid


def _general_scene(profile, difficulty, rng):
    code = int(profile[4:])
    (low, high), palette_count = _content_limits(difficulty)
    for _ in range(500):
        palette = tuple(rng.sample(_PALETTE, palette_count))
        a_height, a_width = rng.randint(low, high), rng.randint(low, high)
        source = _random_content(rng, a_height, a_width, palette)
        target = _transform(source, code)
        if _first_transform(source, target) != code:
            continue
        c_height, c_width = rng.randint(low, high), rng.randint(low, high)
        query = _random_content(rng, c_height, c_width, palette)
        if code != 1 and _transform(query, code) == query:
            continue
        specs = [_panel_spec(panel, rng) for panel in (source, target, query)]
        layout = rng.choice(("staircase", "row", "column"))
        grid = _draw_panels(specs, _positions(specs, layout, rng), rng)
        if grid is None:
            continue
        analysis = _analysis(grid)
        if not analysis["errors"] and analysis["scene_profile"] == profile:
            return grid
    raise AssertionError(f"could not construct scene profile {profile}")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = sorted(set(overrides) - {"scene_profile"})
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = ctx.draw_choice("scene_profile", PUBLIC_PROFILES + GENERAL_PROFILES * 8)
    if profile not in SCENE_PROFILES:
        raise ValueError(f"unknown scene_profile: {profile!r}")
    if profile in PUBLIC_PROFILES:
        return [row[:] for row in _PUBLIC_INPUTS[profile]]
    return _general_scene(profile, difficulty, ctx.draw_rng("scene"))
