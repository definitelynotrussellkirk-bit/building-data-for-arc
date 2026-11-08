"""Two ordered transforms with an episode-fixed source for transform two.

``header`` is the byte-exact canonical rule. ``post_first_marker`` keeps the
first header transform but derives the second transform from the unique color-9
marker's corner *after* that first transform.  The derived transform moves the
marker to the top-left corner.  Inputs are matched across settings.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
from pathlib import Path
import random

TASK_ID = "dcc5f8961845"
VERSION = "1.0.0"
HERE = Path(__file__).resolve().parent
CANONICAL = (HERE / "canonical.rkt").read_text(encoding="utf-8")
POST_FIRST_MARKER = (HERE / "post_first_marker.rkt").read_text(encoding="utf-8")
SETTINGS = (
    {"second_source": "header"},
    {"second_source": "post_first_marker"},
)
HEADER = SETTINGS[0]
MARKER = SETTINGS[1]
_ALLOWED = ("header", "post_first_marker")
_PALETTE = tuple(range(1, 9))
_CORNERS = ("tl", "tr", "bl", "br")


def _setting(settings: dict) -> str:
    if (type(settings) is not dict or set(settings) != {"second_source"}
            or type(settings["second_source"]) is not str
            or settings["second_source"] not in _ALLOWED):
        raise ValueError(
            "settings must be exactly second_source=header|post_first_marker"
        )
    return settings["second_source"]


def program(settings: dict) -> str:
    return CANONICAL if _setting(settings) == "header" else POST_FIRST_MARKER


def _grid(value: list[list[int]]) -> list[list[int]]:
    if (type(value) is not list or not 3 <= len(value) <= 30
            or type(value[0]) is not list or not 2 <= len(value[0]) <= 30):
        raise ValueError("expected a rectangular 3..30 by 2..30 ARC grid")
    width = len(value[0])
    if any(type(row) is not list or len(row) != width
           or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
           for row in value):
        raise ValueError("grid cells must be exact integer colors 0..9")
    return deepcopy(value)


def analyze(value: list[list[int]]) -> dict:
    grid = _grid(value)
    h, w = len(grid), len(grid[0])
    cmd1, cmd2 = grid[0][0], grid[0][1]
    if not (0 <= cmd1 <= 5 and 0 <= cmd2 <= 5):
        raise ValueError("the first two cells must be transform commands 0..5")
    if any(grid[0][c] != 0 for c in range(2, w)):
        raise ValueError("only the first two header cells may be nonzero")
    if any(grid[1]):
        raise ValueError("row one must be a blank separator")
    occupied = [(r, c) for r in range(2, h) for c in range(w) if grid[r][c] != 0]
    if not occupied:
        raise ValueError("missing motif")
    r0, r1 = min(r for r, _ in occupied), max(r for r, _ in occupied)
    c0, c1 = min(c for _, c in occupied), max(c for _, c in occupied)
    motif = [row[c0:c1 + 1] for row in grid[r0:r1 + 1]]
    if len(motif) < 2 or len(motif[0]) < 2:
        raise ValueError("motif must be at least 2 by 2")
    marker = [(r, c) for r, row in enumerate(motif)
              for c, cell in enumerate(row) if cell == 9]
    if len(marker) != 1:
        raise ValueError("motif must contain exactly one color-9 marker")
    corners = {(0, 0), (0, len(motif[0]) - 1),
               (len(motif) - 1, 0), (len(motif) - 1, len(motif[0]) - 1)}
    if marker[0] not in corners:
        raise ValueError("the color-9 marker must occupy a motif corner")
    colors = {cell for row in motif for cell in row if cell not in (0, 9)}
    if len(colors) < 2:
        raise ValueError("motif must contain at least two non-marker colors")
    return {
        "grid": grid,
        "height": h,
        "width": w,
        "cmd1": cmd1,
        "cmd2": cmd2,
        "bbox": [r0, c0, r1, c1],
        "motif": motif,
        "marker": list(marker[0]),
        "colors": sorted(colors | {9}),
    }


def _transform(grid: list[list[int]], command: int) -> list[list[int]]:
    if type(command) is not int or not 0 <= command <= 5:
        raise ValueError("transform command must be an integer in 0..5")
    grid = [row[:] for row in grid]
    if command == 0:
        return grid
    if command == 1:
        return [list(row) for row in zip(*grid[::-1])]
    if command == 2:
        return [row[::-1] for row in grid[::-1]]
    if command == 3:
        return [list(row) for row in zip(*grid)]
    if command == 4:
        return [row[::-1] for row in grid]
    return grid[::-1]


def _marker_position(grid: list[list[int]]) -> tuple[int, int]:
    positions = [(r, c) for r, row in enumerate(grid)
                 for c, value in enumerate(row) if value == 9]
    if len(positions) != 1:
        raise ValueError("expected exactly one marker after transformation")
    return positions[0]


def _corner_name(grid: list[list[int]]) -> str:
    r, c = _marker_position(grid)
    h, w = len(grid), len(grid[0])
    mapping = {
        (0, 0): "tl",
        (0, w - 1): "tr",
        (h - 1, 0): "bl",
        (h - 1, w - 1): "br",
    }
    try:
        return mapping[(r, c)]
    except KeyError as error:
        raise ValueError("marker left the motif corners") from error


def _corner_command(grid: list[list[int]]) -> int:
    return {"tl": 0, "tr": 4, "bl": 5, "br": 2}[_corner_name(grid)]


def solve(grid: list[list[int]], settings: dict) -> list[list[int]]:
    mode = _setting(settings)
    scene = analyze(grid)
    first = _transform(scene["motif"], scene["cmd1"])
    second = scene["cmd2"] if mode == "header" else _corner_command(first)
    return _transform(first, second)


def _recolor(template: tuple[tuple[int, ...], ...], rng: random.Random) -> list[list[int]]:
    keys = sorted({value for row in template for value in row if value not in (0, 9)})
    chosen = rng.sample(_PALETTE, len(keys))
    mapping = dict(zip(keys, chosen))
    return [[mapping.get(value, value) for value in row] for row in template]


_TEACHING = (
    {
        "template": ((9, 1, 0, 2), (3, 1, 2, 2), (3, 0, 1, 2)),
        "shape": (9, 12),
        "commands": (1, 3),
    },
    {
        "template": ((1, 0, 2), (1, 3, 2), (0, 3, 1), (2, 1, 9)),
        "shape": (10, 13),
        "commands": (2, 1),
    },
)


def _paint_scene(h: int, w: int, motif: list[list[int]], top: int, left: int,
                 cmd1: int, cmd2: int) -> list[list[int]]:
    if not (2 <= top <= h - len(motif) and 0 <= left <= w - len(motif[0])):
        raise ValueError("motif placement is outside the canvas")
    grid = [[0] * w for _ in range(h)]
    grid[0][0], grid[0][1] = cmd1, cmd2
    for dr, row in enumerate(motif):
        for dc, value in enumerate(row):
            grid[top + dr][left + dc] = value
    analyze(grid)
    return grid


def _teaching_inputs(seed: int) -> list[list[list[int]]]:
    rng = random.Random(seed * 104729 + 0xDCC5)
    grids = []
    for index, spec in enumerate(_TEACHING):
        motif = _recolor(spec["template"], rng)
        h, w = spec["shape"]
        top = 2 + rng.randrange(h - len(motif) - 1)
        left = rng.randrange(w - len(motif[0]) + 1)
        cmd1, cmd2 = spec["commands"]
        grids.append(_paint_scene(h, w, motif, top, left, cmd1, cmd2))
    return grids


def _corner_cell(corner: str, h: int, w: int) -> tuple[int, int]:
    return {
        "tl": (0, 0), "tr": (0, w - 1),
        "bl": (h - 1, 0), "br": (h - 1, w - 1),
    }[corner]


def _random_motif(rng: random.Random, h: int, w: int, corner: str,
                  density: float) -> list[list[int]]:
    palette = rng.sample(_PALETTE, 3)
    motif = []
    for r in range(h):
        row = []
        for c in range(w):
            if rng.random() <= density:
                row.append(palette[(r * 7 + c * 11 + r * c + rng.randrange(3)) % 3])
            else:
                row.append(0)
        motif.append(row)
    corners = ((0, 0), (0, w - 1), (h - 1, 0), (h - 1, w - 1))
    for index, (r, c) in enumerate(corners):
        motif[r][c] = palette[index % len(palette)]
    mr, mc = _corner_cell(corner, h, w)
    motif[mr][mc] = 9
    # Constructively expose all palette colors even at the minimum dimensions.
    available = [(r, c) for r in range(h) for c in range(w)
                 if (r, c) != (mr, mc)]
    for color, (r, c) in zip(palette, available):
        motif[r][c] = color
    motif[mr][mc] = 9
    return motif


_DEMO_SPECS = (
    (11, 14, 4, 6, .56),
    (14, 17, 5, 8, .48),
    (18, 21, 7, 9, .61),
    (23, 26, 9, 11, .52),
)
_QUERY_SPECS = (
    (8, 9, 2, 3, .67),
    (13, 16, 5, 7, .46),
    (21, 24, 9, 12, .59),
    (30, 30, 28, 30, .58),
)


def _random_scene(seed: int, index: int, *, query: bool) -> list[list[int]]:
    stream = (seed + 1) * 1_000_003 + index * 10_007 + (0x51A7 if query else 0xD3A0)
    rng = random.Random(stream)
    h, w, mh, mw, density = (_QUERY_SPECS if query else _DEMO_SPECS)[index]
    corner = _CORNERS[(seed + index * 3 + (1 if query else 0)) % 4]
    motif = _random_motif(rng, mh, mw, corner, density)
    cmd1 = (seed + index * 2 + (1 if query else 3)) % 6
    cmd2 = (seed * 3 + index * 5 + (4 if query else 2)) % 6
    if query and index == 3:
        top, left = 2, 0
    else:
        top = 2 + rng.randrange(h - mh - 1 if h - mh - 1 > 0 else 1)
        left = rng.randrange(w - mw + 1)
    return _paint_scene(h, w, motif, top, left, cmd1, cmd2)


def _all_inputs(seed: int) -> tuple[list[list[list[int]]], list[list[list[int]]]]:
    demos = _teaching_inputs(seed)
    demos.extend(_random_scene(seed, index, query=False) for index in range(4))
    queries = [_random_scene(seed, index, query=True) for index in range(4)]
    return demos, queries


def _other(settings: dict) -> dict:
    return MARKER if _setting(settings) == "header" else HEADER


def rival_outputs(grid: list[list[int]], settings: dict) -> dict[str, list[list[int]]]:
    """Finite plausible shortcuts used for lesson authoring, not uniqueness proof."""
    scene = analyze(grid)
    motif, cmd1, cmd2 = scene["motif"], scene["cmd1"], scene["cmd2"]
    first = _transform(motif, cmd1)
    original_command = _corner_command(motif)
    marker_command = _corner_command(first)
    header_pass = _transform(first, cmd2)
    results = {
        "other_setting": solve(grid, _other(settings)),
        "crop_only": deepcopy(motif),
        "first_only": first,
        "second_only": _transform(motif, cmd2),
        "reverse_header_order": _transform(_transform(motif, cmd2), cmd1),
        "original_corner_after_first": _transform(first, original_command),
        "normalize_before_first": _transform(_transform(motif, original_command), cmd1),
        "marker_then_header": _transform(_transform(first, marker_command), cmd2),
        "header_then_marker": _transform(header_pass, _corner_command(header_pass)),
    }
    for command in range(6):
        results[f"fixed_after_first_{command}"] = _transform(first, command)
    return results


def lesson_report(episode: dict, settings: dict) -> dict:
    _setting(settings)
    train = episode.get("train")
    test = episode.get("test")
    if type(train) is not list or type(test) is not list:
        raise ValueError("episode must contain train and test lists")
    survivors = None
    for pair in train:
        expected = pair["output"]
        fits = {name for name, value in rival_outputs(pair["input"], settings).items()
                if value == expected}
        survivors = fits if survivors is None else survivors & fits
    survivors = sorted(survivors or ())
    disagreements = []
    for name in survivors:
        if any(rival_outputs(pair["input"], settings).get(name) != pair["output"]
               for pair in test):
            disagreements.append(name)
    return {
        "finite_scope": sorted({name for pair in train + test
                                for name in rival_outputs(pair["input"], settings)}),
        "demonstration_survivors": survivors,
        "surviving_query_disagreements": disagreements,
    }


def generate(seed: int, settings: dict, demos: int, queries: int) -> dict:
    _setting(settings)
    if type(seed) is not int or not 0 <= seed < 2**63:
        raise ValueError("seed must be an exact integer in 0..2**63-1")
    if type(demos) is not int or not 2 <= demos <= 6:
        raise ValueError("demos must be an exact integer in 2..6")
    if type(queries) is not int or not 1 <= queries <= 4:
        raise ValueError("queries must be an exact integer in 1..4")
    demo_inputs, query_inputs = _all_inputs(seed)
    train = [{"input": grid, "output": solve(grid, settings)}
             for grid in demo_inputs[:demos]]
    test = [{"input": grid, "output": solve(grid, settings)}
            for grid in query_inputs[:queries]]
    episode = {"train": train, "test": test, "program_solution": program(settings)}
    serialized = [repr(pair["input"]) for pair in train + test]
    if len(serialized) != len(set(serialized)):
        raise RuntimeError("constructive input schedule produced a duplicate")
    report = lesson_report(episode, settings)
    if report["demonstration_survivors"]:
        raise RuntimeError(f"teaching construction left rivals: {report}")
    return deepcopy(episode)


def _common_racket(body: str) -> str:
    return f"""(rule!
  (let ((dummy 0))
    (define (apply-transform grid cmd)
      (cond [(= cmd 0) grid]
            [(= cmd 1) (rotate-cw grid)]
            [(= cmd 2) (rotate-180 grid)]
            [(= cmd 3) (transpose grid)]
            [(= cmd 4) (flip-lr grid)]
            [else (flip-ud grid)]))
    (define (marker-command grid)
      (let* ((h (rows grid))
             (w (cols grid))
             (marker (first (for*/list ([r (in-range h)] [c (in-range w)]
                                        #:when (= (at grid r c) 9)) (list r c))))
             (r (first marker)) (c (second marker)))
        (cond [(and (= r 0) (= c 0)) 0]
              [(and (= r 0) (= c (- w 1))) 4]
              [(and (= r (- h 1)) (= c 0)) 5]
              [else 2])))
    (let* ((cmd1 (at g 0 0))
           (cmd2 (at g 0 1))
           (clean (set-cell (set-cell g 0 0 0) 0 1 0))
           (obj (crop-to-content clean))
           (first-pass (apply-transform obj cmd1)))
      {body})))"""


def rival_programs(settings: dict) -> dict[str, str]:
    """Total Racket counterparts for the finite lesson audit."""
    _setting(settings)
    programs = {
        "crop_only": _common_racket("obj"),
        "first_only": _common_racket("first-pass"),
        "second_only": _common_racket("(apply-transform obj cmd2)"),
        "reverse_header_order": _common_racket(
            "(apply-transform (apply-transform obj cmd2) cmd1)"
        ),
        "original_corner_after_first": _common_racket(
            "(apply-transform first-pass (marker-command obj))"
        ),
        "normalize_before_first": _common_racket(
            "(apply-transform (apply-transform obj (marker-command obj)) cmd1)"
        ),
        "marker_then_header": _common_racket(
            "(apply-transform (apply-transform first-pass (marker-command first-pass)) cmd2)"
        ),
        "header_then_marker": _common_racket(
            "(let ((header-pass (apply-transform first-pass cmd2))) "
            "(apply-transform header-pass (marker-command header-pass)))"
        ),
    }
    for command in range(6):
        programs[f"fixed_after_first_{command}"] = _common_racket(
            f"(apply-transform first-pass {command})"
        )
    return programs


def sequential_witness() -> dict:
    grid = _teaching_inputs(0)[0]
    scene = analyze(grid)
    first = _transform(scene["motif"], scene["cmd1"])
    correct_command = _corner_command(first)
    skip_command = _corner_command(scene["motif"])
    correct = _transform(first, correct_command)
    skip = _transform(first, skip_command)
    return {
        "schema": "dcc5f8961845-sequential-witness-v1",
        "task_id": TASK_ID,
        "setting": deepcopy(MARKER),
        "program": POST_FIRST_MARKER,
        "program_sha256": hashlib.sha256(POST_FIRST_MARKER.encode()).hexdigest(),
        "step_a": "apply the first header transform to the cropped motif",
        "step_a_command": scene["cmd1"],
        "intermediate": {
            "grid": first,
            "marker_corner": _corner_name(first),
            "derived_step_b_command": correct_command,
        },
        "step_b": "choose the transform that moves the post-first marker corner to top-left",
        "why_b_depends_on_a": (
            "the first transform changes the marker corner, and that post-transform corner "
            "selects the second command"
        ),
        "input": grid,
        "correct_output": correct,
        "skip_a_intermediate": {
            "grid": scene["motif"],
            "marker_corner": _corner_name(scene["motif"]),
            "derived_step_b_command": skip_command,
        },
        "skip_a_output": skip,
        "outputs_differ": correct != skip,
    }
