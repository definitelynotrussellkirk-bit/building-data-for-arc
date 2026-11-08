"""Bounded behavioral contract for the native tile-order family.

Literal examples establish semantics independently of the implementation.
Sampling checks cover two seeds and the supported count endpoints, rather than
repeating the generator's full production battery.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import sys
from types import ModuleType

import pytest


TASK = "997c17fd6870"
SETTINGS = tuple(
    {"tile_width": width, "order_mode": mode}
    for width in (2, 3)
    for mode in ("reverse", "densest_prefix")
)
DEFAULT = {"tile_width": 2, "order_mode": "reverse"}


def _root():
    """Bind to this test's own repository, never cwd or a cached prototype."""
    here = Path(__file__).resolve()
    for candidate in here.parents:
        if ((candidate / "generators" / TASK).is_dir()
                and (candidate / "shared/runtime/reviewer_support.py").is_file()):
            return candidate
    raise AssertionError(f"No task-local repository ancestor for {here}")


ROOT = _root()
HOME = ROOT / "generators" / TASK / "workspace/parametric"


def _load(path, suffix):
    path = path.resolve()
    assert path.is_relative_to(ROOT), "test module source escaped this repository"
    assert path.is_file(), f"native family source must exist: {path}"
    name = "_native_997c17fd6870_" + suffix + hashlib.sha256(str(path).encode()).hexdigest()[:12]
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def family():
    return _load(HOME / "native_family.py", "family")


@pytest.fixture(scope="module")
def support():
    return _load(ROOT / "shared/runtime/reviewer_support.py", "public")


def _frozen(grid):
    return tuple(map(tuple, grid))


def _inputs(episode):
    return [_frozen(pair["input"]) for pair in episode["train"] + episode["test"]]


def test_adapter_uses_adjacent_source_despite_cached_prototype(family, monkeypatch):
    poison = ModuleType("prototype")
    poison.program = poison.generate = lambda *args, **kwargs: pytest.fail("cached prototype used")
    monkeypatch.setitem(sys.modules, "prototype", poison)
    adapter = _load(HOME / "adapter.py", "adapter")
    assert adapter.program(DEFAULT) == family.program(DEFAULT)
    assert adapter.generate(17, DEFAULT, demos=2, queries=1) == family.generate(
        17, DEFAULT, demos=2, queries=1
    )


def test_default_program_is_exact_canonical_bytes(family):
    authority = ROOT / "shared/data/base/solutions/training/8ee62060__997c17fd6870.json"
    canonical = json.loads(authority.read_text())["racket_target"]["target_code"]
    assert family.program(DEFAULT) == canonical
    programs = [family.program(setting) for setting in SETTINGS]
    assert all(type(program) is str and program.strip() for program in programs)
    assert len(set(programs)) == len(SETTINGS)


def test_every_native_and_rival_program_is_accepted_by_the_real_rule_wrapper(family):
    from puzzle_generators.rule_wrap import wrap_rule

    for setting in SETTINGS:
        wrap_rule(family.program(setting))
        for name in family.rivals(setting):
            wrap_rule(family.rival_program(setting, name))


@pytest.mark.parametrize("mode", ["reverse", "densest_prefix"])
def test_literal_leftmost_density_tie_and_suffix(mode, family):
    grid = [[1, 2, 3, 4, 5, 6, 7, 8], [0, 0, 3, 4, 5, 6, 0, 0]]
    assert list(family.tile_scores(grid, 2)) == [2, 4, 4, 2]
    expected = (
        [[7, 8, 5, 6, 3, 4, 1, 2], [0, 0, 5, 6, 3, 4, 0, 0]]
        if mode == "reverse" else
        [[3, 4, 1, 2, 5, 6, 7, 8], [3, 4, 0, 0, 5, 6, 0, 0]]
    )
    original = deepcopy(grid)
    assert family.reference(grid, {"tile_width": 2, "order_mode": mode}) == expected
    assert grid == original


