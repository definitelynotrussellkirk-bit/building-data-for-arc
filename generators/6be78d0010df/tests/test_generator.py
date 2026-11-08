from __future__ import annotations

import copy
import importlib.util
import os
from pathlib import Path
import random

import pytest

from reviewer_support import canonical_pairs, find_root

TASK_ID = "6be78d0010df"
HOME = Path(__file__).resolve().parents[1]
GENERATOR_PATH = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))
SPEC = importlib.util.spec_from_file_location("generator_6be78d0010df_under_test", GENERATOR_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def _pairs():
    return canonical_pairs(TASK_ID, root=find_root(__file__))


def _crop(panel):
    cells = [
        (r, c)
        for r, row in enumerate(panel)
        for c, value in enumerate(row)
        if value != 0
    ]
    assert cells
    r0 = min(r for r, _ in cells)
    r1 = max(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    c1 = max(c for _, c in cells)
    return [row[c0 : c1 + 1] for row in panel[r0 : r1 + 1]], (r0, c0)


def _panels(grid):
    h = len(grid)
    dividers = [c for c in range(len(grid[0])) if all(grid[r][c] == 1 for r in range(h))]
    assert len(dividers) == 2
    d1, d2 = dividers
    return (
        [row[:d1] for row in grid],
        [row[d1 + 1 : d2] for row in grid],
        [row[d2 + 1 :] for row in grid],
    )


def _expected(grid):
    a_panel, b_panel, c_panel = _panels(grid)
    a, _ = _crop(a_panel)
    b, _ = _crop(b_panel)
    c, _ = _crop(c_panel)
    assert (len(a), len(a[0])) == (len(b), len(b[0]))
    mapping = {}
    for r in range(len(a)):
        for col in range(len(a[0])):
            av, bv = a[r][col], b[r][col]
            assert (av == 0) == (bv == 0)
            if av:
                if av in mapping:
                    assert mapping[av] == bv
                mapping[av] = bv
    return [[0 if value == 0 else mapping[value] for value in row] for row in c]


def _facts(grid):
    a_panel, b_panel, c_panel = _panels(grid)
    a, a_offset = _crop(a_panel)
    b, b_offset = _crop(b_panel)
    c, _ = _crop(c_panel)
    mapping = {}
    for r in range(len(a)):
        for col in range(len(a[0])):
            if a[r][col]:
                mapping[a[r][col]] = b[r][col]
    source_colors = sorted(mapping)
    mapped_colors = [mapping[color] for color in source_colors]
    return {
        "panel_n": len(grid),
        "n_colors_used": len(source_colors),
        "analogy_alignment": "aligned" if a_offset == b_offset else "shifted",
        "mapping_order": "monotone" if mapped_colors == sorted(mapped_colors) else "nonmonotone",
        "palette_size": len({value for row in grid for value in row}),
        "source_colors": set(source_colors),
        "query_colors": {value for row in c for value in row if value},
    }


def _episode(grid):
    return {"input": grid, "output": _expected(grid)}


def test_rule_pin_and_all_canonical_examples_match_the_authority():
    assert MODULE.RULE_HASH == "20d652a9b458"
    pairs = _pairs()
    assert len(pairs) == 5
    for pair in pairs:
        assert MODULE.self_check(pair["input"]) == []
        assert _expected(pair["input"]) == pair["output"]
        assert MODULE.rule_mirror(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "overrides",
    [
        {
            "panel_n": 4,
            "n_colors_used": 2,
            "analogy_alignment": "aligned",
            "mapping_order": "monotone",
        },
        {
            "panel_n": 7,
            "n_colors_used": 4,
            "analogy_alignment": "shifted",
            "mapping_order": "nonmonotone",
        },
    ],
)
def test_exact_overrides_are_observable_in_every_band(band, overrides):
    grid = MODULE.generate(77, 13, difficulty=band, **overrides)
    assert MODULE.self_check(grid) == []
    facts = _facts(grid)
    observed = MODULE.observe_overrides(grid)
    for name, value in overrides.items():
        assert facts[name] == value
        assert observed[name] == value
    assert facts["query_colors"] == facts["source_colors"]


@pytest.mark.parametrize(
    "overrides",
    [
        {"unknown": 1},
        {"panel_n": 3},
        {"panel_n": 8},
        {"panel_n": True},
        {"panel_n": 4.0},
        {"n_colors_used": 1},
        {"n_colors_used": 5},
        {"n_colors_used": "2"},
        {"analogy_alignment": "diagonal"},
        {"analogy_alignment": 1},
        {"mapping_order": "identity"},
        {"mapping_order": False},
    ],
)
def test_invalid_overrides_fail_loudly(overrides):
    with pytest.raises(ValueError):
        MODULE.generate(1, 2, **overrides)


def test_invalid_difficulty_fails_loudly():
    with pytest.raises(ValueError):
        MODULE.generate(1, 2, difficulty="extreme")


def test_self_check_rejects_the_retained_no_divider_counterexample():
    grid = [
        [4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [4, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    ]
    assert MODULE.self_check(grid)


def test_self_check_is_structural_and_mutation_sensitive():
    base = MODULE.generate(
        91,
        8,
        panel_n=6,
        n_colors_used=3,
        analogy_alignment="shifted",
        mapping_order="nonmonotone",
    )
    assert MODULE.self_check(base) == []
    d1, d2 = [
        c
        for c in range(len(base[0]))
        if all(base[r][c] == 1 for r in range(len(base)))
    ]

    mutations = {}
    changed = copy.deepcopy(base)
    changed[0][d1] = 0
    mutations["broken divider"] = changed

    changed = copy.deepcopy(base)
    changed[0][0] = 1
    mutations["stray divider color"] = changed

    changed = copy.deepcopy(base)
    b_cells = [
        (r, c)
        for r in range(len(changed))
        for c in range(d1 + 1, d2)
        if changed[r][c] not in (0, 1)
    ]
    r, c = b_cells[0]
    changed[r][c] = 0
    mutations["A/B shape mismatch"] = changed

    changed = copy.deepcopy(base)
    a_panel, b_panel, _ = _panels(changed)
    a, _ = _crop(a_panel)
    b, b_offset = _crop(b_panel)
    source = next(value for row in a for value in row if value)
    locations = [(r, c) for r, row in enumerate(a) for c, value in enumerate(row) if value == source]
    if len(locations) >= 2:
        rr, cc = locations[-1]
        current = b[rr][cc]
        replacement = next(color for color in range(2, 10) if color != current and color not in {source})
        changed[b_offset[0] + rr][d1 + 1 + b_offset[1] + cc] = replacement
        mutations["inconsistent color map"] = changed

    changed = copy.deepcopy(base)
    c_cells = [
        (r, c)
        for r in range(len(changed))
        for c in range(d2 + 1, len(changed[0]))
        if changed[r][c] not in (0, 1)
    ]
    r, c = c_cells[0]
    used = {value for row in changed for value in row}
    changed[r][c] = next(color for color in range(2, 10) if color not in used)
    mutations["foreign query color"] = changed

    changed = copy.deepcopy(base)
    for r in range(len(changed)):
        for c in range(d2 + 1, len(changed[0])):
            changed[r][c] = 0
    mutations["empty query"] = changed

    for name, changed in mutations.items():
        assert MODULE.self_check(changed), name

    assert MODULE.self_check([])
    assert MODULE.self_check([[0], [0, 1]])
    assert MODULE.self_check([[True] * 20 for _ in range(6)])


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_four_draw_schedule_covers_profile_and_both_shortcut_witnesses(band):
    for start in range(8):
        grids = [MODULE.generate(1234, start + offset, difficulty=band) for offset in range(4)]
        facts = [_facts(grid) for grid in grids]
        assert any(
            len(grid) == 6 and len(grid[0]) == 20 and fact["palette_size"] in {4, 6}
            for grid, fact in zip(grids, facts)
        )
        assert any(fact["analogy_alignment"] == "shifted" for fact in facts)
        assert any(fact["mapping_order"] == "nonmonotone" for fact in facts)


def test_default_draws_are_deterministic_lawful_and_match_an_independent_oracle():
    random.seed(20261011)
    state = random.getstate()
    for band in (None, "easy", "medium", "hard"):
        for index in range(48):
            grid = MODULE.generate(700 + index, index, difficulty=band)
            assert random.getstate() == state
            assert grid == MODULE.generate(700 + index, index, difficulty=band)
            assert MODULE.self_check(grid) == []
            assert MODULE.rule_mirror(grid) == _expected(grid)
            facts = _facts(grid)
            assert facts["query_colors"] == facts["source_colors"]


def test_sorted_palette_shortcut_fits_canonical_demos_but_not_the_held_out_case():
    pairs = _pairs()
    rival = MODULE.SEMANTIC_RIVALS["sorted_palette_mapping"]
    assert all(rival(pair["input"]) == pair["output"] for pair in pairs[:4])
    assert rival(pairs[4]["input"]) != pairs[4]["output"]


def test_generated_witnesses_refute_both_declared_rivals():
    nonmonotone = MODULE.generate(
        19,
        1,
        panel_n=6,
        n_colors_used=3,
        analogy_alignment="aligned",
        mapping_order="nonmonotone",
    )
    assert MODULE.SEMANTIC_WITNESSES["nonmonotone_mapping"](nonmonotone)
    assert MODULE.SEMANTIC_RIVALS["sorted_palette_mapping"](nonmonotone) != _expected(nonmonotone)

    shifted = MODULE.generate(
        23,
        2,
        panel_n=6,
        n_colors_used=3,
        analogy_alignment="shifted",
        mapping_order="monotone",
    )
    assert MODULE.SEMANTIC_WITNESSES["independent_panel_offsets"](shifted)
    assert MODULE.CANONICAL_SHORTCUTS["aligned_panels_only"](shifted) != _expected(shifted)
    assert all(
        MODULE.CANONICAL_SHORTCUTS["aligned_panels_only"](pair["input"]) == pair["output"]
        for pair in _pairs()
    )


def test_lesson_hook_accepts_scheduled_windows_and_flags_an_ambiguous_manual_window():
    for band in ("easy", "medium", "hard"):
        for start in range(8):
            items = [_episode(MODULE.generate(88, start + offset, difficulty=band)) for offset in range(5)]
            assert MODULE.lesson_identifiable(items[:4], items[4]) == []

    demos = [
        _episode(
            MODULE.generate(
                55,
                index,
                panel_n=6,
                n_colors_used=2,
                analogy_alignment="aligned",
                mapping_order="monotone",
            )
        )
        for index in range(4)
    ]
    query = _episode(
        MODULE.generate(
            55,
            9,
            panel_n=6,
            n_colors_used=2,
            analogy_alignment="shifted",
            mapping_order="nonmonotone",
        )
    )
    reasons = MODULE.lesson_identifiable(demos, query)
    assert any("sorted_palette_mapping" in reason for reason in reasons)
    assert any("aligned_panels_only" in reason for reason in reasons)


def _singleton_nonzero_components(grid):
    remaining = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0
    }
    singleton_count = 0
    while remaining:
        start = min(remaining)
        color = grid[start[0]][start[1]]
        component = {start}
        todo = [start]
        remaining.remove(start)
        while todo:
            r, c = todo.pop()
            for neighbor in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if neighbor in remaining and grid[neighbor[0]][neighbor[1]] == color:
                    remaining.remove(neighbor)
                    component.add(neighbor)
                    todo.append(neighbor)
        if len(component) == 1:
            singleton_count += 1
    return singleton_count


def test_generated_inputs_stay_inside_canonical_marker_count_support():
    for band in ("easy", "medium", "hard"):
        for index in range(24):
            grid = MODULE.generate(321, index, difficulty=band)
            assert _singleton_nonzero_components(grid) in {0, 2}
