from __future__ import annotations

import copy
import importlib.util
import json
import os
from pathlib import Path
import random
import sys

import pytest

# Portable bootstrap: works in the packet and in arcpuzzles' staged runtime.
for ancestor in Path(__file__).resolve().parents:
    runtime = ancestor / "shared" / "runtime"
    if (runtime / "reviewer_support.py").is_file():
        sys.path.insert(0, str(runtime))
        break
    if (ancestor / "reviewer_support.py").is_file():
        sys.path.insert(0, str(ancestor))
        break

from reviewer_support import canonical_path, find_root  # noqa: E402

TASK_ID = "ffd3a33c5687"
ROOT = find_root(__file__)
DEFAULT_GENERATOR = ROOT / "generators" / TASK_ID / "generator.py"
if not DEFAULT_GENERATOR.is_file():
    DEFAULT_GENERATOR = ROOT / "puzzle_generators" / "per_puzzle" / TASK_ID / "generator.py"
GENERATOR_PATH = Path(os.environ.get("GENERATOR_UNDER_TEST", DEFAULT_GENERATOR))
SPEC = importlib.util.spec_from_file_location(f"review_{TASK_ID}", GENERATOR_PATH)
assert SPEC is not None and SPEC.loader is not None
gen = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = gen
SPEC.loader.exec_module(gen)

WORKSPACE = GENERATOR_PATH.parent / "workspace"
PROBE_SPEC = importlib.util.spec_from_file_location(
    f"reference_probe_{TASK_ID}", WORKSPACE / "reference_probe.py"
)
assert PROBE_SPEC is not None and PROBE_SPEC.loader is not None
probe = importlib.util.module_from_spec(PROBE_SPEC)
sys.modules[PROBE_SPEC.name] = probe
PROBE_SPEC.loader.exec_module(probe)


def _canonical_train_pairs() -> list[dict]:
    for line in canonical_path(ROOT).read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return [pair for pair in row["train"] if pair.get("output") is not None]
    raise AssertionError("canonical task is missing")


def _demo(seed: int, index: int, band: str = "medium") -> dict:
    grid = gen.generate(seed, index, difficulty=band)
    return {"input": grid, "output": gen.rule_mirror(grid)}


def test_rule_pin_and_canonical_pairs_match_independent_oracle():
    assert gen.RULE_HASH == "4276b16a10bb"
    assert tuple(gen.SCHEDULE_PROFILES) == (0, 1, 2, 3, 4)
    pairs = _canonical_train_pairs()
    assert len(pairs) == 4
    for pair in pairs:
        source = copy.deepcopy(pair["input"])
        assert gen.self_check(source) == []
        assert gen.strict_canonical_like(source) == []
        assert probe.left_priority_output(source) == pair["output"]
        assert gen.rule_mirror(source) == pair["output"]
        assert source == pair["input"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "requested",
    [
        {"grid_h": 5, "grid_w": 5, "n_singletons": 2, "n_pairs": 0, "n_conflicts": 0},
        {"grid_h": 7, "grid_w": 9, "n_singletons": 4, "n_pairs": 1, "n_conflicts": 1},
        {"grid_h": 12, "grid_w": 16, "n_singletons": 5, "n_pairs": 3, "n_conflicts": 2},
    ],
)
def test_declared_overrides_are_exact_observable_and_global(band, requested):
    grid = gen.generate(8128, 17, difficulty=band, **requested)
    assert gen.observe_overrides(grid) == requested
    assert gen.self_check(grid) == []
    assert gen.rule_mirror(grid) == probe.left_priority_output(grid)
    assert gen.rule_mirror(grid) != grid


def test_invalid_and_unknown_overrides_fail_loudly():
    with pytest.raises((TypeError, ValueError), match="unknown override"):
        gen.generate(1, 0, typo_axis=2)
    for name, value in (
        ("grid_h", 4),
        ("grid_w", 17),
        ("n_singletons", 1),
        ("n_pairs", 4),
        ("n_conflicts", 3),
        ("n_pairs", True),
        ("grid_h", 7.5),
    ):
        with pytest.raises((TypeError, ValueError)):
            gen.generate(1, 0, **{name: value})


