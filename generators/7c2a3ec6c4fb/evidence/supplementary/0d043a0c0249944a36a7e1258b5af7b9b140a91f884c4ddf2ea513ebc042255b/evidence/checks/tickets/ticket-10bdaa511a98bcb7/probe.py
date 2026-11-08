#!/usr/bin/env python3
"""One bounded current-source probe for a rarest-palette shortcut."""
from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
import signal
import sys
import time
import traceback

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import canonical_path, find_root, load_selected_generator

TASK_ID = "7c2a3ec6c4fb"
TICKET_ID = "ticket-10bdaa511a98bcb7"
PINNED_SEED = "9d9e417683edc82a349aff33cd16193a6d08b2dab46f0aae30ab0adf76cc85b9"
SOURCE_SHA256 = "8700398dc69b3e155a72ac7624307ec1d312e877cfeab3e7df4bfbfb8482cf57"
RULE_HASH = "38ad2c645d79"
RULE_SHA256 = "640d5deff723c95eb5ee161d578592e7eaac3bf36c965b02a0fc973007837a9b"
DIFFICULTY = "easy"
OVERRIDES = {
    "scene_profile": "square11_c3",
    "n_pairs": 2,
    "pattern_profile": "color_swap",
}
OUT = Path(__file__).resolve().parent


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def literal(value):
    if isinstance(value, list):
        return "(" + " ".join(literal(item) for item in value) + ")"
    if type(value) is not int or not 0 <= value <= 9:
        raise ValueError("not a literal ARC grid")
    return str(value)


