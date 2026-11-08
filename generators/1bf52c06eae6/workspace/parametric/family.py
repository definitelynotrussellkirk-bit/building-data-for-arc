"""Native two-setting square-priority family for 1bf52c06eae6.

``smallest_first`` is the exact canonical rule: each color's bounding box is
expanded to a top-left-anchored square and the smallest square wins overlaps.

``probe_demote`` adds a unique color-9 probe.  Step A runs the canonical shape
priority conceptually at the probe coordinate (ignoring the probe itself) and
selects the first covering shape color.  Step B demotes that input-derived
shape to the end of the priority order and re-renders the entire square mosaic.
The probe is an instruction and is absent from the output.
"""
from __future__ import annotations

from collections import defaultdict
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random
from typing import Any, Callable

HOME = Path(__file__).resolve().parent
CANONICAL_PROGRAM = (HOME / "canonical.rkt").read_text(encoding="utf-8")
PROBE_DEMOTE_PROGRAM = (HOME / "probe_demote.rkt").read_text(encoding="utf-8")
PROGRAMS = {
    "smallest_first": CANONICAL_PROGRAM,
    "probe_demote": PROBE_DEMOTE_PROGRAM,
}

# height, width, strictly increasing sides, selected canonical covering rank,
# requested nonzero input cells (including the probe)
DEMO_SPECS = (
    (12, 15, (3, 5, 8), 1, 24),
    (13, 17, (3, 5, 8, 11), 2, 34),
    (14, 18, (4, 6, 9), 0, 38),
    (16, 20, (3, 6, 9, 13), 1, 48),
    (18, 22, (4, 7, 11, 15), 2, 58),
    (20, 24, (5, 8, 12, 17), 1, 72),
)
QUERY_SPECS = (
    (13, 16, (3, 6, 9), 1, 30),
    (17, 21, (4, 7, 11, 14), 2, 52),
    (22, 26, (5, 9, 14, 18), 1, 78),
    (30, 30, (6, 11, 17, 25), 2, 112),
)


