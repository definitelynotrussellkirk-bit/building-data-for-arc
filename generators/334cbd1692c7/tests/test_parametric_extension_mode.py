from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path

import pytest

TASK_ID = "334cbd1692c7"
HOME = Path(__file__).resolve().parents[1]
ROOT = HOME.parents[1]
GENERATOR_PATH = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))
PROTOTYPE_PATH = HOME / "workspace" / "parametric" / "prototype.py"
ADAPTER_PATH = HOME / "workspace" / "parametric" / "adapter.py"


def _load(path: Path, name: str):
    assert path.is_file(), f"missing source: {path}"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def generator():
    return _load(GENERATOR_PATH, "_task_334c_generator_test")


def prototype():
    return _load(PROTOTYPE_PATH, "_task_334c_parametric_test")


def adapter():
    return _load(ADAPTER_PATH, "_task_334c_adapter_test")


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
    assert module.program({"extension_mode": "to_edges"}) == canonical_program()
    assert adapter().program({"extension_mode": "to_edges"}) == canonical_program()


def test_generation_is_setting_matched_and_count_prefix_stable():
    module = prototype()
    edge = module.generate(17, {"extension_mode": "to_edges"}, demos=6, queries=4)
    key = module.generate(17, {"extension_mode": "key_only"}, demos=6, queries=4)
    assert [pair["input"] for pair in edge["train"] + edge["test"]] == [
        pair["input"] for pair in key["train"] + key["test"]
    ]
    short = module.generate(17, {"extension_mode": "to_edges"}, demos=2, queries=1)
    assert short["train"] == edge["train"][:2]
    assert short["test"] == edge["test"][:1]
    serial = [json.dumps(pair["input"]) for pair in edge["train"] + edge["test"]]
    assert len(serial) == len(set(serial))


def test_two_demonstrations_identify_each_setting_and_reject_shortcuts():
    module = prototype()
    for seed in (0, 17, 91):
        for setting in module.SETTINGS:
            episode = module.generate(seed, setting, demos=2, queries=4)
            assert module.fit_settings(episode["train"]) == [setting]
            for pair in episode["train"] + episode["test"]:
                assert module.transform(pair["input"], setting) == pair["output"]
            for pair in episode["train"]:
                assert module.transform(pair["input"], {"extension_mode": "to_edges"}) != module.transform(
                    pair["input"], {"extension_mode": "key_only"}
                )
                assert module.no_key_erase(pair["input"], setting) != pair["output"]
                assert module.rotated_arm_colors(pair["input"], setting) != pair["output"]


def test_four_query_bank_has_substantive_30_by_30_multi_rectangle_case():
    module = prototype()
    episode = module.generate(23, {"extension_mode": "to_edges"}, demos=3, queries=4)
    large = [pair for pair in episode["test"] if len(pair["input"]) == 30 and len(pair["input"][0]) == 30]
    assert len(large) == 1
    facts = module.analyze(large[0]["input"])
    assert len(facts["rectangles"]) >= 3
    assert len(facts["markers"]) >= 3
    assert len(facts["key_offsets"]) >= 11
    changed = sum(
        before != after
        for input_row, output_row in zip(large[0]["input"], large[0]["output"])
        for before, after in zip(input_row, output_row)
    )
    assert changed >= 50


def test_base_generator_has_a_parseable_key_and_rectangle_across_bands():
    source = generator()
    module = prototype()
    for difficulty in (None, "medium", "hard"):
        for index in range(80):
            grid = source.generate(4000 + index, index, difficulty=difficulty)
            assert source.self_check(grid, difficulty=difficulty) == []
            facts = module.analyze(grid)
            assert len(facts["rectangles"]) == 1
            assert len(facts["markers"]) == 1
            assert len(facts["key_offsets"]) == 9


def test_protected_racket_matches_all_labels_for_both_settings(racket_apply):
    module = prototype()
    for setting in module.SETTINGS:
        episode = module.generate(7, setting, demos=2, queries=4)
        source = module.program(setting)
        for pair in episode["train"] + episode["test"]:
            assert racket_apply(source, pair["input"]) == pair["output"]


def test_key_extraction_is_a_real_input_dependent_intermediate():
    module = prototype()
    first = module.generate(2, {"extension_mode": "to_edges"}, demos=2, queries=4)["test"][0]
    second = module.generate(3, {"extension_mode": "to_edges"}, demos=2, queries=4)["test"][0]
    facts_a = module.analyze(first["input"])
    facts_b = module.analyze(second["input"])
    assert facts_a["key_offsets"] != facts_b["key_offsets"]
    assert module.rotated_arm_colors(first["input"], {"extension_mode": "to_edges"}) != first["output"]


@pytest.mark.parametrize(
    "settings",
    [None, {}, {"extension_mode": "short"}, {"extension_mode": 1}, {"extension_mode": "to_edges", "extra": 1}],
)
def test_invalid_settings_fail_loudly(settings):
    with pytest.raises((TypeError, ValueError)):
        prototype().generate(0, settings, demos=2, queries=4)


@pytest.mark.parametrize("demos,queries", [(1, 4), (7, 4), (2, 0), (2, 5), (True, 4)])
def test_invalid_counts_fail_loudly(demos, queries):
    with pytest.raises((TypeError, ValueError)):
        prototype().generate(0, {"extension_mode": "to_edges"}, demos=demos, queries=queries)
