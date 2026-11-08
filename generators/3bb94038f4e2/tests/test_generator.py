"""Task-local regression suite for 3bb94038f4e2.

The oracle and canonical reader live in workspace and do not import production
helpers.  Tests are portable through ``arcpuzzles check --stage task_tests``.
"""
from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (  # noqa: E402
    canonical_pairs,
    intended_output,
    load_generator,
    normalized_rule_hash,
    pinned_profile_seed,
    profile,
    racket_outputs,
    semantic_features,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))
CANONICAL_PROFILES = {profile(pair["input"]) for pair in canonical_pairs()}


def test_rule_hash_is_pinned_to_selected_authority():
    assert normalized_rule_hash() == "f19859825874"
    assert gen.RULE_HASH == normalized_rule_hash()


@pytest.mark.parametrize("pair", canonical_pairs(), ids=["train0", "train1", "test0"])
def test_accepts_canonical_inputs_and_independent_oracle(pair):
    before = deepcopy(pair["input"])
    assert gen.self_check(pair["input"]) == []
    assert intended_output(pair["input"]) == pair["output"]
    assert pair["input"] == before


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("h,w", [(6, 7), (6, 16), (14, 7), (14, 16), (9, 11)])
def test_exact_dimension_overrides_work_in_every_band(band, h, w):
    grid = gen.generate(17, 9, difficulty=band, grid_h=h, grid_w=w)
    assert (len(grid), len(grid[0])) == (h, w)
    assert gen.observe_overrides(grid) == {"grid_h": h, "grid_w": w}
    assert gen.self_check(grid) == []
    assert intended_output(grid) != grid


@pytest.mark.parametrize(
    "overrides",
    [
        {"typo": 1},
        {"grid_h": 5},
        {"grid_h": 15},
        {"grid_w": 6},
        {"grid_w": 17},
        {"grid_h": True},
        {"grid_h": 7.0},
        {"grid_w": "8"},
    ],
)
def test_invalid_or_unknown_overrides_are_rejected(overrides):
    with pytest.raises(ValueError):
        gen.generate(0, 0, **overrides)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_constructive_default_path_never_drops_the_required_gap(band):
    for i in range(160):
        seed, index = 1000 + i, i * 17 + 3
        grid = gen.generate(seed, index, difficulty=band)
        assert gen.self_check(grid) == []
        assert semantic_features(grid)["true_gaps"]
        assert grid == gen.generate(seed, index, difficulty=band)
        assert intended_output(grid) != grid


def test_profile_floor_has_an_exact_canonical_hit_in_each_band():
    for band in ("easy", "medium", "hard"):
        hits = 0
        for index in range(20):
            seed = pinned_profile_seed(band, index)
            grid = gen.generate(seed, seed % 7919 + index, difficulty=band)
            hits += profile(grid) in CANONICAL_PROFILES
        assert hits > 0, band


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_each_broad_profile_is_a_complete_semantic_counterexample(band):
    for index in range(1, 20, 2):
        grid = gen.generate(700 + index, index, difficulty=band)
        features = semantic_features(grid)
        assert len(features["true_gaps"]) >= 2
        assert features["wide_gaps"]
        assert features["vertical_gaps"]
        assert features["other_color_gaps"]
        assert features["protected_centers"]
        expected = intended_output(grid)
        assert all(rival(grid) != expected for rival in gen.LESSON_COMPETITORS.values())
        assert all(predicate(grid) for predicate in gen.SEMANTIC_WITNESSES.values())


def test_canonical_shortcuts_really_fit_canonical_and_are_refuted_by_broad_draws():
    assert gen.CANONICAL_SHORTCUTS
    for name, shortcut in gen.CANONICAL_SHORTCUTS.items():
        assert all(shortcut(pair["input"]) == pair["output"] for pair in canonical_pairs()), name
        broad = gen.generate(811, 1, difficulty="medium")
        assert shortcut(broad) != intended_output(broad), name


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_cyclic_query_rotation_is_identifiable(band):
    # Production lessons consume three demos and one query.  The alternating
    # core/broad schedule guarantees every three-of-four rotation retains a
    # broad counterexample; check consecutive starts instead of only residue 0.
    for start in range(12):
        pairs = []
        for offset in range(4):
            grid = gen.generate(2026 + start, start + offset, difficulty=band)
            pairs.append({"input": grid, "output": intended_output(grid)})
        for query_index in range(4):
            query = pairs[query_index]
            demos = [pair for i, pair in enumerate(pairs) if i != query_index]
            assert gen.lesson_identifiable(demos, query) == []
            for name, rival in gen.LESSON_COMPETITORS.items():
                assert any(rival(d["input"]) != d["output"] for d in demos), name


