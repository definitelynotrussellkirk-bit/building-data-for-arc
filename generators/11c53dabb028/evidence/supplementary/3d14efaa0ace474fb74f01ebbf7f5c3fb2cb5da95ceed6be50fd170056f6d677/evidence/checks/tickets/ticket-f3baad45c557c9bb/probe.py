"""One source-bound, Racket-backed witness against the nonzero-mode shortcut.
Run: PYTHONPATH=WORK/repo/shared/runtime RACKET_PATH=/path/to/racket \
     TMPDIR=WORK/checks/tickets/ticket-f3baad45c557c9bb/tmp \
     timeout 120s python3 -B WORK/checks/tickets/ticket-f3baad45c557c9bb/probe.py
No census, lesson rotation, or generator edits are performed.
"""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import time

TICKET = "ticket-f3baad45c557c9bb"
TASK = "11c53dabb028"
EXPECTED_SOURCE = "32cf2d21a7096a0f76115322813333a55e1ac27b1bba22567719db7ebfe02ac8"
EXPECTED_RULE = "573d7b5ea64c"
TICKET_SEED = "2ab5f6a8f444959a7c8b0cbf6fd480b6fa6158a0e5e9b6ec989fccff13a30694"
OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2] / "repo"
GENERATOR = ROOT / "generators" / TASK / "generator.py"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    start = time.monotonic()
    report = {
        "ticket_id": TICKET, "type": "adversarial_witness", "task_id": TASK,
        "ticket_seed": TICKET_SEED, "status": "unknown",
        "authoring_started_utc": "2026-10-23T09:49:39Z",
        "probe_started_utc": datetime.now(timezone.utc).isoformat(),
        "targeted_probe_count": 1, "targeted_probe_limit_seconds": 120,
        "generator_sha256": sha(GENERATOR), "rule_hash": EXPECTED_RULE,
        "probe_sha256": sha(Path(__file__)),
        "shortcut": "Choose the most frequent nonzero input color (ties: smallest color), then tile the zero-mask complement 2 by 2.",
        "limits": [
            "One generated input, one canonical Racket application; no peer battery, census, or lesson-wide ambiguity assessment.",
            "This refutes an existing declared rival on one production input. It is not a newly confirmed production lesson defect or a no-issue safety certification.",
        ],
    }
    try:
        assert report["generator_sha256"] == EXPECTED_SOURCE, "source identity mismatch"
        programs = []
        with (ROOT / "shared/data/canonical/puzzles.jsonl").open() as stream:
            for line in stream:
                row = json.loads(line)
                if row.get("task_id") == TASK:
                    programs.append(row["program_solution"])
        assert programs and len(set(programs)) == 1, "missing or divergent selected canonical program"
        program = programs[0]
        actual_rule = hashlib.sha256(" ".join(program.split()).encode()).hexdigest()[:12]
        assert actual_rule == EXPECTED_RULE, "canonical rule identity mismatch"
        assert program.startswith("(rule! ") and program.endswith(")"), "unexpected rule wrapper"
        report["canonical_program_sha256"] = hashlib.sha256(program.encode()).hexdigest()
        report["canonical_rule_hash"] = actual_rule
        spec = importlib.util.spec_from_file_location("assigned_witness_generator", GENERATOR)
        generator = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(generator)
        assert generator.RULE_HASH == actual_rule
        seed = int(TICKET_SEED[:16], 16)
        index = 1 + 3 * (int(TICKET_SEED[-2:], 16) % 2)
        grid = generator.generate(seed, index, difficulty="medium")
        reasons = generator.self_check(grid)
        first = next(value for row in grid for value in row if value)
        counts = Counter(value for row in grid for value in row if value)
        mode = min(counts, key=lambda value: (-counts[value], value))
        h, w = len(grid), len(grid[0])
        rival = [[mode if grid[r % h][c % w] == 0 else 0 for c in range(2*w)] for r in range(2*h)]
        diagnostic = [[first if grid[r % h][c % w] == 0 else 0 for c in range(2*w)] for r in range(2*h)]
        report.update({
            "sample": {"seed": seed, "sample_index": index, "difficulty": "medium", "overrides": {},
                       "seed_recipe": "int(ticket_seed[:16],16)",
                       "sample_index_recipe": "1 + 3*(int(ticket_seed[-2:],16)%2)",
                       "schedule_profile": generator.schedule_profile(seed, index, "medium")},
            "input": grid, "self_check_reasons": reasons,
            "nonzero_color_counts": dict(sorted(counts.items())),
            "first_row_major_color": first, "rival_mode_color": mode,
            "rival_output": rival,
        })
        assert not reasons, "generated witness rejected by target validator"
        assert first != mode, "selected input does not distinguish shortcut"
        from arc_repl.racket_bridge import RacketBridge
        with RacketBridge(startup_timeout=60.0, timeout=10.0) as bridge:
            bridge.eval_text(f"(define ticket_candidate {program[7:-1]})")
            bridge.define_grid("ticket_input", grid)
            actual = bridge.eval_text("(ticket_candidate ticket_input)")
        report["racket_output"] = actual
        report["racket_matches_independent_diagnostic"] = actual == diagnostic
        report["racket_differs_from_shortcut"] = actual != rival
        report["output_shape"] = [len(actual), len(actual[0])]
        report["generator_sha256_after"] = sha(GENERATOR)
        assert report["generator_sha256_after"] == EXPECTED_SOURCE, "source changed during probe"
        assert actual == diagnostic, "canonical execution disagrees with diagnostic expectation"
        assert actual != rival, "Racket result does not distinguish shortcut"
        report["status"] = "completed"
        report["summary"] = "Retained one lawful, default-generated multicolor witness: canonical Racket selects the first row-major color while the nonzero-mode shortcut selects a different color. Existing curriculum counterexample confirmed; no new production defect claimed."
        report["exit_code"] = 0
    except Exception as exc:
        report["status"] = "blocked" if isinstance(exc, (ImportError, FileNotFoundError)) else "unknown"
        report["error"] = f"{type(exc).__name__}: {exc}"
        report["summary"] = "The single bounded probe did not establish a lawful shortcut witness; see retained error."
        report["exit_code"] = 1
    report["probe_elapsed_seconds"] = round(time.monotonic() - start, 6)
    report["probe_finished_utc"] = datetime.now(timezone.utc).isoformat()
    (OUT / "result.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({key: report[key] for key in ("status", "summary", "probe_elapsed_seconds", "exit_code")}))
    return report["exit_code"]


if __name__ == "__main__":
    raise SystemExit(main())
