"""Meaningful diagnostics tests, independent of changing generator strategy."""
from __future__ import annotations
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest

PATH = Path(__file__).resolve().parents[1] / "workspace/lesson_probe.py"
SPEC = importlib.util.spec_from_file_location("task_local_lesson_probe", PATH)
probe = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(probe)

FOUR_STATES = [[0, 0, 8, 8, 4, 0, 5, 0, 5]]
MISSING_01 = [[0, 8, 8, 4, 0, 0, 5]]


def test_all_truth_tables_are_independent_and_have_correct_bit_order():
    assert probe.occupancy_states(FOUR_STATES) == [0, 1, 2, 3]
    outputs = [probe.boolean_output(FOUR_STATES, table) for table in range(16)]
    assert len({probe.grid_hash(grid) for grid in outputs}) == 16
    assert outputs[6] == [[0, 2, 2, 0]]
    assert outputs[4] == [[0, 0, 2, 0]]
    assert outputs[9] == [[2, 0, 0, 2]]
    with pytest.raises(ValueError):
        probe.boolean_output(FOUR_STATES, True)


def test_query_disagreement_is_distinguished_from_demo_survival():
    competitors = {"actual_declaration_name": lambda grid: probe.boolean_output(grid, 4)}
    inspection, outputs = probe.inspect_lesson([MISSING_01] * 3 + [FOUR_STATES], competitors)
    assert inspection["boolean_survivors"] == [4, 6]
    assert inspection["boolean_query_disagreeing_survivors"] == [4]
    assert inspection["declaration_survivors"] == ["actual_declaration_name"]
    assert inspection["query_disagreeing_survivors"] == ["actual_declaration_name"]
    assert outputs[3] == [[0, 2, 2, 0]]
    no_query_difference, _ = probe.inspect_lesson([MISSING_01] * 4, competitors)
    assert no_query_difference["declaration_survivors"]
    assert no_query_difference["query_disagreeing_survivors"] == []
    assert no_query_difference["boolean_query_disagreeing_survivors"] == []


def test_competitors_are_actual_declarations_and_cannot_mutate_input():
    def mutating_rival(grid):
        grid[0][0] = 9
        return probe.boolean_output(grid, 4)
    source = SimpleNamespace(LESSON_COMPETITORS={"newly_added_rival": mutating_rival})
    names = probe.declarations(source, "LESSON_COMPETITORS")
    assert list(names) == ["newly_added_rival"]
    pristine = [row[:] for row in FOUR_STATES]
    probe.inspect_lesson([FOUR_STATES] * 4, names)
    assert FOUR_STATES == pristine
    with pytest.raises(ValueError, match="dict"):
        probe.declarations(SimpleNamespace(LESSON_COMPETITORS=("copied_name",)), "LESSON_COMPETITORS")


def test_claimed_shortcut_must_fit_every_canonical_pair():
    pairs = [{"split": "train", "index": i, "input": FOUR_STATES,
              "output": probe.boolean_output(FOUR_STATES, 6)} for i in range(5)]
    pairs[4] = {"split": "test", "index": 0, "input": MISSING_01,
                "output": probe.boolean_output(MISSING_01, 6)}
    def only_fits_first_four(grid):
        if len(grid[0]) == 9:
            return probe.boolean_output(grid, 6)
        return [[9]]
    result = probe.canonical_checks({"claim": only_fits_first_four}, pairs)
    assert not result["claim"]["fits_all"]
    assert [record["fits"] for record in result["claim"]["pairs"]] == [True] * 4 + [False]


def test_overlapping_windows_have_separate_counts_and_all_cyclic_starts():
    module = SimpleNamespace(SCHEDULE_PROFILES=("core", "transfer", "broad"),
                             generate=lambda seed, index, **kw: [row[:] for row in FOUR_STATES],
                             self_check=lambda grid, **kw: [])
    report = probe.measure(module, {"all_zero": lambda grid: probe.boolean_output(grid, 0)}, {},
                           lessons_per_band=6, overlap_windows=5, seed=17)
    assert report["schedule_cycle_length"] == 3
    assert report["global_union_counts"]["all"] == {
        "distinct_inputs": 1, "distinct_outputs": 1, "distinct_pairs": 1, "distinct_lessons": 1}
    for band in probe.BANDS:
        independent, overlapping = (report["bands"][band][key] for key in ("independent", "overlapping"))
        assert independent["lesson_count"] == 6
        assert independent["schedule_starts"] == {"0": 2, "1": 2, "2": 2}
        assert overlapping["lesson_count"] == 5
        assert overlapping["schedule_starts"] == {"0": 2, "1": 2, "2": 1}
        assert independent["input_appearances"] == 24
        assert independent["distinct_inputs"] == independent["distinct_outputs"] == 1
        assert independent["distinct_lessons"] == 1
        assert independent["boolean_survival_counts"]["6"] == 6
        assert len(independent["boolean_survival_counts"]) == 16
        assert not independent["failures"]
        assert independent["first_rejections"]["all_zero"]["sample_index"] == 0
        assert overlapping["seeds_and_sample_indices"][0] == {"seed": 23, "sample_indices": [0, 1, 2, 3]}
        assert overlapping["seeds_and_sample_indices"][1]["sample_indices"] == [1, 2, 3, 4]


