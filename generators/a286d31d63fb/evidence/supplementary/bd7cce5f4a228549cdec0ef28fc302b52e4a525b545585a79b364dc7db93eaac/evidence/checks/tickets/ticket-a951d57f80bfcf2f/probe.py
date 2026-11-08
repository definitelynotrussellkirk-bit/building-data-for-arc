#!/usr/bin/env python3
"""One bounded replay of the pinned a286d31d63fb API/domain audit witness."""
from __future__ import annotations

import hashlib
import json
import signal
import time
import traceback
from pathlib import Path

from reviewer_support import load_selected_generator

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[2]
ROOT = WORK / "repo"
TICKET_ID = "ticket-a951d57f80bfcf2f"
TASK_ID = "a286d31d63fb"
RETURN_ID = "review-5c22ad8e91c4bedd:v0001"
PINNED = {
    "source": {
        "path": "repo/generators/a286d31d63fb/generator.py",
        "sha256": "a831e29015bb5b1fb90332adedd799655969ce0d925970debdd90d5d2eca5ac2",
    },
    "audit_index": {
        "path": "repo/generators/a286d31d63fb/evidence/review_index.json",
        "sha256": "c0c7d1bddb76a8ed74ff81af2478e8def3d627c7dc7d91b87bcba25f1420c51c",
    },
    "assets_manifest": {
        "path": "repo/generators/a286d31d63fb/counterexamples/review-5c22ad8e91c4bedd-v0001/audit_assets.json",
        "sha256": "1756160f5a36d2f03c160a849e59a8f01216bda8fa27c973f173dd11d45c5f66",
    },
    "audit_record_sha256": "32a60d6871520c1bbc80cdbb1f7d2e363ae6f8a77f2407492b32693983fcb977",
    "rule_hash": "bc2002d0a0d4",
}
started = time.monotonic()


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_json_sha(value) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def write(name: str, value) -> None:
    (HERE / name).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def alarm_handler(_signum, _frame):
    raise TimeoutError("single audit replay exceeded 115 seconds")


def shape(grid):
    return [len(grid), len(grid[0])]


def component_summary(module, grid):
    rows = []
    for cells in module._components_4conn(grid):
        profile = module._row_profile(cells)
        rows.append({
            "size": len(cells),
            "row_profile": profile,
            "flat": len(set(profile)) == 1,
            "colors": sorted({grid[r][c] for r, c in cells}),
        })
    return rows


def capture(module, call):
    try:
        grid = module.generate(**call)
    except Exception as exc:
        return {
            "call": call,
            "status": "raised",
            "exception_type": type(exc).__name__,
            "exception": str(exc),
        }
    return {
        "call": call,
        "status": "returned",
        "shape": shape(grid),
        "distinct_nonzero_colors": sorted({v for row in grid for v in row if v}),
        "self_check": module.self_check(grid, difficulty=call.get("difficulty")),
        "components": component_summary(module, grid),
        "grid_sha256": canonical_json_sha(grid),
    }


