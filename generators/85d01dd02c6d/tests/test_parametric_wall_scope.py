"""Native parametric wall-scope family for ray-overlap task 85d01dd02c6d."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from arcpuzzles.parametric_worker import evaluate_contract
from reviewer_support import canonical_path, find_root, public_challenge_bytes


TASK_ID = "85d01dd02c6d"
HOME = Path(__file__).resolve().parents[1]
ROOT = find_root(__file__)
PARAMETRIC = HOME / "workspace" / "parametric"
SETTINGS = (
    {"wall_scope": "every_wall"},
    {"wall_scope": "axis_dividers"},
)


def _load(path: Path, name: str):
    assert path.is_file(), f"missing required parametric source: {path}"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_adapter():
    return _load(PARAMETRIC / "adapter.py", "tested_85d01dd02c6d_adapter")


def load_prototype():
    return _load(PARAMETRIC / "prototype.py", "tested_85d01dd02c6d_prototype")


def load_audit():
    return _load(PARAMETRIC / "audit_lessons.py", "tested_85d01dd02c6d_audit")


def canonical_program() -> str:
    programs = {
        row["program_solution"]
        for line in canonical_path(ROOT).read_text().splitlines()
        if (row := json.loads(line)).get("task_id") == TASK_ID
    }
    assert len(programs) == 1
    return programs.pop()


def _inputs(episode):
    return [pair["input"] for split in ("train", "test") for pair in episode[split]]


def _interior_quadrant_counts(grid):
    height, width = len(grid), len(grid[0])
    mid_r, mid_c = height // 2, width // 2
    quadrants = (
        (range(1, mid_r), range(1, mid_c)),
        (range(1, mid_r), range(mid_c, width - 1)),
        (range(mid_r, height - 1), range(1, mid_c)),
        (range(mid_r, height - 1), range(mid_c, width - 1)),
    )
    return [sum(grid[r][c] != 0 for r in rows for c in cols) for rows, cols in quadrants]


def test_default_program_is_exact_canonical_and_alternative_is_distinct():
    adapter = load_adapter()
    assert adapter.program(SETTINGS[0]) == canonical_program()
    assert adapter.program(SETTINGS[1]) != canonical_program()
    assert adapter.program(SETTINGS[1]).startswith("(rule!")


@pytest.mark.parametrize("demos", range(2, 7))
def test_counts_matched_inputs_prefix_stability_and_30x30_stress(demos):
    adapter = load_adapter()
    canonical = adapter.generate(17, SETTINGS[0], demos=demos, queries=4)
    divider_only = adapter.generate(17, SETTINGS[1], demos=demos, queries=4)
    first_query = adapter.generate(17, SETTINGS[0], demos=demos, queries=1)

    assert len(canonical["train"]) == demos
    assert len(canonical["test"]) == 4
    assert canonical["train"] == first_query["train"]
    assert canonical["test"][:1] == first_query["test"]
    assert _inputs(canonical) == _inputs(divider_only)
    assert len({json.dumps(grid, separators=(",", ":")) for grid in _inputs(canonical)}) == demos + 4
    assert all(
        left["output"] != right["output"]
        for split in ("train", "test")
        for left, right in zip(canonical[split], divider_only[split], strict=True)
    )

    visible = json.loads(public_challenge_bytes(canonical))
    assert len(visible["train"]) == demos
    assert len(visible["test"]) == 4
    assert all(set(pair) == {"input"} for pair in visible["test"])
    assert "program_solution" not in visible and "settings" not in visible

    large = canonical["test"][-1]["input"]
    assert (len(large), len(large[0])) == (30, 30)
    assert sum(cell != 0 for row in large for cell in row) >= 150
    assert all(count > 0 for count in _interior_quadrant_counts(large))


def test_first_two_demonstrations_cover_both_orientations_and_all_required_witnesses():
    prototype = load_prototype()
    episode = prototype.generate(0, SETTINGS[0], demos=2, queries=4)
    analyses = [prototype.analyze_scene(pair["input"]) for pair in episode["train"]]
    assert {row["full_divider_orientation"] for row in analyses} == {"vertical", "horizontal"}
    assert {row["partial_wall_orientation"] for row in analyses} == {"vertical", "horizontal"}
    for row in analyses:
        assert row["clear_overlap_witness"]
        assert row["full_divider_blocked_witness"]
        assert row["partial_wall_setting_witness"]


@pytest.mark.parametrize("demos", (2, 3, 6))
def test_public_controller_reveals_one_query_without_future_hints(demos):
    prototype = load_prototype()
    full = prototype.generate(29, SETTINGS[1], demos=demos, queries=4)
    one = prototype.generate(29, SETTINGS[1], demos=demos, queries=1)
    turns = prototype.controller_turns(full)
    assert len(turns) == 4
    assert turns[0] == prototype.public_challenge(one)
    assert all(len(turn["test"]) == 1 for turn in turns)
    assert all("program_solution" not in turn and "settings" not in turn for turn in turns)
    assert [turn["test"][0] for turn in turns] == prototype.public_challenge(full)["test"]


def test_protected_racket_labels_and_demo_only_setting_identification():
    contract = json.loads((PARAMETRIC / "promotion.json").read_text())
    jobs = [
        {"seed": seed, "settings": setting, "demos": demos, "queries": 4}
        for seed, demos in ((0, 2), (17, 6))
        for setting in SETTINGS
    ]
    result = evaluate_contract(ROOT, TASK_ID, contract, jobs)
    assert result["racket"] == {**result["racket"], "backend": "racket", "protected": True}
    assert [check["survivors"] for check in result["checks"]] == [
        [job["settings"]] for job in jobs
    ]
    assert result["racket_evaluations"] >= sum(job["demos"] + job["queries"] for job in jobs)


def test_racket_backed_self_audit_refutes_finite_plausible_rivals():
    report = load_audit().build_report(seeds=(0, 17), demos=2, queries=4, execute_racket=True)
    assert report["schema"] == "arcpuzzles-ray-wall-scope-self-audit-v1"
    assert report["racket"] == {**report["racket"], "backend": "racket", "protected": True}
    assert report["ambiguous_rivals"] == []
    assert report["labels_checked"] == 24
    for episode in report["episodes"]:
        assert episode["selected_labels_match"] is True
        assert all(rival["demo_mismatches"] > 0 for rival in episode["rivals"])
    assert report["large_query"]["shape"] == [30, 30]
    assert all(value > 0 for value in report["large_query"]["interior_nonzero_by_quadrant"])


@pytest.mark.parametrize(
    "patch",
    [
        {"seed": True}, {"seed": -1}, {"seed": 2**63}, {"seed": 1.0},
        {"settings": {}}, {"settings": {"wall_scope": True}},
        {"settings": {"wall_scope": "all"}},
        {"settings": {"wall_scope": "every_wall", "extra": 1}},
        {"demos": 1}, {"demos": 7}, {"demos": True}, {"demos": 3.0},
        {"queries": 0}, {"queries": 5}, {"queries": True}, {"queries": 4.0},
    ],
)
def test_invalid_controls_fail_before_generation(patch):
    request = {"seed": 17, "settings": SETTINGS[0], "demos": 3, "queries": 4}
    request.update(patch)
    with pytest.raises(ValueError):
        load_adapter().generate(**request)
