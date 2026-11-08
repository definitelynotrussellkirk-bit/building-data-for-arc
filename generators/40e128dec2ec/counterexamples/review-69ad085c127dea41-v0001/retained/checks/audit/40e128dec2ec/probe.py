#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

from reviewer_support import load_selected_generator

TASK_ID = "40e128dec2ec"
ROOT = Path.cwd()
GEN, SOURCE_PATH, SOURCE_SHA256 = load_selected_generator(TASK_ID, root=ROOT)


def marker1_transpose(template, marker):
    if marker == 1:
        return GEN._transpose(template)
    return GEN._normal_transform(template, marker)


def main() -> int:
    seed = 35026673918736
    start = 35
    pairs = []
    for sample_index in range(start, start + GEN.EXAMPLES_NEEDED + 1):
        grid = GEN.generate(seed, sample_index, difficulty="easy")
        pairs.append({
            "sample_index": sample_index,
            "input": grid,
            "output": GEN._official_solution(grid),
            "template": [list(row) for row in GEN._analyse(grid)[0]["template"]],
            "frame_colors": list(GEN._analyse(grid)[0]["frame_colors"]),
        })
    demos, query = pairs[:GEN.EXAMPLES_NEEDED], pairs[GEN.EXAMPLES_NEEDED]
    rival_outputs = [
        GEN._solve_with_mapping(pair["input"], marker1_transpose)
        for pair in pairs
    ]
    demo_fits = [
        rival_outputs[i] == demos[i]["output"]
        for i in range(len(demos))
    ]
    query_differs = rival_outputs[-1] != query["output"]
    hook = GEN.lesson_identifiable(demos, query)
    assert all(demo_fits)
    assert query_differs
    assert hook == []
    differing_cells = [
        [r, c]
        for r in range(len(query["output"]))
        for c in range(len(query["output"][0]))
        if rival_outputs[-1][r][c] != query["output"][r][c]
    ]
    result = {
        "schema": "audit-40e128dec2ec-v1",
        "task_id": TASK_ID,
        "source_path": str(SOURCE_PATH.relative_to(ROOT)),
        "source_sha256": SOURCE_SHA256,
        "seed": seed,
        "start_sample_index": start,
        "rival": "marker 1 uses transpose; markers 2/3/4 use official transforms",
        "demo_fits": demo_fits,
        "query_differs": query_differs,
        "lesson_identifiable_return": hook,
        "query_differing_cells": differing_cells,
        "pairs": pairs,
        "rival_outputs": rival_outputs,
    }
    out = Path("../checks/audit/40e128dec2ec/probe-result.json")
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "status": "reproduced",
        "out": str(out),
        "source_sha256": SOURCE_SHA256,
        "demo_fits": demo_fits,
        "query_differs": query_differs,
        "hook_missed": hook == [],
        "query_differing_cells": len(differing_cells),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