def test_first_real_ambiguity_retains_seed_indices_and_complete_lesson():
    module = SimpleNamespace(SCHEDULE_PROFILES=("core", "transfer"),
                             generate=lambda seed, index, **kw: [row[:] for row in (FOUR_STATES if index == 3 else MISSING_01)],
                             self_check=lambda grid, **kw: [])
    report = probe.measure(module, {"left_only": lambda grid: probe.boolean_output(grid, 4)}, {},
                           lessons_per_band=1, overlap_windows=0, seed=29)
    witness = report["first_genuine_ambiguous_lesson"]
    assert witness["seed"] == 29 and witness["sample_indices"] == [0, 1, 2, 3]
    assert len(witness["demonstrations"]) == 3
    assert witness["query"]["input"] == FOUR_STATES
    assert witness["query_disagreeing_survivors"] == ["left_only"]


@pytest.mark.parametrize("bad", [[], [[]], [[False, 4, 0]], [[0, 4, 0], [0]],
                                 [[0, 0, 0]], [[4, 4, 0]], [[0, 4, 10]], [[0, 4, 0.0]]])
def test_python_diagnostic_rejects_malformed_inputs(bad):
    with pytest.raises(ValueError):
        probe.boolean_output(bad, 6)


def test_portable_runtime_bootstrap_imports_generator_without_checkout(tmp_path):
    runtime = tmp_path / "portable"
    package = runtime / "puzzle_generators"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text("")
    (package / "base.py").write_text("PORTABLE_MARKER = 173\n")
    generator_file = package / "per_puzzle/task/generator.py"
    generator_file.parent.mkdir(parents=True)
    generator_file.write_text("from puzzle_generators.base import PORTABLE_MARKER\nVERSION = str(PORTABLE_MARKER)\n")
    script = ("import importlib.util; from pathlib import Path; "
              f"spec=importlib.util.spec_from_file_location('probe', {str(PATH)!r}); "
              "probe=importlib.util.module_from_spec(spec); spec.loader.exec_module(probe); "
              f"gen=probe.load_generator(Path({str(generator_file)!r}), Path({str(runtime)!r})); "
              "assert gen.VERSION == '173'")
    subprocess.run([sys.executable, "-c", script], check=True, capture_output=True, text=True)


def test_canonical_authority_hashes_exact_rule_and_records(tmp_path):
    canonical = tmp_path / "canonical.jsonl"
    row = {"task_id": probe.TASK_ID, "program_solution": "(lambda  (g)\n g)",
           "train": [{"input": FOUR_STATES, "output": [[0, 2, 2, 0]]}], "test": []}
    canonical.write_text(json.dumps(row) + "\n")
    pairs, hashes = probe.authority(canonical)
    assert len(pairs) == 1
    assert hashes["rule_text_sha256"] == probe.sha256(row["program_solution"].encode())
    assert hashes["rule_normalized_sha256"] == probe.sha256(b"(lambda (g) g)")
    assert hashes["canonical_file_sha256"] == probe.sha256(canonical.read_bytes())


def test_parity_matrix_covers_all_64_ordered_pairs_and_edges():
    module = SimpleNamespace(generate=lambda *args, **kw: [row[:] for row in FOUR_STATES],
                             PANEL_PATTERNS=("random", "checker"), DEGENERATE_TEXTURES=("all_zero",))
    cases = probe.parity_matrix(module, 0)
    color_cases = [case for case in cases if case["kind"] == "ordered_foreground_pair"]
    assert len(color_cases) == 64
    assert len({(case["left"], case["right"]) for case in color_cases}) == 64
    assert {case["left"] for case in color_cases} == {1, 2, 3, 5, 6, 7, 8, 9}
    assert len([case for case in cases if case["kind"] == "dimension_and_occupancy_edge"]) == 16
    assert len([case for case in cases if case["kind"] == "default"]) == 4
    assert len([case for case in cases if case["kind"] == "texture"]) == 3
    assert all(probe.boolean_output(case["input"], 6) is not None for case in cases)


