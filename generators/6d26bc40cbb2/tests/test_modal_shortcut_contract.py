from __future__ import annotations

import importlib


TASK_ID = "6d26bc40cbb2"
gen = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")


def test_modal_color_only_rival_keeps_the_complete_original_payload():
    grid = [
        [9, 0, 0, 0, 0, 0, 0],
        [0, 1, 1, 0, 0, 0, 0],
        [0, 2, 0, 9, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0],
    ]

    assert gen.self_check(grid) == []
    rival = gen.rival_modal_color_only(grid)

    # A realistic shortcut deletes markers, keeps the entire original object,
    # but copies only its modal color.  The minority cell must not disappear.
    assert rival[2][1] == 2
    assert rival[3][4] == 1
    assert rival[3][5] == 1
    assert rival[4][4] == 0


def test_multicolor_generation_exposes_a_nonmodal_color_in_new_copy_area():
    # This deterministic witness previously let the realistic modal-only-copy
    # shortcut match the selected rule despite advertising a multicolor lesson.
    grid = gen.generate(1, 1, difficulty="easy")
    facts = gen.analyze_scene(grid)["facts"]
    assert facts["palette_size"] > 1

    authoritative = gen.solve_python(grid)
    rival = gen.rival_modal_color_only(grid)
    assert rival != authoritative
