"""Replay the bounded, task-specific evidence and exact-override audit.

Run through review.py from the packet outer directory. Payload cwd is WORK/repo.
This script does not edit the generator, its authority, or approval metadata.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import sys
import time


TASK_ID = "69cab6228fdc"
SEED = 20261024


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    if any((args.out / name).exists() for name in ("report.json", "racket.json")):
        raise FileExistsError("use a new evidence output directory")
    started = time.monotonic()
    root = Path.cwd().resolve()
    source = root / "generators" / TASK_ID / "generator.py"
    probe_source = source.parent / "workspace" / "passthrough_probe.py"
    sys.path.insert(0, str(root / "shared" / "runtime"))
    sys.path.insert(0, str(root / "src"))
    from reviewer_support import canonical_pairs, load_selected_generator
    from arcpuzzles.catalog import Catalog

    gen, _, source_hash = load_selected_generator(TASK_ID, root=root)
    spec = importlib.util.spec_from_file_location("boundary_passthrough_probe", probe_source)
    probe = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(probe)
    pairs = canonical_pairs(TASK_ID, root=root, variant=0)
    failures = []
    evidence_cases = []
    tampered = copy.deepcopy(pairs)
    tampered[0]["output"][0][0] = (tampered[0]["output"][0][0] + 1) % 10
    evidence_inputs = (
        ("empty", [], "fail", "empty"),
        ("omitted", None, "pass", "not_provided"),
        ("canonical", pairs, "pass", "checked"),
        ("tampered_label", tampered, "fail", "checked"),
    )
    for name, supplied, expected_status, expected_evidence in evidence_inputs:
        report = probe.run_probe(generator=gen, canonical_pairs=supplied, per_band=4, seed=SEED)
        actual = {"name": name, "status": report["status"],
                  "canonical_evidence": report["canonical_evidence"],
                  "canonical_shortcuts": report["canonical_shortcuts"],
                  "failures": report["failures"]}
        evidence_cases.append(actual)
        if (report["status"] != expected_status
                or report["canonical_evidence"]["status"] != expected_evidence):
            failures.append({"surface": "evidence", "case": name, "actual": actual})
    for per_band in (0, -1):
        try:
            probe.run_probe(generator=gen, canonical_pairs=pairs, per_band=per_band)
        except ValueError as error:
            evidence_cases.append({"name": f"per_band={per_band}",
                                   "status": "rejected", "error": str(error)})
        else:
            failures.append({"surface": "evidence", "case": f"per_band={per_band}",
                             "error": "nonpositive sample count did not raise ValueError"})
    for name, malformed in (
        ("missing_input", {"output": pairs[0]["output"]}),
        ("missing_output", {"input": pairs[0]["input"]}),
    ):
        try:
            probe.run_probe(generator=gen, canonical_pairs=[malformed], per_band=4)
        except KeyError as error:
            evidence_cases.append({"name": name, "status": "rejected",
                                   "error": f"KeyError: {error}"})
        else:
            failures.append({"surface": "evidence", "case": name,
                             "error": "missing required canonical field was not rejected"})

    boundary_cases = 0
    boundary_inputs = []
    combinations = itertools.product(
        (None, "easy", "medium", "hard"), (7, 14), (6, 14), (2, 3, 4),
        ("scattered", "contiguous"), ("sparse", "medium", "dense"),
        ("absent", "present"),
    )
    parity_keys = {
        (None, 7, 6, 3, "scattered", "sparse", "present"),
        (None, 14, 14, 4, "contiguous", "dense", "present"),
        (None, 14, 6, 2, "contiguous", "sparse", "absent"),
        (None, 7, 14, 4, "scattered", "medium", "absent"),
    }
    for index, values in enumerate(combinations):
        if time.monotonic() - started > 240:
            failures.append({"surface": "boundaries", "error": "240-second budget exceeded"})
            break
        difficulty, height, width, n_pairs, layout, profile, mode = values
        overrides = dict(grid_h=height, grid_w=width, n_pairs=n_pairs,
                         legend_layout=layout, body_profile=profile, passthrough=mode)
        boundary_cases += 1
        try:
            grid = gen.generate(SEED, index, difficulty=difficulty, **overrides)
            assert gen.self_check(grid) == []
            assert gen.observe_overrides(grid) == overrides
            sources = {value for value in grid[0] if value}
            targets = {value for value in grid[1] if value}
            body = [value for row in grid[3:] for value in row]
            unmapped = set(body) - sources - {0}
            expected_unmapped = min(2, 9 - 2 * n_pairs) if mode == "present" else 0
            assert len(unmapped) == expected_unmapped
            assert not unmapped & targets
            assert all(body.count(value) >= 2 for value in unmapped)
            assert all(any(row) for row in grid[3:])
            if values in parity_keys:
                boundary_inputs.append({"name": f"boundary-{index}", "input": grid,
                                        "output": gen.rule_mirror(grid),
                                        "difficulty": difficulty, "overrides": overrides})
        except Exception as error:
            failures.append({"surface": "boundaries", "sample_index": index,
                             "difficulty": difficulty, "overrides": overrides,
                             "error": f"{type(error).__name__}: {error}"})

    selected = [{"name": f"canonical-{p['split']}-{p['pair_index']}",
                 "input": p["input"], "output": p["output"]} for p in pairs]
    selected.append({"name": "two-unmapped-exact-witness", "input": probe.EXACT_WITNESS,
                     "output": [[3, 5, 6, 0, 0, 0], [4, 6, 5, 0, 0, 0],
                                [3, 4, 5, 6, 0, 0], [4, 3, 6, 5, 0, 0]]})
    selected.extend(boundary_inputs)
    applied = Catalog(root).apply(TASK_ID, [row["input"] for row in selected],
                                  check_generator_domain=True, timeout=60)
    (args.out / "racket.json").write_text(json.dumps(applied, indent=2) + "\n")
    parity = []
    for row, actual in zip(selected, applied["results"], strict=True):
        same = actual["output"] == row["output"] == gen.rule_mirror(row["input"])
        parity.append({"name": row["name"], "matches": same,
                       "input_sha256": actual["input_sha256"],
                       "output_sha256": actual["output_sha256"]})
        if not same or actual["error"] or not actual["valid_output"]:
            failures.append({"surface": "racket_parity", "case": row["name"]})
    report = {
        "schema": "69cab6228fdc-bounded-audit-v1", "task_id": TASK_ID,
        "argv": sys.argv, "cwd": str(root), "seed": SEED,
        "elapsed_seconds": round(time.monotonic() - started, 3), "budget_seconds": 300,
        "generator_sha256": source_hash, "generator_version": gen.VERSION,
        "probe_sha256": hashlib.sha256(probe_source.read_bytes()).hexdigest(),
        "rule_hash": applied["executed_rule_hash"], "rule_text_sha256": applied["rule_text_sha256"],
        "surfaces": {"evidence_nonvacuity_and_label_integrity": evidence_cases,
                     "joint_override_and_palette_boundaries": {"cases": boundary_cases,
                         "difficulties": [None, "easy", "medium", "hard"],
                         "heights": [7, 14], "widths": [6, 14], "pair_counts": [2, 3, 4],
                         "legend_layouts": ["scattered", "contiguous"],
                         "body_profiles": ["sparse", "medium", "dense"],
                         "passthrough_modes": ["absent", "present"]}},
        "racket_parity": parity, "failures": failures,
        "status": "pass" if not failures else "fail",
        "limits": ["Finite boundary and rival coverage; production and canonical authority unchanged.",
                   "The generator still caps fallback colors at two and excludes legend targets in the body.",
                   "Omitted canonical evidence explicitly means the canonical check was not run."]}
    (args.out / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"status": report["status"], "boundary_cases": boundary_cases,
                      "evidence_cases": len(evidence_cases), "racket_pairs": len(parity),
                      "failures": failures, "elapsed_seconds": report["elapsed_seconds"]}))
    return bool(failures)


if __name__ == "__main__":
    raise SystemExit(main())
