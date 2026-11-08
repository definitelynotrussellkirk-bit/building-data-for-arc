"""Focused regression and teaching-contract tests for 270af96a99b0."""
from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from reviewer_support import canonical_pairs, find_root

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import RIVALS, load_generator, observed, rival, solve  # noqa: E402

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))
TASK_ID = "270af96a99b0"
BANDS = (None, "easy", "medium", "hard")
PROFILES = ("p8_tie", "p10_tie", "p12_tie")


def pairs():
    return canonical_pairs(TASK_ID, root=find_root(__file__))


def test_rule_hash_validator_and_independent_oracle_match_canonical_pairs():
    assert gen.RULE_HASH == "cf57cf408f13"
    assert len(pairs()) == 3
    for pair in pairs():
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert solve(pair["input"]) == pair["output"]
        assert gen.rule_mirror(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", BANDS)
@pytest.mark.parametrize(
    "options",
    [
        dict(grid_h=8, grid_w=9, palette_kind="low", shape_profile="p8_tie"),
        dict(grid_h=14, grid_w=16, palette_kind="high", shape_profile="p10_tie"),
        dict(grid_h=8, grid_w=16, palette_kind="mixed", shape_profile="p12_tie"),
    ],
)
def test_exact_overrides_are_observable_in_every_band(band, options):
    grid = gen.generate(17, 9, difficulty=band, **options)
    assert gen.self_check(grid) == []
    assert observed(grid) == options
    assert gen.observe_overrides(grid) == options


@pytest.mark.parametrize(
    "options",
    [
        {"typo": 1},
        {"grid_h": 7},
        {"grid_h": 15},
        {"grid_w": 8},
        {"grid_w": 17},
        {"grid_h": True},
        {"grid_w": 9.5},
        {"palette_kind": "default"},
        {"palette_kind": 1},
        {"shape_profile": "unknown"},
        {"shape_profile": 8},
    ],
)
def test_invalid_overrides_fail_loudly(options):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **options)


@pytest.mark.parametrize("band", BANDS)
def test_default_schedule_hits_all_canonical_size_profiles_in_each_band(band):
    anchors = [gen.generate(8100, index, difficulty=band) for index in (0, 4, 8)]
    assert [(len(grid), len(grid[0])) for grid in anchors] == [(8, 9), (8, 10), (8, 11)]
    assert all(len({value for row in grid for value in row}) == 5 for grid in anchors)


@pytest.mark.parametrize("band", BANDS)
@pytest.mark.parametrize("profile", PROFILES)
def test_generated_domain_is_deterministic_lawful_and_refutes_named_rivals(band, profile):
    seen = set()
    for index in range(24):
        grid = gen.generate(9000 + index, index * 7 + 1, difficulty=band, shape_profile=profile)
        assert grid == gen.generate(9000 + index, index * 7 + 1, difficulty=band, shape_profile=profile)
        assert gen.self_check(grid) == []
        assert gen.strict_canonical_like(grid) == []
        assert observed(grid)["shape_profile"] == profile
        expected = solve(grid)
        assert gen.rule_mirror(grid) == expected
        for name in RIVALS:
            assert rival(grid, name) != expected, (profile, name, grid)
            assert gen.SEMANTIC_RIVALS[name](grid) == rival(grid, name)
            assert gen.SEMANTIC_WITNESSES[name](grid)
        seen.add(json.dumps(grid, separators=(",", ":")))
    assert len(seen) >= 22


@pytest.mark.parametrize("band", BANDS)
@pytest.mark.parametrize("profile", PROFILES)
def test_generated_transformation_stays_in_canonical_shrink_relation(band, profile):
    for index in range(32):
        grid = gen.generate(12000 + index, index, difficulty=band, shape_profile=profile)
        output = gen.rule_mirror(grid)
        assert len(output) <= len(grid)
        assert len(output[0]) <= len(grid[0])
        assert len(output) < len(grid) or len(output[0]) < len(grid[0])


