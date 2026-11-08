"""Focused regressions for the reviewed 1ea6c72cb7e3 generator."""
from __future__ import annotations

import importlib
import json
import random
from pathlib import Path

MODULE = importlib.import_module(
    "puzzle_generators.per_puzzle.1ea6c72cb7e3.generator"
)
TASK_ID = MODULE.TASK_ID


def _canonical_inputs():
    source = Path(__file__).resolve().parents[3] / "data" / "canonical" / "puzzles.jsonl"
    row = next(
        json.loads(line)
        for line in source.read_text().splitlines()
        if json.loads(line).get("task_id") == TASK_ID
    )
    for split in ("train", "test"):
        for pair in row[split]:
            grid = pair["input"]
            yield [
                [int(char) for char in encoded] if isinstance(encoded, str) else list(encoded)
                for encoded in grid
            ]


def _assert_rejected(grid, label):
    errors = MODULE.self_check(grid)
    assert errors, f"impostor {label!r} was accepted"


def main() -> None:
    assert MODULE.RULE_HASH == "e74d7b3af3b2"

    before_state = random.getstate()
    first = MODULE.generate(41, 7, difficulty="medium")
    assert random.getstate() == before_state, "generator mutated global random state"
    second = MODULE.generate(41, 7, difficulty="medium")
    assert first == second, "deterministic replay mismatch"
    assert first is not second and all(a is not b for a, b in zip(first, second)), "grid rows were aliased"
    assert not MODULE.self_check(first)

    # Full override boundaries and every observable profile must be realizable
    # in every difficulty band, including mixed semantic/dimension overrides.
    for band in ("easy", "medium", "hard"):
        for h in (9, 13):
            for w in (9, 14):
                for count in (3, 4):
                    for profile in MODULE.SCENE_PROFILES:
                        grid = MODULE.generate(
                            1000 + h * 100 + w * 10 + count,
                            19,
                            difficulty=band,
                            grid_h=h,
                            grid_w=w,
                            n_watchers=count,
                            scene_profile=profile,
                        )
                        assert not MODULE.self_check(
                            grid,
                            difficulty=band,
                            meta={
                                "overrides": {
                                    "grid_h": h,
                                    "grid_w": w,
                                    "n_watchers": count,
                                    "scene_profile": profile,
                                }
                            },
                        )
                        observed = MODULE.observe_overrides(grid)
                        assert observed == {"n_watchers": count, "scene_profile": profile}
                        assert len(grid) == h and len(grid[0]) == w

    # The checker describes the canonical support, not just generated samples.
    canonical = list(_canonical_inputs())
    assert len(canonical) == 4
    for index, grid in enumerate(canonical):
        assert not MODULE.self_check(grid), (index, MODULE.self_check(grid))

    generated = MODULE.generate(77, 5, difficulty="hard", scene_profile="split_ladder")

    _assert_rejected([[0] * 9 for _ in range(9)], "uniform background")

    no_walls = [row[:] for row in generated]
    for row in range(len(no_walls)):
        for col in range(len(no_walls[0])):
            if no_walls[row][col] == 5:
                no_walls[row][col] = 0
    _assert_rejected(no_walls, "watchers without walls")

    reserved_marker = [row[:] for row in generated]
    watcher = next(
        (row, col)
        for row in range(len(reserved_marker))
        for col in range(len(reserved_marker[0]))
        if reserved_marker[row][col] not in {0, 5}
    )
    reserved_marker[watcher[0]][watcher[1]] = 8
    _assert_rejected(reserved_marker, "conflict marker used as watcher")

    duplicate_watcher = [row[:] for row in generated]
    watcher_cells = [
        (row, col)
        for row in range(len(duplicate_watcher))
        for col in range(len(duplicate_watcher[0]))
        if duplicate_watcher[row][col] not in {0, 5}
    ]
    duplicate_watcher[watcher_cells[1][0]][watcher_cells[1][1]] = duplicate_watcher[watcher_cells[0][0]][watcher_cells[0][1]]
    _assert_rejected(duplicate_watcher, "duplicate watcher label")

    isolated_wall = [row[:] for row in generated]
    spot = next(
        (row, col)
        for row in range(len(isolated_wall))
        for col in range(len(isolated_wall[0]))
        if isolated_wall[row][col] == 0
        and all(
            not (0 <= row + dr < len(isolated_wall) and 0 <= col + dc < len(isolated_wall[0]))
            or isolated_wall[row + dr][col + dc] != 5
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1))
        )
    )
    isolated_wall[spot[0]][spot[1]] = 5
    _assert_rejected(isolated_wall, "isolated wall pixel")

    too_few_watchers = [row[:] for row in generated]
    for row, col in watcher_cells[2:]:
        too_few_watchers[row][col] = 0
    _assert_rejected(too_few_watchers, "two-watcher shortcut")

    try:
        MODULE.generate(1, 0, unknown_axis=3)
    except ValueError:
        pass
    else:
        raise AssertionError("unknown override was silently accepted")

    print(
        "focused regressions: PASS; 4 canonical inputs accepted, "
        "128 mixed override cases checked, 6 targeted impostors rejected"
    )


def test_generator_contract() -> None:
    main()


if __name__ == "__main__":
    main()
