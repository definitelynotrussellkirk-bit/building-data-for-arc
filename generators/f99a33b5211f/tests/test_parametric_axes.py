from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

TASK_ID = "f99a33b5211f"
HOME = Path(__file__).resolve().parents[1]
ROOT = HOME.parents[1]
PROTOTYPE_PATH = HOME / "workspace" / "parametric" / "prototype.py"
ADAPTER_PATH = HOME / "workspace" / "parametric" / "adapter.py"
GENERATOR_PATH = HOME / "generator.py"


def _load(path: Path, name: str):
    assert path.is_file(), f"missing source: {path}"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def prototype():
    return _load(PROTOTYPE_PATH, "_task_f99_axis_parametric_test")


def adapter():
    return _load(ADAPTER_PATH, "_task_f99_axis_adapter_test")


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


def test_existing_native_generator_still_builds_one_valid_frame():
    generator = _load(GENERATOR_PATH, "_task_f99_native_generator_test")
    for seed, difficulty in ((3, None), (11, "medium"), (19, "hard")):
        grid = generator.generate(seed, 0, difficulty=difficulty)
        assert generator.self_check(grid, difficulty=difficulty) == []


def test_default_program_is_exact_canonical_authority():
    module = prototype()
    assert module.program({"axis": "x"}) == canonical_program()
    assert adapter().program({"axis": "x"}) == canonical_program()


def test_generation_is_count_independent_prefix_stable_and_setting_matched():
    module = prototype()
    x_axis = module.generate(17, {"axis": "x"}, demos=6, queries=4)
    y_axis = module.generate(17, {"axis": "y"}, demos=6, queries=4)
    assert [pair["input"] for pair in x_axis["train"] + x_axis["test"]] == [
        pair["input"] for pair in y_axis["train"] + y_axis["test"]
    ]
    short = module.generate(17, {"axis": "x"}, demos=2, queries=1)
    assert short["train"] == x_axis["train"][:2]
    assert short["test"] == x_axis["test"][:1]
    inputs = [json.dumps(pair["input"]) for pair in x_axis["train"] + x_axis["test"]]
    assert len(inputs) == len(set(inputs))


def test_two_demonstrations_identify_both_settings_and_every_scene_disagrees():
    module = prototype()
    for seed in (0, 17, 91):
        for setting in module.SETTINGS:
            episode = module.generate(seed, setting, demos=2, queries=4)
            assert module.fit_settings(episode["train"]) == [setting]
            for pair in episode["train"] + episode["test"]:
                analysis = module.analyze(pair["input"])
                assert analysis["origin_color"] == 5
                assert analysis["x_marker_color"] == 6
                assert analysis["y_marker_color"] == 7
                assert analysis["x_tip"] != analysis["y_tip"]
                assert pair["input"][analysis["x_tip"][0]][analysis["x_tip"][1]] == 0
                assert pair["input"][analysis["y_tip"][0]][analysis["y_tip"][1]] == 0
                assert module.transform(pair["input"], {"axis": "x"}) != module.transform(
                    pair["input"], {"axis": "y"}
                )
                assert module.transform(pair["input"], setting) == pair["output"]


def test_demo_pair_rejects_declared_shortcuts_for_both_settings():
    module = prototype()
    for seed in (2, 9, 31):
        for setting in module.SETTINGS:
            episode = module.generate(seed, setting, demos=2, queries=4)
            expected = [pair["output"] for pair in episode["train"]]
            rivals = {
                "both_axes": [module.paint_both_axes(pair["input"]) for pair in episode["train"]],
                "origin_only": [module.paint_origin_only(pair["input"]) for pair in episode["train"]],
                "marker_cells_only": [module.paint_marker_cells_only(pair["input"]) for pair in episode["train"]],
            }
            for direction in module.CARDINAL:
                rivals[f"fixed_{direction}"] = [
                    module.paint_fixed_global_direction(pair["input"], direction)
                    for pair in episode["train"]
                ]
            assert all(outputs != expected for outputs in rivals.values())


def test_four_query_bank_contains_substantive_30_by_30_stress():
    module = prototype()
    episode = module.generate(23, {"axis": "y"}, demos=3, queries=4)
    large = [pair for pair in episode["test"] if len(pair["input"]) == 30 and len(pair["input"][0]) == 30]
    assert len(large) == 1
    analysis = module.analyze(large[0]["input"])
    assert analysis["distractor_components"] >= 20
    assert analysis["distractor_cells"] >= 100
    assert analysis["nonzero_cells"] >= 103
    assert set(analysis["distractor_colors"]) == {1, 2, 3, 4, 9}


def test_protected_racket_matches_all_labels_for_both_settings(racket_apply):
    module = prototype()
    for setting in module.SETTINGS:
        episode = module.generate(7, setting, demos=2, queries=4)
        source = module.program(setting)
        for pair in episode["train"] + episode["test"]:
            assert racket_apply(source, pair["input"]) == pair["output"]


def test_frame_vector_is_a_real_wrong_intermediate_counterfactual():
    module = prototype()
    episode = module.generate(5, {"axis": "y"}, demos=2, queries=4)
    pair = episode["test"][0]
    analysis = module.analyze(pair["input"])
    assert analysis["x_vector"] != analysis["y_vector"]
    assert analysis["x_tip"] != analysis["y_tip"]
    assert module.transform(pair["input"], {"axis": "y"}) != module.transform(
        pair["input"], {"axis": "x"}
    )


@pytest.mark.parametrize(
    "settings",
    [None, {}, {"axis": "z"}, {"axis": 1}, {"axis": "x", "extra": 1}],
)
def test_invalid_settings_fail_loudly(settings):
    with pytest.raises((TypeError, ValueError)):
        prototype().generate(0, settings, demos=2, queries=4)


@pytest.mark.parametrize("demos,queries", [(1, 4), (7, 4), (2, 0), (2, 5), (True, 4)])
def test_invalid_counts_fail_loudly(demos, queries):
    with pytest.raises((TypeError, ValueError)):
        prototype().generate(0, {"axis": "x"}, demos=demos, queries=queries)


def test_bounded_audit_exercises_counts_shortcuts_orientation_and_large_scene():
    audit_path = HOME / "workspace" / "parametric" / "audit.py"
    module = _load(audit_path, "_task_f99_axis_audit_test")
    report = module.audit(2)
    assert report["status"] == "passed"
    assert report["episodes"] == 4
    assert report["generated_pairs_checked"] == 20
    assert report["large_query_banks"] == 2
    assert report["observed_x_vectors"] == 4
    assert report["observed_y_vectors"] == 4
    assert report["observed_distractor_colors"] == 5
    assert report["maximum_nonzero_cells"] >= 103


def test_preflight_compat_normalizes_single_test_pair_without_touching_lists():
    path = HOME / "workspace" / "parametric" / "preflight_compat.py"
    module = _load(path, "_task_f99_axis_preflight_compat_test")
    pair = {"input": [[0]], "output": [[0]]}
    assert module._split_pairs({"test": pair}, "test") == [pair]
    assert module._split_pairs({"train": [pair]}, "train") == [pair]
