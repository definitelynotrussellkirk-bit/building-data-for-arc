"""Read-only additional-rival review of a materialized lesson census.

Usage from WORK/repo: python3 ../checks/code-review/additional_rivals.py
Does not inspect solve workspaces or masked solve labels.
"""
from collections import Counter
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[1]
REPO = WORK / "repo"
CENSUS = WORK / "checks/lesson-census.json"


def components(grid):
    remaining = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v}
    answer = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        group, stack = {start}, [start]
        while stack:
            r, c = stack.pop()
            for point in ((r-1, c), (r+1, c), (r, c-1), (r, c+1)):
                if point in remaining and grid[point[0]][point[1]] == grid[r][c]:
                    remaining.remove(point)
                    group.add(point)
                    stack.append(point)
        answer.append(group)
    return answer


def rival(grid, name):
    h, w = len(grid), len(grid[0])
    inside = [group for group in components(grid)
              if not any(r in (0, h-1) or c in (0, w-1) for r, c in group)]
    largest = max(map(len, inside), default=0)
    selected = [group for group in inside
                if (len(group) > 1 if name == "discard_internal_singletons"
                    else len(group) == largest)]
    out = [[0] * w for _ in grid]
    for group in selected:
        for r, c in group:
            out[r][c] = grid[r][c]
    return out


def main():
    census = json.loads(CENSUS.read_text())
    canonical = next(json.loads(line) for line in
                     (REPO / "shared/data/canonical/puzzles.jsonl").read_text().splitlines()
                     if json.loads(line).get("task_id") == "899e2a4cfac9")
    pairs = canonical["train"] + [canonical["test"]]
    result = {
        "source_sha256": hashlib.sha256((REPO / "generators/899e2a4cfac9/generator.py").read_bytes()).hexdigest(),
        "census_sha256": hashlib.sha256(CENSUS.read_bytes()).hexdigest(),
        "census_generator_sha256": census["generator_sha256"],
        "rivals": {},
    }
    assert result["source_sha256"] == result["census_generator_sha256"]
    for name in ("discard_internal_singletons", "keep_largest_internal_components"):
        counts, rotations, witnesses = Counter(), Counter(), []
        for lesson in census["lessons"]:
            demos = lesson["instance"]["train"]
            query = lesson["instance"]["test"][0]
            materialized = demos + [query]
            fits = [rival(p["input"], name) == p["output"] for p in materialized]
            if all(fits[:-1]) and not fits[-1]:
                counts[lesson["band"]] += 1
                if len(witnesses) < 3:
                    witnesses.append({
                        key: lesson[key] for key in ("band", "index", "seed", "sample_index", "instance_sha256")
                    } | {"train": demos, "query": query, "rival_query_output": rival(query["input"], name)})
            for i in range(len(materialized)):
                if not fits[i] and all(fits[j] for j in range(len(fits)) if j != i):
                    rotations[lesson["band"]] += 1
        result["rivals"][name] = {
            "canonical_fit": all(rival(p["input"], name) == p["output"] for p in pairs),
            "ambiguous_production_lessons_by_band": dict(counts),
            "ambiguous_query_rotations_by_band": dict(rotations),
            "witnesses": witnesses,
        }
    out = HERE / "additional-rivals.json"
    out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: {a: b for a, b in v.items() if a != "witnesses"}
                      for k, v in result["rivals"].items()}, indent=2))
    print(f"Evidence: {out}")


if __name__ == "__main__":
    main()
