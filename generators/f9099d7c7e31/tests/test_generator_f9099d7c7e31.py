from __future__ import annotations

import copy

import pytest

from puzzle_generators.per_puzzle.f9099d7c7e31 import generator as gen
from scripts.canonical_profile_gate import canonical_pairs


TASK_ID = "f9099d7c7e31"


def _blank(h: int = 9, w: int = 9):
    return [[0 for _ in range(w)] for _ in range(h)]


def test_rule_hash_and_canonical_inputs_are_authority_valid():
    # Assert the DERIVED invariant, not a frozen literal. The return shipped
    # `409d9300e4e0` here, but its own racket__f9099d7c7e31.patch adds a comment
    # to the canonical program_solution, which changes the normalized hash to
    # 9a6f1f4b6ce5 — so the packet's test contradicted the packet's patch.
    # RULE_HASH is *defined* as sha256(whitespace-normalized canonical)[:12]
    # (scripts/generator_defect_lint.probe_rule_hash), so derive it and the
    # assertion can never go stale against a lawful beautification again.
    import hashlib
    import json
    from pathlib import Path

    program = None
    canonical = Path(__file__).resolve().parents[1] / "data/canonical/puzzles.jsonl"
    with canonical.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("content_hash") == TASK_ID:
                program = row["program_solution"]
                break
    assert program is not None, f"no canonical row for {TASK_ID}"
    expected = hashlib.sha256(" ".join(program.split()).encode()).hexdigest()[:12]
    assert gen.RULE_HASH == expected
    pairs = canonical_pairs(TASK_ID)
    assert len(pairs) == 5
    for pair in pairs:
        assert gen.self_check(copy.deepcopy(pair["input"])) == []


def test_exact_overrides_are_observed_in_every_band():
    requested = {
        "grid_h": 9,
        "grid_w": 11,
        "n_objects": 3,
        "target_width": 4,
        "target_height": 2,
        "selection_mode": "width_tie_size",
        "intruder_in_crop": True,
        "larger_narrow_decoy": True,
    }
    for band in ("easy", "medium", "hard"):
        grid = gen.generate(9917, 2, difficulty=band, **requested)
        observed = gen.observe_overrides(grid)
        assert {key: observed[key] for key in requested} == requested
        assert gen.self_check(grid) == []


def test_unknown_and_retired_texture_overrides_fail_loudly():
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(0, 0, bogus_axis=1)
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(0, 0, texture="no_blobs")


def test_scheduled_counterexamples_change_all_named_rivals():
    grids = [gen.generate(431, index, difficulty="medium") for index in range(4)]
    canonical = [gen._canonical_transform(grid) for grid in grids]
    for rival_name, rival in gen.LESSON_COMPETITORS.items():
        assert any(rival(grid) != answer for grid, answer in zip(grids, canonical)), rival_name

    assert any(gen.SEMANTIC_WITNESSES["foreign_cell_inside_crop"](grid) for grid in grids)
    assert any(gen.SEMANTIC_WITNESSES["narrower_object_has_more_cells"](grid) for grid in grids)
    assert any(gen.SEMANTIC_WITNESSES["width_tie_resolved_by_size"](grid) for grid in grids)
    assert any(gen.SEMANTIC_WITNESSES["target_not_leftmost"](grid) for grid in grids)


def test_foreign_cell_is_preserved_by_crop_not_masked_away():
    grid = gen.generate(17, 1, difficulty="easy")
    assert gen.observe_overrides(grid)["intruder_in_crop"] is True
    assert gen._canonical_transform(grid) != gen._mask_winner_only(grid)


def test_self_check_rejects_named_minimal_impostors_and_ambiguity():
    all_background = _blank()

    singleton = _blank()
    singleton[4][4] = 1

    solid_2x2 = _blank()
    for r in (3, 4):
        for c in (3, 4):
            solid_2x2[r][c] = 2

    short_line = _blank()
    short_line[4][3:6] = [3, 3, 3]

    ambiguous = _blank()
    for c in range(1, 5):
        ambiguous[2][c] = 1
        ambiguous[6][c] = 2
    ambiguous[1][1] = 1
    ambiguous[5][1] = 2
    ambiguous[8][6:8] = [3, 3]
    ambiguous[7][6] = 3

    too_narrow = _blank()
    too_narrow[1][1:4] = [1, 1, 1]
    too_narrow[2][1] = 1
    too_narrow[5][1:3] = [2, 2]
    too_narrow[6][1] = 2
    too_narrow[7][6:8] = [3, 3]
    too_narrow[8][6] = 3

    cases = {
        "all_background": all_background,
        "singleton": singleton,
        "solid_2x2": solid_2x2,
        "short_line": short_line,
        "equal_top_key": ambiguous,
        "selected_width_three": too_narrow,
    }
    for name, grid in cases.items():
        assert gen.self_check(grid), name
