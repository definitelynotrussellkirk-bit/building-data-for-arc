from __future__ import annotations

import collections
import importlib.util
import json
import sys
from pathlib import Path

import pytest

TASK_ID = "c831492f416e"
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


def _norm_grid(grid):
    if isinstance(grid, list) and grid and all(isinstance(row, str) for row in grid):
        return [[int(value) for value in row] for row in grid]
    return [list(row) for row in grid]


def _canonical_row() -> dict:
    path = REPO / "shared" / "data" / "canonical" / "puzzles.jsonl"
    for line in path.read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row
    raise AssertionError(f"missing canonical row {TASK_ID}")


def _cells_by_color(grid):
    cells = collections.defaultdict(list)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value:
                cells[value].append((r, c))
    return dict(cells)


def test_public_contract_is_one_observable_semantic_axis() -> None:
    generator = _load_generator()
    assert generator.RULE_HASH == "91f9e86ee830"
    assert set(generator.AXES) == {"scene_profile"}
    assert tuple(generator.SCENE_PROFILES) == (
        "canonical_disjoint",
        "short_gap",
        "cross_horizontal_high",
        "cross_vertical_high",
        "precondition_decoys",
    )
    assert generator.EXAMPLES_NEEDED == len(generator.SCENE_PROFILES) == 5
    assert generator.INCOMPATIBLE_OVERRIDE_COMBINATIONS == ()
    assert generator.HELPFUL_TEXTURES == ()
    assert generator.DEGENERATE_TEXTURES == ()


def test_five_consecutive_examples_cover_every_profile() -> None:
    generator = _load_generator()
    expected = set(generator.SCENE_PROFILES)
    for start in range(15):
        observed = {
            generator.schedule_profile(123, start + offset, difficulty="medium")
            for offset in range(generator.EXAMPLES_NEEDED)
        }
        assert observed == expected


def test_unknown_override_is_rejected() -> None:
    generator = _load_generator()
    with pytest.raises(ValueError, match="unknown override"):
        generator.generate(0, 0, difficulty="medium", typo_profile="short_gap")


@pytest.mark.parametrize(
    "profile",
    [
        "canonical_disjoint",
        "short_gap",
        "cross_horizontal_high",
        "cross_vertical_high",
        "precondition_decoys",
    ],
)
def test_profile_override_is_exactly_observable(profile: str) -> None:
    generator = _load_generator()
    for band in ("easy", "medium", "hard"):
        grid = generator.generate(17, 9, difficulty=band, scene_profile=profile)
        assert generator.observe_overrides(grid) == {"scene_profile": profile}
        assert generator.self_check(grid, difficulty=band) == []
        assert generator.rule_mirror(grid) != grid


def test_default_generation_is_deterministic_valid_and_profile_complete() -> None:
    generator = _load_generator()
    expected = set(generator.SCENE_PROFILES)
    for band in ("easy", "medium", "hard"):
        for seed in range(15):
            profiles = set()
            for sample_index in range(generator.EXAMPLES_NEEDED):
                first = generator.generate(seed, sample_index, difficulty=band)
                second = generator.generate(seed, sample_index, difficulty=band)
                assert first == second
                assert len(first) >= 6 and len(first[0]) >= 7
                assert generator.self_check(first, difficulty=band) == []
                analysis = generator.analyze_grid(first)
                assert analysis["valid"]
                assert not analysis["endpoint_overwrite_risk"]
                profiles.add(generator.observe_overrides(first)["scene_profile"])
            assert profiles == expected


def test_short_gap_profile_contains_a_one_cell_interior() -> None:
    generator = _load_generator()
    for band in ("easy", "medium", "hard"):
        grid = generator.generate(11, 1, difficulty=band, scene_profile="short_gap")
        analysis = generator.analyze_grid(grid)
        assert analysis["aligned_pair_count"] == 2
        assert analysis["short_pair_count"] >= 1
        assert analysis["crossing_count"] == 0


