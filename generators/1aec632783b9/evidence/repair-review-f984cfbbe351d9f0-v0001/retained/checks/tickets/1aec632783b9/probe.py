#!/usr/bin/env python3
"""Protected-Racket learnability probe for peer 1aec632783b9."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from arcpuzzles import Catalog
from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import find_root, load_selected_generator

TASK_ID = "1aec632783b9"
EXPECTED_GENERATOR_SHA256 = "c55bcb365fd21c4da45afc5b8db7230501e7bbc0173c50872b7820b9a5e87505"
SEED = 5
HERE = Path(__file__).resolve().parent


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def rotate_cw(grid):
    return [list(row) for row in zip(*grid[::-1])]


def template_and_key(grid):
    h, w = len(grid), len(grid[0])
    cells = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 1]
    keys = [grid[r][c] for r in range(h) for c in range(w) if grid[r][c] in (2, 3, 4, 5)]
    if not cells or len(keys) != 1:
        raise ValueError("generated peer input violated expected template/key grammar")
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    r1, r2, c1, c2 = min(rows), max(rows), min(cols), max(cols)
    template = [
        [1 if grid[r][c] == 1 else 0 for c in range(c1, c2 + 1)]
        for r in range(r1, r2 + 1)
    ]
    return template, keys[0]


def literal(grid):
    return "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"


def main() -> int:
    root = find_root(__file__)
    generator, source_path, source_sha = load_selected_generator(TASK_ID, root=root)
    if source_sha != EXPECTED_GENERATOR_SHA256:
        raise ValueError(f"peer source drift: expected {EXPECTED_GENERATOR_SHA256}, got {source_sha}")

    programs = {
        row["program_solution"]
        for row in Catalog(root).get(TASK_ID)["variants"]
        if isinstance(row.get("program_solution"), str)
    }
    if len(programs) != 1:
        raise ValueError("expected one selected canonical program")
    canonical = next(iter(programs))
    old = "((= key 3) (rotate-cw grid))"
    new = "((= key 3) grid)"
    if canonical.count(old) != 1:
        raise ValueError("canonical key-3 branch spelling changed")
    rival = canonical.replace(old, new)

    grids = [generator.generate(SEED, index) for index in range(4)]
    parsed = [template_and_key(grid) for grid in grids]
    keys = [key for _, key in parsed]
    if keys != [5, 3, 2, 3]:
        raise AssertionError(f"source-bound schedule changed: {keys}")
    demo_key3 = parsed[1][0]
    query_key3 = parsed[3][0]
    if rotate_cw(demo_key3) != demo_key3:
        raise AssertionError("selected demo no longer hides the key-3 mapping")
    if rotate_cw(query_key3) == query_key3:
        raise AssertionError("selected query no longer distinguishes the key-3 mapping")

    with RacketBridge(timeout=30.0) as bridge:
        runtime = bridge.runtime_identity
        if runtime.get("backend") != "racket" or runtime.get("protected") is not True:
            raise RuntimeError("probe requires protected Racket")
        canonical_rule = wrap_rule(canonical)
        rival_rule = wrap_rule(rival)
        canonical_outputs = [bridge.eval_text(f"({canonical_rule} {literal(grid)})") for grid in grids]
        rival_outputs = [bridge.eval_text(f"({rival_rule} {literal(grid)})") for grid in grids]

    demo_matches = [canonical_outputs[i] == rival_outputs[i] for i in range(3)]
    query_differs = canonical_outputs[3] != rival_outputs[3]
    if demo_matches != [True, True, True] or not query_differs:
        raise AssertionError("rival did not fit all demos and disagree on query")

    result = {
        "schema": "arcpuzzles-peer-learnability-counterexample-v1",
        "task_id": TASK_ID,
        "status": "finding",
        "source": {
            "path": str(source_path.relative_to(root)),
            "sha256": source_sha,
        },
        "lesson": {"seed": SEED, "demo_indices": [0, 1, 2], "query_index": 3},
        "observed_keys": keys,
        "canonical_mapping": "key 3 -> rotate clockwise",
        "rival_mapping": "key 3 -> identity; all other branches unchanged",
        "why_rival_survives": (
            "The only key-3 demonstration has a template invariant under clockwise rotation, "
            "so identity and clockwise produce the same label."
        ),
        "why_query_disagrees": (
            "The key-3 query template is not clockwise invariant, so the two mappings produce different centered outputs."
        ),
        "demo_matches": demo_matches,
        "query_differs": query_differs,
        "templates": [
            {
                "index": index,
                "role": "demo" if index < 3 else "query",
                "key": key,
                "template": template,
                "cw_equals_identity": rotate_cw(template) == template,
            }
            for index, (template, key) in enumerate(parsed)
        ],
        "canonical_program_sha256": sha(canonical),
        "rival_program_sha256": sha(rival),
        "canonical_program": canonical,
        "rival_program": rival,
        "pairs": [
            {
                "index": index,
                "role": "demo" if index < 3 else "query",
                "input": grids[index],
                "canonical_output": canonical_outputs[index],
                "rival_output": rival_outputs[index],
                "outputs_equal": canonical_outputs[index] == rival_outputs[index],
            }
            for index in range(4)
        ],
        "racket_runtime": runtime,
        "recommended_repair": (
            "For every query key, include a demonstration with that key whose template distinguishes "
            "the canonical transform from the other three transforms; otherwise redraw or increase demonstrations."
        ),
        "limits": "One source-bound four-pair lesson and one explicit rival; not a full census.",
    }
    (HERE / "rival-key3-identity.rkt").write_text(rival + "\n", encoding="utf-8")
    (HERE / "counterexample.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": result["status"],
        "task_id": TASK_ID,
        "seed": SEED,
        "keys": keys,
        "demo_matches": demo_matches,
        "query_differs": query_differs,
        "counterexample": str(HERE / "counterexample.json"),
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
