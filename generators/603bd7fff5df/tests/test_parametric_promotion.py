"""Native promotion contract for the halo-depth parametric family."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import canonical_path, find_root, public_challenge_bytes, public_challenge_id

TASK_ID = "603bd7fff5df"
HOME = Path(__file__).resolve().parents[1]
PROTO = HOME / "workspace" / "parametric"
ROOT = find_root(__file__)


def load(name: str):
    path = PROTO / f"{name}.py"
    assert path.is_file(), f"missing parametric {name}.py"
    spec = importlib.util.spec_from_file_location(f"tested_{TASK_ID}_{name}", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def authority_program() -> str:
    programs = {
        row["program_solution"]
        for row in map(json.loads, canonical_path(ROOT).read_text(encoding="utf-8").splitlines())
        if row.get("task_id") == TASK_ID
    }
    assert len(programs) == 1
    return programs.pop()


def all_inputs(episode):
    return [pair["input"] for split in ("train", "test") for pair in episode[split]]


def frozen(grid):
    return tuple(tuple(row) for row in grid)


def test_native_contract_and_exact_canonical_default():
    adapter = load("adapter")
    contract = json.loads((PROTO / "promotion.json").read_text(encoding="utf-8"))
    assert contract == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": f"generators/{TASK_ID}/workspace/parametric/adapter.py",
        "parameters": {"halo_depth": [0, 1, 2]},
        "default": {"halo_depth": 1},
        "limits": {"demos": [2, 6], "queries": [1, 4]},
        "qualification_demos": 3,
        "resources": [
            f"generators/{TASK_ID}/workspace/parametric/canonical.rkt",
            f"generators/{TASK_ID}/workspace/parametric/halo-depth-0.rkt",
            f"generators/{TASK_ID}/workspace/parametric/halo-depth-2.rkt",
            f"generators/{TASK_ID}/workspace/parametric/prototype.py",
        ],
    }
    assert adapter.program({"halo_depth": 1}) == authority_program()
    programs = [adapter.program({"halo_depth": depth}) for depth in (0, 1, 2)]
    assert len(set(programs)) == 3


@pytest.mark.parametrize("demos", range(2, 7))
def test_counts_matched_inputs_stable_prefixes_and_teaching(demos):
    adapter, prototype = load("adapter"), load("prototype")
    episodes = {
        depth: adapter.generate(17, {"halo_depth": depth}, demos, 4)
        for depth in (0, 1, 2)
    }
    one_query = adapter.generate(17, {"halo_depth": 1}, demos, 1)
    fewer_demos = adapter.generate(17, {"halo_depth": 1}, 2, 4)

    for depth, episode in episodes.items():
        assert episode["settings"] == {"halo_depth": depth}
        assert episode["seed"] == 17
        assert episode["program_solution"] == adapter.program({"halo_depth": depth})
        assert len(episode["train"]) == demos
        assert len(episode["test"]) == 4
        assert prototype.teaching_certificate(episode) == {
            "setting_survivors": [depth],
            "plausible_rival_survivors": [],
        }

    reference_inputs = all_inputs(episodes[1])
    assert all(all_inputs(episode) == reference_inputs for episode in episodes.values())
    assert len({frozen(grid) for grid in reference_inputs}) == demos + 4
    assert one_query["train"] == episodes[1]["train"]
    assert one_query["test"] == episodes[1]["test"][:1]
    assert fewer_demos["train"] == episodes[1]["train"][:2]
    assert fewer_demos["test"] == episodes[1]["test"]

    for split in ("train", "test"):
        for index in range(len(episodes[1][split])):
            outputs = [episodes[depth][split][index]["output"] for depth in (0, 1, 2)]
            assert len({frozen(output) for output in outputs}) == 3


def test_fourth_query_is_substantive_30x30_stress_case():
    adapter, prototype = load("adapter"), load("prototype")
    episodes = {
        depth: adapter.generate(91, {"halo_depth": depth}, 3, 4)
        for depth in (0, 1, 2)
    }
    grid = episodes[1]["test"][-1]["input"]
    assert all(episode["test"][-1]["input"] == grid for episode in episodes.values())
    assert (len(grid), len(grid[0])) == (30, 30)
    assert {value for row in grid for value in row} == {0, 5, 8}
    assert sum(value == 8 for row in grid for value in row) >= 70
    r0, c0, r1, c1 = prototype.gray_bbox(grid)
    assert r0 >= 2 and r1 + 2 < 30
    assert r1 - r0 >= 14 and c1 - c0 >= 16
    assert any(grid[r0 - 2][col] == 8 for col in range(c0, c1 + 1))
    assert any(grid[r1 + 2][col] == 8 for col in range(c0, c1 + 1))
    assert [len(episodes[d]["test"][-1]["output"]) for d in (0, 1, 2)] == [
        r1 - r0 + 1,
        r1 - r0 + 3,
        r1 - r0 + 5,
    ]


def test_public_projection_hides_settings_programs_and_query_answers():
    adapter, prototype = load("adapter"), load("prototype")
    episode = adapter.generate(23, {"halo_depth": 2}, 3, 4)
    turn = prototype.public_turn(episode, 0)
    assert set(turn) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in turn["train"])
    assert turn["test"] == [{"input": episode["test"][0]["input"]}]

    changed = deepcopy(episode)
    changed["settings"] = {"private": "changed"}
    changed["program_solution"] = "PRIVATE CHANGED PROGRAM"
    changed["seed"] = 999
    for pair in changed["test"]:
        pair["output"] = [[9]]
    assert prototype.public_turn(changed, 0) == turn
    assert public_challenge_bytes(changed) == public_challenge_bytes(episode)
    assert public_challenge_id(changed) == public_challenge_id(episode)


def test_dependency_metadata_and_wrong_bbox_counterfactual_change_output():
    prototype = load("prototype")
    witness = prototype.dependency_case(seed=91, halo_depth=2)
    assert witness["step_a"] == "locate every gray side marker and compute their bounding box"
    assert witness["intermediate"] == "gray_bbox=(top,left,bottom,right)"
    assert witness["step_b"].startswith("expand the bbox row interval by the episode halo_depth")
    assert witness["correct_intermediate"] != witness["wrong_intermediate"]
    assert witness["output"] != witness["counterfactual_output"]
    assert witness["program"] == prototype.program_for(2)
    assert witness["counterfactual_program"] != witness["program"]


@pytest.mark.parametrize(
    "changes",
    [
        {"seed": True},
        {"seed": -1},
        {"seed": 2**63},
        {"settings": {}},
        {"settings": {"halo_depth": 1, "extra": 0}},
        {"settings": {"halo_depth": True}},
        {"settings": {"halo_depth": -1}},
        {"settings": {"halo_depth": 3}},
        {"demos": 1},
        {"demos": 7},
        {"queries": 0},
        {"queries": 5},
        {"demos": True},
        {"queries": 1.0},
    ],
)
def test_invalid_native_requests_fail_closed(changes):
    adapter = load("adapter")
    kwargs = dict(seed=0, settings={"halo_depth": 1}, demos=3, queries=4)
    kwargs.update(changes)
    with pytest.raises((TypeError, ValueError)):
        adapter.generate(**kwargs)


def test_reusable_audit_tool_smoke():
    audit = load("audit")
    report = audit.run_audit(seeds=range(3), demo_counts=(2, 6))
    assert report["status"] == "passed"
    assert report["counts"] == {
        "seeds": 3,
        "demo_counts": 2,
        "settings": 3,
        "episodes": 18,
        "pairs": 144,
        "thirty_by_thirty_queries": 18,
    }
    assert report["failures"] == []
