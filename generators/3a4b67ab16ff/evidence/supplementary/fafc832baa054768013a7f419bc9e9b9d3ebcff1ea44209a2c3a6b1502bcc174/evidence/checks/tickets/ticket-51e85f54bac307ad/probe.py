"""One source-bound generated witness against reversed overlap priority."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import signal
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[2]
REPO = WORK / "repo"
TICKET = "ticket-51e85f54bac307ad"
TASK = "3a4b67ab16ff"
SEED_HEX = "4b76b33b814a3412ad779c3a4fee1171f5450fdddd5de0fedd3b35e5aa361255"
SOURCE = REPO / f"generators/{TASK}/generator.py"
RULE = REPO / "shared/data/base/solutions/training/1c02dbbe__3a4b67ab16ff.json"
PINNED_SOURCE = "abd406bd9626d25aba8dc67db0971b3722302a2959e2b6453dcbba2cfb431b7f"
PINNED_RULE = "32c694357bd0"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def bounds(cells):
    return [min(r for r, c in cells), min(c for r, c in cells),
            max(r for r, c in cells), max(c for r, c in cells)]


def clipped_cells(box, gray):
    return {(r, c)
            for r in range(max(box[0], gray[0]), min(box[2], gray[2]) + 1)
            for c in range(max(box[1], gray[1]), min(box[3], gray[3]) + 1)}


def main():
    started = time.perf_counter()
    receipt = {"ticket_id": TICKET, "type": "adversarial_witness",
               "targeted_probes": 1, "targeted_probe_budget_seconds": 120,
               "seed": SEED_HEX, "task_id": TASK}

    def timed_out(signum, frame):
        raise TimeoutError("single targeted probe exceeded 115-second internal deadline")

    signal.signal(signal.SIGALRM, timed_out)
    signal.alarm(115)
    try:
        source_sha = digest(SOURCE.read_bytes())
        record = json.loads(RULE.read_text())
        program = record["racket_target"]["target_code"]
        normalized_sha = digest(" ".join(program.split()).encode())
        receipt["identity"] = {
            "generator_path": str(SOURCE.relative_to(WORK)),
            "generator_sha256": source_sha,
            "rule_path": str(RULE.relative_to(WORK)),
            "rule_file_sha256": digest(RULE.read_bytes()),
            "rule_source_sha256": digest(program.encode()),
            "rule_normalized_sha256": normalized_sha,
            "rule_hash": normalized_sha[:12],
            "probe_sha256": digest(Path(__file__).read_bytes()),
        }
        assert source_sha == PINNED_SOURCE, "pinned generator source mismatch"
        assert normalized_sha[:12] == PINNED_RULE, "pinned canonical rule mismatch"

        sys.path.insert(0, str(REPO / "shared/runtime"))
        from arc_repl.racket_bridge import RacketBridge
        from puzzle_generators.rule_wrap import strip_line_comments, strip_rule_wrapper

        spec = importlib.util.spec_from_file_location("ticket_target_generator", SOURCE)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        kwargs = {"seed": int(SEED_HEX, 16), "sample_index": 0,
                  "difficulty": "medium", "scene_profile": "overlap_priority"}
        grid = module.generate(**kwargs)  # Exactly one generated scene.
        errors = module.self_check(grid)
        assert errors == [], f"generated witness is not lawful: {errors}"
        observed = module.observe_overrides(grid)
        assert observed == {"scene_profile": "overlap_priority"}, observed

        gray = bounds([(r, c) for r, row in enumerate(grid)
                       for c, value in enumerate(row) if value == 5])
        colors = sorted({value for row in grid for value in row} - {0, 5})
        assert len(colors) == 2, colors
        boxes = {color: bounds([(r, c) for r, row in enumerate(grid)
                                for c, value in enumerate(row) if value == color])
                 for color in colors}
        intersections = {color: clipped_cells(boxes[color], gray) for color in colors}
        overlap = set.intersection(*(intersections[color] for color in colors))
        assert overlap, "profile did not contain an overlap"

        # Rival: retain the intended geometry but fill in descending numeric
        # order, making the lower color win any overlap.
        shortcut = [[0] * len(grid[0]) for _ in grid]
        for r in range(gray[0], gray[2] + 1):
            for c in range(gray[1], gray[3] + 1):
                shortcut[r][c] = 5
        for color in reversed(colors):
            for r, c in intersections[color]:
                shortcut[r][c] = color

        body = strip_rule_wrapper(strip_line_comments(program))
        assert body.startswith("(lambda"), "this probe expects the pinned explicit lambda"
        with RacketBridge(timeout=20, startup_timeout=30) as bridge:
            bridge.define_grid("ticket-witness", grid)
            canonical = bridge.eval_text(f"({body} ticket-witness)")
            receipt["racket_binary"] = bridge.racket_binary
        assert canonical == module.rule_mirror(grid), "generator mirror differs from canonical Racket"
        changed = [(r, c) for r, row in enumerate(canonical)
                   for c, value in enumerate(row) if value != shortcut[r][c]]
        assert set(changed) == overlap, "rival difference was not exactly the overlap"
        assert all(canonical[r][c] == colors[-1] and shortcut[r][c] == colors[0]
                   for r, c in changed), "unexpected color winner"

        witness = {
            "ticket_id": TICKET, "identity": receipt["identity"],
            "probe_seed_hex": SEED_HEX, "generation_kwargs": kwargs,
            "input": grid, "canonical_racket_output": canonical,
            "shortcut_output": shortcut,
            "shortcut": "Correct bounding-box intersections, descending color order; lower color wins overlaps.",
            "self_check_errors": errors, "observed_overrides": observed,
            "gray_bbox": gray, "color_bboxes": boxes,
            "differing_cells": changed, "difference_count": len(changed),
            "canonical_winning_color": colors[-1], "shortcut_winning_color": colors[0],
        }
        destination = HERE / "witness.json"
        destination.write_text(json.dumps(witness, indent=2) + "\n")
        receipt.update({
            "status": "completed", "checks_passed": 8,
            "summary": f"One lawful generated overlap_priority scene refutes lower-color-wins: canonical Racket and the generator mirror agree; rival differs at exactly {len(changed)} overlap cells. No new safety finding is claimed.",
            "witness_path": str(destination.relative_to(WORK)),
            "witness_sha256": digest(destination.read_bytes()),
            "generator_mirror_matches_canonical": True,
            "difference_count": len(changed),
        })
        exit_code = 0
    except Exception as exc:
        receipt.update({"status": "unknown", "error": f"{type(exc).__name__}: {exc}",
                        "summary": "The one bounded probe did not establish a lawful shortcut witness."})
        exit_code = 1
    finally:
        signal.alarm(0)
        receipt["probe_elapsed_seconds"] = round(time.perf_counter() - started, 6)
        receipt["exit_code"] = exit_code
        (HERE / "probe.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt, indent=2))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
