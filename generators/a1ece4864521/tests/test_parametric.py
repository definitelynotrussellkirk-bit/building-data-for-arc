from __future__ import annotations

import copy
import importlib.util
from pathlib import Path

import pytest

HOME = Path(__file__).resolve().parents[1]
PARAM = HOME / "workspace" / "parametric"
SPEC = importlib.util.spec_from_file_location("parametric_a1ece4864521_under_test", PARAM / "prototype.py")
assert SPEC is not None and SPEC.loader is not None
prototype = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(prototype)


def _frozen(grid):
    return tuple(tuple(row) for row in grid)


def test_programs_and_default_are_distinct_and_exact_files():
    canonical = (PARAM / "canonical.rkt").read_text(encoding="utf-8")
    phase = (PARAM / "phase_diagonal.rkt").read_text(encoding="utf-8")
    assert prototype.program({"fill_route": "below_right"}) == canonical
    assert prototype.program({"fill_route": "phase_diagonal"}) == phase
    assert canonical != phase


def test_counts_are_independent_inputs_match_settings_and_query_prefix_is_stable():
    for seed in range(5):
        for demos in (2, 3, 6):
            canonical = prototype.generate(seed, {"fill_route": "below_right"}, demos, 4)
            phase = prototype.generate(seed, {"fill_route": "phase_diagonal"}, demos, 4)
            assert [p["input"] for p in canonical["train"]] == [p["input"] for p in phase["train"]]
            assert [p["input"] for p in canonical["test"]] == [p["input"] for p in phase["test"]]
            assert len(canonical["train"]) == demos
            assert len(canonical["test"]) == 4
            all_inputs = [p["input"] for p in canonical["train"] + canonical["test"]]
            assert len({_frozen(grid) for grid in all_inputs}) == demos + 4
            one = prototype.generate(seed, {"fill_route": "below_right"}, demos, 1)
            assert one["test"][0] == canonical["test"][0]


def test_minimum_two_demos_identify_setting_and_refute_declared_shortcuts():
    for seed in range(12):
        for settings in prototype.SETTINGS:
            episode = prototype.generate(seed, settings, 2, 4)
            assert prototype.setting_survivors(episode["train"]) == [settings]
            assert prototype.rival_survivors(episode["train"], settings) == []


def test_two_demo_lesson_crosses_phase_with_anomaly_type_and_tiles_vary():
    tiles = set()
    for seed in range(16):
        episode = prototype.generate(seed, {"fill_route": "phase_diagonal"}, 2, 4)
        combos = set()
        for pair in episode["train"]:
            facts = prototype.analyze_scene(pair["input"])
            assert facts["errors"] == []
            tiles.add(tuple(tuple(row) for row in facts["tile"]))
            combos.update((expected, value in (0, 8)) for _r, _c, value, expected in facts["anomalies"])
        assert combos == {(0, False), (0, True), (8, False), (8, True)}
    assert len(tiles) >= 12


def test_query_bank_covers_minimum_and_substantive_30x30_after_private_shuffle():
    for seed in range(8):
        episode = prototype.generate(seed, {"fill_route": "phase_diagonal"}, 2, 4)
        shapes = {(len(p["input"]), len(p["input"][0])) for p in episode["test"]}
        assert (10, 10) in shapes
        assert (30, 30) in shapes
        stress = next(p["input"] for p in episode["test"] if len(p["input"]) == 30 and len(p["input"][0]) == 30)
        facts = prototype.analyze_scene(stress)
        assert len(facts["anomalies"]) >= 6
        assert 6 <= facts["zero_count"] <= 19


def test_episode_validator_rejects_forgery_duplicates_and_boolean_cells():
    settings = {"fill_route": "phase_diagonal"}
    episode = prototype.generate(7, settings, 2, 4)
    prototype.validate_episode(episode, settings=settings, demos=2, queries=4)

    forged = copy.deepcopy(episode)
    forged["test"][0]["output"][0][0] = (forged["test"][0]["output"][0][0] + 1) % 10
    with pytest.raises(ValueError, match="label"):
        prototype.validate_episode(forged, settings=settings, demos=2, queries=4)

    duplicate = copy.deepcopy(episode)
    duplicate["test"][0]["input"] = copy.deepcopy(duplicate["train"][0]["input"])
    with pytest.raises(ValueError, match="duplicate"):
        prototype.validate_episode(duplicate, settings=settings, demos=2, queries=4)

    boolean = copy.deepcopy(episode)
    boolean["train"][0]["input"][0][0] = True
    with pytest.raises(ValueError, match="exact ARC integers"):
        prototype.validate_episode(boolean, settings=settings, demos=2, queries=4)


def test_invalid_scalar_and_setting_types_fail_loudly():
    with pytest.raises(ValueError):
        prototype.generate(True, {"fill_route": "below_right"}, 2, 4)
    with pytest.raises(ValueError):
        prototype.generate(0, {"fill_route": "below_right"}, True, 4)
    with pytest.raises(ValueError):
        prototype.generate(0, {"fill_route": "diagonal"}, 2, 4)


def test_adversarial_probe_bounds_bridge_state_and_scales_smoke_threshold():
    spec = importlib.util.spec_from_file_location(
        "parametric_a1ece4864521_probe_under_test", PARAM / "adversarial_probe.py"
    )
    assert spec is not None and spec.loader is not None
    probe = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(probe)
    assert 1 <= probe.RACKET_RESTART_INTERVAL <= 32
    assert probe.minimum_tile_diversity(seed_count=1) == 2
    assert probe.minimum_tile_diversity(seed_count=4) == 8


def test_adversarial_probe_caches_duplicate_program_input_evaluations(monkeypatch):
    spec = importlib.util.spec_from_file_location(
        "parametric_a1ece4864521_probe_cache_under_test", PARAM / "adversarial_probe.py"
    )
    assert spec is not None and spec.loader is not None
    probe = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(probe)

    class FakeBridge:
        def __init__(self, **_kwargs):
            self.runtime_identity = {
                "schema": "fake",
                "backend": "racket",
                "protected": True,
            }
            self.calls = 0
            self._restarts = 0

        def eval_text(self, _text):
            self.calls += 1
            return [[0, 0, 0, 0, 0] for _ in range(5)]

        def close(self):
            return None

    monkeypatch.setattr(probe, "RacketBridge", FakeBridge)
    evaluator = probe.ProtectedEvaluator()
    program = "(rule! (lambda (g) g))"
    grid = [[0, 0, 0, 0, 0] for _ in range(5)]
    assert evaluator.apply(program, grid) == grid
    assert evaluator.apply(program, grid) == grid
    assert evaluator.bridge.calls == 1
    assert evaluator.evaluations == 1
    assert evaluator.cache_hits == 1
