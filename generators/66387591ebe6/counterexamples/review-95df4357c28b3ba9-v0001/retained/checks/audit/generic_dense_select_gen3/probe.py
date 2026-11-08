#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import json
from collections import Counter
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
PACKET = HERE.parents[2]
REPO = PACKET / "repo"
SOURCE = REPO / "generators" / "generic_dense_select_gen3" / "generator.py"
EXPECTED_SOURCE_SHA = "82f27ec2303a759ab646f81910024bcbbdba448eb00b60334bfc01e27e0d0953"


def load_module(path: Path):
    spec = importlib.util.spec_from_file_location("audit_generic_dense_select_gen3", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def grid_hash(grid: list[list[int]]) -> str:
    raw = json.dumps(grid, separators=(",", ":"), sort_keys=False).encode()
    return sha256_bytes(raw)


def size_only_rival(gen: Any, grid: list[list[int]], bg: int) -> list[list[int]]:
    objs = gen.py_objects(grid, bg=bg)
    sizes = [len(obj["cells"]) for obj in objs]
    keep = next((obj for obj, size in zip(objs, sizes) if sizes.count(size) == 1), None)
    if keep is None:
        return [row[:] for row in grid]
    return gen.erase_objects(grid, [obj for obj in objs if obj is not keep], bg=bg)


def main() -> None:
    source_sha = sha256_bytes(SOURCE.read_bytes())
    if source_sha != EXPECTED_SOURCE_SHA:
        raise SystemExit(f"source hash mismatch: {source_sha}")
    gen = load_module(SOURCE)

    bands = ("easy", "medium", "hard")
    seeds_per_band = 500
    tasks = pairs = 0
    rival_matches = 0
    different_size_pairs = 0
    one_shape_singleton = 0
    unique_input_hashes: set[str] = set()
    pair_counts: Counter[str] = Counter()
    failures: list[dict[str, Any]] = []

    for band in bands:
        for seed in range(seeds_per_band):
            task = gen.generate_task(seed, difficulty=band)
            tasks += 1
            for pair_index, pair in enumerate(task["train"] + task["test"]):
                pairs += 1
                grid = pair["input"]
                expected = pair["output"]
                bg = int(task["meta"]["bg_color"])
                objs = gen.py_objects(grid, bg=bg)
                shapes = [gen.norm_shape(obj["cells"]) for obj in objs]
                sizes = [len(obj["cells"]) for obj in objs]
                shape_singletons = [i for i, shape in enumerate(shapes) if shapes.count(shape) == 1]
                size_singletons = [i for i, size in enumerate(sizes) if sizes.count(size) == 1]
                if len(shape_singletons) == 1:
                    one_shape_singleton += 1
                if len(size_singletons) == 1 and size_singletons == shape_singletons:
                    different_size_pairs += 1
                rival = size_only_rival(gen, grid, bg)
                if rival == expected:
                    rival_matches += 1
                elif len(failures) < 10:
                    failures.append({
                        "band": band,
                        "seed": seed,
                        "pair_index": pair_index,
                        "shape_singletons": shape_singletons,
                        "size_singletons": size_singletons,
                    })
                unique_input_hashes.add(grid_hash(grid))
                pair_counts[band] += 1

    manual_input = json.loads((HERE / "input.json").read_text())
    intended = gen._apply(manual_input, bg=1)
    rival = size_only_rival(gen, manual_input, bg=1)
    manual_objs = gen.py_objects(manual_input, bg=1)
    manual_shapes = [gen.norm_shape(obj["cells"]) for obj in manual_objs]
    manual_sizes = [len(obj["cells"]) for obj in manual_objs]
    (HERE / "python_intended.json").write_text(json.dumps(intended, indent=2) + "\n")
    (HERE / "rival.json").write_text(json.dumps(rival, indent=2) + "\n")

    report = {
        "schema": "arcpuzzles-adversarial-audit-v1",
        "task_id": "generic_dense_select_gen3",
        "finding_kind": "suspected_shortcut",
        "generator_sha256": source_sha,
        "generator_version": gen.VERSION,
        "probe": {
            "bands": list(bands),
            "seed_range_each_band": [0, seeds_per_band - 1],
            "tasks": tasks,
            "pairs": pairs,
            "pairs_by_band": dict(pair_counts),
            "unique_inputs": len(unique_input_hashes),
            "exactly_one_shape_singleton": one_shape_singleton,
            "odd_shape_also_unique_by_cell_count": different_size_pairs,
            "cell_count_rival_matches_saved_output": rival_matches,
            "failures": failures,
        },
        "rival": {
            "name": "unique_cell_count_instead_of_unique_shape",
            "definition": "Keep the only object whose cell count is unique; erase all others. If no size is unique, return the input unchanged.",
            "why_it_fits_generated_pairs": "The generator always chooses odd_size != base_size, so the intended shape singleton is also the sole size singleton.",
        },
        "counterexample": {
            "input_path": "checks/audit/generic_dense_select_gen3/input.json",
            "python_intended_path": "checks/audit/generic_dense_select_gen3/python_intended.json",
            "rival_path": "checks/audit/generic_dense_select_gen3/rival.json",
            "object_sizes": manual_sizes,
            "shape_class_counts": sorted(Counter(map(str, manual_shapes)).values()),
            "intended_differs_from_rival": intended != rival,
            "validator": "none exposed by this generic generator",
            "documented_generated_domain": False,
            "domain_note": "The grid is task-lawful (three repeated translated L triominoes and one different same-size triomino) but deliberately lies outside the generator's different-size construction.",
            "authority_check": "Python _apply mirror only; public arcpuzzles apply cannot resolve a canonical per-puzzle rule for generic_dense_select_gen3.",
            "input_sha256": grid_hash(manual_input),
            "python_intended_sha256": grid_hash(intended),
            "rival_sha256": grid_hash(rival),
        },
        "verdict": "All sampled generated pairs are explainable by the size-only rival; add same-size/different-shape witnesses if the intended concept is shape equivalence rather than size uniqueness.",
    }
    (HERE / "report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    if failures or intended == rival:
        raise SystemExit(1)
    print(json.dumps({
        "tasks": tasks,
        "pairs": pairs,
        "unique_inputs": len(unique_input_hashes),
        "rival_matches": rival_matches,
        "manual_counterexample_differs": intended != rival,
    }, indent=2))


if __name__ == "__main__":
    main()
