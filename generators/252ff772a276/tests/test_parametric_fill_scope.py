from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest
from reviewer_support import canonical_path, find_root, public_challenge_bytes

TASK = "252ff772a276"
TASK_ROOT = Path(__file__).resolve().parents[1]
PARAMETRIC = TASK_ROOT / "workspace" / "parametric"
SETTINGS = ("all_interior", "winner_seed_rows")


def _load():
    path = PARAMETRIC / "prototype.py"
    assert path.is_file(), f"missing {path}"
    spec = importlib.util.spec_from_file_location(f"_{TASK}_parametric_test", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_program() -> str:
    root = find_root(__file__)
    programs = []
    for line in canonical_path(root).read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK and isinstance(row.get("program_solution"), str):
            programs.append(row["program_solution"])
    assert len(set(programs)) == 1
    return programs[0]


def _inputs(episode):
    return [pair["input"] for split in ("train", "test") for pair in episode[split]]


def test_default_program_is_byte_exact_and_alternative_is_distinct():
    p = _load()
    assert p.program({"fill_scope": "all_interior"}) == _canonical_program()
    alternative = p.program({"fill_scope": "winner_seed_rows"})
    assert alternative != _canonical_program()
    assert alternative.strip().startswith("(rule!")


def test_controls_are_strict_and_count_bounds_are_exact():
    p = _load()
    good = {"fill_scope": "all_interior"}
    for settings in (None, {}, {"fill_scope": "typo"}, {"fill_scope": True}, {"fill_scope": "all_interior", "x": 1}):
        with pytest.raises((TypeError, ValueError)):
            p.program(settings)
        with pytest.raises((TypeError, ValueError)):
            p.generate(0, settings, 3, 4)
    for seed in (-1, 2**63, True, 0.0, "0"):
        with pytest.raises((TypeError, ValueError)):
            p.generate(seed, good, 3, 4)
    for demos, queries in ((1, 4), (7, 4), (True, 4), (3.0, 4), (3, 0), (3, 5), (3, True), (3, 4.0)):
        with pytest.raises((TypeError, ValueError)):
            p.generate(0, good, demos, queries)
    assert len(p.generate(2**63 - 1, good, 2, 1)["test"]) == 1


@pytest.mark.parametrize("demos", range(2, 7))
def test_inputs_are_setting_neutral_deterministic_distinct_and_prefix_stable(demos):
    p = _load()
    default = p.generate(17, {"fill_scope": "all_interior"}, demos, 4)
    alternative = p.generate(17, {"fill_scope": "winner_seed_rows"}, demos, 4)
    assert _inputs(default) == _inputs(alternative)
    assert len({json.dumps(grid, separators=(",", ":")) for grid in _inputs(default)}) == demos + 4
    assert default == p.generate(17, {"fill_scope": "all_interior"}, demos, 4)
    assert all(a["output"] != b["output"] for a, b in zip(default["train"], alternative["train"]))

    maximum = p.generate(17, {"fill_scope": "all_interior"}, 6, 4)
    one_query = p.generate(17, {"fill_scope": "all_interior"}, demos, 1)
    assert default["train"] == maximum["train"][:demos]
    assert default["test"] == maximum["test"]
    assert one_query["train"] == default["train"]
    assert one_query["test"] == default["test"][:1]


def test_queries_cover_small_large_boundary_and_substantive_30_by_30():
    p = _load()
    episode = p.generate(3, {"fill_scope": "winner_seed_rows"}, 3, 4)
    dims = [(len(pair["input"]), len(pair["input"][0])) for pair in episode["test"]]
    assert dims == [(10, 14), (16, 20), (24, 27), (30, 30)]
    analyses = [p.analyze(pair["input"]) for pair in episode["test"]]
    assert all(len(row["frames"]) == 3 for row in analyses)
    assert all(len(row["winner_seed_rows"]) >= 2 for row in analyses)
    assert all(row["winner_interior_rows"] > len(row["winner_seed_rows"]) for row in analyses)
    large = analyses[-1]
    assert large["height"] == large["width"] == 30
    assert large["nonzero_count"] >= 110
    assert large["touches_boundary"] is True
    assert large["winner_interior_area"] >= 120


def test_outputs_use_the_selected_winner_and_seed_row_intermediate():
    p = _load()
    for scope in SETTINGS:
        episode = p.generate(29, {"fill_scope": scope}, 3, 4)
        for split in ("train", "test"):
            for pair in episode[split]:
                assert pair["output"] == p.apply_rule(pair["input"], scope)
                summary = p.analyze(pair["input"])
                assert summary["winner_seed_rows"]
                assert summary["winner_seed_rows"] != summary["runner_up_seed_rows"]
    witness = p.generate(29, {"fill_scope": "winner_seed_rows"}, 3, 4)["test"][-1]
    intended = p.apply_rule(witness["input"], "winner_seed_rows")
    wrong = p.apply_rule(witness["input"], "runner_up_seed_rows")
    assert intended != wrong
    assert p.changed_cells(intended, wrong) >= 8


def test_first_turn_projection_is_count_stable_and_private_fields_are_hidden():
    p = _load()
    four = p.generate(9, {"fill_scope": "winner_seed_rows"}, 3, 4)
    one = p.generate(9, {"fill_scope": "winner_seed_rows"}, 3, 1)
    visible_four = public_challenge_bytes({"train": four["train"], "test": [{"input": four["test"][0]["input"]}]})
    visible_one = public_challenge_bytes({"train": one["train"], "test": [{"input": one["test"][0]["input"]}]})
    assert visible_four == visible_one
    for forbidden in (b"winner_seed_rows", b"fill_scope", b"program_solution"):
        assert forbidden not in visible_four
    assert json.dumps(four["test"][0]["output"], separators=(",", ":")).encode() not in visible_four
    assert json.dumps(four["test"][1]["input"], separators=(",", ":")).encode() not in visible_four


@pytest.mark.parametrize("demos", (2, 3, 6))
def test_visible_demonstrations_reject_declared_finite_rivals(demos):
    p = _load()
    for seed in range(8):
        for scope in SETTINGS:
            episode = p.generate(seed, {"fill_scope": scope}, demos, 4)
            report = p.audit_episode(episode, scope)
            assert report["harmful_survivors"] == [], (seed, scope, demos, report)
            assert report["selected_setting"] == scope
            assert report["queries_checked"] == 4
