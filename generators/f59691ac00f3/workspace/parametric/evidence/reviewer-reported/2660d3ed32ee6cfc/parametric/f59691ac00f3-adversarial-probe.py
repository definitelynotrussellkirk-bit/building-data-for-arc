#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import find_root

ROOT = find_root(__file__)
PROTOTYPE = ROOT / "generators/f59691ac00f3/workspace/parametric/prototype.py"
RETAINED = ROOT.parent / "checks/parametric/f59691ac00f3-parent-choice-v1"
OUT = ROOT.parent / "checks/parametric/f59691ac00f3-adversarial.json"

spec = importlib.util.spec_from_file_location("f59691ac_parametric_probe", PROTOTYPE)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

report = {
    "schema": "arcpuzzles-parametric-adversarial-probe-v1",
    "task_id": module.TASK_ID,
    "surfaces": {},
}
with RacketBridge() as bridge:
    sampler_rows = []
    for seed in range(10, 16):
        episode = module.make_episode(
            seed,
            demo_count=1,
            query_count=12,
            root=ROOT,
            bridge=bridge,
        )
        analysis = module.analyze_episode(episode, root=ROOT, bridge=bridge)
        inputs = [json.dumps(row["input"], separators=(",", ":")) for row in episode["pairs"]]
        sampler_rows.append(
            {
                "seed": seed,
                "setting": episode["parameters"]["different_parent"],
                "inputs": len(inputs),
                "unique_inputs": len(set(inputs)),
                "all_four_parent_pairs": all(
                    set(row["parent_pairs"]) == {"22", "25", "52", "55"}
                    for row in episode["pairs"]
                ),
                "rival_fits_one_demo": analysis["rival_fits_demonstrations"],
                "all_queries_distinguish": all(
                    row["rival_query_differs"] for row in analysis["queries"]
                ),
                "status": analysis["status"],
            }
        )
    report["surfaces"]["sampler_count_retry_boundary"] = {
        "status": "pass" if all(
            row["unique_inputs"] == 13
            and row["all_four_parent_pairs"]
            and not row["rival_fits_one_demo"]
            and row["all_queries_distinguish"]
            and row["status"] == "no_ambiguity_found"
            for row in sampler_rows
        ) else "fail",
        "cases": sampler_rows,
        "scope": "six seeds; one demonstration plus twelve queries per seed",
    }

    with tempfile.TemporaryDirectory(prefix="f59691ac-tamper-") as tmp:
        tree = Path(tmp) / "evidence"
        shutil.copytree(RETAINED, tree)
        report_json = json.loads((tree / "report.json").read_text())
        public_rel = report_json["episodes"][0]["public_path"]
        public_path = tree / public_rel
        public = json.loads(public_path.read_text())
        public["test"][0]["output"] = [[9]]
        public_path.write_text(json.dumps(public, indent=2, sort_keys=True) + "\n")
        body = public_path.read_bytes()
        manifest_path = tree / "manifest.json"
        manifest = json.loads(manifest_path.read_text())
        manifest["files"][public_rel] = {
            "bytes": len(body),
            "sha256": hashlib.sha256(body).hexdigest(),
        }
        manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
        verification = module.verify_tree(tree, root=ROOT, bridge=bridge)
        rejected_for_projection = any(
            "public/private projection mismatch" in error
            for error in verification["errors"]
        )
        report["surfaces"]["public_export_verifier_rejection"] = {
            "status": "pass"
            if verification["status"] == "fail" and rejected_for_projection
            else "fail",
            "verification_status": verification["status"],
            "errors": verification["errors"],
            "manifest_rehashed_after_tamper": True,
            "tamper": "insert a query answer into one public challenge",
        }

report["status"] = (
    "pass"
    if all(row["status"] == "pass" for row in report["surfaces"].values())
    else "fail"
)
OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
print(json.dumps(report, indent=2, sort_keys=True))
raise SystemExit(0 if report["status"] == "pass" else 1)
