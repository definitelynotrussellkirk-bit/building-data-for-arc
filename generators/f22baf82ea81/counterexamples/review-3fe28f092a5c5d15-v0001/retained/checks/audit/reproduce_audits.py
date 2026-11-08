#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from reviewer_support import canonical_pairs, find_root, load_selected_generator


HERE = Path(__file__).resolve().parent
ROOT = Path.cwd().resolve()
if not (ROOT / "generators").is_dir():
    raise SystemExit("run from the packet repo directory")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def nonzero_bbox(grid):
    cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value]
    return min(r for r, _ in cells), max(r for r, _ in cells), min(c for _, c in cells), max(c for _, c in cells)


def audit_a778() -> None:
    task = "a77893c9c05c"
    gen, path, source_sha = load_selected_generator(task, root=ROOT)
    canonical = canonical_pairs(task, root=ROOT)
    rejected = []
    thin_frames = []
    for index, pair in enumerate(canonical):
        findings = gen.self_check(pair["input"])
        if findings:
            rejected.append({
                "index": index,
                "split": pair.get("split"),
                "pair_index": pair.get("pair_index"),
                "findings": findings,
            })
        for _color, cells in gen._components(pair["input"]):
            if gen._rect_frame(cells):
                rows = [r for r, _ in cells]
                cols = [c for _, c in cells]
                dims = [max(rows) - min(rows) + 1, max(cols) - min(cols) + 1]
                if min(dims) == 3:
                    thin_frames.append({"canonical_index": index, "dims": dims})
    if not rejected:
        raise AssertionError("expected at least one canonical self_check rejection")
    witness_index = rejected[0]["index"]
    witness = canonical[witness_index]["input"]
    (HERE / task / "input.json").write_text(json.dumps(witness, indent=2) + "\n")

    generated_three = 0
    generated_frame_dims = set()
    generation_selfcheck_failures = 0
    missing_frame_draws = 0
    for index in range(200):
        grid = gen.generate(9100 + index, index)
        findings = gen.self_check(grid)
        generation_selfcheck_failures += bool(findings)
        frames = []
        for _color, cells in gen._components(grid):
            if gen._rect_frame(cells):
                rows = [r for r, _ in cells]
                cols = [c for _, c in cells]
                dims = (max(rows) - min(rows) + 1, max(cols) - min(cols) + 1)
                frames.append(dims)
                generated_frame_dims.add(dims)
                generated_three += min(dims) == 3
        missing_frame_draws += not frames

    report = {
        "schema": "arc-audit-probe-v1",
        "task_id": task,
        "generator_sha256": source_sha,
        "samples": 200,
        "canonical_pairs": len(canonical),
        "canonical_self_check_rejections": rejected,
        "canonical_frames_with_dimension_3": thin_frames,
        "generated_frames_with_dimension_3": generated_three,
        "generated_frame_dimensions": [list(x) for x in sorted(generated_frame_dims)],
        "generated_self_check_failure_draws": generation_selfcheck_failures,
        "generated_missing_frame_draws": missing_frame_draws,
        "counterexample_self_check": gen.self_check(witness),
        "finding": (
            "self_check rejects canonical hollow frames with one dimension 3 and the sampler emits none, "
            "although the selected rule accepts rectangle frames with height/width >= 3"
        ),
    }
    (HERE / task / "probe.json").write_text(json.dumps(report, indent=2) + "\n")


def audit_f22() -> None:
    task = "f22baf82ea81"
    gen, path, source_sha = load_selected_generator(task, root=ROOT)
    solid = centered = 0
    signatures = set()
    for index in range(200):
        grid = gen.generate(100 + index, index)
        r0, r1, c0, c1 = nonzero_bbox(grid)
        outer = grid[r0][c0]
        inner_cells = [
            (r, c)
            for r in range(r0, r1 + 1)
            for c in range(c0, c1 + 1)
            if grid[r][c] != outer
        ]
        ir0, ir1 = min(r for r, _ in inner_cells), max(r for r, _ in inner_cells)
        ic0, ic1 = min(c for _, c in inner_cells), max(c for _, c in inner_cells)
        is_solid = len(inner_cells) == (ir1 - ir0 + 1) * (ic1 - ic0 + 1)
        solid += is_solid
        rh, rw = r1 - r0 + 1, c1 - c0 + 1
        ih, iw = ir1 - ir0 + 1, ic1 - ic0 + 1
        is_centered = (ir0, ic0) == (r0 + (rh - ih) // 2, c0 + (rw - iw) // 2)
        centered += is_centered
        signatures.add((rh, rw, ih, iw, is_solid, is_centered))

    inp = json.loads((HERE / task / "input.json").read_text())
    report = {
        "schema": "arc-audit-probe-v1",
        "task_id": task,
        "generator_sha256": source_sha,
        "samples": 200,
        "solid_inner_rectangle": solid,
        "centered_inner_rectangle": centered,
        "distinct_shape_signatures": len(signatures),
        "counterexample_self_check": gen.self_check(inp),
        "finding": (
            "sampler invariant not required by self_check: inner color is always a "
            "centered solid rectangle"
        ),
    }
    (HERE / task / "probe.json").write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    audit_a778()
    audit_f22()
    print(json.dumps({
        "a77893c9c05c": str(HERE / "a77893c9c05c/probe.json"),
        "f22baf82ea81": str(HERE / "f22baf82ea81/probe.json"),
    }, indent=2))
