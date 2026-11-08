"""One bounded replay of retained orientation-probe assets, not a peer battery."""
from pathlib import Path
import hashlib
import importlib.util
import json
import time

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import strip_line_comments, strip_rule_wrapper
from reviewer_support import canonical_pairs, find_root, load_selected_generator


START = time.monotonic()
ROOT = find_root(__file__)
OUT = Path(__file__).resolve().parent
REQUEST = "review-6210ca385d85e852:v0001:F4"
PROPOSAL = ROOT / "shared/tools/proposals/103e08df07ea2ff5"
PROBE = PROPOSAL / "checks/audit/9b5ca41b4450/orientation_probe.py"
sha = lambda raw: hashlib.sha256(raw).hexdigest()
manifest = json.loads((PROPOSAL / "manifest.json").read_bytes())
assert sha((PROPOSAL / "manifest.json").read_bytes()) == "560c1d66dfdea6e459e9b07c364016e22c1f8e5da51f61ddf6b1b8dd057130db"
asset_results = []
for row in manifest["files"]:
    raw = (ROOT / row["path"]).read_bytes()
    assert len(raw) == row["bytes"] and sha(raw) == row["sha256"]
    asset_results.append({"path": row["path"], "sha256": sha(raw), "status": "matched"})
requests = json.loads((ROOT / "REVIEW/suggestions.json").read_bytes())["items"]
request = next(row for row in requests if row["request_id"] == REQUEST)
request_sha = sha(json.dumps(request, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode())
assert request_sha == "43af19c0bd3fa0828be1bfc7cbd7e73555f6b2e99936e727da4e7e744cc21800"
spec = importlib.util.spec_from_file_location("retained_orientation_probe", PROBE)
retained = importlib.util.module_from_spec(spec)
spec.loader.exec_module(retained)
generator, source_path, source_sha = load_selected_generator(retained.TASK_ID, root=ROOT)
historical = json.loads(PROBE.with_name("orientation-probe.json").read_bytes())
assert historical["generator_sha256"] == source_sha
counterexample = historical["counterexample"]
assert generator.self_check(counterexample) == []

# Reuse retained functions, but bound new sampling to twelve draws instead of
# rerunning its hard-coded 600-draw historical distribution census.
seed_hex = "586f4d5fa49b4934a3ef7048cbe74596d746c569392fff987e3384f6ceb85906"
seed = int(seed_hex, 16) % (2**63)
counts = {name: 0 for name in ("nw_se", "ne_sw", "same_column", "other")}
for band in ("easy", "medium", "hard"):
    for index in range(4):
        counts[retained.orientation(generator.generate(seed, index, difficulty=band))] += 1
pairs = canonical_pairs(retained.TASK_ID, root=ROOT, labeled_only=True)
canonical_fit = [retained.shortcut(pair["input"]) == pair["output"] for pair in pairs]
programs = {row["program_solution"]
            for line in (ROOT / "shared/data/canonical/puzzles.jsonl").read_text().splitlines()
            if (row := json.loads(line)).get("task_id") == retained.TASK_ID}
assert len(programs) == 1
program = programs.pop()
body = strip_rule_wrapper(strip_line_comments(program))
literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in counterexample) + ")"
with RacketBridge(timeout=10) as bridge:
    reference = bridge.eval_text(f"(let ([g {literal}]) {body})")
shortcut = retained.shortcut(counterexample)
assert reference != shortcut
assert all(canonical_fit)
report = {
    "ticket_id": "ticket-af51425572c5a439", "type": "tool_reproduction",
    "status": "completed", "request_id": REQUEST, "request_sha256": request_sha,
    "asset_manifest_sha256": sha((PROPOSAL / "manifest.json").read_bytes()),
    "verified_asset_count": len(asset_results), "assets": asset_results,
    "asset_consumer_task": retained.TASK_ID,
    "generator_source": str(source_path.relative_to(ROOT)), "generator_sha256": source_sha,
    "canonical_program_sha256": sha(program.encode()), "probe_seed": seed_hex,
    "bounded_draws": 12, "orientation_counts": counts,
    "canonical_pairs": len(pairs), "shortcut_fits_canonical": canonical_fit,
    "counterexample": counterexample, "counterexample_self_check": [],
    "reference_output": reference, "shortcut_output": shortcut,
    "counterexample_disagrees": True, "elapsed_seconds": round(time.monotonic() - START, 6),
    "proposed_disposition": "Retain as a source-bound task-specific proposal; bounded replay reproduced the witness.",
    "generalization_requirements": [
        "Parameterize target, seed and sample count; the retained main hard-codes all three.",
        "Derive the reported finding from measured results instead of its unconditional finding string.",
        "Do not promote this orientation-specific rival as a universal ARC rule.",
    ],
    "limits": "Twelve fresh draws and one Racket witness; the inherited 600-draw census was not rerun. No shared-tool integration or new safety approval.",
}
(OUT / "report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
print(json.dumps({key: report[key] for key in ("status", "verified_asset_count", "bounded_draws", "orientation_counts", "canonical_pairs", "counterexample_disagrees", "elapsed_seconds")}, sort_keys=True))
