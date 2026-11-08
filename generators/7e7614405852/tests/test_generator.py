"""Task-local regression tests for the exact-horizontal-triple sampler."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import itertools
import os
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root

TASK_ID = "7e7614405852"
RULE_HASH = "5eb06a6d574a"
AXIS_DOMAINS = {
    "grid_h": range(5, 13),
    "grid_w": range(8, 17),
    "n_len2": range(0, 2),
    "n_len3": range(1, 4),
    "n_len4": range(0, 3),
    "n_len5": range(0, 2),
    "n_vertical3": range(0, 2),
}
HOME = Path(__file__).resolve().parents[1]


def _load_generator():
    path = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))
    spec = importlib.util.spec_from_file_location("generator_under_test", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen = _load_generator()


def reference_output(grid):
    """Independent row scanner matching the canonical written rule."""
    out = [list(row) for row in grid]
    for r, row in enumerate(grid):
        c = 0
        while c < len(row):
            color = row[c]
            if color == 0:
                c += 1
                continue
            end = c + 1
            while end < len(row) and row[end] == color:
                end += 1
            if end - c == 3:
                out[r][c + 1] = 8
            c = end
    return out


def observed_runs(grid):
    counts = {2: 0, 3: 0, 4: 0, 5: 0}
    for row in grid:
        c = 0
        while c < len(row):
            color = row[c]
            if color == 0:
                c += 1
                continue
            end = c + 1
            while end < len(row) and row[end] == color:
                end += 1
            if end - c in counts:
                counts[end - c] += 1
            c = end
    return counts


def _profile(grid):
    return len(grid), len(grid[0]), len({value for row in grid for value in row})


def _profile_seed(band, index):
    digest = hashlib.sha256(
        f"profile-floor:v1:{TASK_ID}:{band}:{index}".encode()
    ).hexdigest()
    return int(digest[:12], 16)


def test_declares_truthful_exact_contract():
    assert getattr(gen, "RULE_HASH", None) == RULE_HASH
    assert getattr(gen, "VERSION", None) == "2.0.0"
    assert set(getattr(gen, "AXES", {})) == set(AXIS_DOMAINS)
    assert getattr(gen, "INCOMPATIBLE_OVERRIDE_COMBINATIONS", None) == []
    assert not hasattr(gen, "DEGENERATE_TEXTURES")
    assert callable(getattr(gen, "observe_overrides", None))
    assert callable(getattr(gen, "strict_canonical_like", None))


@pytest.mark.parametrize(
    "pair",
    canonical_pairs(TASK_ID, root=find_root(__file__)),
    ids=["train0", "train1", "test0"],
)
def test_accepts_canonical_pairs_and_independent_oracle_matches(pair):
    assert gen.self_check(pair["input"]) == []
    assert gen.strict_canonical_like(pair["input"]) == []
    assert reference_output(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_maximal_exact_overrides_are_constructive_and_observable(band):
    options = {
        "grid_h": 5,
        "grid_w": 8,
        "n_len2": 1,
        "n_len3": 3,
        "n_len4": 2,
        "n_len5": 1,
        "n_vertical3": 1,
    }
    observer = getattr(gen, "observe_overrides", None)
    assert callable(observer)
    grid = gen.generate(17, 9, difficulty=band, **options)
    assert gen.self_check(grid) == []
    assert observer(grid) == options
    assert reference_output(grid) != grid


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_boundary_override_cartesian_product_is_constructive(band):
    observer = getattr(gen, "observe_overrides", None)
    assert callable(observer)
    shapes = [(5, 8), (12, 16)]
    count_domains = (
        (0, 1),
        (1, 2, 3),
        (0, 1, 2),
        (0, 1),
        (0, 1),
    )
    for h, w in shapes:
        for n2, n3, n4, n5, vertical in itertools.product(*count_domains):
            options = {
                "grid_h": h,
                "grid_w": w,
                "n_len2": n2,
                "n_len3": n3,
                "n_len4": n4,
                "n_len5": n5,
                "n_vertical3": vertical,
            }
            grid = gen.generate(71, 13, difficulty=band, **options)
            assert gen.self_check(grid) == [], options
            assert observer(grid) == options


@pytest.mark.parametrize(
    "key,value",
    [
        ("typo", 1),
        ("grid_h", 4),
        ("grid_h", 13),
        ("grid_w", 7),
        ("grid_w", 17),
        ("n_len2", 2),
        ("n_len3", 0),
        ("n_len3", 4),
        ("n_len4", 3),
        ("n_len5", 2),
        ("n_vertical3", 2),
        ("n_len3", 2.0),
        ("grid_h", True),
        ("n_len4", "1"),
    ],
)
def test_rejects_unknown_out_of_range_and_non_integer_overrides(key, value):
    with pytest.raises((TypeError, ValueError, KeyError)):
        gen.generate(0, 0, **{key: value})


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_defaults_always_include_rule_discriminating_witnesses(band):
    observer = getattr(gen, "observe_overrides", None)
    assert callable(observer)
    for index in range(64):
        grid = gen.generate(4000 + index, index * 7, difficulty=band)
        stats = observer(grid)
        assert stats["n_len5"] == 1
        assert stats["n_vertical3"] == 1
        assert stats["n_len3"] >= 1
        assert gen.self_check(grid) == []


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_each_band_hits_a_canonical_shape_palette_profile(band):
    canonical_profiles = {
        _profile(pair["input"])
        for pair in canonical_pairs(TASK_ID, root=find_root(__file__))
    }
    seen = {
        _profile(
            gen.generate(
                _profile_seed(band, index),
                _profile_seed(band, index) % 7919 + index,
                difficulty=band,
            )
        )
        for index in range(20)
    }
    assert canonical_profiles & seen, (band, canonical_profiles, seen)


def test_semantic_witnesses_refute_declared_rivals():
    witnesses = getattr(gen, "SEMANTIC_WITNESSES", None)
    rivals = getattr(gen, "SEMANTIC_RIVALS", None)
    mapping = getattr(gen, "WITNESS_RIVALS", None)
    competitors = getattr(gen, "LESSON_COMPETITORS", None)
    shortcuts = getattr(gen, "CANONICAL_SHORTCUTS", None)
    assert isinstance(witnesses, dict) and witnesses
    assert isinstance(rivals, dict) and rivals
    assert isinstance(mapping, dict) and mapping
    assert isinstance(competitors, dict) and competitors
    assert isinstance(shortcuts, dict) and shortcuts

    grid = gen.generate(
        23,
        5,
        grid_h=7,
        grid_w=10,
        n_len2=1,
        n_len3=2,
        n_len4=1,
        n_len5=1,
        n_vertical3=1,
    )
    truth = reference_output(grid)
    for witness_name, rival_names in mapping.items():
        assert witnesses[witness_name](deepcopy(grid)), witness_name
        assert any(rivals[name](deepcopy(grid)) != truth for name in rival_names)
    for name, rival in competitors.items():
        assert rival(deepcopy(grid)) != truth, name


@pytest.mark.parametrize(
    "mutation",
    ["blank", "output_color", "singleton", "too_long", "no_exact_triple"],
)
def test_validator_rejects_destructive_mutations(mutation):
    grid = gen.generate(
        91,
        4,
        grid_h=7,
        grid_w=10,
        n_len2=1,
        n_len3=2,
        n_len4=1,
        n_len5=1,
        n_vertical3=1,
    )
    if mutation == "blank":
        grid = [[0 for _ in row] for row in grid]
    elif mutation == "output_color":
        grid[0][0] = 8
    elif mutation == "singleton":
        for r, row in enumerate(grid):
            for c, value in enumerate(row):
                if value == 0:
                    grid[r][c] = 6
                    break
            else:
                continue
            break
    elif mutation == "too_long":
        grid = [[0] * 10 for _ in range(7)]
        grid[2][1:7] = [4] * 6
        grid[5][2:5] = [3] * 3
    elif mutation == "no_exact_triple":
        grid = [[0] * 10 for _ in range(7)]
        grid[1][1:3] = [2] * 2
        grid[4][3:7] = [5] * 4
    assert gen.self_check(grid)


@pytest.mark.parametrize("bad", [None, [], [[]], [[0], [0, 1]], [[True] * 8 for _ in range(5)]])
def test_validator_reports_malformed_grids_without_raising(bad):
    assert gen.self_check(bad)


def test_deterministic_and_input_oracle_is_pure():
    first = gen.generate(411, 19, difficulty="hard")
    assert first == gen.generate(411, 19, difficulty="hard")
    original = deepcopy(first)
    out = reference_output(first)
    assert first == original
    assert out != first
