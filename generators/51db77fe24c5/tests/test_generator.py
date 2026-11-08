"""Source-bound regressions for the repaired exact-2x2 selector generator."""
from __future__ import annotations

from copy import deepcopy
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
    LEGACY_DISTRACTOR_MASKS,
    NONLEGACY_L_TRIOMINOES,
    SIZE4_CONTROL,
    T_TETROMINOES,
    bbox_2x2_output,
    blue_components,
    historical_shortcut_fixture,
    legacy_memorizer_output,
    load_generator,
    masks,
    observed,
    oracle_output,
    size4_output,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))


def _canonical_pairs():
    from reviewer_support import canonical_pairs, find_root

    return canonical_pairs("51db77fe24c5", root=find_root(__file__))


def test_pins_selected_authority_and_advertises_only_exact_axes():
    assert gen.RULE_HASH == "06fb2695c6fe"
    assert gen.VERSION == "2.0.0"
    assert set(gen.AXES) == {"grid_h", "grid_w", "square_count", "distractor_kind"}
    assert gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []


@pytest.mark.parametrize("pair", _canonical_pairs(), ids=lambda pair: f"{pair['split']}{pair['pair_index']}")
def test_accepts_every_canonical_input_and_independent_oracle_matches(pair):
    original = deepcopy(pair["input"])
    assert gen.self_check(pair["input"]) == []
    assert oracle_output(pair["input"]) == pair["output"]
    assert pair["input"] == original


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("kind", ["domino", "line3", "line4", "t4", "polyomino"])
def test_exact_overrides_are_observable_on_the_smallest_grid_in_every_band(band, kind):
    options = {"grid_h": 8, "grid_w": 8, "square_count": 2, "distractor_kind": kind}
    grid = gen.generate(1701, 29, difficulty=band, **options)
    assert gen.self_check(grid, difficulty=band) == []
    assert observed(grid) == options
    assert gen.observe_overrides(grid) == options


@pytest.mark.parametrize(
    "key,value",
    [
        ("typo_axis", 1),
        ("grid_h", 7),
        ("grid_h", 15),
        ("grid_w", 7),
        ("grid_w", 15),
        ("square_count", 0),
        ("square_count", 3),
        ("distractor_kind", "legacy"),
        ("grid_h", True),
        ("grid_w", 8.5),
        ("square_count", "2"),
        ("distractor_kind", 4),
    ],
)
def test_invalid_and_unknown_overrides_are_rejected(key, value):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **{key: value})


@pytest.mark.parametrize("kind", ["domino", "line3", "line4", "t4", "polyomino"])
def test_each_distractor_kind_has_real_shape_diversity(kind):
    broad_masks = set()
    for index in range(96):
        grid = gen.generate(7000 + index, index, grid_h=10, grid_w=11, distractor_kind=kind)
        assert gen.self_check(grid) == []
        info = observed(grid)
        assert info["distractor_kind"] == kind
        non_square_masks = [mask for mask in masks(grid) if len(mask) != 4 or mask != ((0, 0), (0, 1), (1, 0), (1, 1))]
        broad = [
            mask for mask in non_square_masks
            if mask not in NONLEGACY_L_TRIOMINOES and mask != SIZE4_CONTROL
        ]
        assert len(broad) == 1
        broad_masks.add(broad[0])
    required = {"domino": 2, "line3": 2, "line4": 2, "t4": 4, "polyomino": 40}[kind]
    assert len(broad_masks) >= required


def test_default_distribution_covers_canonical_missing_masks_and_many_novel_masks():
    seen_kinds = set()
    seen_masks = set()
    unique_inputs = set()
    for index in range(320):
        grid = gen.generate(9000 + index, index, difficulty="medium")
        assert grid == gen.generate(9000 + index, index, difficulty="medium")
        assert gen.self_check(grid) == []
        info = observed(grid)
        seen_kinds.add(info["distractor_kind"])
        seen_masks.update(mask for mask in masks(grid) if mask != ((0, 0), (0, 1), (1, 0), (1, 1)))
        unique_inputs.add(json.dumps(grid, separators=(",", ":")))
    assert seen_kinds == {"domino", "line3", "line4", "t4", "polyomino"}
    assert ((0, 0), (1, 0), (2, 0)) in seen_masks  # canonical vertical length 3
    assert ((0, 0), (1, 0), (2, 0), (3, 0)) in seen_masks  # canonical vertical length 4
    assert ((0, 0), (0, 1), (0, 2), (0, 3)) in seen_masks
    assert any(mask in T_TETROMINOES for mask in seen_masks)
    assert len(seen_masks) >= 80
    assert len(unique_inputs) >= 300


