"""Regression tests for the template-row color-substitution generator."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import hashlib
import json
import os
from pathlib import Path
import random

import pytest

TASK_ID = "83ca9df09514"
HOME = Path(__file__).resolve().parents[1]


def _load_generator():
    path = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))
    spec = importlib.util.spec_from_file_location(f"generator_{TASK_ID}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen = _load_generator()


def _canonical_pairs() -> list[dict]:
    try:
        from reviewer_support import canonical_pairs, find_root
    except ImportError:
        root = HOME.parents[1]
        with (root / "shared/data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
            rows = [json.loads(line) for line in handle if json.loads(line).get("task_id") == TASK_ID]
        assert len(rows) == 1
        return [*rows[0]["train"], *rows[0]["test"]]
    return canonical_pairs(TASK_ID, root=find_root(__file__), labeled_only=True)


def _template_row(grid: list[list[int]]) -> int:
    counts = [sum(value != 0 for value in row) for row in grid]
    maximum = max(counts)
    assert counts.count(maximum) == 1
    return counts.index(maximum)


def _oracle(grid: list[list[int]]) -> list[list[int]]:
    """Independent statement of the selected Racket rule."""
    height, width = len(grid), len(grid[0])
    template_row = _template_row(grid)
    template = grid[template_row]
    output = deepcopy(grid)
    for row in range(height):
        if row == template_row:
            continue
        if not any(grid[row]):
            output[row] = [0] * width
            continue
        mapping: dict[int, int] = {}
        for column, value in enumerate(grid[row]):
            if value != 0:
                mapping[template[column]] = value
        output[row] = [mapping.get(template[column], 0) for column in range(width)]
    return output


def _profile(grid: list[list[int]]) -> tuple[int, int, int]:
    return len(grid), len(grid[0]), len({value for row in grid for value in row})


def test_metadata_pins_authority_and_declares_only_constructive_axes():
    assert gen.VERSION == "3.0.1"
    assert gen.RULE_HASH == "1dc6f00b70c9"
    assert set(gen.AXES) == {
        "grid_h",
        "grid_w",
        "n_keys",
        "n_groups",
        "template_position",
        "key_layout",
    }
    assert gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    assert tuple(gen.HELPFUL_TEXTURES) == ()
    assert tuple(gen.DEGENERATE_TEXTURES) == ()


@pytest.mark.parametrize("pair", _canonical_pairs())
def test_canonical_inputs_are_owned_and_match_independent_oracle(pair):
    source = deepcopy(pair["input"])
    assert gen.self_check(source) == []
    assert gen.strict_canonical_like(source) == []
    assert _oracle(source) == pair["output"]
    assert gen.rule_mirror(source) == pair["output"]
    assert source == pair["input"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "requested",
    [
        {
            "grid_h": 6,
            "grid_w": 8,
            "n_keys": 4,
            "n_groups": 4,
            "template_position": "top",
            "key_layout": "prefix",
        },
        {
            "grid_h": 16,
            "grid_w": 18,
            "n_keys": 1,
            "n_groups": 2,
            "template_position": "bottom",
            "key_layout": "shifted",
        },
        {
            "grid_h": 11,
            "grid_w": 13,
            "n_keys": 3,
            "n_groups": 3,
            "template_position": "random",
            "key_layout": "scattered",
        },
    ],
)
def test_every_advertised_override_round_trips_in_every_band(band, requested):
    grid = gen.generate(913, 37, difficulty=band, **requested)
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == requested
    assert gen.rule_mirror(grid) == _oracle(grid)


@pytest.mark.parametrize(
    "overrides",
    [
        {"typo_axis": 1},
        {"grid_h": 5},
        {"grid_h": 17},
        {"grid_w": 7},
        {"grid_w": 19},
        {"n_keys": 0},
        {"n_keys": 5},
        {"n_groups": 1},
        {"n_groups": 5},
        {"template_position": "left"},
        {"key_layout": "dense"},
        {"grid_h": True},
        {"grid_w": 8.0},
        {"n_keys": "2"},
        {"n_groups": None},
    ],
)
def test_invalid_or_unknown_overrides_are_rejected(overrides):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **overrides)


@pytest.mark.parametrize(
    "seed,sample_index",
    [(True, 0), (1.5, 0), ("1", 0), (0, True), (0, -1), (0, 1.0), (0, "1")],
)
def test_seed_and_sample_index_are_strict(seed, sample_index):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(seed, sample_index)


def test_default_schedule_hits_every_canonical_profile_in_every_band():
    expected = {_profile(pair["input"]) for pair in _canonical_pairs()}
    assert expected == {(6, 8, 5), (10, 8, 5), (10, 8, 7), (12, 8, 8), (14, 10, 7)}
    for band in (None, "easy", "medium", "hard"):
        observed = {_profile(gen.generate(600 + index, index, difficulty=band)) for index in range(5)}
        assert observed == expected


def test_default_sampling_exercises_the_full_declared_width_envelope():
    widths = {
        len(gen.generate(seed, seed, difficulty=band)[0])
        for band in ("easy", "medium", "hard")
        for seed in range(1, 9)
    }
    assert min(widths) == 8
    assert max(widths) == 18


def test_schedule_is_deterministic_fresh_and_global_rng_pure():
    random.seed(20261012)
    state = random.getstate()
    first = gen.generate(314159, 7, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(314159, 7, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert first != second


def test_canonical_shortcuts_really_fit_canonical_and_generated_data_refutes_them():
    assert set(gen.CANONICAL_SHORTCUTS) == {
        "first_three_columns_only",
        "exactly_two_template_groups",
        "template_is_row_one",
    }
    for pair in _canonical_pairs():
        for name, rival in gen.CANONICAL_SHORTCUTS.items():
            assert rival(pair["input"]) == pair["output"], name

    for index in range(12):
        grid = gen.generate(1200 + index, index, difficulty=("easy", "medium", "hard")[index % 3])
        intended = _oracle(grid)
        for name, rival in gen.CANONICAL_SHORTCUTS.items():
            assert rival(grid) != intended, (index, name)


def test_every_rotated_lesson_is_identifiable_against_named_competitors():
    for band in (None, "easy", "medium", "hard"):
        pairs = []
        for index in range(16):
            grid = gen.generate(700 + index, index, difficulty=band)
            assert gen.self_check(grid) == []
            pairs.append({"input": grid, "output": _oracle(grid)})
        for start in range(13):
            window = pairs[start : start + 4]
            for query_index in range(4):
                demos = [pair for index, pair in enumerate(window) if index != query_index]
                assert gen.lesson_identifiable(demos, window[query_index]) == []


def test_every_default_sample_exposes_all_declared_semantic_witnesses():
    for index in range(10):
        grid = gen.generate(1900 + index, index)
        for name, witness in gen.SEMANTIC_WITNESSES.items():
            assert witness(grid), (index, name)
        intended = _oracle(grid)
        for name, rival in gen.LESSON_COMPETITORS.items():
            assert rival(grid) != intended, (index, name)


@pytest.mark.parametrize(
    "malformed",
    [None, [], [[]], [[0], [0, 1]], [[True] * 8 for _ in range(6)], [[10] * 8 for _ in range(6)]],
)
def test_self_check_reports_malformed_grids_without_raising(malformed):
    assert gen.self_check(malformed)


def test_self_check_rejects_structural_impostors_without_mutating_input():
    grid = gen.generate(81, 3)
    original = deepcopy(grid)
    assert gen.self_check(grid) == []
    assert grid == original

    damaged = deepcopy(grid)
    template_row = _template_row(damaged)
    damaged[template_row][0] = 0
    assert gen.self_check(damaged)

    damaged = deepcopy(grid)
    template_row = _template_row(damaged)
    for row in range(len(damaged)):
        if row != template_row:
            damaged[row] = [0] * len(damaged[row])
    assert gen.self_check(damaged)


def test_retained_semantic_counterexample_replays_and_refutes_every_canonical_shortcut():
    path = HOME / "counterexamples" / "semantic_shortcuts.json"
    record = json.loads(path.read_text(encoding="utf-8"))
    generator_sha = hashlib.sha256((HOME / "generator.py").read_bytes()).hexdigest()
    assert record["generator_sha256"] == generator_sha
    assert record["rule_hash"] == gen.RULE_HASH

    replay = record["replay"]
    grid = gen.generate(
        replay["seed"],
        replay["sample_index"],
        difficulty=replay["difficulty"],
        **replay["overrides"],
    )
    assert grid == record["input"]
    assert gen.self_check(grid) == []
    intended = _oracle(grid)
    assert intended == record["intended_output"]
    assert set(record["rival_outputs"]) == set(gen.CANONICAL_SHORTCUTS)
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        observed = rival(grid)
        assert observed == record["rival_outputs"][name]
        assert observed != intended


def test_workspace_review_probe_is_source_bound_and_clean():
    probe_path = HOME / "workspace" / "review_probe.py"
    spec = importlib.util.spec_from_file_location("review_probe_83ca9df09514", probe_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load review probe from {probe_path}")
    probe = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(probe)
    report = probe.run_probe(gen, _canonical_pairs(), seeds_per_band=5)
    assert report["status"] == "pass"
    assert report["canonical_profiles_seen"] == 5
    assert report["ambiguous_rotations"] == 0
    assert report["override_failures"] == []
    assert report["shortcut_failures"] == []
