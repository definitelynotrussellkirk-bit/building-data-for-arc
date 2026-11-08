"""Check transform-map teaching in an ARC-style saved lesson, without Racket.

Run through the packet wrapper or with shared/runtime on PYTHONPATH. This reads
demonstration labels and query inputs; it never reads query labels or executes
the reference. Supplied demonstration labels are not independently certified.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys


def _generator():
    for ancestor in Path(__file__).resolve().parents:
        for runtime in (ancestor, ancestor / "shared/runtime"):
            if (runtime / "reviewer_support.py").is_file():
                sys.path.insert(0, str(runtime))
                break
        else:
            continue
        break
    from reviewer_support import find_root
    root = find_root(__file__)
    for path in (root / "generators/2f58238f8bb6/generator.py",
                 root / "puzzle_generators/per_puzzle/2f58238f8bb6/generator.py"):
        if path.is_file():
            spec = importlib.util.spec_from_file_location("key_strip_lesson_check", path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module, hashlib.sha256(path.read_bytes()).hexdigest()
    raise FileNotFoundError("Cannot find this task's local generator")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("lesson", type=Path, help="JSON with train pairs and test query inputs")
    parser.add_argument("--out", type=Path, help="optional new JSON report path")
    args = parser.parse_args(argv)
    try:
        raw = args.lesson.read_bytes()
        lesson = json.loads(raw)
        demos, queries = lesson["train"], lesson["test"]
        if not isinstance(demos, list) or not isinstance(queries, list) or not demos or not queries:
            raise ValueError("train and test must be nonempty lists")
        # Deliberately reconstruct query dictionaries using only known inputs.
        query_inputs = [{"input": query["input"]} for query in queries]
        generator, source_hash = _generator()
        for index, pair in enumerate(demos + query_inputs):
            reasons = generator.self_check(pair["input"])
            if reasons:
                raise ValueError(f"input {index} violates the task grammar: {'; '.join(reasons)}")
        for index, demo in enumerate(demos):
            label = demo["output"]
            if (not isinstance(label, list) or not 1 <= len(label) <= 30
                    or not isinstance(label[0], list) or not 1 <= len(label[0]) <= 30
                    or any(not isinstance(row, list) or len(row) != len(label[0]) for row in label)
                    or any(type(value) is not int or not 0 <= value <= 9 for row in label for value in row)):
                raise ValueError(f"demonstration output {index} must be an integer ARC grid")
        results = [{"query_index": i, "reasons": generator.lesson_identifiable(demos, query)}
                   for i, query in enumerate(query_inputs)]
        problems = sum(bool(result["reasons"]) for result in results)
        report = {
            "schema": "arcpuzzles-key-map-teaching-check-v1",
            "task_id": generator.TASK_ID,
            "generator_sha256": source_hash,
            "lesson_file_sha256": hashlib.sha256(raw).hexdigest(),
            "status": "needs_teaching" if problems else "query_maps_determined",
            "demonstrations": len(demos), "queries": results,
            "query_labels_consulted": False,
            "demonstration_labels_independently_verified": False,
            "scope": "eight D4 transforms per key; assumes cell-wise keys and a top-aligned single-gap gallery",
            "training_admitted": False,
        }
        text = json.dumps(report, indent=2) + "\n"
        if args.out:
            args.out.parent.mkdir(parents=True, exist_ok=True)
            with args.out.open("x") as handle:
                handle.write(text)
        print(text, end="")
        return 1 if problems else 0
    except (OSError, KeyError, TypeError, ValueError) as exc:
        print(json.dumps({"status": "error", "message": str(exc)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