def test_public_racket_route_binds_rule_authority_and_keeps_outputs_distinct(monkeypatch):
    calls = []
    class FakeCatalog:
        def __init__(self, root):
            self.root = root
        def apply(self, task, inputs, **options):
            calls.append((task, inputs, options))
            return {"rule_text_sha256": "exact-authority", "rule_hash_matches_catalog": True,
                    "executed_rule_hash": "normalized-a", "generator_sha256": "loaded-generator",
                    "results": [{"output": probe.boolean_output(grid, 6), "error": None} for grid in inputs]}
    monkeypatch.setitem(sys.modules, "arcpuzzles", SimpleNamespace(Catalog=FakeCatalog))
    monkeypatch.setitem(sys.modules, "arcpuzzles.runtime", SimpleNamespace(MAX_APPLY_INPUTS=64))
    module = SimpleNamespace(generate=lambda *args, **kw: FOUR_STATES)
    pairs = [{"split": "test", "index": 0, "input": FOUR_STATES, "output": [[0, 2, 2, 0]]}]
    report = probe.racket_parity(module, Path("/public-library"), seed=3,
                                 expected_rule_normalized_sha256="normalized-authority", canonical_pairs=pairs, expected_generator_sha256="loaded-generator")
    assert report["route"] == "public Catalog.apply"
    assert report["all_match"]
    assert calls[0][0] == probe.TASK_ID
    assert [len(call[1]) for call in calls] == [64, 21]
    assert report["cases"][-1]["kind"] == "canonical"
    assert "racket_output" in report["cases"][0]
    assert "python_xor_output" in report["cases"][0]
    with pytest.raises(ValueError, match="different generator"):
        probe.racket_parity(module, Path("/public-library"), seed=3,
                             expected_rule_normalized_sha256="normalized-authority", expected_generator_sha256="other-generator")
    with pytest.raises(ValueError, match="canonical authority"):
        probe.racket_parity(module, Path("/public-library"), seed=3, expected_rule_normalized_sha256="other-source")


