"""Regressions for the first-object positional shortcut in ae0a295c2271."""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

from reviewer_support import find_root, load_selected_generator

TASK_ID = "ae0a295c2271"
ROOT = find_root(__file__)
GEN, _SOURCE, _SOURCE_SHA256 = load_selected_generator(TASK_ID, root=ROOT)


def _first_role(grid: list[list[int]]) -> str:
    analysis = GEN._analysis(grid)
    first_shape = analysis["shapes"][0]
    return "unique" if analysis["frequencies"][first_shape] == 1 else "repeated"


def _force_first_red(grid: list[list[int]]) -> list[list[int]]:
    output = GEN.rule_mirror(grid)
    first = GEN._analysis(grid)["components"][0]
    for row, col in first:
        output[row][col] = 2
    return output


def _pair(grid: list[list[int]]) -> dict[str, list[list[int]]]:
    return {"input": grid, "output": GEN.rule_mirror(grid)}


def test_every_three_example_window_contains_both_first_object_roles() -> None:
    for band in ("easy", "medium", "hard"):
        for start in range(12):
            roles = {
                _first_role(GEN.generate(4401, start + offset, difficulty=band))
                for offset in range(GEN.EXAMPLES_NEEDED)
            }
            assert roles == {"unique", "repeated"}, (band, start, roles)


def test_every_three_demo_window_refutes_force_first_red_rival() -> None:
    for band in ("easy", "medium", "hard"):
        for start in range(12):
            demos = [
                _pair(GEN.generate(99173, start + offset, difficulty=band))
                for offset in range(GEN.EXAMPLES_NEEDED)
            ]
            assert any(
                _force_first_red(pair["input"]) != pair["output"]
                for pair in demos
            ), (band, start)


def test_retained_repeated_first_counterexample_is_lawful_and_discriminating() -> None:
    path = (
        Path(__file__).resolve().parents[1]
        / "counterexamples/review-9c93d6a9269c5c94-v0001/retained/checks/audit"
        / TASK_ID
        / "counterexample.json"
    )
    record = json.loads(path.read_text(encoding="utf-8"))
    grid = deepcopy(record["input"])
    assert GEN.self_check(grid) == []
    assert _first_role(grid) == "repeated"
    assert GEN.rule_mirror(grid) == record["actual_racket_output"]
    assert _force_first_red(grid) == record["rival_output"]
    assert record["actual_racket_output"] != record["rival_output"]
