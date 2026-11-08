"""One pinned-source, pinned-seed probe of a dimension-template shortcut."""
from __future__ import annotations
import datetime
import hashlib
import json
from pathlib import Path
import signal
import sys
import time
import traceback

TICKET = "ticket-e90ecd36fc166b47"
TASK = "28b87bd4c441"
PINNED_SHA = "29036f7470aca505bde6c0a0f047c9a131ab22a9a27abcd6b111d333ea6ebc2e"
PINNED_RULE = "0af5c7008ee7"
PROBE_SEED = "b150e9ec8d7c50a3db2e3969f9ab182d3aa1130d308ddb99bed538ce4120948f"
OUT = Path(__file__).resolve().parent
WORK = OUT.parents[2]
ROOT = WORK / "repo"
PREFIX = f"checks/tickets/{TICKET}"
COMMAND = f"python3 review.py run --receipt {PREFIX}/command.json python3 ../{PREFIX}/probe.py"
START = time.monotonic()
START_UTC = datetime.datetime.now(datetime.timezone.utc).isoformat()
signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError("115-second probe limit")))
signal.alarm(115)


def sha(body):
    return hashlib.sha256(body if isinstance(body, bytes) else body.encode()).hexdigest()


def compact(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def learn_dimension_templates(demos):
    learned = {}
    for pair in demos:
        grid = pair["input"]
        marker = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 2]
        assert len(marker) == 1
        mr, mc = marker[0]
        template = tuple((r-mr, c-mc) for r, row in enumerate(pair["output"]) for c, v in enumerate(row) if v == 5)
        key = (len(grid), len(grid[0]))
        if key in learned:
            assert learned[key] == template
        learned[key] = template
    return learned


