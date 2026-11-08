from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pytest

TASK_ID = "83c4d8ce9656"
REPO = Path(__file__).resolve().parents[3]
RUNTIME = REPO / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))


def _load_generator():
    path = REPO / "generators" / TASK_ID / "generator.py"
    spec = importlib.util.spec_from_file_location(f"test_{TASK_ID}", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_row() -> dict:
    path = REPO / "shared" / "data" / "canonical" / "puzzles.jsonl"
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise AssertionError(f"missing canonical row {TASK_ID}")


def _canonical_pairs() -> list[dict]:
    row = _canonical_row()
    return [*row["train"], *row["test"]]


def _normalized_rule_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def _palette_size(grid: list[list[int]]) -> int:
    return len({value for row in grid for value in row})


def test_public_contract_has_four_exact_profiles_and_pinned_rule() -> None:
    generator = _load_generator()
    row = _canonical_row()

    assert generator.RULE_HASH == _normalized_rule_hash(row["program_solution"])
    assert generator.EXAMPLES_NEEDED == 4
    assert len(generator.SCENE_PROFILES) == 4
    assert generator.SCHEDULE_PROFILES == generator.SCENE_PROFILES
    assert set(generator.AXES) == {"scene_profile"}
    assert set(generator.AXES["scene_profile"]["valid"].split("|")) == set(
        generator.SCENE_PROFILES
    )
    assert generator.INCOMPATIBLE_OVERRIDE_COMBINATIONS == ()


def test_every_four_consecutive_samples_cover_every_profile() -> None:
    generator = _load_generator()
    expected = set(generator.SCENE_PROFILES)
    for band in ("easy", "medium", "hard"):
        for seed in (0, 7, 101):
            for start in range(8):
                observed = {
                    generator.schedule_profile(seed, start + offset, band)
                    for offset in range(generator.EXAMPLES_NEEDED)
                }
                assert observed == expected


@pytest.mark.parametrize(
    "profile",
    (
        "canonical_mix",
        "multiple_long_runs",
        "repeated_color_runs",
        "touching_color_runs",
    ),
)
def test_profile_override_is_exactly_observable(profile: str) -> None:
    generator = _load_generator()
    for band in ("easy", "medium", "hard"):
        grid = generator.generate(17, 9, difficulty=band, scene_profile=profile)
        assert generator.observe_overrides(grid) == {"scene_profile": profile}
        assert generator.self_check(grid, difficulty=band) == []


def test_unknown_and_invalid_overrides_fail_loudly() -> None:
    generator = _load_generator()
    with pytest.raises(ValueError, match="unknown override"):
        generator.generate(0, 0, typo_profile="canonical_mix")
    with pytest.raises(ValueError, match="scene_profile"):
        generator.generate(0, 0, scene_profile="not_a_profile")


def test_pinned_profile_floor_has_at_least_twenty_five_percent_exact_support() -> None:
    generator = _load_generator()
    canonical_signatures = {
        (len(pair["input"]), len(pair["input"][0]), _palette_size(pair["input"]))
        for pair in _canonical_pairs()
    }
    exact = 0
    total = 0
    for band in ("easy", "medium", "hard"):
        for index in range(20):
            digest = hashlib.sha256(
                f"profile-floor:v1:{TASK_ID}:{band}:{index}".encode()
            ).hexdigest()
            seed = int(digest[:12], 16)
            sample_index = seed % 7919 + index
            grid = generator.generate(seed, sample_index, difficulty=band)
            total += 1
            exact += (
                len(grid), len(grid[0]), _palette_size(grid)
            ) in canonical_signatures
    assert exact / total >= 0.25


def test_canonical_profile_is_exactly_on_the_public_shape_palette_manifold() -> None:
    generator = _load_generator()
    canonical_signatures = {
        (len(pair["input"]), len(pair["input"][0]), _palette_size(pair["input"]))
        for pair in _canonical_pairs()
    }
    for seed in range(30):
        grid = generator.generate(
            seed,
            seed + 3,
            difficulty="hard",
            scene_profile="canonical_mix",
        )
        signature = (len(grid), len(grid[0]), _palette_size(grid))
        assert signature in canonical_signatures


def test_rule_mirror_matches_every_canonical_pair_and_selfcheck_accepts_inputs() -> None:
    generator = _load_generator()
    for pair in _canonical_pairs():
        assert generator.rule_mirror(pair["input"]) == pair["output"]
        assert generator.self_check(pair["input"]) == []
        assert generator.strict_canonical_like(pair["input"]) == []


def test_selfcheck_rejects_non_teaching_impostors() -> None:
    generator = _load_generator()
    impostors = {
        "blank": [[0] * 8 for _ in range(5)],
        "singleton": [[0] * 8 for _ in range(4)] + [[0, 0, 0, 4, 0, 0, 0, 0]],
        "vertical_only": [
            [0, 0, 3, 0, 0, 0, 0, 0],
            [0, 0, 3, 0, 0, 0, 0, 0],
            [0, 0, 3, 0, 0, 0, 0, 0],
            [0, 0, 4, 0, 0, 0, 0, 0],
            [0, 0, 4, 0, 0, 0, 0, 0],
        ],
        "solid": [[2] * 8 for _ in range(5)],
        "one_short_run": [[0] * 8 for _ in range(4)]
        + [[0, 0, 6, 6, 0, 0, 0, 0]],
    }
    for name, grid in impostors.items():
        assert generator.self_check(grid), name


def test_declared_canonical_shortcuts_reproduce_all_public_pairs() -> None:
    generator = _load_generator()
    assert set(generator.CANONICAL_SHORTCUTS) == {
        "color_span_per_row",
        "nonzero_block_endpoints",
        "longest_run_per_row",
    }
    for name, shortcut in generator.CANONICAL_SHORTCUTS.items():
        for pair in _canonical_pairs():
            assert shortcut(pair["input"]) == pair["output"], name


def test_each_semantic_profile_supplies_its_named_counterexample() -> None:
    generator = _load_generator()
    cases = {
        "multiple_long_runs": (
            "multiple_long_runs_one_row",
            "longest_run_per_row",
        ),
        "repeated_color_runs": (
            "same_color_separated_runs",
            "color_span_per_row",
        ),
        "touching_color_runs": (
            "touching_color_boundary",
            "nonzero_block_endpoints",
        ),
    }
    for profile, (witness_name, rival_name) in cases.items():
        grid = generator.generate(23, 5, difficulty="medium", scene_profile=profile)
        authoritative = generator.rule_mirror(grid)
        assert generator.SEMANTIC_WITNESSES[witness_name](grid)
        assert generator.SEMANTIC_RIVALS[rival_name](grid) != authoritative


def test_one_scheduled_lesson_refutes_every_declared_competitor() -> None:
    generator = _load_generator()
    for band in ("easy", "medium", "hard"):
        demos = []
        for sample_index in range(generator.EXAMPLES_NEEDED):
            grid = generator.generate(44, sample_index, difficulty=band)
            demos.append({"input": grid, "output": generator.rule_mirror(grid)})
        query_grid = generator.generate(44, generator.EXAMPLES_NEEDED, difficulty=band)
        query = {"input": query_grid, "output": generator.rule_mirror(query_grid)}
        assert generator.lesson_identifiable(demos, query) == []
        for name, rival in generator.LESSON_COMPETITORS.items():
            assert any(rival(pair["input"]) != pair["output"] for pair in demos), name


def test_default_generation_is_deterministic_valid_and_diverse() -> None:
    generator = _load_generator()
    seen: set[tuple[tuple[int, ...], ...]] = set()
    observed_profiles: set[str] = set()
    for band in ("easy", "medium", "hard"):
        for seed in range(20):
            for sample_index in range(generator.EXAMPLES_NEEDED):
                grid = generator.generate(seed, sample_index, difficulty=band)
                assert grid == generator.generate(seed, sample_index, difficulty=band)
                assert generator.self_check(grid, difficulty=band) == []
                profile = generator.observe_overrides(grid)["scene_profile"]
                assert profile == generator.schedule_profile(seed, sample_index, band)
                observed_profiles.add(profile)
                seen.add(tuple(tuple(row) for row in grid))
    assert observed_profiles == set(generator.SCENE_PROFILES)
    assert len(seen) >= 200


def test_workspace_profile_audit_reports_a_clean_curriculum() -> None:
    generator = _load_generator()
    path = REPO / "generators" / TASK_ID / "workspace" / "profile_audit.py"
    spec = importlib.util.spec_from_file_location(f"audit_{TASK_ID}", path)
    assert spec and spec.loader
    audit_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(audit_module)

    report = audit_module.audit_census(generator, seeds=2)
    assert report["draws"] == 24
    assert report["profile_counts"] == {
        profile: 6 for profile in generator.SCENE_PROFILES
    }
    assert report["self_check_failures"] == []
    assert report["observer_mismatches"] == []
    assert report["lesson_failures"] == []
    assert report["unrefuted_rivals"] == []
    assert report["canonical_profile_hits"] >= 6
