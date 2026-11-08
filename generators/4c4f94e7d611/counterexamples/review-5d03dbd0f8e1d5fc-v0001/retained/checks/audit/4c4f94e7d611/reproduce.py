"""Read-only, source-bound audit for one undeclared mirror-count shortcut.

Run `build`, obtain all five labels with public arcpuzzles apply, then `analyze`.
No generator, tests, reference rule, or solve data is modified.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[2]
REPO = WORK / "repo"
TASK = "4c4f94e7d611"
SOURCE = REPO / "generators" / TASK / "generator.py"
EXPECTED_SOURCE_SHA256 = "96088190dc76a6d94deea6f6fe73ce20061d24809a98974f6bb0bec3251217b1"
SEED = 0
BAND = "easy"
INDICES = list(range(5))
QUERY_POSITION = 1


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_generator():
    if sha(SOURCE) != EXPECTED_SOURCE_SHA256:
        raise RuntimeError("Audited source bytes changed; this reproduction binds the predecessor.")
    sys.path.insert(0, str(REPO / "shared/runtime"))
    spec = importlib.util.spec_from_file_location("audit_target", SOURCE)
    gen = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gen)
    return gen


def components(grid):
    seen = set()
    result = []
    for row in range(len(grid)):
        for col in range(len(grid[0])):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            seen.add((row, col))
            stack = [(row, col)]
            cells = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for rr, cc in ((r-1, c), (r+1, c), (r, c-1), (r, c+1)):
                    if 0 <= rr < len(grid) and 0 <= cc < len(grid[0]):
                        if (rr, cc) not in seen and grid[rr][cc] == color:
                            seen.add((rr, cc))
                            stack.append((rr, cc))
            result.append({"color": color, "cells": cells})
    return result


def mirror_second_copy_only(grid):
    """Plausible rival: one mirrored second copy, every other copy original."""
    objects = components(grid)
    template = max(objects, key=lambda obj: len(obj["cells"]))
    top = min(r for r, c in template["cells"])
    left = min(c for r, c in template["cells"])
    cells = [(r-top, c-left) for r, c in template["cells"]]
    height = max(r for r, c in cells) + 1
    width = max(c for r, c in cells) + 1
    count = sum(len(obj["cells"]) == 1 for obj in objects)
    if count == 0:
        return [[0]]
    out = [[0] * (count * width + count - 1) for _ in range(height)]
    for i in range(count):
        for r, c in cells:
            out[r][i * (width + 1) + (width - 1 - c if i == 1 else c)] = template["color"]
    return out


def main():
    gen = load_generator()
    mode = sys.argv[1] if len(sys.argv) > 1 else "build"
    if mode == "build":
        pairs = []
        for index in INDICES:
            grid = gen.generate(SEED, index, difficulty=BAND)
            errors = gen.self_check(grid)
            assert errors == [], errors
            pairs.append({
                "seed": SEED, "sample_index": index, "difficulty": BAND,
                "overrides": {}, "profile": gen.schedule_profile(SEED, index, BAND),
                "validator_messages": errors, "observed": gen.observe_overrides(grid),
                "input": grid,
            })
        (HERE / "input.json").write_text(json.dumps({"inputs": [p["input"] for p in pairs]}, indent=2)+"\n")
        (HERE / "generated_manifest.json").write_text(json.dumps({
            "task_id": TASK, "generator_path": str(SOURCE),
            "generator_sha256": sha(SOURCE), "seed": SEED, "difficulty": BAND,
            "requested_start": 0, "query_position_after_rotation": QUERY_POSITION,
            "demonstration_positions": [0, 2, 3, 4], "pairs": pairs,
            "domain_status": "all five are default-generated inputs accepted by self_check; no overrides",
        }, indent=2)+"\n")
        print(json.dumps([{k: p[k] for k in ("sample_index", "profile", "observed")} for p in pairs], indent=2))
        return
    if mode != "analyze":
        raise SystemExit("Use build or analyze")
    receipt = json.loads((HERE / "racket.json").read_text())
    manifest = json.loads((HERE / "generated_manifest.json").read_text())
    assert receipt["generator_sha256"] == EXPECTED_SOURCE_SHA256
    assert receipt["task_id"] == TASK
    authority_rows = receipt["results"]
    assert len(authority_rows) == len(manifest["pairs"]) == 5
    labeled = []
    for row, meta in zip(authority_rows, manifest["pairs"], strict=True):
        assert row["input"] == meta["input"]
        assert row["valid_output"] and row["error"] is None
        assert gen.rule_mirror(row["input"]) == row["output"]
        labeled.append({"input": row["input"], "output": row["output"]})
    from reviewer_support import canonical_pairs
    canonical = canonical_pairs(TASK, root=REPO)
    canonical_fit = [mirror_second_copy_only(p["input"]) == p["output"] for p in canonical]
    demo_positions = manifest["demonstration_positions"]
    demos = [labeled[i] for i in demo_positions]
    query = labeled[QUERY_POSITION]
    demo_fits = [mirror_second_copy_only(p["input"]) == p["output"] for p in demos]
    rival_query = mirror_second_copy_only(query["input"])
    changed = [
        [r, c, query["output"][r][c], rival_query[r][c]]
        for r in range(len(query["output"])) for c in range(len(query["output"][0]))
        if query["output"][r][c] != rival_query[r][c]
    ]
    declared_status = {}
    for name, fn in gen.LESSON_COMPETITORS.items():
        fits = all(fn(p["input"]) == p["output"] for p in demos)
        declared_status[name] = "ambiguous" if fits and fn(query["input"]) != query["output"] else "survived_all" if fits else "refuted"
    report = {
        "schema": "task-local-semantic-audit-v1", "task_id": TASK,
        "generator_sha256": EXPECTED_SOURCE_SHA256,
        "rule_hash": receipt["executed_rule_hash"],
        "rule_text_sha256": receipt["rule_text_sha256"],
        "racket_receipt_sha256": sha(HERE / "racket.json"),
        "reproducer_sha256": sha(Path(__file__)),
        "rival": "mirror_second_copy_only", "canonical_fit": canonical_fit,
        "canonical_matches": sum(canonical_fit), "canonical_total": len(canonical_fit),
        "lesson_seed": SEED, "difficulty": BAND, "sample_indices": INDICES,
        "original_train_positions": [0, 1, 2, 3], "original_query_position": 4,
        "rotated_demonstration_positions": demo_positions,
        "rotated_query_position": QUERY_POSITION,
        "demonstration_fits": demo_fits,
        "query_disagrees": bool(changed), "query_difference_cells": changed,
        "query_rival_output": rival_query,
        "query_actual_racket_output": query["output"],
        "declared_rival_statuses": declared_status,
        "lesson_hook_messages": gen.lesson_identifiable(demos, query),
        "ordinary_order_has_rival_ambiguity": (
            all(mirror_second_copy_only(p["input"]) == p["output"] for p in labeled[:4])
            and mirror_second_copy_only(labeled[4]["input"]) != labeled[4]["output"]
        ),
        "five_validators_pass": all(p["validator_messages"] == [] for p in manifest["pairs"]),
        "command": receipt["command"], "effective_cwd": receipt["cwd"],
        "scope": "one five-pair default-generated lesson, one query rotation, and all four canonical pairs; no broad census",
        "instance": {"train": demos, "test": [query]},
    }
    assert all(canonical_fit) and all(demo_fits) and changed
    (HERE / "counterexample.json").write_text(json.dumps(report, indent=2)+"\n")
    print(json.dumps({k: report[k] for k in (
        "canonical_matches", "canonical_total", "demonstration_fits", "query_disagrees",
        "query_difference_cells", "declared_rival_statuses", "lesson_hook_messages",
        "ordinary_order_has_rival_ambiguity", "five_validators_pass",
    )}, indent=2))


if __name__ == "__main__":
    main()
