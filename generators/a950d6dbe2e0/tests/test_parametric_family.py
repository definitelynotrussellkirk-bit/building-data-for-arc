"""Source-bound tests for the a950d6dbe2e0 native parametric family."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import random

import pytest

from reviewer_support import (
    canonical_path,
    find_root,
    public_challenge_bytes,
    public_challenge_id,
)

HOME = Path(__file__).resolve().parents[1]
ADAPTER_PATH = HOME / "workspace/parametric/adapter.py"
AUDIT_PATH = HOME / "workspace/parametric/audit_lessons.py"
COUNTERFACTUAL_PATH = HOME / "workspace/parametric/select_before_lateral.rkt"
TASK_ID = "a950d6dbe2e0"
MODES = ("full_orbit", "largest_after_lateral")


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def adapter():
    return _load(ADAPTER_PATH, "_a950d6dbe2e0_parametric_test")


def audit_module():
    return _load(AUDIT_PATH, "_a950d6dbe2e0_audit_test")


def canonical_program() -> str:
    programs = {
        row["program_solution"]
        for line in canonical_path(find_root(__file__)).read_text(encoding="utf-8").splitlines()
        if (row := json.loads(line)).get("task_id") == TASK_ID
    }
    assert len(programs) == 1
    return programs.pop()


def literal_input() -> list[list[int]]:
    # The color-2 source object has 3 cells and touches the lateral midline.
    # Its mirrored copy joins it into a 6-cell object.  The color-3 decoy is
    # initially larger (4 cells) but its copy remains a separate 4-cell object.
    h, w = 10, 12
    out = [[0] * w for _ in range(h)]
    for r, c, value in (
        (1, 5, 2), (2, 5, 2), (2, 4, 2),
        (1, 1, 3), (1, 2, 3), (2, 1, 3), (2, 2, 3),
        (4, 0, 4), (4, 1, 4),
    ):
        out[r][c] = value
    return out


def _copy(grid: list[list[int]]) -> list[list[int]]:
    return [row[:] for row in grid]


def expected_lateral_top(grid: list[list[int]]) -> list[list[int]]:
    h, w = len(grid), len(grid[0])
    out = _copy(grid)
    for r in range(h // 2):
        for c in range(w // 2):
            if grid[r][c]:
                out[r][w - 1 - c] = grid[r][c]
    return out


def expected_full_orbit(grid: list[list[int]]) -> list[list[int]]:
    top = expected_lateral_top(grid)
    out = _copy(top)
    h = len(grid)
    for r in range(h // 2):
        for c, value in enumerate(top[r]):
            if value:
                out[h - 1 - r][c] = value
    return out


def expected_largest_after_lateral(grid: list[list[int]]) -> list[list[int]]:
    out = expected_lateral_top(grid)
    h, w = len(grid), len(grid[0])
    selected = {(1, 5), (2, 5), (2, 4)}
    selected |= {(r, w - 1 - c) for r, c in selected}
    for r, c in selected:
        out[h - 1 - r][c] = out[r][c]
    return out


def expected_wrong_order(grid: list[list[int]]) -> list[list[int]]:
    out = expected_lateral_top(grid)
    h, w = len(grid), len(grid[0])
    selected = {(1, 1), (1, 2), (2, 1), (2, 2)}
    selected |= {(r, w - 1 - c) for r, c in selected}
    for r, c in selected:
        out[h - 1 - r][c] = out[r][c]
    return out


@pytest.fixture(scope="module")
def racket():
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    with RacketBridge(timeout=15) as bridge:
        assert bridge.runtime_identity["protected"] is True
        counter = 0

        def apply(program: str, grid: list[list[int]]) -> list[list[int]]:
            nonlocal counter
            counter += 1
            name = f"a950-parametric-test-{counter}"
            bridge.define_grid(name, grid)
            return bridge.eval_text(f"({wrap_rule(program)} {name})")

        yield apply


def all_inputs(episode: dict) -> list[list[list[int]]]:
    return [pair["input"] for pair in episode["train"] + episode["test"]]


def public_projection(episode: dict) -> dict:
    return {
        "train": episode["train"],
        "test": [{"input": pair["input"]} for pair in episode["test"]],
    }


def test_default_program_is_exact_canonical_and_alternative_is_distinct():
    module = adapter()
    default = module.program({"mode": "full_orbit"})
    alternative = module.program({"mode": "largest_after_lateral"})
    assert default == canonical_program()
    assert alternative != default
    assert hashlib.sha256(default.encode()).hexdigest() != hashlib.sha256(alternative.encode()).hexdigest()


@pytest.mark.parametrize(
    "mode,expected",
    [
        ("full_orbit", expected_full_orbit(literal_input())),
        ("largest_after_lateral", expected_largest_after_lateral(literal_input())),
    ],
)
def test_literal_labels_match_independent_expected_and_protected_racket(racket, mode, expected):
    module = adapter()
    source = literal_input()
    assert module.transform(source, mode) == expected
    assert racket(module.program({"mode": mode}), source) == expected
    assert source == literal_input()


def test_lateral_pass_changes_which_object_is_largest():
    explanation = adapter().explain_dependency(literal_input())
    assert explanation["largest_before"]["color"] == 3
    assert explanation["largest_before"]["size"] == 4
    assert explanation["largest_after"]["color"] == 2
    assert explanation["largest_after"]["size"] == 6
    assert explanation["largest_after"]["cells"] != explanation["largest_before"]["cells"]
    assert explanation["final"] == expected_largest_after_lateral(literal_input())


def test_wrong_order_counterfactual_is_executable_and_changes_final_output(racket):
    module = adapter()
    source = literal_input()
    counterfactual = COUNTERFACTUAL_PATH.read_text(encoding="utf-8")
    actual = racket(module.program({"mode": "largest_after_lateral"}), source)
    wrong = racket(counterfactual, source)
    assert wrong == expected_wrong_order(source)
    assert actual != wrong


@pytest.mark.parametrize("mode", MODES)
def test_generation_is_setting_neutral_deterministic_and_prefix_stable(mode):
    module = adapter()
    before = random.getstate()
    selected = module.generate(17, {"mode": mode}, 2, 4)
    other_mode = "largest_after_lateral" if mode == "full_orbit" else "full_orbit"
    other = module.generate(17, {"mode": other_mode}, 2, 4)
    one_query = module.generate(17, {"mode": mode}, 2, 1)
    six_demo = module.generate(17, {"mode": mode}, 6, 4)

    assert all_inputs(selected) == all_inputs(other)
    assert selected == module.generate(17, {"mode": mode}, 2, 4)
    assert random.getstate() == before
    assert len(selected["train"]) == 2 and len(selected["test"]) == 4
    assert len(six_demo["train"]) == 6 and len(six_demo["test"]) == 4
    assert selected["train"] == six_demo["train"][:2]
    assert selected["test"] == six_demo["test"]
    assert selected["train"] == one_query["train"]
    assert selected["test"][0] == one_query["test"][0]
    keys = [json.dumps(value, separators=(",", ":")) for value in all_inputs(six_demo)]
    assert len(keys) == len(set(keys)) == 10


@pytest.mark.parametrize("seed", [0, 1, 17, 2**63 - 1])
@pytest.mark.parametrize("mode", MODES)
def test_supported_count_boundaries_generate_identifiable_lessons(seed, mode):
    module = adapter()
    for demos, queries in ((2, 1), (2, 4), (3, 4), (6, 1), (6, 4)):
        episode = module.generate(seed, {"mode": mode}, demos, queries)
        certificate = module.certificate(episode["train"], [pair["input"] for pair in episode["test"]])
        assert certificate["survivors"] == [mode]
        assert certificate["demonstrations"] == demos
        assert certificate["queries"] == queries


def test_fourth_query_is_substantive_30x30_stress_and_setting_sensitive():
    module = adapter()
    canonical = module.generate(91, {"mode": "full_orbit"}, 3, 4)["test"][3]
    alternative = module.generate(91, {"mode": "largest_after_lateral"}, 3, 4)["test"][3]
    source = canonical["input"]
    cells = [(r, c, value) for r, row in enumerate(source) for c, value in enumerate(row) if value]
    assert (len(source), len(source[0])) == (30, 30)
    assert len(cells) >= 36
    assert len({value for _, _, value in cells}) >= 4
    assert any(r == 0 for r, _, _ in cells)
    assert any(c == 0 for _, c, _ in cells)
    assert any(c == 14 for _, c, _ in cells)
    assert canonical["output"] != alternative["output"]
    assert sum(bool(v) for row in canonical["output"] for v in row) == 4 * len(cells)
    assert sum(bool(v) for row in alternative["output"] for v in row) > 2 * len(cells)


@pytest.mark.parametrize("mode", MODES)
def test_two_demos_identify_setting_and_declared_shortcuts(mode):
    module = adapter()
    episode = module.generate(23, {"mode": mode}, 2, 4)
    certificate = module.certificate(episode["train"], [pair["input"] for pair in episode["test"]])
    assert certificate["survivors"] == [mode]
    assert set(certificate["declared_hypotheses"]) >= {
        "full_orbit",
        "largest_after_lateral",
        "lateral_only",
        "largest_before_lateral",
        "smallest_after_lateral",
        "first_after_lateral",
        "last_after_lateral",
        "all_largest_color_after_lateral",
        "identity",
    }
    assert certificate["query_disagreements"]


@pytest.mark.parametrize(
    "seed,settings,demos,queries",
    [
        (True, {"mode": "full_orbit"}, 2, 4),
        (-1, {"mode": "full_orbit"}, 2, 4),
        (2**63, {"mode": "full_orbit"}, 2, 4),
        (0, {"mode": "wrong"}, 2, 4),
        (0, {"mode": "full_orbit", "extra": 1}, 2, 4),
        (0, {"mode": "full_orbit"}, 1, 4),
        (0, {"mode": "full_orbit"}, 7, 4),
        (0, {"mode": "full_orbit"}, 2, 0),
        (0, {"mode": "full_orbit"}, 2, 5),
        (0, {"mode": "full_orbit"}, 2, True),
    ],
)
def test_bad_requests_fail_explicitly(seed, settings, demos, queries):
    with pytest.raises(ValueError):
        adapter().generate(seed, settings, demos, queries)


def test_boolean_grid_cells_are_rejected():
    source = literal_input()
    source[0][0] = False
    with pytest.raises(ValueError):
        adapter().transform(source, "largest_after_lateral")


def test_public_projection_hides_settings_programs_answers_and_future_queries():
    episode = adapter().generate(5, {"mode": "largest_after_lateral"}, 3, 4)
    first_turn = {"train": episode["train"], "test": [episode["test"][0]]}
    raw = public_challenge_bytes(first_turn)
    public = json.loads(raw)
    assert set(public) == {"train", "test"}
    assert len(public["test"]) == 1 and set(public["test"][0]) == {"input"}
    assert b"settings" not in raw and b"program_solution" not in raw
    assert public_challenge_id(first_turn) == hashlib.sha256(raw).hexdigest()

    one_query = adapter().generate(5, {"mode": "largest_after_lateral"}, 3, 1)
    assert public_challenge_bytes(one_query) == raw
    assert public_projection(one_query) == {
        "train": public_projection(episode)["train"],
        "test": [public_projection(episode)["test"][0]],
    }


def test_all_generated_labels_match_protected_racket(racket):
    module = adapter()
    for mode in MODES:
        episode = module.generate(7, {"mode": mode}, 6, 4)
        program = module.program({"mode": mode})
        for pair in episode["train"] + episode["test"]:
            assert racket(program, pair["input"]) == pair["output"]


def test_audit_tool_checks_bounded_lessons_and_writes_machine_report(tmp_path):
    report = audit_module().run_audit(seed_start=0, seed_count=8)
    assert report["status"] == "passed"
    assert report["episodes"] == 8 * 2 * 3
    assert report["failures"] == []
    assert report["declared_hypotheses"] >= 9
    output = tmp_path / "audit.json"
    audit_module().write_report(output, report)
    assert json.loads(output.read_text()) == report
