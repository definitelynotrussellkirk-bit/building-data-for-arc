from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

TASK_ID = "f41ae450c30b"
TARGET = Path(__file__).resolve().parents[1]
REPO = TARGET.parents[1]
RUNTIME = REPO / "shared" / "runtime"
CANONICAL = REPO / "shared" / "data" / "canonical" / "puzzles.jsonl"

if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))


def _load(path: Path, name: str):
    sys.modules.pop(name, None)
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _canonical_pairs() -> list[dict]:
    with CANONICAL.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return [*row["train"], *row["test"]]
    raise AssertionError(f"missing canonical row for {TASK_ID}")


def test_independent_probe_solver_matches_canonical_and_generated_cases():
    probe = _load(TARGET / "workspace" / "reference_probe.py", "f41_probe")
    generator = _load(TARGET / "generator.py", "f41_generator_for_probe")

    for pair in _canonical_pairs():
        assert probe.solve_visibility_matrix(pair["input"]) == pair["output"]

    for index in range(24):
        grid = generator.generate(8100 + index, index, difficulty=("easy", "medium", "hard")[index % 3])
        assert probe.has_third_object_occlusion(grid)
        assert probe.solve_visibility_matrix(grid) == generator.rule_mirror(grid)
        assert probe.solve_visibility_matrix(grid) != probe.solve_alignment_only(grid)


def test_probe_audit_reports_exact_contract_without_generator_private_helpers():
    probe = _load(TARGET / "workspace" / "reference_probe.py", "f41_probe_audit")
    generator = _load(TARGET / "generator.py", "f41_generator_for_audit")

    report, _ = probe.audit(generator, per_band=8)
    assert report["counts"] == {
        "samples": 24,
        "self_check_errors": 0,
        "nondeterministic": 0,
        "solver_mismatches": 0,
        "observer_mismatches": 0,
        "missing_occlusion_witness": 0,
        "alignment_rival_agreements": 0,
    }
    assert set(report["by_band"]) == {"easy", "medium", "hard"}
    assert all(band["samples"] == 8 for band in report["by_band"].values())
    assert all(band["occlusion_witnesses"] == 8 for band in report["by_band"].values())
