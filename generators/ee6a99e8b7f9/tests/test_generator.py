"""Focused source-bound regressions for ee6a99e8b7f9."""
from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import canonical_pairs, geometry_output, load_generator, observed, shapes

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))


@pytest.mark.parametrize("pair", canonical_pairs(), ids=lambda p: f"v{p['variant']}-{p['split']}{p['pair_index']}")
def test_canonical_pairs_are_owned_and_match_independent_geometry(pair):
    assert gen.self_check(pair["input"]) == []
    assert geometry_output(pair["input"]) == pair["output"]
    assert gen.rule_mirror(pair["input"]) == pair["output"]


def test_rule_hash_is_pinned_to_assignment_authority():
    assert gen.RULE_HASH == "faea8048f031"


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("h,w,n", [(9, 9, 1), (9, 18, 7), (18, 9, 7), (18, 18, 7), (13, 15, 4)])
def test_exact_overrides_are_constructive_and_observable(band, h, w, n):
    grid = gen.generate(117, h * 100 + w * 10 + n, difficulty=band,
                        grid_h=h, grid_w=w, n_shapes=n)
    assert gen.self_check(grid) == []
    assert observed(grid)["grid_h"] == h
    assert observed(grid)["grid_w"] == w
    assert observed(grid)["n_shapes"] == n
    assert gen.observe_overrides(grid) == {"grid_h": h, "grid_w": w, "n_shapes": n}


@pytest.mark.parametrize("kwargs", [
    {"typo": 1}, {"grid_h": 8}, {"grid_h": 19}, {"grid_w": 8}, {"grid_w": 19},
    {"n_shapes": 0}, {"n_shapes": 8}, {"grid_h": True}, {"n_shapes": 2.5},
])
def test_invalid_overrides_fail_loudly(kwargs):
    with pytest.raises((TypeError, ValueError, KeyError)):
        gen.generate(0, 0, **kwargs)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_four_profile_schedule_has_canonical_anchors_and_generalization(band):
    stats = []
    for index in range(8):
        grid = gen.generate(500 + index, index, difficulty=band)
        assert gen.self_check(grid) == []
        assert grid == gen.generate(500 + index, index, difficulty=band)
        assert geometry_output(grid) == gen.rule_mirror(grid)
        stats.append(observed(grid))
    assert {(s["grid_h"], s["grid_w"], len(set([8, 9] + s["colors"]))) for s in stats[:4]} == {
        (9, 9, 3), (11, 11, 4), (15, 15, 4), (13, 13, 4)
    }
    assert all(size == (3, 3) for s in stats[:2] for size in s["shape_sizes"])
    assert any(size != (3, 3) for s in stats[2:4] for size in s["shape_sizes"])
    assert all(max(s["dot_counts"]) >= 2 for s in stats[1:4])
    assert any(s["border_shapes"] for s in stats[:4])


def test_canonical_shortcut_really_fits_canonical_and_is_refuted_by_schedule():
    rival = gen.CANONICAL_SHORTCUTS["fixed_inward_steps"]
    assert all(rival(pair["input"]) == pair["output"] for pair in canonical_pairs())
    for start in range(8):
        grids = [gen.generate(9000 + start, start + offset) for offset in range(5)]
        disagreements = [rival(grid) != gen.rule_mirror(grid) for grid in grids]
        assert sum(disagreements) >= 2
        pairs = [{"input": g, "output": gen.rule_mirror(g)} for g in grids]
        for query_index in range(5):
            demos = [p for i, p in enumerate(pairs) if i != query_index]
            assert gen.lesson_identifiable(demos, pairs[query_index]) == []


def test_all_declared_rivals_are_pure_and_each_five_pair_window_is_rotation_safe():
    for start in range(8):
        grids = [gen.generate(12000 + start, start + offset, difficulty="hard") for offset in range(5)]
        pairs = [{"input": grid, "output": gen.rule_mirror(grid)} for grid in grids]
        for name, rival in gen.LESSON_COMPETITORS.items():
            before = deepcopy(grids)
            first = [rival(grid) for grid in grids]
            second = [rival(grid) for grid in grids]
            assert grids == before, name
            assert first == second, name
            for query_index in range(5):
                demos = [i for i in range(5) if i != query_index]
                fits = all(first[i] == pairs[i]["output"] for i in demos)
                ambiguous = fits and first[query_index] != pairs[query_index]["output"]
                assert not ambiguous, (start, query_index, name)


