"""Task-local regressions for ad5a6c1521b3.

The expected outputs come from the independent workspace oracle or real Racket,
never from production helper functions.
"""
from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import analysis, canonical_pairs, load_generator, racket_outputs, rule_output

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))

EXPECTED_PROFILES = {
    "tie_both_8": ((8, 8), ((2, 5), (4, 4))),
    "single_unique_8": ((8, 8), ((3,), (3, 6))),
    "tie_both_16_three": ((16, 16), ((3, 6, 6), (3, 7))),
    "single_unique_16": ((16, 16), ((4, 10), (7,))),
}


@pytest.mark.parametrize(
    "pair",
    canonical_pairs(),
    ids=lambda pair: f"v{pair['variant']}-{pair['split']}{pair['pair_index']}",
)
def test_accepts_every_canonical_pair_and_oracle_matches(pair):
    original = deepcopy(pair["input"])
    assert gen.self_check(pair["input"]) == []
    assert rule_output(pair["input"]) == pair["output"]
    assert pair["input"] == original


def test_generator_pins_the_reviewed_rule_and_declares_only_truthful_profiles():
    assert gen.RULE_HASH == "8e796791a1a2"
    assert tuple(gen.SCENE_PROFILES) == tuple(EXPECTED_PROFILES)
    assert set(gen.AXES) == {"scene_profile"}
    assert getattr(gen, "INCOMPATIBLE_OVERRIDE_COMBINATIONS", None) == []


def test_selected_target_code_is_exactly_synced_to_canonical_authority():
    from reference_probe import ROOT

    canonical_path = next(
        path
        for path in (
            ROOT / "shared/data/canonical/puzzles.jsonl",
            ROOT / "data/canonical/puzzles.jsonl",
        )
        if path.is_file()
    )
    canonical_rules = []
    with canonical_path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == "ad5a6c1521b3":
                canonical_rules.append(row["program_solution"])
    assert canonical_rules and len(set(canonical_rules)) == 1
    canonical_rule = canonical_rules[0]

    base_root = next(
        path
        for path in (
            ROOT / "shared/data/base/solutions",
            ROOT / "data/base/solutions",
        )
        if path.is_dir()
    )
    selected = []
    for path in base_root.rglob("*.json"):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("task_id") == "ad5a6c1521b3":
            selected.append((path, payload))
    assert len(selected) == 2
    for path, payload in selected:
        assert payload["racket_target"]["target_code"] == canonical_rule, path


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("profile", tuple(EXPECTED_PROFILES))
def test_each_exact_profile_override_round_trips_in_every_band(profile, band):
    grid = gen.generate(20261010, 17, difficulty=band, scene_profile=profile)
    facts = analysis(grid)
    expected_shape, expected_signature = EXPECTED_PROFILES[profile]
    assert gen.self_check(grid) == []
    assert gen.strict_canonical_like(grid) == []
    assert (facts["height"], facts["width"]) == expected_shape
    assert facts["palette_size"] == 3
    assert facts["signature"] == expected_signature
    assert gen.observe_overrides(grid) == {"scene_profile": profile}
    assert rule_output(grid) != grid


@pytest.mark.parametrize(
    "overrides",
    [
        {"typo": "tie_both_8"},
        {"scene_profile": "missing"},
        {"scene_profile": 3},
        {"scene_profile": True},
    ],
)
def test_invalid_and_unknown_overrides_fail_closed(overrides):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **overrides)


@pytest.mark.parametrize("difficulty", ["trivial", 0.5, False])
def test_unknown_difficulty_fails_closed(difficulty):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, difficulty=difficulty)


def test_varying_seed_changes_palette_and_layout_not_only_role_order():
    grids = [gen.generate(seed, 0, scene_profile="tie_both_8") for seed in range(40)]
    inputs = {json.dumps(grid, separators=(",", ":")) for grid in grids}
    outputs = {json.dumps(rule_output(grid), separators=(",", ":")) for grid in grids}
    backgrounds = {analysis(grid)["background"] for grid in grids}
    assert len(inputs) >= 20
    assert len(outputs) >= 20
    assert len(backgrounds) >= 5


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_default_schedule_covers_every_profile_and_is_deterministic(band):
    seen = set()
    for index in range(16):
        grid = gen.generate(700 + index, index, difficulty=band)
        assert grid == gen.generate(700 + index, index, difficulty=band)
        assert gen.self_check(grid) == []
        seen.add(gen.observe_overrides(grid)["scene_profile"])
    assert seen == set(EXPECTED_PROFILES)


