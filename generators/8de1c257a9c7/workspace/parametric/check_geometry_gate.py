"""Opt-in demonstration gate for source-relative template transplantation.

A passing contrast holds dimensions, green position, all red positions and
cyan count fixed while changing cyan geometry and the answer. No deterministic
rule depending only on those held-fixed features can fit both demonstrations.
This is a sufficient teaching witness for that narrow shortcut class, not a
necessary condition for every useful lesson or a reference-label verifier.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
SCHEMA = "stamp-geometry-observability-v1"
FALSE_POSITIVE = (
    "A legitimate finite-bank family, a symmetric or single-template lesson, "
    "or a good varied lesson without exact matching nuisance features may fail. "
    "Enable this gate only when arbitrary source geometry is the intended skill."
)


def _hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _grid(value, allowed):
    if type(value) is not list or not 1 <= len(value) <= 30:
        raise ValueError("Grid must have 1..30 list rows")
    if type(value[0]) is not list or not 1 <= len(value[0]) <= 30:
        raise ValueError("Grid must have 1..30 columns")
    width = len(value[0])
    if any(type(row) is not list or len(row) != width or any(
        type(cell) is not int or cell not in allowed for cell in row
    ) for row in value):
        raise ValueError("Grid must be rectangular with exact integer role colors")
    return value


def _observation(pair, index):
    if type(pair) is not dict or "input" not in pair or "output" not in pair:
        raise ValueError("Demonstrations require input and output")
    grid = _grid(pair["input"], {0, 2, 3, 8})
    output = _grid(pair["output"], {0, 8})
    h, w = len(grid), len(grid[0])
    if (len(output), len(output[0])) != (h, w):
        raise ValueError("Transplantation must preserve canvas dimensions")
    positions = {color: tuple((r, c) for r, row in enumerate(grid)
                 for c, value in enumerate(row) if value == color) for color in (2, 3, 8)}
    if len(positions[3]) != 1 or not positions[2] or not positions[8]:
        raise ValueError("Expected one green anchor, cyan geometry and red destination(s)")
    green = positions[3][0]
    offsets = tuple((r - green[0], c - green[1]) for r, c in positions[8])
    signature = (h, w, green, positions[2], len(positions[8]))
    return {"index": index, "signature": signature, "offsets": offsets,
            "input_sha256": _hash(grid), "output_sha256": _hash(output)}


def check_episode(episode):
    """Inspect train only; neither query labels nor private metadata affect fit."""
    if type(episode) is not dict or type(episode.get("train")) is not list or not episode["train"]:
        raise ValueError("Episode must contain nonempty labeled demonstrations")
    groups = defaultdict(list)
    observations = [_observation(pair, i) for i, pair in enumerate(episode["train"])]
    for row in observations:
        groups[row["signature"]].append(row)
    witnesses = []
    for signature, rows in groups.items():
        h, w, green, reds, count = signature
        for i, a in enumerate(rows):
            for b in rows[i + 1:]:
                if a["offsets"] == b["offsets"] or a["output_sha256"] == b["output_sha256"]:
                    continue
                witnesses.append({
                    "demo_indices": [a["index"], b["index"]],
                    "blind_features": {"shape": [h, w], "green": list(green),
                                       "reds": [list(p) for p in reds], "cyan_count": count},
                    "input_sha256": [a["input_sha256"], b["input_sha256"]],
                    "offsets_sha256": [_hash(a["offsets"]), _hash(b["offsets"])],
                    "output_sha256": [a["output_sha256"], b["output_sha256"]],
                })
    return {
        "schema": SCHEMA,
        "status": "passed" if witnesses else "missing_geometry_contrast",
        "demonstrations": len(observations),
        "distinct_source_geometries": len({row["offsets"] for row in observations}),
        "witnesses": witnesses,
        "fit_scope": "demonstrations_only",
        "reference_labels_reexecuted": False,
        "claim": "A retained witness refutes rules using only dimensions, green/red coordinates and cyan count.",
        "possible_false_positive": FALSE_POSITIVE,
        "limits": "Uses supplied labels; verify them separately through the reference runtime. No unrestricted uniqueness or measured training benefit is implied.",
    }


def _episodes(path):
    raw = path.read_text()
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        value = [json.loads(line) for line in raw.splitlines() if line.strip()]
    if type(value) is dict and "episodes" in value:
        value = value["episodes"]
    elif type(value) is dict and "train" in value:
        value = [value]
    if type(value) is not list or not value:
        raise ValueError("Expected an episode, episode list, episodes report, or episode JSONL")
    # Native export metadata wraps each complete private episode in `episode`.
    return [row["episode"] if type(row) is dict and type(row.get("episode")) is dict else row
            for row in value]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--require-contrast", action="store_true")
    args = parser.parse_args(argv)
    reports = [check_episode(row) for row in _episodes(args.source)]
    passed = all(row["status"] == "passed" for row in reports)
    report = {
        "schema": SCHEMA, "status": "passed" if passed else "missing_geometry_contrast",
        "source_sha256": hashlib.sha256(args.source.read_bytes()).hexdigest(),
        "checker_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "episodes": reports, "episodes_passed": sum(row["status"] == "passed" for row in reports),
        "reference_labels_reexecuted": False,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x") as stream:
        json.dump(report, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print(json.dumps({"status": report["status"], "episodes": len(reports),
                      "episodes_passed": report["episodes_passed"]}))
    return int(args.require_contrast and not passed)


if __name__ == "__main__":
    raise SystemExit(main())
