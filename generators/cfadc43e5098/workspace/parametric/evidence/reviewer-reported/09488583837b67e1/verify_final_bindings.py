"""Check final source/evidence bindings without executing new puzzle labels."""
from pathlib import Path
import hashlib
import json
import sys

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def require(condition, message):
    if not condition:
        raise ValueError(message)

def main():
    work = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent
    root = work / "repo"
    sys.path[:0] = [str(root / "src"), str(root / "shared/runtime")]
    from arcpuzzles.catalog import Catalog
    from arcpuzzles.parametric_priority import _prototype
    task = "cfadc43e5098"
    home = root / "generators" / task / "workspace/parametric"
    manifest = json.loads((home / "evidence/manifest.json").read_text())
    gate = _prototype(root, Catalog(root).describe(task))
    require(gate["status"] == "current", f"Prototype evidence is not current: {gate}")
    require(gate["variant_approved"] is False, "Prototype approval must remain false")
    for item in manifest["files"]:
        path = root / item["path"]
        require(path.stat().st_size == item["bytes"] and digest(path) == item["sha256"], f"Manifest mismatch: {path}")
    receipt = json.loads((home / "evidence/private/export-v1.1.0.json").read_text())
    export = work / "checks/parametric/four-query-export"
    report = json.loads((export / "report.json").read_text())
    require(digest(export / "report.json") == receipt["export_report_sha256"], "Full report mismatch")
    require(digest(export / "manifest.json") == receipt["export_manifest_sha256"], "Export manifest mismatch")
    require(digest(home / "prototype.py") == report["source"]["prototype_sha256"], "Tested prototype changed")
    for item in receipt["source_files"]:
        require(digest(root / item["path"]) == item["sha256"], f"Receipt source mismatch: {item['path']}")
    pairs = queries = 0
    for policy, item in receipt["settings"].items():
        recorded = report["settings"][policy]
        require(item["episode"] == recorded["episode"] and item["analysis"] == recorded["analysis"], f"Copied episode or verdict changed: {policy}")
        ep = item["episode"]
        challenge = {"train": [{"input": v["input"], "output": v["output"]} for v in ep["train"]], "test": [{"input": v["input"]} for v in ep["test"]]}
        raw = (json.dumps(challenge, sort_keys=True, separators=(",", ":")) + "\n").encode()
        public = item["public_export"]
        require(raw == (export / public["public_file"]).read_bytes(), f"Public projection mismatch: {policy}")
        require(hashlib.sha256(raw).hexdigest() == public["public_sha256"], f"Public hash mismatch: {policy}")
        require(digest(root / item["racket_path"]) == ep["racket_sha256"] == item["racket_sha256"], f"Rule mismatch: {policy}")
        require(len(ep["train"]) == 2 and len(ep["test"]) == 4, "Retained example count mismatch")
        require(item["analysis"]["production"]["reference_labels_valid"], "Reference label failure")
        require(all(q["status"] == "no_ambiguity_found" and q["reference_label_valid"] for q in item["analysis"]["queries"]), "Query verdict failure")
        pairs += len(ep["train"]) + len(ep["test"])
        queries += len(ep["test"])
    helper = work / "checks/tooling/private-workspace"
    inventory = json.loads((helper / "DELIVERABLE-INVENTORY.json").read_text())
    for item in inventory["files"]:
        path = helper / item["path"]
        require(path.stat().st_size == item["bytes"] and digest(path) == item["sha256"], f"Helper inventory mismatch: {path}")
    output = {"status": "pass", "scope": "Static bindings and retained actual-run receipts; no additional Racket or integration execution.", "prototype_gate": gate, "manifest_file_count": len(manifest["files"]), "complete_retained_episodes": len(receipt["settings"]), "retained_labeled_pairs": pairs, "retained_queries": queries, "helper_inventory_files": len(inventory["files"]), "source_hashes": {"prototype": digest(home / "prototype.py"), "new_regressions": digest(root / "generators" / task / "tests/test_public_export_revision.py"), "recovery_helper": digest(helper / "packet_tmpfs.py"), "current_manifest": digest(home / "evidence/manifest.json")}}
    print(json.dumps(output, indent=2, sort_keys=True))

if __name__ == "__main__":
    main()
