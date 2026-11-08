"""Episode-fixed marker-count rotation family for ``5553241d87bf``.

The canonical ``identity`` setting copies the separator-cell template exactly.
The alternate setting first counts zero markers in each target cell, uses that
input-derived count as a quarter-turn count, and only then stamps the rotated
complete template.  Inputs are sampled independently of the private setting.
"""
from __future__ import annotations

import copy
from collections import Counter
import hashlib
import json
from pathlib import Path
import random
from typing import Any

from reviewer_support import public_challenge_bytes

TASK_ID = "5553241d87bf"
HERE = Path(__file__).resolve().parent
PARAMETER_NAME = "stamp_transform"
SETTINGS = ("identity", "marker_count_rotation")
SHORTCUTS = (
    "always_quarter_turn",
    "count_minus_one",
    "count_parity",
    "capped_three",
    "foreground_only",
)
DEFAULT_SETTING = "identity"
PROTOTYPE_VERSION = "1.0.0"

# cell size, logical rows, logical columns, target count, row gaps, column gaps
DEMO_PROFILES = (
    (3, 3, 4, 8, None, None),
    (4, 3, 3, 7, None, None),
    (5, 3, 4, 9, None, None),
    (3, 5, 5, 16, None, None),
    (4, 5, 5, 18, None, None),
    (5, 5, 5, 20, None, None),
)
QUERY_PROFILES = (
    (3, 4, 5, 12, None, None),
    (4, 5, 4, 13, None, None),
    (5, 4, 5, 16, None, None),
    (5, 5, 5, 20, (1, 1, 1, 2), (1, 1, 1, 2)),
)


def _integer(value: object, low: int, high: int, label: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{label} must be an exact integer in {low}..{high}")
    return value


def _settings(settings: object) -> str:
    if (
        type(settings) is not dict
        or set(settings) != {PARAMETER_NAME}
        or type(settings[PARAMETER_NAME]) is not str
        or settings[PARAMETER_NAME] not in SETTINGS
    ):
        raise ValueError(
            "settings must contain only "
            "stamp_transform=identity|marker_count_rotation"
        )
    return settings[PARAMETER_NAME]


def _grid(grid: object) -> list[list[int]]:
    if (
        type(grid) is not list
        or not 1 <= len(grid) <= 30
        or type(grid[0]) is not list
        or not 1 <= len(grid[0]) <= 30
    ):
        raise ValueError("grid must be a nonempty 1..30 rectangle")
    width = len(grid[0])
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(value) is not int or not 0 <= value <= 9 for value in row)
        for row in grid
    ):
        raise ValueError("grid cells must be exact integer colors 0..9")
    return grid


def _bounds(size: int, separators: list[int]) -> list[tuple[int, int]]:
    points = [-1, *separators, size]
    return [
        (points[index] + 1, points[index + 1] - 1)
        for index in range(len(points) - 1)
        if points[index + 1] - points[index] > 1
    ]


def _facts(grid: object) -> dict[str, Any]:
    data = _grid(grid)
    height, width = len(data), len(data[0])
    counts = Counter(value for row in data for value in row)
    background = max(counts, key=lambda value: (counts[value], -value))
    separator_rows = [
        row for row in range(height) if all(data[row][col] == 0 for col in range(width))
    ]
    separator_cols = [
        col for col in range(width) if all(data[row][col] == 0 for row in range(height))
    ]
    row_bounds = _bounds(height, separator_rows)
    col_bounds = _bounds(width, separator_cols)
    if not separator_rows or not separator_cols or len(row_bounds) < 2 or len(col_bounds) < 2:
        raise ValueError("complete zero separators must define at least two cell rows and columns")
    heights = {r1 - r0 + 1 for r0, r1 in row_bounds}
    widths = {c1 - c0 + 1 for c0, c1 in col_bounds}
    if len(heights) != 1 or len(widths) != 1:
        raise ValueError("logical cells must have equal dimensions")

    template_index = None
    for row_index, (r0, r1) in enumerate(row_bounds):
        for col_index, (c0, c1) in enumerate(col_bounds):
            if any(
                data[row][col] not in (0, background)
                for row in range(r0, r1 + 1)
                for col in range(c0, c1 + 1)
            ):
                template_index = (row_index, col_index)
                break
        if template_index is not None:
            break
    if template_index is None:
        raise ValueError("no non-background nonzero template cell found")

    tr0, tr1 = row_bounds[template_index[0]]
    tc0, tc1 = col_bounds[template_index[1]]
    pattern = [row[tc0 : tc1 + 1] for row in data[tr0 : tr1 + 1]]
    targets = []
    for row_index, (r0, r1) in enumerate(row_bounds):
        for col_index, (c0, c1) in enumerate(col_bounds):
            if (row_index, col_index) == template_index:
                continue
            dot_count = sum(
                data[row][col] == 0
                for row in range(r0, r1 + 1)
                for col in range(c0, c1 + 1)
            )
            if dot_count:
                targets.append(
                    {
                        "index": [row_index, col_index],
                        "bounds": [r0, r1, c0, c1],
                        "dot_count": dot_count,
                    }
                )
    if not targets:
        raise ValueError("at least one dot-marked target is required")
    return {
        "height": height,
        "width": width,
        "background": background,
        "separator_rows": separator_rows,
        "separator_cols": separator_cols,
        "row_bounds": row_bounds,
        "col_bounds": col_bounds,
        "logical_shape": [len(row_bounds), len(col_bounds)],
        "cell_shape": [next(iter(heights)), next(iter(widths))],
        "template_index": list(template_index),
        "template_bounds": [tr0, tr1, tc0, tc1],
        "pattern": pattern,
        "template_zeros": [
            [row, col]
            for row, values in enumerate(pattern)
            for col, value in enumerate(values)
            if value == 0
        ],
        "targets": targets,
        "target_count": len(targets),
        "target_dot_counts": [record["dot_count"] for record in targets],
    }


