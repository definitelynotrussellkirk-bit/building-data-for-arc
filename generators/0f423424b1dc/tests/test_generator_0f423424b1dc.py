from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

HOME = Path(__file__).resolve().parents[1]
ROOT = Path(__file__).resolve().parents[3]
SPEC = importlib.util.spec_from_file_location("generator_0f423424b1dc", HOME / "generator.py")
assert SPEC and SPEC.loader
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def canonical_pairs():
    path = ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl"
    for line in path.read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == GEN.TASK_ID:
            return [*row["train"], *row["test"]]
    raise AssertionError("canonical task not found")


def pair(grid):
    return {"input": grid, "output": GEN.rule_mirror(grid)}


def test_declares_exact_review_contract():
    assert GEN.RULE_HASH == "1e2581a2f271"
    assert GEN.EXAMPLES_NEEDED == 4
    assert set(GEN.AXES) == {
        "grid_h", "grid_w", "n_targets", "n_mismatched",
        "n_blocked", "n_singletons", "edge_anchor",
    }


def test_canonical_pairs_are_accepted_and_reproduced():
    for example in canonical_pairs():
        assert GEN.self_check(example["input"]) == []
        assert GEN.strict_canonical_like(example["input"]) == []
        assert GEN.rule_mirror(example["input"]) == example["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_every_exact_override_is_observable_in_every_band(band):
    expected = {
        "grid_h": 8,
        "grid_w": 8,
        "n_targets": 3,
        "n_mismatched": 1,
        "n_blocked": 1,
        "n_singletons": 1,
        "edge_anchor": True,
    }
    grid = GEN.generate(17, 9, difficulty=band, **expected)
    assert GEN.self_check(grid) == []
    assert GEN.observe_overrides(grid) == expected


@pytest.mark.parametrize(
    "name,value",
    [
        ("unknown", 1), ("grid_h", 5), ("grid_w", 13),
        ("n_targets", 0), ("n_targets", 4),
        ("n_mismatched", 2), ("n_blocked", -1),
        ("n_singletons", "1"), ("edge_anchor", 1),
    ],
)
def test_invalid_overrides_are_rejected(name, value):
    with pytest.raises(ValueError):
        GEN.generate(0, 0, **{name: value})


def test_four_consecutive_profiles_cover_all_rule_discriminators():
    grids = [GEN.generate(41, i, difficulty="medium") for i in range(4)]
    observed = [GEN.observe_overrides(grid) for grid in grids]
    assert [GEN.schedule_profile(41, i, "medium") for i in range(4)] == [
        "canonical", "mismatch", "blocked", "singleton"
    ]
    assert any(item["n_mismatched"] == 1 for item in observed)
    assert any(item["n_blocked"] == 1 for item in observed)
    assert any(item["n_singletons"] == 1 for item in observed)
    assert all(GEN.self_check(grid) == [] for grid in grids)


def test_named_shortcuts_fit_canonical_but_generated_witnesses_refute_them():
    for name, rival in GEN.CANONICAL_SHORTCUTS.items():
        assert all(rival(ex["input"]) == ex["output"] for ex in canonical_pairs()), name

    grids = {GEN.schedule_profile(9, i): GEN.generate(9, i) for i in range(4)}
    expected = {
        "mismatch": "ignore_endpoint_color",
        "blocked": "ignore_extra_cells",
        "singleton": "extend_singletons",
    }
    for profile, rival_name in expected.items():
        grid = grids[profile]
        assert GEN.SEMANTIC_WITNESSES[profile](grid)
        assert GEN.SEMANTIC_RIVALS[rival_name](grid) != GEN.rule_mirror(grid)


def test_four_demo_lesson_falsifies_every_declared_competitor():
    demos = [pair(GEN.generate(23, i, difficulty="hard")) for i in range(4)]
    query = pair(GEN.generate(23, 4, difficulty="hard"))
    assert GEN.lesson_identifiable(demos, query) == []


def test_generation_is_deterministic_and_validator_rejects_impostors():
    assert GEN.generate(72, 11, difficulty="hard") == GEN.generate(72, 11, difficulty="hard")
    assert GEN.self_check([])
    assert GEN.self_check([[0] * 6 for _ in range(6)])
    filled = GEN.rule_mirror(GEN.generate(5, 0, n_targets=2))
    assert GEN.self_check(filled)
