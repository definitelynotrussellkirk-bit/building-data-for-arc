"""Detect demonstration copying under a bijective ARC color substitution.

Standard library only. Reads a native lesson or list; never executes a solver,
looks up references, or decides whether data should be admitted or rejected.
"""
import argparse
import json
from pathlib import Path
import sys


def validate_grid(grid, location):
    if (not isinstance(grid, list) or not grid
            or any(not isinstance(row, list) or not row for row in grid)
            or len({len(row) for row in grid}) != 1
            or any(type(value) is not int or not 0 <= value <= 9
                   for row in grid for value in row)):
        raise ValueError(f"{location}: expected nonempty rectangular integer ARC grid (0..9)")


def color_substitution(source, query):
    if len(source) != len(query) or len(source[0]) != len(query[0]):
        return None
    forward, reverse = {0: 0}, {0: 0}
    for row_a, row_b in zip(source, query):
        for a, b in zip(row_a, row_b):
            if (a in forward and forward[a] != b) or (b in reverse and reverse[b] != a):
                return None
            forward[a], reverse[b] = b, a
    return forward


def diagnose(value):
    lessons = value if isinstance(value, list) else [value]
    if not lessons:
        raise ValueError("expected at least one native ARC lesson")
    report = {
        "schema": "arc-demo-copy-diagnostic-v1",
        "admission_decision": None,
        "caution": ("Diagnostic only: identity tasks and legitimate recoloring may match. "
                    "A match or agreement does not establish a defect; no match does not "
                    "establish generalization or exclude other shortcuts."),
        "lessons": [],
    }
    for lesson_index, lesson in enumerate(lessons):
        if not isinstance(lesson, dict):
            raise ValueError(f"lesson {lesson_index}: expected an object")
        for split in ("train", "test"):
            pairs = lesson.get(split)
            if not isinstance(pairs, list) or not pairs:
                raise ValueError(f"lesson {lesson_index}.{split}: expected nonempty pair list")
            for index, pair in enumerate(pairs):
                location = f"lesson {lesson_index}.{split}[{index}]"
                if not isinstance(pair, dict):
                    raise ValueError(f"{location}: expected a pair object")
                validate_grid(pair.get("input"), location + ".input")
                if split == "train" or "output" in pair:
                    validate_grid(pair.get("output"), location + ".output")
        row = {"lesson_index": lesson_index, "queries": []}
        for query_index, query in enumerate(lesson["test"]):
            labeled = "output" in query
            result = {"query_index": query_index,
                      "label_status": "labeled" if labeled else "unscored", "matches": []}
            for demo_index, demo in enumerate(lesson["train"]):
                mapping = color_substitution(demo["input"], query["input"])
                if mapping is None:
                    continue
                unknown = sorted({v for r in demo["output"] for v in r} - mapping.keys())
                prediction = (None if unknown else
                              [[mapping[v] for v in r] for r in demo["output"]])
                result["matches"].append({
                    "demo_index": demo_index,
                    "color_map": {str(k): v for k, v in sorted(mapping.items())},
                    "prediction_status": "unmapped_output_colors" if unknown else "predicted",
                    "unmapped_output_colors": unknown, "prediction": prediction,
                    "agrees_with_query_label": (prediction == query["output"]
                                                if labeled and prediction is not None else None),
                })
            result["input_match_count"] = len(result["matches"])
            result["prediction_count"] = sum(m["prediction"] is not None for m in result["matches"])
            result["actual_agreement_count"] = (sum(m["agrees_with_query_label"] is True
                                                    for m in result["matches"])
                                                 if labeled else None)
            row["queries"].append(result)
        report["lessons"].append(row)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", nargs="?", default="-", help="native JSON path, or - for stdin")
    parser.add_argument("--out", type=Path, help="optional new JSON output path")
    args = parser.parse_args()
    try:
        body = sys.stdin.read() if args.input == "-" else Path(args.input).read_text()
        report = diagnose(json.loads(body))
        code = 0
    except (ValueError, OSError) as error:
        report, code = {"schema": "arc-demo-copy-diagnostic-v1", "error": str(error)}, 2
    output = json.dumps(report, indent=2) + "\n"
    if args.out is None:
        sys.stdout.write(output)
    else:
        try:
            with args.out.open("x") as handle:
                handle.write(output)
        except OSError as error:
            sys.stdout.write(json.dumps({"error": str(error)}) + "\n")
            return 2
    return code


if __name__ == "__main__":
    sys.exit(main())
