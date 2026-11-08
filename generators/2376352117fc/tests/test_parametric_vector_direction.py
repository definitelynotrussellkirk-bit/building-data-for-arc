"""Native parametric contract for blue-to-red versus red-to-blue translation."""
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
    spec = importlib.util.spec_from_file_location("_test_vector_direction", path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _nonzero(grid):
    return sum(value != 0 for row in grid for value in row)


def _connected(cells):
    cells = set(cells)
    if not cells:
        return False
    seen = {min(cells)}
    stack = list(seen)
    while stack:
        r, c = stack.pop()
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nxt = (r + dr, c + dc)
            if nxt in cells and nxt not in seen:
                seen.add(nxt)
                stack.append(nxt)
    return seen == cells


def test_default_program_is_exact_catalog_authority():
    from arcpuzzles import Catalog

    prototype = _load()
    record = Catalog(REPO).get("2376352117fc")
    canonical = {v["program_solution"] for v in record["variants"]}
    assert canonical == {prototype.program_for("blue_to_red")}
    assert prototype.program({"vector_direction": "blue_to_red"}) == next(iter(canonical))


def test_program_settings_are_strict():
    prototype = _load()
    with pytest.raises(ValueError):
        prototype.program({})
    with pytest.raises(ValueError):
        prototype.program({"vector_direction": "blue_to_red", "extra": 1})
    with pytest.raises(ValueError):
        prototype.program({"vector_direction": "sideways"})


@pytest.mark.parametrize("seed", [0, 17, 2**63 - 1])
@pytest.mark.parametrize("direction", ["blue_to_red", "red_to_blue"])
def test_counts_prefixes_uniqueness_and_claims(seed, direction):
    prototype = _load()
    large = prototype.generate_episode(seed, direction, demos=6, queries=4)
    small = prototype.generate_episode(seed, direction, demos=2, queries=1)
    assert small["train"] == large["train"][:2]
    assert small["test"] == large["test"][:1]
    assert len(large["train"]) == 6
    assert len(large["test"]) == 4
    inputs = [json.dumps(pair["input"], separators=(",", ":"))
              for pair in large["train"] + large["test"]]
    assert len(inputs) == len(set(inputs))
    assert large["program_solution"] == prototype.program_for(direction)
    for pair in large["train"] + large["test"]:
        assert pair["output"] == prototype.solve(pair["input"], direction)


@pytest.mark.parametrize("seed", [0, 17, 991])
def test_inputs_are_matched_across_settings(seed):
    prototype = _load()
    forward = prototype.generate_episode(seed, "blue_to_red", demos=6, queries=4)
    reverse = prototype.generate_episode(seed, "red_to_blue", demos=6, queries=4)
    assert [p["input"] for p in forward["train"] + forward["test"]] == [
        p["input"] for p in reverse["train"] + reverse["test"]
    ]


@pytest.mark.parametrize("seed", range(32))
@pytest.mark.parametrize("direction", ["blue_to_red", "red_to_blue"])
def test_two_demos_identify_setting_and_declared_rivals(seed, direction):
    prototype = _load()
    episode = prototype.generate_episode(seed, direction, demos=2, queries=4)
    assert prototype.teaching_survivors(episode["train"]) == [direction]
    assert all(
        prototype.solve(pair["input"], "blue_to_red")
        != prototype.solve(pair["input"], "red_to_blue")
        for pair in episode["test"]
    )


def test_sampler_exercises_overlap_clipping_and_large_connected_content():
    prototype = _load()
    episode = prototype.generate_episode(17, "blue_to_red", demos=6, queries=4)
    analyses = [prototype.analyze(pair["input"], "blue_to_red") for pair in episode["train"]]
    assert analyses[0]["target_source_overlap"]
    assert 0 < len(analyses[1]["visible_targets"]) < len(analyses[1]["source_cells"])
    largest = episode["test"][3]["input"]
    assert (len(largest), len(largest[0])) == (30, 30)
    green = {(r, c) for r, row in enumerate(largest) for c, value in enumerate(row) if value == 3}
    assert len(green) >= 80
    assert _connected(green)
    assert _nonzero(largest) >= 82
    assert any(largest[0][c] != 0 or largest[-1][c] != 0 for c in range(30))
    assert any(largest[r][0] != 0 or largest[r][-1] != 0 for r in range(30))


def test_public_first_turn_is_independent_of_future_queries():
    prototype = _load()
    from reviewer_support import public_challenge_bytes, public_challenge_id

    one = prototype.generate_episode(4, "red_to_blue", demos=3, queries=1)
    four = prototype.generate_episode(4, "red_to_blue", demos=3, queries=4)
    def public(ep):
        return {"train": ep["train"], "test": [{"input": ep["test"][0]["input"]}]}
    assert public_challenge_bytes(public(one)) == public_challenge_bytes(public(four))
    assert public_challenge_id(public(one)) == public_challenge_id(public(four))


@pytest.mark.parametrize(
    "args",
    [
        (-1, "blue_to_red", 2, 1),
        (2**63, "blue_to_red", 2, 1),
        (0, "blue_to_red", 1, 1),
        (0, "blue_to_red", 7, 1),
        (0, "blue_to_red", 2, 0),
        (0, "blue_to_red", 2, 5),
        (0, "bad", 2, 1),
        (True, "blue_to_red", 2, 1),
    ],
)
def test_invalid_requests_are_rejected(args):
    prototype = _load()
    with pytest.raises(ValueError):
        prototype.generate_episode(*args)


def test_thin_adapter_returns_only_native_contract_fields():
    path = PARAM / "adapter.py"
    spec = importlib.util.spec_from_file_location("_test_vector_adapter", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    result = module.generate(0, {"vector_direction": "blue_to_red"}, 2, 4)
    assert set(result) == {"train", "test", "program_solution"}
    assert len(result["train"]) == 2 and len(result["test"]) == 4