def features(grid: object) -> dict[str, Any]:
    return copy.deepcopy(_facts(grid))


def rotate_cw(pattern: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*pattern[::-1])]


def _rotate(pattern: list[list[int]], turns: int) -> list[list[int]]:
    out = [row[:] for row in pattern]
    for _ in range(turns % 4):
        out = rotate_cw(out)
    return out


def _turns(mode: str, dot_count: int) -> int:
    if mode == "identity":
        return 0
    if mode == "marker_count_rotation":
        return dot_count % 4
    if mode == "always_quarter_turn":
        return 1
    if mode == "count_minus_one":
        return (dot_count - 1) % 4
    if mode == "count_parity":
        return dot_count % 2
    if mode == "capped_three":
        return min(dot_count, 3) % 4
    raise ValueError(f"unsupported transformation: {mode}")


def _transform(
    grid: list[list[int]],
    mode: str,
    *,
    count_override: tuple[tuple[int, int], int] | None = None,
) -> list[list[int]]:
    facts = _facts(grid)
    out = copy.deepcopy(grid)
    pattern = facts["pattern"]
    background = facts["background"]
    for record in facts["targets"]:
        index = tuple(record["index"])
        dot_count = record["dot_count"]
        if count_override is not None and index == count_override[0]:
            dot_count = count_override[1]
        r0, r1, c0, c1 = record["bounds"]
        if mode == "foreground_only":
            stamp = pattern
            for drow, values in enumerate(stamp):
                for dcol, value in enumerate(values):
                    if value not in (0, background):
                        out[r0 + drow][c0 + dcol] = value
            continue
        stamp = _rotate(pattern, _turns(mode, dot_count))
        if len(stamp) != r1 - r0 + 1 or len(stamp[0]) != c1 - c0 + 1:
            raise ValueError("rotating a non-square template cannot fit its target cell")
        for drow, values in enumerate(stamp):
            for dcol, value in enumerate(values):
                out[r0 + drow][c0 + dcol] = value
    return out


def transform(grid: list[list[int]], settings: dict[str, str]) -> list[list[int]]:
    return _transform(grid, _settings(settings))


def transform_with_count_override(
    grid: list[list[int]], target_index: list[int] | tuple[int, int], wrong_count: int
) -> list[list[int]]:
    _integer(wrong_count, 0, 99, "wrong_count")
    if (
        type(target_index) not in (list, tuple)
        or len(target_index) != 2
        or any(type(value) is not int for value in target_index)
    ):
        raise ValueError("target_index must be a two-integer logical coordinate")
    return _transform(
        grid,
        "marker_count_rotation",
        count_override=((target_index[0], target_index[1]), wrong_count),
    )


def program(settings: dict[str, str]) -> str:
    setting = _settings(settings)
    name = "canonical.rkt" if setting == "identity" else "marker_count_rotation.rkt"
    return (HERE / name).read_text(encoding="utf-8").rstrip("\n")


def _replace_turns(expression: str) -> str:
    source = program({PARAMETER_NAME: "marker_count_rotation"})
    old = "(turns (modulo dot-count 4))"
    if source.count(old) != 1:
        raise ValueError("pinned marker-count turn expression changed")
    return source.replace(old, f"(turns {expression})")


