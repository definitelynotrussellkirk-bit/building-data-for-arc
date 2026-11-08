#!/usr/bin/env python3
"""One source-bound Racket witness for a plausible color-selection shortcut."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import time

TASK = "a452b4b4f04a"
TICKET_ID = "ticket-6f86e10e040c7bbd"
PINNED_SOURCE_SHA = "fc5965005f4cf72f3c35f78c9b8a5822d41bb63782a05b87052186b4f2c42093"
PINNED_RULE_HASH = "f54dbee03c8b"
PROBE_SEED_HEX = "89c681f5b4c35e122c50b36252bab42c3bc5d0327ad29db2d4d1c418801eb29c"


def digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def worker(out: Path) -> int:
    import importlib
    from puzzle_generators import runner
    from scripts.canonical_profile_gate import canonical_pairs, canonical_rule_source, normalized_rule_hash

    gen = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK}.generator")
    source = Path(gen.__file__)
    source_sha = hashlib.sha256(source.read_bytes()).hexdigest()
    program = canonical_rule_source(TASK)
    rule_hash = normalized_rule_hash(program)
    bundle = runner._load_bundle(TASK)
    if bundle.rule_source != program:
        raise AssertionError("runtime Racket authority differs from canonical source")
    bridge, fn_name = runner._open_bridge_with_rule(bundle.rule_callable_text)

    def lowest_color_only(grid):
        """Canonical-fitting rival: complete only the numerically lowest color."""
        output = [list(row) for row in grid]
        groups = {}
        for r, row in enumerate(grid):
            for c, color in enumerate(row):
                if color:
                    groups.setdefault(color, []).append((r, c))
        if not groups:
            return output
        color = min(groups)
        cells = groups[color]
        rows, cols = zip(*cells)
        r0, r1, c0, c1 = min(rows), max(rows), min(cols), max(cols)
        for r in range(r0, r1 + 1):
            output[r][c0] = output[r][c1] = color
        for c in range(c0, c1 + 1):
            output[r0][c] = output[r1][c] = color
        return output

    try:
        canonical = canonical_pairs(TASK)
        canonical_matches = sum(lowest_color_only(pair["input"]) == pair["output"] for pair in canonical)
        seed = int(PROBE_SEED_HEX[:16], 16)
        start = 0
        lesson = runner.run_one(
            TASK,
            seed=seed,
            sample_index=start,
            n_train=gen.EXAMPLES_NEEDED,
            n_test=1,
            bundle=bundle,
            bridge=bridge,
            fn_name=fn_name,
            difficulty="medium",
        )
        demos = lesson["train"]
        demo_records = []
        witness = None
        for index, pair in enumerate(demos):
            grid = pair["input"]
            colors = sorted({v for row in grid for v in row if v})
            rival = lowest_color_only(grid)
            record = {
                "index": index,
                "profile": gen.schedule_profile(seed, start + index, "medium"),
                "colors": colors,
                "validator_issues": gen.self_check(grid),
                "input_sha256": digest(grid),
                "racket_output_sha256": digest(pair["output"]),
                "rival_output_sha256": digest(rival),
                "rival_disagrees": rival != pair["output"],
            }
            demo_records.append(record)
            if witness is None and len(colors) > 1 and rival != pair["output"]:
                witness = {
                    **record,
                    "input": grid,
                    "actual_racket_output": pair["output"],
                    "rival_output": rival,
                }
        hook_errors = gen.lesson_identifiable(demos, {"input": lesson["test"][0]["input"]})
        passed = (
            source_sha == PINNED_SOURCE_SHA
            and rule_hash == PINNED_RULE_HASH
            and canonical_matches == len(canonical)
            and len(demos) == gen.EXAMPLES_NEEDED == 3
            and all(not rec["validator_issues"] for rec in demo_records)
            and witness is not None
            and not hook_errors
        )
        report = {
            "schema": "bounded-adversarial-witness-v1",
            "ticket_id": TICKET_ID,
            "task_id": TASK,
            "passed": passed,
            "generator_sha256": source_sha,
            "rule_hash": rule_hash,
            "label_authority": "selected canonical Racket via puzzle_generators.runner",
            "shortcut": {
                "name": "lowest_color_only",
                "definition": "Preserve all markers, but complete a rectangle only for the numerically lowest nonzero color.",
                "plausibility": "It agrees with every single-color canonical example and ignores object-wise iteration on multicolor scenes.",
                "canonical_matches": canonical_matches,
                "canonical_pair_count": len(canonical),
            },
            "lesson": {
                "seed": seed,
                "sample_index": start,
                "difficulty": "medium",
                "demonstrations": demo_records,
                "query_input_sha256": digest(lesson["test"][0]["input"]),
                "existing_lesson_hook_errors": hook_errors,
            },
            "lawful_witness": witness,
            "classification": "bounded_no_new_safety_finding",
            "disposition": (
                "The shortcut fits all canonical examples but is refuted by an emitted, validator-accepted multicolor demonstration "
                "inside this default three-demonstration window; no peer source change is proposed."
            ),
            "scope_limit": "One pinned default lesson and one rival were inspected; this is not a complete shortcut census or model-behavior claim.",
        }
        out.write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps({"passed": passed, "canonical_matches": canonical_matches, "witness_demo": None if witness is None else witness["index"]}))
        return 0 if passed else 1
    finally:
        bridge.close()


def main() -> int:
    if "--worker" in sys.argv:
        out = Path(sys.argv[sys.argv.index("--out") + 1])
        return worker(out)

    root = Path.cwd()
    sys.path.insert(0, str(root / "src"))
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime, run_process

    out = Path(__file__).with_name("report.json").resolve()
    started = time.monotonic()
    with tempfile.TemporaryDirectory(prefix="bounded-a452-witness-") as tmp:
        runtime = Path(tmp)
        prepare_runtime(Catalog(root), runtime, TASK)
        worker_script = runtime / "ticket_probe.py"
        shutil.copy2(__file__, worker_script)
        command = [sys.executable, "-B", worker_script.name, "--worker", "--out", "report.json"]
        run = run_process(command, runtime, timeout=90, on_output=lambda s: print(s, end="", flush=True))
        if not (runtime / "report.json").exists():
            failure = {
                "schema": "bounded-adversarial-witness-v1",
                "ticket_id": TICKET_ID,
                "task_id": TASK,
                "passed": False,
                "worker": run,
                "elapsed_seconds": round(time.monotonic() - started, 3),
            }
            out.write_text(json.dumps(failure, indent=2) + "\n")
            return 1
        report = json.loads((runtime / "report.json").read_text())
        report["worker_command"] = command
        report["worker_exit_code"] = run["exit_code"]
        report["worker_timed_out"] = run["timed_out"]
        report["elapsed_seconds"] = round(time.monotonic() - started, 3)
        report["passed"] = bool(report.get("passed")) and run["exit_code"] == 0 and not run["timed_out"]
        out.write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps({"passed": report["passed"], "seconds": report["elapsed_seconds"]}))
        return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
