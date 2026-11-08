"""Source-bound, findings-only audit; no runtime snapshot or source mutation."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import time

from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator
from arc_repl.racket_bridge import RacketBridge

TASK = "d53f4142488d"
EXPECTED_SOURCE_SHA = "017b9c870defd3c3ddb2819c7166466e94fe2a2964d6b009baccc3f068902a3f"
EXPECTED_RULE_SHA = "e9afa0f7c2033d6728e454df630bb1a8f5763a8e42f73a8e338d97cfd395a969"
HERE = Path(__file__).resolve().parent
ROOT = find_root(__file__)
COMMAND = (
    "PATH=/dev/shm/arcpuzzles_racket_4c463a4d2f73/bin:$PATH "
    "WORK/.venv/bin/python review.py run "
    "/workspace/scratch/4c463a4d2f73/arc_review/WORK/.venv/bin/python "
    "../checks/audit/d53f4142488d/probe.py"
)


def digest(value):
    raw = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def components(grid, color):
    """Independent four-neighbor count in the rule's body region (rows >= 7)."""
    remaining = {(r, c) for r in range(7, len(grid)) for c in range(len(grid[0]))
                 if grid[r][c] == color}
    count = 0
    while remaining:
        count += 1
        stack = [remaining.pop()]
        while stack:
            r, c = stack.pop()
            for point in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if point in remaining:
                    remaining.remove(point)
                    stack.append(point)
    return count


def no_cleanup_rival(grid):
    """Count indicator-color objects and draw bars, but preserve the entire body."""
    result = deepcopy(grid)
    for row in (1, 3, 5):
        color = grid[row][0]
        result[row][0] = 0
        for column in range(min(len(grid[0]), components(grid, color))):
            result[row][column] = color
    return result


def changed_cells(left, right):
    return [[r, c, left[r][c], right[r][c]]
            for r in range(len(left)) for c in range(len(left[r]))
            if left[r][c] != right[r][c]]


def foreign_cells(grid):
    allowed = {grid[1][0], grid[3][0], grid[5][0], grid[7][0]}
    return [[r, c, grid[r][c]] for r in range(7, len(grid))
            for c in range(len(grid[0])) if grid[r][c] not in allowed]