signal.signal(signal.SIGALRM, alarm_handler)
signal.setitimer(signal.ITIMER_REAL, 115)
report = {
    "schema": "arcpuzzles-single-audit-replay-v1",
    "ticket_id": TICKET_ID,
    "ticket_type": "audit_replay",
    "consumer": "existing_audit_assessment",
    "task_id": TASK_ID,
    "audit_return_id": RETURN_ID,
    "targeted_probe_count": 1,
    "automatic_resolution_change": False,
    "target_modified": False,
}
status = "unknown"
try:
    bindings = []
    for kind in ("source", "audit_index", "assets_manifest"):
        bound = PINNED[kind]
        path = WORK / bound["path"]
        actual = sha(path)
        if actual != bound["sha256"]:
            raise AssertionError(f"{kind} hash {actual} != {bound['sha256']}")
        bindings.append({"kind": kind, "path": bound["path"], "sha256": actual})

    index = json.loads((WORK / PINNED["audit_index"]["path"]).read_text(encoding="utf-8"))
    audit = next(row for row in index["audits"] if row["return_id"] == RETURN_ID)
    audit_record_sha = canonical_json_sha(audit)
    if audit_record_sha != PINNED["audit_record_sha256"]:
        raise AssertionError("audit record hash mismatch")
    if audit["source_sha256"] != PINNED["source"]["sha256"]:
        raise AssertionError("audit record source binding mismatch")

    manifest = json.loads((WORK / PINNED["assets_manifest"]["path"]).read_text(encoding="utf-8"))
    if manifest["audited_generator_sha256"] != PINNED["source"]["sha256"]:
        raise AssertionError("asset manifest source binding mismatch")
    for asset in manifest["files"]:
        path = ROOT / asset["path"]
        actual = sha(path)
        if actual != asset["sha256"] or path.stat().st_size != asset["bytes"]:
            raise AssertionError(f"retained asset mismatch: {asset['path']}")
        bindings.append({
            "kind": "retained_asset",
            "path": "repo/" + asset["path"],
            "sha256": actual,
            "bytes": asset["bytes"],
        })

    module, source_path, source_sha = load_selected_generator(TASK_ID, root=ROOT)
    if source_sha != PINNED["source"]["sha256"]:
        raise AssertionError("loaded source hash mismatch")

    observations = {
        "declared_height_boundary_rejected": capture(module, {
            "seed": 0, "sample_index": 0, "difficulty": "easy", "height": 8,
        }),
        "degenerate_ignores_exact_height": capture(module, {
            "seed": 0, "sample_index": 3, "difficulty": "easy",
            "texture": "all_flat", "height": 10,
        }),
        "palette_size_not_honored": capture(module, {
            "seed": 0, "sample_index": 0, "difficulty": "easy", "palette_size": 2,
        }),
        "three_flat_leaves_only_one_nonflat": capture(module, {
            "seed": 0, "sample_index": 0, "difficulty": "hard",
            "flat_component_count": 3,
        }),
    }
    h = observations["declared_height_boundary_rejected"]
    d = observations["degenerate_ignores_exact_height"]
    p = observations["palette_size_not_honored"]
    f = observations["three_flat_leaves_only_one_nonflat"]
    reproduced = {
        "declared_height_boundary_rejected": (
            h["status"] == "raised"
            and h["exception_type"] == "ValueError"
            and "outside [10, 11]" in h["exception"]
        ),
        "degenerate_ignores_exact_height": (
            d["status"] == "returned"
            and d["shape"][0] != 10
            and any("non-flat" in reason for reason in d["self_check"])
        ),
        "palette_size_not_honored": (
            p["status"] == "returned"
            and len(p["distinct_nonzero_colors"]) != 2
        ),
        "three_flat_leaves_only_one_nonflat": (
            f["status"] == "returned"
            and sum(not row["flat"] for row in f["components"]) == 1
        ),
    }
    all_reproduced = all(reproduced.values())
    report.update({
        "status": "completed" if all_reproduced else "not_reproduced",
        "assessment": "existing_audit_reproduced" if all_reproduced else "existing_audit_not_reproduced",
        "reproduced": all_reproduced,
        "finding_results": reproduced,
        "observations": observations,
        "source": {"path": str(source_path.relative_to(ROOT)), "sha256": source_sha},
        "rule_hash": PINNED["rule_hash"],
        "audit_record_sha256": audit_record_sha,
        "verified_retained_assets": len(manifest["files"]),
        "existing_audit_resolution": audit["resolution"],
        "limitations": [
            "One exact four-call replay of the pinned witness; the large lint and override batteries were not rerun.",
            "This does not establish a Racket-rule defect, clear the existing audit, approve the peer generator, or modify peer source.",
        ],
    })
    write("bindings.json", {
        "audit_record_sha256": audit_record_sha,
        "verified_count": len(bindings),
        "files": bindings,
    })
    status = "completed" if all_reproduced else "unknown"
except Exception as exc:
    report.update({
        "status": "unknown",
        "assessment": "replay_error",
        "reproduced": False,
        "error": f"{type(exc).__name__}: {exc}",
        "traceback": traceback.format_exc(),
    })
finally:
    signal.setitimer(signal.ITIMER_REAL, 0)
    report["probe_elapsed_seconds"] = round(time.monotonic() - started, 6)
    write("replay.json", report)

print(json.dumps({
    "ticket_id": TICKET_ID,
    "status": status,
    "reproduced": report.get("reproduced", False),
    "finding_results": report.get("finding_results"),
    "verified_retained_assets": report.get("verified_retained_assets"),
    "probe_elapsed_seconds": report["probe_elapsed_seconds"],
}, indent=2, sort_keys=True))
raise SystemExit(0 if status == "completed" else 1)
