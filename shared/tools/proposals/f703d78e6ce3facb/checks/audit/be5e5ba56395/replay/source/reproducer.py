#!/usr/bin/env python3
"""Reproduce the exact-source component-validator gap in be5e5ba56395.

Run from the packet outer directory after the blind solve::

    python3 review.py run ../.venv-review/bin/python \
      ../checks/audit/be5e5ba56395/reproducer.py \
      --out ../checks/audit/be5e5ba56395/replay

Imports use the wrapper's public API paths. find_root(__file__) resolves either
WORK/checks/... with WORK/repo beside it or a retained task-local evidence tree.
The output directory must be new. Use TMPDIR outside retained checks for the
single Catalog.apply staging tree. Only this evidence folder is written.

The malformed witness is hand-authored, not claimed to be a generator draw.
The source checksum guard prevents silently applying this finding to new bytes.
Reference labels come only from the actual selected Racket rule. The pure rival
below outlines already-solid components and preserves a malformed component;
it is a diagnostic comparison outside the written domain, not a demonstrated
in-domain competing rule or complete-lesson ambiguity.
"""
from __future__ import annotations

import argparse
from collections import deque
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
from typing import Any

from arcpuzzles import Catalog
from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator

TASK_ID = "be5e5ba56395"
AUDITED_SHA256 = "1f7dc969ae2a45b93d933594b50e8185cfc01b7c4cd76f40a8626475c307a6e3"


