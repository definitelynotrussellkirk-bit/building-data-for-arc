"""Native parametric-family tests for the densest-segment extension."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import pytest


HOME = Path(__file__).resolve().parents[1]
PARAMETRIC = HOME / "workspace" / "parametric"
PROTOTYPE = PARAMETRIC / "prototype.py"
AUDIT = PARAMETRIC / "audit.py"
DEFAULT = {"packing_rule": "all_right"}
ALTERNATE = {"packing_rule": "densest_left"}


def _load(name: str, path: Path):
    digest = hashlib.sha256(str(path).encode() + path.read_bytes()).hexdigest()[:16]
    spec = importlib.util.spec_from_file_location(f"{name}_{digest}", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def proto():
    assert PROTOTYPE.is_file(), "native prototype.py is missing"
    return _load("d185_parametric", PROTOTYPE)


@pytest.fixture(scope="module")
def racket_apply():
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    bridge = RacketBridge()
    identity = bridge.runtime_identity
    assert identity["backend"] == "racket"
    assert identity["protected"] is True
    wrapped: dict[str, str] = {}

    def apply(program: str, grid: list[list[int]]):
        wrapped.setdefault(program, wrap_rule(program))
        literal = "'(" + " ".join(
            "(" + " ".join(map(str, row)) + ")" for row in grid
        ) + ")"
        return bridge.eval_text(f"({wrapped[program]} {literal})")

    try:
        yield apply
    finally:
        bridge.close()


def test_native_contract_files_and_exact_settings(proto):
    assert proto.TASK_ID == "d185ceed5cc1"
    assert proto.PACKING_RULES == ("all_right", "densest_left")
    assert proto.SETTINGS == (DEFAULT, ALTERNATE)
    for name in (
        "adapter.py",
        "prototype.py",
        "canonical.rkt",
        "densest_left.rkt",
        "wrong_widest.rkt",
        "promotion.json",
    ):
        assert (PARAMETRIC / name).is_file(), name


@pytest.mark.parametrize(
    "settings",
    [None, {}, {"packing_rule": "other"}, {"packing_rule": 1},
     {"packing_rule": "all_right", "extra": False}],
)
def test_settings_are_closed_and_literal(proto, settings):
    with pytest.raises(ValueError):
        proto.normalize_settings(settings)


def test_default_program_is_byte_identical_to_selected_canonical(proto):
    canonical = proto.canonical_record()["program_solution"]
    assert proto.program(DEFAULT) == canonical
    assert (PARAMETRIC / "canonical.rkt").read_text() == canonical
    assert hashlib.sha256(canonical.encode()).hexdigest() == proto.CANONICAL_PROGRAM_SHA256
    assert proto.program(ALTERNATE) == (PARAMETRIC / "densest_left.rkt").read_text()


def test_counts_matched_inputs_and_prefix_stability(proto):
    for seed in (0, 17, 991):
        short = proto.generate(seed, DEFAULT, 2, 1)
        long_default = proto.generate(seed, DEFAULT, 6, 4)
        long_alternate = proto.generate(seed, ALTERNATE, 6, 4)
        assert len(short["train"]) == 2 and len(short["test"]) == 1
        assert len(long_default["train"]) == 6 and len(long_default["test"]) == 4
        assert [p["input"] for p in long_default["train"]] == [
            p["input"] for p in long_alternate["train"]
        ]
        assert [p["input"] for p in long_default["test"]] == [
            p["input"] for p in long_alternate["test"]
        ]
        assert short["train"] == long_default["train"][:2]
        assert short["test"][0]["input"] == long_default["test"][0]["input"]
        inputs = [json.dumps(pair["input"], separators=(",", ":"))
                  for split in ("train", "test") for pair in long_default[split]]
        assert len(inputs) == len(set(inputs))


def test_every_supported_demo_count_identifies_both_settings(proto):
    for seed in (0, 1, 17, 991):
        for demos in range(2, 7):
            for chosen in proto.SETTINGS:
                episode = proto.generate(seed, chosen, demos, 4)
                survivors = [
                    candidate
                    for candidate in proto.SETTINGS
                    if all(
                        proto.solve(pair["input"], candidate) == pair["output"]
                        for pair in episode["train"]
                    )
                ]
                assert survivors == [chosen]
                assert all(
                    proto.solve(pair["input"], chosen) == pair["output"]
                    for pair in episode["test"]
                )


def test_constructive_curriculum_exposes_the_selector_and_shortcuts(proto):
    episode = proto.generate(17, ALTERNATE, 2, 4)
    analyses = [proto.analyze(pair["input"]) for pair in episode["train"]]
    rows = [row for analysis in analyses for row in analysis["rows"]]
    assert all(row["unique_winner"] for row in rows)
    assert all(row["winner_index"] != row["widest_index"] for row in rows)
    assert {row["winner_index"] for row in rows} >= {0, 1, 2}
    assert {row["row_total"] % 2 for row in rows} == {0, 1}
    assert all(row["winner_count"] >= 3 for row in rows)
    assert all(row["winner_width"] > row["winner_count"] for row in rows)
    assert all(row["widest_width"] > row["winner_width"] for row in rows)
    assert all(analysis["settings_differ"] for analysis in analyses)


def test_four_queries_include_substantive_boundary_touching_30x30(proto):
    episode = proto.generate(17, ALTERNATE, 3, 4)
    assert [
        [len(pair["input"]), len(pair["input"][0])]
        for pair in episode["test"]
    ] == [[10, 15], [18, 22], [24, 27], [30, 30]]
    grid = episode["test"][3]["input"]
    facts = proto.analyze(grid)
    nonzero = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value]
    assert len(nonzero) >= 300
    assert {r for r, _ in nonzero} >= {0, 29}
    assert {c for _, c in nonzero} >= {0, 29}
    assert facts["winner_positions"] >= [0, 1, 2, 3, 4]
    assert facts["settings_differ"] is True


def test_stage_b_consumes_the_count_argmax_intermediate(proto):
    grid = proto.sample_input(17, "query", 3)
    analysis = proto.analyze(grid)
    expected = proto.solve(grid, ALTERNATE)
    wrong = proto.solve_widest_left(grid)
    assert expected != wrong
    assert analysis["wrong_intermediate_changes_output"] is True
    assert analysis["changed_cells_vs_widest"] >= 20
    assert all(
        row["winner_index"] != row["widest_index"]
        for row in analysis["rows"]
    )


def test_racket_programs_match_python_and_wrong_intermediate_changes_output(proto, racket_apply):
    cases = [proto.sample_input(0, "demo", 0), proto.sample_input(17, "query", 3)]
    for settings in proto.SETTINGS:
        source = proto.program(settings)
        for grid in cases:
            assert racket_apply(source, grid) == proto.solve(grid, settings)
    stress = cases[-1]
    intended = proto.program(ALTERNATE)
    wrong = (PARAMETRIC / "wrong_widest.rkt").read_text()
    assert racket_apply(intended, stress) != racket_apply(wrong, stress)


def test_finite_protected_racket_audit_rejects_declared_rivals(proto):
    assert AUDIT.is_file()
    audit = _load("d185_audit", AUDIT)
    report = audit.build_report(seeds=(0,), demo_counts=(2,), run_racket=True)
    summary = report["summary"]
    assert summary == {
        "cases": 2,
        "all_inputs_setting_independent": True,
        "all_labels_match": True,
        "all_declared_unique": True,
        "all_rivals_rejected": True,
        "query_outputs_consulted": False,
        "racket_checked": True,
    }
    causal = report["causal_case"]
    assert causal["ablation"] == "wrong_intermediate_widest_segment"
    assert causal["expected_output"] != causal["counterfactual_output"]
    assert causal["changed_cells"] >= 20


def test_public_turn_reveals_one_query_and_no_private_fields(proto):
    episode = proto.generate(17, ALTERNATE, 3, 4)
    first = proto.public_turn(episode, 0)
    assert set(first) == {"train", "test"}
    assert len(first["train"]) == 3
    assert len(first["test"]) == 1
    assert all(set(pair) == {"input", "output"} for pair in first["train"])
    assert set(first["test"][0]) == {"input"}
    assert first["test"][0]["input"] == episode["test"][0]["input"]
    altered = copy.deepcopy(episode)
    altered["settings"] = DEFAULT
    altered["program_solution"] = "private"
    altered["test"][1:] = [{"input": [[9]], "output": [[8]]}] * 3
    assert proto.public_turn(altered, 0) == first
    first["train"][0]["input"][0][0] = 99
    assert episode["train"][0]["input"][0][0] != 99


@pytest.mark.parametrize("seed", [True, -1, 1.0, "1", None])
def test_invalid_seed_is_rejected(proto, seed):
    with pytest.raises(ValueError):
        proto.generate(seed, DEFAULT, 3, 4)


@pytest.mark.parametrize("demos", [1, 7, True, 2.0])
def test_invalid_demo_count_is_rejected(proto, demos):
    with pytest.raises(ValueError):
        proto.generate(0, DEFAULT, demos, 4)


@pytest.mark.parametrize("queries", [0, 5, True, 1.0])
def test_invalid_query_count_is_rejected(proto, queries):
    with pytest.raises(ValueError):
        proto.generate(0, DEFAULT, 3, queries)
