from __future__ import annotations

import importlib
import json
import random
from pathlib import Path

import pytest

TASK_ID = "fda98b5c7670"
GEN = importlib.import_module(
    "puzzle_generators.per_puzzle.fda98b5c7670.generator"
)
ROOT = Path(__file__).resolve().parents[1]


def _canonical_row() -> dict:
    for line in (ROOT / "data/canonical/puzzles.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row
    raise AssertionError("canonical task row is missing")


def _pairs(row: dict) -> list[dict]:
    test = row["test"]
    return [*row["train"], *([test] if isinstance(test, dict) else test)]


def test_all_canonical_pairs_are_owned_and_mirrored_exactly():
    pairs = _pairs(_canonical_row())
    assert len(pairs) == 3
    for pair in pairs:
        before = [row[:] for row in pair["input"]]
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == before


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_eight_role_schedule_covers_axis_palette_and_canonical_anchors(band):
    analyses = []
    for sample_index, expected_profile in enumerate(GEN.SCHEDULE_PROFILES):
        grid = GEN.generate(20260725, sample_index, difficulty=band)
        analysis = GEN._analyse(grid)
        assert analysis["errors"] == []
        assert GEN.schedule_profile(20260725, sample_index, band) == expected_profile
        expected_palette, expected_axis = expected_profile.rsplit("_", 1)
        assert analysis["axis"] == expected_axis
        assert analysis["palette_kind"] == expected_palette
        assert GEN.rule_mirror(grid) != grid
        analyses.append(analysis)

    canonical = analyses[:2]
    assert all(item["n_lines"] == 2 for item in canonical)
    assert all(item["points_per_line"] == 2 for item in canonical)
    assert all(
        (item["height"], item["width"]) in GEN._CANONICAL_PROFILES
        for item in canonical
    )


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
@pytest.mark.parametrize("axis", ["row", "col"])
@pytest.mark.parametrize("palette_kind", GEN.PALETTE_KINDS)
def test_exact_override_boundaries_are_realized(band, axis, palette_kind):
    for height, width, n_lines, points in (
        (6, 6, 1, 2),
        (14, 14, 5, 4),
        (6, 14, 5, 4),
        (14, 6, 5, 4),
    ):
        grid = GEN.generate(
            991,
            37,
            difficulty=band,
            grid_h=height,
            grid_w=width,
            axis=axis,
            n_lines=n_lines,
            points_per_line=points,
            palette_kind=palette_kind,
        )
        assert len(grid) == height
        assert len(grid[0]) == width
        assert GEN.observe_overrides(grid) == {
            "axis": axis,
            "n_lines": n_lines,
            "points_per_line": points,
            "palette_kind": palette_kind,
        }


def test_unknown_or_invalid_overrides_fail_closed():
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(1, 2, texture="mismatched_endpoints")
    with pytest.raises(ValueError):
        GEN.generate(1, 2, axis="diagonal")
    with pytest.raises(ValueError):
        GEN.generate(1, 2, palette_kind="marker_echo")
    with pytest.raises(ValueError):
        GEN.generate(1, 2, grid_h=6, axis="row", n_lines=6)


def test_all_declared_mutation_fixtures_are_rejected():
    fixtures = GEN.mutation_fixtures()
    assert len(fixtures) >= 8
    for name, grid in fixtures:
        assert GEN.self_check(grid), name
        with pytest.raises(ValueError):
            GEN.rule_mirror(grid)


def test_each_semantic_witness_fires_and_defeats_its_named_rival():
    witnessed = {name: None for name in GEN.SEMANTIC_WITNESSES}
    for sample_index in range(32):
        grid = GEN.generate(12345, sample_index, difficulty="medium")
        authoritative = GEN.rule_mirror(grid)
        for name, witness in GEN.SEMANTIC_WITNESSES.items():
            if witnessed[name] is None and witness(grid):
                rivals = GEN.WITNESS_RIVALS[name]
                assert any(
                    GEN.SEMANTIC_RIVALS[rival](grid) != authoritative
                    for rival in rivals
                )
                witnessed[name] = sample_index
    assert all(index is not None for index in witnessed.values()), witnessed


def test_three_consecutive_demos_identify_every_scheduled_query():
    for start in range(24):
        pairs = []
        for sample_index in range(start, start + 4):
            grid = GEN.generate(8080, sample_index, difficulty="hard")
            pairs.append({"input": grid, "output": GEN.rule_mirror(grid)})
        assert GEN.lesson_identifiable(pairs[:3], pairs[3]) == []


def test_determinism_freshness_and_process_rng_purity():
    random.seed(8675309)
    state = random.getstate()
    first = GEN.generate(42, 17, difficulty="hard")
    assert random.getstate() == state
    second = GEN.generate(42, 17, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second, strict=True))
    first[0][0] = 0
    assert second[0][0] in (2, 3)
