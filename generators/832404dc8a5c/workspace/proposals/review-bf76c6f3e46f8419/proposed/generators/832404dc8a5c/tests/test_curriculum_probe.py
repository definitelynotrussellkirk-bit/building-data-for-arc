"""Read-only curriculum diagnostic tool; separate from generator acceptance."""
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

from reviewer_support import find_root, load_selected_generator


ROOT = find_root(__file__)
SOURCE = Path(__file__).resolve().parents[1] / "workspace/probe_curriculum.py"


def probe():
    assert SOURCE.is_file(), "the requested read-only curriculum probe is missing"
    spec = importlib.util.spec_from_file_location("curriculum_probe", SOURCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_discovers_new_rival_names_and_preserves_namespaces():
    tool = probe()
    identity = lambda grid: grid
    declared = SimpleNamespace(CANONICAL_SHORTCUTS={"newly_declared": identity},
                               LESSON_COMPETITORS={"newly_declared": identity, "another_new_name": identity})
    assert set(tool.declared_rivals(declared)) == {
        "CANONICAL_SHORTCUTS.newly_declared", "LESSON_COMPETITORS.newly_declared",
        "LESSON_COMPETITORS.another_new_name",
    }


def test_difference_counts_missing_extra_and_changed_cells():
    tool = probe()
    result = tool.difference([[0, 6], [6, 0]], [[8], [6, 0], [4]])
    assert result["differing_cells"] == 3
    assert result["first_mismatch"] == {"row": 0, "column": 0, "expected": 0, "actual": 8, "kind": "changed"}


def test_report_records_live_labels_all_rivals_boundary_and_input_only_census():
    tool = probe()
    gen, source, source_hash = load_selected_generator("832404dc8a5c", root=ROOT)
    report = tool.collect_report(root=ROOT, census_seeds=range(1), census_indices=range(2))
    assert report["generator_sha256"] == source_hash == hashlib.sha256(source.read_bytes()).hexdigest()
    assert report["rule_sha256"] == hashlib.sha256(report["rule"].encode()).hexdigest()
    expected_names = {f"{namespace}.{name}" for namespace in tool.NAMESPACES
                      for name in getattr(gen, namespace, {})}
    assert set(report["rival_inventory"]) == expected_names
    assert report["input_size_census"]["label_policy"] == "input-only; no Racket outputs generated"
    assert report["input_size_census"]["total_inputs"] == 6
    assert any(case["height"] == case["width"] == 30 for case in report["cases"])
    assert all(not case["self_check"] for case in report["cases"])
    assert all(case["label_source"] == "live RacketBridge" for case in report["cases"])
    assert all(set(case["rivals"]) == expected_names for case in report["cases"])
    for case in report["cases"]:
        replay = case["replay"]
        assert case["input"] == gen.generate(replay["seed"], replay["sample_index"],
                                             difficulty=replay["difficulty"], **replay["overrides"])
        for name, predict in tool.declared_rivals(gen).items():
            result = predict(deepcopy(case["input"]))
            assert case["rivals"][name]["differing_cells"] == sum(
                left != right for row_a, row_b in zip(case["output"], result)
                for left, right in zip(row_a, row_b)
            )


def test_cli_refuses_existing_output_without_overwriting(tmp_path):
    probe()
    target = tmp_path / "retained.json"
    target.write_text('{"retained":true}\n')
    before = target.read_bytes()
    result = subprocess.run([sys.executable, str(SOURCE), "--out", str(target)],
                            text=True, capture_output=True)
    assert result.returncode != 0
    assert "fresh output" in result.stderr
    assert target.read_bytes() == before
