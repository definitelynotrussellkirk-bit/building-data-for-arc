"""Task-local regressions for the repaired d3633a9fb1cd sampler."""
from copy import deepcopy
import hashlib
import os
from pathlib import Path
import subprocess
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (
    canonical_pairs,
    component_manhattan_output,
    geometry_output,
    has_detour_counterexample,
    has_tie_counterexample,
    load_generator,
    observed,
    racket_outputs,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))


@pytest.mark.parametrize("pair", canonical_pairs(), ids=["train0", "train1", "train2", "test0"])
def test_accepts_canonical_pairs_and_independent_oracle(pair):
    assert gen.self_check(pair["input"]) == []
    assert geometry_output(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_exact_overrides_are_realized_in_every_band(band):
    options = {
        "room_depth": 4,
        "room_span_a": 3,
        "room_span_b": 5,
        "gap": 2,
        "orientation": "vertical",
        "seed_mode": "double",
        "barrier": True,
    }
    grid = gen.generate(17, 9, difficulty=band, **options)
    assert gen.self_check(grid) == []
    assert observed(grid) == options
    assert gen.observe_overrides(grid) == options


@pytest.mark.parametrize(
    "key,value",
    [
        ("typo", 1),
        ("room_depth", 3),
        ("room_depth", 7),
        ("room_span_a", 1),
        ("room_span_b", 6),
        ("gap", 0),
        ("gap", 3),
        ("orientation", "diagonal"),
        ("seed_mode", "triple"),
        ("barrier", 1),
        ("room_depth", True),
        ("gap", "1"),
    ],
)
def test_rejects_unknown_or_invalid_overrides(key, value):
    with pytest.raises(ValueError):
        gen.generate(0, 0, **{key: value})



def test_canonical_span_two_is_constructive_even_with_barrier_and_two_seeds():
    options = {
        "room_depth": 6,
        "room_span_a": 2,
        "room_span_b": 3,
        "gap": 1,
        "orientation": "horizontal",
        "seed_mode": "double",
        "barrier": True,
    }
    for band in (None, "easy", "medium", "hard"):
        grid = gen.generate(404, 17, difficulty=band, **options)
        assert gen.self_check(grid) == []
        assert observed(grid) == options
        assert has_detour_counterexample(grid)
        assert has_tie_counterexample(grid)


def test_pinned_profile_floor_has_exact_canonical_support_in_every_band():
    def pinned_seed(band, index):
        digest = hashlib.sha256(
            f"profile-floor:v1:{gen.TASK_ID}:{band}:{index}".encode()
        ).hexdigest()
        return int(digest[:12], 16)

    profiles = {
        (len(pair["input"]), len(pair["input"][0]), len({v for row in pair["input"] for v in row}))
        for pair in canonical_pairs()
    }
    for band in ("easy", "medium", "hard"):
        hits = 0
        for index in range(20):
            seed = pinned_seed(band, index)
            grid = gen.generate(seed, seed % 7919 + index, difficulty=band)
            profile = (len(grid), len(grid[0]), len({v for row in grid for v in row}))
            hits += profile in profiles
        assert hits >= 1, f"{band} had no exact canonical profile in the pinned 20-draw census"

def test_distribution_covers_canonical_and_geodesic_teaching_branches():
    for band in (None, "easy", "medium", "hard"):
        orientations = set()
        modes = set()
        shapes = set()
        barriers = ties = detours = 0
        for index in range(192):
            grid = gen.generate(1000 + index, index * 11 + 3, difficulty=band)
            assert gen.self_check(grid) == []
            assert grid == gen.generate(1000 + index, index * 11 + 3, difficulty=band)
            stats = observed(grid)
            orientations.add(stats["orientation"])
            modes.add(stats["seed_mode"])
            shapes.add((len(grid), len(grid[0])))
            barriers += stats["barrier"]
            ties += has_tie_counterexample(grid)
            detours += has_detour_counterexample(grid)
            before = deepcopy(grid)
            geometry_output(grid)
            assert grid == before
        assert orientations == {"horizontal", "vertical"}
        assert modes == {"single", "mixed", "double"}
        assert len(shapes) >= 8
        assert barriers >= 25
        assert ties >= 20
        assert detours >= 10


def test_semantic_hooks_refute_declared_rivals():
    tie_grid = gen.generate(91, 4, seed_mode="double", barrier=False)
    detour_grid = gen.generate(92, 5, seed_mode="double", barrier=True)
    assert gen.SEMANTIC_WITNESSES["tie_stays_zero"](tie_grid)
    assert gen.SEMANTIC_RIVALS["tie_break_low_color"](tie_grid) != geometry_output(tie_grid)
    assert gen.SEMANTIC_WITNESSES["wall_detour"](detour_grid)
    assert gen.SEMANTIC_RIVALS["component_manhattan"](detour_grid) == component_manhattan_output(detour_grid)
    assert gen.SEMANTIC_RIVALS["component_manhattan"](detour_grid) != geometry_output(detour_grid)


def test_default_generation_does_not_change_global_random_state():
    import random
    random.seed(123456)
    before = random.getstate()
    gen.generate(22, 7, difficulty="hard")
    assert random.getstate() == before


def test_keyed_rng_is_independent_of_python_hash_seed():
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


def test_real_racket_reference_on_canonical_and_generated_witnesses():
    from arc_repl.racket_bridge import racket_runtime_status
    status = racket_runtime_status()
    if not status["available"]:
        pytest.skip(status["reason"])
    grids = [pair["input"] for pair in canonical_pairs()]
    grids += [
        gen.generate(300 + i, i, seed_mode="double", barrier=bool(i % 2))
        for i in range(12)
    ]
    assert racket_outputs(grids) == [geometry_output(grid) for grid in grids]


def test_seed_pair_geometry_search_is_cached_across_draws():
    cache = gen._seed_pair_candidates
    cache.cache_clear()
    options = {
        "room_depth": 6,
        "room_span_a": 4,
        "room_span_b": 4,
        "gap": 1,
        "orientation": "horizontal",
        "seed_mode": "double",
        "barrier": True,
    }
    for seed in range(12):
        gen.generate(seed, seed * 17, difficulty="hard", **options)
    info = cache.cache_info()
    assert info.misses <= 2
    assert info.hits >= 20


def test_every_three_demo_default_window_refutes_both_declared_competitors():
    for band in ("easy", "medium", "hard"):
        for start in range(12):
            grids = [gen.generate(8000 + start, start + offset, difficulty=band) for offset in range(3)]
            for name, competitor in gen.LESSON_COMPETITORS.items():
                assert any(
                    competitor(grid) != geometry_output(grid)
                    for grid in grids
                ), f"{band} start={start} left {name} consistent with all three demos"
