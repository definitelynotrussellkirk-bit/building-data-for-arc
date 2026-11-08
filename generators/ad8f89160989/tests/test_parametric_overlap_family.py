"""Contract, lesson, and adversarial tests for the overlap-count family."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import canonical_path, find_root, public_challenge_bytes


TASK_ID = "ad8f89160989"
SETTINGS = ({"coverage_mode": "union"}, {"coverage_mode": "overlap_highlight"})


def _root() -> Path:
    return find_root(__file__)


def _load(name: str):
    path = _root() / "generators" / TASK_ID / "workspace" / "parametric" / name
    assert path.is_file(), f"missing parametric source: {path}"
    spec = importlib.util.spec_from_file_location(f"_test_{TASK_ID}_{path.stem}", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_program() -> str:
    rows = []
    with canonical_path(_root()).open(encoding="utf-8") as stream:
        for line in stream:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                rows.append(row)
    assert len(rows) == 1
    return rows[0]["program_solution"]


def _inputs(episode: dict):
    return [pair["input"] for pair in [*episode["train"], *episode["test"]]]


def test_default_program_is_exact_canonical_and_variant_is_distinct() -> None:
    prototype = _load("prototype.py")
    assert prototype.program(SETTINGS[0]) == _canonical_program()
    assert prototype.program(SETTINGS[1]) != _canonical_program()
    assert prototype.program(SETTINGS[1]) == (
        _root() / "generators" / TASK_ID / "workspace" / "parametric" / "overlap_highlight.rkt"
    ).read_text(encoding="utf-8")
    with pytest.raises(ValueError, match="exactly"):
        prototype.program({})
    with pytest.raises(ValueError, match="coverage_mode"):
        prototype.program({"coverage_mode": "xor"})


def test_python_rule_uses_coverage_counts_not_binary_union() -> None:
    prototype = _load("prototype.py")
    grid = [[0] * 9 for _ in range(9)]
    # Coverage 4 at (4,4), coverage 2 at (1,4), and isolated coverage 1 near (7,7).
    for r, c, color in (
        (3, 4, 2), (5, 4, 3), (4, 3, 4), (4, 5, 6),
        (1, 3, 7), (1, 5, 9), (7, 7, 2),
    ):
        grid[r][c] = color
    union = prototype.apply_python(grid, SETTINGS[0])
    highlighted = prototype.apply_python(grid, SETTINGS[1])
    counts = prototype.coverage_counts(grid)
    assert counts[4][4] == 4
    assert counts[1][4] == 2
    assert counts[7][6] == 1
    assert union[4][4] == union[1][4] == union[7][6] == 8
    assert highlighted[4][4] == highlighted[1][4] == 1
    assert highlighted[7][6] == 8
    assert prototype.apply_binary_intermediate(grid) == union
    assert prototype.apply_binary_intermediate(grid) != highlighted


def test_three_demos_identify_each_setting_and_inputs_are_matched() -> None:
    prototype = _load("prototype.py")
    episodes = [prototype.generate_episode(20261026, settings, demos=3, queries=4) for settings in SETTINGS]
    assert _inputs(episodes[0]) == _inputs(episodes[1])
    for settings, episode in zip(SETTINGS, episodes):
        assert prototype.teaching_survivors(episode) == [settings]
        assert prototype.semantic_survivors(episode) == [settings["coverage_mode"]]
        assert prototype.episode_errors(episode) == []
        demo_counts = [prototype.coverage_histogram(pair["input"]) for pair in episode["train"]]
        assert any(hist.get("2", 0) for hist in demo_counts)
        assert any(hist.get("3", 0) for hist in demo_counts)
        assert any(hist.get("4", 0) for hist in demo_counts)


def test_minimum_lesson_breaks_orientation_and_color_shortcuts() -> None:
    prototype = _load("prototype.py")
    for seed in range(32):
        episode = prototype.generate_episode(seed, SETTINGS[1], demos=3, queries=4)
        opposite_same = False
        perpendicular_different = False
        for pair in episode["train"]:
            source = pair["input"]
            counts = prototype.coverage_counts(source)
            height, width = len(source), len(source[0])
            for row, count_row in enumerate(counts):
                for column, count in enumerate(count_row):
                    if count != 2 or source[row][column] != 0:
                        continue
                    neighbors = [
                        (dr, dc, source[row + dr][column + dc])
                        for dr, dc in prototype.DIRS4
                        if 0 <= row + dr < height
                        and 0 <= column + dc < width
                        and source[row + dr][column + dc] != 0
                    ]
                    vectors = {(dr, dc) for dr, dc, _ in neighbors}
                    colors = {color for _, _, color in neighbors}
                    is_opposite = vectors in ({(-1, 0), (1, 0)}, {(0, -1), (0, 1)})
                    has_vertical = any(dr != 0 for dr, _, _ in neighbors)
                    has_horizontal = any(dc != 0 for _, dc, _ in neighbors)
                    opposite_same |= is_opposite and len(colors) == 1
                    perpendicular_different |= has_vertical and has_horizontal and len(colors) == 2
        assert opposite_same, f"seed {seed} lacks same-color opposite-pair witness"
        assert perpendicular_different, f"seed {seed} lacks different-color perpendicular-pair witness"


def test_query_bank_is_prefix_stable_distinct_and_contains_substantive_30x30() -> None:
    prototype = _load("prototype.py")
    one = prototype.generate_episode(8181, SETTINGS[1], demos=3, queries=1)
    four = prototype.generate_episode(8181, SETTINGS[1], demos=3, queries=4)
    eight = prototype.generate_episode(8181, SETTINGS[1], demos=6, queries=8)
    assert one["train"] == four["train"]
    assert one["test"] == four["test"][:1]
    assert four["train"] == eight["train"][:3]
    assert four["test"] == eight["test"][:4]
    keys = {json.dumps(grid, separators=(",", ":")) for grid in _inputs(eight)}
    assert len(keys) == len(_inputs(eight))
    first_four_dims = {(len(pair["input"]), len(pair["input"][0])) for pair in four["test"]}
    assert (30, 30) in first_four_dims
    large = next(pair["input"] for pair in four["test"] if len(pair["input"]) == 30 and len(pair["input"][0]) == 30)
    seeds = [(r, c) for r, row in enumerate(large) for c, value in enumerate(row) if value]
    assert len(seeds) >= 16
    assert {r < 15 for r, _ in seeds} == {False, True}
    assert {c < 15 for _, c in seeds} == {False, True}


def test_count_boundaries_determinism_and_setting_neutral_inputs() -> None:
    prototype = _load("prototype.py")
    for demos in (3, 6):
        for queries in (1, 8):
            first = prototype.generate_episode(555, SETTINGS[0], demos=demos, queries=queries)
            second = prototype.generate_episode(555, SETTINGS[0], demos=demos, queries=queries)
            alternate = prototype.generate_episode(555, SETTINGS[1], demos=demos, queries=queries)
            assert first == second
            assert _inputs(first) == _inputs(alternate)
            assert len(first["train"]) == demos
            assert len(first["test"]) == queries
    for kwargs in (
        {"demos": 2, "queries": 4}, {"demos": 7, "queries": 4},
        {"demos": 3, "queries": 0}, {"demos": 3, "queries": 9},
    ):
        with pytest.raises(ValueError):
            prototype.generate_episode(0, SETTINGS[0], **kwargs)
    with pytest.raises(ValueError):
        prototype.generate_episode(True, SETTINGS[0], demos=3, queries=4)


def test_full_bank_places_exact_center_before_flexible_quadrants() -> None:
    prototype = _load("prototype.py")
    for seed in range(10_000, 10_032):
        episode = prototype.generate_episode(seed, SETTINGS[1], demos=6, queries=8)
        assert len(episode["train"]) == 6
        assert len(episode["test"]) == 8


def test_crossed_controls_separate_intermediate_from_nuisance_colors() -> None:
    prototype = _load("prototype.py")
    controls = prototype.crossed_controls()
    assert controls["fixed_geometry_different_intermediate"] is True
    assert controls["fixed_intermediate_different_colors"] is True
    assert controls["fixed_geometry_outputs_differ"] is True
    assert controls["fixed_intermediate_overlap_mask_equal"] is True


def test_public_first_turn_has_no_private_or_future_fields() -> None:
    prototype = _load("prototype.py")
    one = prototype.generate_episode(777, SETTINGS[1], demos=3, queries=1)
    four = prototype.generate_episode(777, SETTINGS[1], demos=3, queries=4)
    visible_one = prototype.public_turn(one, 0)
    visible_four = prototype.public_turn(four, 0)
    assert public_challenge_bytes(visible_one) == public_challenge_bytes(visible_four)
    assert set(visible_four) == {"train", "test"}
    assert len(visible_four["test"]) == 1
    assert set(visible_four["test"][0]) == {"input"}
    raw = public_challenge_bytes(visible_four)
    assert prototype.public_turn_id(four, 0) == hashlib.sha256(raw).hexdigest()
    for forbidden in (b"coverage_mode", b"program", b"query_count", b"source_index", b"answer"):
        assert forbidden not in raw
    with pytest.raises(IndexError):
        prototype.public_turn(one, 1)


def test_malformed_grids_and_episode_payloads_fail_loudly() -> None:
    prototype = _load("prototype.py")
    for bad in (
        [], [[0], [0, 0]], [[True, 0], [0, 2]], [[8, 0], [0, 2]], [[1, 0], [0, 2]],
    ):
        with pytest.raises(ValueError):
            prototype.coverage_counts(bad)
    episode = copy.deepcopy(prototype.generate_episode(9, SETTINGS[0], demos=3, queries=4))
    episode["train"][0]["input"][0][0] = 8
    errors = prototype.episode_errors(episode)
    assert any("train[0] invalid input" in error for error in errors)


def test_promotion_contract_is_native_and_bounded() -> None:
    path = _root() / "generators" / TASK_ID / "workspace" / "parametric" / "promotion.json"
    contract = json.loads(path.read_text(encoding="utf-8"))
    assert contract == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": f"generators/{TASK_ID}/workspace/parametric/adapter.py",
        "parameters": {"coverage_mode": ["union", "overlap_highlight"]},
        "default": {"coverage_mode": "union"},
        "limits": {"demos": [3, 6], "queries": [1, 8]},
        "qualification_demos": 3,
        "resources": [
            f"generators/{TASK_ID}/workspace/parametric/prototype.py",
            f"generators/{TASK_ID}/workspace/parametric/overlap_highlight.rkt",
        ],
    }
