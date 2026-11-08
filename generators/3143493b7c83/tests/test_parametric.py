"""Native contains-versus-exact-bbox parametric family for 3143493b7c83."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root, public_challenge_bytes, public_challenge_id

TASK_ID = "3143493b7c83"
HOME = Path(__file__).resolve().parents[1]
ROOT = find_root(__file__)
PROTO = HOME / "workspace" / "parametric"


def load(name="adapter"):
    path = PROTO / f"{name}.py"
    assert path.is_file(), f"missing parametric {name}.py"
    spec = importlib.util.spec_from_file_location(f"tested_3143493b7c83_{name}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def all_inputs(episode):
    return [pair["input"] for split in ("train", "test") for pair in episode[split]]


def authority_program():
    programs = {
        row["program_solution"]
        for row in map(
            json.loads,
            (ROOT / "shared/data/canonical/puzzles.jsonl").read_text().splitlines(),
        )
        if row.get("task_id") == TASK_ID
    }
    assert len(programs) == 1
    return programs.pop()


def test_default_program_is_exact_selected_authority():
    adapter = load()
    canonical = authority_program()
    assert adapter.program({"match_mode": "contains"}) == canonical
    alternate = adapter.program({"match_mode": "exact_bbox"})
    assert alternate != canonical
    assert "template-on?" in alternate


@pytest.mark.parametrize("demos", range(2, 7))
def test_counts_matched_inputs_prefix_identification_and_public_projection(demos):
    adapter, proto = load(), load("prototype")
    contains = adapter.generate(17, {"match_mode": "contains"}, demos, 4)
    exact = adapter.generate(17, {"match_mode": "exact_bbox"}, demos, 4)
    single = adapter.generate(17, {"match_mode": "contains"}, demos, 1)

    assert len(contains["train"]) == demos and len(contains["test"]) == 4
    assert contains["train"] == single["train"]
    assert contains["test"][:1] == single["test"]
    assert all_inputs(contains) == all_inputs(exact)
    assert len({json.dumps(grid, separators=(",", ":")) for grid in all_inputs(contains)}) == demos + 4
    assert all(
        a["output"] != b["output"]
        for split in ("train", "test")
        for a, b in zip(contains[split], exact[split])
    )
    assert proto.teaching_certificate(contains)["setting_survivors"] == ["contains"]
    assert proto.teaching_certificate(exact)["setting_survivors"] == ["exact_bbox"]
    assert proto.teaching_certificate(contains)["plausible_rival_survivors"] == []
    assert proto.teaching_certificate(exact)["plausible_rival_survivors"] == []

    first_turn = {"train": contains["train"], "test": [contains["test"][0]]}
    assert proto.visible_turn(contains, 0) == public_challenge_bytes(first_turn)
    changed = deepcopy(contains)
    changed["program_solution"] = "private"
    for pair in changed["test"]:
        pair["output"] = [[9]]
    assert public_challenge_bytes(changed) == public_challenge_bytes(contains)
    assert public_challenge_id(changed) == public_challenge_id(contains)


def test_fourth_query_is_substantive_30x30_boundary_stress():
    adapter = load()
    contains = adapter.generate(91, {"match_mode": "contains"}, 3, 4)
    exact = adapter.generate(91, {"match_mode": "exact_bbox"}, 3, 4)
    cin = contains["test"][-1]["input"]
    cout = contains["test"][-1]["output"]
    eout = exact["test"][-1]["output"]
    assert (len(cin), len(cin[0])) == (30, 30)
    changed = [(r, c) for r in range(30) for c in range(30) if cout[r][c] != cin[r][c]]
    disagreement = [(r, c) for r in range(30) for c in range(30) if cout[r][c] != eout[r][c]]
    assert len(changed) >= 18
    assert len(disagreement) >= 6
    assert max(r for r, _ in changed) - min(r for r, _ in changed) >= 16
    assert max(c for _, c in changed) - min(c for _, c in changed) >= 16


def test_python_contains_mirror_covers_all_canonical_pairs():
    proto = load("prototype")
    for pair in canonical_pairs(TASK_ID, root=ROOT, labeled_only=True):
        assert proto.transform(pair["input"], {"match_mode": "contains"}) == pair["output"]


def test_sequential_dependency_witness_changes_output_under_wrong_intermediate():
    proto = load("prototype")
    witness = proto.dependency_witness()
    assert witness["step_a"] == "extract the 2x-upscaled marker bitmap"
    assert witness["intermediate"] == "ordered key offsets inside the marker bounding box"
    assert witness["step_b"].startswith("scan 4-aligned lattice cells")
    assert witness["correct_intermediate"] != witness["wrong_intermediate"]
    assert witness["correct_output"] != witness["wrong_intermediate_output"]
    assert witness["skip_a_output"] != witness["correct_output"]


@pytest.mark.parametrize(
    "changes",
    [
        {"seed": True},
        {"seed": -1},
        {"seed": 2**63},
        {"settings": {}},
        {"settings": {"match_mode": "approx"}},
        {"settings": {"match_mode": "contains", "extra": 1}},
        {"demos": 1},
        {"demos": 7},
        {"queries": 0},
        {"queries": 5},
    ],
)
def test_invalid_controls_fail(changes):
    adapter = load()
    kwargs = dict(seed=17, settings={"match_mode": "contains"}, demos=3, queries=4)
    kwargs.update(changes)
    with pytest.raises(ValueError):
        adapter.generate(**kwargs)
