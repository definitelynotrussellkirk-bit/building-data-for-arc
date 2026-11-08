"""Focused regressions for the 2a5919c40197 row-uniformity curriculum."""
from __future__ import annotations

import copy
import importlib.util
import json
import os
from pathlib import Path
import random
import sys

import pytest


# Portable bootstrap: works both in the packet and the staged task-test runtime.
for ancestor in Path(__file__).resolve().parents:
    runtime = ancestor / "shared" / "runtime"
    if (runtime / "reviewer_support.py").is_file():
        sys.path.insert(0, str(runtime))
        break
    if (ancestor / "reviewer_support.py").is_file():
        sys.path.insert(0, str(ancestor))
        break

from reviewer_support import canonical_pairs, canonical_path, find_root  # noqa: E402


TASK_ID = "2a5919c40197"
ROOT = find_root(__file__)
DEFAULT_GENERATOR = ROOT / "generators" / TASK_ID / "generator.py"
if not DEFAULT_GENERATOR.is_file():
    DEFAULT_GENERATOR = (
        ROOT / "puzzle_generators" / "per_puzzle" / TASK_ID / "generator.py"
    )
GENERATOR_PATH = Path(os.environ.get("GENERATOR_UNDER_TEST", DEFAULT_GENERATOR))
SPEC = importlib.util.spec_from_file_location(f"review_{TASK_ID}", GENERATOR_PATH)
assert SPEC is not None and SPEC.loader is not None
GEN = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = GEN
SPEC.loader.exec_module(GEN)


def _pairs() -> list[dict]:
    return canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)


def _profile(grid: list[list[int]]) -> tuple[int, int, int]:
    return len(grid), len(grid[0]), len({value for row in grid for value in row})


def _pair(seed: int, sample_index: int, band: str) -> dict:
    grid = GEN.generate(seed, sample_index, difficulty=band)
    return {"input": grid, "output": GEN.rule_mirror(grid)}


def _selected_solution_path() -> Path:
    relative = Path("data/base/solutions/training/25d8a9c8__2a5919c40197.json")
    for candidate in (ROOT / relative, ROOT / "shared" / relative):
        if candidate.is_file():
            return candidate
    raise AssertionError("selected base solution is missing from the test runtime")


def _canonical_rule() -> str:
    for line in canonical_path(ROOT).read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row["program_solution"]
    raise AssertionError("canonical task row is missing")


def test_rule_pin_mirror_and_strict_hook_match_every_canonical_pair():
    assert GEN.RULE_HASH == "bb6a3cb8ba31"
    pairs = _pairs()
    assert len(pairs) == 5
    for pair in pairs:
        source = copy.deepcopy(pair["input"])
        assert GEN.self_check(source) == []
        assert GEN.strict_canonical_like(source) == []
        assert GEN.rule_mirror(source) == pair["output"]
        assert source == pair["input"]


def test_selected_solution_source_is_exactly_synchronized_to_canonical():
    canonical = _canonical_rule()
    selected = json.loads(_selected_solution_path().read_text(encoding="utf-8"))
    racket = selected["racket_target"]
    assert racket["raw_code"] == canonical
    assert racket["target_code"] == canonical


def test_public_axis_is_small_exact_and_observable_in_every_band():
    assert set(GEN.AXES) == {"scene_profile"}
    assert GEN.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    for band in (None, "easy", "medium", "hard"):
        for index, profile in enumerate(GEN.SCHEDULE_PROFILES):
            requested = {"scene_profile": profile}
            grid = GEN.generate(100 + index, index, difficulty=band, **requested)
            assert GEN.self_check(grid) == []
            assert GEN.observe_overrides(grid) == requested
            if profile == "canonical_anchor":
                assert len(grid) == 3 and len(grid[0]) == 3
                assert _profile(grid) in {(3, 3, 3), (3, 3, 4)}
            else:
                assert 3 <= len(grid) <= 18
                assert 4 <= len(grid[0]) <= 18
                assert GEN.SEMANTIC_WITNESSES["late_change_after_three"](grid)


def test_invalid_unknown_and_retired_overrides_fail_loudly():
    bad_cases = (
        {"typo_axis": 3},
        {"texture": "random"},
        {"uniform_ratio": 0.5},
        {"palette_size": 3},
        {"grid_h": 3},
        {"grid_w": 3},
        {"scene_profile": "unknown"},
        {"scene_profile": 1},
        {"scene_profile": True},
    )
    for overrides in bad_cases:
        with pytest.raises((TypeError, ValueError)):
            GEN.generate(0, 0, **overrides)
    with pytest.raises(ValueError, match="difficulty"):
        GEN.generate(0, 0, difficulty="impossible")


