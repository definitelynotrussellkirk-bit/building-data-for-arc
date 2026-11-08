"""Bounded visible-lesson shortcut audit for the farthest-relay family.

The CLI consumes a native qualification plus its sibling execution receipt, so
all intended labels were already replayed through protected Racket.  Rivals are
pure, explicit algorithms over the same visible grids.  A rival that fits every
demonstration but differs on a query is reported as a concrete teaching hole;
runtime or malformed-data errors fail closed rather than counting as refutation.
"""
from __future__ import annotations

import argparse
from collections import deque
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any, Callable


HERE = Path(__file__).resolve().parent
TASK_ID = "9199b47fab1e"
CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
COLORS = (3, 4, 5)


def _load_prototype():
    path = HERE / "prototype.py"
    name = "_arc_9199b47fab1e_audit_prototype_" + hashlib.sha256(str(path).encode()).hexdigest()[:16]
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load exact prototype {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if Path(module.__file__).resolve() != path.resolve():
        raise ImportError("prototype import escaped its task home")
    return module


PROTOTYPE = _load_prototype()


def _grid(value: Any) -> list[list[int]]:
    if (
        type(value) is not list
        or not value
        or type(value[0]) is not list
        or not value[0]
        or any(
            type(row) is not list
            or len(row) != len(value[0])
            or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
            for row in value
        )
    ):
        raise ValueError("expected a rectangular exact-integer ARC grid")
    return copy.deepcopy(value)


def _sources(grid: list[list[int]]) -> list[tuple[int, int]]:
    result = [
        (row, column)
        for row, values in enumerate(grid)
        for column, value in enumerate(values)
        if value == 2
    ]
    if not result:
        raise ValueError("rival input has no color-2 source")
    return result


def _distances(
    grid: list[list[int]],
    sources: list[tuple[int, int]],
    traversable: Callable[[int], bool] = lambda value: value in (0, 2),
) -> dict[tuple[int, int], int]:
    height, width = len(grid), len(grid[0])
    distance = {point: 0 for point in sources}
    queue = deque(sources)
    while queue:
        row, column = queue.popleft()
        for dr, dc in CARDINAL:
            nr, nc = row + dr, column + dc
            if (
                0 <= nr < height
                and 0 <= nc < width
                and (nr, nc) not in distance
                and traversable(grid[nr][nc])
            ):
                distance[(nr, nc)] = distance[(row, column)] + 1
                queue.append((nr, nc))
    return distance


def _paint(grid: list[list[int]], distances: dict[tuple[int, int], int]) -> list[list[int]]:
    output = _grid(grid)
    for (row, column), distance in distances.items():
        output[row][column] = COLORS[distance % 3]
    return output


def first_seed_relay(grid: list[list[int]]) -> list[list[int]]:
    grid = _grid(grid)
    return _paint(grid, _distances(grid, [_sources(grid)[0]]))


def last_seed_relay(grid: list[list[int]]) -> list[list[int]]:
    grid = _grid(grid)
    return _paint(grid, _distances(grid, [_sources(grid)[-1]]))


def nearest_primary_relay(grid: list[list[int]]) -> list[list[int]]:
    """Wrong intermediate: row-major first cell one BFS step from any source."""
    grid = _grid(grid)
    primary = _distances(grid, _sources(grid))
    positive = [point for point, distance in primary.items() if distance > 0]
    relay = min(positive, key=lambda point: (primary[point], point)) if positive else min(primary)
    return _paint(grid, _distances(grid, [relay]))


def wall_ignoring_primary(grid: list[list[int]]) -> list[list[int]]:
    """Preserve walls, but color every 0/2 by unobstructed Manhattan distance."""
    grid = _grid(grid)
    sources = _sources(grid)
    output = copy.deepcopy(grid)
    for row, values in enumerate(grid):
        for column, value in enumerate(values):
            if value in (0, 2):
                distance = min(abs(row - sr) + abs(column - sc) for sr, sc in sources)
                output[row][column] = COLORS[distance % 3]
    return output


def first_seed_primary(grid: list[list[int]]) -> list[list[int]]:
    return first_seed_relay(grid)


def last_seed_primary(grid: list[list[int]]) -> list[list[int]]:
    return last_seed_relay(grid)


def color_8_only_primary(grid: list[list[int]]) -> list[list[int]]:
    grid = _grid(grid)
    return _paint(grid, _distances(grid, _sources(grid), lambda value: value != 8))


def manhattan_farthest_relay(grid: list[list[int]]) -> list[list[int]]:
    """Wrong A: choose a farthest 0/2 cell by Manhattan distance through walls."""
    grid = _grid(grid)
    sources = _sources(grid)
    candidates = [
        (row, column)
        for row, values in enumerate(grid)
        for column, value in enumerate(values)
        if value in (0, 2)
    ]
    score = lambda point: min(abs(point[0] - sr) + abs(point[1] - sc) for sr, sc in sources)
    maximum = max(map(score, candidates))
    relay = min(point for point in candidates if score(point) == maximum)
    return _paint(grid, _distances(grid, [relay]))


def _rivals(settings: dict[str, Any]) -> dict[str, Callable[[list[list[int]]], list[list[int]]]]:
    normalized = PROTOTYPE.normalize_settings(settings)
    mode = normalized["source_mode"]
    if mode == "original_seeds":
        return {
            "other_setting_farthest_relay": lambda grid: PROTOTYPE.solve_python(
                grid, {"source_mode": "farthest_relay"}
            ),
            "first_seed_only": first_seed_primary,
            "last_seed_only": last_seed_primary,
            "wall_ignoring_manhattan": wall_ignoring_primary,
            "color_8_only_barrier": color_8_only_primary,
        }
    return {
        "other_setting_original_seeds": lambda grid: PROTOTYPE.solve_python(
            grid, {"source_mode": "original_seeds"}
        ),
        "first_seed_relay": first_seed_relay,
        "last_seed_relay": last_seed_relay,
        "nearest_primary_relay": nearest_primary_relay,
        "manhattan_farthest_relay": manhattan_farthest_relay,
    }


def _difference(expected: list[list[int]], actual: list[list[int]]) -> dict[str, Any] | None:
    if expected == actual:
        return None
    for row in range(min(len(expected), len(actual))):
        for column in range(min(len(expected[0]), len(actual[0]))):
            if expected[row][column] != actual[row][column]:
                return {
                    "row": row,
                    "column": column,
                    "expected": expected[row][column],
                    "rival": actual[row][column],
                }
    return {
        "expected_shape": [len(expected), len(expected[0])],
        "rival_shape": [len(actual), len(actual[0])],
    }


def audit_episode(episode: dict[str, Any], settings: dict[str, Any]) -> dict[str, Any]:
    if type(episode) is not dict:
        raise ValueError("episode must be an object")
    for split in ("train", "test"):
        if type(episode.get(split)) is not list or not episode[split]:
            raise ValueError(f"episode requires a nonempty {split} list")
        for pair in episode[split]:
            if type(pair) is not dict or set(pair) < {"input", "output"}:
                raise ValueError("each pair needs input and output")
            _grid(pair["input"])
            _grid(pair["output"])

    rows = []
    for name, solver in _rivals(settings).items():
        demo_differences = []
        query_differences = []
        for index, pair in enumerate(episode["train"]):
            actual = _grid(solver(pair["input"]))
            difference = _difference(pair["output"], actual)
            if difference is not None:
                demo_differences.append({"index": index, **difference})
        if not demo_differences:
            for index, pair in enumerate(episode["test"]):
                actual = _grid(solver(pair["input"]))
                difference = _difference(pair["output"], actual)
                if difference is not None:
                    query_differences.append({"index": index, **difference})
        rows.append(
            {
                "name": name,
                "demo_survives": not demo_differences,
                "demo_differences": demo_differences,
                "query_differences": query_differences,
                "ambiguous": not demo_differences and bool(query_differences),
                "equivalent_on_retained_pairs": not demo_differences and not query_differences,
            }
        )
    return {
        "settings": copy.deepcopy(settings),
        "rival_count": len(rows),
        "rivals": rows,
        "demo_survivors": [row["name"] for row in rows if row["demo_survives"]],
        "ambiguous_rivals": [row["name"] for row in rows if row["ambiguous"]],
        "equivalent_survivors": [
            row["name"] for row in rows if row["equivalent_on_retained_pairs"]
        ],
    }


def audit_qualification(qualification: dict[str, Any], execution: dict[str, Any]) -> dict[str, Any]:
    if (
        qualification.get("schema") != "arcpuzzles-parametric-qualification-v1"
        or qualification.get("status") != "qualified"
        or qualification.get("task_id") != TASK_ID
    ):
        raise ValueError("expected a qualified native receipt for this task")
    racket = execution.get("racket", {})
    if racket.get("backend") != "racket" or racket.get("protected") is not True:
        raise ValueError("self-audit requires protected-Racket qualification labels")
    episodes = execution.get("episodes")
    if type(episodes) is not list or not episodes:
        raise ValueError("qualification execution has no episodes")
    rows = [audit_episode(episode, episode["settings"]) for episode in episodes]
    ambiguous = [
        {"episode_index": index, "settings": row["settings"], "rivals": row["ambiguous_rivals"]}
        for index, row in enumerate(rows)
        if row["ambiguous_rivals"]
    ]
    survivors = [
        {"episode_index": index, "settings": row["settings"], "rivals": row["demo_survivors"]}
        for index, row in enumerate(rows)
        if row["demo_survivors"]
    ]
    return {
        "schema": "arcpuzzles-9199b47fab1e-finite-self-audit-v1",
        "task_id": TASK_ID,
        "status": "pass" if not survivors else "finite_rival_survivors",
        "source_binding": qualification["source_binding"],
        "racket": {"backend": "racket", "protected": True},
        "scope": "native qualification episodes; five declared plausible rivals per setting",
        "limits": "finite rival elimination does not prove universal program uniqueness",
        "episodes": rows,
        "ambiguous_findings": ambiguous,
        "demo_survivor_findings": survivors,
        "counts": {
            "episodes": len(rows),
            "rivals": sum(row["rival_count"] for row in rows),
            "qualification_racket_evaluations": execution.get("racket_evaluations"),
        },
    }


def _write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as handle:
        json.dump(value, handle, sort_keys=True, indent=2)
        handle.write("\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--qualification", required=True, type=Path)
    parser.add_argument("--execution", type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args(argv)
    qualification = json.loads(args.qualification.read_text())
    execution_path = args.execution or args.qualification.with_name("execution.json")
    execution = json.loads(execution_path.read_text())
    report = audit_qualification(qualification, execution)
    _write(args.out, report)
    print(json.dumps({"status": report["status"], **report["counts"]}, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
