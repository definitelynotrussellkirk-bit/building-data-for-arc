"""Build a one-binding graph-depth intervention from native qualified pairs."""
import argparse
from collections import deque
import json
from pathlib import Path

TASK = "366cda05b486"
DESCRIPTIONS = {
    "step_a": "Extract monochromatic cardinal objects and traverse their cardinal-contact graph from the unique blue object to compute shortest object-hop distances.",
    "intermediate": "The input-dependent shortest distance of every reachable whole object from the blue seed.",
    "step_b": "Select every reachable object tied at the maximum distance, crop their complete cell union tightly, and paint those cells cyan while preserving gaps.",
    "why_b_depends_on_a": "The maximum layer depends on transitive graph routes, including detours, cycles and ties. Replacing only the distance-map binding by blue/immediate-neighbor depths changes the selected objects while preserving maximum selection, crop and paint. This is graph-derived selection, not iterative grid simulation or a training-gain claim.",
}
LOCAL_DEPTHS = """(depths
 (let ((near-depths (make-hash)))
   (for ([i (in-list cl)])
     (hash-set! near-depths i
       (cond ((= i seed) 0)
             ((member i (neighbors g objs seed)) 1)
             (else -1))))
   near-depths))"""


def intermediate(grid):
    height, width = len(grid), len(grid[0])
    objects, owner = [], {}
    deltas = ((-1, 0), (1, 0), (0, -1), (0, 1))
    for row in range(height):
        for column in range(width):
            if grid[row][column] == 0 or (row, column) in owner:
                continue
            color, index = grid[row][column], len(objects)
            queue, cells = [(row, column)], set()
            owner[row, column] = index
            while queue:
                r, c = queue.pop()
                cells.add((r, c))
                for dr, dc in deltas:
                    rr, cc = r + dr, c + dc
                    if (0 <= rr < height and 0 <= cc < width and grid[rr][cc] == color
                            and (rr, cc) not in owner):
                        owner[rr, cc] = index
                        queue.append((rr, cc))
            objects.append({"color": color, "cells": sorted(cells)})
    seed, = [i for i, obj in enumerate(objects) if obj["color"] == 1]
    adjacency = [set() for obj in objects]
    for (row, column), index in owner.items():
        for dr, dc in deltas:
            other = owner.get((row + dr, column + dc))
            if other is not None and other != index:
                adjacency[index].add(other)
    depths, queue = {seed: 0}, deque([seed])
    while queue:
        index = queue.popleft()
        for other in sorted(adjacency[index]):
            if other not in depths:
                depths[other] = depths[index] + 1
                queue.append(other)
    return {"reachable_objects": [
        {**objects[index], "shortest_object_hops": distance,
         "counterfactual_local_depth": distance if distance <= 1 else -1}
        for index, distance in sorted(depths.items())], "maximum_depth": max(depths.values())}


def build(qualification):
    qualification = Path(qualification)
    report = json.loads(qualification.read_text())
    if report["task_id"] != TASK or report["status"] != "qualified":
        raise ValueError("Expected this family's successful qualification")
    execution = json.loads(qualification.with_name("execution.json").read_text())
    index, episode = next((index, episode) for index, episode in enumerate(execution["episodes"])
                          if episode["settings"] == {"scope": "farthest"} and episode["seed"] == 0)
    program = episode["program"]
    needle = "(depths (hop-distances g objs seed))"
    if program.count(needle) != 1:
        raise ValueError("Expected exactly one qualified full-hop distance binding")
    counterfactual = program.replace(needle, LOCAL_DEPTHS, 1)
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
