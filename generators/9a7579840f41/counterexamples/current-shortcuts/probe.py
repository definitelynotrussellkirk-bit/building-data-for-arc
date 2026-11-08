"""Reproduce the strongest canonical-fitting shortcut for task 9a7579840f41."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
TASK_ID = "9a7579840f41"
sys.path.insert(0, str(REPO / "shared/runtime"))
from reviewer_support import canonical_pairs  # noqa: E402

spec = importlib.util.spec_from_file_location(
    "current_generator", REPO / f"generators/{TASK_ID}/generator.py"
)
generator = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(generator)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def local_color1_corner_rival(grid: list[list[int]]) -> list[list[int]]:
    """Ignore color 7 and stamp every local corner of every color-1 component."""
    h, w = len(grid), len(grid[0])
    wire = {
        (r, c)
        for r in range(h)
        for c in range(w)
        if grid[r][c] == 1
    }
    shape = generator._normalize(
        [
            (r, c)
            for r in range(h)
            for c in range(w)
            if grid[r][c] == 4
        ]
    )
    corners = [
        (r, c)
        for r, c in wire
        if (
            ((r - 1, c) in wire or (r + 1, c) in wire)
            and ((r, c - 1) in wire or (r, c + 1) in wire)
        )
    ]
    out = [[0] * w for _ in range(h)]
    for r, c in corners:
        for dr, dc in shape:
            rr, cc = r + dr, c + dc
            if 0 <= rr < h and 0 <= cc < w:
                out[rr][cc] = 4
    return out


def connected_start_component_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Trace only the component attached to 7, ignoring disconnected color-1 cells."""
    h, w = len(grid), len(grid[0])
    path, _error = generator._trace_wire_from_start(grid)
    if not path:
        raise ValueError("no start-connected wire path")
    shape = generator._normalize(
        [
            (r, c)
            for r in range(h)
            for c in range(w)
            if grid[r][c] == 4
        ]
    )
    out = [[0] * w for _ in range(h)]
    for r, c in generator._turns(path):
        for dr, dc in shape:
            rr, cc = r + dr, c + dc
            if 0 <= rr < h and 0 <= cc < w:
                out[rr][cc] = 4
    return out


def main() -> None:
    counterexample = json.loads((HERE / "input.json").read_text())
    authority_record = json.loads((HERE / "authority_output.json").read_text())
    authority = authority_record["results"][0]["output"]
    rival = local_color1_corner_rival(counterexample)
    independent = connected_start_component_mirror(counterexample)
    (HERE / "rival_output.json").write_text(json.dumps(rival, indent=2) + "\n")
    (HERE / "independent_output.json").write_text(
        json.dumps(independent, indent=2) + "\n"
    )

    canonical = canonical_pairs(TASK_ID, root=REPO, labeled_only=True)
    canonical_matches = sum(
        local_color1_corner_rival(pair["input"]) == pair["output"]
        for pair in canonical
    )

    generated_matches = 0
    generated_total = 0
    for band_index, band in enumerate(("easy", "medium", "hard")):
        for index in range(100):
            grid = generator.generate(
                970_000 + band_index * 10_000 + index,
                23 * index + 11,
                difficulty=band,
            )
            generated_total += 1
            generated_matches += int(
                local_color1_corner_rival(grid) == generator.rule_mirror(grid)
            )

    differing_cells = [
        [r, c, authority[r][c], rival[r][c]]
        for r in range(len(authority))
        for c in range(len(authority[0]))
        if authority[r][c] != rival[r][c]
    ]
    evidence = {
        "task_id": TASK_ID,
        "generator_sha256": sha256(REPO / f"generators/{TASK_ID}/generator.py"),
        "rule_hash": generator.RULE_HASH,
        "rival": (
            "ignore color 7; stamp the normalized color-4 template at every "
            "local orthogonal corner of every color-1 component"
        ),
        "canonical_matches": f"{canonical_matches}/{len(canonical)}",
        "generated_matches": f"{generated_matches}/{generated_total}",
        "counterexample_self_check": generator.self_check(counterexample),
        "counterexample_strict": generator.strict_canonical_like(counterexample),
        "authority_matches_independent_start_component_mirror": authority == independent,
        "rival_matches_authority": rival == authority,
        "differing_cells": differing_cells,
        "domain_note": (
            "The exact separator adds a disconnected L-shaped color-1 component. "
            "It is rejected by the generator grammar and is not emitted. Within "
            "the accepted single-component nonbranching domain, this rival is "
            "answer-equivalent to ordered turn detection."
        ),
        "files": {
            "input": "input.json",
            "authority": "authority_output.json",
            "independent": "independent_output.json",
            "rival": "rival_output.json",
        },
    }
    (HERE / "evidence.json").write_text(json.dumps(evidence, indent=2) + "\n")
    print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    main()
