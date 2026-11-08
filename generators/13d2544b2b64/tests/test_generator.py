from __future__ import annotations

import json

import pytest
from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator

TASK_ID = "13d2544b2b64"
EXPECTED_PROFILES = (
    "canonical_controls",
    "equality_mismatch",
    "horizontal_precedence",
    "target_overwrite",
)
ROOT = find_root(__file__)


def _load_generator():
    module, _source, _digest = load_selected_generator(TASK_ID, root=ROOT)
    return module


def _canonical_rows() -> list[dict]:
    rows = [
        row for line in canonical_path(ROOT).read_text().splitlines() if line.strip()
        if (row := json.loads(line)).get("task_id") == TASK_ID
    ]
    assert rows, f"missing canonical row {TASK_ID}"
    return rows


def _pair(generator, seed: int, sample_index: int, band: str = "medium") -> dict:
    input_grid = generator.generate(seed, sample_index, difficulty=band)
    return {"input": input_grid, "output": generator.rule_mirror(input_grid)}


def test_public_contract_is_pinned_and_minimal() -> None:
    generator = _load_generator()
    assert generator.RULE_HASH == "301b331591ad"
    assert generator.VERSION == "3.1.0"
    assert tuple(generator.SCENE_PROFILES) == EXPECTED_PROFILES
    assert generator.SCHEDULE_PROFILES == EXPECTED_PROFILES
    assert generator.EXAMPLES_NEEDED == len(EXPECTED_PROFILES)
    assert generator.LESSON_SCHEDULE_PERIOD == len(EXPECTED_PROFILES)
    assert generator.MIN_STRICT_FRAC == 1.0
    assert set(generator.AXES) == {"scene_profile"}
    assert generator.INCOMPATIBLE_OVERRIDE_COMBINATIONS == ()


def test_unknown_and_invalid_overrides_fail_loudly() -> None:
    generator = _load_generator()
    with pytest.raises(ValueError, match="unknown override"):
        generator.generate(0, 0, typo_profile="equality_mismatch")
    with pytest.raises(ValueError, match="unknown scene_profile"):
        generator.generate(0, 0, scene_profile="not-a-profile")


def test_every_four_example_window_covers_every_profile() -> None:
    generator = _load_generator()
    for band in ("easy", "medium", "hard"):
        for start in range(16):
            observed = {
                generator.schedule_profile(123, start + offset, band)
                for offset in range(len(EXPECTED_PROFILES))
            }
            assert observed == set(EXPECTED_PROFILES)


@pytest.mark.parametrize("profile", EXPECTED_PROFILES)
def test_profile_override_is_exactly_observable_and_canonical_shaped(profile: str) -> None:
    generator = _load_generator()
    for band in ("easy", "medium", "hard"):
        grid = generator.generate(17, 5, difficulty=band, scene_profile=profile)
        palette = {value for row in grid for value in row}
        assert (len(grid), len(grid[0]), len(palette)) == (8, 8, 4)
        assert generator.observe_overrides(grid) == {"scene_profile": profile}
        assert generator.self_check(grid, difficulty=band) == []
        assert generator.strict_canonical_like(grid) == []
        assert generator.rule_mirror(grid) != grid


def test_profile_semantics_hit_each_canonical_blind_spot() -> None:
    generator = _load_generator()
    facts = {}
    for index, profile in enumerate(EXPECTED_PROFILES):
        grid = generator.generate(31, index, scene_profile=profile)
        facts[profile] = generator.analyze_grid(grid)

    controls = facts["canonical_controls"]
    assert controls["horizontal_change_count"] >= 1
    assert controls["vertical_change_count"] >= 1
    assert controls["outer_change_count"] >= 1
    assert controls["one_sided_counterexample_count"] >= 1

    mismatch = facts["equality_mismatch"]
    assert mismatch["different_nonbackground_pair_count"] >= 2
    assert mismatch["horizontal_change_count"] >= 1
    assert mismatch["vertical_change_count"] >= 1

    precedence = facts["horizontal_precedence"]
    assert precedence["priority_conflict_count"] >= 1
    assert precedence["outer_change_count"] >= 1

    overwrite = facts["target_overwrite"]
    assert overwrite["target_overwrite_count"] >= 1
    assert overwrite["outer_change_count"] >= 1