def test_historical_finite_mask_shortcut_is_reproduced_and_then_broken():
    old_grammar = historical_shortcut_fixture(novel=False)
    assert {mask for mask in masks(old_grammar) if mask != ((0, 0), (0, 1), (1, 0), (1, 1))} == LEGACY_DISTRACTOR_MASKS
    assert legacy_memorizer_output(old_grammar) == oracle_output(old_grammar)

    repaired_grammar = historical_shortcut_fixture(novel=True)
    assert legacy_memorizer_output(repaired_grammar) != oracle_output(repaired_grammar)


def test_every_generated_lesson_refutes_all_declared_shortcuts():
    for start in range(48):
        demos = []
        for offset in range(3):
            grid = gen.generate(12000 + start, start + offset, difficulty="hard")
            truth = oracle_output(grid)
            assert gen.strict_canonical_like(grid) == []
            for name, rival in gen.LESSON_COMPETITORS.items():
                assert rival(grid) != truth, name
            for name, witness in gen.SEMANTIC_WITNESSES.items():
                assert witness(grid), name
            demos.append({"input": grid, "output": truth})
        query_grid = gen.generate(12000 + start, start + 3, difficulty="hard")
        query = {"input": query_grid, "output": oracle_output(query_grid)}
        assert gen.lesson_identifiable(demos, query) == []


def test_bbox_rival_recolors_the_required_l_witness():
    grid = gen.generate(31, 8, distractor_kind="domino")
    assert any(mask in NONLEGACY_L_TRIOMINOES for mask in masks(grid))
    assert bbox_2x2_output(grid) != oracle_output(grid)


@pytest.mark.parametrize(
    "grid",
    [
        None,
        [],
        [[]],
        [[0], [0, 1]],
        [[True for _ in range(8)] for _ in range(8)],
        [[0 for _ in range(8)] for _ in range(8)],
    ],
)
def test_malformed_or_semantically_empty_grid_is_diagnostic_not_exception(grid):
    assert gen.self_check(grid)


def test_keyed_generation_is_replayable_and_does_not_touch_global_random_state():
    random.seed(20261004)
    state = random.getstate()
    first = gen.generate(412, 111, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(412, 111, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))

    script = (
        "import importlib.util,json,sys;"
        "p=sys.argv[1];s=importlib.util.spec_from_file_location('g',p);"
        "m=importlib.util.module_from_spec(s);s.loader.exec_module(m);"
        "print(json.dumps(m.generate(41,9,difficulty='hard'),separators=(',',':')))"
    )
    source = str(Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py")))
    outputs = []
    for hash_seed in ("1", "991"):
        env = dict(os.environ, PYTHONHASHSEED=hash_seed, PYTHONDONTWRITEBYTECODE="1")
        outputs.append(subprocess.check_output([sys.executable, "-B", "-c", script, source], env=env, text=True))
    assert outputs[0] == outputs[1]


def test_each_difficulty_band_hits_canonical_scale_in_pinned_twenty_draw_census():
    """Mirror the blocking profile-floor sample used for repaired generators."""
    import hashlib

    for band in ("easy", "medium", "hard"):
        profiles = []
        for index in range(20):
            digest = hashlib.sha256(
                f"profile-floor:v1:51db77fe24c5:{band}:{index}".encode()
            ).hexdigest()
            seed = int(digest[:12], 16)
            grid = gen.generate(seed, seed % 7919 + index, difficulty=band)
            profiles.append((len(grid), len(grid[0])))
        assert any(8 <= h <= 10 and 8 <= w <= 10 for h, w in profiles), (
            band,
            profiles,
        )


def test_every_generated_input_refutes_the_size_four_component_shortcut():
    for kind in ("domino", "line3", "line4", "t4", "polyomino"):
        for index in range(12):
            grid = gen.generate(15000 + index, index, grid_h=8, grid_w=8,
                                square_count=2, distractor_kind=kind)
            assert SIZE4_CONTROL in masks(grid)
            assert size4_output(grid) != oracle_output(grid)
