#!/usr/bin/env python3
"""Finite declared-rival lesson gate over supplied upstream Racket labels.

This scorer does not execute the reference rule or independently verify labels.
Keep the upstream arcpuzzles generate/apply receipt with its labeled inputs.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys

SCHEMA = "arcpuzzles-task-local-finite-lesson-gate-v1"


class LessonGateError(ValueError):
    """Malformed input, invalid declaration, or failed competitor execution."""


def digest(value):
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def _grid(grid, location):
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        raise LessonGateError(f"{location}: expected a nonempty list of nonempty rows")
    width = len(grid[0])
    if len(grid) > 30 or width > 30:
        raise LessonGateError(f"{location}: ARC dimensions exceed 30")
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        raise LessonGateError(f"{location}: ragged or malformed rows")
    if any(type(cell) is not int or not 0 <= cell <= 9 for row in grid for cell in row):
        raise LessonGateError(f"{location}: cells must be exact integer ARC colors 0..9")


def _expected_count(value, name):
    if value is not None and (type(value) is not int or value < 1):
        raise LessonGateError(f"{name} must be a positive exact integer when supplied")


def _validate_episode(episode, expected_demos, expected_queries):
    _expected_count(expected_demos, "expected_demos")
    _expected_count(expected_queries, "expected_queries")
    if not isinstance(episode, dict):
        raise LessonGateError("episode must be an object with train and test lists")
    seen = {}
    for split, expected in (("train", expected_demos), ("test", expected_queries)):
        pairs = episode.get(split)
        if not isinstance(pairs, list) or not pairs:
            raise LessonGateError(f"{split}: require at least one labeled pair")
        if expected is not None and len(pairs) != expected:
            raise LessonGateError(f"{split}: expected {expected} pairs, received {len(pairs)}")
        for index, pair in enumerate(pairs):
            location = f"{split}[{index}]"
            if not isinstance(pair, dict):
                raise LessonGateError(f"{location}: pair must be an object")
            for key in ("input", "output"):
                if key not in pair:
                    raise LessonGateError(f"{location}: missing {key}; upstream labels are required")
                _grid(pair[key], location + "." + key)
            key = digest(pair["input"])
            if key in seen:
                raise LessonGateError(f"duplicate input at {location}; first occurrence is {seen[key]}")
            seen[key] = location


def _competitors(declarations):
    if not isinstance(declarations, dict) or not declarations:
        raise LessonGateError("LESSON_COMPETITORS must be a nonempty dictionary")
    for name, solver in declarations.items():
        if not isinstance(name, str) or not name or not callable(solver):
            raise LessonGateError("each competitor must have a nonempty string name and callable solver")
    return sorted(declarations)


def _predict(name, solver, grid, location):
    protected = copy.deepcopy(grid)
    try:
        result = solver(protected)
    except Exception as exc:
        raise LessonGateError(f"competitor {name!r} failed at {location}: {type(exc).__name__}: {exc}") from exc
    if protected != grid:
        raise LessonGateError(f"competitor {name!r} mutated its input at {location}")
    _grid(result, f"competitor {name!r} result at {location}")
    return result


def score_episode(episode, competitors, *, expected_demos=None, expected_queries=None):
    """Pure finite-rival scoring; the caller supplies authoritative labels.

    First eliminate rivals using demonstrations only. Freeze the surviving
    names, then compare those rivals separately against each supplied query
    label. Query labels can affect per-query agreement, never demo survival.
    Inputs are copied before competitor execution; mutating rivals are errors.
    """
    _validate_episode(episode, expected_demos, expected_queries)
    names = _competitors(competitors)
    demos = episode["train"]
    demo_evidence = {}
    for name in names:
        refutations, predictions = [], []
        for index, pair in enumerate(demos):
            result = _predict(name, competitors[name], pair["input"], f"train[{index}]")
            predictions.append(digest(result))
            if result != pair["output"]:
                refutations.append(index)
        demo_evidence[name] = {"refuting_demo_indices": refutations,
                               "prediction_sha256": predictions}

    # Immutable phase boundary: no query answer has entered the filtering code.
    survivors = tuple(name for name in names if not demo_evidence[name]["refuting_demo_indices"])
    queries = []
    for index, pair in enumerate(episode["test"]):
        ambiguous, rival_rows = [], []
        for name in names:
            row = {"name": name, "survived_demonstrations": name in survivors,
                   "refuting_demo_indices": list(demo_evidence[name]["refuting_demo_indices"])}
            if name in survivors:
                prediction = _predict(name, competitors[name], pair["input"], f"test[{index}]")
                agrees = prediction == pair["output"]
                row.update(prediction_sha256=digest(prediction), agrees_with_supplied_label=agrees)
                if not agrees:
                    ambiguous.append(name)
            rival_rows.append(row)
        queries.append({"query_index": index, "input_sha256": digest(pair["input"]),
                        "supplied_label_sha256": digest(pair["output"]),
                        "ambiguous_rivals": ambiguous, "passed": not ambiguous,
                        "rivals": rival_rows})
    labeled = {split: [{key: p[key] for key in ("input", "output")} for p in episode[split]]
               for split in ("train", "test")}
    return {"passed": all(query["passed"] for query in queries),
            "demos": len(demos), "queries_count": len(queries), "rival_count": len(names),
            "labeled_pairs_sha256": digest(labeled),
            "demo_input_sha256": [digest(p["input"]) for p in demos],
            "demo_label_sha256": [digest(p["output"]) for p in demos],
            "demo_survivors": list(survivors), "demo_evidence": demo_evidence,
            "queries": queries, "labels_reexecuted": False,
            "scope": "finite LESSON_COMPETITORS teaching check against supplied upstream labels"}


def parse_episodes(text):
    """Read one episode, a nonempty JSON array, or one episode per JSONL row."""
    if not isinstance(text, str) or not text.strip():
        raise LessonGateError("input contains no episodes")
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        episodes = []
        for line_index, line in enumerate(text.splitlines(), 1):
            if not line.strip():
                continue
            try:
                episodes.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise LessonGateError(f"invalid JSONL at line {line_index}: {exc.msg}") from exc
    else:
        episodes = value if isinstance(value, list) else [value]
    if not episodes:
        raise LessonGateError("input contains no episodes")
    for index, episode in enumerate(episodes):
        if not isinstance(episode, dict) or "train" not in episode or "test" not in episode:
            raise LessonGateError(f"episode {index}: require an object with train and test")
    return episodes


def _file_record(path):
    path = Path(path)
    if not path.is_file():
        raise LessonGateError(f"missing regular evidence file: {path}")
    body = path.read_bytes()
    if not body:
        raise LessonGateError(f"empty evidence file: {path}")
    return {"path": str(path.resolve()), "sha256": hashlib.sha256(body).hexdigest(),
            "bytes": len(body)}, body


def _selected_generator(task_id):
    from reviewer_support import find_root, load_selected_generator
    root = find_root(__file__)
    return load_selected_generator(task_id, root=root)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", action="append", required=True,
                        help="labeled official episode JSON/JSONL; repeat for multiple files")
    parser.add_argument("--task-id", default="8b6a2892a064")
    parser.add_argument("--expect-demos", type=int)
    parser.add_argument("--expect-queries", type=int)
    parser.add_argument("--upstream-receipt", action="append", required=True,
                        help="retained arcpuzzles generate/apply receipt; hashed, not independently verified")
    parser.add_argument("--out", required=True, help="new private gate-result JSON path")
    args = parser.parse_args(argv)
    try:
        output = Path(args.out)
        if output.exists():
            raise LessonGateError("--out must be a new path")
        _expected_count(args.expect_demos, "--expect-demos")
        _expected_count(args.expect_queries, "--expect-queries")
        receipts = [_file_record(path)[0] for path in args.upstream_receipt]
        module, source_path, source_hash = _selected_generator(args.task_id)
        rivals = getattr(module, "LESSON_COMPETITORS", None)
        _competitors(rivals)
        inputs, scores = [], []
        for filename in args.input:
            file_record, body = _file_record(filename)
            try:
                episodes = parse_episodes(body.decode("utf-8"))
            except UnicodeDecodeError as exc:
                raise LessonGateError(f"input is not UTF-8: {filename}") from exc
            file_record["episodes"] = len(episodes)
            inputs.append(file_record)
            for index, episode in enumerate(episodes):
                if "task_id" in episode and episode["task_id"] != args.task_id:
                    raise LessonGateError(f"{filename} episode {index}: task_id does not match selected source")
                try:
                    score = score_episode(episode, rivals, expected_demos=args.expect_demos,
                                          expected_queries=args.expect_queries)
                except LessonGateError as exc:
                    raise LessonGateError(f"{filename} episode {index}: {exc}") from exc
                score.update(input_file_sha256=file_record["sha256"], episode_index_in_file=index)
                scores.append(score)
        passed = all(score["passed"] for score in scores)
        report = {"schema": SCHEMA, "status": "pass" if passed else "ambiguous", "passed": passed,
                  "task_id": args.task_id, "generator_source": str(Path(source_path).resolve()),
                  "generator_source_sha256": source_hash, "generator_version": getattr(module, "VERSION", None),
                  "gate_source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  "declared_competitors": sorted(rivals), "inputs": inputs,
                  "upstream_receipts": receipts, "episodes": scores,
                  "expected_demos": args.expect_demos, "expected_queries": args.expect_queries,
                  "command": [sys.executable, __file__, *(sys.argv[1:] if argv is None else argv)],
                  "labels_reexecuted": False, "upstream_receipt_contents_verified": False,
                  "limitation": "Finite rival elimination only; retain the supplied upstream Racket labeling receipts."}
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("x", encoding="utf-8") as handle:
            json.dump(report, handle, indent=2)
            handle.write("\n")
        print(json.dumps({"status": report["status"], "passed": passed, "episodes": len(scores),
                          "queries": sum(s["queries_count"] for s in scores), "out": str(output),
                          "labels_reexecuted": False}))
        return 0 if passed else 1
    except (LessonGateError, OSError, ImportError, ValueError) as exc:
        print(json.dumps({"status": "error", "error": type(exc).__name__, "message": str(exc),
                          "labels_reexecuted": False}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
