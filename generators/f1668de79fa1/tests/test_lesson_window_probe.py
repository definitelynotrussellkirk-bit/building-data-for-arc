"""Literal lesson fixtures for the authoring probe; no synthetic Python labels."""
from copy import deepcopy
import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest


TOOL_PATH = Path(__file__).resolve().parents[1] / "workspace/probe_lesson_windows.py"
SPEC = importlib.util.spec_from_file_location("f1668_lesson_window_probe", TOOL_PATH)
probe = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(probe)


PAIRS = [
    {"input": [[1]], "output": [[2]]},
    {"input": [[3]], "output": [[4]]},
    {"input": [[5]], "output": [[6]]},
]


def agrees_with_fixtures(grid):
    return {1: [[2]], 3: [[4]], 5: [[6]]}[grid[0][0]]


def one_discriminator(grid):
    return {1: [[9]], 3: [[4]], 5: [[6]]}[grid[0][0]]


def two_discriminators(grid):
    return {1: [[9]], 3: [[8]], 5: [[6]]}[grid[0][0]]


def test_each_pair_is_held_out_and_a_single_discriminator_becomes_ambiguous():
    rows = probe.score_rotations(SimpleNamespace(), {"rival": one_discriminator}, PAIRS)
    assert [row["query_position"] for row in rows] == [0, 1, 2]
    assert [row["train_positions"] for row in rows] == [[1, 2], [0, 2], [0, 1]]
    assert [row["status"] for row in rows] == ["ambiguous", "no_declared_ambiguity", "no_declared_ambiguity"]
    assert rows[0]["ambiguities"] == [{"rival": "rival", "predictions": [[[9]], [[4]], [[6]]]}]
    assert rows[2]["rivals"] == {"rival": "refuted"}


def test_surviving_all_labels_is_not_ambiguity_and_two_discriminators_cover_rotations():
    rivals = {"agrees": agrees_with_fixtures, "two_wrong": two_discriminators}
    rows = probe.score_rotations(SimpleNamespace(), rivals, PAIRS)
    assert [row["rivals"] for row in rows] == [{"agrees": "survived_all", "two_wrong": "refuted"}] * 3
    assert all(row["ambiguities"] == [] for row in rows)


def test_dynamic_namespaces_preserve_identical_local_names():
    gen = SimpleNamespace(CANONICAL_SHORTCUTS={"same": agrees_with_fixtures},
                          LESSON_COMPETITORS={"same": one_discriminator},
                          SEMANTIC_RIVALS={"same": two_discriminators})
    rivals, declarations, errors = probe.declared_rivals(gen)
    assert errors == []
    assert set(rivals) == {"CANONICAL_SHORTCUTS:same", "LESSON_COMPETITORS:same", "SEMANTIC_RIVALS:same"}
    assert all(declaration == {"present": True, "names": ["same"]} for declaration in declarations.values())
    first = probe.score_rotations(gen, rivals, PAIRS)[0]
    assert first["rivals"] == {"CANONICAL_SHORTCUTS:same": "survived_all",
                               "LESSON_COMPETITORS:same": "ambiguous", "SEMANTIC_RIVALS:same": "refuted"}


def test_malformed_rival_predictions_are_errors_even_after_a_refuting_demo():
    def malformed(grid):
        return {1: [[9]], 3: [[4]], 5: None}[grid[0][0]]
    rows = probe.score_rotations(SimpleNamespace(), {"malformed": malformed}, PAIRS)
    assert [row["status"] for row in rows] == ["error", "error", "error"]
    assert rows[-1]["errors"][0]["pair_positions"] == [2]
    assert rows[-1]["errors"][0]["predictions"][2]["returned"] is None
    assert "rectangular" in rows[-1]["errors"][0]["predictions"][2]["error"]


def test_rival_exception_keeps_exact_error_and_does_not_erase_other_ambiguities():
    def broken(grid):
        if grid == [[5]]:
            raise ValueError("literal fixture failure")
        return [[9]]
    row = probe.score_rotations(SimpleNamespace(), {"broken": broken, "wrong": one_discriminator}, PAIRS)[0]
    assert row["status"] == "error"
    assert row["rivals"]["wrong"] == "ambiguous"
    assert row["errors"][0]["predictions"][2]["error"] == "ValueError: literal fixture failure"


def test_rival_mutation_cannot_change_authoritative_pairs_or_cached_predictions():
    def mutating(grid):
        grid[0][0] = {1: 2, 3: 4, 5: 6}[grid[0][0]]
        return grid
    pairs = deepcopy(PAIRS)
    cache = {}
    first = probe.score_rotations(SimpleNamespace(), {"mutating": mutating}, pairs, prediction_cache=cache)
    first[0]["rivals"]["mutating"] = "changed report copy"
    second = probe.score_rotations(SimpleNamespace(), {"mutating": mutating}, pairs, prediction_cache=cache)
    assert pairs == PAIRS
    assert [row["rivals"]["mutating"] for row in second] == ["survived_all"] * 3


