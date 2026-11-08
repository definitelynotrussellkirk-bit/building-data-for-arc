"""Promotion regressions for the exact-pass midpoint cascade family."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import sys

import pytest

from reviewer_support import canonical_path, find_root

TASK_ID = "fe54bfae4cee"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK_ID / "workspace" / "parametric"
PROTOTYPE_PATH = HOME / "prototype.py"
ADAPTER_PATH = HOME / "adapter.py"


def _load(path: Path, name: str):
    assert path.is_file(), f"missing implementation: {path}"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _prototype():
    return _load(PROTOTYPE_PATH, "fe54bfae4cee_parametric_prototype_test")


def _adapter():
    return _load(ADAPTER_PATH, "fe54bfae4cee_parametric_adapter_test")


def _canonical_program() -> str:
    programs = {
        row["program_solution"]
        for line in canonical_path(ROOT).read_text(encoding="utf-8").splitlines()
        if line.strip()
        if (row := json.loads(line)).get("task_id") == TASK_ID
    }
    assert len(programs) == 1
    return programs.pop()


def _all_pairs(episode):
    return episode["train"] + episode["test"]


def _inputs(episode):
    return [pair["input"] for pair in _all_pairs(episode)]


def _changed(left, right):
    return {
        (r, c)
        for r, row in enumerate(left)
        for c, value in enumerate(row)
        if right[r][c] != value
    }


def test_default_program_is_byte_exact_canonical_and_two_pass_is_distinct():
    adapter = _adapter()
    canonical = _canonical_program()
    assert adapter.program({"passes": 1}) == canonical
    assert adapter.program({"passes": 2}) != canonical
    assert adapter.program({"passes": 2}).startswith("(rule!")


@pytest.mark.parametrize(
    "settings",
    [None, {}, {"passes": True}, {"passes": 0}, {"passes": 3}, {"passes": "2"}, {"passes": 1, "extra": 0}],
)
def test_invalid_settings_reject_loudly(settings):
    adapter = _adapter()
    with pytest.raises(ValueError):
        adapter.program(settings)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"demos": 1, "queries": 4},
        {"demos": 7, "queries": 4},
        {"demos": 3, "queries": 3},
        {"demos": 3, "queries": 5},
        {"demos": True, "queries": 4},
        {"demos": 3, "queries": 4.0},
    ],
)
def test_episode_count_contract_rejects_out_of_scope_requests(kwargs):
    adapter = _adapter()
    with pytest.raises(ValueError):
        adapter.generate(0, {"passes": 1}, **kwargs)


def test_paired_settings_share_distinct_inputs_and_every_demo_identifies_pass_count():
    adapter = _adapter()
    one = adapter.generate(17, {"passes": 1}, demos=3, queries=4)
    two = adapter.generate(17, {"passes": 2}, demos=3, queries=4)

    assert _inputs(one) == _inputs(two)
    assert len(one["train"]) == len(two["train"]) == 3
    assert len(one["test"]) == len(two["test"]) == 4
    serialized = [json.dumps(grid, separators=(",", ":")) for grid in _inputs(one)]
    assert len(serialized) == len(set(serialized)) == 7
    assert all(a["output"] != b["output"] for a, b in zip(_all_pairs(one), _all_pairs(two)))
    assert one["program_solution"] == adapter.program({"passes": 1})
    assert two["program_solution"] == adapter.program({"passes": 2})


def test_exact_depth_three_teaches_one_vs_two_vs_unbounded_closure():
    prototype = _prototype()
    grid = prototype.build_input(seed=5, slot=0)
    stage1 = prototype.apply_passes(grid, 1)
    stage2 = prototype.apply_passes(grid, 2)
    stage3 = prototype.apply_passes(grid, 3)
    stage4 = prototype.apply_passes(grid, 4)

    assert _changed(grid, stage1)
    assert _changed(stage1, stage2)
    assert _changed(stage2, stage3)
    assert stage4 == stage3
    assert prototype.apply_until_stable(grid) == stage3
    assert grid == prototype.build_input(seed=5, slot=0)


def test_episode_counts_are_independent_and_query_profiles_are_fixed():
    adapter = _adapter()
    short = adapter.generate(31, {"passes": 2}, demos=2, queries=4)
    long = adapter.generate(31, {"passes": 2}, demos=6, queries=4)

    assert _inputs(short)[:2] == _inputs(long)[:2]
    assert [pair["input"] for pair in short["test"]] == [pair["input"] for pair in long["test"]]
    assert len(short["train"]) == 2
    assert len(long["train"]) == 6
    assert len(short["test"]) == len(long["test"]) == 4


def test_four_queries_include_substantive_exact_30_by_30_stress():
    adapter = _adapter()
    episode = adapter.generate(101, {"passes": 2}, demos=3, queries=4)
    stress = episode["test"][-1]["input"]
    assert (len(stress), len(stress[0])) == (30, 30)
    nonzero = [(r, c) for r, row in enumerate(stress) for c, value in enumerate(row) if value]
    assert len(nonzero) >= 20
    quadrants = {
        (r >= 15, c >= 15)
        for r, c in nonzero
    }
    assert quadrants == {(False, False), (False, True), (True, False), (True, True)}


def test_outputs_are_fresh_exact_integer_grids_and_input_is_not_mutated():
    prototype = _prototype()
    grid = prototype.build_input(seed=7, slot=9)
    before = copy.deepcopy(grid)
    out = prototype.apply_passes(grid, 2)
    assert grid == before
    assert out is not grid
    assert all(type(cell) is int and 0 <= cell <= 9 for row in out for cell in row)
    out[0][0] = 9 if out[0][0] != 9 else 8
    assert grid == before


def test_public_projection_masks_settings_program_seed_and_query_answers():
    prototype = _prototype()
    episode = prototype.generate_episode(11, passes=2, demos=3, queries=4)
    public = prototype.public_challenge(episode)
    assert set(public) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])
    serialized = json.dumps(public, sort_keys=True)
    for forbidden in ("passes", "settings", "seed", "program", "program_solution", "output\":"):
        if forbidden == "output\":" :
            continue
        assert forbidden not in serialized
    assert all("output" not in pair for pair in public["test"])


def test_declared_shortcuts_are_refuted_by_demonstrations_and_queries():
    prototype = _prototype()
    for passes in (1, 2):
        episode = prototype.generate_episode(23, passes=passes, demos=3, queries=4)
        audit = prototype.audit_episode(episode)
        assert audit["chosen"] == f"passes_{passes}"
        assert audit["survivors"] == [f"passes_{passes}"]
        assert audit["ambiguous_query_changers"] == []
        by_name = {row["name"]: row for row in audit["rivals"]}
        for name in ("identity", "passes_1", "passes_2", "closure", "horizontal_only", "vertical_only"):
            assert name in by_name
        for name, row in by_name.items():
            if name == f"passes_{passes}":
                assert row["demo_mismatches"] == []
            else:
                assert row["demo_mismatches"], name


def test_evidence_builder_emits_schema_bound_witness_and_hash_named_public_file(tmp_path):
    builder_path = HOME / "build_evidence.py"
    builder = _load(builder_path, "fe54bfae4cee_evidence_builder_test")
    prototype = _prototype()
    episode = prototype.generate_episode(3, passes=2, demos=3, queries=4)
    public_path = builder.write_public_episode(episode, tmp_path)
    raw = public_path.read_bytes()
    import hashlib

    assert public_path.name == f"challenge-{hashlib.sha256(raw).hexdigest()}.json"
    visible = json.loads(raw)
    assert all("output" not in pair for pair in visible["test"])

    case = {
        "input": [[1, 0, 1], [0, 0, 0], [0, 1, 0]],
        "settings": {"passes": 2},
        "intermediate_value": [[1, 1, 1], [0, 0, 0], [0, 1, 0]],
        "program": prototype.program_for(2),
        "output": [[1, 1, 1], [0, 1, 0], [0, 1, 0]],
        "ablation": "skip_a",
        "counterfactual_program": prototype.program_for(1),
        "counterfactual_output": [[1, 1, 1], [0, 0, 0], [0, 1, 0]],
    }
    witness = builder.witness_document({"task_id": TASK_ID}, [case])
    assert witness["schema"] == "arcpuzzles-sequential-dependency-witness-v1"
    assert witness["source_binding"] == {"task_id": TASK_ID}
    assert witness["racket"] == {"backend": "racket", "protected": True}
    assert witness["cases"] == [case]
    for key in ("step_a", "intermediate", "step_b", "why_b_depends_on_a"):
        assert witness[key]