def test_cli_portable_layout_binds_source_tool_rule_and_sampling_provenance(tmp_path):
    runtime = tmp_path / "runtime"
    package = runtime / "puzzle_generators"
    package.mkdir(parents=True)
    (package / "base.py").write_text("# standalone bootstrap marker\n")
    generator_file = package / "per_puzzle/d70726fd510f/generator.py"
    generator_file.parent.mkdir(parents=True)
    generator_file.write_text(
        "VERSION='fixture-1'\nSCHEDULE_PROFILES=('core','transfer','broad')\n"
        "def generate(seed, sample_index, **kw):\n return [[0,0,8,8,4,0,5,0,5]]\n"
        "def self_check(grid, **kw):\n return []\n"
        "def shortcut(grid):\n return [[0,2,2,0]]\n"
        "def rival(grid):\n return [[0,0,0,0]]\n"
        "CANONICAL_SHORTCUTS={'fixture_shortcut':shortcut}\n"
        "LESSON_COMPETITORS={'custom_source_declaration':rival}\n")
    canonical = tmp_path / "canonical.jsonl"
    row = {"task_id": probe.TASK_ID, "program_solution": "(lambda (g) g)",
           "train": [{"input": FOUR_STATES, "output": [[0, 2, 2, 0]]}] * 4,
           "test": [{"input": FOUR_STATES, "output": [[0, 2, 2, 0]]}]}
    canonical.write_text(json.dumps(row) + "\n")
    output = tmp_path / "diagnostic.json"
    command = [sys.executable, str(PATH), "--generator-file", str(generator_file),
               "--runtime-root", str(runtime), "--canonical-file", str(canonical),
               "--lessons-per-band", "3", "--overlap-windows", "2", "--seed", "101",
               "--sample-index", "4", "--out", str(output)]
    subprocess.run(command, check=True, capture_output=True, text=True)
    report = json.loads(output.read_text())
    provenance = report["provenance"]
    assert provenance["generator_sha256"] == probe.sha256(generator_file.read_bytes())
    assert provenance["tool_sha256"] == probe.sha256(PATH.read_bytes())
    assert provenance["rule_text_sha256"] == probe.sha256(row["program_solution"].encode())
    assert provenance["pair_count"] == 5
    assert report["declared_competitors"] == ["custom_source_declaration"]
    assert report["canonical_shortcuts"]["fixture_shortcut"]["fits_all"]
    assert "racket_parity" not in report
    assert "independent Python" in report["label_authority"]
    assert report["lessons"]["bands"]["easy"]["independent"]["seeds_and_sample_indices"][0] == {
        "seed": 101, "sample_indices": [4, 5, 6, 7]}
    # The real CLI gate accepts a four-state lesson which refutes the declared rival.
    passed = subprocess.run(command + ["--require-pass", "--require-rival-refutation"], capture_output=True, text=True)
    assert passed.returncode == 0
    assert json.loads(output.read_text())["diagnostic_gate"]["status"] == "PASS"
    # Run the actual CLI with a separately supplied public package source. The
    # portable runtime has no arcpuzzles package; --library-root must add src.
    public_library = tmp_path / "public-library"
    public_package = public_library / "src/arcpuzzles"
    public_package.mkdir(parents=True)
    expected_generator_hash = probe.sha256(generator_file.read_bytes())
    normalized = probe.sha256(row["program_solution"].encode())[:12]
    public_package.joinpath("runtime.py").write_text("MAX_APPLY_INPUTS=64\n")
    public_package.joinpath("__init__.py").write_text(
        "class Catalog:\n"
        " def __init__(self, root): self.root=root\n"
        " def apply(self, task, inputs, **kw):\n"
        "  results=[]\n"
        "  for grid in inputs:\n"
        "   width=len(grid[0])//2\n"
        "   output=[[2 if bool(row[c]) != bool(row[width+1+c]) else 0 for c in range(width)] for row in grid]\n"
        "   results.append({'output':output,'error':None})\n"
        f"  return {{'executed_rule_hash':{normalized!r},'rule_hash_matches_catalog':True,'rule_text_sha256':'wrapped', 'generator_sha256':{expected_generator_hash!r},'results':results}}\n")
    portable_parity = subprocess.run(command + ["--library-root", str(public_library), "--racket-parity", "--require-pass"],
                                     capture_output=True, text=True)
    assert portable_parity.returncode == 0, portable_parity.stderr + portable_parity.stdout
    routed_report = json.loads(output.read_text())
    assert routed_report["racket_parity"]["all_match"]
    assert len(routed_report["racket_parity"]["application_provenance"]) == 2
    # Preserve the five canonical claims, but make three demos omit01 and let a
    # left-only rival survive them and fail on the four-state query at index7.
    source = generator_file.read_text().replace(
        "return [[0,0,8,8,4,0,5,0,5]]", "return [[0,0,8,8,4,0,5,0,5]] if sample_index == 7 else [[0,8,8,4,0,0,5]]")
    source = source.replace("return [[0,0,0,0]]",
        "return [[2 if row[c] != 0 and row[len(row)//2+1+c] == 0 else 0 for c in range(len(row)//2)] for row in grid]")
    generator_file.write_text(source)
    failed = subprocess.run(command + ["--require-pass"], capture_output=True, text=True)
    assert failed.returncode == 2
    bad_report = json.loads(output.read_text())
    assert bad_report["canonical_shortcuts"]["fixture_shortcut"]["fits_all"]
    assert bad_report["diagnostic_gate"]["status"] == "FAIL"
    assert any(problem["kind"] == "genuine_query_ambiguity" for problem in bad_report["diagnostic_gate"]["problems"])
    assert bad_report["lessons"]["first_genuine_ambiguous_lesson"]["sample_indices"] == [4, 5, 6, 7]
    diagnostic_only = subprocess.run(command, capture_output=True, text=True)
    assert diagnostic_only.returncode == 0


def test_explicit_cycle_makes_baseline_and_final_sampling_plans_identical():
    functions = dict(generate=lambda seed, index, **kw: FOUR_STATES, self_check=lambda grid, **kw: [])
    baseline = SimpleNamespace(**functions)
    final = SimpleNamespace(SCHEDULE_PROFILES=("core", "transfer", "broad"), **functions)
    first = probe.measure(baseline, {}, {}, lessons_per_band=7, overlap_windows=4,
                          seed=0, sample_index=4, schedule_cycle=3)
    second = probe.measure(final, {}, {}, lessons_per_band=7, overlap_windows=4,
                           seed=0, sample_index=4, schedule_cycle=3)
    assert first["generator_declared_schedule_profiles"] == []
    assert first["schedule_cycle_source"] == "explicit diagnostic indexing cycle"
    for band in probe.BANDS:
        for mode in ("independent", "overlapping"):
            assert first["bands"][band][mode]["seeds_and_sample_indices"] == second["bands"][band][mode]["seeds_and_sample_indices"]