def test_default_schedule_reaches_every_canonical_profile_and_teaches_conflicts():
    canonical_profiles = {(5, 5, 4), (5, 7, 3), (6, 9, 4), (7, 7, 6), (7, 9, 6)}
    for band_index, band in enumerate(("easy", "medium", "hard")):
        grids = [gen.generate(9000 + band_index, index, difficulty=band) for index in range(10)]
        assert {probe.profile(grid) for grid in grids} == canonical_profiles
        for grid in grids:
            assert gen.self_check(grid) == []
            assert gen.strict_canonical_like(grid) == []
            assert probe.orbit_counts(grid)["n_conflicts"] >= 1
            assert gen.SEMANTIC_WITNESSES["occupied_color_conflict"](grid)
            expected = probe.left_priority_output(grid)
            assert gen.rule_mirror(grid) == expected
            assert gen.CANONICAL_SHORTCUTS["preserve_occupied_conflicts"](grid) != expected
            assert gen.CANONICAL_SHORTCUTS["right_priority"](grid) != expected


def test_named_rivals_fit_all_canonical_demos_but_exact_witness_refutes_them():
    pairs = _canonical_train_pairs()
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        assert all(rival(pair["input"]) == pair["output"] for pair in pairs), name

    witness = probe.exact_counterexample()
    assert gen.self_check(witness) == []
    authority = probe.left_priority_output(witness)
    assert authority == [
        [0, 0, 0, 0, 0],
        [0, 2, 0, 2, 0],
        [4, 0, 0, 0, 4],
        [5, 0, 0, 0, 5],
        [0, 0, 0, 0, 0],
    ]
    assert probe.preserve_conflicts_output(witness) != authority
    assert probe.right_priority_output(witness) != authority
    assert gen.rule_mirror(witness) == authority


def test_three_demo_lessons_identify_every_named_competitor():
    for band_index, band in enumerate(("easy", "medium", "hard")):
        for start in range(8):
            examples = [_demo(12000 + band_index, start + offset, band) for offset in range(4)]
            assert gen.lesson_identifiable(examples[:3], examples[3]) == []


def test_self_check_rejects_malformed_empty_and_identity_scenes():
    valid = gen.generate(44, 3, difficulty="medium")
    ragged = copy.deepcopy(valid)
    ragged[-1].pop()
    illegal = copy.deepcopy(valid)
    illegal[0][0] = 10
    blank = [[0] * 5 for _ in range(5)]
    symmetric_identity = [[0] * 5 for _ in range(5)]
    symmetric_identity[1][0] = symmetric_identity[1][4] = 2
    for grid in (ragged, illegal, blank, symmetric_identity):
        errors = gen.self_check(grid)
        assert isinstance(errors, list) and errors
        assert all(isinstance(error, str) and error for error in errors)


def test_replay_is_fresh_and_global_random_state_is_untouched():
    random.seed(321)
    before = random.getstate()
    first = gen.generate(404, 5, difficulty="hard")
    after = random.getstate()
    second = gen.generate(404, 5, difficulty="hard")
    assert before == after
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 8 if first[0][0] != 8 else 7
    assert first != second


def test_racket_authority_matches_independent_oracle_on_generated_conflicts():
    from arcpuzzles import Catalog

    grids = [
        gen.generate(51000 + band_index, index, difficulty=band)
        for band_index, band in enumerate(("easy", "medium", "hard"))
        for index in range(3)
    ]
    receipt = Catalog(ROOT).apply(TASK_ID, grids, reference="canonical", timeout=180)
    assert receipt["rule_hash_matches_catalog"]
    assert [item["output"] for item in receipt["results"]] == [
        probe.left_priority_output(grid) for grid in grids
    ]
