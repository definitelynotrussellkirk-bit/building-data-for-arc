#!/usr/bin/env python3
"""Racket-backed yellow-turn parametric prototype for fbf36c193fa6.

Red rays remain canonical.  The episode-fixed parameter chooses whether yellow
staircase rays turn clockwise (the exact canonical rule) or counterclockwise
around the cyan square.  Inputs are constructed independently of that setting
and contain open controls, branch blockers, boundary contacts and gray decoys.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import random
from typing import Any, Iterable

from reviewer_support import canonical_path, find_root, public_challenge_bytes, public_challenge_id

TASK_ID = "fbf36c193fa6"
VERSION = "yellow-turn-prototype-v1"
ALLOWED_TURNS = ("clockwise", "counterclockwise")
DEFAULT_TURN = "clockwise"
MIN_DEMOS = 2
MAX_DEMOS = 6
MIN_QUERIES = 1
MAX_QUERIES = 4
HERE = Path(__file__).resolve().parent

_DEMO_SIZES = ((16, 16), (18, 19), (20, 18), (21, 23), (23, 21), (22, 22))
_QUERY_SIZES = ((17, 20), (20, 17), (24, 24), (30, 30))
_DEMO_PROFILES = ("open", "mixed_both", "mixed_clockwise", "mixed_counterclockwise", "pinched", "dense")
_QUERY_PROFILES = ("mixed_both", "open", "dense", "boundary")

Cell = tuple[int, int]
BBox = tuple[int, int, int, int]


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _stable_rng(seed: int, role: str, index: int) -> random.Random:
    digest = hashlib.sha256(f"{VERSION}:{seed}:{role}:{index}".encode()).digest()
    return random.Random(int.from_bytes(digest[:16], "big"))


def validate_seed(seed: int) -> int:
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative integer (bool rejected)")
    return seed


def validate_count(name: str, value: int, lo: int, hi: int) -> int:
    if type(value) is not int or not lo <= value <= hi:
        raise ValueError(f"{name} must be an integer in [{lo},{hi}]")
    return value


def normalize_settings(settings: dict[str, Any] | None = None) -> dict[str, str]:
    if settings is None:
        settings = {}
    if not isinstance(settings, dict):
        raise TypeError("settings must be a dictionary")
    unknown = sorted(set(settings) - {"yellow_turn"})
    if unknown:
        raise ValueError(f"unknown setting(s): {', '.join(unknown)}")
    turn = settings.get("yellow_turn", DEFAULT_TURN)
    if type(turn) is not str or turn not in ALLOWED_TURNS:
        raise ValueError(f"yellow_turn must be one of {ALLOWED_TURNS}")
    return {"yellow_turn": turn}


@lru_cache(maxsize=1)
def canonical_program(root: str | Path | None = None) -> str:
    root_path = find_root(root or __file__)
    matches = []
    with canonical_path(root_path).open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                row = json.loads(line)
                if row.get("task_id") == TASK_ID:
                    matches.append(row)
    if len(matches) != 1:
        raise ValueError(f"expected exactly one canonical row for {TASK_ID}")
    return str(matches[0]["program_solution"])


def render_program(yellow_turn: str = DEFAULT_TURN, *, root: str | Path | None = None) -> str:
    selected = normalize_settings({"yellow_turn": yellow_turn})
    canonical = canonical_program(root)
    if selected["yellow_turn"] == DEFAULT_TURN:
        return canonical
    old = """(ycorners (list (list r1 c1 -1 1)
                                (list r1 c2 1 1)
                                (list r2 c2 1 -1)
                                (list r2 c1 -1 -1)))"""
    new = """(ycorners (list (list r1 c1 1 -1)
                                (list r2 c1 1 1)
                                (list r2 c2 -1 1)
                                (list r1 c2 -1 -1)))"""
    if canonical.count(old) != 1:
        raise ValueError("canonical yellow-corner block changed")
    return canonical.replace(old, new, 1)


def _in_bounds(row: int, col: int, height: int, width: int) -> bool:
    return 0 <= row < height and 0 <= col < width


def _square_cells(box: BBox) -> set[Cell]:
    top, left, bottom, right = box
    return {(row, col) for row in range(top, bottom + 1) for col in range(left, right + 1)}


def _red_specs(box: BBox) -> tuple[tuple[Cell, int, int], ...]:
    top, left, bottom, right = box
    return (
        ((top, left), -1, -1),
        ((top, right), -1, 1),
        ((bottom, left), 1, -1),
        ((bottom, right), 1, 1),
    )


def _yellow_specs(box: BBox, turn: str) -> tuple[tuple[Cell, int, int], ...]:
    top, left, bottom, right = box
    if turn == "clockwise":
        return (
            ((top, left), -1, 1),
            ((top, right), 1, 1),
            ((bottom, right), 1, -1),
            ((bottom, left), -1, -1),
        )
    return (
        ((top, left), 1, -1),
        ((bottom, left), 1, 1),
        ((bottom, right), -1, 1),
        ((top, right), -1, -1),
    )


def _red_trace(grid: list[list[int]], corner: Cell, dr: int, dc: int) -> list[Cell]:
    height, width = len(grid), len(grid[0])
    row, col = corner[0] + dr, corner[1] + dc
    cells: list[Cell] = []
    while _in_bounds(row, col, height, width):
        if grid[row][col] == 5:
            break
        if grid[row][col - dc] == 5 and grid[row - dr][col] == 5:
            break
        cells.append((row, col))
        row += dr
        col += dc
    return cells


def _yellow_trace(grid: list[list[int]], corner: Cell, dr: int, dc: int) -> list[Cell]:
    height, width = len(grid), len(grid[0])
    active_row, active_col = corner[0] + dr, corner[1] + dc
    if not _in_bounds(active_row, active_col, height, width) or grid[active_row][active_col] == 5:
        return []
    cells: list[Cell] = [(active_row, active_col)]
    phase = 0 if dr * dc < 0 else 1
    while True:
        next_row, next_col = active_row + dr, active_col + dc
        if phase == 0:
            step_row, step_col = active_row + dr, active_col
        else:
            step_row, step_col = active_row, active_col + dc
        if not _in_bounds(next_row, next_col, height, width):
            return cells
        if not _in_bounds(step_row, step_col, height, width) or grid[step_row][step_col] == 5:
            return cells
        cells.append((step_row, step_col))
        if grid[next_row][next_col] == 5:
            return cells
        cells.append((next_row, next_col))
        active_row, active_col = next_row, next_col
        phase = 1 - phase


def _find_box(grid: list[list[int]]) -> BBox:
    cyan = [(row, col) for row, values in enumerate(grid) for col, value in enumerate(values) if value == 8]
    if len(cyan) != 9:
        raise ValueError("expected exactly one solid 3x3 cyan square")
    top = min(row for row, _ in cyan)
    bottom = max(row for row, _ in cyan)
    left = min(col for _, col in cyan)
    right = max(col for _, col in cyan)
    box = (top, left, bottom, right)
    if bottom - top != 2 or right - left != 2 or set(cyan) != _square_cells(box):
        raise ValueError("cyan cells must form one solid 3x3 square")
    return box


def apply_python(grid: list[list[int]], yellow_turn: str = DEFAULT_TURN) -> list[list[int]]:
    normalize_settings({"yellow_turn": yellow_turn})
    if (
        type(grid) is not list
        or not grid
        or type(grid[0]) is not list
        or not grid[0]
        or any(type(row) is not list or len(row) != len(grid[0]) for row in grid)
        or any(type(cell) is not int or not 0 <= cell <= 9 for row in grid for cell in row)
    ):
        raise ValueError("grid must be a nonempty rectangular ARC integer grid")
    box = _find_box(grid)
    red_cells = {
        cell
        for corner, dr, dc in _red_specs(box)
        for cell in _red_trace(grid, corner, dr, dc)
    }
    yellow_cells = {
        cell
        for corner, dr, dc in _yellow_specs(box, yellow_turn)
        for cell in _yellow_trace(grid, corner, dr, dc)
    }
    output = deepcopy(grid)
    for row, col in red_cells:
        output[row][col] = 2
    for row, col in yellow_cells:
        output[row][col] = 4
    return output


def _ray_points(corner: Cell, dr: int, dc: int, height: int, width: int) -> tuple[list[Cell], list[Cell], list[Cell]]:
    start = (corner[0] + dr, corner[1] + dc)
    if not _in_bounds(*start, height, width):
        return [], [], []
    starts = [start]
    intermediates: list[Cell] = []
    diagonals: list[Cell] = []
    active_row, active_col = start
    phase = 0 if dr * dc < 0 else 1
    while True:
        next_cell = (active_row + dr, active_col + dc)
        step_cell = (active_row + dr, active_col) if phase == 0 else (active_row, active_col + dc)
        if not _in_bounds(*next_cell, height, width) or not _in_bounds(*step_cell, height, width):
            break
        intermediates.append(step_cell)
        diagonals.append(next_cell)
        active_row, active_col = next_cell
        phase = 1 - phase
    return starts, intermediates, diagonals


def _sensitive_cells(height: int, width: int, box: BBox) -> set[Cell]:
    cells = set(_square_cells(box))
    for corner, dr, dc in _red_specs(box):
        row, col = corner[0] + dr, corner[1] + dc
        while _in_bounds(row, col, height, width):
            cells.update({(row, col), (row, col - dc), (row - dr, col)})
            row += dr
            col += dc
    for turn in ALLOWED_TURNS:
        for corner, dr, dc in _yellow_specs(box, turn):
            starts, intermediates, diagonals = _ray_points(corner, dr, dc, height, width)
            cells.update(starts)
            cells.update(intermediates)
            cells.update(diagonals)
    return {(row, col) for row, col in cells if _in_bounds(row, col, height, width)}


def _pick(values: list[Cell], index: int) -> Cell | None:
    if not values:
        return None
    return values[min(index, len(values) - 1)]


def _deliberate_blockers(profile: str, box: BBox, height: int, width: int) -> set[Cell]:
    if profile == "open":
        return set()
    blockers: set[Cell] = set()
    red = _red_specs(box)
    # Direct gray on one diagonal and an orthogonal gray pair pinching the
    # opposite diagonal preserve both canonical red stopping branches.
    corner, dr, dc = red[0]
    diagonal = [(corner[0] + dr * depth, corner[1] + dc * depth) for depth in range(1, 5)]
    direct = _pick([cell for cell in diagonal if _in_bounds(*cell, height, width)], 1)
    if direct:
        blockers.add(direct)
    corner, dr, dc = red[3]
    targets = [(corner[0] + dr * depth, corner[1] + dc * depth) for depth in range(2, 6)]
    target = _pick([cell for cell in targets if _in_bounds(*cell, height, width)], 1)
    if target:
        blockers.update({(target[0], target[1] - dc), (target[0] - dr, target[1])})

    turns: Iterable[str]
    if profile == "mixed_clockwise":
        turns = ("clockwise",)
    elif profile == "mixed_counterclockwise":
        turns = ("counterclockwise",)
    elif profile == "boundary":
        # The large stress scene uses boundary gray cells as decoys.  Keep its
        # yellow rays open so the 30x30 canvas, rather than only the cells next
        # to the source square, participates in the transformation.
        turns = ()
    else:
        turns = ALLOWED_TURNS
    for turn in turns:
        specs = _yellow_specs(box, turn)
        starts, _, _ = _ray_points(*specs[0], height, width)
        _, intermediates, _ = _ray_points(*specs[1], height, width)
        _, _, diagonals = _ray_points(*specs[2], height, width)
        start = _pick(starts, 0)
        intermediate = _pick(intermediates, 1)
        diagonal = _pick(diagonals, 1)
        for cell in (start, intermediate, diagonal):
            if cell is not None:
                blockers.add(cell)
    if profile in {"pinched", "dense"}:
        for corner, dr, dc in red[1:3]:
            target = (corner[0] + 3 * dr, corner[1] + 3 * dc)
            if _in_bounds(*target, height, width):
                blockers.update({(target[0], target[1] - dc), (target[0] - dr, target[1])})
    return {cell for cell in blockers if _in_bounds(*cell, height, width) and cell not in _square_cells(box)}


def _anchor(seed: int, role: str, index: int, height: int, width: int) -> tuple[int, int]:
    rng = _stable_rng(seed, role + "-anchor", index)
    rows = list(range(4, height - 6))
    cols = list(range(4, width - 6))
    if not rows or not cols:
        raise ValueError("scene too small for the 3x3 square and four-cell margins")
    if role == "query" and index == 3:
        # Center the 30x30 stress scene so every quadrant has room for long
        # red and yellow rays. Boundary contacts are supplied independently
        # by setting-neutral gray decoys.
        return rows[len(rows) // 2], cols[len(cols) // 2]
    return rows[rng.randrange(len(rows))], cols[rng.randrange(len(cols))]


def _scene(seed: int, role: str, index: int, height: int, width: int, profile: str) -> list[list[int]]:
    rng = _stable_rng(seed, role, index)
    top, left = _anchor(seed, role, index, height, width)
    box = (top, left, top + 2, left + 2)
    square = _square_cells(box)
    grid = [[0 for _ in range(width)] for _ in range(height)]
    for row, col in square:
        grid[row][col] = 8

    blockers = _deliberate_blockers(profile, box, height, width)
    for row, col in blockers:
        grid[row][col] = 5

    sensitive = _sensitive_cells(height, width, box)
    target_gray = min(64, max(20, (height * width) // 12))
    # Ensure real boundary contacts, selected only from cells irrelevant to all
    # red/yellow variants so they remain decoys rather than accidental blockers.
    boundary = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if (row in (0, height - 1) or col in (0, width - 1))
        and (row, col) not in sensitive
        and (row, col) not in blockers
    ]
    rng.shuffle(boundary)
    for cell in boundary[: min(8, max(0, target_gray - len(blockers)))]:
        grid[cell[0]][cell[1]] = 5

    candidates = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if (row, col) not in sensitive and grid[row][col] == 0
    ]
    rng.shuffle(candidates)
    need = target_gray - sum(cell == 5 for values in grid for cell in values)
    if need < 0 or len(candidates) < need:
        raise RuntimeError("insufficient setting-independent gray-decoy capacity")
    for row, col in candidates[:need]:
        grid[row][col] = 5

    if sum(cell == 5 for values in grid for cell in values) != target_gray:
        raise RuntimeError("gray-count construction drift")
    clockwise = apply_python(grid, "clockwise")
    counterclockwise = apply_python(grid, "counterclockwise")
    if clockwise == counterclockwise:
        raise RuntimeError("constructed scene does not distinguish yellow_turn")
    for output in (clockwise, counterclockwise):
        colors = {cell for values in output for cell in values}
        if not {2, 4, 5, 8} <= colors:
            raise RuntimeError("constructed scene lost a required ray/input role")
    return grid


def episode_inputs(
    seed: int,
    *,
    demos: int = 3,
    queries: int = 4,
) -> tuple[list[list[list[int]]], list[list[list[int]]]]:
    validate_seed(seed)
    demos = validate_count("demos", demos, MIN_DEMOS, MAX_DEMOS)
    queries = validate_count("queries", queries, MIN_QUERIES, MAX_QUERIES)
    train = [
        _scene(seed, "demo", index, *_DEMO_SIZES[index], _DEMO_PROFILES[index])
        for index in range(demos)
    ]
    test = [
        _scene(seed, "query", index, *_QUERY_SIZES[index], _QUERY_PROFILES[index])
        for index in range(queries)
    ]
    grids = train + test
    if len({json.dumps(grid, separators=(",", ":")) for grid in grids}) != len(grids):
        raise RuntimeError("episode input sampler produced a duplicate")
    return train, test


def build_episode_python(
    seed: int,
    settings: dict[str, Any] | None = None,
    *,
    demos: int = 3,
    queries: int = 4,
) -> dict[str, Any]:
    selected = normalize_settings(settings)
    train_inputs, test_inputs = episode_inputs(seed, demos=demos, queries=queries)

    def pair(grid: list[list[int]]) -> dict[str, Any]:
        return {"input": grid, "output": apply_python(grid, selected["yellow_turn"])}

    return {
        "train": [pair(grid) for grid in train_inputs],
        "test": [pair(grid) for grid in test_inputs],
        "program_solution": render_program(selected["yellow_turn"]),
    }


def execute(bridge: Any, source: str, grid: list[list[int]]) -> list[list[int]]:
    if not source.startswith("(rule!") or not source.endswith(")"):
        raise ValueError("expected a rule! wrapper")
    bridge.define_grid("g", grid)
    body = source[len("(rule! ") : -1]
    expression = f"({body} g)" if body.lstrip().startswith("(lambda") else body
    result = bridge.eval_text(expression)
    if (
        type(result) is not list
        or not result
        or type(result[0]) is not list
        or not result[0]
        or any(type(row) is not list or len(row) != len(result[0]) for row in result)
        or any(type(cell) is not int or not 0 <= cell <= 9 for row in result for cell in row)
    ):
        raise ValueError("Racket rule returned a non-ARC grid")
    return result


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    return {
        "train": deepcopy(episode["train"]),
        "test": [{"input": deepcopy(pair["input"])} for pair in episode["test"]],
    }


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_public_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(public_challenge_bytes(payload))


def _source_hashes(root: Path) -> dict[str, str]:
    paths = [
        HERE / "prototype.py",
        HERE / "adapter.py",
        HERE / "promotion.json",
        HERE / "README.md",
        HERE.parents[1] / "tests" / "test_parametric_yellow_turn.py",
        HERE.parents[1] / "tests" / "test_generator_fbf36c193fa6.py",
        HERE.parents[1] / "tests" / "test_ray_distribution.py",
    ]
    return {
        path.relative_to(root).as_posix(): _sha256(path.read_bytes())
        for path in paths
        if path.is_file()
    }


def materialize(output: str | Path, *, base_seed: int = 20261024) -> dict[str, Any]:
    validate_seed(base_seed)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    root = find_root(__file__)
    settings = ALLOWED_TURNS
    train_inputs, test_inputs = episode_inputs(base_seed, demos=3, queries=4)
    grids = train_inputs + test_inputs

    from arc_repl.racket_bridge import RacketBridge

    outputs: dict[str, list[list[list[int]]]] = {}
    with RacketBridge() as bridge:
        for turn in settings:
            source = render_program(turn)
            rows = [execute(bridge, source, grid) for grid in grids]
            expected = [apply_python(grid, turn) for grid in grids]
            if rows != expected:
                raise ValueError(f"Racket/Python parity failure for yellow_turn={turn}")
            outputs[turn] = rows
        runtime_identity = bridge.runtime_identity

    seen_ids: set[str] = set()
    complete = []
    all_teaching = True
    for chosen in settings:
        train = [
            {"input": deepcopy(grids[index]), "output": deepcopy(outputs[chosen][index])}
            for index in range(3)
        ]
        test = [
            {"input": deepcopy(grids[3 + index]), "output": deepcopy(outputs[chosen][3 + index])}
            for index in range(4)
        ]
        rivals = []
        survivors = []
        for candidate in settings:
            demo_differences = [index for index in range(3) if outputs[candidate][index] != outputs[chosen][index]]
            query_differences = [index for index in range(4) if outputs[candidate][3 + index] != outputs[chosen][3 + index]]
            if not demo_differences:
                survivors.append(candidate)
            rivals.append(
                {
                    "settings": {"yellow_turn": candidate},
                    "demo_differences": demo_differences,
                    "query_differences": query_differences,
                }
            )
        teaching_pass = survivors == [chosen]
        all_teaching = all_teaching and teaching_pass
        source = render_program(chosen)
        private = {
            "schema": "fbf36c193fa6-parametric-yellow-turn-v1",
            "seed": base_seed,
            "settings": {"yellow_turn": chosen},
            "program": source,
            "program_sha256": _sha256(source.encode()),
            "train": train,
            "test": test,
            "rival_checks": rivals,
            "demo_only_survivors": [{"yellow_turn": turn} for turn in survivors],
            "demo_only_teaching_pass": teaching_pass,
            "label_authority": "bundled Racket bridge executing exact instantiated programs",
        }
        public = public_challenge(private)
        identifier = public_challenge_id(public)
        if identifier in seen_ids:
            raise ValueError("duplicate visible challenge across settings")
        seen_ids.add(identifier)
        name = f"challenge-{identifier}"
        private["public_id"] = identifier
        private["public_file"] = f"public/{name}.json"
        _write_public_json(output / "public" / f"{name}.json", public)
        _write_json(output / "private" / "episodes" / f"{name}.json", private)
        rule_path = output / "private" / "rules" / f"yellow-turn-{chosen}.rkt"
        rule_path.parent.mkdir(parents=True, exist_ok=True)
        rule_path.write_text(source, encoding="utf-8")
        complete.append(private)

    max_query_shape = max(
        ([len(pair["input"]), len(pair["input"][0])] for row in complete for pair in row["test"]),
        key=lambda shape: shape[0] * shape[1],
    )
    report = {
        "schema": "fbf36c193fa6-parametric-yellow-turn-report-v1",
        "status": "prototype",
        "task_id": TASK_ID,
        "version": VERSION,
        "parameters": {"yellow_turn": list(ALLOWED_TURNS)},
        "default": {"yellow_turn": DEFAULT_TURN},
        "default_program_exact_canonical": render_program(DEFAULT_TURN) == canonical_program(),
        "complete_episodes": len(complete),
        "pairs_per_episode": {"train": 3, "test": 4},
        "racket_rule_applications": len(settings) * len(grids),
        "all_labels_executed_in_racket": True,
        "all_racket_outputs_match_python_mirror": True,
        "all_demo_only_teaching_checks_pass": all_teaching,
        "input_sampling_independent_of_settings": True,
        "max_query_shape": max_query_shape,
        "runtime_identity": runtime_identity,
        "source_sha256": _source_hashes(root),
        "bounded_adversarial_checks": [
            {
                "surface": "portable canonical/base authority lookup",
                "result": "repaired",
                "detail": "task tests now resolve the selected library root through reviewer_support instead of the copied generator directory and no longer require an unstaged scripts package",
            },
            {
                "surface": "setting-independent teaching and public serialization",
                "result": "repaired",
                "detail": "matched inputs distinguish both turns from two demos; public files now use exact canonical bytes and packet-conformant challenge-<full-visible-byte-SHA-256>.json filenames while ignoring private query answers",
            },
        ],
        "limitations": [
            "Proposed task-local prototype only; the production generator remains 16..23 and clockwise canonical.",
            "The separate parametric grammar extends naturally to 24x24 and 30x30 for stress evidence.",
            "Finite setting/seed evidence is not universal identifiability or measured training gain.",
        ],
    }
    _write_json(output / "report.json", report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-seed", type=int, default=20261024)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    try:
        report = materialize(args.out, base_seed=args.base_seed)
    except Exception as exc:
        print(json.dumps({"status": "error", "error": f"{type(exc).__name__}: {exc}"}))
        return 2
    print(
        json.dumps(
            {
                "status": report["status"],
                "complete_episodes": report["complete_episodes"],
                "racket_rule_applications": report["racket_rule_applications"],
                "out": str(args.out),
            }
        )
    )
    return 0 if report["all_demo_only_teaching_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
