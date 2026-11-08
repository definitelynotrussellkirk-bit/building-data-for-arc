#!/usr/bin/env python3
"""Reproduce the two adversarial-audit probes for this review packet."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

PACKET = Path(__file__).resolve().parents[2]
REPO = PACKET / "repo"
sys.path.insert(0, str(REPO / "shared/runtime"))
from reviewer_support import canonical_pairs  # noqa: E402


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_generator(task_id: str):
    path = REPO / "generators" / task_id / "generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_{task_id}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module, path


def probe_rotation_task() -> dict:
    task_id = "1d26c382ab68"
    module, path = load_generator(task_id)
    failures: list[dict] = []
    seen: set[str] = set()
    slots, rotations, colors, dims = set(), set(), set(), set()
    draws = 0
    band_ids = {None: 0, "easy": 1, "medium": 2, "hard": 3}
    for band, band_id in band_ids.items():
        for sample_index in range(150):
            seed = 700_000 + band_id * 10_000 + sample_index
            try:
                grid = module.generate(seed, sample_index, difficulty=band)
                info = module._structure(grid)
                observed = module.observe_overrides(grid)
                findings = module.self_check(grid)
                if findings:
                    failures.append({"band": band, "sample_index": sample_index,
                                     "check": "self_check", "detail": findings})
                if observed["match_slot"] != sample_index % 3:
                    failures.append({"band": band, "sample_index": sample_index,
                                     "check": "slot_schedule", "observed": observed["match_slot"]})
                expected_rotation = ("0", "90", "180", "270")[sample_index % 4]
                if observed["match_rotation"] != expected_rotation:
                    failures.append({"band": band, "sample_index": sample_index,
                                     "check": "rotation_schedule",
                                     "observed": observed["match_rotation"]})
                if not info["reflection_distractor"]:
                    failures.append({"band": band, "sample_index": sample_index,
                                     "check": "reflection_missing"})
                if module.expected_output(grid) == grid:
                    failures.append({"band": band, "sample_index": sample_index,
                                     "check": "identity"})
                seen.add(json.dumps(grid, separators=(",", ":")))
                slots.add(observed["match_slot"])
                rotations.add(observed["match_rotation"])
                colors.add(observed["candidate_color"])
                dims.add((observed["grid_h"], observed["grid_w"]))
                draws += 1
            except Exception as exc:  # retained as structured evidence
                failures.append({"band": band, "sample_index": sample_index,
                                 "check": "exception",
                                 "detail": f"{type(exc).__name__}: {exc}"})
    return {
        "schema": "audit-1d26c382ab68-v1",
        "task_id": task_id,
        "generator_sha256": sha256(path),
        "rule_hash": getattr(module, "RULE_HASH", None),
        "draws": draws,
        "unique_inputs": len(seen),
        "match_slots": sorted(slots),
        "match_rotations": sorted(rotations),
        "candidate_colors": sorted(colors),
        "dimension_profiles": [list(item) for item in sorted(dims)],
        "structural_failures": failures,
        "portable_task_test_result": "1 failed, 13 passed",
        "portable_task_test_evidence": "checks/audit/1d26c382ab68/task-tests/result.json",
        "portable_test_defect": (
            "test resolves canonical data under generators/1d26c382ab68/"
            "data/canonical/puzzles.jsonl, absent from portable runtime"
        ),
        "command": ["python3", "checks/audit/run_audit_probes.py"],
        "cwd": "packet_root",
    }


def probe_priority_task() -> dict:
    task_id = "a5b0638997f5"
    module, path = load_generator(task_id)
    pairs = canonical_pairs(task_id, root=REPO)
    counterexamples = []
    for index, pair in enumerate(pairs):
        findings = module.self_check(pair["input"])
        if findings:
            counterexamples.append({
                "canonical_pair_index": index,
                "variant": pair["variant"],
                "split": pair["split"],
                "pair_index": pair["pair_index"],
                "input": pair["input"],
                "self_check_errors": findings,
            })
    return {
        "schema": "audit-a5b0638997f5-v1",
        "task_id": task_id,
        "generator_sha256": sha256(path),
        "catalog_rule_hash": "9991f0c71fc6",
        "canonical_pairs_checked": len(pairs),
        "canonical_inputs_rejected": len(counterexamples),
        "counterexamples": counterexamples,
        "battery_evidence": "checks/audit/a5b0638997f5/battery/result.json",
        "additional_reproduced_findings": [
            "missing RULE_HASH",
            "canonical palette 6 unreachable (generated palette fixed at 5)",
            "dead/overlapping texture domain",
            "unknown override key accepted",
        ],
        "command": ["python3", "checks/audit/run_audit_probes.py"],
        "cwd": "packet_root",
    }


def main() -> int:
    outputs = {
        "1d26c382ab68/probe.json": probe_rotation_task(),
        "a5b0638997f5/canonical-validator-counterexample.json": probe_priority_task(),
    }
    root = PACKET / "checks/audit"
    for relative, report in outputs.items():
        destination = root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"{destination.relative_to(PACKET)}: "
              f"{len(report.get('structural_failures', report.get('counterexamples', [])))} findings")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
