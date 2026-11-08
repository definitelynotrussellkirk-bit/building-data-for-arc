from __future__ import annotations

import collections
import importlib.util
import json
import sys
from pathlib import Path

import pytest

TASK_ID = "f44596002946"
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
    for line in path.read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row
    raise AssertionError(f"missing canonical row {TASK_ID}")


def _palette_size(grid: list[list[int]]) -> int:
    return len({value for row in grid for value in row})


def _color_cells(grid: list[list[int]]) -> dict[int, list[tuple[int, int]]]:
    cells: dict[int, list[tuple[int, int]]] = collections.defaultdict(list)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value:
                cells[value].append((r, c))
    return dict(cells)


def _segment_cells(points: list[tuple[int, int]]) -> set[tuple[int, int]]:
    if len(points) != 2:
        return set()
    (r1, c1), (r2, c2) = points
    if r1 == r2:
        return {(r1, c) for c in range(min(c1, c2), max(c1, c2) + 1)}
    if c1 == c2:
        return {(r, c1) for r in range(min(r1, r2), max(r1, r2) + 1)}
    return set()


def _has_endpoint_overwrite_risk(grid: list[list[int]]) -> bool:
    segments = []
    for color, points in _color_cells(grid).items():
        cells = _segment_cells(points)
        if cells:
            segments.append((color, cells, set(points)))
    for index, (_, left_cells, left_endpoints) in enumerate(segments):
        for _, right_cells, right_endpoints in segments[index + 1 :]:
            for point in left_cells & right_cells:
                if point in left_endpoints or point in right_endpoints:
                    return True
    return False


def test_axis_contract_is_one_observable_semantic_profile() -> None:
    generator = _load_generator()
    assert set(generator.AXES) == {"scene_profile"}
    assert callable(generator.observe_overrides)
    assert generator.INCOMPATIBLE_OVERRIDE_COMBINATIONS == ()


def test_four_consecutive_examples_cover_every_profile() -> None:
    generator = _load_generator()
    expected = set(generator.SCENE_PROFILES)
    assert len(expected) == generator.EXAMPLES_NEEDED == 4
    for start in range(12):
        observed = {
            generator.schedule_profile(seed=123, sample_index=start + offset, difficulty="medium")
            for offset in range(generator.EXAMPLES_NEEDED)
        }
        assert observed == expected


def test_unknown_override_is_rejected() -> None:
    generator = _load_generator()
    with pytest.raises(ValueError, match="unknown override"):
        generator.generate(0, 0, difficulty="medium", typo_profile="canonical_mixed")


@pytest.mark.parametrize("profile", [
    "canonical_mixed",
    "cross_horizontal_high",
    "cross_vertical_high",
    "precondition_decoys",
])
def test_profile_override_is_exactly_observable(profile: str) -> None:
    generator = _load_generator()
    for band in ("easy", "medium", "hard"):
        grid = generator.generate(17, 5, difficulty=band, scene_profile=profile)
        assert generator.observe_overrides(grid) == {"scene_profile": profile}
        assert generator.self_check(grid, difficulty=band) == []


def test_crossing_profiles_flip_the_numeric_winner() -> None:
    generator = _load_generator()
    horizontal = generator.generate(
        9, 1, difficulty="hard", scene_profile="cross_horizontal_high"
    )
    vertical = generator.generate(
        9, 2, difficulty="hard", scene_profile="cross_vertical_high"
    )
    h_analysis = generator.analyze_grid(horizontal)
    v_analysis = generator.analyze_grid(vertical)
    assert h_analysis["crossing_count"] == v_analysis["crossing_count"] == 1
    assert h_analysis["crossing_winner_orientation"] == "H"
    assert v_analysis["crossing_winner_orientation"] == "V"
    assert not _has_endpoint_overwrite_risk(horizontal)
    assert not _has_endpoint_overwrite_risk(vertical)


def test_precondition_profile_contains_both_negative_branches() -> None:
    generator = _load_generator()
    grid = generator.generate(
        31, 3, difficulty="medium", scene_profile="precondition_decoys"
    )
    analysis = generator.analyze_grid(grid)
    assert analysis["aligned_pair_count"] == 1
    assert analysis["diagonal_pair_count"] == 1
    assert analysis["aligned_triple_count"] == 1
    assert generator.rule_mirror(grid) != grid


def test_default_generation_never_places_an_endpoint_on_another_segment() -> None:
    generator = _load_generator()
    for band in ("easy", "medium", "hard"):
        for seed in range(40):
            for sample_index in range(4):
                grid = generator.generate(seed, sample_index, difficulty=band)
                assert not _has_endpoint_overwrite_risk(grid), (
                    band,
                    seed,
                    sample_index,
                )


def test_every_default_draw_matches_a_canonical_shape_palette_signature() -> None:
    generator = _load_generator()
    signatures = {(7, 11, 4), (8, 10, 4), (9, 9, 3)}
    for band in ("easy", "medium", "hard"):
        for seed in range(30):
            grid = generator.generate(seed, seed, difficulty=band)
            assert (len(grid), len(grid[0]), _palette_size(grid)) in signatures


def test_rule_mirror_matches_every_canonical_pair() -> None:
    generator = _load_generator()
    row = _canonical_row()
    for pair in [*row["train"], *row["test"]]:
        assert generator.rule_mirror(pair["input"]) == pair["output"]
        assert generator.self_check(pair["input"]) == []


def test_one_scheduled_lesson_refutes_every_declared_competitor() -> None:
    generator = _load_generator()
    demos = []
    for sample_index in range(generator.EXAMPLES_NEEDED):
        inp = generator.generate(44, sample_index, difficulty="medium")
        demos.append({"input": inp, "output": generator.rule_mirror(inp)})
    query_input = generator.generate(44, generator.EXAMPLES_NEEDED, difficulty="medium")
    query = {"input": query_input, "output": generator.rule_mirror(query_input)}
    assert generator.lesson_identifiable(demos, query) == []
    for name, rival in generator.LESSON_COMPETITORS.items():
        assert any(rival(demo["input"]) != demo["output"] for demo in demos), name


def test_difficulty_bands_use_distinct_keyed_layouts() -> None:
    generator = _load_generator()
    for sample_index in range(generator.EXAMPLES_NEEDED):
        grids = {
            tuple(tuple(row) for row in generator.generate(73, sample_index, difficulty=band))
            for band in ("easy", "medium", "hard")
        }
        assert len(grids) == 3


def test_workspace_profile_audit_reports_clean_curriculum() -> None:
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
    assert report["endpoint_overwrite_risks"] == []
    assert report["lesson_failures"] == []
