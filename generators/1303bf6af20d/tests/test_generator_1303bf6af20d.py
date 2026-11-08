from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
from pathlib import Path

import pytest

from arc_repl.racket_bridge import RacketBridge
from scripts.rule_smoke import rule_application

ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "1303bf6af20d"
GEN = importlib.import_module(
    f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
)
BASE_PATH = ROOT / "data/base/solutions/custom/7bb4cfc1__1303bf6af20d.json"


def _canonical_row() -> dict:
    for row in map(json.loads, (ROOT / "data/canonical/puzzles.jsonl").read_text().splitlines()):
        if row.get("task_id") == TASK_ID:
            return row
    raise AssertionError("canonical row missing")


def _normalized_rule_hash(rule: str) -> str:
    return hashlib.sha256(" ".join(rule.split()).encode()).hexdigest()[:12]


def test_rule_hash_authorities_and_all_canonical_inputs() -> None:
    row = _canonical_row()
    base = json.loads(BASE_PATH.read_text())
    rule = row["program_solution"]
    assert _normalized_rule_hash(rule) == GEN.RULE_HASH
    assert base["racket_target"]["raw_code"] == rule
    assert base["racket_target"]["target_code"] == rule

    bridge = RacketBridge()
    pairs = [*row["train"], *row["test"]]
    assert len(pairs) == 4
    for pair in pairs:
        before = copy.deepcopy(pair["input"])
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        expected = pair.get("output", GEN.rule_mirror(pair["input"]))
        actual = bridge.eval_text(rule_application(rule, pair["input"]))
        assert actual == expected
        assert pair["input"] == before


def test_regression_declared_override_boundaries_are_exact_or_loud() -> None:
    successful_cases = [
        {"grid_h": 8},
        {"grid_h": 16},
        {"grid_w": 8},
        {"grid_w": 16},
        {"template_size": 4},
        {"template_size": 6},
        {"n_blobs": 2},
        {"n_blobs": 6},
        {"grid_h": 8, "grid_w": 8, "template_size": 4, "n_blobs": 2},
        {"grid_h": 16, "grid_w": 16, "template_size": 6, "n_blobs": 6},
    ]
    for overrides in successful_cases:
        grid = GEN.generate(991, 17, difficulty="medium", **overrides)
        observed = GEN.observe_overrides(grid)
        assert GEN.self_check(grid) == []
        for key, value in overrides.items():
            assert observed[key] == value

    with pytest.raises(ValueError, match="unsupported override"):
        GEN.generate(991, 17, difficulty="easy", divider_row=6)
    with pytest.raises(ValueError):
        GEN.generate(991, 17, difficulty="easy", grid_h=8, grid_w=8, n_blobs=6)

def test_regression_self_check_rejects_targeted_impostors() -> None:
    valid = GEN.generate(717, 5, difficulty="medium")
    info = GEN._analysis(valid)
    assert info["errors"] == []

    impostors: dict[str, list[list[int]]] = {
        "all_background": [[0] * 9 for _ in range(8)],
        "missing_divider": [
            [0 if value == 9 else value for value in row]
            for row in valid
        ],
    }

    no_match = copy.deepcopy(valid)
    for blob in info["matching"]:
        for r, c in blob["cells"]:
            no_match[r][c] = 0
    impostors["no_matching_object"] = no_match

    no_nonmatch = copy.deepcopy(valid)
    for blob in info["nonmatching"]:
        for r, c in blob["cells"]:
            no_nonmatch[r][c] = 0
    impostors["no_nonmatching_object"] = no_nonmatch

    second_template = copy.deepcopy(valid)
    divider = info["divider_row"]
    placed = False
    for r in range(divider):
        for c in range(len(second_template[0])):
            if second_template[r][c] == 0:
                second_template[r][c] = 4
                placed = True
                break
        if placed:
            break
    impostors["disconnected_second_template"] = second_template

    for name, grid in impostors.items():
        assert GEN.self_check(grid), name


def test_determinism_fresh_returns_and_global_rng_purity() -> None:
    random.seed(8675309)
    state = random.getstate()
    first = GEN.generate(1234, 9, difficulty="hard")
    assert random.getstate() == state
    second = GEN.generate(1234, 9, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 0
    assert second == GEN.generate(1234, 9, difficulty="hard")


def test_all_bands_cover_semantic_branches_and_canonical_schedule() -> None:
    for band in ("easy", "medium", "hard"):
        strict_hits = edge_hits = interior_hits = 0
        observed_sizes: set[int] = set()
        observed_counts: set[int] = set()
        for sample_index in range(48):
            grid = GEN.generate(4000 + sample_index, sample_index, difficulty=band)
            assert GEN.self_check(grid) == []
            observed = GEN.observe_overrides(grid)
            observed_sizes.add(observed["template_size"])
            observed_counts.add(observed["n_blobs"])
            strict_hits += int(GEN.strict_canonical_like(grid) == [])
            edge_hits += int(GEN.SEMANTIC_WITNESSES["template_on_side_edge"](grid))
            interior_hits += int(GEN.SEMANTIC_WITNESSES["template_interior_horizontally"](grid))
            assert GEN.SEMANTIC_WITNESSES["rotation_match_present"](grid)
            assert GEN.SEMANTIC_WITNESSES["preserved_nonmatch_present"](grid)
            if sample_index % 4:
                assert GEN.SEMANTIC_WITNESSES["nontrivially_rotated_match"](grid)
                assert GEN.SEMANTIC_WITNESSES["same_size_count_shortcut_rebuttal"](grid)
                assert GEN.SEMANTIC_WITNESSES["reflection_only_distractor"](grid)
                assert GEN._recolor_all_blobs(grid) != GEN.rule_mirror(grid)
                assert GEN._recolor_same_cell_count(grid) != GEN.rule_mirror(grid)
                assert GEN._recolor_exact_orientation(grid) != GEN.rule_mirror(grid)
                assert GEN._recolor_rotations_or_reflections(grid) != GEN.rule_mirror(grid)
        assert strict_hits == 12
        assert edge_hits > 0 and interior_hits > 0
        assert observed_sizes
        assert observed_counts


def test_materialized_lesson_is_identifiable() -> None:
    pairs = []
    for sample_index in range(5):
        grid = GEN.generate(8800 + sample_index, sample_index + 1, difficulty=("easy", "medium", "hard")[sample_index % 3])
        pairs.append({"input": grid, "output": GEN.rule_mirror(grid)})
    assert GEN.lesson_identifiable(pairs[:4], pairs[4]) == []
