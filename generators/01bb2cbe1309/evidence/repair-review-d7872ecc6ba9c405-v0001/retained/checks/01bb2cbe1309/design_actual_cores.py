"""Inspect the actual two teaching cores without changing the native source."""
from __future__ import annotations

import hashlib
import importlib.util
from itertools import product
import json
from pathlib import Path

from design_probe import changed, compose, repeat, stable


def main():
    source = Path("generators/01bb2cbe1309/workspace/parametric/native_family.py")
    spec = importlib.util.spec_from_file_location("diagonal_actual_core", source)
    family = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(family)
    ops = {
        "S": {}, "reverseS": {"reverse": True},
        "F": {"inplace": True}, "R": {"inplace": True, "reverse": True},
        "M": {"orientation": "main"}, "A": {"orientation": "anti"},
    }
    extras = {
        "ignore_blockers_fill_zeros": {"relax_blockers": True},
        "ignore_blockers_overwrite": {"relax_blockers": True, "overwrite_blockers": True},
        "also_axis_pairs": {"axes": True},
        "ignore_endpoint_equality": {"unequal": True},
    }
    report = {"source": source.as_posix(),
              "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
              "seeds": [0, 17], "cases": []}
    for seed, passes in product((0, 17), (1, 2)):
        episode = family.generate(seed, {"passes": passes}, demos=2, queries=4)
        demos = [row["input"] for row in episode["train"]]
        labels = [row["output"] for row in episode["train"]]
        assert all(repeat(grid, passes) == want for grid, want in zip(demos, labels))
        rivals = {"identity": lambda g: g, "fixedpoint": stable}
        for count in (1, 2, 3):
            rivals[f"snapshot{count}"] = lambda g, n=count: repeat(g, n)
        for name, options in {**ops, **extras}.items():
            for count in (1, 2):
                rivals[f"{name}{count}"] = lambda g, n=count, o=options: repeat(g, n, **o)
        differences = {
            name: [changed(want, function(grid)) for grid, want in zip(demos, labels)]
            for name, function in rivals.items()
        }
        survivors = [list(names) for size in (1, 2)
                     for names in product(ops, repeat=size)
                     if all(compose(grid, [ops[name] for name in names]) == want
                            for grid, want in zip(demos, labels))]
        assert survivors == ([["S"]] if passes == 1 else [["S", "S"]])
        intended = {f"snapshot{passes}", f"S{passes}"}
        unexpected = [name for name, diffs in differences.items()
                      if name not in intended and not any(diffs)]
        assert not unexpected, unexpected
        report["cases"].append({
            "seed": seed, "passes": passes,
            "demo_shapes": [[len(grid), len(grid[0])] for grid in demos],
            "label_sha256": [hashlib.sha256(json.dumps(row, separators=(",", ":")).encode()).hexdigest()
                             for row in episode["train"]],
            "rival_disagreements": differences,
            "surviving_operations": survivors,
            "unexpected_surviving_rivals": unexpected,
        })
    destination = Path(__file__).with_suffix(".json")
    destination.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"report": str(destination), "source_sha256": report["source_sha256"],
                      "cases": [{key: case[key] for key in
                                 ("seed", "passes", "demo_shapes", "surviving_operations", "unexpected_surviving_rivals")}
                                for case in report["cases"]]}))


if __name__ == "__main__":
    main()