def _foreground_only_program() -> str:
    source = program({PARAMETER_NAME: "identity"})
    old = """(for* ((dr (range 0 ph)) (dc (range 0 pw)))
                             (hash-set! result
                                        (list (+ r1 dr) (+ c1 dc))
                                        (list-ref (list-ref pattern dr) dc)))"""
    new = """(for* ((dr (range 0 ph)) (dc (range 0 pw)))
                             (let ((value (list-ref (list-ref pattern dr) dc)))
                               (when (and (!= value bg) (!= value 0))
                                 (hash-set! result
                                            (list (+ r1 dr) (+ c1 dc))
                                            value))))"""
    if source.count(old) != 1:
        raise ValueError("pinned canonical stamp expression changed")
    return source.replace(old, new)


def rival_programs() -> dict[str, str]:
    return {
        "identity": program({PARAMETER_NAME: "identity"}),
        "marker_count_rotation": program({PARAMETER_NAME: "marker_count_rotation"}),
        "always_quarter_turn": _replace_turns("1"),
        "count_minus_one": _replace_turns("(modulo (+ dot-count 3) 4)"),
        "count_parity": _replace_turns("(modulo dot-count 2)"),
        "capped_three": _replace_turns("(min dot-count 3)"),
        "foreground_only": _foreground_only_program(),
    }


def rival_outputs(grid: list[list[int]]) -> dict[str, list[list[int]]]:
    return {name: _transform(grid, name) for name in (*SETTINGS, *SHORTCUTS)}


def _rng(seed: int, split: str, index: int) -> random.Random:
    digest = hashlib.sha256(
        f"{TASK_ID}:marker-count-rotation-v1:{seed}:{split}:{index}".encode()
    ).digest()
    return random.Random(int.from_bytes(digest, "big"))


def _axis_bounds(count: int, cell_size: int, gaps: tuple[int, ...] | None):
    gaps = (1,) * (count - 1) if gaps is None else gaps
    if len(gaps) != count - 1 or any(type(value) is not int or value < 1 for value in gaps):
        raise ValueError("separator gaps must contain positive integer widths")
    bounds = []
    cursor = 0
    for index in range(count):
        bounds.append((cursor, cursor + cell_size - 1))
        cursor += cell_size
        if index < len(gaps):
            cursor += gaps[index]
    return bounds, cursor


def _template_pattern(cell_size: int, background: int, colors: list[int], rng: random.Random):
    pattern = [[background] * cell_size for _ in range(cell_size)]
    positions = [
        (0, 0),
        (1, 0),
        (cell_size - 1, 0),
        (cell_size - 1, 1),
        (0, cell_size - 1),
        (1, cell_size - 2),
    ]
    for index, (row, col) in enumerate(positions):
        pattern[row][col] = colors[index % len(colors)]
    zero = (cell_size - 1, cell_size - 1)
    pattern[zero[0]][zero[1]] = 0
    pattern = _rotate(pattern, rng.randrange(4))
    orbit = {json.dumps(_rotate(pattern, turns), separators=(",", ":")) for turns in range(4)}
    if len(orbit) != 4:
        raise AssertionError("template must have four distinct rotations")
    return pattern


def _draw(seed: int, split: str, index: int) -> list[list[int]]:
    profiles = DEMO_PROFILES if split == "train" else QUERY_PROFILES
    cell_size, logical_rows, logical_cols, target_count, row_gaps, col_gaps = profiles[index]
    row_bounds, height = _axis_bounds(logical_rows, cell_size, row_gaps)
    col_bounds, width = _axis_bounds(logical_cols, cell_size, col_gaps)
    if not (7 <= height <= 30 and 7 <= width <= 30):
        raise AssertionError("profile dimensions left the supported ARC range")
    rng = _rng(seed, split, index)
    background, color1, color2, color3 = rng.sample(range(1, 10), 4)
    grid = [[0] * width for _ in range(height)]
    for r0, r1 in row_bounds:
        for c0, c1 in col_bounds:
            for row in range(r0, r1 + 1):
                for col in range(c0, c1 + 1):
                    grid[row][col] = background

    logical = [(row, col) for row in range(logical_rows) for col in range(logical_cols)]
    template_index = rng.choice(logical)
    pattern = _template_pattern(cell_size, background, [color1, color2, color3], rng)
    tr0, _ = row_bounds[template_index[0]]
    tc0, _ = col_bounds[template_index[1]]
    for drow, values in enumerate(pattern):
        for dcol, value in enumerate(values):
            grid[tr0 + drow][tc0 + dcol] = value

    candidates = [position for position in logical if position != template_index]
    if target_count > len(candidates):
        raise AssertionError("profile target count exceeds logical capacity")
    rng.shuffle(candidates)
    targets = candidates[:target_count]
    dot_counts = [1 + index % 4 for index in range(target_count)]
    rng.shuffle(dot_counts)
    cells = [(row, col) for row in range(cell_size) for col in range(cell_size)]
    for rank, ((row_index, col_index), dot_count) in enumerate(zip(targets, dot_counts)):
        r0, _ = row_bounds[row_index]
        c0, _ = col_bounds[col_index]
        marker_rng = random.Random(rng.getrandbits(128) ^ rank)
        markers = marker_rng.sample(cells, dot_count)
        for drow, dcol in markers:
            grid[r0 + drow][c0 + dcol] = 0

    facts = _facts(grid)
    if facts["logical_shape"] != [logical_rows, logical_cols]:
        raise AssertionError("logical board shape drifted")
    if facts["cell_shape"] != [cell_size, cell_size]:
        raise AssertionError("cell shape drifted")
    if facts["template_index"] != list(template_index):
        raise AssertionError("template inference drifted")
    if facts["target_count"] != target_count:
        raise AssertionError("target inference drifted")
    if set(facts["target_dot_counts"]) != {1, 2, 3, 4}:
        raise AssertionError("every sampled scene must expose all marker counts")
    outputs = rival_outputs(grid)
    if outputs["identity"] == outputs["marker_count_rotation"]:
        raise AssertionError("parametric settings do not disagree")
    for shortcut in SHORTCUTS:
        if outputs[shortcut] in (outputs["identity"], outputs["marker_count_rotation"]):
            raise AssertionError(f"shortcut {shortcut} fits a constructed input")
    return grid