def test_crossing_profiles_teach_numeric_precedence_not_axis_precedence() -> None:
    generator = _load_generator()
    cases = {
        "cross_horizontal_high": "H",
        "cross_vertical_high": "V",
    }
    for profile, expected_orientation in cases.items():
        grid = generator.generate(29, 3, difficulty="hard", scene_profile=profile)
        analysis = generator.analyze_grid(grid)
        assert analysis["crossing_count"] == 1
        assert analysis["crossing_winner_orientation"] == expected_orientation
        assert analysis["crossing_point"] is not None
        assert analysis["crossing_high_color"] > analysis["crossing_low_color"]
        r, c = analysis["crossing_point"]
        assert generator.rule_mirror(grid)[r][c] == analysis["crossing_high_color"]


def test_precondition_profile_keeps_decoys_and_connects_only_the_valid_pair() -> None:
    generator = _load_generator()
    grid = generator.generate(31, 4, difficulty="medium", scene_profile="precondition_decoys")
    analysis = generator.analyze_grid(grid)
    assert analysis["aligned_pair_count"] == 1
    assert analysis["diagonal_pair_count"] == 1
    assert analysis["aligned_triple_count"] == 1

    output = generator.rule_mirror(grid)
    by_color = _cells_by_color(grid)
    for color in analysis["decoy_colors"]:
        for r, c in by_color[color]:
            assert output[r][c] == color
    assert output != grid


def test_rule_mirror_and_checks_accept_every_canonical_pair() -> None:
    generator = _load_generator()
    row = _canonical_row()
    raw_pairs = [*row["train"], row["test"]]
    for pair in raw_pairs:
        inp = _norm_grid(pair["input"])
        out = _norm_grid(pair["output"])
        assert generator.rule_mirror(inp) == out
        assert generator.self_check(inp) == []
        assert generator.strict_canonical_like(inp) == []


def test_scheduled_lesson_refutes_every_declared_competitor() -> None:
    generator = _load_generator()
    demos = []
    for sample_index in range(generator.EXAMPLES_NEEDED):
        inp = generator.generate(44, sample_index, difficulty="medium")
        demos.append({"input": inp, "output": generator.rule_mirror(inp)})
    query_input = generator.generate(44, generator.EXAMPLES_NEEDED, difficulty="medium")
    query = {"input": query_input, "output": generator.rule_mirror(query_input)}

    assert generator.lesson_identifiable(demos, query) == []
    for name, rival in generator.LESSON_COMPETITORS.items():
        assert any(rival(pair["input"]) != pair["output"] for pair in demos), name


def test_workspace_profile_audit_reports_clean_curriculum() -> None:
    generator = _load_generator()
    path = REPO / "generators" / TASK_ID / "workspace" / "profile_audit.py"
    spec = importlib.util.spec_from_file_location(f"audit_{TASK_ID}", path)
    assert spec and spec.loader
    audit_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(audit_module)

    report = audit_module.audit_census(generator, seeds=2)
    assert report["draws"] == 30
    assert report["profile_counts"] == {
        profile: 6 for profile in generator.SCENE_PROFILES
    }
    assert report["strict_hits"] == 24
    assert report["strict_rate"] == pytest.approx(0.8)
    assert report["canonical_mismatches"] == []
    assert report["self_check_failures"] == []
    assert report["observer_mismatches"] == []
    assert report["endpoint_overwrite_risks"] == []
    assert report["lesson_failures"] == []
    assert report["surviving_rivals"] == []
    assert report["passed"]


def test_crossing_profiles_do_not_alias_the_short_gap_witness() -> None:
    generator = _load_generator()
    grid = generator.generate(
        156925347025477,
        6062,
        difficulty="easy",
        scene_profile="cross_horizontal_high",
    )
    analysis = generator.analyze_grid(grid)
    assert analysis["crossing_count"] == 1
    assert analysis["short_pair_count"] == 0
    assert not generator.SEMANTIC_WITNESSES[
        "minimum_one_cell_interior_is_connected"
    ](grid)
