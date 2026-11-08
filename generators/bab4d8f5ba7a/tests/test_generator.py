from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

import pytest


TASK_ID = "bab4d8f5ba7a"
GENERATOR_DIR = Path(__file__).resolve().parents[1]
REPO = GENERATOR_DIR.parents[1]
RUNTIME = REPO / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))


def _load_generator():
    path = GENERATOR_DIR / "generator.py"
    spec = importlib.util.spec_from_file_location(f"focused_{TASK_ID}", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def gen():
    return _load_generator()


@pytest.fixture(scope="module")
def canonical_row():
    path = REPO / "shared" / "data" / "canonical" / "puzzles.jsonl"
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise AssertionError(f"canonical row {TASK_ID} not found")


def _all_pairs(row):
    return [*(row.get("train") or []), *(row.get("test") or [])]


def test_rule_hash_and_unknown_override_contract(gen):
    assert gen.RULE_HASH == "1130750019d1"
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(0, 0, mystery_axis="typo")


def test_declared_axes_are_exactly_observable(gen):
    expected = {
        "scene_profile": set(gen.SCENE_PROFILES),
        "palette_kind": set(gen.PALETTE_KINDS),
        "teaching_profile": set(gen.TEACHING_PROFILES),
    }
    assert set(gen.AXES) == set(expected)
    for axis, values in expected.items():
        for value in values:
            grid = gen.generate(17, 5, difficulty="easy", **{axis: value})
            observed = gen.observe_overrides(grid)
            assert observed[axis] == value
            assert gen.self_check(grid) == []


def test_every_pair_of_declared_overrides_materializes(gen):
    # The repository override gate probes categorical pairs. Exercise a compact
    # representative matrix here so one mode cannot silently bypass another.
    for scene in gen.SCENE_PROFILES:
        for teaching in gen.TEACHING_PROFILES:
            grid = gen.generate(
                11,
                3,
                difficulty="hard",
                scene_profile=scene,
                teaching_profile=teaching,
                palette_kind="includes_nine",
            )
            observed = gen.observe_overrides(grid)
            assert observed == {
                "scene_profile": scene,
                "palette_kind": "includes_nine",
                "teaching_profile": teaching,
            }


def test_default_schedule_covers_every_teaching_profile(gen):
    seen = {
        gen.observe_overrides(gen.generate(3, index))["teaching_profile"]
        for index in range(len(gen.TEACHING_PROFILES))
    }
    assert seen == set(gen.TEACHING_PROFILES)


def test_semantic_profiles_are_structurally_distinct(gen):
    grids = {
        profile: gen.generate(
            29,
            2,
            scene_profile="canonical_8x10_r4",
            palette_kind="canonical_distinct",
            teaching_profile=profile,
        )
        for profile in gen.TEACHING_PROFILES
    }
    analyses = {name: gen.analyze_grid(grid) for name, grid in grids.items()}

    assert all(count == 1 for count in analyses["canonical_single"]["marker_counts"])
    assert not analyses["canonical_single"]["stray_markers"]

    assert all(count == 2 for count in analyses["multi_marker"]["marker_counts"])
    assert not analyses["multi_marker"]["stray_markers"]

    assert all(count == 1 for count in analyses["stray_marker"]["marker_counts"])
    assert len(analyses["stray_marker"]["stray_markers"]) == 1

    assert sorted(analyses["mixed_markers"]["marker_counts"]) == [1, 1, 1, 2]
    assert len(analyses["mixed_markers"]["stray_markers"]) == 1

    assert all(count == 1 for count in analyses["inert_distractors"]["marker_counts"])
    assert all(count == 1 for count in analyses["inert_distractors"]["distractor_counts"])


def test_self_check_accepts_canonical_and_rejects_destroyed_grammar(gen, canonical_row):
    for pair in _all_pairs(canonical_row):
        assert gen.self_check(pair["input"]) == []

    valid = gen.generate(7, 0, teaching_profile="canonical_single")
    blank = [[0 for _ in row] for row in valid]
    assert gen.self_check(blank)

    no_marker = [list(row) for row in valid]
    for r, row in enumerate(no_marker):
        if row[0] != 0:
            no_marker[r] = [row[0], *([0] * (len(row) - 1))]
    assert gen.self_check(no_marker)

    marker_in_header = [list(row) for row in valid]
    active_row = next(r for r, row in enumerate(marker_in_header) if row[0] != 0)
    marker_in_header[active_row][0] = 8
    assert gen.self_check(marker_in_header)


def test_rule_mirror_matches_every_canonical_output(gen, canonical_row):
    for pair in _all_pairs(canonical_row):
        assert gen.rule_mirror(pair["input"]) == pair["output"]


def test_rule_mirror_preserves_strays_and_distractors(gen):
    for profile in ("stray_marker", "mixed_markers", "inert_distractors"):
        grid = gen.generate(101, 4, teaching_profile=profile)
        output = gen.rule_mirror(grid)
        for r, row in enumerate(grid):
            for c, value in enumerate(row):
                if c > 0 and value == 8 and row[0] != 0:
                    assert output[r][c] == row[0]
                else:
                    assert output[r][c] == value


def test_every_semantic_witness_refutes_a_named_rival(gen):
    profile_for = {
        "multiple_row_header_colors": "canonical_single",
        "multiple_markers_in_one_row": "multi_marker",
        "headerless_marker_preserved": "stray_marker",
        "non_cyan_body_cell_preserved": "inert_distractors",
        "strict_canonical_anchor": "canonical_single",
    }
    assert set(gen.WITNESS_RIVALS) == set(gen.SEMANTIC_WITNESSES)
    assert set(gen.CANONICAL_SHORTCUTS) <= set(gen.SEMANTIC_RIVALS)

    for witness_name, teaching_profile in profile_for.items():
        grid = gen.generate(
            211,
            0,
            scene_profile="canonical_8x10_r4",
            palette_kind="canonical_distinct",
            teaching_profile=teaching_profile,
        )
        assert gen.SEMANTIC_WITNESSES[witness_name](grid)
        expected = gen.rule_mirror(grid)
        rival_names = gen.WITNESS_RIVALS[witness_name]
        if isinstance(rival_names, str):
            rival_names = [rival_names]
        assert rival_names
        for rival_name in rival_names:
            assert gen.SEMANTIC_RIVALS[rival_name](grid) != expected
