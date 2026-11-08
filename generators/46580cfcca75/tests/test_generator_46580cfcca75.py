"""Task-local regression suite for 46580cfcca75.

The oracle in ``workspace/reference_oracle.py`` is independent of generator.py.
"""
from __future__ import annotations

import importlib.util
import itertools
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
ROOT = HOME.parents[1]
sys.path.insert(0, str(ROOT / "shared/runtime"))
sys.path.insert(0, str(HOME / "workspace"))
from reviewer_support import canonical_pairs, find_root  # noqa: E402
import reference_oracle as oracle_mod  # noqa: E402

GEN_PATH = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))


def _load(path=GEN_PATH):
    spec = importlib.util.spec_from_file_location("generator_under_test", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


gen = _load()
BANDS = (None, "easy", "medium", "hard")
CANONICAL_PROFILES = {(6, 8, 3), (7, 7, 3), (7, 9, 3), (8, 9, 2)}


def _pairs():
    return canonical_pairs("46580cfcca75", root=find_root(__file__), labeled_only=True)


def _profile(grid):
    return len(grid), len(grid[0]), len({value for row in grid for value in row})


def test_declares_required_contract():
    assert gen.RULE_HASH == "001f318153f4"
    assert callable(gen.self_check)
    assert callable(gen.strict_canonical_like)
    assert callable(gen.observe_overrides)
    assert gen.EXAMPLES_NEEDED == 3
    assert set(gen.AXES) == {"grid_h", "grid_w", "n_rects"}


@pytest.mark.parametrize("index", range(4))
def test_canonical_inputs_are_lawful_and_oracle_matches(index):
    pair = _pairs()[index]
    assert gen.self_check(pair["input"]) == []
    assert gen.strict_canonical_like(pair["input"]) == []
    assert oracle_mod.oracle(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", BANDS)
def test_default_draws_are_lawful_visible_and_canonical_scale(band):
    for seed in range(120):
        sample_index = seed * 7 + 3
        grid = gen.generate(seed, sample_index, difficulty=band)
        assert gen.self_check(grid) == [], (band, seed)
        assert _profile(grid) in CANONICAL_PROFILES, (band, seed, _profile(grid))
        facts = oracle_mod.facts(grid)
        assert facts["objects"] in (1, 2)
        assert all(facts["solid"])
        assert facts["visible"] >= 1
        assert len(set(facts["colours"])) == facts["objects"]
        assert oracle_mod.oracle(grid) != grid


@pytest.mark.parametrize("band", BANDS)
def test_four_pair_schedule_and_every_rotation_refute_declared_rivals(band):
    for seed in range(40):
        start = seed * 11
        pairs = []
        for offset in range(4):
            grid = gen.generate(seed + 2000, start + offset, difficulty=band)
            pairs.append({"input": grid, "output": oracle_mod.oracle(grid)})
        for query_index in range(4):
            demos = [pair for i, pair in enumerate(pairs) if i != query_index]
            query = pairs[query_index]
            assert gen.lesson_identifiable(demos, query) == [], (band, seed, query_index)
            for rival in gen.LESSON_COMPETITORS.values():
                assert not (
                    all(rival(demo["input"]) == demo["output"] for demo in demos)
                    and rival(query["input"]) != query["output"]
                ), (band, seed, query_index, rival.__name__)


@pytest.mark.parametrize("band", BANDS)
def test_exact_overrides_at_domain_corners_in_every_band(band):
    for h, w, n_rects in itertools.product((6, 14), (7, 16), (1, 2)):
        options = {"grid_h": h, "grid_w": w, "n_rects": n_rects}
        for seed in range(8):
            grid = gen.generate(seed, 9, difficulty=band, **options)
            assert gen.self_check(grid) == [], (band, seed, options)
            assert gen.observe_overrides(grid) == options


@pytest.mark.parametrize("key,value", [
    ("typo", 1),
    ("grid_h", 5), ("grid_h", 15),
    ("grid_w", 6), ("grid_w", 17),
    ("n_rects", 0), ("n_rects", 3),
    ("grid_h", True), ("grid_w", 9.0), ("n_rects", "2"),
])
def test_rejects_invalid_overrides(key, value):
    with pytest.raises(ValueError):
        gen.generate(1, 0, **{key: value})


def test_observed_overrides_replay_default_draw_exactly():
    for band in BANDS:
        for seed in range(80):
            grid = gen.generate(seed, seed * 5 + 1, difficulty=band)
            observed = gen.observe_overrides(grid)
            assert gen.generate(seed, seed * 5 + 1, difficulty=band, **observed) == grid


def test_witnesses_and_rivals_are_real_counterexamples():
    grids = [gen.generate(7, index) for index in range(4)]
    truths = [oracle_mod.oracle(grid) for grid in grids]
    assert any(gen.SEMANTIC_WITNESSES["multiple_objects"](grid) for grid in grids)
    assert any(gen.SEMANTIC_WITNESSES["thin_rectangle"](grid) for grid in grids)
    assert all(gen.SEMANTIC_WITNESSES["interior_erased"](grid) for grid in grids)
    for grid, truth in zip(grids, truths):
        for witness, rival_names in gen.WITNESS_RIVALS.items():
            if gen.SEMANTIC_WITNESSES[witness](grid):
                assert any(gen.SEMANTIC_RIVALS[name](grid) != truth for name in rival_names)


def test_output_is_independent_of_python_hash_seed():
    code = (
        "import importlib.util,json,sys;"
        f"sys.path.insert(0,{str(ROOT / 'shared/runtime')!r});"
        f"s=importlib.util.spec_from_file_location('g',{str(GEN_PATH)!r});"
        "m=importlib.util.module_from_spec(s);s.loader.exec_module(m);"
        "print(json.dumps([m.generate(i,i*5,difficulty=b) "
        "for i in range(50) for b in (None,'easy','medium','hard')]))"
    )
    outputs = set()
    for hash_seed in ("1", "987654"):
        env = dict(os.environ, PYTHONHASHSEED=hash_seed)
        done = subprocess.run(
            [sys.executable, "-c", code], env=env,
            capture_output=True, text=True, check=True,
        )
        outputs.add(done.stdout)
    assert len(outputs) == 1


def test_rejects_full_grid_one_colour_impostor():
    assert gen.self_check([[4] * 7 for _ in range(6)])


def test_difficulty_bands_materially_affect_visible_draws():
    for sample_index in range(4):
        outputs = {
            json.dumps(gen.generate(1234, sample_index, difficulty=band))
            for band in ("easy", "medium", "hard")
        }
        assert len(outputs) >= 2, sample_index