def test_density_counts_the_full_height_before_selecting_prefix(family):
    grid = [
        [1, 0, 2, 0, 3, 0, 4, 0],
        [0, 0, 2, 2, 3, 3, 0, 0],
        [0, 0, 0, 0, 3, 3, 0, 0],
    ]
    assert list(family.tile_scores(grid, 2)) == [1, 3, 5, 1]
    assert family.reference(grid, {"tile_width": 2, "order_mode": "densest_prefix"}) == [
        [3, 0, 2, 0, 1, 0, 4, 0],
        [3, 3, 2, 2, 0, 0, 0, 0],
        [3, 3, 0, 0, 0, 0, 0, 0],
    ]


def test_three_column_tiles_preserve_internal_column_order(family):
    grid = [[1, 2, 0, 3, 4, 5, 6, 0, 0]]
    assert list(family.tile_scores(grid, 3)) == [2, 3, 1]
    assert family.reference(grid, {"tile_width": 3, "order_mode": "reverse"}) == [
        [6, 0, 0, 3, 4, 5, 1, 2, 0]
    ]
    assert family.reference(grid, {"tile_width": 3, "order_mode": "densest_prefix"}) == [
        [3, 4, 5, 1, 2, 0, 6, 0, 0]
    ]


@pytest.mark.parametrize("setting", SETTINGS)
def test_transform_grammar_is_broader_than_sampling_grammar(setting, family):
    width = setting["tile_width"]
    for grid in ([[0] * width], [[9] * width for _ in range(30)]):
        assert family.reference(grid, setting) == grid


def _check_sample_grid(grid):
    assert type(grid) is list and 6 <= len(grid) <= 30 and len(grid) % 2 == 0
    width = len(grid[0])
    assert 6 <= width <= 30 and width % 6 == 0
    assert all(type(row) is list and len(row) == width for row in grid)
    assert all(type(cell) is int and 0 <= cell <= 9 for row in grid for cell in row)
    colors = sorted({cell for row in grid for cell in row if cell})
    assert len(colors) == 2
    legal = {((0, 0), (0, 0))}
    for first, second in (colors, colors[::-1]):
        legal.update({
            ((first, first), (second, first)),
            ((first, 0), (second, second)),
            ((first, second), (second, 0)),
            ((first, second), (second, first)),
        })
    for row in range(0, len(grid), 2):
        for col in range(0, width, 2):
            assert tuple(tuple(line[col:col + 2]) for line in grid[row:row + 2]) in legal


@pytest.mark.parametrize("seed", [0, 17])
@pytest.mark.parametrize("demos", [2, 3, 6])
def test_matched_novel_inputs_identifiable_demos_and_query_boundaries(seed, demos, family):
    episodes = [family.generate(seed, setting, demos=demos, queries=4) for setting in SETTINGS]
    assert all(_inputs(episode) == _inputs(episodes[0]) for episode in episodes)
    for selected, episode in zip(SETTINGS, episodes):
        assert len(episode["train"]) == demos and len(episode["test"]) == 4
        assert episode["program_solution"] == family.program(selected)
        assert len(set(_inputs(episode))) == demos + 4
        for pair in episode["train"] + episode["test"]:
            _check_sample_grid(pair["input"])
            assert pair["output"] == family.reference(pair["input"], selected)
        survivors = [
            setting for setting in SETTINGS
            if all(family.reference(pair["input"], setting) == pair["output"]
                   for pair in episode["train"])
        ]
        assert survivors == [selected], "demonstrations alone must identify the hidden rule"
        dimensions = {(len(pair["input"]), len(pair["input"][0])) for pair in episode["test"]}
        assert {(6, 6), (30, 30)} <= dimensions
        large = next(pair["input"] for pair in episode["test"] if len(pair["input"]) == 30
                     and len(pair["input"][0]) == 30)
        assert sum(any(row) for row in large) >= 10
        assert sum(any(row[col] for row in large) for col in range(30)) >= 10
        assert sum(bool(cell) for row in large for cell in row) >= 45


