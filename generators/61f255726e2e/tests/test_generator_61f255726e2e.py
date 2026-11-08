"""Task-local regression suite for 61f255726e2e; the oracle in workspace/ is independent of generator.py."""
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
import lesson_rivals as oracle_mod  # noqa: E402

GEN_PATH = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))


def _load(path=GEN_PATH):
    spec = importlib.util.spec_from_file_location("generator_under_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen = _load()
BANDS = (None, "easy", "medium", "hard")


def _canonical_pairs():
    with (ROOT / "shared/data/canonical/puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == "61f255726e2e":
                return row["train"] + row["test"]
    raise AssertionError("canonical task missing")


@pytest.mark.parametrize("index", range(4))
def test_canonical_inputs_are_lawful_and_oracle_matches(index):
    pair = _canonical_pairs()[index]
    assert gen.self_check(pair["input"]) == []
    assert gen.strict_canonical_like(pair["input"]) == []
    assert oracle_mod.oracle(pair["input"]) == pair["output"]


def test_canonical_pairs_cannot_separate_outline_from_fill():
    # Documents why the generator must supply hollow objects itself.
    for pair in _canonical_pairs():
        assert oracle_mod.fill_bbox(pair["input"]) == pair["output"]
        assert oracle_mod.union_outline(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", BANDS)
def test_every_grid_is_lawful_and_shows_an_erased_interior(band):
    for seed in range(250):
        grid = gen.generate(seed, seed * 7 + 3, difficulty=band)
        assert gen.self_check(grid) == [], (band, seed)
        facts = oracle_mod.grid_facts(grid)
        assert facts["hollow_bboxes"] >= 1 and facts["interior_blob_cells"] >= 1, (band, seed)
        out = oracle_mod.oracle(grid)
        assert out != grid
        assert oracle_mod.fill_bbox(grid) != out
        assert oracle_mod.union_outline(grid) != out


@pytest.mark.parametrize("band", BANDS)
def test_lessons_identify_outline_against_rivals(band):
    for k in range(120):
        seed, start = 5000 + k, k * 11
        pairs = []
        for i in range(4):
            grid = gen.generate(seed, start + i, difficulty=band)
            pairs.append({"input": grid, "output": oracle_mod.oracle(grid)})
        demos, query = pairs[:3], pairs[3]
        assert gen.lesson_identifiable(demos, query) == []
        for rival in (oracle_mod.fill_bbox, oracle_mod.union_outline):
            assert not all(rival(d["input"]) == d["output"] for d in demos)


@pytest.mark.parametrize("band", BANDS)
def test_exact_overrides_at_domain_corners_in_every_band(band):
    for h, w, n_hollow, n_thin in itertools.product((7, 14), (9, 16), (1, 2), (0, 1, 2, 3)):
        options = dict(grid_h=h, grid_w=w, n_hollow=n_hollow, n_thin=n_thin)
        for seed in range(6):
            grid = gen.generate(seed, 9, difficulty=band, **options)
            assert gen.self_check(grid) == []
            assert gen.observe_overrides(grid) == options


@pytest.mark.parametrize("key,value", [
    ("typo", 1), ("grid_h", 6), ("grid_h", 15), ("grid_w", 8), ("grid_w", 17),
    ("n_hollow", 0), ("n_hollow", 3), ("n_thin", -1), ("n_thin", 4),
    ("grid_h", True), ("n_thin", 2.0), ("n_hollow", "1"),
])
def test_rejects_invalid_overrides(key, value):
    with pytest.raises(ValueError):
        gen.generate(1, 0, **{key: value})


def test_default_draws_are_observable():
    for band in BANDS:
        for seed in range(60):
            grid = gen.generate(seed, 2, difficulty=band)
            observed = gen.observe_overrides(grid)
            assert gen.generate(seed, 2, difficulty=band, **observed) == grid


def test_empty_hollow_witness_is_reachable():
    hits = sum(gen.SEMANTIC_WITNESSES["empty_hollow"](gen.generate(s, 0, n_hollow=2)) for s in range(200))
    assert hits > 20


def test_rivals_declared_in_the_contract_disagree_on_witnesses():
    grid = gen.generate(3, 1, n_hollow=2)
    truth = oracle_mod.oracle(grid)
    assert gen.SEMANTIC_RIVALS["fill_bbox"](grid) != truth
    assert gen.SEMANTIC_RIVALS["outline_over_input"](grid) != truth


def test_output_is_independent_of_python_hash_seed():
    code = (
        "import importlib.util,json,sys;"
        f"sys.path.insert(0,{str(ROOT / 'shared/runtime')!r});"
        f"s=importlib.util.spec_from_file_location('g',{str(GEN_PATH)!r});"
        "m=importlib.util.module_from_spec(s);s.loader.exec_module(m);"
        "print(json.dumps([m.generate(i,i*5,difficulty=b) for i in range(40) for b in (None,'easy','hard')]))"
    )
    outputs = set()
    for hash_seed in ("1", "987654"):
        env = dict(os.environ, PYTHONHASHSEED=hash_seed)
        done = subprocess.run([sys.executable, "-c", code], env=env, capture_output=True, text=True, check=True)
        outputs.add(done.stdout)
    assert len(outputs) == 1
