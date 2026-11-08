from __future__ import annotations

import copy
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
TASK_ID = "f7660051ec70"
SOURCE = ROOT / "generators" / TASK_ID / "generator.py"
EXPECTED_SOURCE_SHA256 = "abd30588253e12d116c5fbe2e9e9dd863019bf91cf6fa6ddab99af5ab2b89ba1"
OUT = Path(__file__).with_name("finding.json")


def load_generator():
    spec = importlib.util.spec_from_file_location(f"audit_{TASK_ID}", SOURCE)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {SOURCE}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def frames(grid):
    """Recover separate color-1 rectangular frames and count interior seeds."""
    height, width = len(grid), len(grid[0])
    seen = set()
    found = []
    for sr in range(height):
        for sc in range(width):
            if grid[sr][sc] != 1 or (sr, sc) in seen:
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
                        and grid[nr][nc] == 1
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            r1 = min(row for row, _ in cells)
            r2 = max(row for row, _ in cells)
            c1 = min(col for _, col in cells)
            c2 = max(col for _, col in cells)
            box_h, box_w = r2 - r1 + 1, c2 - c1 + 1
            if box_h < 3 or box_w < 3:
                continue
            if len(cells) != 2 * (box_h + box_w) - 4:
                continue
            seed_count = sum(
                grid[row][col] == 2
                for row in range(r1 + 1, r2)
                for col in range(c1 + 1, c2)
            )
            found.append(
                {
                    "r1": r1,
                    "c1": c1,
                    "r2": r2,
                    "c2": c2,
                    "seed_count": seed_count,
                }
            )
    return sorted(found, key=lambda frame: (frame["r1"], frame["c1"]))


def fill(grid, *, exactly_one_seed_only: bool):
    out = copy.deepcopy(grid)
    for frame in frames(grid):
        seed_count = frame["seed_count"]
        should_fill = seed_count == 1 if exactly_one_seed_only else seed_count >= 1
        if not should_fill:
            continue
        for row in range(frame["r1"] + 1, frame["r2"]):
            for col in range(frame["c1"] + 1, frame["c2"]):
                if out[row][col] == 0:
                    out[row][col] = 3
    return out


def intended(grid):
    return fill(grid, exactly_one_seed_only=False)


def one_seed_rival(grid):
    return fill(grid, exactly_one_seed_only=True)


def main() -> None:
    from arcpuzzles import Catalog

    source_before = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    assert source_before == EXPECTED_SOURCE_SHA256, source_before
    generator = load_generator()

    seed = 0
    sample_indices = [51, 52, 53, 54]
    grids = [
        generator.generate(seed, index, difficulty="easy")
        for index in sample_indices
    ]

    receipt = Catalog(ROOT).apply(
        TASK_ID,
        grids,
        reference="canonical",
        timeout=180,
    )
    references = [entry["output"] for entry in receipt["results"]]
    intended_outputs = [intended(grid) for grid in grids]
    rival_outputs = [one_seed_rival(grid) for grid in grids]

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
        cases.append(
            {
                "role": role,
                "sample_index": index,
                "input": grid,
                "frames": frames(grid),
                "reference_output": reference,
                "one_seed_rival_output": rival,
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
        "plausible_rival": (
            "Fill a framed interior only when it contains exactly one red seed; "
            "leave frames with two seeds unchanged."
        ),
        "rival_fits_all_demonstrations": True,
        "rival_changes_query": True,
        "rule_hash_matches_catalog": receipt["rule_hash_matches_catalog"],
        "executed_rule_hash": receipt["executed_rule_hash"],
        "catalog_rule_hash": receipt["catalog_rule_hash"],
        "cases": cases,
        "domain_note": (
            "All four inputs are ordinary default easy-band draws. The three demos contain only one-seed "
            "seeded frames, while the query contains a lawful two-seed frame. This finite witness shows a "
            "lesson-schedule ambiguity; it does not claim every lesson is ambiguous."
        ),
        "prior_audit_note": (
            "The selected source also has a prior unresolved audit for silently ignored exact overrides. "
            "This reproduction is a separate teaching-ambiguity finding."
        ),
    }
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "finding": str(OUT),
        "demos_fit": [case["rival_matches_reference"] for case in cases[:3]],
        "query_differs": not cases[3]["rival_matches_reference"],
        "query_frames": cases[3]["frames"],
        "source_sha256": source_before,
    }, indent=2))


if __name__ == "__main__":
    main()
