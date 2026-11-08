"""Native parametric contract for local checkerboard phase."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
REPO = HOME.parents[1]
PARAM = HOME / "workspace" / "parametric"
RUNTIME = REPO / "shared" / "runtime"
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(RUNTIME))


def _load():
    path = PARAM / "prototype.py"
    spec = importlib.util.spec_from_file_location("_test_checker_phase", path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _nonzero(grid):
    return sum(value != 0 for row in grid for value in row)


def test_default_program_is_exact_catalog_authority():
    from arcpuzzles import Catalog

    prototype = _load()
    record = Catalog(REPO).get("2b7bcfbf942b")
    canonical = {v["program_solution"] for v in record["variants"]}
    assert canonical == {prototype.program_for("colored_first")}
    assert prototype.program({"checker_phase": "colored_first"}) == next(iter(canonical))


def test_program_settings_are_strict():
    prototype = _load()
    with pytest.raises(ValueError):
        prototype.program({})
    with pytest.raises(ValueError):
        prototype.program({"checker_phase": "colored_first", "extra": 1})
    with pytest.raises(ValueError):
        prototype.program({"checker_phase": "diagonal"})


@pytest.mark.parametrize("seed", [0, 17, 2**63 - 1])
@pytest.mark.parametrize("phase", ["colored_first", "zero_first"])
def test_counts_prefixes_uniqueness_and_claims(seed, phase):
    prototype = _load()
    large = prototype.generate_episode(seed, phase, demos=6, queries=4)
    small = prototype.generate_episode(seed, phase, demos=2, queries=1)
    assert small["train"] == large["train"][:2]
    assert small["test"] == large["test"][:1]
    inputs = [json.dumps(pair["input"], separators=(",", ":"))
              for pair in large["train"] + large["test"]]
    assert len(inputs) == len(set(inputs)) == 10
    assert large["program_solution"] == prototype.program_for(phase)
    for pair in large["train"] + large["test"]:
        assert pair["output"] == prototype.solve(pair["input"], phase)


@pytest.mark.parametrize("seed", [0, 17, 991])
def test_inputs_are_matched_across_settings(seed):
    prototype = _load()
    colored = prototype.generate_episode(seed, "colored_first", demos=6, queries=4)
    zero = prototype.generate_episode(seed, "zero_first", demos=6, queries=4)
    assert [p["input"] for p in colored["train"] + colored["test"]] == [
        p["input"] for p in zero["train"] + zero["test"]
    ]


@pytest.mark.parametrize("seed", range(64))
@pytest.mark.parametrize("phase", ["colored_first", "zero_first"])
def test_two_demos_identify_setting_and_declared_rivals(seed, phase):
    prototype = _load()
    episode = prototype.generate_episode(seed, phase, demos=2, queries=4)
    assert prototype.teaching_survivors(episode["train"]) == [phase]
    assert all(
        prototype.solve(pair["input"], "colored_first")
        != prototype.solve(pair["input"], "zero_first")
        for pair in episode["test"]
    )


def test_teaching_examples_cover_local_origin_nonframes_and_multiple_colors():
    prototype = _load()
    episode = prototype.generate_episode(17, "colored_first", demos=2, queries=4)
    objects = [obj for pair in episode["train"] for obj in prototype.analyze(pair["input"])["objects"]]
    assert {obj["style"] for obj in objects} >= {"frame", "open", "cross"}
    assert len({obj["color"] for obj in objects}) >= 3
    assert any((obj["bbox"][0] + obj["bbox"][1]) % 2 == 1 for obj in objects)
    assert any((obj["bbox"][3] - obj["bbox"][1] + 1) % 2 == 0 for obj in objects)


def test_largest_query_is_substantive_and_touches_all_boundaries():
    prototype = _load()
    grid = prototype.sample_input(17, "query", 3)
    assert (len(grid), len(grid[0])) == (30, 30)
    assert _nonzero(grid) >= 120
    assert any(value != 0 for value in grid[0])
    assert any(value != 0 for value in grid[-1])
    assert any(row[0] != 0 for row in grid)
    assert any(row[-1] != 0 for row in grid)
    analysis = prototype.analyze(grid)
    assert len(analysis["objects"]) == 5
    assert len({obj["color"] for obj in analysis["objects"]}) == 5


def test_public_first_turn_is_independent_of_future_queries():
    prototype = _load()
    from reviewer_support import public_challenge_bytes, public_challenge_id

    one = prototype.generate_episode(4, "zero_first", demos=3, queries=1)
    four = prototype.generate_episode(4, "zero_first", demos=3, queries=4)
    def public(ep):
        return {"train": ep["train"], "test": [{"input": ep["test"][0]["input"]}]}
    assert public_challenge_bytes(public(one)) == public_challenge_bytes(public(four))
    assert public_challenge_id(public(one)) == public_challenge_id(public(four))


@pytest.mark.parametrize(
    "args",
    [
        (-1, "colored_first", 2, 1),
        (2**63, "colored_first", 2, 1),
        (0, "colored_first", 1, 1),
        (0, "colored_first", 7, 1),
        (0, "colored_first", 2, 0),
        (0, "colored_first", 2, 5),
        (0, "bad", 2, 1),
        (True, "colored_first", 2, 1),
    ],
)
def test_invalid_requests_are_rejected(args):
    prototype = _load()
    with pytest.raises(ValueError):
        prototype.generate_episode(*args)


def test_thin_adapter_returns_only_native_contract_fields():
    path = PARAM / "adapter.py"
    spec = importlib.util.spec_from_file_location("_test_checker_adapter", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    result = module.generate(0, {"checker_phase": "colored_first"}, 2, 4)
    assert set(result) == {"train", "test", "program_solution"}
    assert len(result["train"]) == 2 and len(result["test"]) == 4
