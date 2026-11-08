#!/usr/bin/env python3
"""Infer a transform legend from visible timelines and detect query ambiguity.

Standalone standard-library tool. It reads train inputs/outputs and test inputs
only: no generator, Racket rule, canonical ledger, or test output is consulted.
Scope: a row-0 script, one cropped body, cumulative D4 transforms, and a
top-aligned gallery with one blank separator column. Other grammars are not
certified. Exit 0=finite-family identifiable, 1=ambiguous, 2=incomplete/invalid.
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
from pathlib import Path


OPERATIONS = ("identity", "cw90", "half_turn", "ccw90", "flip_lr", "flip_ud",
              "transpose", "anti_transpose")


def checked_grid(value):
    if not isinstance(value, list) or not value or not isinstance(value[0], list) or not value[0]:
        raise ValueError("expected a nonempty integer grid")
    width = len(value[0])
    if any(not isinstance(row, list) or len(row) != width for row in value):
        raise ValueError("ragged grid")
    if any(type(cell) is not int or not 0 <= cell <= 9 for row in value for cell in row):
        raise ValueError("grid cells must be integer colors 0..9")
    return value


def crop(grid):
    cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value]
    if not cells:
        raise ValueError("empty template or gallery frame")
    top, bottom = min(r for r, _ in cells), max(r for r, _ in cells)
    left, right = min(c for _, c in cells), max(c for _, c in cells)
    return [row[left:right + 1] for row in grid[top:bottom + 1]]


def transform(grid, operation):
    height, width = len(grid), len(grid[0])
    if operation == "identity":
        return [row[:] for row in grid]
    if operation == "cw90":
        return [[grid[height - 1 - c][r] for c in range(height)] for r in range(width)]
    if operation == "half_turn":
        return [[grid[height - 1 - r][width - 1 - c] for c in range(width)] for r in range(height)]
    if operation == "ccw90":
        return [[grid[c][width - 1 - r] for c in range(height)] for r in range(width)]
    if operation == "flip_lr":
        return [[grid[r][width - 1 - c] for c in range(width)] for r in range(height)]
    if operation == "flip_ud":
        return [[grid[height - 1 - r][c] for c in range(width)] for r in range(height)]
    if operation == "transpose":
        return [[grid[c][r] for c in range(height)] for r in range(width)]
    if operation == "anti_transpose":
        return [[grid[height - 1 - c][width - 1 - r] for c in range(height)] for r in range(width)]
    raise ValueError(f"unknown operation {operation}")


def input_parts(grid):
    checked_grid(grid)
    script = [str(value) for value in grid[0] if value]
    if not script:
        raise ValueError("input has no script")
    return script, crop(grid[1:])


def gallery_frames(grid):
    checked_grid(grid)
    occupied = [any(row[c] for row in grid) for c in range(len(grid[0]))]
    if not occupied[0] or not occupied[-1]:
        raise ValueError("gallery has a leading/trailing blank column")
    groups, start = [], 0
    for c, present in enumerate(occupied):
        if not present:
            if c == start:
                raise ValueError("gallery separator is wider than one column")
            groups.append((start, c))
            start = c + 1
    groups.append((start, len(occupied)))
    frames = []
    for left, right in groups:
        frame = [row[left:right] for row in grid]
        if not any(frame[0]):
            raise ValueError("gallery frame is not top-aligned")
        frames.append(crop(frame))
    return frames


def execute(grid, mapping):
    script, current = input_parts(grid)
    states = []
    for code in script:
        current = transform(current, mapping[code])
        states.append(current)
    height = max(map(len, states))
    width = sum(len(state[0]) for state in states) + len(states) - 1
    output = [[0] * width for _ in range(height)]
    offset = 0
    for state in states:
        for r, row in enumerate(state):
            output[r][offset:offset + len(row)] = row
        offset += len(state[0]) + 1
    return output


def query_predictions(grid, candidates, max_mappings):
    script, _ = input_parts(grid)
    codes = sorted(set(script))
    options = [candidates.get(code, list(OPERATIONS)) for code in codes]
    total = math.prod(map(len, options))
    examined, predictions, seen = 0, [], set()
    for choices in itertools.islice(itertools.product(*options), max_mappings):
        mapping = dict(zip(codes, choices))
        output = execute(grid, mapping)
        examined += 1
        key = tuple(map(tuple, output))
        if key not in seen:
            seen.add(key)
            predictions.append({"mapping": mapping, "output": output})
            if len(predictions) == 2:
                break
    status = ("ambiguous" if len(predictions) >= 2 else
              "identifiable" if examined == total else "incomplete")
    return {"status": status, "mapping_space_size": total,
            "mappings_examined": examined, "predictions": predictions}


def analyze(task, *, max_mappings=4096):
    report = {"schema": "transform-legend-probe-v1", "status": "inconsistent",
              "scope": "cumulative D4 symbol mappings with visible intermediate frames",
              "query_outputs_consulted": False, "candidates": {}, "queries": [],
              "observations": [], "errors": []}
    try:
        if type(max_mappings) is not int or max_mappings < 1:
            raise ValueError("max_mappings must be a positive integer")
        if (not isinstance(task, dict) or not isinstance(task.get("train"), list)
                or not task["train"] or not isinstance(task.get("test"), list)):
            raise ValueError("expected nonempty train and a test list")
        candidates = {}
        for index, pair in enumerate(task["train"]):
            if not isinstance(pair, dict):
                raise ValueError("train pair must be an object")
            script, previous = input_parts(pair.get("input"))
            frames = gallery_frames(pair.get("output"))
            if len(script) != len(frames):
                raise ValueError(f"demo {index}: script/frame count mismatch")
            for step, (code, frame) in enumerate(zip(script, frames)):
                fits = [op for op in OPERATIONS if transform(previous, op) == frame]
                candidates[code] = [op for op in candidates.get(code, OPERATIONS) if op in fits]
                report["observations"].append({"demo": index, "step": step,
                                               "code": code, "matching_operations": fits})
                previous = frame
        report["candidates"] = candidates
        if any(not options for options in candidates.values()):
            raise ValueError("visible transitions contradict every consistent D4 legend")
        for pair in task["test"]:
            if not isinstance(pair, dict):
                raise ValueError("test pair must be an object")
            # Deliberately do not access pair['output'], even when present.
            report["queries"].append(query_predictions(pair.get("input"), candidates, max_mappings))
        if not report["queries"]:
            raise ValueError("no query inputs supplied")
        statuses = {row["status"] for row in report["queries"]}
        report["status"] = ("ambiguous" if "ambiguous" in statuses else
                            "incomplete" if "incomplete" in statuses else "identifiable")
    except ValueError as exc:
        report["errors"].append(str(exc))
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--challenge", type=Path, required=True)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--max-mappings", type=int, default=4096)
    args = parser.parse_args(argv)
    if args.out is not None and args.out.exists():
        parser.error("output already exists; choose a fresh evidence path")
    source = args.challenge.read_bytes()
    result = analyze(json.loads(source), max_mappings=args.max_mappings)
    result["challenge_sha256"] = hashlib.sha256(source).hexdigest()
    result["tool_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    payload = json.dumps(result, indent=2) + "\n"
    if args.out is not None:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(payload, encoding="utf-8")
        print(json.dumps({"status": result["status"], "out": str(args.out),
                          "queries": len(result["queries"]), "errors": result["errors"]}))
    else:
        print(payload, end="")
    return {"identifiable": 0, "ambiguous": 1}.get(result["status"], 2)


if __name__ == "__main__":
    raise SystemExit(main())
