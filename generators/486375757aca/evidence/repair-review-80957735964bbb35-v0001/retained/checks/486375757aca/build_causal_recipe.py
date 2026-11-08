"""Select qualified frame cases and replace only B's component-source grid."""
import argparse
import json
from pathlib import Path

TASK = "486375757aca"
DESCRIPTIONS = {
    "step_a": "Execute the complete canonical fill using original blue components and original last seeds, accumulating bbox-interior writes in row-major component order.",
    "intermediate": "The completely filled grid, whose monochromatic cardinal components have new shapes, occupied areas and contacts.",
    "step_b": "Exclude background and blue, measure each remaining component's occupied area, and recolor every whole component tied for largest area to cyan.",
    "why_b_depends_on_a": "Filling changes the components that are measured and which of them tie for the maximum. The counterfactual retains the correct filled grid but derives B's masks and areas from the original input. Only that component-source reference changes; selection and painting stay intact. This is state-dependent selection, not a claim about iterative simulation or training gains.",
}


def groups(grid):
    remaining = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value}
    result = []
    while remaining:
        start = min(remaining)
        color = grid[start[0]][start[1]]
        remaining.remove(start)
        cells, queue = {start}, [start]
        while queue:
            row, col = queue.pop()
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                point = row + dr, col + dc
                if point in remaining and grid[point[0]][point[1]] == color:
                    remaining.remove(point)
                    cells.add(point)
                    queue.append(point)
        result.append({"color": color, "cells": sorted(cells), "area": len(cells)})
    return result


def intermediate(grid):
    original_groups = groups(grid)
    filled = [row[:] for row in grid]
    for obj in original_groups:
        if obj["color"] != 1:
            continue
        cells = obj["cells"]
        top, bottom = min(r for r, c in cells), max(r for r, c in cells)
        left, right = min(c for r, c in cells), max(c for r, c in cells)
        seeds = [grid[r][c] for r in range(top + 1, bottom) for c in range(left + 1, right)
                 if grid[r][c] not in (0, 1)]
        for row in range(top + 1, bottom):
            for col in range(left + 1, right):
                filled[row][col] = seeds[-1]
    measured = [obj for obj in groups(filled) if obj["color"] != 1]
    raw = [obj for obj in original_groups if obj["color"] != 1]
    maximum, raw_maximum = max(obj["area"] for obj in measured), max(obj["area"] for obj in raw)
    return {"filled_grid": filled, "eligible_filled_components": measured,
            "selected_filled_components": [obj for obj in measured if obj["area"] == maximum],
            "counterfactual_selected_raw_components": [obj for obj in raw if obj["area"] == raw_maximum]}


def build(qualification):
    qualification = Path(qualification)
    report = json.loads(qualification.read_text())
    if report["task_id"] != TASK or report["status"] != "qualified":
        raise ValueError("Expected this family's successful qualification")
    execution = json.loads(qualification.with_name("execution.json").read_text())
    index, episode = next((index, episode) for index, episode in enumerate(execution["episodes"])
                          if episode["settings"] == {"post": "largest_to_8"} and episode["seed"] == 0)
    program = episode["program"]
    if program.count("(objects filled 0)") != 1:
        raise ValueError("Expected exactly one qualified post-fill component-source reference")
    counterfactual = program.replace("(objects filled 0)", "(objects g 0)", 1)
    cases = [{"episode_index": index, "split": "train", "pair_index": pair_index,
              "intermediate_value": intermediate(episode["train"][pair_index]["input"]),
              "counterfactual_program": counterfactual, "ablation": "wrong_intermediate"}
             for pair_index in (0, 1)]
    return {**DESCRIPTIONS, "cases": cases}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--qualification", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = build(args.qualification)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x") as handle:
        json.dump(result, handle, indent=2)
        handle.write("\n")
    print(json.dumps({"cases": len(result["cases"]), "racket_executed": False,
                      "out": str(args.out)}))
