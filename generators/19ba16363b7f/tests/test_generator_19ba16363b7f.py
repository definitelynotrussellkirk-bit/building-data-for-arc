from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest


TASK_ID = "19ba16363b7f"
gen = importlib.import_module(
    "puzzle_generators.per_puzzle.19ba16363b7f.generator"
)
ROOT = Path(__file__).resolve().parents[1]
AUTHORITY = (
    ROOT
    / "data/base/solutions/banks/1f065edbcf08/S17_M5__19ba16363b7f.json"
)


def _canonical_inputs():
    row = json.loads(AUTHORITY.read_text())
    visible = row["visible_context"]
    return [pair["input"] for pair in visible["train"]] + [
        pair["input"] for pair in visible["test_inputs"]
    ]


def test_rule_hash_and_all_canonical_inputs_are_accepted():
    assert gen.RULE_HASH == "02a300f6b627"
    for grid in _canonical_inputs():
        assert gen.self_check(grid) == []
        assert gen.strict_canonical_like(grid) == []


def test_exact_override_boundaries_are_observable_and_unknown_keys_reject():
    grid = gen.generate(
        2718,
        99,
        difficulty="easy",
        grid_h=7,
        grid_w=15,
        n_keys=6,
        n_distract=8,
    )
    assert gen.observe_overrides(grid) == {
        "grid_h": 7,
        "grid_w": 15,
        "n_keys": 6,
        "n_distract": 8,
    }
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 0, __typo_axis=3)


def test_four_slot_schedule_realizes_each_decisive_branch():
    grids = [gen.generate(12345, index, difficulty="medium") for index in range(4)]
    assert gen.strict_canonical_like(grids[0]) == []
    assert gen.SEMANTIC_WITNESSES["modal_distractor_beats_selected"](grids[1])
    assert gen.SEMANTIC_WITNESSES["clipped_border_stamp"](grids[2])
    assert gen.rival_drop_border_selected(grids[2]) != gen.rule_mirror(grids[2])
    assert gen.SEMANTIC_WITNESSES["overlapping_stamp_union"](grids[3])


def test_modal_shortcut_is_refuted_by_scheduled_profile():
    grid = gen.generate(8675309, 1, difficulty="hard")
    assert gen.rival_modal_scene_color(grid) != gen.rule_mirror(grid)


def test_all_named_rival_claims_hold_on_their_schedule_witnesses():
    grids = [gen.generate(4242, index, difficulty="hard") for index in range(4)]
    for witness_name, rival_names in gen.WITNESS_RIVALS.items():
        witness_grids = [grid for grid in grids if gen.SEMANTIC_WITNESSES[witness_name](grid)]
        assert witness_grids, witness_name
        for grid in witness_grids:
            official = gen.rule_mirror(grid)
            assert any(gen.SEMANTIC_RIVALS[name](grid) != official for name in rival_names)


def test_self_check_rejects_four_structural_impostors():
    base = gen.generate(777, 0)

    no_legend = [row[:] for row in base]
    no_legend[0][0] = 0

    one_selected = [row[:] for row in base]
    key = one_selected[0][0]
    selected = [
        (r, c)
        for r, row in enumerate(one_selected)
        for c, value in enumerate(row)
        if value == key and (r, c) != (0, 0)
    ]
    one_selected[selected[-1][0]][selected[-1][1]] = 0

    one_distractor_color = [row[:] for row in base]
    other_colors = sorted(
        {value for row in one_distractor_color for value in row if value not in (0, 8, key)}
    )
    for r, row in enumerate(one_distractor_color):
        for c, value in enumerate(row):
            if value == other_colors[-1]:
                one_distractor_color[r][c] = other_colors[0]

    touching_legend = [row[:] for row in base]
    touching_legend[0][1] = key

    for impostor in (no_legend, one_selected, one_distractor_color, touching_legend):
        assert gen.self_check(impostor)
