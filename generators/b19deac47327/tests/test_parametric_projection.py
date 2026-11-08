"""Native parametric family tests for the border-projection task."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import pytest


HOME = Path(__file__).resolve().parents[1]
PARAMETRIC = HOME / "workspace/parametric"
PROTOTYPE = PARAMETRIC / "prototype.py"
AUDIT = PARAMETRIC / "audit.py"


def _load(name: str, path: Path):
    digest = hashlib.sha256(str(path).encode()).hexdigest()[:12]
    spec = importlib.util.spec_from_file_location(f"{name}_{digest}", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def proto():
    assert PROTOTYPE.is_file()
    return _load("b19_parametric", PROTOTYPE)


@pytest.fixture(scope="module")
def racket_apply():
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    bridge = RacketBridge()
    identity = bridge.runtime_identity
    assert identity["backend"] == "racket"
    assert identity["protected"] is True
    wrapped: dict[str, str] = {}

    def apply(program, grid):
        wrapped.setdefault(program, wrap_rule(program))
        literal = "'(" + " ".join(
            "(" + " ".join(map(str, row)) + ")" for row in grid
        ) + ")"
        return bridge.eval_text(f"({wrapped[program]} {literal})")

    try:
        yield apply
    finally:
        bridge.close()


def test_native_contract_files_and_settings(proto):
    assert proto.TASK_ID == "b19deac47327"
    assert proto.FINISH_RULES == ("project_only", "project_then_bridge")
    assert proto.SETTINGS == (
        {"finish_rule": "project_only"},
        {"finish_rule": "project_then_bridge"},
    )
    for name in (
        "adapter.py",
        "canonical.rkt",
        "bridge_longest.rkt",
        "skip_projection.rkt",
        "promotion.json",
    ):
        assert (PARAMETRIC / name).is_file(), name


@pytest.mark.parametrize(
    "value",
    [None, {}, {"finish_rule": "other"}, {"finish_rule": 1},
     {"finish_rule": "project_only", "extra": False}],
)
def test_settings_are_exact_and_closed(proto, value):
    with pytest.raises(ValueError):
        proto.normalize_settings(value)


def test_default_program_is_exact_selected_canonical(proto):
    source = proto.canonical_record()["program_solution"]
    assert proto.program({"finish_rule": "project_only"}) == source
    assert (PARAMETRIC / "canonical.rkt").read_text() == source
    assert hashlib.sha256(source.encode()).hexdigest() == proto.CANONICAL_PROGRAM_SHA256
    assert proto.program({"finish_rule": "project_then_bridge"}) == (
        PARAMETRIC / "bridge_longest.rkt"
    ).read_text()


def test_matched_inputs_counts_and_first_query_are_independent(proto):
    for seed in (0, 17, 991):
        short = proto.generate(seed, proto.SETTINGS[0], 2, 1)
        long_default = proto.generate(seed, proto.SETTINGS[0], 6, 4)
        long_alternate = proto.generate(seed, proto.SETTINGS[1], 6, 4)
        assert len(short["train"]) == 2 and len(short["test"]) == 1
        assert len(long_default["train"]) == 6 and len(long_default["test"]) == 4
        assert [p["input"] for p in long_default["train"]] == [
            p["input"] for p in long_alternate["train"]
        ]
        assert [p["input"] for p in long_default["test"]] == [
            p["input"] for p in long_alternate["test"]
        ]
        assert short["test"][0]["input"] == long_default["test"][0]["input"]
        inputs = [json.dumps(p["input"]) for split in ("train", "test")
                  for p in long_default[split]]
        assert len(inputs) == len(set(inputs))


def test_every_demo_count_identifies_both_settings_in_python(proto):
    for seed in (0, 1, 17, 991):
        for demos in range(2, 7):
            for chosen in proto.SETTINGS:
                episode = proto.generate(seed, chosen, demos, 4)
                survivors = []
                for rival in proto.SETTINGS:
                    if all(proto.solve(pair["input"], rival) == pair["output"]
                           for pair in episode["train"]):
                        survivors.append(rival)
                assert survivors == [chosen]
                for pair in episode["test"]:
                    assert pair["output"] == proto.solve(pair["input"], chosen)


def test_constructive_schedule_has_global_interaction_and_large_queries(proto):
    episode = proto.generate(17, proto.SETTINGS[1], 6, 4)
    facts = [proto.analyze(pair["input"])
             for split in ("train", "test") for pair in episode[split]]
    assert {fact["orientation"] for fact in facts} == {"horizontal", "vertical"}
    assert {fact["winner"]["side"] for fact in facts} == {"first", "second"}
    assert all(fact["winner"]["count"] > max(
        record["count"] for record in fact["records"] if record != fact["winner"]
    ) for fact in facts)
    assert all(fact["winner"]["span"] < max(
        record["span"] for record in fact["records"] if record != fact["winner"]
    ) for fact in facts)
    assert all(fact["bridge_added_cells"] > 0 for fact in facts)
    assert len(episode["test"][2]["input"]) > 20
    assert len(episode["test"][2]["input"][0]) > 20
    stress = episode["test"][3]["input"]
    stress_facts = proto.analyze(stress)
    assert (len(stress), len(stress[0])) == (30, 30)
    assert stress_facts["marker_count"] >= 10
    assert stress_facts["orthogonal_boundary_markers"] == [0, 29]


def test_stage_b_reads_the_stage_a_intermediate(proto):
    grid = proto.sample_input(17, "query", 3)
    stage_a = proto.project(grid)
    output = proto.bridge_longest(grid, stage_a)
    assert output == proto.solve(grid, proto.SETTINGS[1])
    assert output != stage_a
    assert proto.bridge_longest(grid, grid) == grid

    facts = proto.analyze(grid)
    wrong = copy.deepcopy(stage_a)
    row, col = facts["winner"]["cells"][0]
    wrong[row][col] = 0
    wrong_output = proto.bridge_longest(grid, wrong)
    assert wrong_output != output


def test_programs_match_python_on_small_and_30x30_cases(proto, racket_apply):
    cases = [proto.sample_input(0, "demo", 0), proto.sample_input(17, "query", 3)]
    for settings in proto.SETTINGS:
        source = proto.program(settings)
        for grid in cases:
            assert racket_apply(source, grid) == proto.solve(grid, settings)
    stress = cases[-1]
    alternate = proto.program(proto.SETTINGS[1])
    skipped = (PARAMETRIC / "skip_projection.rkt").read_text()
    assert racket_apply(alternate, stress) != racket_apply(skipped, stress)



def test_finite_audit_rejects_declared_rivals_and_emits_causal_case():
    assert AUDIT.is_file()
    audit = _load("b19_parametric_audit", AUDIT)
    report = audit.build_report(seeds=(0,), demo_counts=(2,), run_racket=True)
    summary = report["summary"]
    assert summary["all_inputs_setting_independent"] is True
    assert summary["all_labels_match"] is True
    assert summary["all_declared_unique"] is True
    assert summary["all_rivals_rejected"] is True
    assert summary["query_outputs_consulted"] is False
    assert report["causal_case"]["ablation"] == "skip_projection"
    assert report["causal_case"]["expected_output"] != report["causal_case"]["counterfactual_output"]

def test_public_turn_reveals_one_query_without_secrets(proto):
    episode = proto.generate(17, proto.SETTINGS[1], 3, 4)
    first = proto.public_turn(episode, 0)
    assert set(first) == {"train", "test"}
    assert len(first["test"]) == 1
    assert all(set(pair) == {"input", "output"} for pair in first["train"])
    assert set(first["test"][0]) == {"input"}
    assert first["test"][0]["input"] == episode["test"][0]["input"]
    first["train"][0]["input"][0][0] = 99
    assert episode["train"][0]["input"][0][0] != 99


@pytest.mark.parametrize("seed", [True, -1, 1.0, "1", None])
def test_invalid_seed_is_rejected(proto, seed):
    with pytest.raises(ValueError):
        proto.generate(seed, proto.SETTINGS[0], 3, 4)


@pytest.mark.parametrize("demos", [1, 7, True, 2.0])
def test_invalid_demo_count_is_rejected(proto, demos):
    with pytest.raises(ValueError):
        proto.generate(0, proto.SETTINGS[0], demos, 4)


@pytest.mark.parametrize("queries", [0, 5, True, 1.0])
def test_invalid_query_count_is_rejected(proto, queries):
    with pytest.raises(ValueError):
        proto.generate(0, proto.SETTINGS[0], 3, queries)
