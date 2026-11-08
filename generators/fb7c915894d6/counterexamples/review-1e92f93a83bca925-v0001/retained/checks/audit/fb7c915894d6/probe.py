#!/usr/bin/env python3
from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path

from reviewer_support import canonical_path, find_root, load_selected_generator

TASK_ID = "fb7c915894d6"
ROOT = find_root(__file__)
GEN, SOURCE, SOURCE_SHA256 = load_selected_generator(TASK_ID, root=ROOT)
OUT = Path(__file__).resolve().parent
CARDINAL = ((1, 0), (-1, 0), (0, 1), (0, -1))


def normalize(cells):
    min_row = min(r for r, _ in cells)
    min_col = min(c for _, c in cells)
    return tuple(sorted((r - min_row, c - min_col) for r, c in cells))


def components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    result = []
    for row in range(h):
        for col in range(w):
            if grid[row][col] == 0 or (row, col) in seen:
                continue
            todo = [(row, col)]
            seen.add((row, col))
            cells = []
            while todo:
                current = todo.pop()
                cells.append(current)
                cr, cc = current
                for dr, dc in CARDINAL:
                    nr, nc = cr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and grid[nr][nc] != 0
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        todo.append((nr, nc))
            result.append(cells)
    return result


def observed_axes(grid):
    comps = components(grid)
    frequencies = Counter(normalize(cells) for cells in comps)
    frequent_shape, realized_k = frequencies.most_common(1)[0]
    return {
        "K": realized_k,
        "shape_size": len(frequent_shape),
        "n_distractors": len(comps) - realized_k,
        "component_count": len(comps),
        "shape_class_frequencies": sorted(frequencies.values(), reverse=True),
        "frequent_shape": [list(cell) for cell in frequent_shape],
    }


def canonical_rule_hash():
    for line in canonical_path(ROOT).read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            text = row["program_solution"]
            return hashlib.sha256(" ".join(text.split()).encode()).hexdigest()
    raise KeyError(TASK_ID)


def main():
    request = {"K": 5, "shape_size": 7, "n_distractors": 4}
    default = GEN.generate(1, 0, difficulty="easy")
    requested = GEN.generate(1, 0, difficulty="easy", **request)
    assert default == requested
    observed = observed_axes(requested)
    assert observed["K"] != request["K"] or observed["shape_size"] != request["shape_size"]

    invalid_texture = GEN.generate(1, 0, difficulty="easy", texture="no_frequent")
    invalid_errors = GEN.self_check(invalid_texture, difficulty="easy")

    report = {
        "schema": "audit-probe-v1",
        "task_id": TASK_ID,
        "source_path": str(SOURCE),
        "source_sha256": SOURCE_SHA256,
        "canonical_rule_normalized_sha256": canonical_rule_hash(),
        "finding": (
            "Advertised exact axes K, shape_size, and n_distractors are ignored: "
            "the override request produces a byte-identical grid to the default "
            "and realizes different values."
        ),
        "request": request,
        "seed": 1,
        "sample_index": 0,
        "difficulty": "easy",
        "default_input": default,
        "requested_input": requested,
        "default_equals_requested": default == requested,
        "observed": observed,
        "requested_self_check": GEN.self_check(requested, difficulty="easy"),
        "secondary_contract_finding": {
            "request": {"texture": "no_frequent"},
            "input": invalid_texture,
            "self_check": invalid_errors,
            "accepted_by_generate_but_rejected_by_self_check": bool(invalid_errors),
        },
        "limits": [
            "This probe demonstrates ignored controls for one deterministic request; it does not enumerate every override.",
            "The audit does not modify the target generator.",
        ],
    }
    (OUT / "counterexample.json").write_text(json.dumps(report, indent=2) + "\n")
    (OUT / "inputs.json").write_text(
        json.dumps({"inputs": [requested, invalid_texture]}, indent=2) + "\n"
    )
    print(json.dumps({
        "source_sha256": SOURCE_SHA256,
        "default_equals_requested": True,
        "request": request,
        "observed": observed,
        "invalid_texture_errors": invalid_errors,
    }))


if __name__ == "__main__":
    main()
