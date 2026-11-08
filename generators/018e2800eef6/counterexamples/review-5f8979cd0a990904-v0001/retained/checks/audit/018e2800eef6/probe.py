#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3] / "repo"


def _find_frames(grid):
    h, w = len(grid), len(grid[0])
    frames = []
    for r0 in range(h - 2):
        for c0 in range(w - 2):
            for r1 in range(r0 + 2, h):
                for c1 in range(c0 + 2, w):
                    border = (
                        [(r0, c) for c in range(c0, c1 + 1)]
                        + [(r1, c) for c in range(c0, c1 + 1)]
                        + [(r, c0) for r in range(r0 + 1, r1)]
                        + [(r, c1) for r in range(r0 + 1, r1)]
                    )
                    colors = {grid[r][c] for r, c in border}
                    if len(colors) != 1 or next(iter(colors)) not in (6, 7):
                        continue
                    color = next(iter(colors))
                    interior = [(r, c) for r in range(r0 + 1, r1) for c in range(c0 + 1, c1)]
                    if all(grid[r][c] != color for r, c in interior):
                        frames.append((r0, c0, r1, c1, color, interior))
    maximal = []
    for frame in frames:
        r0, c0, r1, c1, *_ = frame
        if not any(
            or0 <= r0 and oc0 <= c0 and or1 >= r1 and oc1 >= c1
            and (or0, oc0, or1, oc1) != (r0, c0, r1, c1)
            for or0, oc0, or1, oc1, *_ in frames
        ):
            maximal.append(frame)
    if len(maximal) != 2:
        raise AssertionError(f"expected two frames, got {len(maximal)}")
    return maximal


def _key(grid):
    for row in grid:
        for value in row:
            if value in (1, 2, 3):
                return value
    return 0


def _flip_lr(grid):
    return [row[::-1] for row in grid]


def _flip_ud(grid):
    return grid[::-1]


def _rot180(grid):
    return [row[::-1] for row in grid[::-1]]


def solve_with_mapping(grid, *, key2_identity: bool):
    frames = _find_frames(grid)

    def patterned(frame):
        *_, color, interior = frame
        return any(grid[r][c] != 0 and grid[r][c] != color for r, c in interior)

    srcs = [frame for frame in frames if patterned(frame)]
    tgts = [frame for frame in frames if not patterned(frame)]
    if len(srcs) != 1 or len(tgts) != 1:
        raise AssertionError(f"source/target ambiguity: {len(srcs)=}, {len(tgts)=}")
    src, tgt = srcs[0], tgts[0]
    sr0, sc0, sr1, sc1, _, _ = src
    motif = [
        [0 if grid[r][c] in (6, 7) else grid[r][c] for c in range(sc0 + 1, sc1)]
        for r in range(sr0 + 1, sr1)
    ]
    key = _key(grid)
    if key == 1:
        transformed = _flip_lr(motif)
    elif key == 2 and not key2_identity:
        transformed = _flip_ud(motif)
    elif key == 3:
        transformed = _rot180(motif)
    else:
        transformed = [row[:] for row in motif]

    out = [[0 for _ in row] for row in grid]
    for r0, c0, r1, c1, color, _ in frames:
        for c in range(c0, c1 + 1):
            out[r0][c] = color
            out[r1][c] = color
        for r in range(r0 + 1, r1):
            out[r][c0] = color
            out[r][c1] = color

    tr0, tc0, *_ = tgt
    for r, row in enumerate(transformed):
        for c, value in enumerate(row):
            if value:
                out[tr0 + 1 + r][tc0 + 1 + c] = value
    return out


def main():
    inputs = json.loads((HERE / "input.json").read_text())["inputs"]
    generation = json.loads((HERE / "generation.json").read_text())
    receipt = json.loads((HERE / "racket.json").read_text())
    outputs = [row["output"] for row in receipt["results"]]
    assert all(row["error"] is None for row in receipt["results"])
    assert receipt["rule_hash_matches_catalog"] is True
    assert receipt["generator_sha256"] == generation["generator_sha256"]

    intended_python = [solve_with_mapping(grid, key2_identity=False) for grid in inputs]
    rival = [solve_with_mapping(grid, key2_identity=True) for grid in inputs]
    assert intended_python == outputs
    assert rival[:4] == outputs[:4]
    assert rival[4] != outputs[4]

    result = {
        "schema": "arcpuzzles-audit-counterexample-v1",
        "task_id": "018e2800eef6",
        "classification": "generated lesson ambiguity",
        "generator_sha256": generation["generator_sha256"],
        "executed_rule_hash": receipt["executed_rule_hash"],
        "rule_hash_matches_catalog": receipt["rule_hash_matches_catalog"],
        "seed": 4,
        "demo_sample_indices": [0, 1, 2, 3],
        "query_sample_index": 4,
        "keys": generation["keys"],
        "rival": "key 1 = flip-lr; key 2 = identity; key 3 = rotate-180; no key = identity",
        "demos": [
            {
                "sample_index": i,
                "key": generation["keys"][i],
                "input": inputs[i],
                "authority_output": outputs[i],
                "rival_output": rival[i],
                "rival_matches": rival[i] == outputs[i],
            }
            for i in range(4)
        ],
        "query": {
            "sample_index": 4,
            "key": generation["keys"][4],
            "input": inputs[4],
            "authority_output": outputs[4],
            "rival_output": rival[4],
            "rival_matches": False,
        },
        "conclusion": (
            "The exact four-example default lesson omits key 2. The rival therefore "
            "fits all demonstrations but gives a different answer on the next default "
            "generated key-2 query. EXAMPLES_NEEDED=4 is not backed by a schedule or "
            "lesson_identifiable contract that guarantees all key meanings."
        ),
        "evidence_sha256": {
            name: hashlib.sha256((HERE / name).read_bytes()).hexdigest()
            for name in ("input.json", "generation.json", "racket.json")
        },
    }
    (HERE / "counterexample.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "demos_fit": sum(x["rival_matches"] for x in result["demos"]),
        "demos_total": len(result["demos"]),
        "query_disagrees": not result["query"]["rival_matches"],
        "keys": result["keys"],
    }, indent=2))


if __name__ == "__main__":
    main()
