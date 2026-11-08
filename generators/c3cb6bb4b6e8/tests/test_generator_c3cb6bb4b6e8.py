from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
from pathlib import Path

import pytest

from puzzle_generators import base as gen_base
from puzzle_generators.runner import _apply_rule, _load_bundle, _open_bridge_with_rule
from scripts.canonical_profile_gate import canonical_pairs

GEN = importlib.import_module(
    "puzzle_generators.per_puzzle.c3cb6bb4b6e8.generator"
)
TASK_ID = "c3cb6bb4b6e8"
ROOT = Path(__file__).resolve().parents[1]


def _normalized_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def _canonical_rule() -> str:
    for line in (ROOT / "data/canonical/puzzles.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row["program_solution"]
    raise AssertionError("canonical rule not found")


def _bridge():
    bundle = _load_bundle(TASK_ID)
    return _open_bridge_with_rule(bundle.rule_callable_text)


def test_metadata_hash_and_rule_statement_are_pinned():
    assert GEN.GENERATOR_ID == TASK_ID
    assert GEN.TASK_ID == TASK_ID
    assert GEN.VERSION == "2.0.0"
    assert GEN.RULE_HASH == _normalized_hash(_canonical_rule()) == "514be61a9f3b"
    assert "connected component" in GEN.SUMMARY
    assert "Touching frame borders" in GEN.SUMMARY


def test_all_canonical_pairs_self_check_mirror_and_racket_exactness():
    pairs = canonical_pairs(TASK_ID)
    assert len(pairs) == 6
    bridge, fn_name = _bridge()
    try:
        active_counts = []
        for pair in pairs:
            source = copy.deepcopy(pair["input"])
            before = copy.deepcopy(source)
            assert GEN.self_check(source) == []
            expected = GEN.rule_mirror(source)
            actual = _apply_rule(bridge, fn_name, source)
            assert actual == expected == pair["output"]
            assert source == before
            active_counts.append(len(GEN._analyze(source)["active_frames"]))
        # This is the selected-oracle discriminator: merged gray borders are
        # accepted authority inputs but are not rectangular frame objects.
        assert active_counts == [0, 2, 0, 0, 2, 1]
        a, b = pairs[1]["input"], pairs[4]["input"]
        assert _apply_rule(bridge, fn_name, a) == pairs[1]["output"]
        assert _apply_rule(bridge, fn_name, b) == pairs[4]["output"]
        assert _apply_rule(bridge, fn_name, a) == pairs[1]["output"]
    finally:
        bridge.shutdown()


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_distribution_is_lawful_observable_and_strictly_anchored(band):
    strict = 0
    seen = set()
    for sample_index in range(80):
        contexts = []
        gen_base.set_ctx_observer(contexts.append)
        try:
            grid = GEN.generate(71_000 + sample_index, sample_index, difficulty=band)
        finally:
            gen_base.set_ctx_observer(None)
        assert GEN.self_check(grid) == []
        analysis = GEN._analyze(grid)
        if sample_index % 3 == 0:
            assert len(analysis["active_frames"]) < analysis["n_frames"]
        else:
            assert len(analysis["active_frames"]) == analysis["n_frames"]
            assert analysis["gray_component_count"] == analysis["n_frames"]
        observed = GEN.observe_overrides(grid)
        assert contexts
        draws = contexts[-1].recorded_draws()
        assert {name: draws[name] for name in GEN.AXES} == observed
        strict += not GEN.strict_canonical_like(grid)
        seen.add(json.dumps(grid, separators=(",", ":")))
    assert strict == 54
    assert len(seen) >= 70


@pytest.mark.parametrize(
    "overrides",
    [
        {"grid_h": 15},
        {"grid_h": 18},
        {"grid_w": 15},
        {"grid_w": 20},
        {"n_frames": 2},
        {"n_frames": 3},
        {"template_cells": 3},
        {"template_cells": 5},
        {"grid_h": 15, "grid_w": 15, "n_frames": 3, "template_cells": 5},
        {"grid_h": 18, "grid_w": 20, "n_frames": 2, "template_cells": 3},
    ],
)
def test_exact_override_boundaries_are_observable(overrides):
    grid = GEN.generate(123_456, 7, difficulty="medium", **overrides)
    assert GEN.self_check(grid) == []
    observed = GEN.observe_overrides(grid)
    for name, requested in overrides.items():
        assert observed[name] == requested


def test_unknown_and_out_of_range_overrides_reject_loudly():
    with pytest.raises(TypeError):
        GEN.generate(1, 0, unknown_axis=1)
    with pytest.raises(ValueError):
        GEN.generate(1, 0, grid_h=14)
    with pytest.raises(ValueError):
        GEN.generate(1, 0, grid_w=21)
    with pytest.raises(ValueError):
        GEN.generate(1, 0, n_frames=4)
    with pytest.raises(ValueError):
        GEN.generate(1, 0, template_cells=2)


def test_self_check_rejects_targeted_structural_impostors():
    source = GEN.generate(8080, 5, difficulty="hard")
    analysis = GEN._analyze(source)
    mutations = {}

    broken_border = copy.deepcopy(source)
    r, c = min(analysis["frames"][0]["border"])
    broken_border[r][c] = 0
    mutations["broken_border"] = broken_border

    duplicate_key = copy.deepcopy(source)
    frame = analysis["frames"][0]
    key_pos = frame["key"][:2]
    slot = next(p for p in frame["interior"] if p != key_pos and duplicate_key[p[0]][p[1]] == 0)
    duplicate_key[slot[0]][slot[1]] = 2 if frame["key"][2] != 2 else 3
    mutations["duplicate_key"] = duplicate_key

    split_template = copy.deepcopy(source)
    template = list(analysis["template"])
    split_template[template[-1][0]][template[-1][1]] = 0
    occupied = {(r, c) for r, row in enumerate(split_template) for c, v in enumerate(row) if v}
    isolated = next(
        (r, c)
        for r in range(len(split_template))
        for c in range(len(split_template[0]))
        if (r, c) not in occupied
        and all((r + dr, c + dc) not in occupied for dr, dc in GEN._CARDINAL)
    )
    split_template[isolated[0]][isolated[1]] = 1
    mutations["split_template"] = split_template

    stray_gray = copy.deepcopy(source)
    forbidden = set().union(*(f["border"] | set(f["interior"]) for f in analysis["frames"]))
    stray = next(
        (r, c)
        for r, row in enumerate(stray_gray)
        for c, v in enumerate(row)
        if v == 0 and (r, c) not in forbidden
    )
    stray_gray[stray[0]][stray[1]] = 7
    mutations["stray_gray"] = stray_gray

    bad_palette = copy.deepcopy(source)
    bad_palette[analysis["template"][0][0]][analysis["template"][0][1]] = 9
    mutations["bad_palette"] = bad_palette

    for name, grid in mutations.items():
        assert GEN.self_check(grid), name


def test_python_determinism_fresh_returns_and_global_rng_purity():
    random.seed(4444)
    before = random.getstate()
    first = GEN.generate(987_654, 11, difficulty="medium")
    middle = random.getstate()
    second = GEN.generate(987_654, 11, difficulty="medium")
    after = random.getstate()
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    assert before == middle == after
    first[0][0] = 9
    assert second[0][0] != 9


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_three_demo_sliding_window_identifies_query_rule(band):
    seed = 600_000
    for start in range(32):
        lesson = []
        for index in range(start, start + GEN.EXAMPLES_NEEDED + 1):
            grid = GEN.generate(seed, index, difficulty=band)
            lesson.append({"input": grid, "output": GEN.rule_mirror(grid)})
        assert GEN.lesson_identifiable(lesson[:-1], lesson[-1]) == []


def test_negative_recombination_rejected_while_oracle_executes():
    grid = GEN.generate(30303, 7, difficulty="hard")
    analysis = GEN._analyze(grid)
    malformed = copy.deepcopy(grid)
    # Replace a complete frame border with color 6, which is absent from every
    # remaining scene part. This is outside the teaching grammar, while the
    # oracle can still execute the residual scene without crashing.
    for row, col in analysis["frames"][0]["border"]:
        malformed[row][col] = 6
    assert 6 not in {v for row in grid for v in row}
    assert GEN.self_check(malformed)
    bridge, fn_name = _bridge()
    try:
        result = _apply_rule(bridge, fn_name, malformed)
    finally:
        bridge.shutdown()
    assert len(result) == len(malformed)
    assert len(result[0]) == len(malformed[0])