@pytest.mark.parametrize("setting", SETTINGS)
def test_counts_do_not_change_the_first_query_and_rng_is_local(setting, family):
    random.seed(845)
    rng_before = random.getstate()
    short = family.generate(17, setting, demos=2, queries=1)
    long = family.generate(17, setting, demos=6, queries=4)
    again = family.generate(17, setting, demos=2, queries=1)
    assert random.getstate() == rng_before
    assert short == again and short is not again
    assert short["train"] == long["train"][:2]
    assert short["test"][0] == long["test"][0]
    short["train"][0]["input"][0][0] = -1
    assert family.generate(17, setting, demos=2, queries=1) == again


def test_first_public_turn_matches_single_query_and_hides_private_fields(family, support):
    single = family.generate(17, DEFAULT, demos=3, queries=1)
    multi = family.generate(17, DEFAULT, demos=3, queries=4)
    first_turn = deepcopy(multi)
    first_turn["test"] = first_turn["test"][:1]
    first_turn.update(seed="private", settings={"secret": True}, metadata={"secret": True})
    raw = support.public_challenge_bytes(first_turn)
    assert raw == support.public_challenge_bytes(single)
    public = json.loads(raw)
    assert set(public) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert len(public["test"]) == 1 and set(public["test"][0]) == {"input"}
    assert raw == (json.dumps(public, sort_keys=True, separators=(",", ":")) + "\n").encode()


@pytest.mark.parametrize("setting", [
    {}, {"tile_width": 2}, {"order_mode": "reverse"},
    {"tile_width": True, "order_mode": "reverse"},
    {"tile_width": 2.0, "order_mode": "reverse"},
    {"tile_width": 1, "order_mode": "reverse"},
    {"tile_width": 4, "order_mode": "reverse"},
    {"tile_width": 2, "order_mode": True},
    {"tile_width": 2, "order_mode": "unknown"},
    {"tile_width": 2, "order_mode": "reverse", "extra": 0}, None,
])
def test_invalid_settings_rejected_consistently(setting, family):
    for call in (
        lambda: family.program(setting),
        lambda: family.reference([[1, 2, 3, 4, 5, 6]], setting),
        lambda: family.generate(0, setting, demos=2, queries=1),
    ):
        with pytest.raises((ValueError, TypeError)):
            call()


@pytest.mark.parametrize("kwargs", [
    {"seed": True}, {"seed": 0.0}, {"seed": -1}, {"seed": 2**63},
    {"demos": True}, {"demos": 2.0}, {"demos": 1}, {"demos": 7},
    {"queries": True}, {"queries": 1.0}, {"queries": 0}, {"queries": 5},
])
def test_seed_and_count_limits_fail_closed(kwargs, family):
    arguments = {"seed": 0, "settings": DEFAULT, "demos": 3, "queries": 4}
    arguments.update(kwargs)
    with pytest.raises((ValueError, TypeError)):
        family.generate(**arguments)


@pytest.mark.parametrize("grid", [
    [], [[]], [[1, 2], [3]], [[True, 0]], [[1.0, 0]], [["1", 0]],
    [[-1, 0]], [[10, 0]], [[0, 0, 0]], [[0] * 32], [[0, 0]] * 31,
])
def test_invalid_transform_grids_rejected(grid, family):
    for mode in ("reverse", "densest_prefix"):
        with pytest.raises((ValueError, TypeError)):
            family.reference(grid, {"tile_width": 2, "order_mode": mode})
    with pytest.raises((ValueError, TypeError)):
        family.tile_scores(grid, 2)


def test_maximum_literal_seed_is_supported(family):
    episode = family.generate(2**63 - 1, DEFAULT, demos=2, queries=1)
    assert len(episode["train"]) == 2 and len(episode["test"]) == 1
