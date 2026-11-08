"""Native nearest/farthest parametric family for ARC task 9971f3a5882c.

Input sampling is independent of the private setting.  Python outputs are
deterministic claims; native qualification independently executes the exact
Racket programs over every demonstration and query.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random

from reviewer_support import find_root, load_selected_generator, public_challenge_bytes


TASK_ID = "9971f3a5882c"
VERSION = "native-2"
SETTINGS = ("nearest", "farthest")
HERE = Path(__file__).resolve().parent
CANONICAL = (HERE / "nearest.rkt").read_text(encoding="utf-8")

SUBSTITUTIONS = (
    ("(max-of fst above)", "(min-of fst above)"),
    ("(min-of fst below)", "(max-of fst below)"),
    ("(max-of snd lefts)", "(min-of snd lefts)"),
    ("(min-of snd rights)", "(max-of snd rights)"),
)


def _replace_once(text: str, before: str, after: str, label: str) -> str:
    if text.count(before) != 1:
        raise ValueError(f"pinned canonical source no longer has exactly one {label}")
    return text.replace(before, after, 1)


def _farthest_program() -> str:
    result = CANONICAL
    for before, after in SUBSTITUTIONS:
        result = _replace_once(result, before, after, before)
    return result


FARTHEST = _farthest_program()
PROGRAMS = {"nearest": CANONICAL, "farthest": FARTHEST}


def _setting(settings) -> str:
    if type(settings) is not dict or set(settings) != {"marker_selection"}:
        raise ValueError("settings must contain exactly marker_selection")
    value = settings["marker_selection"]
    if type(value) is not str or value not in SETTINGS:
        raise ValueError("marker_selection must be nearest or farthest")
    return value


def program(settings) -> str:
    """Return the exact Racket program for one declared setting."""
    return PROGRAMS[_setting(settings)]


_GENERATOR = None


def _generator():
    global _GENERATOR
    if _GENERATOR is None:
        _GENERATOR, _, _ = load_selected_generator(TASK_ID, root=find_root(__file__))
    return _GENERATOR


def _classify_markers(bbox, marks):
    r0, r1, c0, c1 = bbox
    return {
        "top": [(r, c) for r, c in marks if r < r0 and c0 <= c <= c1],
        "bottom": [(r, c) for r, c in marks if r > r1 and c0 <= c <= c1],
        "left": [(r, c) for r, c in marks if c < c0],
        "right": [(r, c) for r, c in marks if c > c1],
    }


def _correct_bbox(grid):
    cells = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 3
    ]
    if not cells:
        raise ValueError("input contains no color-3 lattice")
    return (
        min(r for r, _ in cells),
        max(r for r, _ in cells),
        min(c for _, c in cells),
        max(c for _, c in cells),
    )


def native_analysis(grid):
    """Return the input-dependent A-stage intermediate in JSON-friendly form."""
    analysis = _generator()._analyze_lattice(deepcopy(grid))
    markers = _classify_markers(analysis["bbox"], analysis["marks"])
    return {
        "bbox": tuple(analysis["bbox"]),
        "markers_by_side": {key: tuple(value) for key, value in markers.items()},
        "full_rows": tuple(analysis["full_rows"]),
        "full_cols": tuple(analysis["full_cols"]),
    }


def _solve_from_bbox(
    grid,
    selection,
    bbox,
    *,
    ignore_sides=(),
    unit_expansion=False,
    boundaries_only=False,
):
    if selection not in SETTINGS:
        raise ValueError("selection must be nearest or farthest")
    height, width = len(grid), len(grid[0])
    r0, r1, c0, c1 = bbox
    marks = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 6
    ]
    markers = _classify_markers(bbox, marks)
    for side in ignore_sides:
        markers[side] = []

    if markers["top"]:
        nr0 = r0 - 1 if unit_expansion else (
            max(r for r, _ in markers["top"]) + 1
            if selection == "nearest"
            else min(r for r, _ in markers["top"]) + 1
        )
    else:
        nr0 = r0
    if markers["bottom"]:
        nr1 = r1 + 1 if unit_expansion else (
            min(r for r, _ in markers["bottom"]) - 1
            if selection == "nearest"
            else max(r for r, _ in markers["bottom"]) - 1
        )
    else:
        nr1 = r1
    if markers["left"]:
        nc0 = c0 - 1 if unit_expansion else (
            max(c for _, c in markers["left"]) + 1
            if selection == "nearest"
            else min(c for _, c in markers["left"]) + 1
        )
    else:
        nc0 = c0
    if markers["right"]:
        nc1 = c1 + 1 if unit_expansion else (
            min(c for _, c in markers["right"]) - 1
            if selection == "nearest"
            else max(c for _, c in markers["right"]) - 1
        )
    else:
        nc1 = c1

    full_rows = [
        row
        for row in range(r0, r1 + 1)
        if all(grid[row][column] == 3 for column in range(c0, c1 + 1))
    ]
    full_cols = [
        column
        for column in range(c0, c1 + 1)
        if all(grid[row][column] == 3 for row in range(r0, r1 + 1))
    ]
    if boundaries_only:
        full_rows = [r0, r1]
        full_cols = [c0, c1]

    result = [[0] * width for _ in range(height)]
    for row in full_rows:
        mapped = nr0 if row == r0 else nr1 if row == r1 else row
        for column in range(nc0, nc1 + 1):
            result[mapped][column] = 3
    for column in full_cols:
        mapped = nc0 if column == c0 else nc1 if column == c1 else column
        for row in range(nr0, nr1 + 1):
            result[row][mapped] = 3
    for row, column in marks:
        result[row][column] = 6
    return result


def native_transform(grid, settings):
    """Independent deterministic label claim used by the native adapter."""
    selection = _setting(settings)
    errors = _generator().self_check(grid)
    if errors:
        raise ValueError(f"input is outside the selected sparse-lattice grammar: {errors}")
    return _solve_from_bbox(grid, selection, _correct_bbox(grid))


PLAUSIBLE_RIVALS = (
    "ignore_top_nearest",
    "ignore_top_farthest",
    "unit_expansion",
    "boundaries_only_nearest",
    "boundaries_only_farthest",
    "identity",
)


def rival_transform(grid, name):
    bbox = _correct_bbox(grid)
    if name == "ignore_top_nearest":
        return _solve_from_bbox(grid, "nearest", bbox, ignore_sides=("top",))
    if name == "ignore_top_farthest":
        return _solve_from_bbox(grid, "farthest", bbox, ignore_sides=("top",))
    if name == "unit_expansion":
        return _solve_from_bbox(grid, "nearest", bbox, unit_expansion=True)
    if name == "boundaries_only_nearest":
        return _solve_from_bbox(grid, "nearest", bbox, boundaries_only=True)
    if name == "boundaries_only_farthest":
        return _solve_from_bbox(grid, "farthest", bbox, boundaries_only=True)
    if name == "identity":
        return deepcopy(grid)
    raise ValueError(f"unknown plausible rival: {name}")


# height, width, bbox-height, bbox-width, top/bottom/left/right padding,
# full-row offsets, full-column offsets, marker counts (T,B,L,R), near/far/single.
DEMO_PROFILES = (
    (15, 19, 5, 7, 5, 5, 5, 7, (0, 2, 4), (0, 3, 6), (2, 1, 1, 2), 2, 4, 2),
    (19, 15, 7, 5, 6, 6, 5, 5, (0, 2, 4, 6), (0, 2, 4), (1, 2, 2, 1), 1, 4, 2),
    (21, 23, 7, 9, 7, 7, 7, 7, (0, 3, 6), (0, 2, 5, 8), (2, 2, 2, 2), 2, 5, 2),
    (23, 21, 9, 7, 7, 7, 7, 7, (0, 2, 5, 8), (0, 3, 6), (2, 1, 2, 1), 3, 5, 2),
    (25, 27, 11, 13, 7, 7, 7, 7, (0, 3, 7, 10), (0, 4, 8, 12), (1, 2, 1, 2), 2, 5, 3),
    (27, 25, 13, 11, 7, 7, 7, 7, (0, 4, 8, 12), (0, 3, 7, 10), (2, 2, 2, 2), 1, 6, 2),
)

QUERY_PROFILES = (
    (20, 26, 8, 12, 6, 6, 7, 7, (0, 2, 5, 7), (0, 3, 7, 11), (2, 2, 1, 1), 1, 5, 3),
    (26, 20, 12, 8, 7, 7, 6, 6, (0, 3, 7, 11), (0, 2, 5, 7), (1, 1, 2, 2), 2, 5, 2),
    (28, 29, 14, 15, 7, 7, 7, 7, (0, 3, 7, 10, 13), (0, 4, 8, 11, 14), (2, 2, 2, 2), 3, 6, 3),
    (30, 30, 14, 16, 7, 9, 7, 7, (0, 3, 7, 10, 13), (0, 4, 8, 12, 15), (2, 2, 2, 2), 4, 6, 3),
)


def _rng(seed, label):
    raw = f"{TASK_ID}:{VERSION}:{seed}:{label}".encode("utf-8")
    return random.Random(int.from_bytes(hashlib.sha256(raw).digest(), "big"))


def _sample_input(seed, label, profile):
    (
        height,
        width,
        lattice_h,
        lattice_w,
        pad_top,
        pad_bottom,
        pad_left,
        pad_right,
        row_offsets,
        col_offsets,
        counts,
        near_expansion,
        far_expansion,
        single_expansion,
    ) = profile
    if pad_top + lattice_h + pad_bottom != height:
        raise RuntimeError("invalid vertical profile geometry")
    if pad_left + lattice_w + pad_right != width:
        raise RuntimeError("invalid horizontal profile geometry")

    r0, c0 = pad_top, pad_left
    r1, c1 = r0 + lattice_h - 1, c0 + lattice_w - 1
    grid = [[0] * width for _ in range(height)]
    full_rows = {r0 + offset for offset in row_offsets}
    full_cols = {c0 + offset for offset in col_offsets}
    for row in range(r0, r1 + 1):
        for column in range(c0, c1 + 1):
            if row in full_rows or column in full_cols:
                grid[row][column] = 3

    rng = _rng(seed, label)
    marker_counts = dict(zip(("top", "bottom", "left", "right"), counts))
    marks = []
    for side in ("top", "bottom", "left", "right"):
        count = marker_counts[side]
        if count == 0:
            continue
        expansions = [single_expansion] if count == 1 else [near_expansion, far_expansion]
        if side in ("top", "bottom"):
            choices = list(range(c0, c1 + 1))
            coordinates = [c1, rng.choice(choices[:-1])] if count == 2 else [rng.choice(choices)]
            for expansion, column in zip(expansions, coordinates):
                row = r0 - expansion - 1 if side == "top" else r1 + expansion + 1
                marks.append((row, column))
        else:
            choices = list(range(r0, r1 + 1))
            coordinates = [r1, rng.choice(choices[:-1])] if count == 2 else [rng.choice(choices)]
            for expansion, row in zip(expansions, coordinates):
                column = c0 - expansion - 1 if side == "left" else c1 + expansion + 1
                marks.append((row, column))

    if len(marks) != len(set(marks)):
        raise RuntimeError("constructed duplicate markers")
    if any(not (0 <= row < height and 0 <= column < width) for row, column in marks):
        raise RuntimeError("profile marker lies outside canvas")
    for row, column in marks:
        grid[row][column] = 6

    errors = _generator().self_check(grid)
    if errors:
        raise RuntimeError(f"constructed invalid native input: {errors}")
    bbox = (r0, r1, c0, c1)
    if _solve_from_bbox(grid, "nearest", bbox) == _solve_from_bbox(grid, "farthest", bbox):
        raise RuntimeError("constructed input failed to distinguish settings")
    return grid


def teaching_certificate(episode):
    """Fit only demonstrations; query labels are deliberately ignored."""
    train = episode.get("train") if isinstance(episode, dict) else None
    if not isinstance(train, list) or not train:
        raise ValueError("nonempty train demonstrations required")

    setting_survivors = []
    for setting in SETTINGS:
        candidate = {"marker_selection": setting}
        if all(native_transform(pair["input"], candidate) == pair["output"] for pair in train):
            setting_survivors.append(setting)

    rival_survivors = []
    for rival in PLAUSIBLE_RIVALS:
        if all(rival_transform(pair["input"], rival) == pair["output"] for pair in train):
            rival_survivors.append(rival)

    return {
        "setting_survivors": setting_survivors,
        "plausible_rival_survivors": rival_survivors,
        "demonstrations_checked": len(train),
    }


def visible_turn(episode, query_index):
    if type(query_index) is not int or not 0 <= query_index < len(episode["test"]):
        raise ValueError("query_index must select one test pair")
    return public_challenge_bytes(
        {"train": episode["train"], "test": [episode["test"][query_index]]}
    )


def generate(seed, settings, demos, queries):
    """Generate matched-input episodes with independent demo/query streams."""
    if type(seed) is not int or not 0 <= seed <= 2**63 - 1:
        raise ValueError("seed must be an exact integer in 0..2**63-1")
    selection = _setting(settings)
    if type(demos) is not int or not 2 <= demos <= 6:
        raise ValueError("demos must be an exact integer in 2..6")
    if type(queries) is not int or not 1 <= queries <= 4:
        raise ValueError("queries must be an exact integer in 1..4")

    train = []
    for index in range(demos):
        grid = _sample_input(seed, f"demo:{index}", DEMO_PROFILES[index])
        train.append({"input": grid, "output": native_transform(grid, settings)})
    test = []
    for index in range(queries):
        grid = _sample_input(seed, f"query:{index}", QUERY_PROFILES[index])
        test.append({"input": grid, "output": native_transform(grid, settings)})

    episode = {"train": train, "test": test, "program_solution": program(settings)}
    certificate = teaching_certificate(episode)
    if certificate["setting_survivors"] != [selection] or certificate["plausible_rival_survivors"]:
        raise RuntimeError(
            "demonstrations failed finite teaching certificate: "
            + json.dumps(certificate, sort_keys=True)
        )

    inputs = [
        json.dumps(pair["input"], separators=(",", ":"))
        for split in (train, test)
        for pair in split
    ]
    if len(inputs) != len(set(inputs)):
        raise RuntimeError("episode inputs must be distinct")
    return episode


_NR0_NEAREST = "(nr0 (if (empty? above) r0 (+ 1 (max-of fst above))))"
_NR0_FARTHEST = "(nr0 (if (empty? above) r0 (+ 1 (min-of fst above))))"
_NR1_NEAREST = "(nr1 (if (empty? below) r1 (- (min-of fst below) 1)))"
_NC0_NEAREST = "(nc0 (if (empty? lefts) c0 (+ 1 (max-of snd lefts))))"
_NC1_NEAREST = "(nc1 (if (empty? rights) c1 (- (min-of snd rights) 1)))"
_FULL_ROWS_BLOCK = """(full-rows (filter (lambda (r)
                                       (all? (lambda (c) (= (at g r c) 3))
                                             (range c0 (+ c1 1))))
                                     (range r0 (+ r1 1))))"""
_FULL_COLS_BLOCK = """(full-cols (filter (lambda (c)
                                       (all? (lambda (r) (= (at g r c) 3))
                                             (range r0 (+ r1 1))))
                                     (range c0 (+ c1 1))))"""


def plausible_programs():
    """Return executable finite wrong rules for the protected self-audit."""
    ignore_near = _replace_once(
        CANONICAL, _NR0_NEAREST, "(nr0 r0)", "nearest top boundary"
    )
    ignore_far = _replace_once(
        FARTHEST, _NR0_FARTHEST, "(nr0 r0)", "farthest top boundary"
    )
    unit = CANONICAL
    for before, after, label in (
        (_NR0_NEAREST, "(nr0 (if (empty? above) r0 (- r0 1)))", "unit top"),
        (_NR1_NEAREST, "(nr1 (if (empty? below) r1 (+ r1 1)))", "unit bottom"),
        (_NC0_NEAREST, "(nc0 (if (empty? lefts) c0 (- c0 1)))", "unit left"),
        (_NC1_NEAREST, "(nc1 (if (empty? rights) c1 (+ c1 1)))", "unit right"),
    ):
        unit = _replace_once(unit, before, after, label)

    boundaries_near = _replace_once(
        _replace_once(
            CANONICAL,
            _FULL_ROWS_BLOCK,
            "(full-rows (list r0 r1))",
            "full rows",
        ),
        _FULL_COLS_BLOCK,
        "(full-cols (list c0 c1))",
        "full columns",
    )
    boundaries_far = _replace_once(
        _replace_once(
            FARTHEST,
            _FULL_ROWS_BLOCK,
            "(full-rows (list r0 r1))",
            "full rows",
        ),
        _FULL_COLS_BLOCK,
        "(full-cols (list c0 c1))",
        "full columns",
    )
    return {
        "ignore_top_nearest": ignore_near,
        "ignore_top_farthest": ignore_far,
        "unit_expansion": unit,
        "boundaries_only_nearest": boundaries_near,
        "boundaries_only_farthest": boundaries_far,
        "identity": "(rule! (lambda (g) g))",
    }


def wrong_intermediate_program():
    """Corrupt A's right bbox boundary before B classifies side markers."""
    return _replace_once(
        CANONICAL,
        "(c1 (max-of snd cells))",
        "(c1 (- (max-of snd cells) 1))",
        "right bbox intermediate",
    )


def dependency_witness():
    """Return a qualification-pair-compatible wrong-intermediate witness draft."""
    settings = {"marker_selection": "nearest"}
    episode = generate(0, settings, 3, 4)
    pair = episode["test"][0]
    analysis = native_analysis(pair["input"])
    r0, r1, c0, c1 = analysis["bbox"]
    wrong = _solve_from_bbox(pair["input"], "nearest", (r0, r1, c0, c1 - 1))
    if wrong == pair["output"]:
        raise RuntimeError("wrong bbox intermediate failed to change final output")
    return {
        "settings": settings,
        "input": deepcopy(pair["input"]),
        "program": program(settings),
        "output": deepcopy(pair["output"]),
        "counterfactual_program": wrong_intermediate_program(),
        "counterfactual_output": wrong,
        "ablation": "wrong_intermediate",
        "intermediate_value": {
            "bbox": list(analysis["bbox"]),
            "markers_by_side": {
                side: [list(point) for point in points]
                for side, points in analysis["markers_by_side"].items()
            },
            "full_rows": list(analysis["full_rows"]),
            "full_cols": list(analysis["full_cols"]),
        },
    }