def main():
    started = time.monotonic()
    generator, source_path, generator_sha = load_selected_generator(TASK, root=ROOT)
    if generator_sha != EXPECTED_SOURCE_SHA:
        raise ValueError("Audit source differs from its assigned immutable version")
    with canonical_path(ROOT).open() as stream:
        selected = [row for line in stream if line.strip()
                    for row in [json.loads(line)] if row.get("task_id") == TASK]
    if len(selected) != 1:
        raise ValueError("Expected exactly one selected canonical rule variant")
    rule = selected[0]["program_solution"]
    rule_sha = hashlib.sha256(rule.encode()).hexdigest()
    if rule_sha != EXPECTED_RULE_SHA or not rule.startswith("(rule! (lambda "):
        raise ValueError("Unsupported or changed hash-pinned rule envelope")
    # This exact selected source is already ordinary Racket. Remove only its
    # outer rule! transport form; preserve the lambda body byte-for-byte.
    wrapped = rule[len("(rule! "):].rstrip()[:-1]
    (HERE / "selected_rule.rkt").write_text(rule)
    canonical = canonical_pairs(TASK, root=ROOT, labeled_only=True)
    (HERE / "input.json").write_text(json.dumps(canonical[0]["input"]) + "\n")
    bridge = RacketBridge(timeout=15, startup_timeout=60)
    cases = []
    errors = []
    try:
        runtime = bridge.runtime_identity

        def check_case(grid, **identity):
            literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
            actual = bridge.eval_text(f"({wrapped} {literal})")
            if not isinstance(actual, list) or not all(isinstance(row, list) for row in actual):
                raise ValueError(f"Racket returned a nongrid: {actual!r}")
            rival = no_cleanup_rival(grid)
            errors = generator.self_check(grid, difficulty=identity.get("difficulty"))
            item = {
                **identity, "input_dimensions": [len(grid), len(grid[0])],
                "output_dimensions": [len(actual), len(actual[0])],
                "input": grid, "racket_output": actual, "rival_output": rival,
                "input_sha256": digest(grid), "racket_output_sha256": digest(actual),
                "rival_output_sha256": digest(rival), "self_check_errors": errors,
                "distractor_cells": foreign_cells(grid),
                "rival_equals_racket": rival == actual,
                "rival_disagreements": changed_cells(rival, actual),
            }
            cases.append(item)
            return item

        for pair in canonical:
            item = check_case(pair["input"], kind="canonical", variant=pair["variant"],
                              split=pair["split"], pair_index=pair["pair_index"])
            item["racket_equals_stored_label"] = item["racket_output"] == pair["output"]
        for difficulty in ("easy", None, "hard"):
            for seed in range(20):
                try:
                    grid = generator.generate(seed, 0, difficulty=difficulty)
                    check_case(grid, kind="generated", difficulty=difficulty,
                               seed=seed, sample_index=0, overrides={})
                except Exception as error:
                    errors.append({"kind": "generated", "difficulty": difficulty,
                                   "seed": seed, "sample_index": 0,
                                   "exception": type(error).__name__, "message": str(error)})
    finally:
        bridge.shutdown()
    if hashlib.sha256(source_path.read_bytes()).hexdigest() != generator_sha:
        raise ValueError("Audit generator changed during the probe")
    canonical_cases = [row for row in cases if row["kind"] == "canonical"]
    generated = [row for row in cases if row["kind"] == "generated"]
    metadata = {
        "task_id": TASK, "generator_sha256": generator_sha,
        "selected_rule_source_sha256": rule_sha,
        "selected_canonical_row_sha256": digest(selected[0]),
        "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "runtime": runtime,
        "command": {"cwd": "packet_root", "argv": ["bash", "-lc", COMMAND]},
        "payload_cwd": str(Path.cwd()), "payload_argv": [sys.executable, *sys.argv],
    }
    summary = {
        **metadata, "status": "completed", "finding_id": "A2-D53-1",
        "hypothesis": "The production domain cannot refute a rival that omits distractor erasure.",
        "canonical_cases": len(canonical_cases),
        "canonical_racket_label_passes": sum(row["racket_equals_stored_label"] for row in canonical_cases),
        "canonical_rival_refutations": sum(not row["rival_equals_racket"] for row in canonical_cases),
        "canonical_validator_rejections": sum(bool(row["self_check_errors"]) for row in canonical_cases),
        "generated_requested": 60, "generated_checked": len(generated),
        "generated_unique_inputs": len({row["input_sha256"] for row in generated}),
        "generated_self_check_passes": sum(not row["self_check_errors"] for row in generated),
        "generated_rival_agreements": sum(row["rival_equals_racket"] for row in generated),
        "generated_with_distractors": sum(bool(row["distractor_cells"]) for row in generated),
        "sample_policy": {"seeds": [0, 19], "sample_index": 0,
                          "difficulties": ["easy", None, "hard"], "overrides": {}},
        "errors": errors, "elapsed_seconds": round(time.monotonic() - started, 3),
        "limitations": "Finite 60-case census; static domain argument is separate. No general lesson-identifiability claim or query-rotation census.",
    }
    (HERE / "cases.json").write_text(json.dumps({**metadata, "cases": cases}, separators=(",", ":")) + "\n")
    witness = next(row for row in canonical_cases if not row["rival_equals_racket"])
    (HERE / "counterexample.json").write_text(json.dumps({
        **metadata, "finding_id": "A2-D53-1", "case": witness,
        "domain_statement": "This is canonical train data accepted by the selected Racket authority; it fails this generator's current self_check and is outside its emitted color domain."
    }, indent=2) + "\n")
    (HERE / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps({key: value for key, value in summary.items()
                      if key not in {"runtime", "payload_argv", "command"}}, indent=2))
    return 0 if not errors and all(row["racket_equals_stored_label"] for row in canonical_cases) else 1


if __name__ == "__main__":
    raise SystemExit(main())
