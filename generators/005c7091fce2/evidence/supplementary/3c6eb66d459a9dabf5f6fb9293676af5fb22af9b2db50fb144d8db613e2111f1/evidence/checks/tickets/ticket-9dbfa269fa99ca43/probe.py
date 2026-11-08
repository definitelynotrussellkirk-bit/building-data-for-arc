#!/usr/bin/env python3
"""One bounded largest-bounding-box shortcut probe; peer source remains untouched."""
from pathlib import Path
import hashlib
import json
import time

from arcpuzzles.catalog import Catalog
from arcpuzzles.runtime import apply_rule
from reviewer_support import canonical_path, find_root, load_selected_generator

TASK = "005c7091fce2"
TICKET = "ticket-9dbfa269fa99ca43"
PIN = "694687d7db47593690050f189d6de52442e9311f3900f6ee2b437263efaf0f01"
TICKET_SEED = "10bb120f2e3f08e70b6b551461740b7b1b30a646d1b8236585dd1b001819669b"
HERE = Path(__file__).resolve().parent
ROOT = find_root(__file__)


def components(grid):
    left = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v}
    result = []
    while left:
        first = min(left)
        color = grid[first[0]][first[1]]
        cells, stack = {first}, [first]
        left.remove(first)
        while stack:
            r, c = stack.pop()
            for cell in ((r-1, c), (r+1, c), (r, c-1), (r, c+1)):
                if cell in left and grid[cell[0]][cell[1]] == color:
                    left.remove(cell)
                    cells.add(cell)
                    stack.append(cell)
        rows, cols = zip(*cells)
        box = [min(rows), min(cols), max(rows), max(cols)]
        result.append({"color": color, "size": len(cells), "bbox": box,
                       "bbox_area": (box[2]-box[0]+1)*(box[3]-box[1]+1),
                       "cells": sorted(cells)})
    return result


def shortcut(grid):
    objs = components(grid)
    winner = min(objs, key=lambda obj: (-obj["bbox_area"], obj["bbox"]))
    output = [[0]*len(grid[0]) for _ in grid]
    for r, c in winner["cells"]:
        output[r][c] = 8
    return output


def literal(value):
    return "("+" ".join(literal(x) for x in value)+")" if isinstance(value, list) else str(value)


def main():
    began = time.monotonic()
    module, path, digest = load_selected_generator(TASK, root=ROOT)
    if digest != PIN:
        raise ValueError("ticket source binding changed")
    rows = [json.loads(line) for line in canonical_path(ROOT).read_text().splitlines()]
    rows = [row for row in rows if row.get("task_id") == TASK]
    programs = {row["program_solution"] for row in rows}
    if len(programs) != 1:
        raise ValueError("canonical authorities disagree")
    program = programs.pop()
    seed = int(TICKET_SEED[:16], 16)
    tested, witness = 0, None
    for index in range(32):
        grid = module.generate(seed, index, difficulty="hard", size_gap="narrow")
        tested += 1
        problems = module.self_check(grid)
        objs = components(grid)
        by_size = sorted(objs, key=lambda obj: (-obj["size"], obj["bbox"]))
        by_area = sorted(objs, key=lambda obj: (-obj["bbox_area"], obj["bbox"]))
        if problems or len(objs) < 2 or by_size[0]["size"] == by_size[1]["size"]:
            continue
        if by_size[0]["cells"] == by_area[0]["cells"]:
            continue
        (HERE/"candidate.json").write_text(json.dumps({"input": grid, "seed": seed, "sample_index": index, "objects": objs, "self_check": problems}, indent=2)+"\n")
        try:
            applied = apply_rule(Catalog(ROOT), TASK, [grid], check_generator_domain=True, timeout=90)
            (HERE/"reference-application.json").write_text(json.dumps(applied, indent=2)+"\n")
            if applied["executed_rule_hash"] != "0f58d70a9f8a" or not applied["rule_hash_matches_catalog"]:
                raise AssertionError("reference rule differs from ticket pin")
            output = applied["results"][0]["output"]
            if output is None:
                raise RuntimeError(str(applied["results"][0]))
        except Exception as error:
            result = {"ticket_id": TICKET, "type": "adversarial_witness", "status": "blocked", "task_id": TASK, "generator_sha256": digest, "ticket_seed": TICKET_SEED, "candidate_sample_index": index, "error": f"{type(error).__name__}: {error}", "probe_seconds": time.monotonic()-began, "summary": "A candidate size-versus-box-area counterexample was found, but exact reference execution failed; no label or safety claim."}
            (HERE/"result.json").write_text(json.dumps(result, indent=2)+"\n")
            print(json.dumps(result, sort_keys=True))
            return
        rival_output = shortcut(grid)
        expected = [[0]*len(grid[0]) for _ in grid]
        for r, c in by_size[0]["cells"]:
            expected[r][c] = 8
        if output != expected:
            raise AssertionError("executed canonical rule disagrees with unique-largest witness")
        witness = {"input": grid, "canonical_output": output, "rival_output": rival_output,
                   "outputs_differ": output != rival_output, "objects": objs,
                   "seed": seed, "sample_index": index, "difficulty": "hard",
                   "overrides": {"size_gap": "narrow"}, "self_check": problems,
                   "unique_largest_size": by_size[0]["size"],
                   "bbox_shortcut_chosen_size": by_area[0]["size"],
                   "racket_sha256": hashlib.sha256(program.encode()).hexdigest()}
        (HERE/"witness.json").write_text(json.dumps(witness, indent=2)+"\n")
        break
    result = {"ticket_id": TICKET, "type": "adversarial_witness", "status": "completed" if witness else "unknown",
              "task_id": TASK, "source_path": str(path.relative_to(ROOT)), "generator_sha256": digest,
              "ticket_rule_hash": "0f58d70a9f8a", "racket_sha256": hashlib.sha256(program.encode()).hexdigest(),
              "ticket_seed": TICKET_SEED, "probe": "largest bounding-box area instead of largest monochrome component by cell count",
              "maximum_candidates": 32, "candidates_inspected": tested,
              "racket_calls": 1 if witness else 0, "witness_found": bool(witness),
              "summary": "One lawful generated input refutes the bounding-box-area shortcut; this is teaching support, not a peer defect or approval." if witness else "No distinguishing lawful witness found in the bounded search; no safety claim.",
              "probe_seconds": time.monotonic()-began, "limits": ["one bounded shortcut probe", "unchanged peer source", "not an audit closure or full generator validation"]}
    (HERE/"result.json").write_text(json.dumps(result, indent=2)+"\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
