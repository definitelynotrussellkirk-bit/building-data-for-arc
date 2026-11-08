"""Source-bound tests for the 67ec1565020d native parametric family."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import random

import pytest

from reviewer_support import canonical_path, find_root, public_challenge_bytes, public_challenge_id

HOME = Path(__file__).resolve().parents[1]
PARAMETRIC = HOME / "workspace/parametric"
ADAPTER_PATH = PARAMETRIC / "adapter.py"
COUNTERFACTUAL_PATH = PARAMETRIC / "raw_wide_count.rkt"
AUDIT_PATH = PARAMETRIC / "audit.py"
EXAMPLES_PATH = PARAMETRIC / "make_examples.py"
TASK_ID = "67ec1565020d"
MODES = ("canonical", "wide_region_relay")


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def adapter():
    return _load(ADAPTER_PATH, "_67ec_parametric_adapter")


def audit_module():
    return _load(AUDIT_PATH, "_67ec_parametric_audit")


def examples_module():
    return _load(EXAMPLES_PATH, "_67ec_parametric_examples")


def canonical_program() -> str:
    programs = {
        row["program_solution"]
        for line in canonical_path(find_root(__file__)).read_text(encoding="utf-8").splitlines()
        if (row := json.loads(line)).get("task_id") == TASK_ID
    }
    assert len(programs) == 1
    return programs.pop()


def literal_input() -> list[list[int]]:
    grid = [[0] * 16 for _ in range(12)]
    for row in range(12):
        grid[row][8] = 5
    # Three individually wide objects touch end-to-end. After canonical
    # recoloring they become one connected color-2 region.
    for column in (1, 2):
        grid[1][column] = 1
    for column in (3, 4):
        grid[1][column] = 6
    for column in (5, 6):
        grid[1][column] = 7
    for row in range(7, 11):
        grid[row][1] = 8
    for row, column in ((8, 5), (8, 6), (9, 5)):
        grid[row][column] = 9
    # Payload candidates in reading order: wide, tall, square.
    for column in range(10, 14):
        grid[1][column] = 6
    for row in range(4, 7):
        grid[row][12] = 7
    for row, column in ((8, 10), (8, 11), (9, 10)):
        grid[row][column] = 9
    return grid


def public_first_turn(episode: dict) -> dict:
    return {"train": episode["train"], "test": [{"input": episode["test"][0]["input"]}]}


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
            name = f"aspect-relay-{counter}"
            bridge.define_grid(name, grid)
            return bridge.eval_text(f"({wrap_rule(program)} {name})")

        yield apply


def test_default_program_is_exact_canonical_and_alternative_is_distinct():
    module = adapter()
    default = module.program({"mode": "canonical"})
    alternative = module.program({"mode": "wide_region_relay"})
    assert default == canonical_program()
    assert alternative != default
    assert hashlib.sha256(default.encode()).hexdigest() != hashlib.sha256(alternative.encode()).hexdigest()


def test_literal_dependency_and_both_programs_match_protected_racket(racket):
    module = adapter()
    source = literal_input()
    explanation = module.explain_dependency(source)
    assert explanation["wide_objects_before"] == 3
    assert explanation["wide_regions_after"] == 1
    assert explanation["selected_payload_index"] == 1
    assert explanation["counterfactual_payload_index"] == 3

    for mode in MODES:
        expected = module.transform(source, mode)
        assert racket(module.program({"mode": mode}), source) == expected
    wrong = racket(COUNTERFACTUAL_PATH.read_text(), source)
    assert wrong == module.transform(source, "raw_wide_count")
    assert wrong != module.transform(source, "wide_region_relay")
    assert source == literal_input()


@pytest.mark.parametrize("mode", MODES)
def test_generation_is_setting_neutral_deterministic_and_prefix_stable(mode):
    module = adapter()
    before = random.getstate()
    episode = module.generate(17, {"mode": mode}, 2, 4)
    other_mode = "wide_region_relay" if mode == "canonical" else "canonical"
    other = module.generate(17, {"mode": other_mode}, 2, 4)
    one_query = module.generate(17, {"mode": mode}, 2, 1)
    six_demo = module.generate(17, {"mode": mode}, 6, 4)

    inputs = lambda value: [pair["input"] for pair in value["train"] + value["test"]]
    assert inputs(episode) == inputs(other)
    assert episode == module.generate(17, {"mode": mode}, 2, 4)
    assert random.getstate() == before
    assert episode["train"] == six_demo["train"][:2]
    assert episode["test"] == six_demo["test"]
    assert episode["train"] == one_query["train"]
    assert episode["test"][0] == one_query["test"][0]
    signatures = [json.dumps(grid, separators=(",", ":")) for grid in inputs(six_demo)]
    assert len(signatures) == len(set(signatures)) == 10


@pytest.mark.parametrize("seed", [0, 1, 17, 2**63 - 1])
@pytest.mark.parametrize("mode", MODES)
def test_supported_count_boundaries_are_identifiable(seed, mode):
    module = adapter()
    for demos, queries in ((2, 1), (2, 4), (3, 4), (6, 1), (6, 4)):
        episode = module.generate(seed, {"mode": mode}, demos, queries)
        certificate = module.certificate(episode["train"], [pair["input"] for pair in episode["test"]])
        assert certificate["survivors"] == [mode]
        assert certificate["demonstrations"] == demos
        assert certificate["queries"] == queries


def test_fourth_query_is_substantive_30x30_and_causally_sensitive():
    module = adapter()
    canonical = module.generate(91, {"mode": "canonical"}, 3, 4)["test"][3]
    relay = module.generate(91, {"mode": "wide_region_relay"}, 3, 4)["test"][3]
    source = relay["input"]
    explanation = module.explain_dependency(source)
    nonzero = [(r, c, v) for r, row in enumerate(source) for c, v in enumerate(row) if v]
    assert (len(source), len(source[0])) == (30, 30)
    assert len(nonzero) >= 130
    assert len({v for _, _, v in nonzero}) >= 5
    assert any(r == 0 for r, _, _ in nonzero)
    assert any(r == 29 for r, _, _ in nonzero)
    assert any(c == 29 for _, c, _ in nonzero)
    assert canonical["output"] != relay["output"]
    assert explanation["wide_regions_after"] in (1, 2, 3)
    assert relay["output"] != module.transform(source, "raw_wide_count")


def test_public_first_turn_hides_private_data_and_matches_one_query_call():
    module = adapter()
    episode = module.generate(5, {"mode": "wide_region_relay"}, 3, 4)
    public = public_first_turn(episode)
    raw = public_challenge_bytes(public)
    decoded = json.loads(raw)
    assert set(decoded) == {"train", "test"}
    assert len(decoded["test"]) == 1 and set(decoded["test"][0]) == {"input"}
    assert b"settings" not in raw and b"program_solution" not in raw
    assert public_challenge_id(public) == hashlib.sha256(raw).hexdigest()
    one = module.generate(5, {"mode": "wide_region_relay"}, 3, 1)
    assert public_challenge_bytes(one) == raw


@pytest.mark.parametrize(
    "seed,settings,demos,queries",
    [
        (True, {"mode": "canonical"}, 2, 4),
        (-1, {"mode": "canonical"}, 2, 4),
        (2**63, {"mode": "canonical"}, 2, 4),
        (0, {"mode": "wrong"}, 2, 4),
        (0, {"mode": "canonical", "extra": 1}, 2, 4),
        (0, {"mode": "canonical"}, 1, 4),
        (0, {"mode": "canonical"}, 7, 4),
        (0, {"mode": "canonical"}, 2, 0),
        (0, {"mode": "canonical"}, 2, 5),
        (0, {"mode": "canonical"}, 2, True),
    ],
)
def test_bad_requests_fail_explicitly(seed, settings, demos, queries):
    with pytest.raises(ValueError):
        adapter().generate(seed, settings, demos, queries)


def test_boolean_grid_cells_are_rejected():
    source = literal_input()
    source[0][0] = False
    with pytest.raises(ValueError):
        adapter().transform(source, "wide_region_relay")


def test_all_generated_labels_match_protected_racket(racket):
    module = adapter()
    for mode in MODES:
        episode = module.generate(7, {"mode": mode}, 6, 4)
        program = module.program({"mode": mode})
        for pair in episode["train"] + episode["test"]:
            assert racket(program, pair["input"]) == pair["output"]


def test_audit_tool_checks_lessons_racket_and_writes_report(tmp_path):
    report = audit_module().run_audit(seed_start=0, seed_count=4, racket_seed_count=1)
    assert report["status"] == "passed"
    assert report["episodes"] == 8
    assert report["lesson_failures"] == []
    assert report["racket_failures"] == []
    assert report["racket_evaluations"] >= 15
    assert report["region_counts"] == [1, 2, 3]
    path = tmp_path / "audit.json"
    audit_module().write_report(path, report)
    assert json.loads(path.read_text()) == report


def test_example_writer_separates_public_turns_and_private_controller_data(tmp_path):
    report = examples_module().write_examples(
        tmp_path / "examples", seed=3, demos=2, queries=4, verify_racket=False
    )
    assert report["status"] == "written"
    assert report["settings"] == 2
    assert report["public_batches"] == 2
    assert report["public_turns"] == 8
    assert report["private_episodes"] == 2
    assert report["first_turn_prefix_stable"] is True
    assert len(list((tmp_path / "examples/public").glob("*.json"))) == 2
    assert len(list((tmp_path / "examples/turns").glob("**/*.json"))) == 8
    private = json.loads(next((tmp_path / "examples/private").glob("*.json")).read_text())
    assert "program_solution" in private and "settings" in private
    visible = next((tmp_path / "examples/turns").glob("**/*.json")).read_bytes()
    assert b"program_solution" not in visible and b"settings" not in visible
