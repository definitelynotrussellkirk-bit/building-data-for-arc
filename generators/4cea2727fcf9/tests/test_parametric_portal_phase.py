"""Focused tests for the repaired base and portal-phase parametric family."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pytest

from reviewer_support import find_root, load_selected_generator

ROOT = find_root(__file__)
TASK = "4cea2727fcf9"
HOME = ROOT / f"generators/{TASK}/workspace/parametric"
PROTOTYPE_PATH = HOME / "prototype.py"
ADAPTER_PATH = HOME / "adapter.py"
CONTRACT_PATH = HOME / "promotion.json"
PROBE_PATH = HOME / "adversarial_probe.py"
CANONICAL_PATH = HOME / "canonical.rkt"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_task_local_parametric_artifacts_are_present():
    for path in (PROTOTYPE_PATH, ADAPTER_PATH, CONTRACT_PATH, PROBE_PATH, CANONICAL_PATH):
        assert path.is_file(), f"missing task-local artifact: {path.name}"


@pytest.fixture(scope="module")
def prototype():
    return _load("parametric_4cea2727fcf9", PROTOTYPE_PATH)


@pytest.fixture(scope="module")
def adapter():
    return _load("parametric_4cea2727fcf9_adapter", ADAPTER_PATH)


@pytest.fixture(scope="module")
def probe():
    return _load("parametric_4cea2727fcf9_probe", PROBE_PATH)


@pytest.fixture(scope="module")
def racket_bridge(prototype):
    with prototype.RacketBridge() as bridge:
        yield bridge


def test_base_repairs_rule_binding_axes_and_causal_generation(prototype):
    generator, source, digest = load_selected_generator(TASK, root=ROOT)
    assert source.name == "generator.py" and len(digest) == 64
    assert generator.RULE_HASH == "fbb3bae580b8"
    assert set(generator.AXES) == {"grid_h", "grid_w", "n_walls"}
    assert "palette_kind" not in generator.AXES
    assert "palette_size" not in generator.AXES
    assert "n_distinct_colors" not in generator.AXES

    # Consecutive sample indices must teach both portal-present and portal-absent
    # cases, and every portal-present draw must causally use teleportation.
    for difficulty in (None, "easy", "medium", "hard"):
        grids = [generator.generate(31, i, difficulty=difficulty) for i in range(6)]
        assert [sum(cell == 4 for row in grid for cell in row) for grid in grids] == [0, 2, 0, 2, 0, 2]
        for grid in grids:
            assert generator.self_check(grid, difficulty=difficulty) == []
            canonical = generator.rule_mirror(grid)
            assert canonical != grid
            assert canonical != generator._rival_ignore_checkpoint(grid)
            if sum(cell == 4 for row in grid for cell in row) == 2:
                assert canonical != generator._rival_ignore_portals(grid)


def test_programs_preserve_exact_canonical_default_and_guard_phase_patch(prototype):
    canonical = prototype.canonical_source(root=ROOT)
    assert hashlib.sha256(canonical.encode()).hexdigest() == (
        "fbb3bae580b8bd2c900b133fd211e8cfd4ce40a8dcc3a1e83ccf8823fea3a9d3"
    )
    assert prototype.program_for("always", root=ROOT) == canonical
    before = prototype.program_for("before_checkpoint", root=ROOT)
    after = prototype.program_for("after_checkpoint", root=ROOT)
    assert before != canonical and after != canonical and before != after
    assert "(if (not got) (portal-exit (list nr nc)) (list nr nc))" in before
    assert "(if got (portal-exit (list nr nc)) (list nr nc))" in after
    for bad in ("never", "before", "", 0, True, None):
        with pytest.raises(ValueError, match="portal_phase"):
            prototype.program_for(bad, root=ROOT)


def test_two_demos_identify_each_setting_with_protected_racket(prototype, racket_bridge):
    programs = {mode: prototype.program_for(mode, root=ROOT) for mode in prototype.ALLOWED_PHASES}
    for chosen in prototype.ALLOWED_PHASES:
        episode = prototype.make_episode(
            17, portal_phase=chosen, demos=2, queries=4, root=ROOT
        )
        survivors = []
        for rival, program in programs.items():
            actual = [prototype.execute_rule(program, p["input"], bridge=racket_bridge) for p in episode["train"]]
            if actual == [p["output"] for p in episode["train"]]:
                survivors.append(rival)
        assert survivors == [chosen]
        for pair in episode["train"] + episode["test"]:
            assert prototype.execute_rule(programs[chosen], pair["input"], bridge=racket_bridge) == pair["output"]
            assert prototype.python_mirror(pair["input"], portal_phase=chosen) == pair["output"]


def test_episode_inputs_are_matched_deterministic_and_queries_are_distinct(prototype):
    episodes = {
        phase: prototype.make_episode(29, portal_phase=phase, demos=6, queries=4, root=ROOT)
        for phase in prototype.ALLOWED_PHASES
    }
    assert episodes["always"] == prototype.make_episode(
        29, portal_phase="always", demos=6, queries=4, root=ROOT
    )
    reference_inputs = [
        pair["input"] for pair in episodes["always"]["train"] + episodes["always"]["test"]
    ]
    for phase, episode in episodes.items():
        assert episode["parameters"] == {"portal_phase": phase}
        assert episode["selection_scope"] == "once_per_episode"
        assert [pair["input"] for pair in episode["train"] + episode["test"]] == reference_inputs
        assert len({prototype.grid_sha256(pair["input"]) for pair in episode["test"]}) == 4
        assert episode["ambiguities"] == []
        assert all(row["demonstration_mismatch_indices"] for row in episode["parameter_rivals"])


def test_adapter_count_bounds_strict_settings_and_no_racket_in_generate(prototype, adapter, monkeypatch):
    contract = json.loads(CONTRACT_PATH.read_text())
    assert contract == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": "generators/4cea2727fcf9/workspace/parametric/adapter.py",
        "parameters": {
            "portal_phase": ["always", "before_checkpoint", "after_checkpoint"]
        },
        "default": {"portal_phase": "always"},
        "limits": {"demos": [2, 6], "queries": [4, 4]},
        "qualification_demos": 2,
        "resources": ["generators/4cea2727fcf9/workspace/parametric/canonical.rkt"],
    }
    assert adapter.program({"portal_phase": "always"}) == prototype.canonical_source(root=ROOT)
    for demos in (2, 3, 6):
        claims = adapter.generate(41, {"portal_phase": "before_checkpoint"}, demos, 4)
        assert set(claims) == {"train", "test", "program_solution"}
        assert len(claims["train"]) == demos and len(claims["test"]) == 4
    for demos in (1, 7, True):
        with pytest.raises(ValueError, match="demos"):
            adapter.generate(41, {"portal_phase": "always"}, demos, 4)
    for queries in (0, 3, 5, True):
        with pytest.raises(ValueError, match="queries"):
            adapter.generate(41, {"portal_phase": "always"}, 2, queries)
    for settings in ({}, {"portal_phase": "never"}, {"portal_phase": "always", "x": 1}):
        with pytest.raises(ValueError):
            adapter.program(settings)

    monkeypatch.setattr(
        adapter.prototype,
        "RacketBridge",
        lambda: pytest.fail("adapter.generate must leave Racket replay to the protected worker"),
    )
    adapter.generate(43, {"portal_phase": "after_checkpoint"}, 2, 4)


def test_last_query_is_substantive_30_by_30_stress(prototype):
    episode = prototype.make_episode(53, portal_phase="always", demos=2, queries=4, root=ROOT)
    grid = episode["test"][-1]["input"]
    assert (len(grid), len(grid[0])) == (30, 30)
    walls = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 8]
    assert len(walls) >= 90
    assert len({r for r, _ in walls}) >= 20
    assert len({c for _, c in walls}) >= 20
    assert any(r in (0, 29) for r, _ in walls)
    assert any(c in (0, 29) for _, c in walls)
    outputs = {
        phase: prototype.python_mirror(grid, portal_phase=phase)
        for phase in prototype.ALLOWED_PHASES
    }
    assert len({prototype.grid_sha256(value) for value in outputs.values()}) >= 2


def test_public_and_first_turn_projection_hide_private_and_future_data(prototype):
    episode = prototype.make_episode(59, portal_phase="after_checkpoint", demos=3, queries=4, root=ROOT)
    public = prototype.public_challenge(episode)
    assert set(public) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])

    public_id = prototype.public_id(episode)
    changed = copy.deepcopy(episode)
    changed["program"] = "private replacement"
    changed["parameters"]["portal_phase"] = "always"
    changed["test"][0]["output"][0][0] ^= 1
    assert prototype.public_id(changed) == public_id

    first = prototype.first_turn_bytes(episode)
    future = copy.deepcopy(episode)
    future["test"][1]["input"][0][0] ^= 1
    future["test"][3]["output"][0][0] ^= 1
    future["program"] = "different private program"
    assert prototype.first_turn_bytes(future) == first
    visible = copy.deepcopy(episode)
    visible["test"][0]["input"][0][0] ^= 1
    assert prototype.first_turn_bytes(visible) != first


def test_bounded_adversarial_probe_attacks_shortcuts_counts_and_exports(probe, racket_bridge):
    report = probe.run_probe(seeds=[0, 1], demo_counts=[2, 6], bridge=racket_bridge)
    assert report["status"] == "pass"
    assert report["phases"] == ["always", "before_checkpoint", "after_checkpoint"]
    assert report["episodes_checked"] == 12
    assert report["queries_per_episode"] == 4
    assert report["max_input_shape"] == [30, 30]
    assert report["shortcut_survivors"] == {}
    assert report["first_turn_invariance_checks"] >= 12


def test_base_semantic_witnesses_are_all_causal():
    generator, _, _ = load_selected_generator(TASK, root=ROOT)
    assert set(generator.SEMANTIC_WITNESSES) == {
        "portal_changes_output",
        "checkpoint_changes_output",
    }
    assert set(generator.WITNESS_RIVALS) == set(generator.SEMANTIC_WITNESSES)
