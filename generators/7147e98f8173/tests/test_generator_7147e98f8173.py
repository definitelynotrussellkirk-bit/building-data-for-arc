from __future__ import annotations

from collections import defaultdict
import copy
import random

import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK = "7147e98f8173"
ROOT = find_root(__file__)
gen, _, _ = load_selected_generator(TASK, root=ROOT)


def _labeled_pairs():
    return canonical_pairs(TASK, root=ROOT, labeled_only=True)


def test_canonical_authority_and_python_mirror_are_exact():
    assert gen.RULE_HASH == "228397e84af8"
    pairs = _labeled_pairs()
    assert len(pairs) == 5
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]


def test_strongest_canonical_shortcut_is_executable_and_refuted_by_query():
    pairs = _labeled_pairs()
    train = [pair for pair in pairs if pair["split"] == "train"]
    test = [pair for pair in pairs if pair["split"] == "test"]
    rival = gen.CANONICAL_SHORTCUTS["corner_fixed_vector"]

    assert len(train) == 4 and len(test) == 1
    assert all(rival(pair["input"]) == pair["output"] for pair in train)
    assert rival(test[0]["input"]) != test[0]["output"]


def test_unknown_axes_invalid_scalars_and_zero_vector_are_rejected():
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 0, typo_axis=1)
    for bad_index in (True, False, 1.0, "1", -1):
        with pytest.raises(ValueError, match="sample_index"):
            gen.generate(1, bad_index)
    for bad_value in (True, 1.0, "10"):
        with pytest.raises(ValueError, match="grid_h"):
            gen.generate(1, 0, grid_h=bad_value)
    with pytest.raises(ValueError, match="vector_dr.*vector_dc"):
        gen.generate(1, 0, vector_dr=0, vector_dc=0)


def test_boundary_overrides_are_observable_and_exact():
    cases = (
        dict(grid_h=10, grid_w=12, corner="tl", template="l3_down", vector_dr=-4, vector_dc=4),
        dict(grid_h=16, grid_w=18, corner="tr", template="l3_right", vector_dr=4, vector_dc=-4),
        dict(grid_h=11, grid_w=13, corner="br", template="hook4", vector_dr=0, vector_dc=4),
        dict(grid_h=15, grid_w=17, corner="bl", template="stair4", vector_dr=-4, vector_dc=0),
    )
    for index, overrides in enumerate(cases):
        grid = gen.generate(100 + index, index, difficulty="hard", **overrides)
        assert gen.self_check(grid, meta={"overrides": overrides}) == []
        assert gen.observe_overrides(grid) == overrides
        assert any(value == 8 for row in gen.rule_mirror(grid) for value in row)


def test_every_corner_template_and_extreme_vector_is_constructive():
    vectors = ((-4, -4), (-4, 4), (4, -4), (4, 4), (0, -4), (4, 0))
    for corner_index, corner in enumerate(("tl", "tr", "br", "bl")):
        for template_index, template in enumerate(("l3_down", "l3_right", "hook4", "stair4")):
            dr, dc = vectors[(corner_index + template_index) % len(vectors)]
            overrides = {
                "grid_h": 10,
                "grid_w": 12,
                "corner": corner,
                "template": template,
                "vector_dr": dr,
                "vector_dc": dc,
            }
            grid = gen.generate(300 + corner_index, template_index, **overrides)
            assert gen.observe_overrides(grid) == overrides
            assert gen.self_check(grid) == []


def test_schedule_decouples_corner_vector_and_survives_every_query_rotation():
    assert gen.LESSON_SCHEDULE_PERIOD == 4
    assert gen.EXAMPLES_NEEDED == 7

    for difficulty in ("easy", "medium", "hard"):
        pairs = []
        for sample_index in range(gen.EXAMPLES_NEEDED + 1):
            grid = gen.generate(81173, sample_index, difficulty=difficulty)
            pairs.append({"input": grid, "output": gen.rule_mirror(grid)})

        corner_to_vectors = defaultdict(set)
        vector_to_corners = defaultdict(set)
        for pair in pairs:
            observed = gen.observe_overrides(pair["input"])
            vector = (observed["vector_dr"], observed["vector_dc"])
            corner_to_vectors[observed["corner"]].add(vector)
            vector_to_corners[vector].add(observed["corner"])
        assert any(len(vectors) >= 2 for vectors in corner_to_vectors.values())
        assert any(len(corners) >= 2 for corners in vector_to_corners.values())

        for query_index, query in enumerate(pairs):
            demos = [pair for index, pair in enumerate(pairs) if index != query_index]
            assert gen.lesson_identifiable(demos, query) == []


def test_default_schedule_contains_canonical_support_and_kills_all_rivals():
    for difficulty in ("easy", "medium", "hard"):
        grids = [gen.generate(915, index, difficulty=difficulty) for index in range(8)]
        assert any(gen.strict_canonical_like(grid) == [] for grid in grids)
        for rival_name, rival in gen.LESSON_COMPETITORS.items():
            assert any(rival(grid) != gen.rule_mirror(grid) for grid in grids), rival_name


def test_self_check_rejects_targeted_impostors():
    base = gen.generate(777, 2, difficulty="medium")
    observed = gen.observe_overrides(base)
    assert observed

    bad = copy.deepcopy(base)
    green = next((r, c) for r, row in enumerate(bad) for c, value in enumerate(row) if value == 3)
    bad[green[0]][green[1]] = 0
    assert gen.self_check(bad)

    bad = copy.deepcopy(base)
    blue = next((r, c) for r, row in enumerate(bad) for c, value in enumerate(row) if value == 1)
    other_corner = next(pos for pos in ((0, 0), (0, len(bad[0]) - 1), (len(bad) - 1, len(bad[0]) - 1), (len(bad) - 1, 0)) if pos != blue)
    bad[other_corner[0]][other_corner[1]] = 1
    assert gen.self_check(bad)

    bad = copy.deepcopy(base)
    red = [(r, c) for r, row in enumerate(bad) for c, value in enumerate(row) if value == 2]
    bad[red[-1][0]][red[-1][1]] = 0
    bad[len(bad) // 2][len(bad[0]) // 2] = 2
    assert gen.self_check(bad)


def test_deterministic_fresh_return_and_global_rng_preserved():
    random.seed(123456789)
    before = random.getstate()
    a = gen.generate(4545, 6, difficulty="hard")
    after = random.getstate()
    b = gen.generate(4545, 6, difficulty="hard")
    assert before == after
    assert a == b
    assert a is not b
    assert all(row_a is not row_b for row_a, row_b in zip(a, b))
    a[0][0] = (a[0][0] + 1) % 10
    assert a != b


def test_workspace_contract_probe_is_reusable_and_complete():
    import importlib.util

    path = ROOT / "generators" / TASK / "workspace" / "probe_contract.py"
    spec = importlib.util.spec_from_file_location("probe_contract_7147e98f8173", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    report = module.probe(seed=915)
    assert report["task_id"] == TASK
    assert report["generator_sha256"]
    assert report["bands"] == {"easy": 8, "medium": 8, "hard": 8}
    assert report["lesson_rotations_checked"] == 24
    assert report["lesson_failures"] == []
    assert report["rivals_refuted"] == sorted(gen.LESSON_COMPETITORS)
