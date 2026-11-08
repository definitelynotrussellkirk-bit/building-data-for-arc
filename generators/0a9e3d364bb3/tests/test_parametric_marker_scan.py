from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest
from reviewer_support import canonical_path, find_root, public_challenge_bytes

TASK = "0a9e3d364bb3"
TASK_ROOT = Path(__file__).resolve().parents[1]
PARAMETRIC = TASK_ROOT / "workspace" / "parametric"
SETTINGS = ("forward", "reverse")


def _load(name: str = "prototype.py"):
    path = PARAMETRIC / name
    assert path.is_file(), f"missing {path}"
    spec = importlib.util.spec_from_file_location(f"_{TASK}_{path.stem}_test", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_program() -> str:
    root = find_root(__file__)
    matches = []
    for line in canonical_path(root).read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK and isinstance(row.get("program_solution"), str):
            matches.append(row["program_solution"])
    assert len(set(matches)) == 1
    return matches[0]


def _inputs(episode):
    return [pair["input"] for split in ("train", "test") for pair in episode[split]]


def test_default_program_is_byte_exact_and_reverse_program_is_distinct():
    p = _load()
    forward = p.program({"marker_scan": "forward"})
    reverse = p.program({"marker_scan": "reverse"})
    assert forward == _canonical_program()
    assert reverse != forward
    assert reverse.strip().startswith("(rule!")


def test_generate_rejects_coercible_controls_and_bad_settings():
    p = _load()
    good = {"marker_scan": "forward"}
    for settings in (
        None,
        {},
        {"marker_scan": "typo"},
        {"marker_scan": True},
        {"marker_scan": "forward", "extra": 1},
    ):
        with pytest.raises((TypeError, ValueError)):
            p.program(settings)
        with pytest.raises((TypeError, ValueError)):
            p.generate(0, settings, 3, 4)
    for seed in (-1, 2**63, True, 0.0, "0"):
        with pytest.raises((TypeError, ValueError)):
            p.generate(seed, good, 3, 4)
    for demos, queries in (
        (1, 4),
        (7, 4),
        (True, 4),
        (3.0, 4),
        (3, 0),
        (3, 5),
        (3, True),
        (3, 4.0),
    ):
        with pytest.raises((TypeError, ValueError)):
            p.generate(0, good, demos, queries)
    assert len(p.generate(2**63 - 1, good, 2, 1)["test"]) == 1


@pytest.mark.parametrize("demos", range(2, 7))
def test_inputs_are_setting_neutral_distinct_deterministic_and_prefix_stable(demos):
    p = _load()
    forward = p.generate(17, {"marker_scan": "forward"}, demos, 4)
    reverse = p.generate(17, {"marker_scan": "reverse"}, demos, 4)
    assert _inputs(forward) == _inputs(reverse)
    assert len({json.dumps(grid, separators=(",", ":")) for grid in _inputs(forward)}) == demos + 4
    assert forward == p.generate(17, {"marker_scan": "forward"}, demos, 4)
    assert all(a["output"] != b["output"] for a, b in zip(forward["train"], reverse["train"]))

    maximum = p.generate(17, {"marker_scan": "forward"}, 6, 4)
    one_query = p.generate(17, {"marker_scan": "forward"}, demos, 1)
    assert forward["train"] == maximum["train"][:demos]
    assert forward["test"] == maximum["test"]
    assert one_query["train"] == forward["train"]
    assert one_query["test"] == forward["test"][:1]


def test_four_queries_cover_small_large_boundary_and_substantive_30_by_30():
    p = _load()
    episode = p.generate(3, {"marker_scan": "forward"}, 3, 4)
    dims = [(len(pair["input"]), len(pair["input"][0])) for pair in episode["test"]]
    assert dims == [(9, 11), (16, 19), (24, 27), (30, 30)]

    summaries = [p.analyze_input(pair["input"]) for pair in episode["test"]]
    assert all(summary["first_color"] != summary["last_color"] for summary in summaries)
    assert all(summary["first_quadrants"] == {(0, 0), (0, 1), (1, 0), (1, 1)} for summary in summaries)
    assert all(summary["last_quadrants"] == {(0, 0), (0, 1), (1, 0), (1, 1)} for summary in summaries)

    large = summaries[-1]
    assert large["height"] == large["width"] == 30
    assert large["body_nonzero_count"] >= 96
    assert large["body_color_count"] >= 3
    assert large["touches_body_boundary"] is True
    assert sum(summary["midline_color_count"] >= 2 for summary in summaries) >= 2


def test_python_claims_apply_selected_intermediate_then_quadrant_mapping():
    p = _load()
    for scan in SETTINGS:
        episode = p.generate(29, {"marker_scan": scan}, 3, 4)
        for split in ("train", "test"):
            for pair in episode[split]:
                summary = p.analyze_input(pair["input"])
                selected = summary["first_color"] if scan == "forward" else summary["last_color"]
                assert pair["output"] == p.apply_rule(pair["input"], scan)
                assert p.selected_marker(pair["input"], scan) == selected
                assert summary["changed_by_setting"][scan] > 0


def test_public_first_turn_is_identical_and_hides_private_fields():
    p = _load()
    four = p.generate(9, {"marker_scan": "reverse"}, 3, 4)
    one = p.generate(9, {"marker_scan": "reverse"}, 3, 1)
    visible_four = public_challenge_bytes(
        {"train": four["train"], "test": [{"input": four["test"][0]["input"]}]}
    )
    visible_one = public_challenge_bytes(
        {"train": one["train"], "test": [{"input": one["test"][0]["input"]}]}
    )
    assert visible_four == visible_one
    assert b"reverse" not in visible_four
    assert b"marker_scan" not in visible_four
    assert b"program_solution" not in visible_four
    assert json.dumps(four["test"][0]["output"], separators=(",", ":")).encode() not in visible_four
    assert json.dumps(four["test"][1]["input"], separators=(",", ":")).encode() not in visible_four


@pytest.mark.parametrize("demos", (2, 3, 6))
def test_demonstrations_reject_declared_setting_and_finite_shortcut_rivals(demos):
    p = _load()
    for seed in range(8):
        for scan in SETTINGS:
            episode = p.generate(seed, {"marker_scan": scan}, demos, 4)
            audit = p.audit_episode(episode, scan)
            assert audit["harmful_survivors"] == [], (seed, scan, demos, audit)
            assert audit["selected_setting"] == scan
            assert audit["queries_checked"] == 4
