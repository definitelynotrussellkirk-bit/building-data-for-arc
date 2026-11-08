"""Lesson-hook regressions using source-bound generated inputs, never canonical labels.

The five fixtures are the unmodified v2.1.0 seed=1042, difficulty="easy",
sample_index=0..4 inputs. Freezing them prevents later generation diversity or
VERSION changes from silently replacing the concrete contract reproducer.
The registry is pinned to the nine rivals present at discovery, so a future
newly declared teaching branch cannot obscure a schedule-only regression.
"""
from __future__ import annotations

from copy import deepcopy

from puzzle_generators.per_puzzle.cc8c719680e6 import generator as gen

BASELINE_SHA256 = "fcb5e074619f09fc2cdbac112de79105426765a444efe592284d15f071d52a78"
_ORIGINAL_RIVALS = (
    "identity", "solid_bbox", "preserve_source_then_frame",
    "existing_bbox_border_only", "one_global_bbox", "one_bbox_per_color",
    "fixed_color_8", "drop_border_touching_components", "drop_interior_components",
)

_BASELINE_INPUT_ROWS = (
    ('0440000', '0400000', '0444000', '0000000', '0000001', '0000011', '0000001'),
    ('0000000000000', '0000000000000', '8800000000066', '0880000000060', '0080000000000', '0000000000000', '0000000000000', '7000000000099', '7700000000090'),
    ('000000000', '000000000', '066000000', '060000000', '066660000', '000000500', '000005550', '000000500', '000000000'),
    ('000000000', '003000000', '003300000', '000330010', '000000110', '000000000', '000000000', '000000000', '000000000', '000000000', '000000300', '000003300', '000000000'),
    ('0220000', '0200000', '0222000', '0000000', '0000030', '0000330', '0000030'),
)


def _baseline_pairs():
    grids = [[[int(cell) for cell in row] for row in rows] for rows in _BASELINE_INPUT_ROWS]
    return [{"input": grid, "output": gen.rule_mirror(grid)} for grid in grids]


def _pin_original_competitors(monkeypatch):
    monkeypatch.setattr(
        gen, "LESSON_COMPETITORS",
        {name: gen.SEMANTIC_RIVALS[name] for name in _ORIGINAL_RIVALS},
    )


def test_rotated_lesson_refutes_all_rivals_without_full_axis_coverage(monkeypatch):
    _pin_original_competitors(monkeypatch)
    pairs = _baseline_pairs()
    demos = [pairs[index] for index in (0, 2, 3, 4)]
    query = pairs[1]
    assert all(gen.self_check(pair["input"]) == [] for pair in [*demos, query])
    assert all(
        any(rival(pair["input"]) != pair["output"] for pair in demos)
        for rival in gen.LESSON_COMPETITORS.values()
    )
    before = deepcopy((demos, query))
    assert gen.lesson_identifiable(demos, query) == []
    assert (demos, query) == before


def test_self_check_valid_seven_by_eight_demo_does_not_crash_partial_observer(monkeypatch):
    _pin_original_competitors(monkeypatch)
    pairs = _baseline_pairs()
    padded = [[*row, 0] for row in pairs[0]["input"]]
    assert len(padded) == 7 and all(len(row) == 8 for row in padded)
    assert gen.self_check(padded) == []
    padded_pair = {"input": padded, "output": gen.rule_mirror(padded)}
    demos = [padded_pair, *pairs[1:4]]
    before = deepcopy((demos, pairs[4]))
    assert gen.lesson_identifiable(demos, pairs[4]) == []
    assert (demos, pairs[4]) == before


def test_malformed_demo_and_query_return_findings_without_raising(monkeypatch):
    _pin_original_competitors(monkeypatch)
    pairs = _baseline_pairs()
    malformed = (
        None,
        {},
        {"output": pairs[0]["output"]},
        {"input": pairs[0]["input"]},
        {"input": None, "output": pairs[0]["output"]},
    )
    for invalid in malformed:
        # A bad first demo followed by a complete valid lesson used to reach
        # competitor evaluation after validation and raise a second exception.
        demos = [deepcopy(invalid), *deepcopy(pairs[:4])]
        query = deepcopy(pairs[4])
        before = deepcopy((demos, query))
        reasons = gen.lesson_identifiable(demos, query)
        assert isinstance(reasons, list) and reasons
        assert all(isinstance(reason, str) for reason in reasons)
        assert (demos, query) == before

        reasons = gen.lesson_identifiable(deepcopy(pairs[:4]), deepcopy(invalid))
        assert isinstance(reasons, list) and reasons
        assert all(isinstance(reason, str) for reason in reasons)
