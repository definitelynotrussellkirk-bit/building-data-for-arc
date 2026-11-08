from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from arcpuzzles import Catalog
from reviewer_support import public_challenge_bytes, public_challenge_id


TASK_ID = "a80c6418f6bc"
TASK_HOME = Path(__file__).resolve().parents[1]
PARAMETRIC = TASK_HOME / "workspace" / "parametric"
PROTOTYPE = PARAMETRIC / "prototype.py"
ADAPTER = PARAMETRIC / "adapter.py"
PROMOTION = PARAMETRIC / "promotion.json"
REPO = TASK_HOME.parents[1]


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _prototype():
    return _load("_a80c6418f6bc_parametric_test_prototype", PROTOTYPE)


def _adapter():
    return _load("_a80c6418f6bc_parametric_test_adapter", ADAPTER)


def _canonical_program() -> str:
    record = Catalog(REPO).get(TASK_ID)
    programs = {
        variant["program_solution"]
        for variant in record["variants"]
        if isinstance(variant.get("program_solution"), str)
    }
    assert len(programs) == 1
    return next(iter(programs))


def _inputs(episode: dict) -> list:
    return [pair["input"] for split in ("train", "test") for pair in episode[split]]


def test_default_program_is_exact_canonical_and_alternate_is_bounded_edit():
    p = _prototype()
    canonical = _canonical_program()
    direct = p.program({"orientation": "direct"})
    rotated = p.program({"orientation": "rotate_180"})

    assert direct == canonical
    assert (PARAMETRIC / "canonical.rkt").read_bytes() == canonical.encode("utf-8")
    assert rotated != direct
    assert "(- edit-h 1 (first add))" in rotated
    assert "(- edit-w 1 (second add))" in rotated
    assert hashlib.sha256(direct.encode()).hexdigest() == p.program_hash("direct")
    assert hashlib.sha256(rotated.encode()).hexdigest() == p.program_hash("rotate_180")


def test_promotion_contract_and_thin_adapter_support_required_counts():
    p = _prototype()
    adapter = _adapter()
    contract = json.loads(PROMOTION.read_text())
    assert contract == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": "generators/a80c6418f6bc/workspace/parametric/adapter.py",
        "parameters": {"orientation": ["direct", "rotate_180"]},
        "default": {"orientation": "direct"},
        "qualification_demos": 3,
        "limits": {"demos": [2, 6], "queries": [1, 4]},
        "resources": [
            "generators/a80c6418f6bc/workspace/parametric/canonical.rkt",
            "generators/a80c6418f6bc/workspace/parametric/rotate_180.rkt",
        ],
    }
    for orientation in p.ORIENTATIONS:
        episode = adapter.generate(17, {"orientation": orientation}, 2, 4)
        assert set(episode) == {"train", "test", "program_solution"}
        assert len(episode["train"]) == 2
        assert len(episode["test"]) == 4
        assert episode["program_solution"] == adapter.program({"orientation": orientation})


@pytest.mark.parametrize("demos", range(2, 7))
def test_counts_are_independent_deterministic_prefix_stable_and_setting_matched(demos):
    p = _prototype()
    direct = p.generate(29, {"orientation": "direct"}, demos, 4)
    rotated = p.generate(29, {"orientation": "rotate_180"}, demos, 4)
    replay = p.generate(29, {"orientation": "direct"}, demos, 4)

    assert direct == replay
    assert direct is not replay
    assert _inputs(direct) == _inputs(rotated)
    assert len({p.grid_hash(grid) for grid in _inputs(direct)}) == demos + 4

    one_query = p.generate(29, {"orientation": "direct"}, demos, 1)
    assert one_query["train"] == direct["train"]
    assert one_query["test"] == direct["test"][:1]

    shorter = p.generate(29, {"orientation": "direct"}, 2, 4)
    assert shorter["train"] == direct["train"][:2]
    assert shorter["test"] == direct["test"]


@pytest.mark.parametrize("orientation", ("direct", "rotate_180"))
def test_python_claims_match_solver_and_all_inputs_validate(orientation):
    p = _prototype()
    for seed in (0, 17, 91):
        episode = p.generate(seed, {"orientation": orientation}, 6, 4)
        for pair in episode["train"] + episode["test"]:
            facts = p.analyze(pair["input"])
            assert facts["errors"] == []
            assert pair["output"] == p.solve_python(pair["input"], orientation)
            assert facts["delta"]
            assert facts["delta"] != facts["rotated_delta"]


