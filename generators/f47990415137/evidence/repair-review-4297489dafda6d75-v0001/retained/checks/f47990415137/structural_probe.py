"""Bounded read-only structural review of the exact current parametric source."""
import argparse
import hashlib
import json
from pathlib import Path
import time
import types


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2] / "repo"
    source = root / "generators/f47990415137/workspace/parametric/prototype.py"
    body = source.read_bytes()
    prototype = types.ModuleType("f47990415137_structural_review")
    prototype.__file__ = str(source)
    exec(compile(body, str(source), "exec"), prototype.__dict__)
    started = time.monotonic()
    failures = []
    totals = {"scenes": 0, "generated_episodes": 0, "episode_pairs_checked": 0}
    failure_counts = {}

    def fail(kind, context, details=None):
        failure_counts[kind] = failure_counts.get(kind, 0) + 1
        if len(failures) < 12:
            failures.append({"kind": kind, "context": context, "details": details})

    def check_grid(grid, context, expected_aspect=None):
        if not (type(grid) is list and 8 <= len(grid) <= 30 and type(grid[0]) is list
                and 8 <= len(grid[0]) <= 30 and all(type(row) is list
                and len(row) == len(grid[0]) and all(type(v) is int and 0 <= v <= 9
                for v in row) for row in grid)):
            fail("invalid_grid", context)
            return
        groups = prototype.components(grid)
        sizes = sorted((len(cells) for _, cells in groups), reverse=True)
        if len(groups) not in (4, 6, 9):
            fail("unexpected_component_count", context, sizes)
        if sizes[0] == sizes[1]:
            fail("nonunique_largest", context, sizes)
        anchor = max(groups, key=lambda pair: len(pair[1]))
        if expected_aspect and prototype.aspect(anchor[1]) != expected_aspect:
            fail("anchor_aspect_changed", context, {
                "expected": expected_aspect, "actual": prototype.aspect(anchor[1])})

    def first_raster_reference(grid):
        groups = prototype.components(grid)
        rh, rw = prototype.dimensions(groups[0][1])
        out = [[0] * len(grid[0]) for _ in grid]
        for _, cells in groups:
            h, w = prototype.dimensions(cells)
            color = 2 if h * rw > w * rh else 3 if h * rw < w * rh else 4
            for r, c in cells:
                out[r][c] = color
        return out

    for seed in range(3):
        for height in range(8, 31):
            for width in range(8, 31):
                for aspect in ("tall", "wide", "square"):
                    context = ["scene", seed, height, width, aspect]
                    try:
                        grid = prototype.sample_scene(seed, height, width, aspect)
                        check_grid(grid, context, aspect)
                        totals["scenes"] += 1
                    except Exception as error:
                        fail("scene_exception", context, repr(error))

    for seed in range(64):
        for demos in (2, 3, 6):
            for queries in (1, 4):
                context = ["episode", seed, demos, queries]
                try:
                    axes = prototype.generate(seed, {"reference": "axes"}, demos, queries)
                    largest = prototype.generate(seed, {"reference": "largest"}, demos, queries)
                    totals["generated_episodes"] += 2
                    if len(axes["train"]) != demos or len(axes["test"]) != queries:
                        fail("count_mismatch", context)
                    inputs = [pair["input"] for split in ("train", "test") for pair in axes[split]]
                    matched = [pair["input"] for split in ("train", "test") for pair in largest[split]]
                    if inputs != matched:
                        fail("unmatched_setting_inputs", context)
                    if len({json.dumps(grid) for grid in inputs}) != len(inputs):
                        fail("duplicate_episode_inputs", context)
                    if not any(a["output"] != b["output"] for a, b in zip(axes["train"], largest["train"])):
                        fail("settings_not_taught", context)
                    for split in ("train", "test"):
                        for index, pair in enumerate(axes[split]):
                            aspect = (("tall" if index % 2 == 0 else "wide") if split == "train"
                                      else ("tall", "wide", "tall", "square")[index])
                            check_grid(pair["input"], context + [split, index], aspect)
                            totals["episode_pairs_checked"] += 1
                    if all(first_raster_reference(pair["input"]) == pair["output"]
                           for pair in largest["train"]):
                        different = [index for index, pair in enumerate(largest["test"])
                                     if first_raster_reference(pair["input"]) != pair["output"]]
                        if different:
                            fail("first_raster_rival_survives", context, {"query_indices": different})
                except Exception as error:
                    fail("episode_exception", context, repr(error))

    unchanged = source.read_bytes() == body
    if not unchanged:
        fail("source_changed_during_probe", [])
    result = {
        "schema": "f47990415137-bounded-structural-review-v1",
        "status": "passed" if not failure_counts else "findings",
        "source": source.relative_to(root).as_posix(),
        "source_sha256": hashlib.sha256(body).hexdigest(),
        "source_unchanged_during_probe": unchanged,
        "scope": {"scene_seeds": [0, 1, 2], "height_width_inclusive": [8, 30],
                  "anchor_aspects": ["tall", "wide", "square"],
                  "episode_seed_inclusive": [0, 63], "demo_counts": [2, 3, 6],
                  "query_counts": [1, 4], "settings": ["axes", "largest"]},
        "checks": ["strict grid dimensions and cells", "4/6/9 components", "unique largest component",
                   "requested anchor aspect", "independent counts", "matched setting inputs",
                   "distinct episode inputs", "finite setting distinction in demos",
                   "first-raster reference rival against demonstrations and private queries"],
        "totals": totals, "failure_counts": failure_counts, "first_failures": failures,
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "limits": "Bounded Python structural and claim-label checks only; no Racket execution, acceptance, universal uniqueness, or training admission."
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps(result, sort_keys=True))
    return 0 if not failure_counts else 1


if __name__ == "__main__":
    raise SystemExit(main())
