"""Replay the retained old three-demo lesson with actual canonical Racket.

Uses stored inputs, never generate(seed, index). The current five-demo schedule
is outside this replay's scope. Supply a new --out path for each execution.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import inspect
import json
from pathlib import Path
import sys
import tempfile

from coverage_probe import reference_batch, reviewer_helpers, selected_generator

TASK_ID = "a61246736c26"
DEFAULT_LESSON = (Path(__file__).resolve().parents[1] / "counterexamples/current-review"
                  / "retained-conditional-lesson.json")


def replay(path, expected_generator_sha256=None):
    body = path.read_bytes()
    lesson = json.loads(body)
    if (lesson.get("schema") != "a61246736c26-retained-conditional-lesson-v1"
            or lesson.get("task_id") != TASK_ID):
        raise ValueError("Expected this task's retained conditional-lesson schema")
    pairs = lesson["pairs"]
    if (lesson["demonstrations"] != 3 or lesson["queries"] != 1
            or [pair["role"] for pair in pairs] != ["demonstration"] * 3 + ["query"]):
        raise ValueError("This replay requires the retained three-demo, one-query lesson")
    helpers = reviewer_helpers()
    root = helpers.find_root(__file__)
    generator, source, current_sha256 = selected_generator()
    if expected_generator_sha256 and current_sha256 != expected_generator_sha256:
        raise ValueError("Selected generator differs from --expected-generator-sha256")
    if generator.RULE_HASH != lesson["canonical_rule"]["normalized_hash"]:
        raise ValueError("Current declared canonical rule differs from the retained lesson")
    rival_name = lesson["rival"]["current_declaration"]
    rival = generator.SEMANTIC_RIVALS[rival_name]
    if not callable(rival):
        raise ValueError(f"Current declared rival is not callable: {rival_name}")
    inputs = [helpers.normalize_grid(pair["input_rows"]) for pair in pairs]
    retained_outputs = [helpers.normalize_grid(pair["canonical_output_rows"]) for pair in pairs]
    retained_rivals = [helpers.normalize_grid(pair["retained_rival_output_rows"]) for pair in pairs]
    outputs, reference = reference_batch(inputs, root=root, declared_rule_hash=generator.RULE_HASH)
    if reference["rule_source_sha256"] != lesson["canonical_rule"]["source_sha256"]:
        raise ValueError("Executed canonical source bytes differ from the retained lesson")
    predicted = [helpers.normalize_grid(rival(deepcopy(grid))) for grid in inputs]
    records = []
    for index, (pair, actual, expected, prediction, old_rival) in enumerate(
            zip(pairs, outputs, retained_outputs, predicted, retained_rivals, strict=True)):
        if len(actual) != len(prediction) or any(len(a) != len(b) for a, b in zip(actual, prediction)):
            raise ValueError(f"Current rival changed output shape on retained pair {index}")
        errors = sum(a != b for row_a, row_b in zip(actual, prediction)
                     for a, b in zip(row_a, row_b))
        records.append({"pair_index": index, "role": pair["role"],
                        "canonical_matches_retained": actual == expected,
                        "rival_matches_retained": prediction == old_rival,
                        "rival_cell_errors": errors})
    if hashlib.sha256(source.read_bytes()).hexdigest() != current_sha256:
        raise ValueError("Generator source changed during replay")
    label_matches = sum(record["canonical_matches_retained"] for record in records)
    demo_fit = sum(record["rival_cell_errors"] == 0 for record in records[:3])
    query_errors = records[3]["rival_cell_errors"]
    reproduced = (label_matches == lesson["expected_replay"]["canonical_label_matches"] == 4
                  and demo_fit == lesson["expected_replay"]["demonstration_fit"] == 3
                  and query_errors == lesson["expected_replay"]["query_cell_errors"] == 80
                  and all(record["rival_matches_retained"] for record in records))
    return {"schema": "a61246736c26-retained-lesson-replay-v1", "task_id": TASK_ID,
            "status": "reproduced_teaching_failure" if reproduced else "not_reproduced",
            "current_generator_sha256": current_sha256,
            "current_generator_version": generator.VERSION,
            "current_examples_needed": getattr(generator, "EXAMPLES_NEEDED", None),
            "retained_generator_sha256": lesson["origin"]["generator_sha256"],
            "retained_lesson": str(path.resolve()),
            "retained_lesson_sha256": hashlib.sha256(body).hexdigest(),
            "parent_evidence": lesson["parent_evidence"], "reference": reference,
            "rival": rival_name,
            "rival_callable_sha256": hashlib.sha256(inspect.getsource(rival).encode()).hexdigest(),
            "canonical_label_matches": {"matches": label_matches, "total": 4},
            "demonstration_fit": {"matches": demo_fit, "total": 3},
            "query_cell_errors": query_errors, "pairs": records,
            "input_source": "retained grids; no generation", "scope": lesson["scope"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lesson", type=Path, default=DEFAULT_LESSON)
    parser.add_argument("--expected-generator-sha256")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        parser.error(f"Output already exists: {args.out}")
    try:
        report = replay(args.lesson, args.expected_generator_sha256)
    except Exception as exc:
        report = {"schema": "a61246736c26-retained-lesson-replay-v1", "task_id": TASK_ID,
                  "status": "error", "exception": f"{type(exc).__name__}: {exc}"}
    report.update({"command": [sys.executable, *sys.argv], "cwd": str(Path.cwd()),
                   "replay_script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                   "exit_code": 0 if report["status"] == "reproduced_teaching_failure" else 1})
    args.out.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile("w", dir=args.out.parent, prefix="lesson-replay-",
                                         suffix=".tmp", encoding="utf-8", delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(json.dumps(report, indent=2, sort_keys=True) + "\n")
        if args.out.exists():
            raise FileExistsError(args.out)
        temporary.replace(args.out)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    print(json.dumps({"status": report["status"], "canonical_label_matches": report.get("canonical_label_matches"),
                      "demonstration_fit": report.get("demonstration_fit"),
                      "query_cell_errors": report.get("query_cell_errors"), "report": str(args.out),
                      "sha256": hashlib.sha256(args.out.read_bytes()).hexdigest()}))
    return report["exit_code"]


if __name__ == "__main__":
    raise SystemExit(main())
