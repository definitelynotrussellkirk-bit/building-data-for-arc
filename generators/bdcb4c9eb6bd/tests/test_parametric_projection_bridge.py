from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest

from arcpuzzles.catalog import Catalog
from reviewer_support import find_root, public_challenge_bytes


TASK_ID = "bdcb4c9eb6bd"
ROOT = find_root(__file__)
PARAMETRIC = ROOT / "generators" / TASK_ID / "workspace" / "parametric"


def _load(name: str):
    path = PARAMETRIC / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"_{TASK_ID}_{name}_test", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_program() -> str:
    root = find_root(__file__)
    catalog = Catalog(root)
    row = catalog.describe(TASK_ID)
    programs = {
        variant["program_solution"]
        for variant in catalog._variants()[row.get("rule_task_id", TASK_ID)]
        if isinstance(variant.get("program_solution"), str)
    }
    assert len(programs) == 1
    return next(iter(programs))


def _settings(name: str) -> dict[str, str]:
    return {"finish_rule": name}


def test_default_program_is_byte_exact_canonical_and_variant_is_distinct() -> None:
    prototype = _load("prototype")
    canonical = prototype.program(_settings("project_only"))
    bridge = prototype.program(_settings("project_then_bridge"))
    assert canonical == _canonical_program()
    assert (PARAMETRIC / "canonical.rkt").read_text() == canonical
    assert bridge == (PARAMETRIC / "project_then_bridge.rkt").read_text()
    assert bridge != canonical


def test_generation_supports_all_declared_counts_and_is_setting_matched() -> None:
    prototype = _load("prototype")
    for demos in range(2, 7):
        for queries in range(1, 5):
            canonical = prototype.generate(9000 + demos * 10 + queries, _settings("project_only"), demos, queries)
            bridge = prototype.generate(9000 + demos * 10 + queries, _settings("project_then_bridge"), demos, queries)
            assert len(canonical["train"]) == len(bridge["train"]) == demos
            assert len(canonical["test"]) == len(bridge["test"]) == queries
            assert [p["input"] for p in canonical["train"] + canonical["test"]] == [
                p["input"] for p in bridge["train"] + bridge["test"]
            ]
            assert len({json.dumps(p["input"]) for p in canonical["train"] + canonical["test"]}) == demos + queries
            assert prototype.teaching_check(canonical)["ok"] is True
            assert prototype.teaching_check(bridge)["ok"] is True


def test_every_generated_pair_matches_python_solver_and_settings_differ() -> None:
    prototype = _load("prototype")
    for seed in (0, 17, 12345):
        canonical = prototype.generate(seed, _settings("project_only"), 3, 4)
        bridge = prototype.generate(seed, _settings("project_then_bridge"), 3, 4)
        for c_pair, b_pair in zip(canonical["train"] + canonical["test"], bridge["train"] + bridge["test"]):
            assert c_pair["input"] == b_pair["input"]
            assert c_pair["output"] == prototype.solve_python(c_pair["input"], _settings("project_only"))
            assert b_pair["output"] == prototype.solve_python(b_pair["input"], _settings("project_then_bridge"))
            assert c_pair["output"] != b_pair["output"]


def test_stage_b_consumes_stage_a_border_contacts() -> None:
    prototype = _load("prototype")
    episode = prototype.generate(17, _settings("project_then_bridge"), 2, 4)
    for pair in episode["train"] + episode["test"]:
        facts = prototype.analyze_input(pair["input"])
        stage_a = prototype.project_only(pair["input"])
        output = pair["output"]
        assert facts["rectangles"] >= 2
        assert facts["bridge_axes"]
        assert stage_a != output
        # The raw input has no color 2, while Stage A creates the opposite-border
        # contacts that Stage B reads.
        assert all(2 not in row for row in pair["input"])
        assert any(stage_a[row][0] == stage_a[row][-1] == 2 for row in range(len(stage_a))) or any(
            stage_a[0][column] == stage_a[-1][column] == 2 for column in range(len(stage_a[0]))
        )
        assert any(3 in row for row in output)