def test_profiles_cover_ties_multiple_colors_three_components_and_passive_colors():
    facts = {
        profile: analysis(gen.generate(101, 0, scene_profile=profile))
        for profile in EXPECTED_PROFILES
    }
    tie = facts["tie_both_8"]
    assert len(tie["active"]) == 2
    assert any(len({row["size"] for row in item["components"]}) == 1 for item in tie["active"])
    assert rule_output(gen.generate(101, 0, scene_profile="tie_both_8")) != rule_output(
        gen.generate(101, 0, scene_profile="tie_both_8"), top_left_tie=True
    )

    single = facts["single_unique_8"]
    assert len(single["active"]) == 1 and len(single["passive"]) == 1
    winner = max(single["active"][0]["components"], key=lambda row: row["size"])
    loser = min(single["active"][0]["components"], key=lambda row: row["size"])
    assert sum(winner["bbox"][:2]) < sum(loser["bbox"][:2])

    three = facts["tie_both_16_three"]
    assert len(three["active"]) == 2
    assert max(len(item["components"]) for item in three["active"]) == 3

    large_single = facts["single_unique_16"]
    assert len(large_single["active"]) == 1 and len(large_single["passive"]) == 1


@pytest.mark.parametrize("profile", tuple(EXPECTED_PROFILES))
def test_every_profile_exposes_bbox_fill_and_left_column(profile):
    grid = gen.generate(333, 9, scene_profile=profile)
    official = rule_output(grid)
    assert official != rule_output(grid, preserve_winner_holes=True)
    assert official != rule_output(grid, omit_left_column=True)


def test_semantic_contract_has_real_counterexamples_and_every_three_demo_window_identifies_rule():
    assert set(gen.SEMANTIC_RIVALS) >= {
        "first_split_only",
        "top_left_tie",
        "preserve_winner_holes",
        "omit_left_column",
    }
    assert gen.CANONICAL_SHORTCUTS
    assert gen.LESSON_COMPETITORS
    assert gen.SEMANTIC_WITNESSES
    pairs = []
    period = gen.LESSON_SCHEDULE_PERIOD
    for index in range(period + 3):
        grid = gen.generate(812, index)
        pairs.append({"input": grid, "output": rule_output(grid)})
    for start in range(period):
        demos = pairs[start : start + 3]
        query = pairs[start + 3]
        assert gen.lesson_identifiable(demos, query) == []
        for name, rival in gen.LESSON_COMPETITORS.items():
            if rival(query["input"]) != query["output"]:
                assert any(rival(pair["input"]) != pair["output"] for pair in demos), name
    for name, predicate in gen.SEMANTIC_WITNESSES.items():
        assert any(predicate(pair["input"]) for pair in pairs), name
    for witness_name, rival_names in gen.WITNESS_RIVALS.items():
        predicate = gen.SEMANTIC_WITNESSES[witness_name]
        firing = [pair for pair in pairs if predicate(pair["input"])]
        assert firing, witness_name
        for pair in firing:
            assert any(
                gen.SEMANTIC_RIVALS[rival_name](pair["input"]) != pair["output"]
                for rival_name in rival_names
            ), witness_name


def test_retained_branch_counterexample_is_replayable():
    fixture = json.loads(
        (HOME / "counterexamples" / "branch-witness.json").read_text(encoding="utf-8")
    )
    grid = fixture["input"]
    expected = fixture["canonical_output"]
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == {"scene_profile": fixture["scene_profile"]}
    assert rule_output(grid) == expected
    for name in fixture["refuted_rivals"]:
        assert gen.SEMANTIC_RIVALS[name](grid) != expected


@pytest.mark.parametrize(
    "grid",
    [None, [], [[]], [[0], [0, 1]], [[True] * 8 for _ in range(8)]],
)
def test_malformed_grid_is_diagnostic_not_an_exception(grid):
    assert gen.self_check(grid)
    assert gen.strict_canonical_like(grid)
    assert gen.observe_overrides(grid) == {}


def test_keyed_generation_is_independent_of_python_hash_seed():
    script = (
        "import json,sys;sys.path.insert(0,sys.argv[1]);"
        "from reference_probe import load_generator;"
        "print(json.dumps(load_generator().generate(31,8,difficulty='hard')))"
    )
    outputs = []
    for hash_seed in ("1", "901"):
        env = dict(os.environ, PYTHONHASHSEED=hash_seed, PYTHONDONTWRITEBYTECODE="1")
        outputs.append(
            subprocess.check_output(
                [sys.executable, "-B", "-c", script, str(HOME / "workspace")],
                env=env,
                text=True,
            )
        )
    assert outputs[0] == outputs[1]


def test_real_racket_matches_independent_oracle_when_available():
    from arc_repl.racket_bridge import racket_runtime_status

    status = racket_runtime_status()
    if not status["available"]:
        pytest.skip(status["reason"])
    grids = [pair["input"] for pair in canonical_pairs()]
    grids += [
        gen.generate(1700 + index, index, scene_profile=profile)
        for index, profile in enumerate(EXPECTED_PROFILES)
    ]
    assert racket_outputs(grids) == [rule_output(grid) for grid in grids]
