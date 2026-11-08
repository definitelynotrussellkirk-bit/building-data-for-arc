"""Focused semantic regressions for generator 06b4c496c6cf."""
from __future__ import annotations

import copy
import importlib
import json
import random
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, canonical_path, find_root


gen = importlib.import_module(
    "puzzle_generators.per_puzzle.06b4c496c6cf.generator"
)
TASK_ID = "06b4c496c6cf"
ROOT = find_root(__file__)
BASE_PATH = ROOT / "data/base/solutions/banks/40f7bd2c7916/S15_M2__06b4c496c6cf.json"
CANONICAL_PAIRS = canonical_pairs(TASK_ID, root=ROOT)


def _canonical_row() -> dict:
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise AssertionError(f"missing canonical row for {TASK_ID}")


def _canonical_pairs() -> list[dict]:
    return CANONICAL_PAIRS


def _pair(grid) -> dict:
    return {"input": grid, "output": gen.rule_mirror(grid)}


def test_rule_pin_canonical_pairs_and_selected_source_are_exact():
    row = _canonical_row()
    assert gen.VERSION == "3.2.0"
    assert gen.RULE_HASH == "7bb33c62cc2e"
    pairs = _canonical_pairs()
    assert len(pairs) == 3
    for pair in pairs:
        before = copy.deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == before

    target = json.loads(BASE_PATH.read_text(encoding="utf-8"))["racket_target"]
    assert target["target_code"] == row["program_solution"]
    assert target["raw_code"] != target["target_code"]


def test_eight_demo_schedule_refutes_every_canonical_compatible_rival():
    grids = [
        gen.generate(1701, index, difficulty="medium")
        for index in range(gen.EXAMPLES_NEEDED + 1)
    ]
    assert [gen.observe_overrides(grid)["texture"] for grid in grids] == list(
        gen._TEXTURE_SCHEDULE
    )
    demos = [_pair(grid) for grid in grids[:-1]]
    query = _pair(grids[-1])
    assert gen.lesson_identifiable(demos, query) == []

    for witness_name, rival_names in gen.WITNESS_RIVALS.items():
        witness_grid = next(
            grid
            for grid in grids
            if gen.SEMANTIC_WITNESSES[witness_name](grid)
        )
        official = gen.rule_mirror(witness_grid)
        for rival_name in rival_names:
            assert gen.SEMANTIC_RIVALS[rival_name](witness_grid) != official


def test_override_boundaries_are_exact_observable_and_band_safe():
    case = 0
    for difficulty in ("easy", "medium", "hard"):
        for texture in gen.TEXTURES:
            for grid_h, grid_w in ((10, 12), (18, 22)):
                for marker_count in (2, 6):
                    requested = {
                        "grid_h": grid_h,
                        "grid_w": grid_w,
                        "marker_count": marker_count,
                        "texture": texture,
                    }
                    grid = gen.generate(
                        9000 + case,
                        case,
                        difficulty=difficulty,
                        **requested,
                    )
                    assert gen.self_check(grid) == []
                    assert gen.observe_overrides(grid) == requested
                    case += 1

    for texture in ("overlap_pair", "pair_markers"):
        with pytest.raises(ValueError, match="requires marker_count >= 2"):
            gen.generate(1, 1, texture=texture, marker_count=1)
    with pytest.raises(TypeError, match="unknown override"):
        gen.generate(1, 2, bogus_axis=3)


