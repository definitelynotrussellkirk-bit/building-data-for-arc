#!/usr/bin/env python3
"""Source-bound adversarial probes for the two assigned audit targets."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Callable

from reviewer_support import canonical_pairs, find_root, load_selected_generator


def grid_sha(grid: Any) -> str:
    return hashlib.sha256(
        json.dumps(grid, separators=(",", ":"), sort_keys=True).encode()
    ).hexdigest()


def call_receipt(call: Callable[[], Any]) -> dict[str, Any]:
    try:
        value = call()
    except BaseException as exc:
        return {
            "status": "rejected",
            "error_type": type(exc).__name__,
            "error": str(exc),
        }
    row: dict[str, Any] = {"status": "accepted", "value_type": type(value).__name__}
    if isinstance(value, list) and value and isinstance(value[0], list):
        row.update({
            "height": len(value),
            "width": len(value[0]),
            "grid_sha256": grid_sha(value),
        })
    else:
        row["value"] = value
    return row


def canonical_receipts(generator, task_id: str, root: Path) -> list[dict[str, Any]]:
    rows = []
    for pair in canonical_pairs(task_id, root=root, labeled_only=True):
        errors = list(generator.self_check(pair["input"])) if hasattr(generator, "self_check") else ["missing self_check"]
        row = {
            "variant": pair["variant"],
            "split": pair["split"],
            "pair_index": pair["pair_index"],
            "height": len(pair["input"]),
            "width": len(pair["input"][0]),
            "input_sha256": grid_sha(pair["input"]),
            "self_check_errors": errors,
            "accepted": not errors,
        }
        if hasattr(generator, "rule_mirror"):
            try:
                actual = generator.rule_mirror(pair["input"])
            except BaseException as exc:
                row["mirror"] = {"status": "error", "error_type": type(exc).__name__, "error": str(exc)}
            else:
                row["mirror"] = {
                    "status": "ok",
                    "matches_label": actual == pair["output"],
                    "output_sha256": grid_sha(actual),
                }
        rows.append(row)
    return rows


def probe_95(generator, task_id: str, root: Path) -> dict[str, Any]:
    canonical = canonical_receipts(generator, task_id, root)
    generated = generator.generate(7, 0)
    override_probes = {
        "anchor_corner_true": call_receipt(lambda: generator.generate(7, 0, anchor_corner=True)),
        "anchor_corner_false": call_receipt(lambda: generator.generate(7, 0, anchor_corner=False)),
        "palette_kind_warm": call_receipt(lambda: generator.generate(7, 0, palette_kind="warm")),
        "palette_kind_cool": call_receipt(lambda: generator.generate(7, 0, palette_kind="cool")),
    }
    return {
        "canonical": canonical,
        "canonical_summary": {
            "pairs": len(canonical),
            "accepted": sum(row["accepted"] for row in canonical),
            "rejected": sum(not row["accepted"] for row in canonical),
            "dimensions": sorted({(row["height"], row["width"]) for row in canonical}),
        },
        "default_generated": {
            "height": len(generated),
            "width": len(generated[0]),
            "self_check_errors": generator.self_check(generated),
            "grid_sha256": grid_sha(generated),
        },
        "advertised_axes": sorted(getattr(generator, "AXES", {})),
        "has_observe_overrides": hasattr(generator, "observe_overrides"),
        "override_probes": override_probes,
        "override_equalities": {
            "anchor_corner_true_equals_false": override_probes["anchor_corner_true"].get("grid_sha256") == override_probes["anchor_corner_false"].get("grid_sha256"),
            "palette_warm_equals_cool": override_probes["palette_kind_warm"].get("grid_sha256") == override_probes["palette_kind_cool"].get("grid_sha256"),
        },
    }


def probe_def(generator, task_id: str, root: Path) -> dict[str, Any]:
    canonical = canonical_receipts(generator, task_id, root)
    invalids: list[dict[str, Any]] = []
    for axis, values in (
        ("seed", [True, False, 1.0, 1.75, "1"]),
        ("sample_index", [True, False, 1.0, 1.75, "1", -1]),
    ):
        for value in values:
            if axis == "seed":
                generate = lambda value=value: generator.generate(value, 0, difficulty="easy")
                schedule = lambda value=value: generator.schedule_profile(value, 0, "easy")
            else:
                generate = lambda value=value: generator.generate(991, value, difficulty="easy")
                schedule = lambda value=value: generator.schedule_profile(991, value, "easy")
            invalids.append({
                "axis": axis,
                "value": value,
                "value_type": type(value).__name__,
                "generate": call_receipt(generate),
                "schedule_profile": call_receipt(schedule),
            })
    return {
        "canonical": canonical,
        "canonical_summary": {
            "pairs": len(canonical),
            "accepted": sum(row["accepted"] for row in canonical),
            "mirror_matches": sum(row.get("mirror", {}).get("matches_label") is True for row in canonical),
        },
        "invalid_scalar_probes": invalids,
        "invalid_scalar_summary": {
            "probes": len(invalids),
            "generate_accepted": sum(row["generate"]["status"] == "accepted" for row in invalids),
            "schedule_accepted": sum(row["schedule_profile"]["status"] == "accepted" for row in invalids),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("task_id", choices=("95c6376a953c", "defba1ab4f90"))
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    root = find_root(__file__)
    generator, source, digest = load_selected_generator(args.task_id, root=root)
    body = probe_95(generator, args.task_id, root) if args.task_id == "95c6376a953c" else probe_def(generator, args.task_id, root)
    result = {
        "schema": "arcpuzzles-assigned-audit-probe-v1",
        "task_id": args.task_id,
        "generator_path": str(source),
        "generator_sha256": digest,
        "rule_hash": getattr(generator, "RULE_HASH", None),
        **body,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"task_id": args.task_id, "generator_sha256": digest, "out": str(args.out)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