def teaching_certificate(train, query_inputs, settings):
    chosen = _settings(settings)
    if type(train) is not list or not train or type(query_inputs) is not list or not query_inputs:
        raise ValueError("nonempty demonstrations and query inputs are required")
    names = (*SETTINGS, *SHORTCUTS)
    rejected: dict[str, int] = {}
    for index, pair in enumerate(train):
        _grid(pair["output"])
        for name, output in rival_outputs(pair["input"]).items():
            if output != pair["output"]:
                rejected.setdefault(name, index)
    survivors = [name for name in names if name not in rejected]
    if chosen not in survivors:
        raise ValueError("demonstration labels contradict selected transformation")
    query_identifiable = []
    for grid in query_inputs:
        outputs = rival_outputs(grid)
        query_identifiable.append(all(outputs[name] == outputs[chosen] for name in survivors))
    return {
        "scope": (
            "two admitted stamp transforms plus fixed-turn, off-by-one, parity, "
            "capped-count, and foreground-only shortcuts"
        ),
        "survivors": survivors,
        "rejected": rejected,
        "identified": survivors == [chosen],
        "query_identifiable": query_identifiable,
        "query_answers_used_for_fitting": False,
    }


def generate(seed: int, settings: dict[str, str], demos: int = 3, queries: int = 4):
    _integer(seed, 0, 2**63 - 1, "seed")
    _settings(settings)
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    episode = {
        "task_id": TASK_ID,
        "seed": seed,
        "settings": copy.deepcopy(settings),
        "program_solution": program(settings),
        "reference": "proposed_parametric",
        "training_admitted": False,
    }
    for split, count in (("train", demos), ("test", queries)):
        episode[split] = []
        for index in range(count):
            grid = _draw(seed, split, index)
            episode[split].append({"input": grid, "output": transform(grid, settings)})
    episode["certificate"] = verify_episode(episode)
    return episode


def verify_episode(episode):
    if type(episode) is not dict:
        raise ValueError("episode must be an object")
    settings = episode.get("settings")
    _settings(settings)
    if episode.get("program_solution") != program(settings):
        raise ValueError("program_solution does not match selected transformation")
    seen = set()
    for split, bounds in (("train", (2, 6)), ("test", (1, 4))):
        pairs = episode.get(split)
        if type(pairs) is not list or not bounds[0] <= len(pairs) <= bounds[1]:
            raise ValueError(f"unsupported {split} count")
        for pair in pairs:
            if type(pair) is not dict or not {"input", "output"} <= set(pair):
                raise ValueError("each pair must contain input and output")
            expected = transform(pair["input"], settings)
            _grid(pair["output"])
            if pair["output"] != expected:
                raise ValueError(f"{split} label disagrees with selected transformation")
            key = json.dumps(pair["input"], separators=(",", ":"))
            if key in seen:
                raise ValueError("all inputs must be distinct")
            seen.add(key)
    certificate = teaching_certificate(
        episode["train"], [pair["input"] for pair in episode["test"]], settings
    )
    if not certificate["identified"] or not all(certificate["query_identifiable"]):
        raise ValueError("demonstrations do not identify the selected transformation")
    return certificate


def visible_turn(episode, index: int) -> bytes:
    _integer(index, 0, len(episode["test"]) - 1, "query index")
    return public_challenge_bytes(
        {"train": episode["train"], "test": [episode["test"][index]]}
    )
