from __future__ import annotations
import hashlib
import json
from pathlib import Path

TASK = "ad4e576b99c4"
TICKET = "ticket-440d5abef304d0cc"
repo = Path.cwd()
manifest_path = repo / "generators" / TASK / "workspace/parametric/evidence/manifest.json"
manifest_bytes = manifest_path.read_bytes()
manifest = json.loads(manifest_bytes)
base = repo / "generators" / TASK / "workspace/parametric/evidence/reviewer-reported/e622a7eb1a6fbedc/parametric/paired-batch-v1/public"
public_results = []
for declared in manifest["owner_public_inspection"]["public_files"]:
    path = base / f"{declared['sha256']}.json"
    raw = path.read_bytes()
    payload = json.loads(raw)
    tests = payload.get("test")
    trains = payload.get("train")
    public_results.append({
        "file": str(path.relative_to(repo)),
        "declared_sha256": declared["sha256"],
        "actual_sha256": hashlib.sha256(raw).hexdigest(),
        "declared_queries": declared["queries"],
        "actual_queries": len(tests) if isinstance(tests, list) else None,
        "test_keys": [sorted(item) for item in tests] if isinstance(tests, list) else None,
        "train_keys": [sorted(item) for item in trains] if isinstance(trains, list) else None,
        "test_outputs_exposed": any("output" in item for item in tests) if isinstance(tests, list) else None,
    })
all_hashes_match = all(x["declared_sha256"] == x["actual_sha256"] for x in public_results)
all_four = all(x["declared_queries"] == x["actual_queries"] == 4 for x in public_results)
all_masked = all(x["test_keys"] == [["input"]] * 4 and not x["test_outputs_exposed"] for x in public_results)
result = {
    "schema": "supplementary_ticket_probe/1",
    "ticket_id": TICKET,
    "task_id": TASK,
    "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
    "generator_sha256": hashlib.sha256((repo / "generators" / TASK / "generator.py").read_bytes()).hexdigest(),
    "public_files": public_results,
    "all_public_hashes_match": all_hashes_match,
    "all_public_files_have_four_queries": all_four,
    "all_test_queries_are_input_only": all_masked,
    "production_parametric_api": manifest.get("production_parametric_api"),
    "variant_approved": manifest.get("variant_approved"),
    "verification_status": manifest.get("verification_status"),
    "owner_public_inspection_status": manifest.get("owner_public_inspection", {}).get("status"),
    "support_boundary_passed": all_hashes_match and all_four and all_masked,
    "approval_boundary_preserved": manifest.get("variant_approved") is False and manifest.get("production_parametric_api") is False,
    "summary": "Three hash-addressed public episodes each contain exactly four input-only test queries; the manifest separately keeps the prototype unapproved and outside the production API.",
}
Path("../checks/tickets/ticket-440d5abef304d0cc/result.json").write_text(
    json.dumps(result, indent=2, sort_keys=True) + "\n"
)
print(json.dumps({
    "support_boundary_passed": result["support_boundary_passed"],
    "approval_boundary_preserved": result["approval_boundary_preserved"],
    "public_episode_count": len(public_results),
    "query_counts": [x["actual_queries"] for x in public_results],
}, sort_keys=True))