def test_replay_is_fresh_deterministic_global_rng_pure_and_band_live():
    random.seed(20260725)
    state = random.getstate()
    first = gen.generate(123, 456, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(123, 456, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9
    assert first != second

    by_band = {
        band: gen.generate(991, 17, difficulty=band)
        for band in ("easy", "medium", "hard")
    }
    assert len({repr(grid) for grid in by_band.values()}) >= 2


def test_structural_checker_rejects_five_targeted_impostors():
    plain = gen.generate(
        31,
        0,
        difficulty="medium",
        grid_h=10,
        grid_w=16,
        marker_count=3,
        texture="plain",
    )
    facts = gen._scene_facts(plain)

    no_template = copy.deepcopy(plain)
    for row, col in facts["template"]:
        no_template[row][col] = 0
    assert gen.self_check(no_template)

    two_templates = copy.deepcopy(plain)
    two_templates[-1][-1] = 2
    assert any("exactly one" in message for message in gen.self_check(two_templates))

    no_markers = copy.deepcopy(plain)
    for row, col, _color in facts["markers"]:
        no_markers[row][col] = 0
    assert any("1..6 marker" in message for message in gen.self_check(no_markers))

    invalid_marker_color = copy.deepcopy(plain)
    row, col, _color = facts["markers"][0]
    invalid_marker_color[row][col] = 1
    assert gen.self_check(invalid_marker_color)

    combined_relations = gen.generate(
        52,
        1,
        grid_h=12,
        grid_w=16,
        marker_count=3,
        texture="hollow_corner",
    )
    combined_facts = gen._scene_facts(combined_relations)
    first_color = combined_facts["markers"][0][2]
    row, col, _other = combined_facts["markers"][1]
    combined_relations[row][col] = first_color
    assert any(
        "multiple special relations" in message
        for message in gen.self_check(combined_relations)
    )


def test_every_texture_has_the_declared_observable_relation():
    for index, texture in enumerate(gen.TEXTURES):
        grid = gen.generate(
            700 + index,
            index,
            difficulty="medium",
            grid_h=14,
            grid_w=18,
            marker_count=3,
            texture=texture,
        )
        facts = gen._scene_facts(grid)
        assert facts["errors"] == []
        assert facts["texture"] == texture
        if texture == "hollow_corner":
            assert (0, 0) not in facts["template_offsets"]
        elif texture == "overlap_pair":
            assert len(facts["overlap_pairs"]) == 1
        elif texture == "pair_markers":
            assert list(facts["repeated_colors"].values()) == [2]
        elif texture == "clip":
            assert len(facts["clipped_indices"]) == 1


def test_rule_and_checker_are_input_pure():
    grid = gen.generate(19, 23, difficulty="medium")
    snapshot = copy.deepcopy(grid)
    gen.self_check(grid)
    gen.observe_overrides(grid)
    gen.rule_mirror(grid)
    for rival in gen.SEMANTIC_RIVALS.values():
        rival(grid)
    assert grid == snapshot

@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_every_cyclic_lesson_and_query_rotation_refutes_declared_competitors(difficulty):
    cycle = len(gen._TEXTURE_SCHEDULE)
    for start in range(cycle):
        pairs = [
            _pair(gen.generate(81173, sample_index, difficulty=difficulty))
            for sample_index in range(start, start + gen.EXAMPLES_NEEDED + 1)
        ]
        assert gen.lesson_identifiable(pairs[:-1], pairs[-1]) == []
        for query_index, query in enumerate(pairs):
            demos = [pair for index, pair in enumerate(pairs) if index != query_index]
            assert gen.lesson_identifiable(demos, query) == [], (
                difficulty,
                start,
                query_index,
                [gen.observe_overrides(pair["input"])["texture"] for pair in pairs],
            )

def test_declared_shortcuts_cover_palette_and_occupied_cell_anchor():
    expected = {"canonical_colors_only", "first_occupied_cell_anchor"}
    assert expected <= set(gen.CANONICAL_SHORTCUTS)

    pairs = _canonical_pairs()
    for name in expected:
        rival = gen.CANONICAL_SHORTCUTS[name]
        assert all(rival(pair["input"]) == pair["output"] for pair in pairs), name

    generated = [
        gen.generate(22691, index, difficulty="medium")
        for index in range(gen.EXAMPLES_NEEDED + 1)
    ]
    for name in expected:
        rival = gen.CANONICAL_SHORTCUTS[name]
        assert any(rival(grid) != gen.rule_mirror(grid) for grid in generated), name


def test_retained_before_rotation_counterexample_is_reproducible():
    fixture_path = (
        Path(__file__).resolve().parents[1]
        / "counterexamples"
        / "rotation_ambiguity_before.json"
    )
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    rival = gen.CANONICAL_SHORTCUTS[fixture["rival_name"]]

    assert all(
        rival(pair["input"]) == pair["output"]
        for pair in fixture["demonstrations"]
    )
    assert rival(fixture["query"]["input"]) == fixture["rival_query_output"]
    assert rival(fixture["query"]["input"]) != fixture["query"]["output"]
