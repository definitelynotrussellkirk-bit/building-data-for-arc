"""Focused regressions for the reviewed 678b4a951150 generator."""
from __future__ import annotations

import copy
import importlib
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

GEN = importlib.import_module(
    "puzzle_generators.per_puzzle.678b4a951150.generator"
)


def _canonical_pairs():
    source = Path(__file__).resolve().parents[3] / "data" / "canonical" / "puzzles.jsonl"
    for line in source.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") != GEN.TASK_ID:
            continue
        test = row["test"] if isinstance(row["test"], list) else [row["test"]]
        return [*row["train"], *test]
    raise AssertionError("canonical task row not found")


def _must_reject(grid, label):
    errors = GEN.self_check(grid)
    assert errors, f"self_check accepted targeted impostor: {label}"


def main() -> None:
    assert GEN.RULE_HASH == "f5f03a3a484b"

    # Canonical ownership and Python/Racket-rule parity mirror.
    pairs = _canonical_pairs()
    assert len(pairs) == 5
    for index, pair in enumerate(pairs):
        assert not GEN.self_check(pair["input"]), (index, GEN.self_check(pair["input"]))
        assert GEN.rule_mirror(pair["input"]) == pair["output"], index

    # Determinism, fresh return values, and global-RNG purity.
    state = random.getstate()
    first = GEN.generate(41, 7, difficulty="medium")
    second = GEN.generate(41, 7, difficulty="medium")
    assert first == second and first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9
    assert GEN.generate(41, 7, difficulty="medium") == second
    assert random.getstate() == state

    # Exact boundary overrides work in every band and are observable from the grid.
    override_cases = 0
    for band in ("easy", "medium", "hard"):
        for height in (8, 10):
            for width in (11, 14):
                for targets in (4, 8):
                    for sixes in (3, 4):
                        grid = GEN.generate(
                            1000 + override_cases,
                            override_cases % 4,
                            difficulty=band,
                            grid_h=height,
                            grid_w=width,
                            n_targets=targets,
                            n_sixes=sixes,
                        )
                        assert not GEN.self_check(grid)
                        assert GEN.observe_overrides(grid) == {
                            "grid_h": height,
                            "grid_w": width,
                            "n_targets": targets,
                            "n_sixes": sixes,
                        }
                        override_cases += 1

    try:
        GEN.generate(1, 0, misspelled_axis=3)
    except ValueError:
        pass
    else:
        raise AssertionError("unknown override was silently accepted")

    # Four consecutive scheduled examples contain every decisive refuter.
    demos = []
    for sample_index in range(4):
        grid = GEN.generate(71, sample_index, difficulty="hard")
        demos.append({"input": grid, "output": GEN.rule_mirror(grid)})
    query_grid = GEN.generate(71, 4, difficulty="hard")
    query = {"input": query_grid, "output": GEN.rule_mirror(query_grid)}
    assert not GEN.lesson_identifiable(demos, query)
    for name, rival in GEN.LESSON_COMPETITORS.items():
        assert any(rival(pair["input"]) != pair["output"] for pair in demos), name

    # Mutation-sensitive malformed and rule-hiding scenes.
    base = GEN.generate(23, 2, difficulty="easy")

    no_targets = copy.deepcopy(base)
    for row, col in GEN._target_centers(no_targets):
        no_targets[row][col - 1] = 0
    _must_reject(no_targets, "all horizontal targets removed")

    missing_sixes = copy.deepcopy(base)
    for row in range(len(missing_sixes)):
        for col in range(len(missing_sixes[0])):
            if missing_sixes[row][col] == 6:
                missing_sixes[row][col] = 0
    _must_reject(missing_sixes, "color-6 distractors removed")

    output_color_in_input = copy.deepcopy(base)
    output_color_in_input[0][0] = 3
    _must_reject(output_color_in_input, "output-only color 3 injected")

    target_only = [[0] * 14 for _ in range(8)]
    for row, start in enumerate((1, 3, 5, 7)):
        target_only[row][start] = 7
        target_only[row][start + 2] = 7
    target_only[4][1] = target_only[5][2] = target_only[6][3] = 6
    _must_reject(target_only, "every orange cell is a target endpoint")

    print(
        "focused regressions: PASS; 5 canonical pairs, "
        f"{override_cases} boundary override cases, 6 named rivals, "
        "4 targeted impostors"
    )


def test_generator_contract() -> None:
    main()


if __name__ == "__main__":
    main()
