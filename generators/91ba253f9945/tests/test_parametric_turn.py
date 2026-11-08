"""Focused behavior tests for the repaired local-frame quarter-turn family."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import (
    canonical_pairs,
    canonical_path,
    find_root,
    public_challenge_bytes,
)

TASK_ID = "91ba253f9945"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK_ID
PARAMETRIC = HOME / "workspace" / "parametric"
PROTOTYPE = PARAMETRIC / "prototype.py"
ADAPTER = PARAMETRIC / "adapter.py"
CONTRACT = PARAMETRIC / "promotion.json"
PROBE = PARAMETRIC / "adversarial_probe.py"
SAMPLER_AUDIT = PARAMETRIC / "sampler_audit.py"
GENERATOR = HOME / "generator.py"


def _load(name: str, path: Path):
    assert path.is_file(), f"missing artifact: {path}"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def generator():
    return _load("generator_91ba253f9945", GENERATOR)


@pytest.fixture(scope="module")
def prototype():
    return _load("parametric_91ba253f9945", PROTOTYPE)


@pytest.fixture(scope="module")
def adapter():
    return _load("adapter_91ba253f9945", ADAPTER)


@pytest.fixture(scope="module")
def probe():
    return _load("probe_91ba253f9945", PROBE)


def _canonical_program() -> str:
    rows = [json.loads(line) for line in canonical_path(ROOT).read_text().splitlines()]
    programs = {row["program_solution"] for row in rows if row.get("task_id") == TASK_ID}
    assert len(programs) == 1
    return next(iter(programs))


def _all_inputs(episode):
    return [pair["input"] for split in ("train", "test") for pair in episode[split]]


def _quadrants(grid):
    h, w = len(grid), len(grid[0])
    occupied = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value}
    return [
        sum((r, c) in occupied for r in rr for c in cc)
        for rr in (range(0, h // 2), range(h // 2, h))
        for cc in (range(0, w // 2), range(w // 2, w))
    ]


def test_required_parametric_artifacts_exist():
    for path in (PROTOTYPE, ADAPTER, CONTRACT, PROBE, SAMPLER_AUDIT):
        assert path.is_file()


def test_base_generator_now_samples_the_coordinate_frame_domain(generator):
    for difficulty in (None, "easy", "medium", "hard"):
        for seed in range(4):
            grid = generator.generate(seed, 0, difficulty=difficulty)
            assert generator.self_check(grid, difficulty=difficulty) == []
            colors = {value for row in grid for value in row}
            assert {2, 3, 4, 5, 6, 7, 8, 9} <= colors
            assert len(grid) <= 30 and len(grid[0]) <= 30

    stress = generator.generate(
        91,
        0,
        difficulty="hard",
        grid_h=30,
        grid_w=30,
        marker_count=6,
        decoy_count=10,
    )
    assert generator.self_check(stress, difficulty="hard") == []
    assert (len(stress), len(stress[0])) == (30, 30)
    assert all(count > 0 for count in _quadrants(stress))


def test_python_mirror_matches_every_original_canonical_label(prototype):
    for pair in canonical_pairs(TASK_ID, root=ROOT, labeled_only=True):
        assert prototype.apply_rule(pair["input"], "counterclockwise") == pair["output"]


def test_default_program_is_exact_canonical_and_alternate_is_one_turn_change(prototype, adapter):
    canonical = _canonical_program()
    assert prototype.program({"turn": "counterclockwise"}) == canonical
    assert adapter.program({"turn": "counterclockwise"}) == canonical

    clockwise = prototype.program({"turn": "clockwise"})
    assert clockwise == adapter.program({"turn": "clockwise"})
    assert clockwise != canonical
    assert canonical.count("(gpos tgt (- (second p)) (first p))") == 1
    assert clockwise.count("(gpos tgt (second p) (- (first p)))") == 1
    assert hashlib.sha256(clockwise.encode()).hexdigest() != hashlib.sha256(canonical.encode()).hexdigest()


def test_matched_inputs_counts_distinctness_and_first_turn_stability(prototype):
    for demos in (2, 3, 6):
        left = prototype.generate(17, {"turn": "counterclockwise"}, demos, 4)
        right = prototype.generate(17, {"turn": "clockwise"}, demos, 4)
        assert _all_inputs(left) == _all_inputs(right)
        assert len(left["train"]) == demos and len(left["test"]) == 4
        encoded = [json.dumps(grid, separators=(",", ":")) for grid in _all_inputs(left)]
        assert len(encoded) == len(set(encoded))
        assert all(
            a["output"] != b["output"]
            for split in ("train", "test")
            for a, b in zip(left[split], right[split])
        )

    full = prototype.generate(29, {"turn": "clockwise"}, 3, 4)
    one = prototype.generate(29, {"turn": "clockwise"}, 3, 1)
    assert full["train"] == one["train"]
    assert full["test"][0] == one["test"][0]
    assert public_challenge_bytes(
        {"train": full["train"], "test": [{"input": full["test"][0]["input"]}]}
    ) == public_challenge_bytes(one)


def test_marker_motifs_are_novel_within_episodes_and_diverse_across_seeds(prototype):
    seen = set()
    for seed in range(16):
        episode = prototype.generate(seed, {"turn": "counterclockwise"}, 6, 4)
        intermediates = [
            prototype.extract_intermediate(pair["input"])
            for split in ("train", "test")
            for pair in episode[split]
        ]
        assert len(intermediates) == 10
        assert len(set(intermediates)) == 10
        seen.update(intermediates)
    assert len(seen) >= 150


def test_all_claim_labels_match_python_rule_and_last_query_is_substantive_30_square(prototype):
    for turn in prototype.TURNS:
        episode = prototype.generate(41, {"turn": turn}, 2, 4)
        for split in ("train", "test"):
            for pair in episode[split]:
                assert pair["output"] == prototype.apply_rule(pair["input"], turn)
        large = episode["test"][-1]["input"]
        assert (len(large), len(large[0])) == (30, 30)
        assert sum(value != 0 for row in large for value in row) >= 35
        assert all(count > 0 for count in _quadrants(large))
        assert any(large[0][c] for c in range(30))
        assert any(large[29][c] for c in range(30))
        assert any(large[r][0] for r in range(30))
        assert any(large[r][29] for r in range(30))


def test_public_projection_hides_settings_program_answers_and_future_queries(prototype):
    episode = prototype.generate(53, {"turn": "clockwise"}, 3, 4)
    first = {"train": episode["train"], "test": [{"input": episode["test"][0]["input"]}]}
    raw = public_challenge_bytes(first)
    assert b"clockwise" not in raw and b"program" not in raw and b"output" not in json.dumps(first["test"]).encode()

    private_change = copy.deepcopy(episode)
    private_change["program_solution"] = "private replacement"
    private_change["test"][0]["output"][0][0] ^= 1
    private_change["test"][2]["input"][0][0] ^= 1
    changed = {"train": private_change["train"], "test": [{"input": private_change["test"][0]["input"]}]}
    assert public_challenge_bytes(changed) == raw

    visible_change = copy.deepcopy(first)
    visible_change["test"][0]["input"][0][0] ^= 1
    assert public_challenge_bytes(visible_change) != raw


def test_contract_and_adapter_reject_malformed_requests(adapter):
    contract = json.loads(CONTRACT.read_text())
    assert contract == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": "generators/91ba253f9945/workspace/parametric/adapter.py",
        "parameters": {"turn": ["counterclockwise", "clockwise"]},
        "default": {"turn": "counterclockwise"},
        "limits": {"demos": [2, 6], "queries": [1, 4]},
        "resources": [
            "generators/91ba253f9945/workspace/parametric/prototype.py",
            "generators/91ba253f9945/workspace/parametric/adversarial_probe.py",
            "generators/91ba253f9945/workspace/parametric/sampler_audit.py",
        ],
    }
    for settings in ({}, {"turn": "left"}, {"turn": "clockwise", "extra": 1}, None):
        with pytest.raises((TypeError, ValueError)):
            adapter.program(settings)
    for demos in (1, 7, True, 2.0):
        with pytest.raises((TypeError, ValueError)):
            adapter.generate(0, {"turn": "clockwise"}, demos, 4)
    for queries in (0, 5, True, 4.0):
        with pytest.raises((TypeError, ValueError)):
            adapter.generate(0, {"turn": "clockwise"}, 3, queries)
    for seed in (-1, True, 1.0):
        with pytest.raises((TypeError, ValueError)):
            adapter.generate(seed, {"turn": "clockwise"}, 3, 4)


def test_deep_adversarial_probe_refutes_declared_shortcuts(probe):
    report = probe.run(seeds=(0, 17, 41, 91), demo_counts=(2, 6))
    assert report["status"] == "passed"
    assert report["episodes"] == 16
    assert report["remaining_demo_shortcuts"] == []
    assert report["remaining_query_shortcuts"] == []
    assert "legacy_six_motif_lookup" in report["rivals"]
    assert report["motif_diversity"]["episode_reuse_failures"] == []
    assert report["motif_diversity"]["unique_marker_motifs"] >= 40
    assert report["crossed_controls"]["intermediate_varies_at_fixed_profile"] is True
    assert report["crossed_controls"]["profiles_vary_at_fixed_intermediate"] is True
    assert report["boundaries"] == {
        "minimum_demos": 2,
        "maximum_demos": 6,
        "minimum_query_shape": [11, 15],
        "maximum_query_shape": [30, 30],
    }


def test_probe_rejects_episode_specific_fixed_motif_shortcut(probe):
    report = probe.run(seeds=(0, 17), demo_counts=(2,))
    assert "reuse_first_demo_intermediate" in report["rivals"]
    assert report["ambiguous_episode_shortcuts"] == []
    assert report["episode_shortcut_checks"] == 4 * len(report["rivals"])
