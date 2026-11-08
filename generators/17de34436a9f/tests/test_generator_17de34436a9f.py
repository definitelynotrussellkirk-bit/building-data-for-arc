from __future__ import annotations

import copy
import importlib.util
import json
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
RUNTIME_ROOT = REPO_ROOT / "shared" / "runtime"
if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))

MODULE_PATH = REPO_ROOT / "generators" / "17de34436a9f" / "generator.py"
SPEC = importlib.util.spec_from_file_location("review_generator_17de34436a9f", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def test_pins_rule_and_declares_only_real_exact_axes():
    assert GEN.RULE_HASH == "9f94f78b9fd2"
    assert GEN.VERSION == "3.0.0"
    assert set(GEN.AXES) == {
        "grid_h",
        "grid_w",
        "marker_corner",
        "body_size",
        "body_color",
    }
    assert GEN.DEGENERATE_TEXTURES == ()


def test_unknown_override_fails_loudly():
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(1, 0, typo_axis="br")


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_exact_override_is_realized_in_every_band(band):
    cases = (
        {
            "grid_h": 7,
            "grid_w": 7,
            "marker_corner": "tl",
            "body_size": 4,
            "body_color": 1,
        },
        {
            "grid_h": 14,
            "grid_w": 14,
            "marker_corner": "tr",
            "body_size": 7,
            "body_color": 8,
        },
        {
            "grid_h": 7,
            "grid_w": 14,
            "marker_corner": "br",
            "body_size": 6,
            "body_color": 4,
        },
        {
            "grid_h": 14,
            "grid_w": 7,
            "marker_corner": "bl",
            "body_size": 5,
            "body_color": 6,
        },
    )
    for index, requested in enumerate(cases):
        grid = GEN.generate(100 + index, 20 + index, difficulty=band, **requested)
        assert GEN.self_check(grid, difficulty=band) == []
        assert GEN.observe_overrides(grid) == requested


def _canonical_pairs():
    path = REPO_ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl"
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == GEN.TASK_ID:
                return [copy.deepcopy(pair) for split in ("train", "test") for pair in row[split]]
    raise AssertionError("canonical task row not found")


def test_python_rule_mirror_matches_every_canonical_pair():
    pairs = _canonical_pairs()
    assert len(pairs) == 5
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]


def test_sequential_schedule_covers_all_corner_meanings_with_strict_anchors():
    assert GEN.EXAMPLES_NEEDED == 4
    assert GEN.MIN_STRICT_FRAC == 1.0
    assert tuple(GEN.SCHEDULE_PROFILES) == ("tl", "tr", "br", "bl")
    for band in ("easy", "medium", "hard"):
        grids = [GEN.generate(77, index, difficulty=band) for index in range(4)]
        assert [GEN.schedule_profile(77, index, band) for index in range(4)] == [
            "tl",
            "tr",
            "br",
            "bl",
        ]
        assert [GEN.observe_overrides(grid)["marker_corner"] for grid in grids] == [
            "tl",
            "tr",
            "br",
            "bl",
        ]
        assert all(GEN.strict_canonical_like(grid) == [] for grid in grids)


def test_declared_canonical_shortcut_is_real_and_generated_br_refutes_it():
    shortcut = GEN.CANONICAL_SHORTCUTS["bottom_right_identity"]
    for pair in _canonical_pairs():
        assert shortcut(pair["input"]) == pair["output"]

    generated = GEN.generate(
        313,
        9,
        difficulty="hard",
        grid_h=9,
        grid_w=9,
        marker_corner="br",
        body_size=6,
        body_color=7,
    )
    assert shortcut(generated) != GEN.rule_mirror(generated)


def _pair_for(grid):
    return {"input": grid, "output": GEN.rule_mirror(grid)}


def test_named_witnesses_refute_named_rivals_and_lessons_identify_rule():
    grids = [
        GEN.generate(901 + seed, seed * 7 + index, difficulty=band)
        for band in ("easy", "medium", "hard")
        for seed in range(8)
        for index in range(4)
    ]
    assert set(GEN.WITNESS_RIVALS) == set(GEN.SEMANTIC_WITNESSES)
    for witness_name, rival_names in GEN.WITNESS_RIVALS.items():
        witnesses = [
            grid for grid in grids if GEN.SEMANTIC_WITNESSES[witness_name](grid)
        ]
        assert witnesses, witness_name
        for rival_name in rival_names:
            rival = GEN.SEMANTIC_RIVALS[rival_name]
            assert any(rival(grid) != GEN.rule_mirror(grid) for grid in witnesses), (
                witness_name,
                rival_name,
            )

    for band in ("easy", "medium", "hard"):
        for start in range(8):
            lesson = [
                _pair_for(GEN.generate(2026, start + offset, difficulty=band))
                for offset in range(5)
            ]
            assert GEN.lesson_identifiable(lesson[:4], lesson[4]) == []


def test_mutation_fixtures_are_rejected_but_symmetric_canonical_body_is_lawful():
    fixtures = GEN.mutation_fixtures()
    assert {name for name, _ in fixtures} >= {
        "missing_marker",
        "duplicate_marker",
        "marker_not_corner",
        "disconnected_body",
        "multicolor_body",
        "body_touches_marker",
        "illegal_color",
        "ragged_grid",
    }
    accepted = {name: GEN.self_check(grid) for name, grid in fixtures}
    assert all(errors for errors in accepted.values()), accepted

    canonical_br = next(
        pair["input"]
        for pair in _canonical_pairs()
        if pair["input"][-1][-1] == 9
    )
    assert GEN.self_check(canonical_br) == []


def test_source_bound_lesson_probe_checks_every_cyclic_start(tmp_path):
    probe_path = MODULE_PATH.parent / "workspace" / "lesson_probe.py"
    probe_spec = importlib.util.spec_from_file_location(
        "review_lesson_probe_17de34436a9f", probe_path
    )
    assert probe_spec is not None and probe_spec.loader is not None
    probe = importlib.util.module_from_spec(probe_spec)
    probe_spec.loader.exec_module(probe)

    report = probe.run_probe(lessons_per_band=4)
    assert report["status"] == "PASS"
    assert report["source_binding"]["declared_rule_hash"] == GEN.RULE_HASH
    assert report["source_binding"]["computed_rule_hash"] == GEN.RULE_HASH
    for band in ("easy", "medium", "hard"):
        audit = report["bands"][band]
        assert audit["lessons"] == 4
        assert audit["cyclic_starts_checked"] == [0, 1, 2, 3]
        assert audit["identifiability_failures"] == []
        assert all(count == 4 for count in audit["witness_lessons"].values())
        assert not any(audit["competitor_query_changing_survivors"].values())


@pytest.mark.parametrize("bad_value", ["not-a-color", [], 1.5, True])
def test_self_check_reports_non_arc_cells_without_crashing(bad_value):
    grid = [[0 for _ in range(7)] for _ in range(7)]
    grid[0][0] = 9
    for row, col in ((3, 3), (4, 3), (5, 3), (5, 4)):
        grid[row][col] = 4
    grid[3][3] = bad_value

    errors = GEN.self_check(grid)

    assert any("integer ARC colors 0..9" in error for error in errors)