def test_canonical_shortcuts_include_later_variants_and_test_pairs():
    canonical = [
        {"input": [[1]], "output": [[2]], "variant": 0, "split": "train", "pair_index": 0},
        {"input": [[3]], "output": [[4]], "variant": 0, "split": "test", "pair_index": 0},
        {"input": [[5]], "output": [[6]], "variant": 1, "split": "test", "pair_index": 0},
    ]
    def wrong_late(grid):
        return {1: [[2]], 3: [[4]], 5: [[9]]}[grid[0][0]]
    fit, failures = probe.canonical_shortcut_fit(
        {"CANONICAL_SHORTCUTS:good": agrees_with_fixtures,
         "CANONICAL_SHORTCUTS:bad": wrong_late, "SEMANTIC_RIVALS:allowed_wrong": two_discriminators}, canonical)
    assert fit["CANONICAL_SHORTCUTS:good"] == {"pairs": 3, "fits": 3, "errors": 0, "status": "fits_all"}
    assert fit["CANONICAL_SHORTCUTS:bad"] == {"pairs": 3, "fits": 2, "errors": 0, "status": "refuted"}
    assert set(fit) == {"CANONICAL_SHORTCUTS:good", "CANONICAL_SHORTCUTS:bad"}
    assert failures == [{"kind": "canonical_shortcut_disagreement", "rival": "CANONICAL_SHORTCUTS:bad",
                         "canonical_index": 2, "pair": canonical[2],
                         "prediction": {"output": [[9]], "error": None}}]


def test_missing_canonical_pairs_cannot_pass_vacuously():
    with pytest.raises(ValueError, match="no labeled pairs"):
        probe.canonical_shortcut_fit({"CANONICAL_SHORTCUTS:fixture": agrees_with_fixtures}, [])


def test_raw_duplicates_and_validator_rejects_keep_absolute_indices():
    samples = [
        {"sample_index": 2, "input_sha256": "literal-grid-a", "findings": []},
        {"sample_index": 3, "input_sha256": "literal-grid-b", "findings": ["fixture clipped stamp invalid"]},
        {"sample_index": 4, "input_sha256": "literal-grid-a", "findings": []},
        {"sample_index": 5, "input_sha256": None, "findings": ["generate/input: fixture generator error"]},
    ]
    before = deepcopy(samples)
    rejects, duplicates = probe.window_validation(samples)
    assert rejects == [{"pair_position": 1, "sample_index": 3, "findings": ["fixture clipped stamp invalid"]},
                       {"pair_position": 3, "sample_index": 5, "findings": ["generate/input: fixture generator error"]}]
    assert duplicates == [{"pair_position": 2, "sample_index": 4, "first_pair_position": 0,
                           "first_sample_index": 2, "input_sha256": "literal-grid-a"}]
    assert samples == before


def test_self_check_mutation_is_preserved_as_a_reject():
    def checker(grid, *, difficulty):
        grid[0][0] = 9
        return ["fixture finding"] if difficulty == "hard" else []
    grid = [[1]]
    assert probe.self_check_findings(SimpleNamespace(self_check=checker), grid, "hard") == [
        "fixture finding", "self_check mutated its input"]
    assert grid == [[1]]


def test_hook_findings_and_bad_declarations_are_not_silenced():
    gen = SimpleNamespace(lesson_identifiable=lambda demos, query: ["fixture teaching gap"])
    rows = probe.score_rotations(gen, {"agrees": agrees_with_fixtures}, PAIRS)
    assert [row["status"] for row in rows] == ["hook_rejected"] * 3
    assert all(row["ambiguities"] == [] and row["hook_findings"] == ["fixture teaching gap"] for row in rows)
    rivals, declarations, errors = probe.declared_rivals(SimpleNamespace(SEMANTIC_RIVALS={"bad": 7}))
    assert rivals == {}
    assert declarations["SEMANTIC_RIVALS"] == {"present": True, "names": []}
    assert "expected nonempty string name and callable" in errors[0]


def test_status_requires_named_contract_and_complete_coverage():
    report = {"errors": [], "rivals": ["fixture"], "failures": [], "coverage_complete": True,
              "summary": {"rotations_scored": 3}, "sampler": {"expected_rotations": 3}}
    assert probe.report_status(report) == "no_declared_ambiguity"
    assert probe.report_status({**report, "rivals": []}) == "no_contract"
    assert probe.report_status({**report, "coverage_complete": False}) == "incomplete"
    assert probe.report_status({**report, "summary": {"rotations_scored": 2}}) == "incomplete"
    assert probe.report_status({**report, "failures": ["literal duplicate fixture"]}) == "failed"
    assert probe.report_status({**report, "summary": {"ambiguous_rotations": 1}}) == "ambiguous"
    assert probe.report_status({**report, "errors": ["literal authority failure"]}) == "error"


def test_explicit_module_selection_supports_both_owned_layouts(tmp_path):
    library = tmp_path / "library"
    library_source = library / "generators/fixture/generator.py"
    library_source.parent.mkdir(parents=True)
    library_source.write_text("TAG = 'library'\n")
    portable = tmp_path / "portable"
    portable_source = portable / "puzzle_generators/per_puzzle/fixture/generator.py"
    portable_source.parent.mkdir(parents=True)
    portable_source.write_text("TAG = 'runtime'\n")
    assert probe.load_source(probe.select_generator(library, "fixture"), "test_probe").TAG == "library"
    assert probe.load_source(probe.select_generator(portable, "fixture"), "test_probe").TAG == "runtime"
    with pytest.raises(ValueError, match="invalid task ID"):
        probe.select_generator(library, "../fixture")


def test_default_band_is_optional_and_unambiguous():
    assert probe.parse_bands("easy,medium,hard,default") == ("easy", "medium", "hard", None)
    with pytest.raises(Exception, match="distinct"):
        probe.parse_bands("default,none")
