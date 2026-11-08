from __future__ import annotations

import random

import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator


ROOT = find_root(__file__)
gen, _, _ = load_selected_generator("038f266f3acf", root=ROOT)


def test_canonical_inputs_are_accepted_and_python_mirror_is_exact() -> None:
    pairs = canonical_pairs(gen.TASK_ID, root=ROOT)
    assert len(pairs) == 10
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]


def test_every_profile_override_is_exact_and_unknown_axes_reject() -> None:
    for band in ("easy", "medium", "hard"):
        for index, profile in enumerate(gen.SCHEDULE_PROFILES):
            grid = gen.generate(
                9100 + index,
                index,
                difficulty=band,
                profile=profile,
            )
            assert gen.self_check(
                grid,
                meta={"overrides": {"profile": profile}},
            ) == []
            assert gen.observe_overrides(grid) == {"profile": profile}
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 0, not_an_axis="typo")


def test_self_check_rejects_targeted_rule_hiding_mutations() -> None:
    base = gen.generate(1201, 0, profile="small_pair")
    analysis = gen._analysis(base)
    first = analysis["rectangles"][0]
    r1, c1, r2, c2 = first["bbox"]
    marker_r, marker_c = first["marker"]

    missing_marker = [row[:] for row in base]
    missing_marker[marker_r][marker_c] = 3
    assert gen.self_check(missing_marker)

    extra_marker = [row[:] for row in base]
    extra_cell = next(
        (r, c)
        for r in range(r1, r2 + 1)
        for c in range(c1, c2 + 1)
        if (r, c) != (marker_r, marker_c)
    )
    extra_marker[extra_cell[0]][extra_cell[1]] = 2
    assert gen.self_check(extra_marker)

    corner_marker = [row[:] for row in base]
    corner_marker[marker_r][marker_c] = 3
    corner_marker[r1][c1] = 2
    assert gen.self_check(corner_marker)

    holed_rectangle = [row[:] for row in base]
    interior_or_green = next(
        (r, c)
        for r in range(r1, r2 + 1)
        for c in range(c1, c2 + 1)
        if base[r][c] == 3
    )
    holed_rectangle[interior_or_green[0]][interior_or_green[1]] = 0
    assert gen.self_check(holed_rectangle)

    foreign_color = [row[:] for row in base]
    foreign_color[0][0] = 4
    assert gen.self_check(foreign_color)


def test_every_four_slot_lesson_kills_all_named_competitors() -> None:
    for band in ("easy", "medium", "hard"):
        for start in range(8):
            demos = []
            for sample_index in range(start, start + gen.EXAMPLES_NEEDED):
                grid = gen.generate(6000 + start, sample_index, difficulty=band)
                demos.append({"input": grid, "output": gen.rule_mirror(grid)})
            query_grid = gen.generate(
                7000 + start,
                start + gen.EXAMPLES_NEEDED,
                difficulty=band,
            )
            assert gen.lesson_identifiable(demos, {"input": query_grid}) == []
            for competitor in gen.LESSON_COMPETITORS.values():
                assert any(
                    competitor(demo["input"]) != demo["output"]
                    for demo in demos
                )


def test_generation_is_deterministic_fresh_and_global_rng_pure() -> None:
    random.seed(99117)
    before = random.getstate()
    first = gen.generate(33, 17, difficulty="hard")
    after = random.getstate()
    second = gen.generate(33, 17, difficulty="hard")
    assert first == second
    assert first is not second
    assert first[0] is not second[0]
    assert before == after
