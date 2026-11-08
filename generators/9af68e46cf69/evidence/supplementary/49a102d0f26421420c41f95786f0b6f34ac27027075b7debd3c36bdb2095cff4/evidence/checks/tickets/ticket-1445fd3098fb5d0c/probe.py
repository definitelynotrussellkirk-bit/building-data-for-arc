#!/usr/bin/env python3
"""Exactly one source-pinned open-bbox adversarial witness; no search or census."""
from collections import deque
from pathlib import Path
import hashlib
import json
import signal
import time

from reviewer_support import load_selected_generator
from arc_repl.racket_bridge import RacketBridge

TASK_ID = "9af68e46cf69"
TICKET_ID = "ticket-1445fd3098fb5d0c"
EXPECTED_SOURCE = "2eb732c96e68ad6de3d40e0af4bf307fcc8f94d0d0774b818adf361814a213a8"
EXPECTED_RULE = "7fd2884c3200"
SEED_HEX = "af1194cafc7afda1234635d20ff24d76f3badc651f8018a0bb1e6b883dd881f3"
OUT = Path(__file__).resolve().parent
WORK = OUT.parents[2]
ROOT = WORK / "repo"
DELTAS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def components(grid, color):
    todo = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color}
    answer = []
    while todo:
        start = min(todo)
        todo.remove(start)
        queue = deque([start])
        component = {start}
        while queue:
            r, c = queue.popleft()
            for dr, dc in DELTAS:
                point = (r + dr, c + dc)
                if point in todo:
                    todo.remove(point)
                    component.add(point)
                    queue.append(point)
        answer.append(component)
    return answer


def bbox(component):
    return min(r for r, c in component), min(c for r, c in component), max(r for r, c in component), max(c for r, c in component)


def inside(point, box):
    r, c = point
    r0, c0, r1, c1 = box
    return r0 < r < r1 and c0 < c < c1


def escape_path(grid, start, box):
    queue = deque([start])
    previous = {start: None}
    r0, c0, r1, c1 = box
    while queue:
        r, c = queue.popleft()
        if not (r0 <= r <= r1 and c0 <= c <= c1):
            path = []
            point = (r, c)
            while point is not None:
                path.append(list(point))
                point = previous[point]
            return path[::-1]
        for dr, dc in DELTAS:
            point = (r + dr, c + dc)
            rr, cc = point
            if 0 <= rr < len(grid) and 0 <= cc < len(grid[0]) and grid[rr][cc] == 9 and point not in previous:
                previous[point] = (r, c)
                queue.append(point)
    raise AssertionError("open-bbox background did not reach the exterior")


def sexpr_grid(grid):
    return "(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"


def write_json(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def main():
    started = time.monotonic()
    signal.signal(signal.SIGALRM, lambda *args: (_ for _ in ()).throw(TimeoutError("single probe exceeded 110 seconds")))
    signal.alarm(110)
    result = {"ticket_id": TICKET_ID, "type": "adversarial_witness", "targeted_probe_count": 1,
              "task_id": TASK_ID, "seed": SEED_HEX, "seed_integer_conversion": "int(seed_hex, 16)",
              "sample_index": 0, "shortcut": "any_bbox_background", "status": "unknown"}
    try:
        gen, source, actual_source = load_selected_generator(TASK_ID, root=ROOT)
        assert actual_source == EXPECTED_SOURCE
        assert gen.RULE_HASH == EXPECTED_RULE
        canonical = next(json.loads(line) for line in (ROOT / "shared/data/canonical/puzzles.jsonl").read_text().splitlines()
                         if json.loads(line).get("task_id") == TASK_ID)
        program = canonical["program_solution"]
        rule_hash = hashlib.sha256(" ".join(program.split()).encode()).hexdigest()[:12]
        assert rule_hash == EXPECTED_RULE
        (OUT / "canonical_rule.rkt").write_text(program)
        result.update(generator_source="repo/generators/9af68e46cf69/generator.py", generator_sha256=actual_source,
                      rule_hash=rule_hash, program_sha256=hashlib.sha256(program.encode()).hexdigest())
        controls = {"grid_h": 9, "grid_w": 11, "n_holey": 1, "n_solid": 1}
        grid = gen.generate(int(SEED_HEX, 16), 0, **controls)
        errors = gen.self_check(grid, meta={"overrides": controls})
        assert errors == [], errors
        blue = components(grid, 1)
        background = components(grid, 9)
        assert len(grid) == 9 and len(grid[0]) == 11
        assert {cell for row in grid for cell in row} == {1, 9}
        expected = [row[:] for row in grid]
        rival = [row[:] for row in grid]
        positives, decoys = [], []
        for obj in blue:
            box = bbox(obj)
            holes = [region for region in background if all(inside(point, box) for point in region)]
            interior = sorted(point for region in background for point in region if inside(point, box))
            if holes:
                positives.append(obj)
                for r, c in obj:
                    expected[r][c] = 8
            elif interior:
                decoys.append((obj, box, interior[0]))
            if interior:
                for r, c in obj:
                    rival[r][c] = 8
        assert len(blue) == 2 and len(positives) == 1 and len(decoys) == 1
        assert rival == gen.SEMANTIC_RIVALS["any_bbox_background"](grid)
        obj, box, start = decoys[0]
        path = escape_path(grid, start, box)
        assert all(grid[r][c] == 9 for r, c in path)
        assert all(abs(a[0]-b[0]) + abs(a[1]-b[1]) == 1 for a, b in zip(path, path[1:]))
        body = program.strip()
        assert body.startswith("(rule! ") and body.endswith(")")
        function = body[len("(rule! "):-1]
        with RacketBridge(timeout=10, startup_timeout=20) as bridge:
            actual = bridge.eval_text("(" + function + " '" + sexpr_grid(grid) + ")")
            runtime = bridge.runtime_identity
        assert actual == expected
        assert actual != rival
        differences = [[r, c] for r in range(len(grid)) for c in range(len(grid[0])) if actual[r][c] != rival[r][c]]
        assert {tuple(point) for point in differences} == obj
        witness = {"input": grid, "output": actual, "rival_output": rival,
                   "decoy_cells": sorted([list(point) for point in obj]), "decoy_bbox": list(box),
                   "interior_background_cell": list(start), "background_escape_path": path,
                   "disagreement_cells": differences}
        write_json("witness.json", witness)
        result.update(status="completed", overrides=controls, lawful_self_check_errors=errors,
                      independently_counted_positive_objects=len(positives), independently_counted_negative_objects=len(blue)-len(positives),
                      racket_output_matches_independent_rule=True, rival_disagreement_cells=len(differences),
                      decoy_bbox=list(box), background_escape_path=path, runtime_identity=runtime,
                      limitation="One exact controlled draw and one shortcut only; no lesson, seed-space, census, or overall safety claim.")
    except Exception as error:
        result.update(error_type=type(error).__name__, error=str(error))
    finally:
        signal.alarm(0)
    result["probe_elapsed_seconds"] = round(time.monotonic() - started, 6)
    result["probe_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    write_json("results.json", result)
    print(json.dumps({key: value for key, value in result.items() if key != "runtime_identity"}, sort_keys=True))
    return 0 if result["status"] == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