def digest(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def grid_digest(grid: list[list[int]]) -> str:
    return digest(json.dumps(grid, separators=(",", ":")).encode())


def components(grid: list[list[int]]) -> list[dict[str, Any]]:
    """Analyze same-color 4-connected components; does not produce rule labels."""
    height, width = len(grid), len(grid[0])
    seen = set()
    result = []
    for row in range(height):
        for column in range(width):
            color = grid[row][column]
            if color == 0 or (row, column) in seen:
                continue
            queue = deque([(row, column)])
            seen.add((row, column))
            cells = []
            while queue:
                r, c = queue.popleft()
                cells.append([r, c])
                for rr, cc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                    if 0 <= rr < height and 0 <= cc < width and grid[rr][cc] == color and (rr, cc) not in seen:
                        seen.add((rr, cc))
                        queue.append((rr, cc))
            r0, r1 = min(r for r, c in cells), max(r for r, c in cells)
            c0, c1 = min(c for r, c in cells), max(c for r, c in cells)
            result.append({"color": color, "cells": sorted(cells), "bbox": [r0, c0, r1, c1],
                           "cell_count": len(cells), "bbox_area": (r1 - r0 + 1) * (c1 - c0 + 1),
                           "solid": len(cells) == (r1 - r0 + 1) * (c1 - c0 + 1),
                           "at_least_3_by_3": r1 - r0 >= 2 and c1 - c0 >= 2})
    return result


def solid_only_outline(grid: list[list[int]]) -> list[list[int]]:
    """Pure diagnostic rival: outline filled components; leave other shapes alone."""
    output = [row[:] for row in grid]
    for component in components(grid):
        if component["solid"]:
            r0, c0, r1, c1 = component["bbox"]
            for r in range(r0 + 1, r1):
                for c in range(c0 + 1, c1):
                    output[r][c] = 0
    return output


def fixtures() -> list[dict[str, Any]]:
    legal = [[1, 1, 1, 0, 2, 2, 2] for _ in range(3)] + [[0] * 7 for _ in range(2)]
    witness = [row[:] for row in legal]
    for r in (1, 2):
        for c in (5, 6):
            witness[r][c] = 0
    l_only = [[0 if value == 1 else value for value in row] for row in witness]
    return [{"name": name, "origin": "hand_authored", "seed": None, "sample_index": None,
             "difficulty": None, "overrides": None, "input": grid}
            for name, grid in (("two_solid_rectangles_control", legal),
                               ("rectangle_plus_L_witness", witness),
                               ("L_only_rejection_control", l_only))]


def save_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run(out: Path) -> dict[str, Any]:
    root = find_root(__file__)
    out.mkdir(parents=True, exist_ok=False)
    report: dict[str, Any] = {
        "schema": "be5e5ba56395-component-audit-v1", "task_id": TASK_ID,
        "status": "running", "created_utc": datetime.now(timezone.utc).isoformat(),
        "command": {"cwd": str(Path.cwd()), "argv": [sys.executable, *sys.argv],
                    "source_root": str(root),
                    "environment": {name: os.environ.get(name) for name in ("RACKET_PATH", "TMPDIR")}},
        "classification": "documented-domain false acceptance by self_check",
        "claims": {"in_domain_wrong_label_reproduced": False,
                   "complete_lesson_ambiguity_reproduced": False,
                   "malformed_witness_was_generated": False},
        "scope": {"hand_authored_cases": 3, "native_generated_draws": 1,
                  "canonical_pairs": 5, "reference_batches": 1,
                  "no_safety_or_audit_status_change": True},
        "failures": [], "cases": [],
    }
    save_json(out/'report.json', report)
    try:
        module, source_path, source_hash = load_selected_generator(TASK_ID, root=root)
        report["generator_source_sha256"] = source_hash
        report["expected_audited_source_sha256"] = AUDITED_SHA256
        source = source_path.read_bytes()
        if source_hash != AUDITED_SHA256 or digest(source) != source_hash:
            raise RuntimeError("Source differs from the exact audited revision; finding must be assessed again")
        source_dir = out/'source'
        source_dir.mkdir()
        (source_dir/'generator.py').write_bytes(source)
        (source_dir/'reproducer.py').write_bytes(Path(__file__).read_bytes())
        report["reproducer_sha256"] = digest(Path(__file__).read_bytes())
        report["source_paths"] = {"generator": str(source_path.relative_to(root)),
                                  "generator_snapshot": "source/generator.py",
                                  "reproducer_snapshot": "source/reproducer.py"}
        catalog = Catalog(root)
        task = catalog.get(TASK_ID)
        if len(task["variants"]) != 1:
            raise RuntimeError("This bounded reproducer expects the audited single canonical variant")
        canonical = task["variants"][0]
        save_json(source_dir/'canonical_task.json', canonical)
        rule = canonical["program_solution"]
        (source_dir/'canonical_rule.rkt').write_text(rule, encoding="utf-8")
        report["canonical_authority"] = {
            "program": rule, "program_text_sha256": digest(rule.encode()),
            "normalized_rule_hash": digest(" ".join(rule.split()).encode())[:12],
            "ledger_sha256": digest(canonical_path(root).read_bytes()),
            "task_row_snapshot": "source/canonical_task.json", "program_snapshot": "source/canonical_rule.rkt",
        }
        report["prior_audit_index"] = {
            "path": f"generators/{TASK_ID}/evidence/review_index.json",
            "sha256": digest((root/f"generators/{TASK_ID}/evidence/review_index.json").read_bytes()),
            "observation": "Same source already has unresolved/needs_triage reports of this validator gap; this is an independent replay.",
        }
        report["cases"] = fixtures()
        generated = module.generate(seed=0, sample_index=0, difficulty=None)
        report["cases"].append({"name": "native_seed_0_sample_0_control", "origin": "native_generator",
                                "seed": 0, "sample_index": 0, "difficulty": None, "overrides": {}, "input": generated})
        for pair in canonical_pairs(TASK_ID, root=root, labeled_only=True):
            report["cases"].append({"name": f"canonical_v{pair['variant']}_{pair['split']}_{pair['pair_index']}",
                                    "origin": "canonical", "seed": None, "sample_index": None,
                                    "difficulty": None, "overrides": None, **pair})
        for case in report["cases"]:
            component_rows = components(case["input"])
            case["components"] = component_rows
            case["all_components_solid_at_least_3_by_3"] = bool(component_rows) and all(c["solid"] and c["at_least_3_by_3"] for c in component_rows)
            case["input_sha256"] = grid_digest(case["input"])
            case["input_dimensions"] = [len(case["input"]), len(case["input"][0])]
        save_json(out/'report.json', report)
        applied = catalog.apply(TASK_ID, [case["input"] for case in report["cases"]],
                                reference="canonical", check_generator_domain=True, timeout=90)
        report["apply_receipt"] = applied
        save_json(out/'racket.json', applied)
        if applied["generator_sha256"] != source_hash or not applied["rule_hash_matches_catalog"]:
            raise RuntimeError("Reference execution identity does not match the saved source/catalog")
        if applied["executed_rule_hash"] != report["canonical_authority"]["normalized_rule_hash"]:
            raise RuntimeError("Executed authority differs from the saved canonical rule")
        for case, result in zip(report["cases"], applied["results"], strict=True):
            if result["error"] or not result["valid_output"]:
                raise RuntimeError(f"Reference execution failed for {case['name']}: {result['error']}")
            output = result["output"]
            rival = solid_only_outline(case["input"])
            case["generator_domain"] = result["generator_domain"]
            case["reference_output"] = output
            case["reference_output_sha256"] = result["output_sha256"]
            case["rival_output"] = rival
            case["rival_output_sha256"] = grid_digest(rival)
            case["rival_differing_cells"] = [[r, c] for r in range(len(output)) for c in range(len(output[0])) if output[r][c] != rival[r][c]]
            case["newly_colored_cells"] = [[r, c] for r in range(len(output)) for c in range(len(output[0])) if case["input"][r][c] == 0 and output[r][c] != 0]
            if case["origin"] == "canonical":
                case["matches_canonical_label"] = output == case["output"]
        by_name = {case["name"]: case for case in report["cases"]}
        legal, witness, l_only = [by_name[name] for name in ("two_solid_rectangles_control", "rectangle_plus_L_witness", "L_only_rejection_control")]
        expected_added = [[1, 6], [2, 5], [2, 6]]
        observations = {
            "legal_control_accepted": legal["generator_domain"]["status"] == "valid" and legal["all_components_solid_at_least_3_by_3"],
            "malformed_witness_accepted": witness["generator_domain"]["status"] == "valid" and not witness["all_components_solid_at_least_3_by_3"],
            "L_only_control_rejected": l_only["generator_domain"]["status"] == "invalid",
            "witness_reference_adds_three_bbox_border_cells": witness["newly_colored_cells"] == expected_added,
            "rival_disagreement_confined_to_three_added_cells": witness["rival_differing_cells"] == expected_added,
            "native_single_draw_accepted_and_solid": by_name["native_seed_0_sample_0_control"]["generator_domain"]["status"] == "valid" and by_name["native_seed_0_sample_0_control"]["all_components_solid_at_least_3_by_3"],
            "all_five_canonical_labels_match": all(case.get("matches_canonical_label", True) for case in report["cases"]),
        }
        report["observations"] = observations
        if not all(observations.values()):
            raise AssertionError({name: value for name, value in observations.items() if not value})
        if digest(source_path.read_bytes()) != source_hash:
            raise RuntimeError("Generator source changed during the probe")
        save_json(out/'minimal_witness.json', {"input": witness["input"], "generator_domain": witness["generator_domain"],
                                              "components": witness["components"], "reference_output": witness["reference_output"],
                                              "rival_output": witness["rival_output"], "newly_colored_cells": expected_added,
                                              "seed": None, "sample_index": None, "origin": "hand_authored"})
        report["status"] = "reproduced"
        report["limitations"] = [
            "The malformed witness is outside the written all-components-solid domain and was not emitted by the sampler.",
            "Only one native draw (seed=0, sample_index=0, default difficulty/overrides) was inspected; this is not a frequency estimate.",
            "All five canonical labels were replayed successfully; no in-domain wrong reference label was reproduced.",
            "The rival agrees on the solid-rectangle domain. Its malformed-input disagreement is not complete-lesson ambiguity.",
            "No target source, tests, rule, approval, or audit status was changed.",
        ]
    except Exception as exc:
        failure = {"type": type(exc).__name__, "error": str(exc)}
        if hasattr(exc, "run"):
            failure["process_receipt"] = exc.run
        report["failures"].append(failure)
        report["status"] = "failed"
    save_json(out/'report.json', report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    report = run(args.out)
    print(json.dumps({"status": report["status"], "observations": report.get("observations"),
                      "failures": report["failures"], "report": str((args.out/'report.json').resolve())}, sort_keys=True))
    return 0 if report["status"] == "reproduced" else 1


if __name__ == "__main__":
    raise SystemExit(main())
