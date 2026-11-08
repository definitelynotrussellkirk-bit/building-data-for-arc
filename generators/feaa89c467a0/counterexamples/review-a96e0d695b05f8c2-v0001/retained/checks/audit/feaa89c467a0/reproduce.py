#!/usr/bin/env python3
"""Reproduce feaa89c467a0 n_classes=4 class collision."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Iterable

from reviewer_support import load_selected_generator

TASK_ID = "feaa89c467a0"
EXPECTED_SOURCE_SHA256 = "6213fecd5d93506562f8f73ceed3ae9ede977b27270af9a48ca71acdfc395cde"
GENERATE_KWARGS = {
    "seed": 0,
    "sample_index": 0,
    "difficulty": "easy",
    "n_classes": 4,
}
PANEL_STARTS = (0, 6, 12, 18)


def sha256_json(value: Any) -> str:
    data = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(data).hexdigest()


def norm(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def transform(cells: Iterable[tuple[int, int]], t: int) -> tuple[tuple[int, int], ...]:
    out = []
    for r, c in cells:
        if t == 0:
            out.append((r, c))
        elif t == 1:
            out.append((c, -r))
        elif t == 2:
            out.append((-r, -c))
        elif t == 3:
            out.append((-c, r))
        elif t == 4:
            out.append((r, -c))
        elif t == 5:
            out.append((-c, -r))
        elif t == 6:
            out.append((-r, c))
        elif t == 7:
            out.append((c, r))
        else:
            raise ValueError(t)
    return norm(out)


def free_dihedral_key(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    base = tuple(cells)
    return min(transform(base, t) for t in range(8))


def rotation_key(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    base = tuple(cells)
    return min(transform(base, t) for t in range(4))


def panel_cells(grid: list[list[int]], start: int) -> tuple[tuple[int, int], ...]:
    cells = [(r, c - start) for r, row in enumerate(grid) for c in range(start, start + 5) if row[c] != 0]
    return norm(cells)


def class_ids(keys: list[Any]) -> list[int]:
    mapping: dict[Any, int] = {}
    result = []
    for key in keys:
        if key not in mapping:
            mapping[key] = len(mapping)
        result.append(mapping[key])
    return result


def relation_matrix(cells_by_panel: list[tuple[tuple[int, int], ...]]) -> list[list[int]]:
    free = [free_dihedral_key(cells) for cells in cells_by_panel]
    rot = [rotation_key(cells) for cells in cells_by_panel]
    out = []
    for i in range(4):
        row = []
        for j in range(4):
            if i == j:
                row.append(8)
            elif free[i] != free[j]:
                row.append(0)
            elif rot[i] == rot[j]:
                row.append(2)
            else:
                row.append(6)
        out.append(row)
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--racket", type=Path)
    args = parser.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    root = Path(os.environ.get("ARCPUZZLES_HOME", Path.cwd()))
    module, source, digest = load_selected_generator(TASK_ID, root=root)
    if digest != EXPECTED_SOURCE_SHA256:
        raise SystemExit(f"unexpected source SHA-256: {digest}")

    grid = module.generate(**GENERATE_KWARGS)
    panels = [panel_cells(grid, start) for start in PANEL_STARTS]
    counts = [len(cells) for cells in panels]
    free_keys = [free_dihedral_key(cells) for cells in panels]
    rotations = [rotation_key(cells) for cells in panels]
    free_ids = class_ids(free_keys)
    actual_class_count = len(set(free_keys))
    requested_class_count = GENERATE_KWARGS["n_classes"]
    same_count_pairs = [
        [i, j]
        for i in range(4)
        for j in range(i + 1, 4)
        if counts[i] == counts[j]
    ]
    duplicate_class_pairs = [
        [i, j]
        for i in range(4)
        for j in range(i + 1, 4)
        if free_keys[i] == free_keys[j]
    ]
    matrix = relation_matrix(panels)

    (args.out_dir / "input.json").write_text(json.dumps(grid, indent=2) + "\n")
    report: dict[str, Any] = {
        "schema": "arcpuzzles-audit-counterexample-v1",
        "task_id": TASK_ID,
        "generator_path": str(source),
        "generator_sha256": digest,
        "generate_kwargs": GENERATE_KWARGS,
        "input": grid,
        "input_sha256": sha256_json(grid),
        "panel_cell_counts": counts,
        "free_dihedral_class_ids": free_ids,
        "free_dihedral_keys": [[[r, c] for r, c in key] for key in free_keys],
        "rotation_keys": [[[r, c] for r, c in key] for key in rotations],
        "requested_n_classes": requested_class_count,
        "actual_free_dihedral_classes": actual_class_count,
        "requested_class_count_realized": actual_class_count == requested_class_count,
        "duplicate_class_pairs": duplicate_class_pairs,
        "same_cell_count_pairs": same_count_pairs,
        "python_relation_matrix": matrix,
        "root_cause": (
            "No 3-cell polyomino has eight distinct dihedral orientations; _asym_motif(3) "
            "falls back to a 4-cell L, which can collide with the requested 4-cell class."
        ),
        "domain_status": "generated by the advertised exact override n_classes=4",
        "reproduction": {
            "cwd": "packet_root",
            "argv": [
                "python3", "review.py", "run", "python3",
                "../checks/audit/feaa89c467a0/reproduce.py",
                "--out-dir", "../checks/audit/feaa89c467a0",
            ],
        },
    }
    if args.racket:
        racket = json.loads(args.racket.read_text())
        report["racket_evidence_path"] = str(args.racket)
        report["racket"] = racket
        results = racket.get("results") or racket.get("items") or []
        if results:
            actual = results[0].get("output")
            report["actual_racket_output"] = actual
            report["racket_matches_python_relation_matrix"] = actual == matrix

    out = args.out_dir / ("counterexample.json" if args.racket else "probe.json")
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "output": str(out),
        "generator_sha256": digest,
        "requested_n_classes": requested_class_count,
        "actual_free_dihedral_classes": actual_class_count,
        "panel_cell_counts": counts,
        "class_ids": free_ids,
        "duplicate_class_pairs": duplicate_class_pairs,
    }, indent=2))
    return 0 if actual_class_count != requested_class_count and duplicate_class_pairs else 1


if __name__ == "__main__":
    raise SystemExit(main())
