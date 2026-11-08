"""Focused regressions for source-bound canonical input-behavior coverage."""
import hashlib
import importlib.util
import json
from pathlib import Path
from reviewer_support import find_root


ROOT = find_root(__file__)
TASK_DIR = next(p for p in Path(__file__).resolve().parents
                if p.is_relative_to(ROOT) and p.name == "d7f13ee34d85" and (p / "generator.py").is_file())
GATE = TASK_DIR / "workspace" / "canonical_behavior_gate.py"


def load_gate():
    assert GATE.is_file(), "the task-local canonical behavior gate must exist"
    spec = importlib.util.spec_from_file_location("d7f13ee34d85_behavior_gate_test", GATE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def scene(*, canonical):
    grid = [[0] * 16 for _ in range(13)]
    frames = [(1, 1, 4, 4, 8), (1, 8, 5 if canonical else 6, 6, 8 if canonical else 9)]
    for top, left, height, width, color in frames:
        for r in range(top, top + height):
            for c in range(left, left + width):
                if r in (top, top + height - 1) or c in (left, left + width - 1):
                    grid[r][c] = color
    shapes = ([(8, 1), (9, 1), (10, 1)], [(8, 6), (9, 6), (10, 6), (10, 7)]) if canonical else (
        [(8, 1), (8, 2)], [(8, 6), (9, 6), (9, 7)])
    for color, cells in zip((2, 3), shapes):
        for r, c in cells:
            grid[r][c] = color
    return grid


def fixture_files(tmp_path, *, supported=False, first_index_only=False):
    canonical = scene(canonical=True)
    baseline = scene(canonical=False)
    ledger = tmp_path / "shared/data/canonical/puzzles.jsonl"
    ledger.parent.mkdir(parents=True)
    ledger.write_text(json.dumps({"task_id": "d7f13ee34d85", "program_solution": "(rule! g)",
                                 "train": [{"input": canonical, "output": canonical}], "test": []}) + "\n")
    source = tmp_path / "generator.py"
    expression = "SUPPORTED if sample_index == 0 else BASELINE" if first_index_only else (
        "SUPPORTED" if supported else "BASELINE")
    source.write_text("EXAMPLES_NEEDED = 3\nSUPPORTED = " + repr(canonical) + "\nBASELINE = " + repr(baseline)
                      + "\ndef generate(seed, sample_index, *, difficulty=None):\n    return " + expression + "\n")
    return source, ledger


def run(gate, root, source, **options):
    return gate.audit(root=root, generator_file=source, samples=3, lessons=2,
                      bands=("easy",), seed=12, **options)


def test_missing_canonical_behaviors_fail_even_when_all_inputs_are_valid(tmp_path):
    gate = load_gate()
    source, _ = fixture_files(tmp_path)
    report = run(gate, tmp_path, source)
    assert report["status"] == "fail"
    assert {x["feature"] for x in report["missing_ordinary_support"]} == set(gate.FEATURES)
    assert report["canonical"]["feature_counts"] == dict.fromkeys(gate.FEATURES, 1)
    assert report["errors"] == []


def test_support_retains_witnesses_and_does_not_overstate_duplicate_inputs(tmp_path):
    gate = load_gate()
    source, _ = fixture_files(tmp_path, supported=True)
    report = run(gate, tmp_path, source)
    assert report["status"] == "pass"
    ordinary = report["bands"]["easy"]["ordinary"]
    assert ordinary["count"] == 3 and ordinary["unique_inputs"] == 1
    assert report["demos"] == 3 and report["demos_source"] == "generator.EXAMPLES_NEEDED"
    assert {r["sample_index"] for r in ordinary["draws"]} == {0}
    assert len({r["seed"] for r in ordinary["draws"]}) == 3
    assert set(ordinary["witnesses"]) == set(gate.FEATURES)
    assert all(gate.extract_features(w["input"])[name] for name, w in ordinary["witnesses"].items())
    assert report["reference_executed"] is False
    assert report["verdict_scope"] == "finite_input_behavior_support_only"


def test_generator_and_rule_hashes_bind_identical_behavior_to_exact_source(tmp_path):
    gate = load_gate()
    source, ledger = fixture_files(tmp_path, supported=True)
    before = run(gate, tmp_path, source)
    source.write_text(source.read_text() + "\n# semantic no-op\n")
    row = json.loads(ledger.read_text())
    row["program_solution"] = "(rule! (let ((x g)) x))"
    ledger.write_text(json.dumps(row) + "\n")
    after = run(gate, tmp_path, source)
    assert before["status"] == after["status"] == "pass"
    assert before["generator_sha256"] != after["generator_sha256"]
    assert after["generator_sha256"] == hashlib.sha256(source.read_bytes()).hexdigest()
    assert before["canonical_program_text_sha256"] != after["canonical_program_text_sha256"]
    assert after["canonical_program_text_sha256"] == hashlib.sha256(row["program_solution"].encode()).hexdigest()


def test_lesson_exposure_is_diagnostic_unless_feature_is_a_teaching_target(tmp_path):
    gate = load_gate()
    source, _ = fixture_files(tmp_path, first_index_only=True)
    ordinary_only = run(gate, tmp_path, source)
    strict = run(gate, tmp_path, source, lesson_target_features=("negative_centering_offset",))
    assert ordinary_only["status"] == "pass"
    assert strict["status"] == "fail"
    assert strict["missing_ordinary_support"] == []
    assert strict["bands"]["easy"]["lessons"]["zero_demo_windows"]["negative_centering_offset"] == 1
    assert strict["missing_lesson_targets"] == [
        {"band": "easy", "lesson_index": 1, "feature": "negative_centering_offset"}]
