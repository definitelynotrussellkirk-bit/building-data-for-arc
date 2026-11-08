"""Evidence-scoring regressions; expected grids here are literal fixtures."""
from copy import deepcopy
import hashlib
import importlib.util
from pathlib import Path
from types import SimpleNamespace


def probe_module():
    path = Path(__file__).resolve().parents[1] / "workspace/review_probe.py"
    spec = importlib.util.spec_from_file_location("lesson_review_probe_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def episode(train, test, *, start=0):
    return {
        "train": train, "test": test, "seed": 0, "episode_index": 0,
        "sample_index": start,
        "sample_indices": list(range(start, start + len(train) + len(test))),
        "rejections": [], "executed_rule_hash": "literal-test-rule",
        "provenance": {"generator_sha256": "literal-test-generator",
                       "catalog_rule_hash": "literal-test-rule"},
    }


def test_dynamic_declarations_preserve_both_namespaces():
    probe = probe_module()
    first = lambda grid: grid
    second = lambda grid: [[0]]
    module = SimpleNamespace(CANONICAL_SHORTCUTS={"new_unlisted_name": first},
                             LESSON_COMPETITORS={"new_unlisted_name": second})
    rules = probe.declared_rules(module)
    assert set(rules) == {"CANONICAL_SHORTCUTS.new_unlisted_name",
                          "LESSON_COMPETITORS.new_unlisted_name"}
    assert rules["CANONICAL_SHORTCUTS.new_unlisted_name"]["function"] is first
    assert rules["LESSON_COMPETITORS.new_unlisted_name"]["function"] is second


def test_loaded_generator_is_bound_to_the_exact_captured_source(tmp_path):
    probe = probe_module()
    selected = tmp_path / "generators" / probe.TASK_ID / "generator.py"
    selected.parent.mkdir(parents=True)
    captured = b"MARKER = 'captured source'\n"
    selected.write_bytes(captured)
    module = probe.load_selected_generator(tmp_path)
    selected.write_bytes(b"MARKER = 'later source'\n")
    assert module.MARKER == "captured source"
    assert module.__review_source_sha256 == hashlib.sha256(captured).hexdigest()
    assert module.__review_source_sha256 != probe.file_digest(selected)


def test_canonical_fit_checks_fifth_pair_and_counts_exceptions_separately():
    probe = probe_module()
    pairs = [{"input": [[color]], "output": [[color]]} for color in (1, 2, 3, 4)]
    pairs.append({"input": [[5]], "output": [[0]]})

    def fails_on_fifth(grid):
        if grid == [[5]]:
            raise RuntimeError("fifth pair")
        return grid

    rules = {
        "identity": {"function": lambda grid: grid, "declaration": "CANONICAL_SHORTCUTS", "name": "identity"},
        "exception": {"function": fails_on_fifth, "declaration": "CANONICAL_SHORTCUTS", "name": "exception"},
    }
    fits = probe.canonical_fits(rules, pairs)
    assert fits["identity"]["matching_pairs"] == 4
    assert fits["identity"]["disagreement_pairs"] == [4]
    assert fits["identity"]["fits_every_usable_pair"] is False
    assert fits["exception"]["disagreement_pairs"] == []
    assert fits["exception"]["exceptions"] == [{"pair_index": 4, "error": "RuntimeError: fifth pair"}]


def test_input_mutation_is_not_counted_as_a_genuine_disagreement():
    probe = probe_module()
    pair = {"input": [[1]], "output": [[0]]}

    def mutating(grid):
        grid[0][0] = 2
        return [[2]]

    result = probe.call_rule(mutating, pair)
    assert result["agrees"] is None
    assert result["mutated_input"] is True
    assert result["error"] == "rival mutated its input"
    assert pair == {"input": [[1]], "output": [[0]]}


def test_complete_lesson_outcomes_distinguish_refutation_query_and_error():
    probe = probe_module()
    yes = {"agrees": True, "error": None}
    no = {"agrees": False, "error": None}
    error = {"agrees": None, "error": "RuntimeError"}
    assert probe.lesson_status([yes, no], 1) == "query_discriminates"
    assert probe.lesson_status([yes, yes], 1) == "survived_all"
    assert probe.lesson_status([no, yes], 1) == "refuted_by_demo"
    assert probe.lesson_status([error, no], 1) == "demo_error"
    assert probe.lesson_status([yes, error], 1) == "query_error"


def test_query_witness_does_not_count_as_teaching_in_the_demonstrations():
    probe = probe_module()
    module = SimpleNamespace(lesson_identifiable=lambda demos, query: [])
    rules = {"identity": {"function": lambda grid: grid}}
    data = episode([{"input": [[1]], "output": [[1]]}],
                   [{"input": [[2]], "output": [[0]]}])
    witnesses = {}
    record = probe.assess_lesson(module, rules, data, "easy", "test", witnesses)
    assert record["rivals"]["identity"]["status"] == "query_discriminates"
    assert record["hook_claims_identifiable_but_query_rival_survives"] is True
    assert witnesses["identity"]["split"] == "test"
    summary = probe.summarize([record])
    assert summary["lessons_with_all_declared_rivals_refuted_by_demos"] == 0
    assert summary["lessons_with_query_discriminating_survivor"] == 1


def test_schedule_profile_exceptions_are_reported_without_aborting_the_lesson():
    probe = probe_module()

    def broken_profile(seed, sample_index, difficulty=None):
        raise RuntimeError(f"profile at {sample_index}")

    module = SimpleNamespace(lesson_identifiable=lambda demos, query: [],
                             schedule_profile=broken_profile)
    rules = {"zero": {"function": lambda grid: [[0]]}}
    data = episode([{"input": [[1]], "output": [[0]]}],
                   [{"input": [[2]], "output": [[0]]}])
    record = probe.assess_lesson(module, rules, data, "easy", "test", {})
    assert record["schedule_profiles"] == [None, None]
    assert record["schedule_profile_errors"] == [
        {"sample_index": 0, "error": "RuntimeError: profile at 0"},
        {"sample_index": 1, "error": "RuntimeError: profile at 1"},
    ]
    summary = probe.summarize([record])
    assert summary["schedule_profile_exception_exposures"] == 2
    assert summary["rival_exception_exposures"] == 0
    assert summary["accepted_schedule_profile_exposures"] == {}


def test_overlapping_windows_count_pair_exposures_and_unique_inputs_separately():
    probe = probe_module()
    module = SimpleNamespace(lesson_identifiable=lambda demos, query: [])
    rules = {"zero": {"function": lambda grid: [[0]]}}
    pair_a = {"input": [[1]], "output": [[0]]}
    pair_b = {"input": [[2]], "output": [[0]]}
    pair_c = {"input": [[3]], "output": [[0]]}
    first = probe.assess_lesson(module, rules, episode([pair_a], [pair_b]), "easy", "start0", {})
    second = probe.assess_lesson(module, rules, episode([pair_b], [pair_c], start=1), "easy", "start1", {})
    unchanged = deepcopy([first, second])
    summary = probe.summarize([first, second])
    assert summary["complete_lessons"] == 2
    assert summary["pair_exposures"] == 4
    assert summary["distinct_inputs"] == 3
    assert summary["unique_accepted_draw_coordinates"] == 3
    assert summary["lessons_with_all_declared_rivals_refuted_by_demos"] == 0
    assert [first, second] == unchanged