def test_strongest_canonical_shortcut_fits_public_pairs_and_exact_witness_refutes_it():
    name = "inspect only the first three cells of each row"
    rival = GEN.CANONICAL_SHORTCUTS[name]
    for pair in _pairs():
        assert rival(pair["input"]) == pair["output"]

    witness = [
        [1, 1, 1, 2],  # first three equal, but the full row is not uniform
        [3, 3, 3, 3],
        [4, 6, 4, 6],
    ]
    assert GEN.self_check(witness) == []
    intended = GEN.rule_mirror(witness)
    shortcut = rival(witness)
    assert intended[0] == [0, 0, 0, 0]
    assert shortcut[0] == [5, 5, 5, 5]
    assert intended != shortcut
    assert GEN.SEMANTIC_WITNESSES["late_change_after_three"](witness)


def test_alternating_schedule_teaches_anchor_and_width_extension_under_every_rotation():
    assert GEN.EXAMPLES_NEEDED == 3
    assert tuple(GEN.SCHEDULE_PROFILES) == ("canonical_anchor", "width_extension")
    for band_index, band in enumerate(("easy", "medium", "hard")):
        for start in range(12):
            pairs = [
                _pair(20_000 + band_index * 100 + start, start + offset, band)
                for offset in range(4)
            ]
            profiles = [
                GEN.schedule_profile(0, start + offset, difficulty=band)
                for offset in range(4)
            ]
            assert profiles.count("canonical_anchor") == 2
            assert profiles.count("width_extension") == 2
            assert sum(GEN.strict_canonical_like(pair["input"]) == [] for pair in pairs) == 2
            assert sum(
                GEN.SEMANTIC_WITNESSES["late_change_after_three"](pair["input"])
                for pair in pairs
            ) == 2

            # Production order: first three demonstrations, fourth query.
            assert GEN.lesson_identifiable(pairs[:3], pairs[3]) == []
            # Every held-out rotation leaves both an anchor and a rival refuter.
            for query_index in range(4):
                demos = [pair for index, pair in enumerate(pairs) if index != query_index]
                assert GEN.lesson_identifiable(demos, pairs[query_index]) == []
                for name, competitor in GEN.LESSON_COMPETITORS.items():
                    assert any(
                        competitor(demo["input"]) != demo["output"] for demo in demos
                    ), (band, start, query_index, name)


def test_default_distribution_has_exact_canonical_support_and_real_width_witnesses():
    canonical_profiles = {_profile(pair["input"]) for pair in _pairs()}
    assert canonical_profiles == {(3, 3, 3), (3, 3, 4)}
    for band_index, band in enumerate(("easy", "medium", "hard")):
        grids = [
            GEN.generate(30_000 + band_index * 1000 + index, index, difficulty=band)
            for index in range(120)
        ]
        assert all(GEN.self_check(grid) == [] for grid in grids)
        exact = sum(_profile(grid) in canonical_profiles for grid in grids)
        assert exact == 60
        witness_grids = [grid for index, grid in enumerate(grids) if index % 2 == 1]
        assert all(len(grid[0]) >= 4 for grid in witness_grids)
        assert all(GEN.SEMANTIC_WITNESSES["late_change_after_three"](grid) for grid in witness_grids)
        assert all(
            GEN.CANONICAL_SHORTCUTS["inspect only the first three cells of each row"](grid)
            != GEN.rule_mirror(grid)
            for grid in witness_grids
        )
        assert len({json.dumps(grid, separators=(",", ":")) for grid in grids}) >= 115


def test_self_check_rejects_malformed_or_semantically_collapsed_inputs():
    bad = (
        None,
        [],
        [[]],
        [[1, 1, 1], [2, 2]],
        [[10, 1, 1], [2, 2, 2], [3, 4, 3]],
        [[1, 1, 1], [2, 2, 2], [3, 3, 3]],  # no non-uniform row
        [[1, 2, 1], [2, 1, 2], [3, 4, 3]],  # no uniform row
        [[1]],
        [[1, 1], [2, 3]],
    )
    for grid in bad:
        findings = GEN.self_check(grid)
        assert isinstance(findings, list) and findings
        assert all(isinstance(item, str) and item for item in findings)


def test_replay_is_fresh_deterministic_and_global_rng_pure():
    random.seed(1927)
    before = random.getstate()
    first = GEN.generate(42, 7, difficulty="hard")
    after = random.getstate()
    second = GEN.generate(42, 7, difficulty="hard")
    assert before == after
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert first != second
