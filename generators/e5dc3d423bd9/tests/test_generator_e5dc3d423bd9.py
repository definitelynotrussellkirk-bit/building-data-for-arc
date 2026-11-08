"""Regression suite for e5dc3d423bd9.

The selected rule and the wrong-rule competitor come from workspace/reference_probe.py,
which deliberately does not import the generator implementation.
"""
from __future__ import annotations

import copy
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
import reference_probe as oracle_mod  # noqa: E402

GEN_PATH = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))
EXPECTED_RULE_HASH = "c76c9e5b1858"
BANDS = (None, "easy", "medium", "hard")


def _load(path: Path = GEN_PATH):
    spec = importlib.util.spec_from_file_location("generator_under_test", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen = _load()


def _canonical_pairs() -> list[dict]:
    with (ROOT / "shared/data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == "e5dc3d423bd9":
                train = row.get("train", [])
                test = row.get("test", [])
                return (list(train.values()) if isinstance(train, dict) else list(train)) + (
                    list(test.values()) if isinstance(test, dict) else list(test)
                )
    raise AssertionError("canonical task missing")


def test_rule_hash_is_pinned_to_selected_authority():
    assert getattr(gen, "RULE_HASH", None) == EXPECTED_RULE_HASH


@pytest.mark.parametrize("index", range(4))
def test_canonical_inputs_are_lawful_and_independent_oracle_matches(index):
    pair = _canonical_pairs()[index]
    assert gen.self_check(copy.deepcopy(pair["input"])) == []
    assert gen.strict_canonical_like(copy.deepcopy(pair["input"])) == []
    assert oracle_mod.oracle(pair["input"]) == pair["output"]


def test_canonical_pairs_do_not_disprove_mark_every_frame_shortcut():
    for pair in _canonical_pairs():
        assert oracle_mod.mark_every_frame_floor_center(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", BANDS)
def test_every_default_grid_contains_odd_targets_and_one_even_decoy(band):
    for seed in range(180):
        grid = gen.generate(seed, seed * 13 + 7, difficulty=band)
        assert gen.self_check(copy.deepcopy(grid)) == [], (band, seed)
        facts = oracle_mod.grid_facts(grid)
        assert 1 <= facts["n_odd"] <= 3, (band, seed, facts)
        assert facts["n_even"] == 1, (band, seed, facts)
        assert facts["n_frames"] == facts["n_odd"] + 1
        assert facts["distinct_colors"]
        truth = oracle_mod.oracle(grid)
        rival = oracle_mod.mark_every_frame_floor_center(grid)
        assert truth != rival, (band, seed, facts)


@pytest.mark.parametrize("band", BANDS)
def test_exact_overrides_at_domain_corners_in_every_band(band):
    for grid_h, grid_w, n_odd in itertools.product((7, 14), (10, 18), (1, 3)):
        options = {"grid_h": grid_h, "grid_w": grid_w, "n_odd": n_odd}
        for seed in range(4):
            grid = gen.generate(seed, 31, difficulty=band, **options)
            assert gen.self_check(grid) == [], (band, options, seed)
            assert gen.observe_overrides(grid) == options
            facts = oracle_mod.grid_facts(grid)
            assert facts["n_even"] == 1
            assert facts["n_odd"] == n_odd


@pytest.mark.parametrize(
    "key,value",
    [
        ("typo", 1),
        ("grid_h", 6),
        ("grid_h", 15),
        ("grid_w", 9),
        ("grid_w", 19),
        ("n_odd", 0),
        ("n_odd", 4),
        ("grid_h", True),
        ("grid_w", 10.0),
        ("n_odd", "2"),
    ],
)
def test_rejects_invalid_overrides(key, value):
    with pytest.raises(ValueError):
        gen.generate(1, 0, **{key: value})


def test_rejects_unknown_difficulty():
    with pytest.raises(ValueError):
        gen.generate(1, 0, difficulty="nightmare")


def test_default_draws_are_exactly_replayable_from_observed_axes():
    for band in BANDS:
        for seed in range(80):
            sample_index = seed * 19 + 2
            grid = gen.generate(seed, sample_index, difficulty=band)
            observed = gen.observe_overrides(copy.deepcopy(grid))
            assert set(observed) == set(gen.AXES)
            assert gen.generate(seed, sample_index, difficulty=band, **observed) == grid


@pytest.mark.parametrize("band", BANDS)
def test_complete_lessons_refute_declared_competitor(band):
    for lesson in range(80):
        seed = 20_000 + lesson
        start = lesson * 7
        pairs = []
        for offset in range(4):
            grid = gen.generate(seed, start + offset, difficulty=band)
            pairs.append({"input": grid, "output": oracle_mod.oracle(grid)})
        demos, query = pairs[:3], pairs[3]
        assert gen.lesson_identifiable(demos, query) == []
        rival = gen.SEMANTIC_RIVALS["mark_every_frame_floor_center"]
        assert not all(rival(demo["input"]) == demo["output"] for demo in demos)
        assert any(gen.SEMANTIC_WITNESSES[name](demo["input"]) for name in gen.SEMANTIC_WITNESSES for demo in demos)


def test_declared_rival_matches_independent_wrong_rule_and_disagrees_with_truth():
    rival = gen.SEMANTIC_RIVALS["mark_every_frame_floor_center"]
    for seed in range(100):
        grid = gen.generate(90_000 + seed, seed)
        assert rival(copy.deepcopy(grid)) == oracle_mod.mark_every_frame_floor_center(grid)
        assert rival(copy.deepcopy(grid)) != oracle_mod.oracle(grid)


def test_self_check_rejects_nonframes_and_touching_frames():
    solid = [[0] * 8 for _ in range(7)]
    for r in range(1, 4):
        for c in range(1, 4):
            solid[r][c] = 2
    assert gen.self_check(solid)

    touching = [[0] * 9 for _ in range(7)]
    for r, c in itertools.product(range(3), range(3)):
        if r in (0, 2) or c in (0, 2):
            touching[r + 1][c + 1] = 2
            touching[r + 1][c + 4] = 3  # exactly one background column is required; these touch
    assert gen.self_check(touching)


@pytest.mark.parametrize(
    "bad",
    [
        [],
        [[0, 0], [0]],
        [[0, 11], [0, 0]],
        [[0, "2"], [0, 0]],
    ],
)
def test_self_check_rejects_malformed_grids(bad):
    assert gen.self_check(bad)


def test_generation_does_not_mutate_returned_grids_via_contract_hooks():
    grid = gen.generate(3, 4)
    before = copy.deepcopy(grid)
    assert gen.strict_canonical_like(grid) == []
    for fn in gen.SEMANTIC_WITNESSES.values():
        fn(grid)
    for fn in gen.SEMANTIC_RIVALS.values():
        fn(grid)
    assert grid == before


def test_output_is_independent_of_python_hash_seed():
    code = (
        "import importlib.util,json,sys;"
        f"sys.path.insert(0,{str(ROOT / 'shared/runtime')!r});"
        f"s=importlib.util.spec_from_file_location('g',{str(GEN_PATH)!r});"
        "m=importlib.util.module_from_spec(s);s.loader.exec_module(m);"
        "print(json.dumps([m.generate(i,i*5,difficulty=b) for i in range(50) "
        "for b in (None,'easy','medium','hard')],separators=(',',':')))"
    )
    outputs = set()
    for hash_seed in ("1", "987654"):
        env = dict(os.environ, PYTHONHASHSEED=hash_seed)
        done = subprocess.run(
            [sys.executable, "-c", code],
            env=env,
            capture_output=True,
            text=True,
            check=True,
        )
        outputs.add(done.stdout)
    assert len(outputs) == 1