def test_lesson_hook_exposes_saved_bbox_shortcut_and_accepts_generated_demos():
    witness_path = Path(gen.__file__).resolve().parent / "counterexamples" / "canonical-demos-admit-bbox-perimeter.json"
    witness = json.loads(witness_path.read_text())
    assert witness["task_id"] == TASK_ID
    assert witness["rule_hash"] == gen.RULE_HASH
    assert witness["rival"] == "bbox_perimeter_then_position"

    canonical = pairs()
    for pair in canonical:
        assert rival(pair["input"], witness["rival"]) == pair["output"]

    query_grid = witness["query"]["input"]
    canonical_output = witness["query"]["canonical_output"]
    rival_output = witness["query"]["rival_output"]
    assert solve(query_grid) == canonical_output
    assert rival(query_grid, witness["rival"]) == rival_output
    assert rival_output != canonical_output

    query = {"input": query_grid, "output": canonical_output}
    reasons = gen.lesson_identifiable(canonical, query)
    assert any(witness["rival"] in reason for reason in reasons)

    demos = []
    for index in range(gen.EXAMPLES_NEEDED):
        grid = gen.generate(4001, index)
        demos.append({"input": grid, "output": solve(grid)})
    assert gen.lesson_identifiable(demos, query) == []


def test_self_check_rejects_minimal_impostors_and_structural_damage():
    bad_grids = [None, [], [[]], [[0], [0, 1]], [[True] * 9 for _ in range(8)]]
    assert all(gen.self_check(grid) for grid in bad_grids)
    assert gen.self_check([[0] * 9 for _ in range(8)])

    valid = gen.generate(77, 5, grid_h=8, grid_w=9, shape_profile="p8_tie")
    assert gen.self_check(valid) == []

    one_object = [[0 for _ in row] for row in valid]
    for r, row in enumerate(valid):
        for c, value in enumerate(row):
            if value:
                one_object[r][c] = value
                break
        if any(one_object[r]):
            break
    assert gen.self_check(one_object)

    duplicate_color = deepcopy(valid)
    colors = sorted({value for row in valid for value in row if value})
    for r, row in enumerate(duplicate_color):
        for c, value in enumerate(row):
            if value == colors[-1]:
                duplicate_color[r][c] = colors[0]
    assert gen.self_check(duplicate_color)

    no_tie = deepcopy(valid)
    # Erase one tied object entirely; component count and perimeter evidence both break.
    tied_color = sorted({value for row in valid for value in row if value})[1]
    for r, row in enumerate(no_tie):
        for c, value in enumerate(row):
            if value == tied_color:
                no_tie[r][c] = 0
    assert gen.self_check(no_tie)


def test_generation_and_rule_mirror_are_pure_and_hash_seed_independent():
    grid = gen.generate(31337, 11, difficulty="hard")
    untouched = deepcopy(grid)
    assert gen.rule_mirror(grid) == solve(grid)
    assert grid == untouched

    script = (
        "import json,sys;sys.path.insert(0,sys.argv[1]);"
        "from reference_probe import load_generator;"
        "print(json.dumps(load_generator(sys.argv[2]).generate(31337,11,difficulty='hard')))"
    )
    outputs = []
    for hash_seed in ("1", "901"):
        env = dict(os.environ, PYTHONHASHSEED=hash_seed, PYTHONDONTWRITEBYTECODE="1")
        outputs.append(
            subprocess.check_output(
                [sys.executable, "-B", "-c", script, str(HOME / "workspace"), str(HOME / "generator.py")],
                env=env,
                text=True,
            )
        )
    assert outputs[0] == outputs[1]


def test_selected_racket_authority_matches_independent_oracle():
    from arcpuzzles import Catalog

    grids = [pair["input"] for pair in pairs()]
    grids += [
        gen.generate(51000 + band_index, profile_index, difficulty=band, shape_profile=profile)
        for band_index, band in enumerate(("easy", "medium", "hard"))
        for profile_index, profile in enumerate(PROFILES)
    ]
    receipt = Catalog(find_root(__file__)).apply(TASK_ID, grids, reference="canonical", timeout=180)
    assert receipt["rule_hash_matches_catalog"]
    assert all(item["error"] is None for item in receipt["results"])
    assert [item["output"] for item in receipt["results"]] == [solve(grid) for grid in grids]
