from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys

from reviewer_support import find_root

TASK_ID = "c3052979ff96"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK_ID
PROBE_PATH = HOME / "workspace" / "reference_probe.py"


def _load_probe():
    spec = importlib.util.spec_from_file_location(
        "reference_probe_c3052979ff96", PROBE_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_reference_probe_independently_exposes_both_decisive_rivals():
    probe = _load_probe()
    canonical = probe.canonical_report()
    assert canonical == {
        "pairs": 5,
        "oracle_matches": 5,
        "code_one_is_clockwise_matches": 5,
        "strip_unrelated_objects_matches": 0,
        "canonical_codes": [2, 3, 4],
    }

    gen = probe.load_generator()
    witness = gen.generate(
        20261011,
        0,
        grid_profile="13x13",
        code_value=1,
        shape_id=4,
        source_quadrant=2,
        n_distractors=4,
    )
    analysis = probe.analyze_grid(witness)
    assert analysis["code"] == 1
    assert analysis["distractor_components"] == 4
    assert analysis["code_one_is_clockwise_diff_cells"] > 0
    assert analysis["strip_unrelated_objects_diff_cells"] > 0
    assert analysis["intended_output"] == gen.rule_mirror(witness)


def test_reference_probe_cli_writes_source_bound_report(tmp_path):
    report_path = tmp_path / "probe.json"
    result = subprocess.run(
        [
            sys.executable,
            str(PROBE_PATH),
            "--generated",
            "8",
            "--json-out",
            str(report_path),
        ],
        cwd=tmp_path,
        text=True,
        capture_output=True,
    )
    assert result.returncode == 0, result.stderr + result.stdout
    report = json.loads(report_path.read_text())
    assert report["task_id"] == "c3052979ff96"
    assert report["rule_hash"] == "a9dc0b2876d4"
    assert len(report["generator_sha256"]) == 64
    assert report["canonical"]["code_one_is_clockwise_matches"] == 5
    assert report["generated"]["draws"] == 8
    assert report["generated"]["self_check_failures"] == []
    assert report["generated"]["oracle_mismatches"] == []
    assert report["generated"]["code_one_counterexamples"] >= 2
    assert report["generated"]["strip_counterexamples"] == 8
    assert report["witness"]["analysis"]["code"] == 1


def test_retained_strongest_shortcut_counterexample_replays_exactly():
    probe = _load_probe()
    path = HOME / "counterexamples" / "strongest-canonical-shortcut.json"
    payload = json.loads(path.read_text())
    assert payload["task_id"] == "c3052979ff96"
    assert payload["rule_hash"] == "a9dc0b2876d4"
    assert payload["intended_output"] == probe.intended_output(payload["input"])
    assert payload["rival_output"] == probe.code_one_is_clockwise(payload["input"])
    assert payload["racket_output"] == payload["intended_output"]
    assert payload["rival_output"] != payload["intended_output"]
    assert payload["differing_cells"] == probe._diff_cells(
        payload["intended_output"], payload["rival_output"]
    )