def _validate_settings(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {"priority_mode"}:
        raise ValueError("settings must contain exactly priority_mode")
    mode = settings["priority_mode"]
    if type(mode) is not str or mode not in PROGRAMS:
        raise ValueError("priority_mode must be smallest_first or probe_demote")
    return mode


def _plain_int(name: str, value: Any, low: int, high: int) -> int:
    if type(value) is not int:
        raise ValueError(f"{name} must be a plain integer")
    if not low <= value <= high:
        raise ValueError(f"{name} must be in {low}..{high}")
    return value


def _validate_grid(grid: Any) -> None:
    if (type(grid) is not list or not 1 <= len(grid) <= 30 or type(grid[0]) is not list
            or not 1 <= len(grid[0]) <= 30
            or any(type(row) is not list or len(row) != len(grid[0])
                   or any(type(value) is not int or not 0 <= value <= 9 for value in row)
                   for row in grid)):
        raise ValueError("grid must be rectangular 1..30 with exact integer colors 0..9")


def cells_by_color(grid: list[list[int]], *, exclude: set[int] | frozenset[int] = frozenset()) -> dict[int, list[tuple[int, int]]]:
    _validate_grid(grid)
    result: dict[int, list[tuple[int, int]]] = defaultdict(list)
    for row, values in enumerate(grid):
        for col, color in enumerate(values):
            if color and color not in exclude:
                result[color].append((row, col))
    return dict(result)


def boxes(grid: list[list[int]], *, exclude_probe: bool = False) -> list[tuple[int, int, int, int, int, int]]:
    height, width = len(grid), len(grid[0])
    excluded = {9} if exclude_probe else set()
    result = []
    for color, cells in sorted(cells_by_color(grid, exclude=excluded).items()):
        rows = [row for row, _ in cells]
        cols = [col for _, col in cells]
        r1, c1, r2, c2 = min(rows), min(cols), max(rows), max(cols)
        side = max(r2 - r1 + 1, c2 - c1 + 1)
        result.append((side * side, color, r1, c1,
                       min(height - 1, r1 + side - 1),
                       min(width - 1, c1 + side - 1)))
    return sorted(result)


def _inside(box: tuple[int, int, int, int, int, int], row: int, col: int) -> bool:
    return box[2] <= row <= box[4] and box[3] <= col <= box[5]


def render(grid: list[list[int]], ordered_boxes: list[tuple[int, int, int, int, int, int]]) -> list[list[int]]:
    output = [[0 for _ in row] for row in grid]
    for row in range(len(grid)):
        for col in range(len(grid[0])):
            hit = next((box for box in ordered_boxes if _inside(box, row, col)), None)
            if hit is not None:
                output[row][col] = hit[1]
    return output


def smallest_first_output(grid: list[list[int]]) -> list[list[int]]:
    return render(grid, boxes(grid))


def probe_position(grid: list[list[int]]) -> tuple[int, int]:
    probe = cells_by_color(grid).get(9, [])
    if len(probe) != 1:
        raise ValueError("probe_demote scene must contain exactly one color-9 probe")
    return probe[0]


def selected_color(grid: list[list[int]]) -> int:
    row, col = probe_position(grid)
    hit = next((box for box in boxes(grid, exclude_probe=True) if _inside(box, row, col)), None)
    if hit is None:
        raise ValueError("probe must be covered by at least one shape square")
    return hit[1]


def probe_demote_output(grid: list[list[int]]) -> list[list[int]]:
    shape_boxes = boxes(grid, exclude_probe=True)
    selected = selected_color(grid)
    ordered = [box for box in shape_boxes if box[1] != selected]
    ordered.extend(box for box in shape_boxes if box[1] == selected)
    return render(grid, ordered)


def label(grid: list[list[int]], mode: str) -> list[list[int]]:
    if mode == "smallest_first":
        return smallest_first_output(grid)
    if mode == "probe_demote":
        return probe_demote_output(grid)
    raise ValueError("unknown priority mode")


def _rng(seed: int, domain: str, index: int) -> random.Random:
    raw = f"1bf52c06eae6:{domain}:{seed}:{index}".encode()
    return random.Random(int.from_bytes(hashlib.sha256(raw).digest(), "big"))


def _candidate_boxes(height: int, width: int, side: int, probe: tuple[int, int],
                     covers_probe: bool, rng: random.Random):
    pr, pc = probe
    short = max(2, side - 2)
    candidates = []
    for r1 in range(height - side + 1):
        for c1 in range(width - side + 1):
            covers = r1 <= pr <= r1 + side - 1 and c1 <= pc <= c1 + side - 1
            if covers != covers_probe:
                continue
            for box_h, box_w in ((side, short), (short, side)):
                r2, c2 = r1 + box_h - 1, c1 + box_w - 1
                for diagonal in (0, 1):
                    critical = ((r1, c1), (r2, c2)) if diagonal == 0 else ((r1, c2), (r2, c1))
                    if probe in critical:
                        continue
                    candidates.append((r1, c1, r2, c2, critical))
    rng.shuffle(candidates)
    return candidates


def _choose_shape_colors(seed: int, pair_index: int, count: int, selected_rank: int,
                         rng: random.Random) -> list[int]:
    selected = 1 + ((seed + pair_index) % 8)
    remaining = [color for color in range(1, 9) if color != selected]
    rng.shuffle(remaining)
    colors = remaining[:count]
    colors[selected_rank] = selected
    # Replacing one entry can duplicate selected only if it was already present; it was removed.
    return colors


def build_input(seed: int, pair_index: int,
                spec: tuple[int, int, tuple[int, ...], int, int]) -> list[list[int]]:
    height, width, sides, selected_rank, target_foreground = spec
    if not (0 <= selected_rank < len(sides) - 1):
        raise ValueError("selected rank must leave a later covering shape")
    rng = _rng(seed, "scene", pair_index)
    jitter_r = rng.choice((-1, 0, 1))
    jitter_c = rng.choice((-1, 0, 1))
    probe = (max(2, min(height - 3, height // 2 + jitter_r)),
             max(2, min(width - 3, width // 2 + jitter_c)))
    colors = _choose_shape_colors(seed, pair_index, len(sides), selected_rank, rng)

    for attempt in range(256):
        attempt_rng = random.Random(rng.getrandbits(128) ^ attempt)
        grid = [[0 for _ in range(width)] for _ in range(height)]
        occupied: set[tuple[int, int]] = {probe}
        placed: list[tuple[int, int, int, int, int]] = []
        ok = True
        for rank, (side, color) in enumerate(zip(sides, colors, strict=True)):
            covers = rank >= selected_rank
            candidates = _candidate_boxes(height, width, side, probe, covers, attempt_rng)
            if rank == 0 and not covers and height == width == 30:
                candidates.sort(key=lambda item: 0 if (item[0], item[1], item[4][0]) == (0, 0, (0, 0)) else 1)
            elif not covers:
                pr, pc = probe
                candidates.sort(key=lambda item: (
                    max(item[0] - pr, 0, pr - (item[0] + side - 1))
                    + max(item[1] - pc, 0, pc - (item[1] + side - 1))
                ))
            chosen = next((item for item in candidates if not (set(item[4]) & occupied)), None)
            if chosen is None:
                ok = False
                break
            r1, c1, r2, c2, critical = chosen
            for row, col in critical:
                grid[row][col] = color
                occupied.add((row, col))
            placed.append((color, r1, c1, r2, c2))
        if not ok:
            continue

        fill_candidates = []
        for color, r1, c1, r2, c2 in placed:
            for row in range(r1, r2 + 1):
                for col in range(c1, c2 + 1):
                    if (row, col) not in occupied:
                        fill_candidates.append((row, col, color))
        attempt_rng.shuffle(fill_candidates)
        current = len(occupied)
        for row, col, color in fill_candidates:
            if current >= target_foreground:
                break
            if (row, col) in occupied:
                continue
            grid[row][col] = color
            occupied.add((row, col))
            current += 1
        if current < target_foreground:
            continue
        grid[probe[0]][probe[1]] = 9

        observed_boxes = boxes(grid, exclude_probe=True)
        if [box[0] for box in observed_boxes] != [side * side for side in sides]:
            continue
        covering = [box for box in observed_boxes if _inside(box, *probe)]
        if len(covering) < 2 or covering[0][1] != colors[selected_rank]:
            continue
        selected_box = observed_boxes[selected_rank]
        has_exclusive_selected_cell = any(
            _inside(selected_box, row, col)
            and not any(_inside(other, row, col) for other in observed_boxes
                        if other[1] != selected_box[1])
            for row in range(height)
            for col in range(width)
        )
        if not has_exclusive_selected_cell:
            continue
        if selected_color(grid) != colors[selected_rank]:
            continue
        demoted = probe_demote_output(grid)
        if smallest_first_output(grid) == demoted:
            continue
        if demoted[probe[0]][probe[1]] == colors[selected_rank]:
            continue
        if demoted == render(grid, list(reversed(observed_boxes))):
            continue
        return grid
    raise RuntimeError("could not construct a lawful probe-priority scene")


def _ordered_with_color_last(grid: list[list[int]], color: int) -> list[list[int]]:
    shape_boxes = boxes(grid, exclude_probe=True)
    return render(grid, [box for box in shape_boxes if box[1] != color]
                  + [box for box in shape_boxes if box[1] == color])


def rival_output(grid: list[list[int]], name: str) -> list[list[int]]:
    shape_boxes = boxes(grid, exclude_probe=True)
    row, col = probe_position(grid)
    covering = [box for box in shape_boxes if _inside(box, row, col)]
    selected = selected_color(grid)
    if name == "exclude_probe_smallest_first":
        return render(grid, shape_boxes)
    if name == "always_demote_global_smallest":
        return _ordered_with_color_last(grid, shape_boxes[0][1])
    if name == "demote_global_largest":
        return _ordered_with_color_last(grid, shape_boxes[-1][1])
    if name == "remove_selected":
        return render(grid, [box for box in shape_boxes if box[1] != selected])
    if name == "select_largest_covering":
        return _ordered_with_color_last(grid, covering[-1][1])
    if name == "keep_probe_after_demote":
        output = probe_demote_output(grid)
        output[row][col] = 9
        return output
    if name == "reverse_priority":
        return render(grid, list(reversed(shape_boxes)))
    if name == "bbox_rectangles":
        output = [[0 for _ in values] for values in grid]
        raw = cells_by_color(grid, exclude={9})
        rectangles = []
        for color, cells in raw.items():
            rows = [r for r, _ in cells]
            cols = [c for _, c in cells]
            r1, c1, r2, c2 = min(rows), min(cols), max(rows), max(cols)
            rectangles.append(((r2 - r1 + 1) * (c2 - c1 + 1), color, r1, c1, r2, c2))
        rectangles.sort()
        for r in range(len(grid)):
            for c in range(len(grid[0])):
                hit = next((box for box in rectangles if box[2] <= r <= box[4] and box[3] <= c <= box[5]), None)
                if hit is not None:
                    output[r][c] = hit[1]
        return output
    raise ValueError("unknown rival")


RIVALS = (
    "exclude_probe_smallest_first",
    "always_demote_global_smallest",
    "demote_global_largest",
    "remove_selected",
    "select_largest_covering",
    "keep_probe_after_demote",
    "reverse_priority",
    "bbox_rectangles",
)


def teaching_report(episode: dict[str, Any], mode: str) -> dict[str, Any]:
    demos = episode["train"]
    setting_survivors = [candidate for candidate in PROGRAMS
                         if all(label(pair["input"], candidate) == pair["output"] for pair in demos)]
    rival_survivors = [name for name in RIVALS
                       if all(rival_output(pair["input"], name) == pair["output"] for pair in demos)]
    return {
        "mode": mode,
        "setting_survivors": setting_survivors,
        "surviving_rivals": rival_survivors,
    }


def program(settings: dict[str, Any]) -> str:
    return PROGRAMS[_validate_settings(settings)]


def generate(seed: int, settings: dict[str, Any], demos: int, queries: int) -> dict[str, Any]:
    _plain_int("seed", seed, 0, 2**63 - 1)
    _plain_int("demos", demos, 2, 6)
    if type(queries) is not int or queries != 4:
        raise ValueError("queries must be exactly 4")
    mode = _validate_settings(settings)
    specs = list(DEMO_SPECS[:demos]) + list(QUERY_SPECS)
    inputs = [build_input(seed, index, spec) for index, spec in enumerate(specs)]
    serialized = [json.dumps(grid, separators=(",", ":")) for grid in inputs]
    if len(serialized) != len(set(serialized)):
        raise RuntimeError("episode inputs must be distinct")
    pairs = [{"input": deepcopy(grid), "output": label(grid, mode)} for grid in inputs]
    episode = {
        "train": pairs[:demos],
        "test": pairs[demos:],
        "program_solution": program(settings),
    }
    report = teaching_report(episode, mode)
    if report["setting_survivors"] != [mode] or report["surviving_rivals"]:
        raise RuntimeError(f"demonstrations do not teach the declared rule: {report}")
    return episode
