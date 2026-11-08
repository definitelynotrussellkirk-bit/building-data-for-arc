"""Focused base and parametric tests for 6387de413b52."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import sys

import pytest


HOME = Path(__file__).resolve().parents[1]
WORK = HOME / "workspace" / "parametric"
ROOT = HOME.parents[1]
RUNTIME = ROOT / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))
CANONICAL_SHA256 = "64c7d23f90a72e344a9cb5652dd443b5562ef005c1d5dabb06221d51d06ca238"


def module(name: str):
    path = WORK / f"{name}.py"
    assert path.is_file(), f"missing native parametric {name}.py"
    spec = importlib.util.spec_from_file_location(f"test_6387_{name}_{hash(path)}", path)
    loaded = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(loaded)
    return loaded


def generator_module():
    path = HOME / "generator.py"
    spec = importlib.util.spec_from_file_location("test_6387_generator", path)
    loaded = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(loaded)
    return loaded


def inputs(episode: dict, split: str):
    return [pair["input"] for pair in episode[split]]


def test_default_program_is_exact_canonical_and_swap_is_distinct() -> None:
    adapter = module("adapter")
    canonical = adapter.program({"row_source": "color2"})
    assert hashlib.sha256(canonical.encode()).hexdigest() == CANONICAL_SHA256
    swapped = adapter.program({"row_source": "color3"})
    assert swapped != canonical
    assert swapped.count("(rule!") == 1


def test_base_generator_produces_lawful_nonempty_cross_products() -> None:
    generator, prototype = generator_module(), module("prototype")
    for difficulty in (None, "medium"):
        for seed in (0, 17, 43):
            grid = generator.generate(seed, seed % 7, difficulty=difficulty)
            assert generator.self_check(grid, difficulty=difficulty) == []
            output = prototype.predict(grid, "color2")
            assert any(value == 8 for row in output for value in row)
            facts = prototype.intermediate(grid, {"row_source": "color2"})
            assert facts["active_rows"] and facts["active_cols"]


def test_independent_counts_matched_settings_and_query_prefix() -> None:
    adapter = module("adapter")
    for seed in (0, 17, 93):
        for demos in (2, 3, 6):
            canonical = adapter.generate(seed, {"row_source": "color2"}, demos, 4)
            swapped = adapter.generate(seed, {"row_source": "color3"}, demos, 4)
            assert len(canonical["train"]) == demos
            assert len(canonical["test"]) == 4
            assert inputs(canonical, "train") == inputs(swapped, "train")
            assert inputs(canonical, "test") == inputs(swapped, "test")
            one = adapter.generate(seed, {"row_source": "color2"}, demos, 1)
            assert one["train"] == canonical["train"]
            assert one["test"] == canonical["test"][:1]
            all_inputs = inputs(canonical, "train") + inputs(canonical, "test")
            assert len({json.dumps(grid) for grid in all_inputs}) == demos + 4
        two = adapter.generate(seed, {"row_source": "color2"}, 2, 4)
        six = adapter.generate(seed, {"row_source": "color2"}, 6, 4)
        assert two["train"] == six["train"][:2]
        assert two["test"] == six["test"]


def test_two_demos_identify_both_role_settings() -> None:
    adapter, prototype = module("adapter"), module("prototype")
    for seed in (0, 17, 93):
        for source, opposite in (("color2", "color3"), ("color3", "color2")):
            episode = adapter.generate(seed, {"row_source": source}, 2, 4)
            assert any(prototype.predict(pair["input"], opposite) != pair["output"]
                       for pair in episode["train"])
            for pair in episode["train"] + episode["test"]:
                assert pair["output"] == prototype.predict(pair["input"], source)


def test_intermediate_axis_sets_are_input_dependent_and_consumed() -> None:
    adapter, prototype = module("adapter"), module("prototype")
    episode = adapter.generate(17, {"row_source": "color3"}, 2, 4)
    for pair in episode["train"] + episode["test"]:
        grid = pair["input"]
        chosen = prototype.intermediate(grid, {"row_source": "color3"})
        wrong = prototype.intermediate(grid, {"row_source": "color2"})
        assert (chosen["active_rows"], chosen["active_cols"]) != (
            wrong["active_rows"], wrong["active_cols"])
        assert prototype.paint_intermediate(chosen) == pair["output"]
        assert prototype.paint_intermediate(wrong) != pair["output"]


def test_canonical_mirror_matches_all_original_labels() -> None:
    prototype = module("prototype")
    pairs = prototype.original_pairs()
    assert len(pairs) >= 3
    for pair in pairs:
        assert prototype.predict(pair["input"], "color2") == pair["output"]


def test_query_bank_contains_dense_30_by_30_stress() -> None:
    adapter, prototype = module("adapter"), module("prototype")
    episode = adapter.generate(17, {"row_source": "color3"}, 3, 4)
    pair = next(pair for pair in episode["test"] if len(pair["input"]) == 30)
    grid, output = pair["input"], pair["output"]
    assert len(grid[0]) == 30
    nonzero = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value]
    assert len(nonzero) >= 60
    assert {((r >= 15), (c >= 15)) for r, c in nonzero} == {
        (False, False), (False, True), (True, False), (True, True)
    }
    facts = prototype.describe_scene(grid)
    assert facts["color2_components"] >= 4
    assert facts["color3_components"] >= 4
    assert facts["canonical_cells"] >= 120
    assert facts["swapped_cells"] >= 120
    assert sum(value == 8 for row in output for value in row) == facts["swapped_cells"]


def test_bounded_rival_audit_has_no_harmful_survivor() -> None:
    audit = module("audit")
    report = audit.run_audit(seeds=(0, 17, 93), demos_values=(2, 3, 6))
    assert report["episodes"] == 18
    assert report["harmful_survivors"] == []
    assert report["input_failures"] == []


def test_preflight_compat_normalizes_single_pair_split_without_mutation() -> None:
    compat = module("preflight_compat")
    pair = {"input": [[2]], "output": [[8]]}
    source = [{"train": [pair], "test": pair, "program_solution": "(rule! g)"}]
    normalized = compat.normalize_record_splits(source)
    assert normalized[0]["train"] == [pair]
    assert normalized[0]["test"] == [pair]
    assert source[0]["test"] is pair
    assert normalized[0] is not source[0]


def test_invalid_requests_fail_closed() -> None:
    adapter = module("adapter")
    for settings in ({}, None, {"row_source": "all"}, {"row_source": 2},
                     {"row_source": "color2", "extra": 1}):
        with pytest.raises(ValueError):
            adapter.program(settings)
    for seed, demos, queries in ((True, 2, 4), (-1, 2, 4), (2**63, 2, 4),
                                  (0, 1, 4), (0, 7, 4), (0, True, 4),
                                  (0, 2, 0), (0, 2, 5), (0, 2, True)):
        with pytest.raises(ValueError):
            adapter.generate(seed, {"row_source": "color2"}, demos, queries)


def test_generation_is_rng_neutral_deterministic_and_fresh() -> None:
    adapter = module("adapter")
    random.seed(94321)
    before = random.getstate()
    episode = adapter.generate(17, {"row_source": "color3"}, 3, 4)
    saved = copy.deepcopy(episode)
    assert random.getstate() == before
    episode["train"][0]["input"][0][0] = 9
    assert adapter.generate(17, {"row_source": "color3"}, 3, 4) == saved
