from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
PARAM = HOME / "workspace" / "parametric"
sys.path.insert(0, str(HOME.parents[1] / "shared" / "runtime"))


def _load(name: str = "prototype.py"):
    path = PARAM / name
    spec = importlib.util.spec_from_file_location(f"_test_a20_{path.stem}", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _canonical_program() -> str:
    repo = HOME.parents[1]
    with (repo / "shared/data/canonical/puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == "a20ecf84f041":
                return row["program_solution"]
    raise AssertionError("canonical task missing")


def test_default_program_is_exact_canonical_authority():
    prototype = _load()
    assert prototype.program({"finish": "full_result"}) == _canonical_program()
    assert prototype.program_for("full_result") == _canonical_program()
    assert prototype.program_for("mark_largest_component") != _canonical_program()


@pytest.mark.parametrize("seed", [0, 17, 2**63 - 1])
@pytest.mark.parametrize("finish", ["full_result", "mark_largest_component"])
def test_counts_prefixes_labels_and_distinct_inputs(seed, finish):
    prototype = _load()
    large = prototype.generate_episode(seed, finish, demos=6, queries=4)
    small = prototype.generate_episode(seed, finish, demos=2, queries=1)
    assert small["train"] == large["train"][:2]
    assert small["test"] == large["test"][:1]
    assert len(large["train"]) == 6
    assert len(large["test"]) == 4
    assert large["program_solution"] == prototype.program_for(finish)
    encoded = [json.dumps(pair["input"], separators=(",", ":"))
               for pair in large["train"] + large["test"]]
    assert len(encoded) == len(set(encoded))
    for pair in large["train"] + large["test"]:
        assert pair["output"] == prototype.solve(pair["input"], finish)


@pytest.mark.parametrize("seed", [0, 17, 991])
def test_inputs_are_matched_across_settings(seed):
    prototype = _load()
    canonical = prototype.generate_episode(seed, "full_result", demos=6, queries=4)
    relay = prototype.generate_episode(seed, "mark_largest_component", demos=6, queries=4)
    assert [p["input"] for p in canonical["train"] + canonical["test"]] == [
        p["input"] for p in relay["train"] + relay["test"]
    ]


@pytest.mark.parametrize("seed", range(24))
@pytest.mark.parametrize("finish", ["full_result", "mark_largest_component"])
def test_two_demos_identify_setting_and_declared_rivals(seed, finish):
    prototype = _load()
    episode = prototype.generate_episode(seed, finish, demos=2, queries=4)
    assert prototype.teaching_survivors(episode["train"]) == [finish]
    assert all(
        prototype.solve(pair["input"], "full_result")
        != prototype.solve(pair["input"], "mark_largest_component")
        for pair in episode["test"]
    )


def test_query_bank_reaches_lawful_geometry_limit_with_substantive_content():
    prototype = _load()
    episode = prototype.generate_episode(17, "mark_largest_component", demos=6, queries=4)
    largest = episode["test"][3]
    assert (len(largest["input"]), len(largest["input"][0])) == (19, 29)
    assert (len(largest["output"]), len(largest["output"][0])) == (19, 29)
    assert sum(v != 0 for row in largest["input"] for v in row) >= 180
    info = prototype.analyze(largest["input"])
    assert info["panel_size"] == 9
    assert len(info["components4"]) >= 2
    sizes = [component["size"] for component in info["components4"]]
    assert sizes.count(max(sizes)) == 1
    assert sum(v == 8 for row in largest["output"] for v in row) == max(sizes)


def test_public_first_turn_is_independent_of_future_queries():
    prototype = _load()
    from reviewer_support import public_challenge_bytes, public_challenge_id

    one = prototype.generate_episode(4, "mark_largest_component", demos=3, queries=1)
    four = prototype.generate_episode(4, "mark_largest_component", demos=3, queries=4)

    def public(ep):
        return {"train": ep["train"], "test": [{"input": ep["test"][0]["input"]}]}

    assert public_challenge_bytes(public(one)) == public_challenge_bytes(public(four))
    assert public_challenge_id(public(one)) == public_challenge_id(public(four))


@pytest.mark.parametrize(
    "args",
    [
        (-1, "full_result", 2, 1),
        (2**63, "full_result", 2, 1),
        (0, "full_result", 1, 1),
        (0, "full_result", 7, 1),
        (0, "full_result", 2, 0),
        (0, "full_result", 2, 5),
        (0, "bad", 2, 1),
        (True, "full_result", 2, 1),
    ],
)
def test_invalid_requests_are_rejected(args):
    prototype = _load()
    with pytest.raises(ValueError):
        prototype.generate_episode(*args)


def test_thin_adapter_returns_only_native_contract_fields():
    module = _load("adapter.py")
    result = module.generate(0, {"finish": "mark_largest_component"}, 2, 4)
    assert set(result) == {"train", "test", "program_solution"}
    assert len(result["train"]) == 2 and len(result["test"]) == 4