def test_fourth_query_is_substantive_30x30_and_touches_all_boundaries() -> None:
    prototype = _load("prototype")
    episode = prototype.generate(0, _settings("project_then_bridge"), 3, 4)
    grid = episode["test"][3]["input"]
    output = episode["test"][3]["output"]
    assert (len(grid), len(grid[0])) == (30, 30)
    background = prototype.background_color(grid)
    assert any(value != background for value in grid[0])
    assert any(value != background for value in grid[-1])
    assert any(row[0] != background for row in grid)
    assert any(row[-1] != background for row in grid)
    assert sum(value != background for row in grid for value in row) >= 80
    assert sum(value == 3 for row in output for value in row) >= 20


def test_public_turn_is_prefix_stable_and_private_fields_never_escape() -> None:
    prototype = _load("prototype")
    full = prototype.generate(314, _settings("project_then_bridge"), 3, 4)
    shorter = prototype.generate(314, _settings("project_then_bridge"), 3, 1)
    assert shorter["train"] == full["train"]
    assert shorter["test"] == full["test"][:1]
    first = prototype.public_turn(full, 0)
    last = prototype.public_turn(full, 3)
    assert first["train"] == last["train"] == full["train"]
    assert first["test"] == [{"input": full["test"][0]["input"]}]
    assert last["test"] == [{"input": full["test"][3]["input"]}]
    payload = public_challenge_bytes(first)
    for secret in (b"finish_rule", b"project_only", b"project_then_bridge", b"program_solution", b"settings"):
        assert secret not in payload
    assert full["test"][1]["input"] != first["test"][0]["input"]


def test_generation_is_fresh_and_rejects_typed_invalid_requests() -> None:
    prototype = _load("prototype")
    episode = prototype.generate(77, _settings("project_only"), 2, 4)
    replay = prototype.generate(77, _settings("project_only"), 2, 4)
    assert episode == replay
    assert episode is not replay
    original = copy.deepcopy(replay)
    episode["train"][0]["input"][0][0] = 9
    assert replay == original

    bad_settings = [
        {},
        {"finish_rule": "unknown"},
        {"finish_rule": 1},
        {"finish_rule": "project_only", "extra": True},
    ]
    for settings in bad_settings:
        with pytest.raises(ValueError):
            prototype.generate(0, settings, 2, 4)
    for demos, queries in ((True, 4), (1, 4), (7, 4), (2, True), (2, 0), (2, 5)):
        with pytest.raises(ValueError):
            prototype.generate(0, _settings("project_only"), demos, queries)


def _racket_literal(grid: list[list[int]]) -> str:
    return "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"


def test_protected_racket_programs_match_python_labels() -> None:
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    prototype = _load("prototype")
    with RacketBridge(timeout=30, startup_timeout=60) as bridge:
        assert bridge.runtime_identity["backend"] == "racket"
        assert bridge.runtime_identity["protected"] is True
        for rule in ("project_only", "project_then_bridge"):
            episode = prototype.generate(0, _settings(rule), 2, 1)
            program = prototype.program(_settings(rule))
            wrapped = wrap_rule(program)
            for pair in episode["train"] + episode["test"]:
                actual = bridge.eval_text(f"({wrapped} {_racket_literal(pair['input'])})")
                assert actual == pair["output"]


def test_bounded_shortcut_audit_rejects_plausible_rivals_from_demos() -> None:
    audit = _load("audit")
    for seed in (0, 17, 91):
        for rule in ("project_only", "project_then_bridge"):
            episode = _load("prototype").generate(seed, _settings(rule), 2, 4)
            result = audit.audit_episode(episode, _settings(rule))
            assert result["ambiguous_rivals"] == []
            assert result["demo_survivors"] == []
            assert result["rival_count"] >= 5
    bridge = _load("prototype").generate(0, _settings("project_then_bridge"), 2, 4)
    result = audit.audit_episode(bridge, _settings("project_then_bridge"))
    any_edge = next(row for row in result["rivals"] if row["name"] == "bridge_any_border_contact")
    assert any_edge["demo_survives"] is False
