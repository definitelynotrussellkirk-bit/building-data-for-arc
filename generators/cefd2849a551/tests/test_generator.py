"""Task-local regression and semantic-contract suite for cefd2849a551."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import random
import subprocess
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (  # noqa: E402
    bbox_perimeter_rival,
    boundary_output,
    canonical_pairs,
    eight_neighbor_rival,
    identity_rival,
    load_generator,
    observed,
    racket_outputs,
)

GEN = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))
TASK_ID = "cefd2849a551"
SHAPES = ("rect", "step", "L", "T")
PALETTES = ("default", "warm", "cool", "varied")


def _pair(grid):
    return {"input": deepcopy(grid), "output": boundary_output(grid)}


def test_rule_pin_and_truthful_axis_contract():
    assert GEN.RULE_HASH == "4681778f7a43"
    assert GEN.VERSION == "2.0.0"
    assert GEN.EXAMPLES_NEEDED == 3
    assert GEN.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    assert GEN.SCHEDULE_PROFILES == SHAPES
    assert set(GEN.AXES) == {
        "grid_h",
        "grid_w",
        "shape_kind",
        "palette_kind",
    }
    assert GEN.DEGENERATE_TEXTURES == ()
    assert GEN.HELPFUL_TEXTURES == ()


def test_canonical_inputs_are_lawful_and_independent_oracle_matches_labels():
    pairs = canonical_pairs()
    assert len(pairs) == 3
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert boundary_output(pair["input"]) == pair["output"]
        assert GEN.rule_mirror(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("shape_kind", SHAPES)
@pytest.mark.parametrize("palette_kind", PALETTES)
def test_exact_joint_overrides_are_constructive_and_observable(
    band, shape_kind, palette_kind
):
    grid = GEN.generate(
        183,
        7,
        difficulty=band,
        grid_h=6,
        grid_w=7,
        shape_kind=shape_kind,
        palette_kind=palette_kind,
    )
    expected = {
        "grid_h": 6,
        "grid_w": 7,
        "shape_kind": shape_kind,
        "palette_kind": palette_kind,
    }
    assert GEN.self_check(grid) == []
    assert observed(grid) == expected
    assert GEN.observe_overrides(grid) == expected
    assert GEN.rule_mirror(grid) == boundary_output(grid)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("grid_h,grid_w", [(6, 7), (6, 18), (16, 7), (16, 18)])
def test_dimension_endpoints_work_in_every_band(band, grid_h, grid_w):
    grid = GEN.generate(
        91,
        19,
        difficulty=band,
        grid_h=grid_h,
        grid_w=grid_w,
        shape_kind="T",
        palette_kind="varied",
    )
    assert (len(grid), len(grid[0])) == (grid_h, grid_w)
    assert GEN.self_check(grid) == []
    assert GEN.observe_overrides(grid)["shape_kind"] == "T"


@pytest.mark.parametrize(
    "seed,sample_index,difficulty,overrides",
    [
        (True, 0, None, {}),
        (1.0, 0, None, {}),
        ("1", 0, None, {}),
        (0, True, None, {}),
        (0, 1.0, None, {}),
        (0, -1, None, {}),
        (0, 0, "impossible", {}),
        (0, 0, None, {"grid_h": True}),
        (0, 0, None, {"grid_h": 5}),
        (0, 0, None, {"grid_h": 17}),
        (0, 0, None, {"grid_w": 6}),
        (0, 0, None, {"grid_w": 19}),
        (0, 0, None, {"shape_kind": "circle"}),
        (0, 0, None, {"shape_kind": 1}),
        (0, 0, None, {"palette_kind": "neon"}),
        (0, 0, None, {"palette_kind": 4}),
        (0, 0, None, {"typo": 1}),
    ],
)
def test_invalid_controls_are_rejected(seed, sample_index, difficulty, overrides):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(seed, sample_index, difficulty=difficulty, **overrides)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_cyclic_four_pair_window_and_query_rotation_is_identifiable(band):
    for start in range(12):
        pairs = [
            _pair(GEN.generate(1207 + start, start + offset, difficulty=band))
            for offset in range(4)
        ]
        assert {GEN.observe_overrides(pair["input"])["shape_kind"] for pair in pairs} == set(SHAPES)
        for query_index, query in enumerate(pairs):
            demos = [pair for index, pair in enumerate(pairs) if index != query_index]
            assert GEN.lesson_identifiable(demos, query) == []
            for name, rival in GEN.LESSON_COMPETITORS.items():
                assert any(
                    rival(item["input"]) != item["output"] for item in demos
                ), (band, start, query_index, name)


def test_declared_witnesses_refute_their_named_rivals_on_generated_inputs():
    grids = [GEN.generate(711, index, difficulty="medium") for index in range(8)]
    truth = [boundary_output(grid) for grid in grids]
    expected_rivals = {
        "identity": identity_rival,
        "eight_neighbor_boundary": eight_neighbor_rival,
        "bbox_perimeter": bbox_perimeter_rival,
    }
    assert set(GEN.SEMANTIC_RIVALS) == set(expected_rivals)
    for name, independent in expected_rivals.items():
        assert all(
            GEN.SEMANTIC_RIVALS[name](grid) == independent(grid)
            for grid in grids
        )
    for witness_name, rival_names in GEN.WITNESS_RIVALS.items():
        fired = [grid for grid in grids if GEN.SEMANTIC_WITNESSES[witness_name](grid)]
        assert fired, witness_name
        for grid in fired:
            assert any(
                GEN.SEMANTIC_RIVALS[name](grid) != boundary_output(grid)
                for name in rival_names
            )
    assert all(identity_rival(grid) != answer for grid, answer in zip(grids, truth))


def test_retained_semantic_counterexample_replays_exactly():
    path = HOME / "counterexamples" / "semantic-rivals.json"
    record = json.loads(path.read_text())
    assert record["task_id"] == TASK_ID
    source_path = Path(GEN.__file__).resolve()
    assert hashlib.sha256(source_path.read_bytes()).hexdigest() == record["generator_sha256"]
    grid = GEN.generate(
        record["seed"],
        record["sample_index"],
        difficulty=record["difficulty"],
    )
    assert grid == record["input"]
    assert GEN.self_check(grid) == []
    assert boundary_output(grid) == record["intended_output"]
    for name, rival_output in record["rival_outputs"].items():
        assert GEN.SEMANTIC_RIVALS[name](grid) == rival_output
        assert rival_output != record["intended_output"]


def test_generation_is_deterministic_fresh_and_does_not_touch_global_rng():
    random.seed(8675309)
    expected_next = random.random()
    random.seed(8675309)
    for band in (None, "easy", "medium", "hard"):
        for index in range(16):
            first = GEN.generate(77, index, difficulty=band)
            second = GEN.generate(77, index, difficulty=band)
            assert first == second
            assert first is not second
            assert all(left is not right for left, right in zip(first, second))
            assert GEN.self_check(first) == []
            original = deepcopy(first)
            assert GEN.rule_mirror(first) == boundary_output(first)
            for function in (*GEN.SEMANTIC_RIVALS.values(), *GEN.SEMANTIC_WITNESSES.values()):
                function(first)
                assert first == original
    assert random.random() == expected_next


def test_validator_rejects_malformed_and_task_semantic_impostors():
    malformed = [None, [], [[]], [[0], [0, 1]], [[True] * 7 for _ in range(6)]]
    for grid in malformed:
        assert GEN.self_check(grid)

    valid = GEN.generate(4, 2, grid_h=8, grid_w=10, shape_kind="L")
    color = next(value for row in valid for value in row if value)
    height, width = len(valid), len(valid[0])
    impostors = {
        "all_background": [[0] * width for _ in range(height)],
        "full_one_color": [[color] * width for _ in range(height)],
        "singleton": [[color if (r, c) == (3, 4) else 0 for c in range(width)] for r in range(height)],
        "short_line": [[color if r == 3 and 2 <= c <= 5 else 0 for c in range(width)] for r in range(height)],
        "hollow_ring": [[color if 1 <= r <= 5 and 1 <= c <= 6 and (r in (1, 5) or c in (1, 6)) else 0 for c in range(width)] for r in range(height)],
        "two_components": deepcopy(valid),
    }
    impostors["two_components"][0][0] = color
    for name, grid in impostors.items():
        assert GEN.self_check(grid), name


def test_pinned_profile_floor_has_exact_support_in_every_band():
    canonical_profiles = {(6, 9, 2), (6, 7, 2)}
    pooled = 0
    for band in ("easy", "medium", "hard"):
        exact = 0
        for index in range(20):
            digest = hashlib.sha256(
                f"profile-floor:v1:{TASK_ID}:{band}:{index}".encode()
            ).hexdigest()
            seed = int(digest[:12], 16)
            grid = GEN.generate(seed, seed % 7919 + index, difficulty=band)
            profile = (
                len(grid),
                len(grid[0]),
                len({value for row in grid for value in row}),
            )
            exact += profile in canonical_profiles
        assert exact >= 1, (band, exact)
        pooled += exact
    assert pooled >= 3


def test_keyed_generation_is_independent_of_python_hash_seed():
    script = (
        "import json,sys;sys.path.insert(0,sys.argv[1]);"
        "from reference_probe import load_generator;"
        "g=load_generator();print(json.dumps([g.generate(31,i,difficulty='hard') for i in range(8)]))"
    )
    results = []
    for hash_seed in ("1", "901"):
        environment = dict(
            os.environ,
            PYTHONHASHSEED=hash_seed,
            PYTHONDONTWRITEBYTECODE="1",
        )
        results.append(
            subprocess.check_output(
                [sys.executable, "-B", "-c", script, str(HOME / "workspace")],
                env=environment,
                text=True,
            )
        )
    assert results[0] == results[1]


def test_real_racket_reference_matches_independent_oracle_when_available():
    from arc_repl.racket_bridge import racket_runtime_status

    status = racket_runtime_status()
    if not status["available"]:
        pytest.skip(status["reason"])
    grids = [pair["input"] for pair in canonical_pairs()]
    grids += [GEN.generate(319, index, difficulty="hard") for index in range(16)]
    assert racket_outputs(grids) == [boundary_output(grid) for grid in grids]