@pytest.mark.parametrize("mutation", ["unknown_color", "ragged", "hollow_shape", "orphan_dot", "remove_dots"])
def test_validator_rejects_destructive_mutations(mutation):
    grid = gen.generate(31, 2)
    if mutation == "unknown_color":
        grid[0][0] = 0
    elif mutation == "ragged":
        grid[0].pop()
    elif mutation == "hollow_shape":
        for r, row in enumerate(grid):
            for c, value in enumerate(row):
                if value in (5, 6):
                    grid[r][c] = 8
                    break
            else:
                continue
            break
    elif mutation == "orphan_dot":
        occupied = set().union(*(shape["cells"] for shape in shapes(grid)))
        r, c = next((r, c) for r, row in enumerate(grid) for c, value in enumerate(row)
                    if value == 8 and all(abs(r - rr) + abs(c - cc) > 1 for rr, cc in occupied))
        grid[r][c] = 9
    elif mutation == "remove_dots":
        grid = [[8 if value == 9 else value for value in row] for row in grid]
    assert gen.self_check(grid)


@pytest.mark.parametrize("grid", [None, [], [[]], [[8], [8, 8]], [[True] * 9 for _ in range(9)]])
def test_malformed_grid_is_diagnostic_not_exception(grid):
    assert gen.self_check(grid)


def test_keyed_rng_is_independent_of_python_hash_seed():
    script = ("import importlib.util,json,sys;"
              "p=sys.argv[1];s=importlib.util.spec_from_file_location('g',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);"
              "print(json.dumps(m.generate(812,17,difficulty='hard')))" )
    outputs = []
    for seed in ("1", "909"):
        env = dict(os.environ, PYTHONHASHSEED=seed, PYTHONDONTWRITEBYTECODE="1")
        outputs.append(subprocess.check_output([sys.executable, "-B", "-c", script, str(HOME / "generator.py")],
                                               env=env, text=True))
    assert outputs[0] == outputs[1]


@pytest.mark.parametrize(
    "seed,sample_index,difficulty",
    [
        (True, 0, None),
        (1.0, 0, None),
        ("1", 0, None),
        (0, True, None),
        (0, 1.0, None),
        (0, "1", None),
        (0, -1, None),
        (0, 0, True),
        (0, 0, 0),
        (0, 0, 1.0),
        (0, 0, "__invalid_difficulty__"),
    ],
)
def test_invalid_call_scalars_fail_loudly(seed, sample_index, difficulty):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(seed, sample_index, difficulty=difficulty)


def test_even_midpoint_shortcut_is_declared_and_refuted_in_every_rotation():
    rival = gen.CANONICAL_SHORTCUTS.get("pink_upper_midpoint")
    assert rival is not None
    assert all(rival(pair["input"]) == pair["output"] for pair in canonical_pairs())

    for start in range(8):
        grids = [gen.generate(16000 + start, start + offset) for offset in range(5)]
        disagreements = [rival(grid) != gen.rule_mirror(grid) for grid in grids]
        assert sum(disagreements) >= 2, (start, disagreements)
        pairs = [{"input": grid, "output": gen.rule_mirror(grid)} for grid in grids]
        for query_index in range(5):
            demos = [pair for index, pair in enumerate(pairs) if index != query_index]
            assert gen.lesson_identifiable(demos, pairs[query_index]) == []


def test_retained_even_midpoint_counterexample_matches_authority_and_rival():
    case_path = HOME / "counterexamples" / "review-5c22ad8e91c4bedd" / "case.json"
    case = json.loads(case_path.read_text(encoding="utf-8"))
    grid = case["input"]
    assert case["rule_hash"] == gen.RULE_HASH
    assert case["executed_rule_hash"] == gen.RULE_HASH
    assert case["rule_hash_matches_catalog"] is True
    assert case["self_check"] == gen.self_check(grid) == []
    assert case["canonical_lower_output"] == gen.rule_mirror(grid)
    assert case["upper_midpoint_rival_output"] == gen.CANONICAL_SHORTCUTS["pink_upper_midpoint"](grid)
    assert case["differing_cells"] == [[2, 3], [2, 4]]
