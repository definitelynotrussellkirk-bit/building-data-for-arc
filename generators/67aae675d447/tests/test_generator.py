"""Portable task-local regression suite for 67aae675d447."""
from __future__ import annotations

from copy import deepcopy
import os
from pathlib import Path
import subprocess
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (  # noqa: E402
    BASES,
    canonical_pairs,
    frame,
    geometry_output,
    load_generator,
    observed,
    orientation_witness,
    racket_outputs,
)

gen = load_generator()
EXPECTED_AXES = {
    "grid_h", "grid_w", "n_motif", "bbox_u_span", "bbox_v_span",
    "n_distractors", "source_orientation", "target_orientation",
}


@pytest.mark.parametrize("pair", canonical_pairs(), ids=lambda p: f"{p['split']}{p['pair_index']}")
def test_canonical_inputs_are_accepted_and_match_independent_oracle(pair):
    assert gen.self_check(pair["input"]) == []
    assert geometry_output(pair["input"]) == pair["output"]
    assert gen.rule_mirror(pair["input"]) == pair["output"]


def test_public_contract_exposes_only_real_observable_axes():
    assert set(gen.AXES) == EXPECTED_AXES
    assert gen.RULE_HASH == "e0f86f3cb6ab"
    assert callable(gen.observe_overrides)
    assert callable(gen.strict_canonical_like)
    assert callable(gen.lesson_identifiable)
    assert gen.SEMANTIC_WITNESSES
    assert gen.SEMANTIC_RIVALS
    assert gen.WITNESS_RIVALS
    assert gen.LESSON_COMPETITORS


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_exact_overrides_are_observable_in_every_band(band):
    options = {
        "grid_h": 10, "grid_w": 14, "n_motif": 7,
        "bbox_u_span": 2, "bbox_v_span": 2, "n_distractors": 3,
        "source_orientation": 7, "target_orientation": 5,
    }
    grid = gen.generate(17, 9, difficulty=band, **options)
    assert gen.self_check(grid) == []
    assert observed(grid) == options
    assert gen.observe_overrides(grid) == options


@pytest.mark.parametrize("key,value", [
    ("typo", 1), ("grid_h", 9), ("grid_h", 25), ("grid_w", 13), ("grid_w", 25),
    ("n_motif", 2), ("n_motif", 8), ("bbox_u_span", 1), ("bbox_u_span", 7),
    ("bbox_v_span", 1), ("bbox_v_span", 7), ("n_distractors", -1),
    ("n_distractors", 4), ("source_orientation", -1), ("source_orientation", 8),
    ("target_orientation", -1), ("target_orientation", 8), ("grid_h", True),
    ("n_motif", 3.0), ("n_distractors", "2"),
])
def test_invalid_or_unknown_overrides_fail_loudly(key, value):
    with pytest.raises(ValueError):
        gen.generate(0, 0, **{key: value})


@pytest.mark.parametrize("bad_seed,bad_index", [(True, 0), (1.0, 0), (0, True), (0, -1), (0, "1")])
def test_invalid_seed_or_sample_index_fails_loudly(bad_seed, bad_index):
    with pytest.raises(ValueError):
        gen.generate(bad_seed, bad_index)


@pytest.mark.parametrize("index", range(64))
def test_all_independent_frame_orientation_pairs(index):
    source_orientation, target_orientation = divmod(index, 8)
    grid = gen.generate(
        73, index, grid_h=16, grid_w=18, n_motif=5,
        bbox_u_span=4, bbox_v_span=3, n_distractors=2,
        source_orientation=source_orientation, target_orientation=target_orientation,
    )
    assert gen.self_check(grid) == []
    assert frame(grid, (2, 3, 4))[1:] == BASES[source_orientation]
    assert frame(grid, (5, 6, 7))[1:] == BASES[target_orientation]
    assert gen.observe_overrides(grid) == observed(grid)
    assert gen.rule_mirror(grid) == geometry_output(grid)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_first_twenty_draws_include_canonical_profile_and_broad_support(band):
    stats = []
    hashes = set()
    for index in range(80):
        grid = gen.generate(1009 + index, index * 7 + 3, difficulty=band)
        assert gen.self_check(grid) == []
        assert grid == gen.generate(1009 + index, index * 7 + 3, difficulty=band)
        assert gen.rule_mirror(grid) == geometry_output(grid)
        stats.append(observed(grid))
        hashes.add(repr(grid))
    assert any(
        s["grid_h"] == 13 and s["grid_w"] == 19
        and s["n_motif"] == 3 and s["n_distractors"] == 0
        for s in stats[:20]
    )
    assert len(hashes) >= 75
    assert {s["source_orientation"] for s in stats} == set(range(8))
    assert {s["target_orientation"] for s in stats} == set(range(8))
    assert len({(s["bbox_u_span"], s["bbox_v_span"]) for s in stats}) >= 12
    assert max(s["n_distractors"] for s in stats) == 3


