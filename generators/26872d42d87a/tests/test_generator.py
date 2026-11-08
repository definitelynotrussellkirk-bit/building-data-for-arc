from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib

import pytest

from reviewer_support import canonical_pairs, find_root

TASK_ID = "26872d42d87a"
GEN = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")
ROOT = find_root(__file__)
PAIRS = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)


def _shape(grid):
    return len(grid), len(grid[0])


def test_rule_hash_and_canonical_pairs_are_authoritative():
    assert len(PAIRS) == 5
    source = next(
        row["program_solution"]
        for row in __import__("json").loads("[" + ",".join(
            line.strip() for line in (ROOT / "shared/data/canonical/puzzles.jsonl").read_text().splitlines()
            if line.strip()
        ) + "]")
        if row.get("task_id") == TASK_ID
    )
    expected = hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]
    assert GEN.RULE_HASH == expected == "bc262329ef0d"
    for pair in PAIRS:
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_every_scene_profile_is_exact_observable_and_semantically_rich(band):
    for index, profile in enumerate(GEN.SCENE_PROFILES):
        grid = GEN.generate(431 + index, 97 + index, difficulty=band, scene_profile=profile)
        before = deepcopy(grid)
        assert GEN.self_check(grid, difficulty=band) == []
        assert GEN.observe_overrides(grid) == {"scene_profile": profile}
        assert _shape(grid) == GEN.PROFILE_DIMENSIONS[profile]
        assert GEN.canonical_profile_signature(grid) == profile
        assert set(value for row in grid for value in row) == {0, 5, 6}
        true_output = GEN.rule_mirror(grid)
        assert grid == before
        assert true_output != grid
        for witness in ("wide_horizontal_near_miss", "vertical_near_miss"):
            assert GEN.SEMANTIC_WITNESSES[witness](grid)
            for rival_name in GEN.WITNESS_RIVALS[witness]:
                assert GEN.SEMANTIC_RIVALS[rival_name](grid) != true_output


def test_canonical_fitting_shortcuts_are_refuted_by_every_generated_input():
    for name, rival in GEN.CANONICAL_SHORTCUTS.items():
        assert all(rival(pair["input"]) == pair["output"] for pair in PAIRS), name
    for band in ("easy", "medium", "hard"):
        for sample_index in range(40):
            grid = GEN.generate(900 + sample_index, sample_index * 17, difficulty=band)
            expected = GEN.rule_mirror(grid)
            assert all(
                rival(grid) != expected for rival in GEN.CANONICAL_SHORTCUTS.values()
            )


def test_default_schedule_covers_all_profiles_and_is_diverse():
    for band in ("easy", "medium", "hard"):
        profiles = set()
        grids = set()
        for sample_index in range(100):
            grid = GEN.generate(1207, sample_index, difficulty=band)
            assert grid == GEN.generate(1207, sample_index, difficulty=band)
            assert GEN.self_check(grid) == []
            profiles.add(GEN.observe_overrides(grid)["scene_profile"])
            grids.add(tuple(map(tuple, grid)))
        assert profiles == set(GEN.SCENE_PROFILES)
        assert len(grids) >= 90


@pytest.mark.parametrize(
    "kwargs",
    [
        {"scene_profile": "not-a-profile"},
        {"scene_profile": 8},
        {"grid_h": 8},
        {"texture": "default"},
        {"__override_contract_unknown_axis__": 1},
    ],
)
def test_invalid_or_unknown_overrides_are_rejected(kwargs):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(1, 2, **kwargs)


def test_unknown_difficulty_is_rejected():
    with pytest.raises(ValueError):
        GEN.generate(1, 2, difficulty="extreme")


@pytest.mark.parametrize(
    "grid",
    [
        None,
        [],
        [[]],
        [[0], [0, 1]],
        [[True] * 10 for _ in range(8)],
        [[0] * 10 for _ in range(8)],
        [[0, 5, 6, 7] for _ in range(8)],
    ],
)
def test_malformed_or_out_of_domain_grids_are_diagnostic(grid):
    assert GEN.self_check(grid)


def test_retained_shortcut_counterexample_matches_racket_bound_evidence():
    import json

    record = json.loads(
        (ROOT / "generators" / TASK_ID / "counterexamples" / "local-rule-shortcuts-v3.json").read_text()
    )
    grid = record["input"]
    expected = record["python_rule_output"]
    assert record["generator_sha256"] == __import__("hashlib").sha256(
        (ROOT / "generators" / TASK_ID / "generator.py").read_bytes()
    ).hexdigest()
    assert record["rule_hash"] == GEN.RULE_HASH
    assert record["racket"]["executed_rule_hash"] == GEN.RULE_HASH
    assert record["racket"]["rule_hash_matches_catalog"] is True
    assert record["racket"]["matches_python_rule_output"] is True
    assert GEN.self_check(grid) == []
    assert GEN.rule_mirror(grid) == expected
    assert all(record["witnesses"].values())
    assert all(
        GEN.CANONICAL_SHORTCUTS[name](grid) == rival_output
        and rival_output != expected
        for name, rival_output in record["rivals"].items()
    )
