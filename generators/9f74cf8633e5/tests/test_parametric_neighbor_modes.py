from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path

import pytest

TASK_ID = "9f74cf8633e5"
HOME = Path(__file__).resolve().parents[1]
ROOT = HOME.parents[1]
PROTOTYPE_PATH = HOME / "workspace" / "parametric" / "prototype.py"
ADAPTER_PATH = HOME / "workspace" / "parametric" / "adapter.py"


def _load(path: Path, name: str):
    assert path.is_file(), f"missing source: {path}"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def prototype():
    return _load(PROTOTYPE_PATH, "_task_9f74_parametric_test")


def adapter():
    return _load(ADAPTER_PATH, "_task_9f74_adapter_test")


def canonical_program() -> str:
    from arcpuzzles.catalog import Catalog

    record = Catalog(ROOT).get(TASK_ID)
    programs = {
        variant["program_solution"]
        for variant in record["variants"]
        if isinstance(variant.get("program_solution"), str)
    }
    assert len(programs) == 1
    return next(iter(programs))


def _racket_literal(grid):
    return "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"


@pytest.fixture(scope="module")
def racket_apply():
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    with RacketBridge() as bridge:
        assert bridge.runtime_identity["backend"] == "racket"
        assert bridge.runtime_identity["protected"] is True

        def apply(program, grid):
            return bridge.eval_text(f"({wrap_rule(program)} {_racket_literal(grid)})")

        yield apply


def test_default_program_is_exact_canonical_authority():
    module = prototype()
    assert module.program({"neighbor_mode": "diagonal"}) == canonical_program()
    assert adapter().program({"neighbor_mode": "diagonal"}) == canonical_program()


def test_generation_is_count_independent_prefix_stable_and_setting_matched():
    module = prototype()
    diagonal = module.generate(17, {"neighbor_mode": "diagonal"}, demos=6, queries=4)
    orthogonal = module.generate(17, {"neighbor_mode": "orthogonal"}, demos=6, queries=4)
    assert [pair["input"] for pair in diagonal["train"] + diagonal["test"]] == [
        pair["input"] for pair in orthogonal["train"] + orthogonal["test"]
    ]
    short = module.generate(17, {"neighbor_mode": "diagonal"}, demos=2, queries=1)
    assert short["train"] == diagonal["train"][:2]
    assert short["test"] == diagonal["test"][:1]
    inputs = [json.dumps(pair["input"]) for pair in diagonal["train"] + diagonal["test"]]
    assert len(inputs) == len(set(inputs))


def test_two_demonstrations_identify_both_settings_and_every_scene_disagrees():
    module = prototype()
    for seed in (0, 17, 91):
        for setting in module.SETTINGS:
            episode = module.generate(seed, setting, demos=2, queries=4)
            assert module.fit_settings(episode["train"]) == [setting]
            for pair in episode["train"] + episode["test"]:
                analysis = module.analyze(pair["input"])
                assert len(analysis["diagonal"]) >= 2
                assert len(analysis["orthogonal"]) >= 2
                assert analysis["negative_controls"] >= 2
                assert module.transform(pair["input"], {"neighbor_mode": "diagonal"}) != module.transform(
                    pair["input"], {"neighbor_mode": "orthogonal"}
                )
                assert module.transform(pair["input"], setting) == pair["output"]


def test_four_query_bank_contains_substantive_30_by_30_stress():
    module = prototype()
    episode = module.generate(23, {"neighbor_mode": "orthogonal"}, demos=3, queries=4)
    large = [pair for pair in episode["test"] if len(pair["input"]) == 30 and len(pair["input"][0]) == 30]
    assert len(large) == 1
    analysis = module.analyze(large[0]["input"])
    assert len(analysis["diagonal"]) >= 8
    assert len(analysis["orthogonal"]) >= 8
    assert analysis["negative_controls"] >= 4
    assert sum(cell != 0 for row in large[0]["input"] for cell in row) >= 80
    assert len({color for _, _, color in analysis["diagonal"] + analysis["orthogonal"]}) >= 6


def test_protected_racket_matches_all_labels_for_both_settings(racket_apply):
    module = prototype()
    for setting in module.SETTINGS:
        episode = module.generate(7, setting, demos=2, queries=4)
        source = module.program(setting)
        for pair in episode["train"] + episode["test"]:
            assert racket_apply(source, pair["input"]) == pair["output"]


def test_relation_detection_is_a_real_wrong_intermediate_counterfactual():
    module = prototype()
    episode = module.generate(5, {"neighbor_mode": "orthogonal"}, demos=2, queries=4)
    pair = episode["test"][0]
    analysis = module.analyze(pair["input"])
    assert analysis["orthogonal"] != analysis["diagonal"]
    assert module.transform(pair["input"], {"neighbor_mode": "orthogonal"}) != module.transform(
        pair["input"], {"neighbor_mode": "diagonal"}
    )


@pytest.mark.parametrize(
    "settings",
    [None, {}, {"neighbor_mode": "king"}, {"neighbor_mode": 1}, {"neighbor_mode": "diagonal", "extra": 1}],
)
def test_invalid_settings_fail_loudly(settings):
    with pytest.raises((TypeError, ValueError)):
        prototype().generate(0, settings, demos=2, queries=4)


@pytest.mark.parametrize("demos,queries", [(1, 4), (7, 4), (2, 0), (2, 5), (True, 4)])
def test_invalid_counts_fail_loudly(demos, queries):
    with pytest.raises((TypeError, ValueError)):
        prototype().generate(0, {"neighbor_mode": "diagonal"}, demos=demos, queries=queries)


def test_bounded_audit_exercises_counts_shortcuts_and_large_scene():
    audit_path = HOME / "workspace" / "parametric" / "audit.py"
    module = _load(audit_path, "_task_9f74_audit_test")
    report = module.audit(2)
    assert report["status"] == "passed"
    assert report["episodes"] == 4
    assert report["generated_pairs_checked"] == 20
    assert report["large_query_banks"] == 2
    assert report["observed_center_positions"] >= 8
    assert report["observed_positive_colors"] >= 6


def test_preflight_compat_normalizes_single_test_pair_without_touching_lists():
    path = HOME / "workspace" / "parametric" / "preflight_compat.py"
    module = _load(path, "_task_9f74_preflight_compat_test")
    pair = {"input": [[0]], "output": [[0]]}
    assert module._split_pairs({"test": pair}, "test") == [pair]
    assert module._split_pairs({"train": [pair]}, "train") == [pair]