def test_rule_mirror_matches_all_canonical_pairs_and_accepts_inputs() -> None:
    generator = _load_generator()
    for pair in canonical_pairs(TASK_ID, root=ROOT):
        input_grid = pair["input"]
        output_grid = pair["output"]
        original = [line[:] for line in input_grid]
        assert generator.rule_mirror(input_grid) == output_grid
        assert input_grid == original
        assert generator.self_check(input_grid) == []
        assert generator.strict_canonical_like(input_grid) == []


def test_declared_canonical_shortcuts_really_fit_every_canonical_pair() -> None:
    generator = _load_generator()
    pairs = canonical_pairs(TASK_ID, root=ROOT)
    assert set(generator.CANONICAL_SHORTCUTS) == {
        "ignore_color_equality",
        "vertical_priority",
        "background_only",
    }
    for name, rival in generator.CANONICAL_SHORTCUTS.items():
        for pair in pairs:
            assert rival(pair["input"]) == pair["output"], name


def test_each_declared_shortcut_gets_a_generated_counterexample() -> None:
    generator = _load_generator()
    profile_for = {
        "ignore_color_equality": "equality_mismatch",
        "vertical_priority": "horizontal_precedence",
        "background_only": "target_overwrite",
    }
    for name, profile in profile_for.items():
        grid = generator.generate(41, 0, scene_profile=profile)
        official = generator.rule_mirror(grid)
        assert generator.SEMANTIC_RIVALS[name](grid) != official, name


def test_every_scheduled_lesson_refutes_every_declared_competitor() -> None:
    generator = _load_generator()
    for band in ("easy", "medium", "hard"):
        for start in range(8):
            demos = [_pair(generator, 53, start + offset, band) for offset in range(4)]
            query = _pair(generator, 53, start + 4, band)
            assert generator.lesson_identifiable(demos, query) == []
            for name, rival in generator.LESSON_COMPETITORS.items():
                assert any(rival(pair["input"]) != pair["output"] for pair in demos), name


def test_generation_is_deterministic_and_band_keyed() -> None:
    generator = _load_generator()
    for profile in EXPECTED_PROFILES:
        medium = generator.generate(73, 1, difficulty="medium", scene_profile=profile)
        assert medium == generator.generate(
            73, 1, difficulty="medium", scene_profile=profile
        )
        variants = {
            tuple(tuple(row) for row in generator.generate(
                73, 1, difficulty=band, scene_profile=profile
            ))
            for band in ("easy", "medium", "hard")
        }
        assert len(variants) >= 2


def test_task_local_mutation_fixtures_are_rejected() -> None:
    generator = _load_generator()
    fixtures = list(generator.mutation_fixtures())
    assert len(fixtures) >= 4
    for name, grid in fixtures:
        assert generator.self_check(grid), name


def test_selected_active_racket_source_is_exactly_canonical() -> None:
    manifest = ROOT / "RUNTIME_MANIFEST.json"
    if manifest.is_file():
        # The execution source takes precedence over task-test library mirrors.
        paths = {
            ROOT / entry["runtime_path"]
            for entry in json.loads(manifest.read_text())["files"]
            if entry["runtime_path"].startswith("data/base/solutions/")
        }
    else:
        authorities = json.loads((ROOT / "catalog/authority_files.json").read_text())
        targets = {path for path, task_id in authorities.items() if task_id == TASK_ID}
        assert targets, f"no selected authority for {TASK_ID}"
        mappings = json.loads((ROOT / "catalog/runtime_files.json").read_text())
        paths = {ROOT / entry["path"] for entry in mappings if entry["target"] in targets}
        assert len(paths) == len(targets), "a selected authority is missing its runtime mapping"

    selected = [
        row["racket_target"]["target_code"] for path in sorted(paths)
        if (row := json.loads(path.read_text())).get("task_id") == TASK_ID
    ]
    assert selected, f"no selected authority source for {TASK_ID}"
    for canonical in _canonical_rows():
        for source in selected:
            assert source == canonical["program_solution"]