@pytest.mark.parametrize("mutation", [
    "extra_frame_color", "unknown_color", "target_eight", "erase_frame",
    "empty_motif", "too_many_distractors", "degenerate_bbox", "ragged",
])
def test_validator_rejects_destructive_mutations(mutation):
    grid = gen.generate(4, 2, grid_h=16, grid_w=18, n_motif=4,
                        bbox_u_span=4, bbox_v_span=4, n_distractors=0)
    if mutation == "extra_frame_color":
        grid[0][0] = 2
    elif mutation == "unknown_color":
        grid[0][0] = 9
    elif mutation == "target_eight":
        target = frame(grid, (5, 6, 7))[0]
        grid[target[0] - 2][target[1] - 2] = 8
    elif mutation == "erase_frame":
        source = frame(grid, (2, 3, 4))[0]
        grid[source[0]][source[1]] = 0
    elif mutation == "empty_motif":
        for r, row in enumerate(grid):
            for c, value in enumerate(row):
                if value == 8:
                    grid[r][c] = 0
    elif mutation == "too_many_distractors":
        source = frame(grid, (2, 3, 4))[0]
        target = frame(grid, (5, 6, 7))[0]
        added = 0
        for r, row in enumerate(grid):
            for c, value in enumerate(row):
                if (value == 0 and max(abs(r-source[0]), abs(c-source[1])) > 3
                        and max(abs(r-target[0]), abs(c-target[1])) > 3):
                    grid[r][c] = 8
                    added += 1
                    if added == 4:
                        break
            if added == 4:
                break
    elif mutation == "degenerate_bbox":
        source = frame(grid, (2, 3, 4))
        for r, row in enumerate(grid):
            for c, value in enumerate(row):
                if value == 8:
                    grid[r][c] = 0
        from reference_probe import lift
        for uv in ((-1, -1), (-1, 0), (-1, 1)):
            r, c = lift(source, uv)
            grid[r][c] = 8
    elif mutation == "ragged":
        grid[-1].pop()
    assert gen.self_check(grid)


@pytest.mark.parametrize("grid", [None, [], [[]], [[0], [0, 1]], [[True] * 14 for _ in range(10)]])
def test_malformed_grid_returns_diagnostics_instead_of_raising(grid):
    assert gen.self_check(grid)


def test_semantic_rivals_and_witnesses_are_real_disagreements():
    grid = orientation_witness()
    assert gen.self_check(grid) == []
    intended = geometry_output(grid)
    for name, rival in gen.SEMANTIC_RIVALS.items():
        original = deepcopy(grid)
        predicted = rival(grid)
        assert grid == original, name
        assert predicted != intended, name
    assert gen.SEMANTIC_WITNESSES["independent_target_orientation"](grid)
    assert "source_basis_at_target" in gen.WITNESS_RIVALS["independent_target_orientation"]


def test_declared_lesson_competitors_are_refuted_by_each_lawful_demo():
    for index in range(24):
        grid = gen.generate(712, index)
        intended = gen.rule_mirror(grid)
        for name, rival in gen.LESSON_COMPETITORS.items():
            assert rival(grid) != intended, (index, name)
    pairs = [{"input": gen.generate(712, i), "output": gen.rule_mirror(gen.generate(712, i))} for i in range(4)]
    query_grid = gen.generate(712, 4)
    query = {"input": query_grid, "output": gen.rule_mirror(query_grid)}
    assert gen.lesson_identifiable(pairs, query) == []


def test_oracle_and_rivals_do_not_mutate_inputs():
    grid = gen.generate(38, 11, n_distractors=3)
    original = deepcopy(grid)
    assert gen.rule_mirror(grid) == geometry_output(grid)
    assert grid == original
    for rival in gen.SEMANTIC_RIVALS.values():
        rival(grid)
        assert grid == original


def test_python_hash_seed_does_not_change_generation():
    script = (
        "import json,os;from reviewer_support import load_selected_generator;"
        f"m,_,_=load_selected_generator('{gen.TASK_ID}',root=os.environ['ARCPUZZLES_HOME']);"
        "print(json.dumps(m.generate(31,8,difficulty='hard')))"
    )
    results = []
    for hash_seed in ("1", "901"):
        env = dict(os.environ, PYTHONHASHSEED=hash_seed, PYTHONDONTWRITEBYTECODE="1")
        results.append(subprocess.check_output([sys.executable, "-B", "-c", script], env=env, text=True))
    assert results[0] == results[1]


def test_real_racket_authority_matches_oracle_when_available():
    from arc_repl.racket_bridge import racket_runtime_status
    status = racket_runtime_status()
    if not status["available"]:
        pytest.skip(status["reason"])
    grids = [pair["input"] for pair in canonical_pairs()]
    grids += [
        gen.generate(319, i, source_orientation=i // 8, target_orientation=i % 8,
                     n_motif=5, bbox_u_span=4, bbox_v_span=3, n_distractors=2)
        for i in range(0, 64, 3)
    ]
    assert racket_outputs(grids) == [geometry_output(grid) for grid in grids]


def test_sampler_does_not_claim_an_unverified_fixed_schedule_period():
    """A stochastic core/broad mixture must not advertise a period to strict gates."""
    assert not hasattr(gen, "LESSON_SCHEDULE_PERIOD")
    assert not hasattr(gen, "SCHEDULE_PROFILES")
