from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import random
import sys
from pathlib import Path

import pytest

from reviewer_support import find_root

TASK_DIR = Path(__file__).resolve().parents[1]
REPO = find_root(__file__)
sys.path.insert(0, str(REPO / "shared" / "runtime"))

SPEC = importlib.util.spec_from_file_location(
    "generator_26f02d922ca0_under_test", TASK_DIR / "generator.py"
)
assert SPEC and SPEC.loader
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def _canonical_row() -> dict:
    path = REPO / "shared" / "data" / "canonical" / "puzzles.jsonl"
    for line in path.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == GEN.TASK_ID:
            return row
    raise AssertionError("canonical row not found")


def _canonical_pairs() -> list[dict]:
    row = _canonical_row()
    pairs: list[dict] = []
    for split in ("train", "test"):
        value = row.get(split, [])
        pairs.extend(value if isinstance(value, list) else [value])
    return pairs


def test_rule_hash_and_python_oracle_match_all_canonical_pairs():
    row = _canonical_row()
    normalized = " ".join(row["program_solution"].split())
    assert hashlib.sha256(normalized.encode()).hexdigest()[:12] == GEN.RULE_HASH
    for pair in _canonical_pairs():
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]


def test_generation_is_deterministic_fresh_and_global_rng_pure():
    random.seed(271828)
    before = random.getstate()
    first = GEN.generate(117, 6, difficulty="hard")
    assert random.getstate() == before
    second = GEN.generate(117, 6, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 7
    assert second == GEN.generate(117, 6, difficulty="hard")


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_exact_dimension_overrides_work_at_all_boundaries_and_profiles(difficulty):
    for sample_index in range(4):
        for grid_h, grid_w in ((9, 12), (9, 24), (18, 12), (18, 24)):
            expected = {"grid_h": grid_h, "grid_w": grid_w}
            grid = GEN.generate(
                19,
                sample_index,
                difficulty=difficulty,
                grid_h=grid_h,
                grid_w=grid_w,
            )
            assert GEN.observe_overrides(grid) == expected
            assert GEN.self_check(grid, difficulty=difficulty, meta={"overrides": expected}) == []


def test_unknown_override_is_rejected_loudly():
    with pytest.raises((KeyError, TypeError, ValueError), match="unknown override"):
        GEN.generate(3, 0, palette_kind="warm")


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_four_consecutive_profiles_cover_every_named_semantic_witness(difficulty):
    assert len(GEN.SCHEDULE_PROFILES) == 4
    grids = [GEN.generate(42, index, difficulty=difficulty) for index in range(4)]
    assert {
        GEN.schedule_profile(42, index, difficulty) for index in range(4)
    } == set(GEN.SCHEDULE_PROFILES)
    for grid in grids:
        assert GEN.self_check(grid) == []
        assert set(GEN.rule_mirror(grid)[0]) == {0, 8}
    hits = {
        name: any(predicate(grid) for grid in grids)
        for name, predicate in GEN.SEMANTIC_WITNESSES.items()
    }
    assert hits and all(hits.values()), hits
    demos = [
        {"input": grid, "output": GEN.rule_mirror(grid)}
        for grid in grids
    ]
    query_grid = GEN.generate(42, 4, difficulty=difficulty)
    assert GEN.lesson_identifiable(
        demos,
        {"input": query_grid, "output": GEN.rule_mirror(query_grid)},
    ) == []


def test_canonical_profile_is_emitted_but_refutes_color_and_order_shortcuts():
    grid = GEN.generate(91, 0, difficulty="hard")
    assert (len(grid), len(grid[0]), len({value for row in grid for value in row})) == (
        9,
        16,
        6,
    )
    assert GEN.strict_canonical_like(grid) == []
    truth = GEN.rule_mirror(grid)
    assert GEN.CANONICAL_SHORTCUTS["colors_3_and_4_are_matches"](grid) != truth
    assert GEN.CANONICAL_SHORTCUTS["first_two_candidates_match"](grid) != truth
    assert GEN.SEMANTIC_WITNESSES["color_role_conflict"](grid)
    assert GEN.SEMANTIC_WITNESSES["nonprefix_match_pattern"](grid)


def test_mirror_profile_requires_horizontal_mirror_equivalence():
    grid = GEN.generate(91, 2, difficulty="medium")
    assert GEN.SEMANTIC_WITNESSES["mirror_only_match"](grid)
    assert GEN.SEMANTIC_RIVALS["exact_key_only"](grid) != GEN.rule_mirror(grid)


def test_variable_candidate_profile_refutes_fixed_canonical_vector():
    grid = GEN.generate(91, 3, difficulty="medium")
    analysis = GEN._analysis(grid)
    assert analysis["errors"] == []
    assert len(analysis["candidates"]) != 4
    assert GEN.SEMANTIC_WITNESSES["variable_candidate_count"](grid)
    assert GEN.CANONICAL_SHORTCUTS["fixed_canonical_vector"](grid) != GEN.rule_mirror(grid)


def test_each_witness_really_refutes_every_rival_it_claims():
    grids = [GEN.generate(7, index, difficulty="medium") for index in range(4)]
    for witness_name, rival_names in GEN.WITNESS_RIVALS.items():
        witness_grids = [
            grid for grid in grids if GEN.SEMANTIC_WITNESSES[witness_name](grid)
        ]
        assert witness_grids, witness_name
        for rival_name in rival_names:
            assert any(
                GEN.SEMANTIC_RIVALS[rival_name](grid) != GEN.rule_mirror(grid)
                for grid in witness_grids
            ), (witness_name, rival_name)


def test_declared_canonical_shortcuts_fit_every_real_canonical_pair():
    for name, shortcut in GEN.CANONICAL_SHORTCUTS.items():
        assert all(shortcut(pair["input"]) == pair["output"] for pair in _canonical_pairs()), name


def test_lesson_identifiable_detects_a_surviving_wrong_rule():
    grids = [GEN.generate(11, index, difficulty="easy") for index in range(4)]
    demos = [
        {"input": grid, "output": GEN.rule_mirror(grid)}
        for grid in grids
    ]
    query_grid = GEN.generate(11, 4, difficulty="easy")
    malformed = copy.deepcopy(demos)
    malformed[0]["output"] = GEN.SEMANTIC_RIVALS["first_two_candidates_match"](
        malformed[0]["input"]
    )
    reasons = GEN.lesson_identifiable(
        malformed,
        {"input": query_grid, "output": GEN.rule_mirror(query_grid)},
    )
    assert reasons
    assert any("demo 0" in reason for reason in reasons)


def test_review_probe_emits_machine_checkable_counterexamples():
    import subprocess

    probe = TASK_DIR / "workspace" / "review_probe.py"
    completed = subprocess.run(
        [
            sys.executable,
            str(probe),
            "--seed",
            "91",
            "--difficulty",
            "hard",
        ],
        cwd=REPO,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    report = json.loads(completed.stdout)
    assert report["task_id"] == GEN.TASK_ID
    assert report["authority"]["rule_hash"] == GEN.RULE_HASH
    assert report["canonical_shortcuts_fit_all_pairs"] == {
        name: True for name in GEN.CANONICAL_SHORTCUTS
    }
    assert {example["profile"] for example in report["examples"]} == set(
        GEN.SCHEDULE_PROFILES
    )
    assert all(example["oracle_output"] == GEN.rule_mirror(example["grid"])
               for example in report["examples"])
    for rival_name in GEN.SEMANTIC_RIVALS:
        assert any(
            example["rivals"][rival_name]["disagrees"]
            for example in report["examples"]
        ), rival_name
