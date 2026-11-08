"""Single bounded, source-bound policy replay of retained profile-floor evidence.

Synthetic grids reproduce the retained profile counts only. They are not claimed
to be lawful instances or the historical generator's actual sampled outputs.
"""
from __future__ import annotations

import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import time
import types

STARTED = time.monotonic()
OUT = Path(__file__).resolve().parent
REPO = Path.cwd()
TASK = "1c1ef857c9e2"
REQUEST = "review-a0f464a466dfe576:v0001:F1"
SEED = "f4283291fed7aab0633f7f403f602b7b8f4af0b3450ce1b4684ba19ace62e1b9"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


expected = {
    "REVIEW/suggestions.json": "2cf732622eeeca12a0b3d2618fd72be588896badeb17ad67a61226d101f1b646",
    "shared/tools/proposals/1ff551e580891a12/manifest.json": "c35009b5a6e9eb4707680a45db6958b5d7a09c5b65c70e2dc41662d9b9583386",
    f"generators/{TASK}/generator.py": "df45898722e7ee3c7a7460303cf734706ad36441e3ae10f8c6f5c80593b8ed9e",
}
bindings = {}
for path, sha in expected.items():
    actual = digest(REPO / path)
    assert actual == sha, (path, actual, sha)
    bindings[path] = actual
request = next(row for row in json.loads((REPO / "REVIEW/suggestions.json").read_text())["items"]
               if row["request_id"] == REQUEST)
request_sha = hashlib.sha256(json.dumps(request, sort_keys=True, ensure_ascii=False,
                                      separators=(",", ":")).encode()).hexdigest()
assert request_sha == "3490077a9b73d1e19b6feadd0e36b2eb09bb2b4fd6a62ea6604ec78747d15f57"
(OUT / "request.json").write_text(json.dumps(request, indent=2) + "\n")
manifest = json.loads((REPO / "shared/tools/proposals/1ff551e580891a12/manifest.json").read_text())
for entry in manifest["files"]:
    path = REPO / entry["path"]
    assert path.stat().st_size == entry["bytes"]
    assert digest(path) == entry["sha256"]
    bindings[entry["path"]] = entry["sha256"]
asset_root = REPO / "shared/tools/proposals/1ff551e580891a12/checks/before/checks"
retained = json.loads((asset_root / f"{TASK}_before_profile_floor.json").read_text())["audits"][0]
dist_log = (asset_root / f"{TASK}_before_dist_gate.log").read_text()
assert retained["exact_hits"] == 0 and retained["draws_total"] == 60

# Import unchanged tool source under the legacy package name it expects. No
# source files or runtime trees are copied or altered.
scripts = types.ModuleType("scripts")
scripts.__path__ = [str(REPO / "shared/tools")]
sys.modules["scripts"] = scripts
gate_path = REPO / "shared/tools/canonical_profile_gate.py"
spec = importlib.util.spec_from_file_location("scripts.canonical_profile_gate", gate_path)
gate = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = gate
spec.loader.exec_module(gate)
assert gate.canonical_rule_hash(TASK) == "13aa128bacd8"
actual_profiles = sorted({gate._profile(grid) for grid in gate.canonical_inputs(TASK)})
assert [list(x) for x in actual_profiles] == retained["canonical_profiles"]

generator = types.ModuleType(f"puzzle_generators.per_puzzle.{TASK}.generator")
generator.self_check = lambda grid: []
sys.modules[generator.__name__] = generator
cases = []
logs = []
for opt_out in (None, "Synthetic replay of retained zero-support profile counts for this ticket"):
    counts = {band: 0 for band in gate.BANDS}

    def generate(seed, sample_index, difficulty):
        index = counts[difficulty]
        counts[difficulty] += 1
        # Match the historical exact=0, envelope=(0,14,20) evidence precisely.
        n = 12 if index < retained["per_band"][difficulty]["envelope"] else 10
        grid = [[0] * n for _ in range(n)]
        grid[0][0] = 1 + int(SEED[:2], 16) % 9
        return grid

    generator.generate = generate
    generator.CANONICAL_PROFILE_OPT_OUT = opt_out
    case_name = "without_opt_out" if opt_out is None else "with_opt_out"
    output = OUT / (case_name + ".json")
    sys.argv = [str(gate_path), TASK, "--strict", "--require-pass", "--min-band-support", "1",
                "--json-out", str(output)]
    stream = io.StringIO()
    with contextlib.redirect_stdout(stream):
        returncode = gate.main()
    audit = json.loads(output.read_text())["audits"][0]
    for band in gate.BANDS:
        for key in ("draws", "crashes", "exact", "envelope", "envelope_only"):
            assert audit["per_band"][band][key] == retained["per_band"][band][key]
    assert returncode == 1
    assert audit["status"] == ("FAIL" if opt_out is None else "WARN")
    cases.append({"case": case_name, "returncode": returncode, "status": audit["status"],
                  "synthetic_generator_calls": sum(counts.values()), "evidence": output.name})
    logs.append("CASE " + case_name + "\n" + stream.getvalue())

for path in ("shared/tools/canonical_profile_gate.py", "shared/tools/run_generator_battery.sh",
             "shared/tools/coder_synth_verify.py", "shared/data/canonical/puzzles.jsonl"):
    bindings[path] = digest(REPO / path)
battery = (REPO / "shared/tools/run_generator_battery.sh").read_text().splitlines()
report = {
    "ticket_id": "ticket-6cdff93f5084f4cb", "request_id": REQUEST,
    "request_sha256": request_sha, "task_id": TASK, "rule_hash": "13aa128bacd8",
    "seed": SEED, "bindings": bindings, "retained_profile_evidence": retained,
    "retained_distribution_log": dist_log,
    "current_battery_profile_policy": [f"{i+1}: {battery[i]}" for i in range(754, 764)],
    "probe_scope": "One targeted synthetic policy replay using the unchanged current gate and real canonical inputs; paired no-opt-out/opt-out cases reproduce retained profile counts. Historical generator sampling, reference execution, and aggregate battery execution were not rerun.",
    "cases": cases, "probe_elapsed_seconds": time.monotonic() - STARTED,
    "proposed_request_disposition": "deferred",
    "proposed_reason": "Partially implemented: non-before battery phases already require strict PASS and min_band_support=1 over the default 20 pinned draws per band. Retained 0/60 evidence is still relevant to the policy. The explicit opt-out remains blocking under --require-pass (WARN exit 1), and its rationale is not embedded in the aggregate summary. Keep the request open for a maintainer decision on intended opt-out semantics and summary exposure; do not repeat the already implemented floor change.",
    "safety_finding": False,
    "limitations": ["Synthetic profile replay is not a safety audit of the current generator.",
                    "The retained historical generator source and sampled grids are not among the two retained assets.",
                    "The gate uses its native task/band/index pinned seeds. The ticket seed selects only the synthetic palette value.",
                    "Aggregate-summary omission is a static source observation, not a full battery run."]
}
(OUT / "probe.log").write_text("\n".join(logs))
(OUT / "probe_result.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps({"cases": cases, "proposed_request_disposition": report["proposed_request_disposition"],
                  "probe_elapsed_seconds": report["probe_elapsed_seconds"]}, indent=2))
