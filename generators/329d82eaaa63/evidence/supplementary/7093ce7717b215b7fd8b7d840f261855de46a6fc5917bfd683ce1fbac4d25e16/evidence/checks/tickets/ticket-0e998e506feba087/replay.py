#!/usr/bin/env python3
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import subprocess
import sys
import time
from pathlib import Path

TICKET_ID = "ticket-0e998e506feba087"
TASK_ID = "329d82eaaa63"
PROBE_SEED_HEX = "119c748e17eb9de7c95a5e4af9be7e710a5cbd72181aae15872d64d167738f44"
EXPECTED = {
    "source_sha256": "607bc195e64e6e24e646bb602def28614aa6db5e0d60cb40c861302aa9f3bc8a",
    "assets_sha256": "ed2d9805a460e9a2bc95107877b4fd3e22fea2d7c509b0d3bf1fbda57dd618b4",
    "index_sha256": "4fba68f69bd22971bf3efd917e6330de7f58eda6e4d95b3919a122e23d33d211",
    "record_sha256": "327ac88f87497f24a537dfe9e5ee30ca6ae9ba09833335871fab6fa4df1bd81d",
    "return_id": "review-565c1a422d0e35f2:v0001",
    "rule_hash": "c3b26f3f0fc8",
    "requested_combinations": 2688,
    "feasible_exact": 1456,
    "structured_incompatible": 1232,
    "rotations_checked": 320,
    "portable_tests": 54,
}

HERE = Path(__file__).resolve()
WORK = HERE.parents[3]
REPO = WORK / "repo"
TASK = REPO / "generators" / TASK_ID
for candidate in (REPO / "shared" / "runtime", REPO / "src", REPO):
    sys.path.insert(0, str(candidate))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_generator():
    source = TASK / "generator.py"
    spec = importlib.util.spec_from_file_location(f"ticket_{TASK_ID}", source)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def main() -> int:
    started = time.monotonic()
    source = TASK / "generator.py"
    assets = TASK / "counterexamples" / "review-565c1a422d0e35f2-v0001" / "audit_assets.json"
    index_path = TASK / "evidence" / "review_index.json"
    retained_probe = assets.parent / "retained" / "checks" / "audit" / TASK_ID / "probe.json"
    retained_tests = assets.parent / "retained" / "checks" / "audit" / TASK_ID / "task-tests" / "result.json"

    index = json.loads(index_path.read_text())
    record = next(row for row in index["audits"] if row["return_id"] == EXPECTED["return_id"])
    record_sha = hashlib.sha256(json.dumps(record, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    identity = {
        "source_sha256": sha(source),
        "assets_sha256": sha(assets),
        "index_sha256": sha(index_path),
        "record_sha256": record_sha,
        "retained_probe_sha256": sha(retained_probe),
        "retained_tests_sha256": sha(retained_tests),
    }
    identity_ok = (
        identity["source_sha256"] == EXPECTED["source_sha256"]
        and identity["assets_sha256"] == EXPECTED["assets_sha256"]
        and identity["index_sha256"] == EXPECTED["index_sha256"]
        and identity["record_sha256"] == EXPECTED["record_sha256"]
    )

    gen = load_generator()
    seed = int(PROBE_SEED_HEX[:16], 16)
    exact_failures: list[dict] = []
    structured_failures: list[dict] = []
    feasible = incompatible = 0
    requested = 0
    for h in range(3, 19):
        for w in range(4, 25):
            for n in range(1, 9):
                requested += 1
                axes = {"grid_h": h, "grid_w": w, "n_seeds": n}
                expected_feasible = n <= gen._max_seeds(w)
                try:
                    grid = gen.generate(seed, requested, **axes)
                except ValueError as exc:
                    tag = set(getattr(exc, "incompatible_axes", ()))
                    if expected_feasible or tag != {"grid_w", "n_seeds"}:
                        structured_failures.append({"axes": axes, "error": str(exc), "tag": sorted(tag)})
                    else:
                        incompatible += 1
                    continue
                if not expected_feasible:
                    exact_failures.append({"axes": axes, "error": "unexpectedly accepted"})
                    continue
                observed = gen.observe_overrides(grid)
                errors = gen.self_check(grid)
                if observed != axes or errors:
                    exact_failures.append({"axes": axes, "observed": observed, "self_check": errors})
                else:
                    feasible += 1

    ambiguous: list[dict] = []
    rotations = 0
    bands = (None, "easy", "medium", "hard")
    for band_index, band in enumerate(bands):
        for seed_offset in range(20):
            case_seed = seed + 1000 * band_index + seed_offset
            grids = [gen.generate(case_seed, i, difficulty=band) for i in range(4)]
            pairs = [{"input": copy.deepcopy(g), "output": gen.rule_mirror(g)} for g in grids]
            for query_index, query in enumerate(pairs):
                demos = [pair for i, pair in enumerate(pairs) if i != query_index]
                hook = gen.lesson_identifiable(demos, query)
                survivors = [
                    name
                    for name, rival in gen.LESSON_COMPETITORS.items()
                    if all(rival(d["input"]) == d["output"] for d in demos)
                    and rival(query["input"]) != query["output"]
                ]
                rotations += 1
                if hook or survivors:
                    ambiguous.append({
                        "band": band,
                        "seed_offset": seed_offset,
                        "query_index": query_index,
                        "hook": hook,
                        "survivors": survivors,
                    })

    test_run = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", str(TASK / "tests" / "test_generator_329d82eaaa63.py")],
        cwd=REPO,
        text=True,
        capture_output=True,
        timeout=60,
        check=False,
    )
    combined_test_output = (test_run.stdout + "\n" + test_run.stderr).strip()
    tests_ok = test_run.returncode == 0 and "54 passed" in combined_test_output

    reproduced = (
        identity_ok
        and gen.RULE_HASH == EXPECTED["rule_hash"]
        and requested == EXPECTED["requested_combinations"]
        and feasible == EXPECTED["feasible_exact"]
        and incompatible == EXPECTED["structured_incompatible"]
        and not exact_failures
        and not structured_failures
        and rotations == EXPECTED["rotations_checked"]
        and not ambiguous
        and tests_ok
    )
    report = {
        "schema": "audit-replay-ticket-v1",
        "ticket_id": TICKET_ID,
        "task_id": TASK_ID,
        "status": "reproduced" if reproduced else "not_reproduced",
        "identity": identity,
        "identity_ok": identity_ok,
        "rule_hash": gen.RULE_HASH,
        "axis_cartesian": {
            "requested_combinations": requested,
            "feasible_exact": feasible,
            "structured_incompatible": incompatible,
            "exact_failures": exact_failures[:20],
            "structured_failures": structured_failures[:20],
        },
        "lesson_rotations": {
            "checked": rotations,
            "ambiguous": ambiguous[:20],
        },
        "portable_tests": {
            "exit_code": test_run.returncode,
            "expected_pass_count": EXPECTED["portable_tests"],
            "matched": tests_ok,
            "tail": combined_test_output[-1000:],
        },
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "limit": "Finite replay of retained declared axes/rivals; does not clear the audit or cover undeclared hypotheses.",
    }
    out = HERE.parent / "report.json"
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "status": report["status"],
        "axis_cartesian": report["axis_cartesian"],
        "lesson_rotations": {"checked": rotations, "ambiguous": len(ambiguous)},
        "portable_tests": report["portable_tests"],
        "elapsed_seconds": report["elapsed_seconds"],
        "out": str(out),
    }, sort_keys=True))
    return 0 if reproduced else 1


if __name__ == "__main__":
    raise SystemExit(main())
