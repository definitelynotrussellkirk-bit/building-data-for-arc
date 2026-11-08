from __future__ import annotations

import copy
import hashlib
import json
import random
from pathlib import Path

from scripts.generator_module_loader import load_module_from_path


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "60c27b9638fb"
MODULE = load_module_from_path(
    "test_generator_60c27b9638fb_module",
    ROOT / "puzzle_generators/per_puzzle/60c27b9638fb/generator.py",
)
BASE_PATH = (
    ROOT
    / "data/base/solutions/banks/be1bc1d91387/M137__60c27b9638fb.json"
)


def _canonical_row():
    for line in (ROOT / "data/canonical/puzzles.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row
    raise AssertionError("canonical row not found")


def _normalized_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def _blank(height: int, width: int):
    return [[0 for _ in range(width)] for _ in range(height)]


def _paint(grid, cells_and_colors):
    for row, col, color in cells_and_colors:
        grid[row][col] = color
    return grid


def test_rule_hash_and_task_local_authorities_are_synchronized():
    row = _canonical_row()
    base = json.loads(BASE_PATH.read_text())
    authorities = [
        row["program_solution"],
        base["racket_target"]["raw_code"],
        base["racket_target"]["target_code"],
    ]
    assert len(set(authorities)) == 1
    assert {_normalized_hash(source) for source in authorities} == {MODULE.RULE_HASH}
    assert MODULE.RULE_HASH == "73df2925e9f2"


def test_all_canonical_inputs_are_accepted_and_mirror_exact_outputs():
    row = _canonical_row()
    pairs = row["train"] + row["test"]
    assert len(pairs) == 5
    for pair in pairs:
        original = copy.deepcopy(pair["input"])
        assert MODULE.self_check(pair["input"]) == []
        assert MODULE.rule_mirror(pair["input"]) == pair["output"]
        assert MODULE.canonical_profile_signature(pair["input"]) is not None
        assert pair["input"] == original


def test_every_three_demo_one_query_window_supports_the_query():
    query_commands = set()
    for band in ("easy", "medium", "hard"):
        for seed in range(12):
            for start in range(8):
                grids = [
                    MODULE.generate(
                        seed=seed,
                        sample_index=start + offset,
                        difficulty=band,
                    )
                    for offset in range(MODULE.EXAMPLES_NEEDED + 1)
                ]
                commands = [grid[0][0] for grid in grids]
                assert len(set(commands[:3])) == 3
                assert commands[3] == commands[0]
                query_commands.add(commands[3])
                assert all(MODULE.self_check(grid, difficulty=band) == [] for grid in grids)
    assert query_commands == {1, 2, 3, 4}


def test_every_declared_axis_combination_is_exactly_observable():
    for profile in MODULE.PROFILE_NAMES:
        for cmd in (1, 2, 3, 4):
            for palette_size in (2, 4):
                for command_in_payload in (False, True):
                    expected = {
                        "scene_profile": profile,
                        "cmd": cmd,
                        "palette_size": palette_size,
                        "command_in_payload": command_in_payload,
                    }
                    grid = MODULE.generate(
                        seed=431,
                        sample_index=17,
                        difficulty="hard",
                        **expected,
                    )
                    assert MODULE.self_check(
                        grid,
                        difficulty="hard",
                        meta={"overrides": expected},
                    ) == []
                    assert MODULE.observe_overrides(grid) == expected
                    analysis = MODULE._analyze(grid)
                    assert len({repr(x) for x in analysis["outputs"].values()}) == 4


def test_self_check_rejects_targeted_shortcut_impostors():
    # Invalid command absent from every payload color: the teaching grammar is
    # deliberately stricter than the Racket rule's broad else branch.
    invalid_cmd = MODULE.generate(seed=7, sample_index=0, difficulty="easy")
    replacement = next(
        color
        for color in range(5, 10)
        if color not in {value for row in invalid_cmd[1:] for value in row}
    )
    invalid_cmd[0][0] = replacement
    assert any("command" in error for error in MODULE.self_check(invalid_cmd))

    # Payload leaking into the reserved upper/left command margin.
    command_margin = MODULE.generate(seed=8, sample_index=1, difficulty="easy")
    payload = [(r, c) for r, row in enumerate(command_margin) for c, v in enumerate(row)
               if v != 0 and (r, c) != (0, 0)]
    r, c = payload[0]
    color = command_margin[r][c]
    command_margin[r][c] = 0
    command_margin[1][2] = color
    assert any("row 2" in error for error in MODULE.self_check(command_margin))

    # Old self_check accepted this L triomino even though two of the four
    # command transforms collapse to the same answer.
    ambiguous = _blank(8, 9)
    ambiguous[0][0] = 1
    _paint(ambiguous, ((3, 3, 2), (3, 4, 3), (4, 3, 3)))
    errors = MODULE.self_check(ambiguous)
    assert any("linked profiles" in error for error in errors)
    assert any("pairwise-distinct" in error for error in errors)

    # Same canonical mask plus a disconnected answer leak must not be accepted.
    extra_component = MODULE.generate(seed=9, sample_index=0, difficulty="easy")
    extra_component[-1][-1] = next(
        color for color in range(1, 10) if color != extra_component[0][0]
    )
    assert any("linked profiles" in error for error in MODULE.self_check(extra_component))

    # Count-only shortcut: four cells in a solid rectangle on canonical dims.
    rectangle = _blank(8, 9)
    rectangle[0][0] = 1
    _paint(rectangle, ((3, 3, 2), (3, 4, 3), (4, 3, 2), (4, 4, 3)))
    assert any("linked profiles" in error for error in MODULE.self_check(rectangle))


def test_replay_is_deterministic_fresh_and_global_rng_pure():
    random.seed(991827)
    before = random.getstate()
    first = MODULE.generate(seed=55, sample_index=13, difficulty="medium")
    after = random.getstate()
    second = MODULE.generate(seed=55, sample_index=13, difficulty="medium")
    assert before == after
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = 9
    third = MODULE.generate(seed=55, sample_index=13, difficulty="medium")
    assert third == second


def test_unknown_overrides_reject_loudly():
    try:
        MODULE.generate(seed=1, sample_index=0, mystery_axis=1)
    except ValueError as exc:
        assert "unknown override" in str(exc)
    else:
        raise AssertionError("unknown override was silently accepted")
