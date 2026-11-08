from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path

import pytest

TASK_ID = "39ad03f74acb"
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
    return _load(GENERATOR_PATH, "_task_39ad_generator_test")


def prototype():
    return _load(PROTOTYPE_PATH, "_task_39ad_parametric_test")


def adapter():
    return _load(ADAPTER_PATH, "_task_39ad_adapter_test")


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


def _segments(grid):
    h, w = len(grid), len(grid[0])
    found = []
    for r in range(h):
        c = 0
        while c < w:
            if grid[r][c] != 1:
                c += 1
                continue
            start = c
            while c < w and grid[r][c] == 1:
                c += 1
            if c - start >= 3:
                found.append(("h", r, start, c - start))
    for c in range(w):
        r = 0
        while r < h:
            if grid[r][c] != 1:
                r += 1
                continue
            start = r
            while r < h and grid[r][c] == 1:
                r += 1
            if r - start >= 3:
                found.append(("v", start, c, r - start))
    return found


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


def test_ordinary_sampler_repairs_orientation_only_lessons():
    module = generator()
    assert module.VERSION == "1.2.0"
    for difficulty in (None, "easy", "medium", "hard"):
        for index in range(20):
            grid = module.generate(8100 + index, index, difficulty=difficulty)
            assert module.self_check(grid, difficulty=difficulty) == []
            orientations = {segment[0] for segment in _segments(grid)}
            assert orientations == {"h", "v"}, (difficulty, index, orientations)


def test_default_program_is_exact_canonical_authority():
    module = prototype()
    assert module.program({"selection_mode": "all"}) == canonical_program()
    assert adapter().program({"selection_mode": "all"}) == canonical_program()


def test_generation_is_count_independent_prefix_stable_and_setting_matched():
    module = prototype()
    all_episode = module.generate(17, {"selection_mode": "all"}, demos=6, queries=4)
    long_episode = module.generate(17, {"selection_mode": "longest"}, demos=6, queries=4)
    assert [pair["input"] for pair in all_episode["train"] + all_episode["test"]] == [
        pair["input"] for pair in long_episode["train"] + long_episode["test"]
    ]
    short = module.generate(17, {"selection_mode": "all"}, demos=2, queries=1)
    assert short["train"] == all_episode["train"][:2]
    assert short["test"] == all_episode["test"][:1]
    inputs = [json.dumps(pair["input"]) for pair in all_episode["train"] + all_episode["test"]]
    assert len(inputs) == len(set(inputs))


def test_two_demonstrations_identify_each_setting_and_reject_simple_shortcuts():
    module = prototype()
    for seed in (0, 17, 91):
        for setting in module.SETTINGS:
            episode = module.generate(seed, setting, demos=2, queries=4)
            assert module.fit_settings(episode["train"]) == [setting]
            assert all(module.transform(pair["input"], setting) == pair["output"] for pair in episode["train"] + episode["test"])
            assert all(
                module.transform(pair["input"], {"selection_mode": "all"})
                != module.transform(pair["input"], {"selection_mode": "longest"})
                for pair in episode["train"]
            )
            # The generated lesson cannot be solved by a vertical-only or horizontal-only painter.
            for pair in episode["train"]:
                assert module.orientation_only(pair["input"], "h") != pair["output"]
                assert module.orientation_only(pair["input"], "v") != pair["output"]


def test_four_query_episode_contains_substantive_30_by_30_stress():
    module = prototype()
    episode = module.generate(23, {"selection_mode": "longest"}, demos=3, queries=4)
    large = [pair for pair in episode["test"] if len(pair["input"]) == 30 and len(pair["input"][0]) == 30]
    assert len(large) == 1
    segments = _segments(large[0]["input"])
    assert {segment[0] for segment in segments} == {"h", "v"}
    assert len(segments) >= 8
    assert sum(segment[3] for segment in segments) >= 70
    lengths = {segment[3] for segment in segments}
    assert len(lengths) >= 6


def test_protected_racket_matches_all_labels_for_both_settings(racket_apply):
    module = prototype()
    for setting in module.SETTINGS:
        episode = module.generate(7, setting, demos=2, queries=4)
        source = module.program(setting)
        for pair in episode["train"] + episode["test"]:
            assert racket_apply(source, pair["input"]) == pair["output"]


def test_longest_dependency_has_a_real_skip_a_counterfactual():
    module = prototype()
    episode = module.generate(5, {"selection_mode": "longest"}, demos=2, queries=4)
    pair = episode["test"][0]
    lengths = module.segment_lengths(pair["input"])
    assert len(set(lengths)) >= 2
    assert max(lengths) == module.longest_length(pair["input"])
    assert module.transform(pair["input"], {"selection_mode": "longest"}) != module.transform(
        pair["input"], {"selection_mode": "all"}
    )


@pytest.mark.parametrize(
    "settings",
    [None, {}, {"selection_mode": "shortest"}, {"selection_mode": 1}, {"selection_mode": "all", "extra": 1}],
)
def test_invalid_settings_fail_loudly(settings):
    module = prototype()
    with pytest.raises((TypeError, ValueError)):
        module.generate(0, settings, demos=2, queries=4)


@pytest.mark.parametrize("demos,queries", [(1, 4), (7, 4), (2, 0), (2, 5), (True, 4)])
def test_invalid_counts_fail_loudly(demos, queries):
    with pytest.raises((TypeError, ValueError)):
        prototype().generate(0, {"selection_mode": "all"}, demos=demos, queries=queries)
