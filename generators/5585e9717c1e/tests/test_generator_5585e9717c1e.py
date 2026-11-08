"""Focused regressions for the reviewed 5585e9717c1e generator."""
from __future__ import annotations

import importlib
import json
import random
from pathlib import Path

MODULE = importlib.import_module(
    "puzzle_generators.per_puzzle.5585e9717c1e.generator"
)
TASK_ID = MODULE.TASK_ID


def _canonical_inputs():
    source = Path(__file__).resolve().parents[1] / "data" / "canonical" / "puzzles.jsonl"
    row = next(
        json.loads(line)
        for line in source.read_text().splitlines()
        if json.loads(line).get("task_id") == TASK_ID
    )
    pairs = list(row.get("train", []))
    test = row.get("test", [])
    pairs.extend(test if isinstance(test, list) else [test])
    for pair in pairs:
        yield [
            [int(char) for char in encoded] if isinstance(encoded, str) else list(encoded)
            for encoded in pair["input"]
        ]


def _mutate_without_changing_original(grid, fn):
    changed = [row[:] for row in grid]
    fn(changed)
    return changed


def main() -> None:
    assert MODULE.RULE_HASH == "fc44e914eb1c"

    before_state = random.getstate()
    first = MODULE.generate(41, 7, difficulty="medium")
    second = MODULE.generate(41, 7, difficulty="medium")
    assert random.getstate() == before_state
    assert first == second
    assert first is not second and all(a is not b for a, b in zip(first, second))
    assert not MODULE.self_check(first)

    canonical = list(_canonical_inputs())
    assert len(canonical) == 3
    for index, grid in enumerate(canonical):
        assert not MODULE.self_check(grid), (index, MODULE.self_check(grid))
        assert not MODULE.strict_canonical_like(grid)

    # Every exact override is recoverable. Incompatible n/index tuples reject
    # explicitly rather than silently clamping the requested match position.
    for band in ("easy", "medium", "hard"):
        for match_index in (0, 1):
            for family in ("a11_h83", "a22_h1471", "a36_h191151"):
                for color in (1, 8):
                    grid = MODULE.generate(
                        1000 + match_index * 10 + color,
                        5,
                        difficulty=band,
                        match_index=match_index,
                        target_family=family,
                        shape_color=color,
                    )
                    assert not MODULE.self_check(grid)
                    assert MODULE.observe_overrides(grid) == {
                        "match_index": match_index,
                        "target_family": family,
                        "shape_color": color,
                    }
                    assert MODULE._solve_histogram(grid) != MODULE._solve_exact_mask(grid)

    try:
        MODULE.generate(1, 0, typo_axis=3)
    except ValueError:
        pass
    else:
        raise AssertionError("unknown override was silently accepted")

    # Structural mutation witnesses: each was accepted by the pre-repair
    # self_check, which only looked for a full color-9 column.
    all_background = [[0] * 39 for _ in range(9)]
    assert MODULE.self_check(all_background)

    broken_divider = _mutate_without_changing_original(
        first, lambda grid: grid.__setitem__(4, grid[4][:9] + [0] + grid[4][10:])
    )
    assert MODULE.self_check(broken_divider)

    duplicate_key = _mutate_without_changing_original(
        first, lambda grid: grid[0].__setitem__(10, grid[0][0])
    )
    assert MODULE.self_check(duplicate_key)

    ambiguous = [row[:] for row in first]
    parsed = MODULE._parsed(ambiguous)
    assert parsed is not None
    target = parsed["matches"][0]
    other = 0 if target != 0 else 1
    panel_starts = [0, 10, 20, 30, 40]
    target_start = panel_starts[target]
    other_start = panel_starts[other]
    for r in range(len(ambiguous)):
        for c in range(9):
            if (r, c) != (0, 0):
                ambiguous[r][other_start + c] = ambiguous[r][target_start + c]
    assert MODULE.self_check(ambiguous)

    print(
        "focused regressions: PASS; 3 canonical inputs accepted, 36 exact "
        "override cases checked, and 4 pre-repair structural impostors rejected"
    )


def test_generator_contract() -> None:
    main()


if __name__ == "__main__":
    main()