def independent_analysis(grid):
    """Segment 8-connected nonzero objects and retain exact bbox crops."""
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    objects = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] == 0 or (row, col) in seen:
                continue
            pending = [(row, col)]
            seen.add((row, col))
            cells = []
            while pending:
                current_row, current_col = pending.pop()
                cells.append((current_row, current_col))
                for delta_row in (-1, 0, 1):
                    for delta_col in (-1, 0, 1):
                        if delta_row == delta_col == 0:
                            continue
                        nxt = (current_row + delta_row, current_col + delta_col)
                        if (
                            0 <= nxt[0] < height
                            and 0 <= nxt[1] < width
                            and grid[nxt[0]][nxt[1]] != 0
                            and nxt not in seen
                        ):
                            seen.add(nxt)
                            pending.append(nxt)
            row0 = min(cell[0] for cell in cells)
            row1 = max(cell[0] for cell in cells)
            col0 = min(cell[1] for cell in cells)
            col1 = max(cell[1] for cell in cells)
            crop = tuple(tuple(grid[r][col0 : col1 + 1]) for r in range(row0, row1 + 1))
            palette = tuple(sorted({grid[r][c] for r, c in cells}))
            objects.append(
                {
                    "bbox": [row0, col0, row1, col1],
                    "cells": set(cells),
                    "crop": crop,
                    "palette": palette,
                }
            )

    crop_counts = Counter(obj["crop"] for obj in objects)
    palette_counts = Counter(obj["palette"] for obj in objects)
    singleton_objects = [obj for obj in objects if crop_counts[obj["crop"]] == 1]
    minimum_palette_frequency = min(palette_counts.values()) if palette_counts else None
    rarest = [
        obj
        for obj in objects
        if palette_counts[obj["palette"]] == minimum_palette_frequency
    ]
    rival_target = rarest[0] if rarest else None

    errors = []
    if height != width or height not in (11, 12, 13):
        errors.append("canvas outside declared square sizes")
    if len(objects) not in (5, 7, 9):
        errors.append("wrong object count")
    if len(singleton_objects) != 1:
        errors.append("wrong exact-crop singleton count")
    expected_multiplicities = [1] + [2] * ((len(objects) - 1) // 2)
    if sorted(crop_counts.values()) != expected_multiplicities:
        errors.append("wrong exact-crop multiplicities")
    for index, obj in enumerate(objects):
        top, left, bottom, right = obj["bbox"]
        if any(
            grid[r][c] and (r, c) not in obj["cells"]
            for r in range(top, bottom + 1)
            for c in range(left, right + 1)
        ):
            errors.append("foreign foreground in object bbox")
        for other in objects[index + 1 :]:
            other_top, other_left, other_bottom, other_right = other["bbox"]
            if not (
                bottom < other_top
                or other_bottom < top
                or right < other_left
                or other_right < left
            ):
                errors.append("overlapping object bboxes")

    answer = [list(row) for row in singleton_objects[0]["crop"]] if len(singleton_objects) == 1 else None
    rival_output = [list(row) for row in rival_target["crop"]] if rival_target else None
    summary = [
        {
            "bbox": obj["bbox"],
            "crop": [list(row) for row in obj["crop"]],
            "palette": list(obj["palette"]),
            "exact_multiplicity": crop_counts[obj["crop"]],
            "palette_multiplicity": palette_counts[obj["palette"]],
        }
        for obj in objects
    ]
    return {
        "errors": errors,
        "objects": summary,
        "output": answer,
        "rival_output": rival_output,
        "minimum_palette_frequency": minimum_palette_frequency,
        "rarest_palette_candidate_count": len(rarest),
    }


def timeout_handler(_signum, _frame):
    raise TimeoutError("single targeted probe exceeded internal 110-second budget")


def run(result):
    root = find_root(__file__)
    module, selected_path, selected_sha = load_selected_generator(TASK_ID, root=root)
    if selected_sha != SOURCE_SHA256 or module.RULE_HASH != RULE_HASH:
        raise RuntimeError("selected peer source/rule identity differs from pinned ticket")

    ledger = canonical_path(root)
    canonical = next(
        json.loads(line)
        for line in ledger.read_text(encoding="utf-8").splitlines()
        if line.strip() and json.loads(line).get("task_id") == TASK_ID
    )
    source = canonical["program_solution"]
    if sha256(source.encode()) != RULE_SHA256:
        raise RuntimeError("canonical raw rule bytes differ from reviewed authority")
    if sha256(" ".join(source.split()).encode())[:12] != RULE_HASH:
        raise RuntimeError("canonical normalized rule hash mismatch")

    review_index_path = selected_path.parent / "evidence" / "review_index.json"
    review_index = json.loads(review_index_path.read_text(encoding="utf-8"))
    if review_index["current_source_sha256"] != SOURCE_SHA256:
        raise RuntimeError("review index does not bind selected source")

    generated = module.generate(
        PINNED_SEED,
        0,
        difficulty=DIFFICULTY,
        **OVERRIDES,
    )
    canonical_pairs = canonical["train"] + canonical["test"]
    all_inputs = [pair["input"] for pair in canonical_pairs] + [generated]
    stripped = source.strip()
    if not stripped.startswith("(rule! ") or not stripped.endswith(")"):
        raise RuntimeError("authority is not expected plain rule lambda")

    with RacketBridge(timeout=30, max_calls_before_restart=16) as bridge:
        runtime = bridge.runtime_identity
        bridge.eval_text(
            "(define ticket-rule " + stripped[len("(rule! ") : -1].strip() + ")"
        )
        reference = bridge.eval_text("(map ticket-rule '" + literal(all_inputs) + ")")
    if not isinstance(reference, list) or len(reference) != len(all_inputs):
        raise RuntimeError("unexpected reference result shape")

    canonical_rival_matches = []
    canonical_label_matches = []
    for pair, actual in zip(canonical_pairs, reference):
        analysis = independent_analysis(pair["input"])
        canonical_label_matches.append(actual == pair["output"])
        canonical_rival_matches.append(analysis["rival_output"] == actual)
    if not all(canonical_label_matches) or not all(canonical_rival_matches):
        raise RuntimeError("rarest-palette rival is not canonical-perfect")

    actual = reference[-1]
    analysis = independent_analysis(generated)
    strict_errors = list(module.strict_canonical_like(generated))
    mirror = module.rule_mirror(generated) if not strict_errors else None
    independent_errors = analysis["errors"]
    safety_findings = []
    if strict_errors or independent_errors:
        safety_findings.append(
            {
                "kind": "validation_failure",
                "strict_errors": strict_errors,
                "independent_errors": independent_errors,
            }
        )
    if not strict_errors and not independent_errors and (
        actual != analysis["output"] or actual != mirror
    ):
        safety_findings.append(
            {
                "kind": "reference_label_mismatch",
                "racket_output": actual,
                "independent_output": analysis["output"],
                "module_mirror": mirror,
            }
        )

    lawful_witness = (
        not safety_findings
        and actual == analysis["output"] == mirror
        and actual != analysis["rival_output"]
    )
    if not lawful_witness:
        raise RuntimeError("the bounded generated case did not refute the rival cleanly")

    result.update(
        {
            "status": "lawful_rival_refuting_witness",
            "provenance": {
                "selected_source": str(selected_path.relative_to(root)),
                "source_sha256": selected_sha,
                "version": module.VERSION,
                "rule_hash": RULE_HASH,
                "canonical_program_sha256": sha256(source.encode()),
                "canonical_ledger": str(ledger.relative_to(root)),
                "review_index": str(review_index_path.relative_to(root)),
                "review_index_sha256": sha256(review_index_path.read_bytes()),
                "racket_runtime": runtime,
            },
            "canonical_shortcut_check": {
                "pair_count": len(canonical_pairs),
                "racket_matches_retained_labels": canonical_label_matches,
                "rarest_palette_rival_matches_racket": canonical_rival_matches,
            },
            "case": {
                "origin": "generated",
                "input": generated,
                "input_sha256": sha256(json.dumps(generated, separators=(",", ":")).encode()),
                "strict_validation_errors": strict_errors,
                "independent_validation_errors": independent_errors,
                "objects": analysis["objects"],
                "minimum_palette_frequency": analysis["minimum_palette_frequency"],
                "rarest_palette_candidate_count": analysis["rarest_palette_candidate_count"],
                "racket_output": actual,
                "independent_exact_crop_output": analysis["output"],
                "module_mirror_output": mirror,
                "rarest_palette_rival_output": analysis["rival_output"],
                "lawful_rival_refuting_witness": lawful_witness,
            },
            "real_safety_findings": safety_findings,
            "interpretation": (
                "The witness refutes the rarest-palette shortcut on the current approved source. "
                "It is evidence of lesson coverage, not a generator defect or approval change."
            ),
        }
    )


def main() -> int:
    started = time.monotonic()
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(110)
    result = {
        "schema": "arcpuzzles-bounded-adversarial-witness-v1",
        "ticket_id": TICKET_ID,
        "ticket_type": "adversarial_witness",
        "consumer": "target_current_audit",
        "task_id": TASK_ID,
        "pinned_seed": PINNED_SEED,
        "sample_index": 0,
        "difficulty": DIFFICULTY,
        "overrides": OVERRIDES,
        "shortcut": (
            "Segment 8-connected objects, count each object's nonzero color palette, "
            "and output the first object whose palette has minimum frequency."
        ),
        "budget": {
            "targeted_probe_runs": 1,
            "generated_cases": 1,
            "max_seconds": 120,
        },
        "command": " ".join(sys.argv),
        "cwd": str(Path.cwd()),
        "probe_sha256": sha256(Path(__file__).read_bytes()),
        "limits": [
            "One generated case only; no frequency estimate or seed census.",
            "Four canonical pairs establish only this rival's canonical plausibility.",
            "No peer files changed; no battery, approval, or training claim.",
        ],
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
        (OUT / "result.json").write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        summary = {
            "ticket_id": TICKET_ID,
            "status": result["status"],
            "elapsed_seconds": result["elapsed_seconds"],
            "lawful_witness": bool(result.get("case", {}).get("lawful_rival_refuting_witness")),
            "real_safety_finding_count": len(result.get("real_safety_findings", [])),
            "execution_error": error,
        }
        line = json.dumps(summary, sort_keys=True) + "\n"
        (OUT / "probe.log").write_text(line, encoding="utf-8")
        print(line, end="")
    return 1 if error else 0


if __name__ == "__main__":
    raise SystemExit(main())