def template_rival(grid, learned):
    """Read dimensions and red marker only; never read gray source geometry."""
    h, w = len(grid), len(grid[0])
    marker = next((r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 2)
    output = [[0] * w for _ in range(h)]
    for dr, dc in learned[(h, w)]:
        r, c = marker[0]+dr, marker[1]+dc
        assert 0 <= r < h and 0 <= c < w
        output[r][c] = 5
    return output


result = {
    "ticket_id": TICKET, "type": "adversarial_witness", "status": "unknown",
    "summary": "Probe did not complete.", "evidence_paths": [f"{PREFIX}/probe.py", f"{PREFIX}/result.json", f"{PREFIX}/command.json"],
    "elapsed_minutes": None,
    "timing_note": "Total authoring time was not instrumented; elapsed_minutes remains null. Payload runtime is measured separately.",
    "probe_seed": PROBE_SEED,
    "command": COMMAND,
    "launch_cwd": str(ROOT.parents[1]), "payload_cwd": str(Path.cwd()),
    "targeted_probe_limit_seconds": 120, "targeted_probe_count": 1,
    "started_utc": START_UTC,
}
try:
    assert Path.cwd().resolve() == ROOT.resolve()
    source_path = ROOT / f"generators/{TASK}/generator.py"
    # Verify raw bytes before loading the target or invoking any target method.
    source_body = source_path.read_bytes()
    assert sha(source_body) == PINNED_SHA, "Pinned generator changed"
    sys.path.insert(0, str(ROOT / "shared/runtime"))
    from reviewer_support import load_selected_generator, canonical_pairs
    from arc_repl.racket_bridge import RacketBridge
    generator, loaded_path, loaded_sha = load_selected_generator(TASK, root=ROOT)
    assert loaded_sha == PINNED_SHA and loaded_path.resolve() == source_path.resolve()
    rows = []
    for line in (ROOT / "shared/data/canonical/puzzles.jsonl").open():
        row = json.loads(line)
        if row.get("task_id") == TASK:
            rows.append(row)
    programs = {row["program_solution"] for row in rows}
    assert len(programs) == 1
    program = programs.pop()
    rule_hash = sha(" ".join(program.split()))[:12]
    assert rule_hash == PINNED_RULE == generator.RULE_HASH
    normalized = canonical_pairs(TASK, root=ROOT)
    canon_train = [pair for pair in normalized if pair["split"] == "train"]
    canon_test = [pair for pair in normalized if pair["split"] == "test"]
    assert len(canon_train) == 3 and len(canon_test) == 1
    query = canon_test[0]
    generator_seed = int(PROBE_SEED[:16], 16)
    demo_inputs = [generator.generate(generator_seed, index, difficulty="medium") for index in range(8)]
    profiles = [generator.observe_overrides(grid)["scene_profile"] for grid in demo_inputs]
    assert set(profiles) == set(generator.PROFILE_NAMES)
    inputs = demo_inputs + [pair["input"] for pair in canon_train] + [query["input"]]
    assert all(generator.self_check(grid) == [] for grid in inputs)
    source = program.strip()
    assert source.startswith("(rule!") and source.endswith(")")
    inner = source[len("(rule!"):-1].strip()
    callable_source = f"(lambda (g) {inner})"
    literals = ["(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")" for grid in inputs]
    expression = f"(map {callable_source} '({' '.join(literals)}))"
    (OUT / "reference-batch.rkt").write_text(expression + "\n")
    with RacketBridge() as bridge:
        outputs = bridge.eval_text(expression)
        runtime = bridge.runtime_identity
    assert len(outputs) == 12
    assert outputs == [generator.rule_mirror(grid) for grid in inputs]
    assert outputs[8:11] == [pair["output"] for pair in canon_train]
    assert outputs[-1] == query["output"]
    demos = [{"input": grid, "output": out} for grid, out in zip(demo_inputs, outputs[:8])]
    learned = learn_dimension_templates(demos)
    assert all(template_rival(pair["input"], learned) == pair["output"] for pair in demos)
    assert all(template_rival(pair["input"], learned) == pair["output"] for pair in canon_train)
    rival_output = template_rival(query["input"], learned)
    correct_output = outputs[-1]
    differences = [{"row": r, "col": c, "racket": correct_output[r][c], "rival": rival_output[r][c]}
                   for r in range(len(correct_output)) for c in range(len(correct_output[0]))
                   if correct_output[r][c] != rival_output[r][c]]
    assert differences == [{"row": 2, "col": 2, "racket": 0, "rival": 5}, {"row": 2, "col": 3, "racket": 5, "rival": 0}]
    hook = generator.lesson_identifiable(demos, {"input": query["input"]})
    assert hook == []
    strict = generator.strict_canonical_like(query["input"])
    assert strict == []
    try:
        generator.observe_overrides(query["input"])
    except ValueError as exc:
        observed_rejection = str(exc)
    else:
        raise AssertionError("Expected canonical witness outside exact sampling profiles")
    assert source_body == source_path.read_bytes()
    witness = {
        "task_id": TASK, "rival": "Learn one shape template per grid dimensions from demo outputs; stamp that shape at red marker, ignoring query gray cells.",
        "generator_seed_derivation": "int(probe_seed[:16],16)", "generator_seed": generator_seed,
        "sample_indices": list(range(8)), "difficulty": "medium", "profiles": profiles,
        "train": demos, "query": {"input": query["input"], "racket_output": correct_output, "rival_output": rival_output},
        "differences": differences,
        "learned_templates": [{"dimensions": list(k), "offsets": list(v)} for k, v in sorted(learned.items())],
        "generator_self_check": [], "strict_canonical_like": strict,
        "lesson_identifiable": hook, "observe_overrides_rejection": observed_rejection,
        "canonical_training_pairs": [{"input": pair["input"], "output": pair["output"]} for pair in canon_train],
        "racket_labels_match": {"generated_demo_pairs": 8, "canonical_pairs": 4},
    }
    (OUT / "witness.json").write_text(compact(witness) + "\n")
    bindings = {
        "generator_path": f"repo/generators/{TASK}/generator.py", "generator_sha256": loaded_sha,
        "canonical_path": "repo/shared/data/canonical/puzzles.jsonl", "rule_task_id": TASK,
        "rule_hash": rule_hash, "canonical_raw_program_sha256": sha(program),
        "executed_callable_sha256": sha(callable_source), "executed_expression_sha256": sha(expression),
        "racket_runtime": {key: runtime[key] for key in ("schema", "backend", "protected", "binary_sha256", "prelude_sha256", "bridge_sha256", "boot_script_sha256") if key in runtime},
    }
    result.update({
        "status": "finding", "exit_code": 0,
        "summary": "Corroborated an existing source-bound teaching/coverage finding: a dimension-template rival fits one fresh eight-demo lesson and all three canonical training pairs, but differs at two cells on the validator-accepted canonical query. The lesson hook accepts that query. All 12 Racket labels match the unchanged mirror; no sampled-production label error is claimed.",
        "source_bindings": bindings, "generator_seed": generator_seed,
        "fresh_counts": {"generated_demonstrations": 8, "canonical_training_pairs": 3, "canonical_query": 1, "racket_executed_inputs": 12, "query_difference_cells": 2},
        "existing_finding_return_id": "review-c80cb054851bda44:v0001",
        "limits": ["One seed/profile cycle and one existing canonical query, not a census.", "The witness passes self_check and strict_canonical_like but is outside the eight exact generated profiles.", "This corroborates a retained unresolved finding; it does not establish a wrong reference label, sampled-production failure, or automatic audit disposition."],
    })
    result["evidence_paths"] += [f"{PREFIX}/witness.json", f"{PREFIX}/reference-batch.rkt", f"{PREFIX}/AUDIT-proposed.md"]
    audit = f"""## {TASK}

**Source-bound corroboration — dimension-template shortcut remains on the pinned source.**
Supplementary ticket `{TICKET}` ran one bounded probe against generator SHA-256
`{loaded_sha}` and canonical rule `{rule_hash}` (raw program SHA-256
`{sha(program)}`). This corroborates the retained unresolved finding
`review-c80cb054851bda44:v0001`; it is not a separate new label-error claim.

The pinned ticket seed was converted with `int(probe_seed[:16],16)` to
`{generator_seed}`. One fresh medium-difficulty lesson at sample indices 0–7
covers all eight profiles. A rival learns a shape template for each canvas size
from those demonstration outputs and stamps that template at the red marker,
without examining query gray geometry. It fits all eight demonstrations and the
three canonical training pairs. On the original 12×13 canonical query it differs
from protected Racket at `(2,2)` (rival 5, reference 0) and `(2,3)` (rival 0,
reference 5), using zero-based coordinates.

The canonical query passes `self_check` and `strict_canonical_like`; the complete
eight-demo lesson also returns `lesson_identifiable == []` for it. Conversely,
`observe_overrides` rejects that query because it is outside the eight exact
sampling profiles. This is a teaching and canonical-coverage limitation. All
12 executed reference outputs match the unchanged mirror and all four canonical
labels. No wrong reference label or failure on a sampled production query is
claimed. No peer source, approval record, or audit disposition was changed.

Evidence, relative to WORK: `{PREFIX}/witness.json`, `{PREFIX}/probe.py`,
`{PREFIX}/reference-batch.rkt`, `{PREFIX}/result.json`, and
`{PREFIX}/command.json`. The result retains source/runtime hashes and scope.
Suggested follow-up remains to vary lawful shapes within each canvas size and
include a demo that defeats this rival before claiming canonical-query coverage.
"""
    (OUT / "AUDIT-proposed.md").write_text(audit)
except BaseException as exc:
    result.update({"status": "unknown", "exit_code": 1, "summary": f"Bounded probe stopped: {type(exc).__name__}: {exc}", "error": traceback.format_exc()})
finally:
    signal.alarm(0)
    result["payload_elapsed_seconds"] = round(time.monotonic() - START, 3)
    result["finished_utc"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    (OUT / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({key: result[key] for key in ("ticket_id", "status", "exit_code", "payload_elapsed_seconds", "summary")}))
sys.exit(result["exit_code"])
