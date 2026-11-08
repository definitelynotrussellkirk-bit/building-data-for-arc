#!/usr/bin/env python3
"""One bounded source-bound color-signature witness probe; no peer edits.

Run once through the packet's Racket wrapper. The two target cases are one
generated scene and its lawful half-turn, not a seed census or retry search.
"""
from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
import signal
import sys
import time
import traceback

from reviewer_support import canonical_path, find_root, load_selected_generator
from arc_repl.racket_bridge import RacketBridge


TASK_ID = "7c2a3ec6c4fb"
TICKET_ID = "ticket-7487737a40559cfa"
PINNED_SEED = "9189834f8368f9177b14380a8ea1b519d649493361172de065a17f794307dd18"
SOURCE_SHA256 = "8700398dc69b3e155a72ac7624307ec1d312e877cfeab3e7df4bfbfb8482cf57"
RULE_HASH = "38ad2c645d79"
RULE_SHA256 = "640d5deff723c95eb5ee161d578592e7eaac3bf36c965b02a0fc973007837a9b"
OVERRIDES = {"scene_profile": "square11_c3", "n_pairs": 2,
             "pattern_profile": "color_swap"}
OUT = Path(__file__).resolve().parent


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def literal(value):
    if isinstance(value, list):
        return "(" + " ".join(literal(item) for item in value) + ")"
    if type(value) is not int or not 0 <= value <= 9:
        raise ValueError("not a literal ARC grid")
    return str(value)


