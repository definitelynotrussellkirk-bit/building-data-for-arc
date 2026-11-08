"""One pinned generated episode; one rival; no seed search or peer battery."""
from pathlib import Path
import hashlib
import importlib.util
import json
import sys
import time

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[2]
REPO = WORK / "repo"
sys.path[:0] = [str(REPO / "src"), str(REPO / "shared/runtime")]
SOURCE = REPO / "generators/generic_waypoint_route_gen2/generator.py"
EXPECTED_SOURCE = "a4317b9a443121b6c8342c79a651e94e0ffa741facdbb545f81d6a5ebf040b15"
SEED = "b424b07ac03fedb8ff59e0984af4c4829550d8fa671e9c45b1b386f0b1b603e2"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def grid_hash(grid):
    return sha(json.dumps(grid, separators=(",", ":")).encode())


started = time.monotonic()
assert sha(SOURCE.read_bytes()) == EXPECTED_SOURCE
assert sha((HERE / "gen1_dependency.py").read_bytes()) == "b0c6b063ee8f18c10ddaefc8692939d88365692671eb8d255e0ced0b596cc3bc"
load("puzzle_generators.generic.concepts.waypoint_route.gen1", HERE / "gen1_dependency.py")
gen = load("ticket_waypoint_gen2", SOURCE)
from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule

row = next(json.loads(line) for line in (REPO / "shared/data/canonical/puzzles.jsonl").read_text().splitlines()
           if json.loads(line).get("task_id") == "generic_waypoint_route_gen2")
raw = row["program_solution"]
assert raw == gen.PROGRAM
assert sha(" ".join(raw.split()).encode())[:12] == "46236b0fd524" == gen.RULE_HASH
wrapped = wrap_rule(raw)
# Deterministic conversion of the assigned hexadecimal seed, with no redraw.
generation_seed = int(SEED, 16)
lesson = gen.generate_task(generation_seed, difficulty="medium")
assert gen.self_check_task(lesson) == []


def preserve_initial_orientation(grid):
    state = gen._parse_last_state(grid)
    position = state["head"]
    initial_tail_offset = (state["tail"][0] - position[0], state["tail"][1] - position[1])
    remaining = list(state["dots"])
    while remaining:
        aligned = [p for p in remaining if p[0] == position[0] or p[1] == position[1]]
        if len(aligned) != 1:
            raise ValueError("rival requires the same lawful unique route")
        position = aligned[0]
        remaining.remove(position)
    panel = state["panel"]
    output = [[state["bg"]] * len(panel[0]) for _ in panel]
    tail = (position[0] + initial_tail_offset[0], position[1] + initial_tail_offset[1])
    assert 0 <= tail[0] < len(panel) and 0 <= tail[1] < len(panel[0])
    output[position[0]][position[1]] = state["head_color"]
    output[tail[0]][tail[1]] = state["tail_color"]
    return output


cases = []
with RacketBridge(timeout=30.0) as bridge:
    definition = f"(define ticket-rule {wrapped})"
    bridge.eval_text(definition)
    version = bridge.eval_text("(version)")
    for index, pair in enumerate(lesson["train"] + lesson["test"]):
        grid = pair["input"]
        errors = gen.strict_canonical_like(grid)
        assert not errors
        name = f"ticket-grid-{index}"
        bridge.define_grid(name, grid)
        expected = bridge.eval_text(f"(ticket-rule {name})")
        rival = preserve_initial_orientation(grid)
        differences = [{"row": r, "col": c, "canonical": expected[r][c], "rival": rival[r][c]}
                       for r in range(len(expected)) for c in range(len(expected[0]))
                       if expected[r][c] != rival[r][c]]
        state = gen._parse_last_state(grid)
        cases.append({"pair_index": index, "role": "demo" if index < 3 else "query",
                      "input_sha256": grid_hash(grid), "canonical_output_sha256": grid_hash(expected),
                      "input": grid, "generated_output": pair["output"], "racket_output": expected,
                      "rival_output": rival, "different_cells": differences,
                      "strict_canonical_like": errors,
                      "generated_label_matches_racket": pair["output"] == expected,
                      "remaining_waypoint_count": len(state["dots"]),
                      "input_head": list(state["head"]), "input_tail": list(state["tail"])})

assert sha(SOURCE.read_bytes()) == EXPECTED_SOURCE
matches = [not case["different_cells"] for case in cases[:3]]
lesson_errors = gen.lesson_identifiable(lesson["train"], lesson["test"][0])
# Retain exactly one selected discriminator, preferring the generated query.
witness = next((case for case in [cases[3]] + cases[:3] if case["different_cells"]), None)
if any(not case["generated_label_matches_racket"] for case in cases):
    status, conclusion = "finding", "generated label disagrees with pinned canonical Racket"
elif all(matches) and cases[3]["different_cells"] and not lesson_errors:
    status, conclusion = "finding", "rival fits all generated demonstrations and differs on accepted generated query"
elif witness is not None:
    status, conclusion = "completed", "lawful generated discriminator retained; generated demonstrations already refute this rival, so no peer safety defect established"
else:
    status, conclusion = "unknown", "the one generated episode did not separate this rival; no further search was authorized"
report = {"ticket_id": "ticket-6527fb9654467643", "type": "adversarial_witness",
          "status": status, "conclusion": conclusion, "task_id": gen.TASK_ID,
          "assigned_seed": SEED, "generation_seed_integer": generation_seed, "difficulty": "medium",
          "source_sha256": EXPECTED_SOURCE, "dependency_sha256": sha((HERE / "gen1_dependency.py").read_bytes()),
          "probe_sha256": sha(Path(__file__).read_bytes()),
          "rule": {"normalized_hash": gen.RULE_HASH, "raw_program_sha256": sha(raw.encode()),
                   "wrapped_callable_sha256": sha(wrapped.encode()), "complete_definition_sha256": sha(definition.encode())},
          "racket_version": version, "reference_application_count": 4,
          "rival": "trace the complete unique route, but preserve the input cursor head-to-tail offset when rendering the final cursor",
          "demo_rival_matches": matches, "query_rival_difference_cells": len(cases[3]["different_cells"]),
          "self_check_task": [], "lesson_identifiable": lesson_errors,
          "case_summaries": [{k: v for k, v in case.items() if k not in ("input", "generated_output", "racket_output", "rival_output", "different_cells")} | {"rival_difference_cells": len(case["different_cells"])} for case in cases],
          "witness": witness, "demonstrations": lesson["train"],
          "scope": "one pinned seed, one ordinary generated episode, one rival, one targeted probe",
          "not_run": ["additional seeds", "peer battery", "large census", "exhaustive rivals", "approval or audit clearance"],
          "existing_authority_scope": row.get("rule_scope"),
          "existing_scope_not_a_new_finding": "canonical written solution explicitly states earlier panels are unused context",
          "elapsed_seconds": time.monotonic() - started}
(HERE / "witness.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps({key: report[key] for key in ("status", "conclusion", "demo_rival_matches", "query_rival_difference_cells", "reference_application_count", "elapsed_seconds")}))
