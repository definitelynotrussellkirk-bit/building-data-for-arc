"""Task-local regressions for the repaired rotated-stamping sampler."""
from copy import deepcopy
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
import reference_probe as probe
from reference_probe import (CODES, canonical_pairs, load_generator, observed,
                             oracle_output, racket_outputs, rotate, scene)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))


def test_reference_probe_discovers_an_arbitrarily_nested_runtime_root(tmp_path):
    root = tmp_path / "portable-runtime"
    ledger = root / "data/canonical/puzzles.jsonl"
    ledger.parent.mkdir(parents=True)
    ledger.write_text(json.dumps({
        "task_id": "unrelated",
        "train": [],
        "test": [],
    }) + "\n")
    copied = root / "extra/nesting/generators/2288bfea426b/workspace/reference_probe.py"
    copied.parent.mkdir(parents=True)
    shutil.copy2(Path(probe.__file__), copied)
    spec = importlib.util.spec_from_file_location("nested_reference_probe", copied)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.ROOT == root.resolve()


def test_contract_metadata_is_pinned_and_small():
    assert gen.RULE_HASH == "4df94edcd4cc"
    assert set(gen.AXES) == {"grid_h", "grid_w", "template_size", "n_markers"}
    assert gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    assert gen.EXAMPLES_NEEDED == 3


@pytest.mark.parametrize("pair", canonical_pairs(), ids=["train0", "train1", "train2", "test0"])
def test_accepts_canonical_inputs_and_independent_oracle_matches(pair):
    assert gen.self_check(pair["input"]) == []
    original = deepcopy(pair["input"])
    assert oracle_output(pair["input"]) == pair["output"]
    assert pair["input"] == original


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_exact_boundary_overrides_in_every_band(band):
    options = {"grid_h": 10, "grid_w": 11, "template_size": 6, "n_markers": 5}
    grid = gen.generate(17, 9, difficulty=band, **options)
    assert gen.self_check(grid) == []
    assert observed(grid) == options
    assert gen.observe_overrides(grid) == options
    assert oracle_output(grid) != grid


@pytest.mark.parametrize("key,value", [
    ("typo", 1), ("grid_h", 9), ("grid_h", 19), ("grid_w", 10),
    ("grid_w", 19), ("template_size", 2), ("template_size", 7),
    ("n_markers", 1), ("n_markers", 6), ("grid_h", True),
    ("n_markers", 2.5), ("template_size", "5"),
])
def test_rejects_unknown_invalid_and_non_integer_overrides(key, value):
    with pytest.raises(ValueError):
        gen.generate(0, 0, **{key: value})


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_default_schedule_has_canonical_support_and_missing_branches(band):
    dimensions, sizes, counts, code_sets, inputs = set(), set(), set(), set(), set()
    canonical_profile = repeated = all_codes = 0
    for index in range(80):
        grid = gen.generate(9000 + index, index, difficulty=band)
        assert gen.self_check(grid) == []
        assert grid == gen.generate(9000 + index, index, difficulty=band)
        assert gen._prediction(grid) == oracle_output(grid)
        obs = observed(grid)
        shape, markers = scene(grid)
        dimensions.add((obs["grid_h"], obs["grid_w"]))
        sizes.add(obs["template_size"])
        counts.add(obs["n_markers"])
        code_sets.add(tuple(sorted(code for _, _, code in markers)))
        inputs.add(repr(grid))
        canonical_profile += (obs["grid_h"], obs["grid_w"], len({v for row in grid for v in row})) == (13, 13, 5)
        repeated += len({code for _, _, code in markers}) < len(markers)
        all_codes += {code for _, _, code in markers} == set(CODES)
    assert canonical_profile >= 15
    assert repeated >= 20
    assert all_codes >= 20
    assert len(dimensions) >= 8
    assert sizes == {3, 4, 5, 6}
    assert counts == {2, 3, 4, 5}
    assert len(code_sets) >= 12
    assert len(inputs) == 80


def test_every_default_teaching_scene_refutes_every_declared_rival():
    for index in range(0, 24, 2):
        grid = gen.generate(712 + index, index, difficulty="hard")
        shape, markers = scene(grid)
        assert gen.schedule_profile(712 + index, index, "hard") == "teaching"
        assert len(markers) == 5
        assert {code for _, _, code in markers} == set(CODES)
        assert len({code for _, _, code in markers}) < len(markers)
        assert len({rotate(shape, turn) for turn in range(4)}) == 4
        expected = oracle_output(grid)
        for name, rival in gen.SEMANTIC_RIVALS.items():
            assert rival(grid) != expected, name


def test_canonical_shortcuts_are_real_and_have_generated_counterexamples():
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        assert all(rival(pair["input"]) == pair["output"] for pair in canonical_pairs()), name
    witness = gen.generate(81, 0)
    truth = oracle_output(witness)
    assert all(rival(witness) != truth for rival in gen.CANONICAL_SHORTCUTS.values())
    for witness_name, rival_names in gen.WITNESS_RIVALS.items():
        assert gen.SEMANTIC_WITNESSES[witness_name](witness)
        assert all(gen.SEMANTIC_RIVALS[name](witness) != truth for name in rival_names)


def test_three_consecutive_defaults_are_declared_rival_identifiable():
    for start in range(16):
        pairs = []
        for offset in range(4):
            grid = gen.generate(321, start + offset, difficulty="medium")
            pairs.append({"input": grid, "output": oracle_output(grid)})
        for query_index in range(4):
            demos = [pair for i, pair in enumerate(pairs) if i != query_index]
            assert gen.lesson_identifiable(demos, pairs[query_index]) == []


@pytest.mark.parametrize("grid", [None, [], [[]], [[0], [0, 1]], [[True] * 11 for _ in range(10)]])
def test_malformed_grid_is_diagnostic_not_exception(grid):
    assert gen.self_check(grid)


def test_keyed_rng_independent_of_python_hash_seed():
    script = (
        "import json,sys;sys.path.insert(0,sys.argv[1]);"
        "from reference_probe import load_generator;"
        "print(json.dumps(load_generator().generate(31,8,difficulty='hard')))"
    )
    outputs = []
    for hash_seed in ("1", "901"):
        env = dict(os.environ, PYTHONHASHSEED=hash_seed, PYTHONDONTWRITEBYTECODE="1")
        outputs.append(subprocess.check_output(
            [sys.executable, "-B", "-c", script, str(HOME / "workspace")], env=env, text=True
        ))
    assert outputs[0] == outputs[1]


def test_real_racket_reference_when_available():
    from arc_repl.racket_bridge import racket_runtime_status

    status = racket_runtime_status()
    if not status["available"]:
        pytest.skip(status["reason"])
    grids = [pair["input"] for pair in canonical_pairs()]
    grids += [gen.generate(319, index, difficulty="hard") for index in range(32)]
    assert racket_outputs(grids) == [oracle_output(grid) for grid in grids]