def independent_analysis(grid):
    """Flood-fill foreground without generator helpers; retain bbox zeros."""
    h, w = len(grid), len(grid[0])
    seen, objects = set(), []
    for r in range(h):
        for c in range(w):
            if not grid[r][c] or (r, c) in seen:
                continue
            pending, cells = [(r, c)], []
            seen.add((r, c))
            while pending:
                rr, cc = pending.pop()
                cells.append((rr, cc))
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        nr, nc = rr + dr, cc + dc
                        if (0 <= nr < h and 0 <= nc < w and grid[nr][nc]
                                and (nr, nc) not in seen):
                            seen.add((nr, nc))
                            pending.append((nr, nc))
            r0, r1 = min(x[0] for x in cells), max(x[0] for x in cells)
            c0, c1 = min(x[1] for x in cells), max(x[1] for x in cells)
            crop = tuple(tuple(row[c0:c1 + 1]) for row in grid[r0:r1 + 1])
            objects.append({"bbox": [r0, c0, r1, c1], "crop": crop,
                            "colors": tuple(sorted({grid[x][y] for x, y in cells})),
                            "cells": set(cells)})
    counts = Counter(obj["crop"] for obj in objects)
    singles = [obj for obj in objects if counts[obj["crop"]] == 1]
    signatures = Counter(obj["colors"] for obj in objects)
    unique_palette = [obj for obj in objects if signatures[obj["colors"]] == 1]
    rival_target = unique_palette[0] if len(unique_palette) == 1 else objects[0]
    errors = []
    if h != w or h not in (11, 12, 13):
        errors.append("canvas outside declared square sizes")
    if len(objects) not in (5, 7, 9) or len(singles) != 1:
        errors.append("wrong object/singleton count")
    if sorted(counts.values()) != [1] + [2] * ((len(objects) - 1) // 2):
        errors.append("wrong exact-crop multiplicities")
    for i, obj in enumerate(objects):
        a, b, c, d = obj["bbox"]
        if any(grid[r][s] and (r, s) not in obj["cells"]
               for r in range(a, c + 1) for s in range(b, d + 1)):
            errors.append("foreign foreground in object bbox")
        for other in objects[i + 1:]:
            e, f, g, k = other["bbox"]
            if not (c < e or g < a or d < f or k < b):
                errors.append("overlapping object bboxes")
    answer = [list(row) for row in singles[0]["crop"]] if len(singles) == 1 else None
    summary = [{"bbox": obj["bbox"], "crop": obj["crop"],
                "palette": obj["colors"], "exact_multiplicity": counts[obj["crop"]],
                "palette_multiplicity": signatures[obj["colors"]]}
               for obj in objects]
    return {"errors": errors, "output": answer,
            "rival_output": [list(row) for row in rival_target["crop"]],
            "objects": summary, "unique_palette_candidates": len(unique_palette)}


def timeout_handler(signum, frame):
    raise TimeoutError("single targeted probe exceeded internal110second budget")


def run(result):
    root = find_root(__file__)
    module, selected_path, selected_sha = load_selected_generator(TASK_ID, root=root)
    if selected_sha != SOURCE_SHA256 or module.RULE_HASH != RULE_HASH:
        raise RuntimeError("selected peer source/rule identity differs from pinned ticket")
    ledger = canonical_path(root)
    canonical = next(json.loads(line) for line in ledger.read_text().splitlines()
                     if line.strip() and json.loads(line).get("task_id") == TASK_ID)
    source = canonical["program_solution"]
    if sha256(source.encode()) != RULE_SHA256:
        raise RuntimeError("canonical raw rule bytes differ from reviewed authority")
    if sha256(" ".join(source.split()).encode())[:12] != RULE_HASH:
        raise RuntimeError("canonical normalized rule hash mismatch")
    index_path = selected_path.parent / "evidence" / "review_index.json"
    index = json.loads(index_path.read_text())
    if index["current_source_sha256"] != SOURCE_SHA256:
        raise RuntimeError("review_index does not bind selected source")
    result["provenance"] = {
        "root": str(root), "selected_source": str(selected_path.relative_to(root)),
        "source_sha256": selected_sha, "version": module.VERSION,
        "rule_hash": RULE_HASH, "canonical_program_sha256": sha256(source.encode()),
        "canonical_ledger": str(ledger.relative_to(root)),
        "review_index": str(index_path.relative_to(root)),
        "review_index_sha256": sha256(index_path.read_bytes()),
        "review_index_audits": index.get("audits"),
        "review_index_decisions": index.get("decisions"),
    }
    generated = module.generate(PINNED_SEED, 0, difficulty="easy", **OVERRIDES)
    rotated = [list(reversed(row)) for row in reversed(generated)]
    targets = [("generated", generated), ("half_turn_of_generated", rotated)]
    canonical_pairs = canonical["train"] + canonical["test"]
    all_inputs = [pair["input"] for pair in canonical_pairs] + [g for _, g in targets]
    stripped = source.strip()
    if not stripped.startswith("(rule! ") or not stripped.endswith(")"):
        raise RuntimeError("authority is not expected plain rule lambda")
    with RacketBridge() as bridge:
        bridge.eval_text("(define ticket-rule " + stripped[len("(rule! "):-1].strip() + ")")
        reference = bridge.eval_text("(map ticket-rule '" + literal(all_inputs) + ")")
    if not isinstance(reference, list) or len(reference) != len(all_inputs):
        raise RuntimeError("unexpected reference result shape")
    result["canonical_shortcut_check"] = {
        "pair_count": len(canonical_pairs),
        "racket_matches_retained_labels": [actual == pair["output"]
                                           for actual, pair in zip(reference, canonical_pairs)],
        "color_signature_rival_matches_racket": [
            independent_analysis(pair["input"])["rival_output"] == actual
            for pair, actual in zip(canonical_pairs, reference)],
    }
    findings, cases = [], []
    for (origin, grid), actual in zip(targets, reference[len(canonical_pairs):]):
        analysis = independent_analysis(grid)
        validation = module.strict_canonical_like(grid)
        mirror = module.rule_mirror(grid) if not validation else None
        errors = list(analysis["errors"]) + list(validation)
        mismatch = not errors and (actual != analysis["output"] or actual != mirror)
        if errors or mismatch:
            findings.append({"origin": origin, "validation_errors": errors,
                             "reference_label_mismatch": mismatch})
        cases.append({
            "origin": origin, "input": grid,
            "input_sha256": sha256(json.dumps(grid, separators=(",", ":")).encode()),
            "strict_validation_errors": list(validation),
            "independent_validation_errors": analysis["errors"],
            "objects": analysis["objects"], "racket_output": actual,
            "independent_exact_crop_output": analysis["output"],
            "module_mirror_output": mirror,
            "unique_palette_candidates": analysis["unique_palette_candidates"],
            "color_signature_rival_output": analysis["rival_output"],
            "lawful_rival_refuting_witness": not errors and not mismatch
                and actual != analysis["rival_output"],
        })
    result["cases"] = cases
    result["real_safety_findings"] = findings
    result["status"] = ("safety_finding" if findings else "lawful_rival_refuting_witness"
                        if any(case["lawful_rival_refuting_witness"] for case in cases)
                        else "bounded_unknown")
    result["interpretation"] = (
        "A lawful disagreement only refutes the specified color-signature rival; "
        "it is not a generator defect or approval change. Safety findings, if any, "
        "are listed separately with the actual validation/reference mismatch."
    )


def main():
    started = time.monotonic()
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(110)
    result = {
        "schema": "arcpuzzles-bounded-adversarial-witness-v1",
        "ticket_id": TICKET_ID, "ticket_type": "adversarial_witness",
        "consumer": "target_current_audit", "task_id": TASK_ID,
        "pinned_seed": PINNED_SEED, "sample_index": 0,
        "difficulty": "easy", "overrides": OVERRIDES,
        "shortcut": "8-connected objects; output unique palette crop, else first object",
        "budget": {"targeted_probe_runs": 1, "generated_cases": 1,
                   "deliberate_half_turns": 1, "max_seconds": 120},
        "command": " ".join(sys.argv), "cwd": str(Path.cwd()),
        "probe_sha256": sha256(Path(__file__).read_bytes()),
        "limits": ["One generated scene and one half-turn; no frequency estimate.",
                   "Four retained canonical pairs only establish this rival's plausibility.",
                   "No peer files changed; no battery/census/approval or training claim."],
    }
    error = None
    try:
        run(result)
    except Exception:
        error = traceback.format_exc()
        result.update({"status": "bounded_unknown", "execution_error": error})
    finally:
        signal.alarm(0)
        result["elapsed_seconds"] = round(time.monotonic() - started, 3)
        (OUT / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        summary = {"ticket_id": TICKET_ID, "status": result["status"],
                   "elapsed_seconds": result["elapsed_seconds"],
                   "lawful_witness_count": sum(c["lawful_rival_refuting_witness"]
                                               for c in result.get("cases", [])),
                   "real_safety_finding_count": len(result.get("real_safety_findings", [])),
                   "execution_error": error}
        line = json.dumps(summary, sort_keys=True) + "\n"
        (OUT / "probe.log").write_text(line)
        print(line, end="")
    return 1 if error else 0


if __name__ == "__main__":
    raise SystemExit(main())
