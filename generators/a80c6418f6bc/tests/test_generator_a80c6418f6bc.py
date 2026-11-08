from __future__ import annotations

import copy
import importlib

TASK_ID = "a80c6418f6bc"
MODULE = importlib.import_module(
    f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
)
from reviewer_support import canonical_pairs, find_root

ROOT = find_root(__file__)


def _canonical_pairs():
    return canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)


def _mutate_panel_cell(grid, quadrant, relative_cell, value):
    out = copy.deepcopy(grid)
    info = MODULE._analysis(out)
    q = info["q"]
    panel_key = {"a": "ai", "b": "bi", "c": "ci"}[quadrant]
    r0, c0 = info[panel_key]["origin"]
    r, c = relative_cell
    gr = r0 + r + (q + 1 if quadrant == "c" else 0)
    gc = c0 + c + (q + 1 if quadrant == "b" else 0)
    out[gr][gc] = value
    return out


def test_rule_hash_matches_selected_authority():
    assert MODULE.RULE_HASH == "88309ffec80e"


def test_self_check_accepts_every_canonical_input():
    pairs = _canonical_pairs()
    assert len(pairs) == 3
    for pair in pairs:
        assert MODULE.self_check(pair["input"]) == []


def test_sequential_schedule_covers_shortcut_breaking_branches():
    observations = [
        MODULE.observe_overrides(MODULE.generate(1234, index, difficulty="medium"))
        for index in range(4)
    ]
    assert [item["delta_mode"] for item in observations] == [
        "within_bbox",
        "expand_right",
        "expand_down",
        "expand_both",
    ]
    assert [item["delta_count"] for item in observations] == [1, 2, 3, 1]
    assert [item["placement_mode"] for item in observations] == [
        "aligned",
        "offset",
        "aligned",
        "offset",
    ]
    assert [item["query_relation"] for item in observations] == [
        "same_shape",
        "different_shape",
        "different_shape",
        "different_shape",
    ]


def test_exact_override_matrix_is_observable():
    cases = [
        {"quad_size": 6, "delta_count": 3, "delta_mode": "within_bbox", "placement_mode": "offset", "query_relation": "different_shape"},
        {"quad_size": 8, "delta_count": 1, "delta_mode": "expand_both", "placement_mode": "aligned", "query_relation": "same_shape"},
    ]
    for index, case in enumerate(cases):
        grid = MODULE.generate(900 + index, 7 + index, difficulty="hard", **case)
        observed = MODULE.observe_overrides(grid)
        assert {key: observed[key] for key in case} == case
        assert MODULE.self_check(grid) == []


def test_self_check_rejects_four_targeted_impostors():
    grid = MODULE.generate(
        77,
        1,
        difficulty="medium",
        delta_mode="within_bbox",
        delta_count=2,
        query_relation="different_shape",
    )
    info = MODULE._analysis(grid)
    demo_color = next(iter(info["ai"]["colors"]))
    query_color = next(iter(info["ci"]["colors"]))
    delta_cell = next(iter(info["delta"]))
    source_cell = next(iter(info["ai"]["relative"]))

    prefilled = copy.deepcopy(grid)
    q = info["q"]
    prefilled[q + 1][q + 1] = query_color
    assert any("answer quadrant" in error for error in MODULE.self_check(prefilled))

    hidden_delta = _mutate_panel_cell(grid, "c", delta_cell, query_color)
    assert any("hiding the edit" in error for error in MODULE.self_check(hidden_delta))

    removed_source = _mutate_panel_cell(grid, "b", source_cell, 0)
    assert any("removes or shifts" in error for error in MODULE.self_check(removed_source))

    recolored_demo = _mutate_panel_cell(grid, "b", source_cell, query_color)
    errors = MODULE.self_check(recolored_demo)
    assert any("monochrome" in error or "same demonstration color" in error for error in errors)


def test_generated_returns_are_fresh_and_deterministic():
    first = MODULE.generate(51, 2, difficulty="hard")
    replay = MODULE.generate(51, 2, difficulty="hard")
    assert first == replay
    assert first is not replay
    first[0][0] = (first[0][0] + 1) % 9
    assert MODULE.generate(51, 2, difficulty="hard") == replay


def _candidate_output(grid, kind):
    info = MODULE._analysis(grid)
    q = info["q"]
    out = [row[:] for row in grid]
    for r in range(q):
        for c in range(q):
            out[q + 1 + r][q + 1 + c] = 0
    query_color = next(iter(info["ci"]["colors"]))
    cr0, cc0 = info["ci"]["origin"]
    if kind == "delta_transfer":
        cells = info["ci"]["relative"] | info["delta"]
    elif kind == "copy_b_silhouette":
        cells = info["bi"]["relative"]
    elif kind == "copy_c_only":
        cells = info["ci"]["relative"]
    elif kind == "fill_target_bbox":
        cells = {
            (r, c)
            for r in range(info["bi"]["height"])
            for c in range(info["bi"]["width"])
        }
    elif kind == "absolute_panel_delta":
        return MODULE._absolute_position_shortcut_output(grid)
    else:
        raise AssertionError(kind)
    for r, c in cells:
        out[q + 1 + cr0 + r][q + 1 + cc0 + c] = query_color
    return out


def test_each_ordinary_lesson_has_one_candidate_query_answer():
    candidates = (
        "delta_transfer",
        "copy_b_silhouette",
        "copy_c_only",
        "fill_target_bbox",
        "absolute_panel_delta",
    )
    for seed in range(100):
        demos = [MODULE.generate(seed, index, difficulty="medium") for index in range(3)]
        query = MODULE.generate(seed, 3, difficulty="medium")
        survivors = [
            candidate
            for candidate in candidates
            if all(
                _candidate_output(demo, candidate) == MODULE._mirror_output(demo)
                for demo in demos
            )
        ]
        assert "delta_transfer" in survivors
        answers = {_candidate_output(query, candidate).__repr__() for candidate in survivors}
        assert len(answers) == 1, (seed, survivors)


def test_generate_preserves_process_global_rng_state():
    import random

    random.seed(20260724)
    before = random.getstate()
    MODULE.generate(123, 3, difficulty="hard")
    after = random.getstate()
    assert after == before


def test_within_bbox_default_override_never_seed_rejects_tiny_domains():
    """Regression for exact-override seeds whose 3x3 query had one legal perturbation."""
    for difficulty, seed in (
        ("easy", 7),
        ("easy", 16),
        ("medium", 16),
        ("hard", 16),
    ):
        grid = MODULE.generate(
            seed,
            seed * 17 + 3,
            difficulty=difficulty,
            delta_mode="within_bbox",
        )
        observed = MODULE.observe_overrides(grid)
        assert observed["delta_mode"] == "within_bbox"
        assert observed["query_relation"] == "different_shape"
        assert MODULE.self_check(grid, difficulty=difficulty) == []
