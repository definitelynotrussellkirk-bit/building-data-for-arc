"""Task-local regressions for the repaired component-bounding-box sampler."""
from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (canonical_pairs, components, global_color_bbox,
                             load_generator, observed, oracle_output, racket_outputs)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))


def test_contract_metadata_is_pinned_and_small():
    assert gen.RULE_HASH == "c86a6d30fc9f"
    assert set(gen.AXES) == {"grid_h", "grid_w", "components", "repeat_color"}
    assert gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    assert gen.EXAMPLES_NEEDED == 3
    assert gen.LESSON_SCHEDULE_PERIOD == 2


@pytest.mark.parametrize("pair", canonical_pairs(), ids=["train0", "train1", "train2", "train3", "test0"])
def test_accepts_canonical_inputs_and_independent_oracle_matches(pair):
    original = deepcopy(pair["input"])
    assert gen.self_check(pair["input"]) == []
    assert gen.strict_canonical_like(pair["input"]) == []
    assert oracle_output(pair["input"]) == pair["output"]
    assert pair["input"] == original


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("options", [
    {"grid_h": 8, "grid_w": 9, "components": 4, "repeat_color": 1},
    {"grid_h": 13, "grid_w": 14, "components": 2, "repeat_color": 0},
])
def test_exact_boundary_overrides_in_every_band(band, options):
    grid = gen.generate(17, 9, difficulty=band, **options)
    assert gen.self_check(grid) == []
    assert observed(grid) == options
    assert gen.observe_overrides(grid) == options
    assert oracle_output(grid) != grid


@pytest.mark.parametrize("key,value", [
    ("typo", 1), ("grid_h", 7), ("grid_h", 14), ("grid_w", 8),
    ("grid_w", 15), ("components", 1), ("components", 5),
    ("repeat_color", -1), ("repeat_color", 2), ("grid_h", True),
    ("components", 2.5), ("repeat_color", "1"),
])
def test_rejects_unknown_invalid_and_non_integer_overrides(key, value):
    with pytest.raises(ValueError):
        gen.generate(0, 0, **{key: value})


@pytest.mark.parametrize("grid", [
    None,
    [],
    [[]],
    [[0], [0, 1]],
    [[0] * 9 for _ in range(8)],
    [[4, 4], [4, 4]],
    [[True] * 9 for _ in range(8)],
])
def test_self_check_rejects_malformed_or_non_teaching_impostors(grid):
    assert gen.self_check(grid)


def test_self_check_rejects_component_without_bbox_hole():
    grid = [[0] * 9 for _ in range(8)]
    grid[1][1] = grid[1][2] = grid[2][1] = grid[2][2] = 4
    grid[5][6] = grid[5][7] = grid[6][6] = 6
    assert gen.self_check(grid)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_default_distribution_is_exact_deterministic_and_covers_declared_domain(band):
    dimensions, component_counts, repeat_counts, local_shapes, colors, grids = set(), set(), set(), set(), set(), set()
    core = teaching = 0
    for index in range(160):
        grid = gen.generate(9000 + index, index, difficulty=band)
        assert grid == gen.generate(9000 + index, index, difficulty=band)
        assert gen.self_check(grid) == []
        assert gen._prediction(grid) == oracle_output(grid)
        obs = observed(grid)
        assert gen.observe_overrides(grid) == obs
        dimensions.add((obs["grid_h"], obs["grid_w"]))
        component_counts.add(obs["components"])
        repeat_counts.add(obs["repeat_color"])
        colors.update(v for row in grid for v in row if v)
        grids.add(repr(grid))
        for obj in components(grid):
            r0, c0, _, _ = obj["bbox"]
            local_shapes.add(tuple(sorted((r - r0, c - c0) for r, c in obj["cells"])))
        profile = gen.schedule_profile(9000 + index, index, band)
        teaching += profile == "teaching"
        core += obs["components"] == 3 and obs["repeat_color"] == 0 and (obs["grid_h"], obs["grid_w"]) in gen.CANONICAL_DIMENSIONS
    assert component_counts == {2, 3, 4}
    assert repeat_counts == {0, 1}
    assert colors == set(range(1, 10))
    assert len(dimensions) >= 20
    assert len(local_shapes) >= 20
    assert len(grids) == 160
    assert teaching == 80
    assert core >= 30


def test_every_default_teaching_scene_refutes_global_color_bbox_shortcut():
    for index in range(0, 40, 2):
        grid = gen.generate(712 + index, index, difficulty="hard")
        assert gen.schedule_profile(712 + index, index, "hard") == "teaching"
        assert observed(grid)["repeat_color"] == 1
        truth = oracle_output(grid)
        assert global_color_bbox(grid) != truth
        assert gen.SEMANTIC_WITNESSES["repeated_color_components"](grid)
        assert gen.SEMANTIC_RIVALS["global_color_bbox"](grid) != truth


def test_canonical_shortcut_is_real_and_has_generated_counterexamples():
    rival = gen.CANONICAL_SHORTCUTS["global_color_bbox"]
    assert all(rival(pair["input"]) == pair["output"] for pair in canonical_pairs())
    witness = gen.generate(81, 0)
    assert rival(witness) != oracle_output(witness)
    assert gen.WITNESS_RIVALS == {"repeated_color_components": ["global_color_bbox"]}


def test_every_four_pair_window_is_declared_rival_identifiable_under_every_query_rotation():
    for band in (None, "easy", "medium", "hard"):
        for start in range(12):
            pairs = []
            for offset in range(4):
                grid = gen.generate(321, start + offset, difficulty=band)
                pairs.append({"input": grid, "output": oracle_output(grid)})
            for query_index in range(4):
                demos = [pair for i, pair in enumerate(pairs) if i != query_index]
                assert gen.lesson_identifiable(demos, pairs[query_index]) == []


def test_keyed_rng_is_independent_of_python_hash_seed():
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
    grids += [gen.generate(319, index, difficulty="hard") for index in range(24)]
    assert racket_outputs(grids) == [oracle_output(grid) for grid in grids]


def test_retained_global_color_bbox_counterexample_is_valid_and_discriminating():
    payload = json.loads((HOME / "counterexamples" / "global_color_bbox.json").read_text())
    grid = payload["input"]
    expected = payload["expected_output"]
    rival_output = payload["rival_output"]
    assert payload["task_id"] == "1407f5e6f3e5"
    assert payload["rule_hash"] == gen.RULE_HASH
    assert gen.self_check(grid) == []
    assert oracle_output(grid) == expected
    assert global_color_bbox(grid) == rival_output
    assert expected != rival_output
    assert gen.SEMANTIC_WITNESSES["repeated_color_components"](grid)
