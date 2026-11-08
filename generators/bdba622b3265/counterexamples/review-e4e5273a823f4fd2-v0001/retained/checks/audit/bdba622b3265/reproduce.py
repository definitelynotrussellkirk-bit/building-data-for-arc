from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path


def find_repo() -> Path:
    candidates = [Path.cwd(), *Path(__file__).resolve().parents]
    for candidate in candidates:
        for root in (candidate, candidate / "repo"):
            if (root / "shared" / "data" / "canonical" / "puzzles.jsonl").exists():
                return root
    raise RuntimeError("could not locate packet repo root")


ROOT = find_repo()
TASK_ID = "bdba622b3265"
SOURCE = ROOT / "generators" / TASK_ID / "generator.py"
EXPECTED_SOURCE_SHA256 = "8f66b2168fefc102af00c247620518eaf55e3d1a1275d3f03c0251627250f5cd"
OUT = Path(__file__).with_name("finding.json")


def load_generator():
    spec = importlib.util.spec_from_file_location(f"audit_{TASK_ID}", SOURCE)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {SOURCE}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def objects(grid):
    height, width = len(grid), len(grid[0])
    seen = set()
    found = []
    for sr in range(height):
        for sc in range(width):
            color = grid[sr][sc]
            if color == 0 or (sr, sc) in seen:
                continue
            stack = [(sr, sc)]
            seen.add((sr, sc))
            cells = []
            while stack:
                row, col = stack.pop()
                cells.append((row, col))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = row + dr, col + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            found.append(
                {
                    "color": color,
                    "size": len(cells),
                    "r1": min(row for row, _ in cells),
                    "c1": min(col for _, col in cells),
                }
            )
    return found


def comparison_matrix(items, *, ordering):
    ordered = sorted(items, key=ordering)
    sizes = [item["size"] for item in ordered]
    return [
        [1 if left < right else 2 if left == right else 3 for right in sizes]
        for left in sizes
    ]


def intended(grid):
    return comparison_matrix(
        objects(grid),
        ordering=lambda item: (item["color"], item["r1"], item["c1"]),
    )


def spatial_rival(grid):
    return comparison_matrix(
        objects(grid),
        ordering=lambda item: (item["r1"], item["c1"], item["color"]),
    )


def main() -> None:
    from arcpuzzles import Catalog

    source_before = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    assert source_before == EXPECTED_SOURCE_SHA256, source_before
    generator = load_generator()

    seed = 2
    sample_indices = [160, 161, 162, 163]
    grids = [
        generator.generate(seed, index, difficulty="easy")
        for index in sample_indices
    ]
    assert all(generator.self_check(grid, difficulty="easy") == [] for grid in grids)

    receipt = Catalog(ROOT).apply(
        TASK_ID,
        grids,
        reference="canonical",
        timeout=180,
    )
    references = [entry["output"] for entry in receipt["results"]]
    intended_outputs = [intended(grid) for grid in grids]
    rival_outputs = [spatial_rival(grid) for grid in grids]

    assert receipt["rule_hash_matches_catalog"]
    assert references == intended_outputs
    assert rival_outputs[:3] == references[:3]
    assert rival_outputs[3] != references[3]

    cases = []
    for role, index, grid, reference, rival in zip(
        ("demo", "demo", "demo", "query"),
        sample_indices,
        grids,
        references,
        rival_outputs,
        strict=True,
    ):
        by_color = sorted(objects(grid), key=lambda item: (item["color"], item["r1"], item["c1"]))
        by_space = sorted(objects(grid), key=lambda item: (item["r1"], item["c1"], item["color"]))
        cases.append(
            {
                "role": role,
                "sample_index": index,
                "input": grid,
                "objects_by_color": by_color,
                "objects_by_space": by_space,
                "reference_output": reference,
                "spatial_rival_output": rival,
                "rival_matches_reference": rival == reference,
            }
        )

    source_after = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    assert source_after == source_before
    report = {
        "schema": "arcpuzzles-audit-finding-v1",
        "task_id": TASK_ID,
        "classification": "reproduced_lesson_ambiguity",
        "generator_version": generator.VERSION,
        "generator_sha256": source_before,
        "generator_sha256_after": source_after,
        "seed": seed,
        "difficulty": "easy",
        "demonstration_sample_indices": sample_indices[:3],
        "query_sample_index": sample_indices[3],
        "plausible_rival": "Sort blobs by top-left position (row, column) instead of ascending color, then compare areas identically.",
        "rival_fits_all_demonstrations": True,
        "rival_changes_query": True,
        "rule_hash_matches_catalog": receipt["rule_hash_matches_catalog"],
        "executed_rule_hash": receipt["executed_rule_hash"],
        "catalog_rule_hash": receipt["catalog_rule_hash"],
        "cases": cases,
        "domain_note": (
            "All four inputs are ordinary default easy-band draws and pass the selected generator's self_check. "
            "This is a finite counterexample to lesson identifiability, not a claim about every sampled lesson."
        ),
    }
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "finding": str(OUT),
        "demos_fit": [case["rival_matches_reference"] for case in cases[:3]],
        "query_differs": not cases[3]["rival_matches_reference"],
        "source_sha256": source_before,
    }, indent=2))


if __name__ == "__main__":
    main()
