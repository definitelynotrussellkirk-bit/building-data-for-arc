#!/usr/bin/env python3
"""One bounded source-bound allocation comparison and 3-demo/4-query Racket probe."""
from __future__ import annotations

import hashlib
import json
import signal
import time
import traceback
from collections import Counter
from pathlib import Path

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import load_selected_generator

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[2]
ROOT = WORK / "repo"
TICKET_ID = "ticket-55404ece3cf0388b"
TICKET_SEED = "071fbf7046fed63e096027ecaf7eff66d6304afd0576bffa887d44b4c53ae009"
PRIMARY = "9c69eb63c11a"
EXPECTED_PRIMARY_SHA = "1794fc06ad4bf9a57e0a8387346ad9ffae1610716dc79a0c309a21dbd2781def"
EXPECTED_RULE_HASH = "e0d91c9e70a7"
started = time.monotonic()


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha(path: Path) -> str:
    return sha_bytes(path.read_bytes())


def canonical_bytes(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def write(name: str, value) -> None:
    (HERE / name).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def alarm_handler(_signum, _frame):
    raise TimeoutError("single allocation probe exceeded 115 seconds")


def catalog_rows() -> dict[str, dict]:
    rows = {}
    with (ROOT / "catalog/puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                row = json.loads(line)
                rows[row["id"]] = row
    return rows


def canonical_row(task_id: str) -> dict:
    matches = []
    with (ROOT / "shared/data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                row = json.loads(line)
                if row.get("task_id") == task_id:
                    matches.append(row)
    if len(matches) != 1:
        raise AssertionError(f"expected one canonical row for {task_id}, got {len(matches)}")
    return matches[0]


def components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    out = []
    for r0 in range(h):
        for c0 in range(w):
            if grid[r0][c0] == 0 or (r0, c0) in seen:
                continue
            color = grid[r0][c0]
            stack = [(r0, c0)]
            seen.add((r0, c0))
            cells = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen
                            and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            out.append({"color": color, "cells": cells, "size": len(cells)})
    return out


def keep_selected(grid, selector):
    comps = components(grid)
    selected = selector(comps, len(grid), len(grid[0]))
    out = [[0 for _ in row] for row in grid]
    if selected is not None:
        for r, c in selected["cells"]:
            out[r][c] = selected["color"]
    return out


def median_selector(comps, _h, _w):
    return sorted(comps, key=lambda c: c["size"])[len(comps) // 2]


def second_largest_selector(comps, _h, _w):
    return sorted(comps, key=lambda c: c["size"], reverse=True)[1]


def smallest_selector(comps, _h, _w):
    return min(comps, key=lambda c: c["size"])


def largest_selector(comps, _h, _w):
    return max(comps, key=lambda c: c["size"])


def lowest_color_selector(comps, _h, _w):
    return min(comps, key=lambda c: c["color"])


def highest_color_selector(comps, _h, _w):
    return max(comps, key=lambda c: c["color"])


def middle_color_selector(comps, _h, _w):
    return sorted(comps, key=lambda c: c["color"])[len(comps) // 2]


def first_row_major_selector(comps, _h, _w):
    return min(comps, key=lambda c: min(c["cells"]))


def center_selector(comps, h, w):
    cr, cc = (h - 1) / 2, (w - 1) / 2
    def score(comp):
        r = sum(x for x, _ in comp["cells"]) / comp["size"]
        c = sum(y for _, y in comp["cells"]) / comp["size"]
        return ((r - cr) ** 2 + (c - cc) ** 2, comp["color"])
    return min(comps, key=score)


signal.signal(signal.SIGALRM, alarm_handler)
signal.setitimer(signal.ITIMER_REAL, 115)
report = {
    "schema": "arcpuzzles-allocation-quality-probe-v1",
    "ticket_id": TICKET_ID,
    "ticket_type": "allocation_quality",
    "consumer": "bounded_owner_allocation_experiment_proposal",
    "ticket_seed": TICKET_SEED,
    "targeted_probe_count": 1,
    "production_changes": False,
}
status = "unknown"
try:
    manifest_path = WORK / "PACKET-MANIFEST.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    main_ids = list(manifest["main_draw_policy"]["ids"])
    if manifest["main_draw_policy"]["distribution"] != "uniform":
        raise AssertionError("unexpected main draw policy")
    ranked = sorted(
        (task_id for task_id in main_ids if task_id != PRIMARY),
        key=lambda task_id: hashlib.sha256(f"{TICKET_SEED}:{task_id}".encode()).digest(),
    )
    sampled = [PRIMARY, *ranked[:2]]
    if sampled != ["9c69eb63c11a", "bb75d495c809", "9adaf46a8128"]:
        raise AssertionError(f"seeded sample changed: {sampled}")

    catalog = catalog_rows()
    selected_catalog = [catalog[task_id] for task_id in main_ids]
    mix_weights = Counter(str(row.get("mix_weight")) for row in selected_catalog)
    safety_counts = Counter(row.get("train_safety", "") for row in selected_catalog)
    review_counts = Counter(row.get("review_status", "") or "unreviewed" for row in selected_catalog)
    reason_counts = Counter(
        reason
        for task_id in main_ids
        for reason in manifest["selection"]["reasons"].get(task_id, [])
    )
    selection = {
        "algorithm": "Primary ticket target plus the first two other main-pool IDs ordered by SHA256(ticket_seed + ':' + task_id).",
        "ticket_seed": TICKET_SEED,
        "primary": PRIMARY,
        "sampled_task_ids": sampled,
        "main_pool_size": len(main_ids),
        "main_draw_distribution": manifest["main_draw_policy"]["distribution"],
        "packet_selection_policy": manifest["selection"]["policy"],
        "packet_selection_quotas": manifest["selection"]["quotas"],
        "sample_reasons": {task_id: manifest["selection"]["reasons"].get(task_id, []) for task_id in sampled},
        "reason_counts": dict(sorted(reason_counts.items())),
        "manifest_sha256": sha(manifest_path),
    }
    write("selection.json", selection)

    inspections = []
    for task_id in sampled:
        pin = manifest["generators"][task_id]
        source = ROOT / pin["generator"]
        source_sha = sha(source)
        if source_sha != pin["generator_sha256"]:
            raise AssertionError(f"source drift for {task_id}")
        module, loaded_source, loaded_sha = load_selected_generator(task_id, root=ROOT)
        if loaded_sha != source_sha or loaded_source.resolve() != source.resolve():
            raise AssertionError(f"loader binding mismatch for {task_id}")
        idx_path = ROOT / f"generators/{task_id}/evidence/review_index.json"
        idx = json.loads(idx_path.read_text(encoding="utf-8"))
        current_audits = [a for a in idx.get("audits", []) if a.get("source_sha256") == source_sha]
        unresolved = [a for a in current_audits if a.get("resolution") not in ("resolved", "cleared")]
        row = catalog[task_id]
        tests = sorted(str(p.relative_to(ROOT)) for p in (ROOT / f"generators/{task_id}").glob("tests/test*.py"))
        parametric_manifests = sorted(str(p.relative_to(ROOT)) for p in (ROOT / f"generators/{task_id}/workspace/parametric").glob("**/manifest.json"))
        inspections.append({
            "task_id": task_id,
            "source_path": str(source.relative_to(ROOT)),
            "source_sha256": source_sha,
            "rule_hash": pin["rule_hash"],
            "approved_in_packet": pin["approved"],
            "selection_reasons": manifest["selection"]["reasons"].get(task_id, []),
            "catalog": {
                "mix_weight": row.get("mix_weight"),
                "review_status": row.get("review_status") or "unreviewed",
                "train_safety": row.get("train_safety"),
                "health": row.get("health"),
                "sources": row.get("sources"),
                "version": row.get("version"),
                "summary": row.get("summary"),
            },
            "declared_axes": sorted(getattr(module, "AXES", {}).keys()),
            "has_rule_hash_constant": hasattr(module, "RULE_HASH"),
            "semantic_hooks": {
                name: hasattr(module, name)
                for name in ("lesson_identifiable", "SEMANTIC_WITNESSES", "strict_canonical_like")
            },
            "task_tests": tests,
            "parametric_evidence_manifests": parametric_manifests,
            "current_source_audits": [
                {
                    "return_id": a.get("return_id"),
                    "resolution": a.get("resolution"),
                    "verification_status": a.get("verification_status"),
                    "headline": " ".join((a.get("text") or "").split())[:500],
                }
                for a in current_audits
            ],
            "unresolved_current_source_audit_count": len(unresolved),
            "review_index_sha256": sha(idx_path),
        })
    write("inspection.json", {"sampled": inspections})

    primary = next(row for row in inspections if row["task_id"] == PRIMARY)
    if primary["source_sha256"] != EXPECTED_PRIMARY_SHA or primary["rule_hash"] != EXPECTED_RULE_HASH:
        raise AssertionError("primary ticket identity mismatch")

    module, _, source_sha = load_selected_generator(PRIMARY, root=ROOT)
    episode_seed = int(TICKET_SEED[:16], 16)
    inputs = [module.generate(episode_seed, i, difficulty=None) for i in range(7)]
    input_hashes = [sha_bytes(canonical_bytes(grid)) for grid in inputs]
    self_checks = [module.self_check(grid, difficulty=None) for grid in inputs]
    if any(self_checks):
        raise AssertionError(f"primary self_check failure: {self_checks}")

    canon = canonical_row(PRIMARY)
    rule_source = canon["program_solution"]
    bridge = RacketBridge()
    try:
        bridge.eval_text(f"(define __allocation_rule {wrap_rule(rule_source)})")
        outputs = []
        for grid in inputs:
            bridge.define_grid("__allocation_input", grid)
            outputs.append(bridge.eval_text("(__allocation_rule __allocation_input)"))
    finally:
        bridge.shutdown()

    mirror_outputs = [keep_selected(grid, median_selector) for grid in inputs]
    parity = [got == want for got, want in zip(outputs, mirror_outputs)]
    if not all(parity):
        raise AssertionError(f"Racket/Python median parity failed: {parity}")

    selectors = {
        "keep_second_largest": second_largest_selector,
        "keep_smallest": smallest_selector,
        "keep_largest": largest_selector,
        "keep_lowest_color": lowest_color_selector,
        "keep_highest_color": highest_color_selector,
        "keep_middle_color": middle_color_selector,
        "keep_first_row_major": first_row_major_selector,
        "keep_closest_to_center": center_selector,
    }
    rivals = {}
    for name, selector in selectors.items():
        rival_outputs = [keep_selected(grid, selector) for grid in inputs]
        demo_matches = [rival_outputs[i] == outputs[i] for i in range(3)]
        query_matches = [rival_outputs[i] == outputs[i] for i in range(3, 7)]
        rivals[name] = {
            "demo_matches": demo_matches,
            "fits_all_demonstrations": all(demo_matches),
            "query_matches": query_matches,
            "changes_any_query_answer": not all(query_matches),
        }

    shapes = [[len(grid), len(grid[0])] for grid in inputs]
    component_sizes = [[c["size"] for c in components(grid)] for grid in inputs]
    probe = {
        "task_id": PRIMARY,
        "generator_sha256": source_sha,
        "rule_hash": EXPECTED_RULE_HASH,
        "episode_seed": episode_seed,
        "sample_indices": list(range(7)),
        "demo_count": 3,
        "query_count": 4,
        "distinct_input_count": len(set(input_hashes)),
        "input_sha256": input_hashes,
        "shapes": shapes,
        "component_sizes": component_sizes,
        "self_check": self_checks,
        "racket_python_parity": parity,
        "rivals": rivals,
        "answer_equivalent_current_support_rivals": [
            name for name, row in rivals.items()
            if row["fits_all_demonstrations"] and not row["changes_any_query_answer"]
        ],
        "ambiguous_finite_rivals": [
            name for name, row in rivals.items()
            if row["fits_all_demonstrations"] and row["changes_any_query_answer"]
        ],
        "limitations": [
            "Finite rival inventory only; the source has no lesson_identifiable or semantic-witness hook.",
            "One default-difficulty episode does not verify advertised exact overrides, all seeds, or a five-blob lesson.",
            "The Racket labels validate this episode only; they do not resolve the existing source-bound audit.",
        ],
    }
    write("probe.json", probe)

    context = {
        "packet": {
            "owner_generator_count": manifest["selection"]["owner_generator_count"],
            "included_generator_count": len(main_ids),
            "main_draw_distribution": manifest["main_draw_policy"]["distribution"],
            "priority_affects": "packet inclusion/rotation, not main-draw probability",
            "selection_policy": manifest["selection"]["policy"],
            "selection_quotas": manifest["selection"]["quotas"],
            "selection_reason_counts": dict(sorted(reason_counts.items())),
        },
        "catalog_selected_pool": {
            "mix_weight_counts": dict(sorted(mix_weights.items())),
            "train_safety_counts": dict(sorted(safety_counts.items())),
            "review_status_counts": dict(sorted(review_counts.items())),
        },
        "training_context": {
            "snapshot_time": "2026-10-23 11:10-11:17 UTC, with 12:52 UTC update",
            "arc_puzzles_export": "18,852 accepted episodes from 1,558 generators with draws",
            "reported_sampling": "generator defaults, uniform, four queries, canvas limit 30",
            "reported_materialized_token_share": {
                "ARCpuzzles": "37%", "NVARC": "36%", "ARC-GEN": "16%", "RE-ARC": "11%"
            },
            "output_side_at_least_20": {"ARCpuzzles_export": "7.3%", "public_evaluation": "47%"},
            "freshness_limit": "older frozen r6 measurements; not a measurement of this packet's refreshed sources",
            "external_source_gap": "No ARC-GEN or RE-ARC record was in the three-record seeded peer sample; packet-local current rejection/ambiguity/grammar receipts for those sources were therefore not available for a source-level quality comparison.",
        },
    }
    write("allocation-context.json", context)

    report.update({
        "status": "completed",
        "sampled_task_ids": sampled,
        "selection": selection,
        "inspection_path": "inspection.json",
        "allocation_context_path": "allocation-context.json",
        "probe_path": "probe.json",
        "primary_probe": {
            "distinct_input_count": probe["distinct_input_count"],
            "racket_python_parity": all(parity),
            "ambiguous_finite_rivals": probe["ambiguous_finite_rivals"],
            "answer_equivalent_current_support_rivals": probe["answer_equivalent_current_support_rivals"],
        },
        "proposal": {
            "baseline": "equal 20/20/20 authoring minutes across the three seeded records",
            "alternative": "10/30/20 minutes for 9c69eb63c11a/bb75d495c809/9adaf46a8128",
            "rationale": "Spend only a bounded confirmation on 9c69's already reproduced three-blob/axis defect; prioritize the approved bb75 API-boundary repair; retain substantial time for 9ada's explicit marker-4 lesson ambiguity and ignored-axis repairs.",
            "estimate_label": "authoring-time hypothesis, not measured training quality or global optimum",
            "bounded_test": "For each family, attempt at most four 3-demo/4-query episodes and at most eight generation attempts. Require current source/rule hashes, seven distinct lawful inputs, Racket labels, and demonstration-only rejection of relevant answer-changing rivals. Stop a family immediately on label disagreement/source drift; stop volume expansion if fewer than 3/4 episodes pass or if duplicate/rejection cost exceeds 2 attempts per accepted episode.",
            "success_metric": "accepted identifiable query targets per Racket-labeled grid and per authoring minute, with coverage of advertised axes/roles reported separately",
        },
        "limitations": [
            "No mixture weights, approval states, source files, audit resolutions, or training jobs changed.",
            "Training-context percentages are dated owner reports and cannot establish current-source quality.",
            "The three-record sample is useful for a bounded allocation hypothesis, not a library-wide ranking.",
        ],
    })
    status = "completed"
except Exception as exc:
    report.update({
        "status": "unknown",
        "error": f"{type(exc).__name__}: {exc}",
        "traceback": traceback.format_exc(),
    })
finally:
    signal.setitimer(signal.ITIMER_REAL, 0)
    report["probe_elapsed_seconds"] = round(time.monotonic() - started, 6)
    write("report.json", report)

print(json.dumps({
    "ticket_id": TICKET_ID,
    "status": status,
    "sampled_task_ids": report.get("sampled_task_ids"),
    "primary_probe": report.get("primary_probe"),
    "probe_elapsed_seconds": report["probe_elapsed_seconds"],
}, indent=2, sort_keys=True))
raise SystemExit(0 if status == "completed" else 1)