def test_independent_oracle_matches_generated_distribution():
    seen_inputs = set()
    seen_outputs = set()
    for band in (None, "easy", "medium", "hard"):
        for i in range(80):
            grid = gen.generate(4000 + i, i * 13 + 1, difficulty=band)
            out = intended_output(grid)
            seen_inputs.add(json.dumps(grid, separators=(",", ":")))
            seen_outputs.add(json.dumps(out, separators=(",", ":")))
            assert gen.self_check(grid) == []
            assert out != grid
    assert len(seen_inputs) >= 100
    assert len(seen_outputs) >= 100


@pytest.mark.parametrize(
    "grid",
    [
        None,
        [],
        [[]],
        [[0], [0, 1]],
        [[True] * 7 for _ in range(6)],
        [[0] * 7 for _ in range(6)],
        [[0] * 6 for _ in range(6)],
        [[0] * 17 for _ in range(6)],
    ],
)
def test_validator_rejects_malformed_or_trivial_inputs(grid):
    assert gen.self_check(grid)


def test_validator_accepts_rule_domain_not_only_literal_scaffold():
    grid = [[0] * 8 for _ in range(6)]
    grid[3][2:5] = [1, 0, 1]
    assert gen.self_check(grid) == []
    assert intended_output(grid)[3][3] == 1


def test_keyed_generation_is_independent_of_python_hash_seed():
    script = (
        "import json,sys;sys.path.insert(0,sys.argv[1]);"
        "from reference_probe import load_generator;"
        "print(json.dumps(load_generator().generate(31,8,difficulty='hard')))"
    )
    outputs = []
    for hash_seed in ("1", "901"):
        env = dict(os.environ, PYTHONHASHSEED=hash_seed, PYTHONDONTWRITEBYTECODE="1")
        outputs.append(
            subprocess.check_output(
                [sys.executable, "-B", "-c", script, str(HOME / "workspace")],
                env=env,
                text=True,
            )
        )
    assert outputs[0] == outputs[1]


def test_real_racket_authority_matches_oracle_when_available():
    from arc_repl.racket_bridge import racket_runtime_status

    status = racket_runtime_status()
    if not status["available"]:
        pytest.skip(status["reason"])
    grids = [pair["input"] for pair in canonical_pairs()]
    grids += [gen.generate(9100 + i, i, difficulty="hard") for i in range(24)]
    assert racket_outputs(grids) == [intended_output(grid) for grid in grids]


def test_task_local_analyzer_reports_complete_schedule():
    from analyze_curriculum import analyze

    report = analyze(gen, per_band=12, cyclic_starts=6)
    assert report["status"] == "pass"
    assert report["totals"]["self_check_errors"] == 0
    assert report["totals"]["nondeterministic"] == 0
    assert report["totals"]["cyclic_ambiguous_rotations"] == 0
    assert report["totals"]["cyclic_rotations"] == 3 * 6 * 4
    for band in ("easy", "medium", "hard"):
        assert set(report["per_band"][band]["profiles"]) == {"core", "broad"}


def _max_foreground_component(grid):
    background = max({v for row in grid for v in row}, key=lambda v: sum(row.count(v) for row in grid))
    seen = set()
    biggest = 0
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value == background or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            size = 0
            while stack:
                rr, cc = stack.pop()
                size += 1
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < len(grid) and 0 <= nc < len(grid[0])
                            and (nr, nc) not in seen and grid[nr][nc] == value):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            biggest = max(biggest, size)
    return biggest


def test_distribution_retains_canonical_small_component_morphology():
    # Canonical inputs have maximum same-color 4-connected components of size
    # 1..2.  At least some ordinary draws must stay within the lint tolerance.
    for band in ("easy", "medium", "hard"):
        sizes = [_max_foreground_component(gen.generate(6000 + i, i, difficulty=band))
                 for i in range(40)]
        assert min(sizes) <= 3, (band, sizes)


@pytest.mark.parametrize(
    "seed,left_index,right_index",
    [(369778641, 83, 85), (702232904, 93, 95), (2671966845, 99, 101)],
)
def test_adjacent_broad_schedule_slots_are_not_duplicate_rejections(
    seed, left_index, right_index
):
    # These exact production-census cases previously collapsed to the same 6x7
    # broad input, so the materializer skipped the second broad slot and left a
    # rotated lesson with only core demos.
    left = gen.generate(seed, left_index, difficulty="easy")
    right = gen.generate(seed, right_index, difficulty="easy")
    assert left != right