def test_first_two_demonstrations_refute_declared_rivals_for_bounded_seeds():
    p = _prototype()
    for seed in range(24):
        for orientation in p.ORIENTATIONS:
            episode = p.generate(seed, {"orientation": orientation}, 2, 4)
            intended_demos = [pair["output"] for pair in episode["train"]]
            intended_queries = [pair["output"] for pair in episode["test"]]
            for name, rival in p.declared_rivals(orientation).items():
                rival_demos = [rival(pair["input"]) for pair in episode["train"]]
                rival_queries = [rival(pair["input"]) for pair in episode["test"]]
                assert rival_demos != intended_demos, (seed, orientation, name)
                assert rival_queries != intended_queries, (seed, orientation, name)


def test_demonstrations_cover_two_axis_expansion_before_queries():
    p = _prototype()
    episode = p.generate(0, {"orientation": "direct"}, 2, 4)
    demo_modes = [p.analyze(pair["input"])["delta_mode"] for pair in episode["train"]]
    assert demo_modes == ["within_bbox", "expand_both"]
    assert all(
        p.analyze(pair["input"])["delta_mode"]
        in {"within_bbox", "expand_right", "expand_down", "expand_both"}
        for pair in episode["test"]
    )


def test_fourth_query_is_substantive_30_by_30_with_boundary_contact():
    p = _prototype()
    pair = p.generate(17, {"orientation": "rotate_180"}, 3, 4)["test"][3]
    grid = pair["input"]
    facts = p.analyze(grid)
    assert (len(grid), len(grid[0])) == (30, 30)
    assert facts["separator"] == (14, 14)
    occupied = facts["a_info"]["cells"] | facts["b_info"]["cells"] | facts["c_info"]["cells"]
    assert len(occupied) >= 80
    global_cells = p.non_separator_nonzero_cells(grid)
    assert any(r in (0, 29) or c in (0, 29) for r, c in global_cells)
    assert len({r for r, _ in global_cells}) >= 24
    assert len({c for _, c in global_cells}) >= 24


def test_public_projection_uses_only_visible_bytes_and_hides_future_answers():
    p = _prototype()
    episode = p.generate(17, {"orientation": "direct"}, 3, 4)
    visible = {"train": episode["train"], "test": episode["test"][:1]}
    identifier = public_challenge_id(visible)
    assert identifier == p.public_id(episode, query_count=1)

    hidden = copy.deepcopy(visible)
    hidden["settings"] = {"orientation": "rotate_180"}
    hidden["program_solution"] = "private"
    hidden["test"][0]["output"] = [[9]]
    assert public_challenge_bytes(hidden) == public_challenge_bytes(visible)

    changed = copy.deepcopy(visible)
    changed["test"][0]["input"][0][0] = (changed["test"][0]["input"][0][0] + 1) % 10
    assert public_challenge_bytes(changed) != public_challenge_bytes(visible)


@pytest.mark.parametrize(
    ("settings", "demos", "queries"),
    [
        ({}, 3, 4),
        ({"orientation": "unknown"}, 3, 4),
        ({"orientation": "direct", "extra": 1}, 3, 4),
        ({"orientation": "direct"}, 1, 4),
        ({"orientation": "direct"}, 7, 4),
        ({"orientation": "direct"}, 3, 0),
        ({"orientation": "direct"}, 3, 5),
        ({"orientation": "direct"}, True, 4),
        ({"orientation": "direct"}, 3, 4.0),
    ],
)
def test_invalid_settings_and_count_requests_are_rejected(settings, demos, queries):
    p = _prototype()
    with pytest.raises(ValueError):
        p.generate(0, settings, demos, queries)


def test_wrong_intermediate_ablation_changes_final_output():
    p = _prototype()
    pair = p.generate(17, {"orientation": "rotate_180"}, 3, 4)["test"][0]
    intended = pair["output"]
    wrong = p.solve_with_delta(pair["input"], "rotate_180", {(0, 0)})
    assert wrong != intended
