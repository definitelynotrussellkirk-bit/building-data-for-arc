from __future__ import annotations

import copy
import importlib
import json
import random
from pathlib import Path

import pytest

from scripts.canonical_profile_gate import canonical_pairs


gen = importlib.import_module("puzzle_generators.per_puzzle.14c5c68b0201.generator")
TASK_ID = "14c5c68b0201"


def _scene(**overrides):
    requested = {
        "layout_profile": "official_a",
        "motif_index": 1,
        "anchor_profile": "interior",
        "palette_band": "low",
        "background_color": 8,
    }
    requested.update(overrides)
    return gen.generate(7401, 9, difficulty="medium", **requested)



def test_task_local_racket_source_roles_are_explicit_and_selected_sources_match():
    root = Path(__file__).resolve().parents[1]
    paths = [
        root / "data/base/solutions/training/a57f2f04__14c5c68b0201.json",
        root / "data/base/solutions/augmented/a57f2f04__dfdf4bc032da.json",
    ]
    selected = []
    for path in paths:
        target = json.loads(path.read_text(encoding="utf-8"))["racket_target"]
        assert target["target_code_role"] == "selected_task_rule"
        assert target["raw_code_role"] == "archival_executable_source"
        assert ";;" in target["target_code"]
        selected.append(target["target_code"])
    assert selected[0] == selected[1]

def test_canonical_inputs_are_owned_and_rule_pin_is_current():
    pairs = canonical_pairs(TASK_ID)
    assert len(pairs) == 8
    assert gen.RULE_HASH == "b125453b4d98"
    assert gen.VERSION == "3.1.0"
    for pair in pairs:
        assert gen.self_check(copy.deepcopy(pair["input"])) == []


def test_override_boundaries_are_exact_observable_in_every_band():
    cases = [
        {
            "layout_profile": "official_a",
            "motif_index": 0,
            "anchor_profile": "corners",
            "palette_band": "low",
            "background_color": 8,
        },
        {
            "layout_profile": "triple",
            "motif_index": 3,
            "anchor_profile": "interior",
            "palette_band": "high",
            "background_color": 9,
        },
        {
            "layout_profile": "wide",
            "motif_index": 2,
            "anchor_profile": "edges",
            "palette_band": "low",
            "background_color": 9,
        },
    ]
    for band in ("easy", "medium", "hard"):
        for index, requested in enumerate(cases):
            grid = gen.generate(8000 + index, index, difficulty=band, **requested)
            assert gen.self_check(grid) == []
            assert gen.observe_overrides(grid) == requested

    with pytest.raises(ValueError, match="unknown override key"):
        gen.generate(1, 2, difficulty="easy", typo_axis="ignored")


def test_ordinary_draws_observe_every_declared_axis_and_difficulty_is_live():
    observed_by_band = {}
    for band in ("easy", "medium", "hard"):
        rows = []
        for index in range(40):
            grid = gen.generate(91000 + index, index * 7 + 3, difficulty=band)
            observed = gen.observe_overrides(grid)
            assert set(observed) == set(gen.AXES)
            assert all(value is not None for value in observed.values())
            rows.append(tuple(sorted(observed.items())))
        observed_by_band[band] = rows

    # Same seed/index cohort cannot be byte-identical across all three bands.
    assert any(
        observed_by_band["easy"][i] != observed_by_band["medium"][i]
        or observed_by_band["medium"][i] != observed_by_band["hard"][i]
        for i in range(40)
    )


def test_structural_impostors_are_rejected():
    valid = _scene()
    assert gen.self_check(valid) == []

    # 1. A zero corridor joins the first hole to the canvas edge.
    corridor = copy.deepcopy(valid)
    for row in range(0, 3):
        corridor[row][2] = 0
    assert gen.self_check(corridor)

    # 2. One rectangular hole contains two active colors.
    mixed_color = copy.deepcopy(valid)
    mixed_color[3][3] = 7
    assert gen.self_check(mixed_color)

    # 3. A stamp is replaced by a solid rectangle, hiding texture semantics.
    solid_stamp = copy.deepcopy(valid)
    scene, errors = gen._parse_scene(solid_stamp)
    assert not errors and scene is not None
    first = scene["holes"][0]
    sr1, sc1, sr2, sc2 = first["stamp_bbox"]
    for row in range(sr1, sr2 + 1):
        for col in range(sc1, sc2 + 1):
            solid_stamp[row][col] = first["color"]
    assert gen.self_check(solid_stamp)

    # 4. Two independent holes reuse one active color.
    duplicate_color = copy.deepcopy(valid)
    scene, errors = gen._parse_scene(duplicate_color)
    assert not errors and scene is not None and len(scene["holes"]) == 2
    first_color = scene["holes"][0]["color"]
    second_color = scene["holes"][1]["color"]
    for row, cells in enumerate(duplicate_color):
        for col, value in enumerate(cells):
            if value == second_color:
                duplicate_color[row][col] = first_color
    assert gen.self_check(duplicate_color)


def test_rule_rivals_have_real_killing_witnesses():
    witness_grids = [
        _scene(layout_profile="official_b", motif_index=0, anchor_profile="corners"),
        _scene(layout_profile="official_a", motif_index=1, anchor_profile="edges"),
        _scene(layout_profile="triple", motif_index=3, anchor_profile="interior", background_color=9),
    ]
    for witness_name, rival_names in gen.WITNESS_RIVALS.items():
        candidates = [grid for grid in witness_grids if gen.SEMANTIC_WITNESSES[witness_name](grid)]
        assert candidates, witness_name
        for rival_name in rival_names:
            assert any(
                gen.SEMANTIC_RIVALS[rival_name](grid) != gen._solve_true_py(grid)
                for grid in candidates
            ), (witness_name, rival_name)


def test_replay_is_fresh_and_process_global_rng_pure():
    random.seed(20260727)
    state = random.getstate()
    first = gen.generate(4567, 33, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(4567, 33, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = (first[0][0] + 1) % 10
    assert first != second
