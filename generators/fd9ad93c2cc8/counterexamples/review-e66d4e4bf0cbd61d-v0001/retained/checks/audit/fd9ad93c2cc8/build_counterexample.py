#!/usr/bin/env python3
"""Build the source-bound wildcard-vs-exact audit counterexample."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path


def load_generator(repo_root: Path):
    source = repo_root / "generators/fd9ad93c2cc8/generator.py"
    spec = importlib.util.spec_from_file_location("audit_fd9ad93c2cc8_generator", source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, source


def main() -> int:
    repo_root = Path.cwd()
    module, source = load_generator(repo_root)
    out_dir = Path(__file__).resolve().parent

    seed = 20261003
    sample_index = 0
    difficulty = "medium"
    overrides = {"grid_h": 7, "board_w": 8, "match_count": 3}
    grid = module.generate(seed, sample_index, difficulty=difficulty, **overrides)
    scene = module._inspect_scene(grid)
    if scene.foreign_cells or len(scene.target_hits) != 3:
        raise RuntimeError("chosen source draw no longer has the expected clean 3-target profile")

    tr, tc = scene.target_hits[0]
    chosen = None
    for dr in range(3):
        for dc in range(3):
            if (dr, dc) in module._TEMPLATE_MASK:
                continue
            rr, cc = tr + dr, tc + dc
            if scene.board[rr][cc] == 0:
                chosen = (rr, cc)
                break
        if chosen is not None:
            break
    if chosen is None:
        raise RuntimeError("no template-zero cell available for the one-cell mutation")

    rr, cc = chosen
    mutated = [row[:] for row in grid]
    mutated[rr][4 + cc] = 3

    def exact_rival(candidate):
        board = [row[4:] for row in candidate]
        height, width = len(board), len(board[0])
        output = [[0] * width for _ in range(height)]
        hits = []
        for r in range(height - 2):
            for c in range(width - 2):
                exact = all(
                    board[r + dr][c + dc]
                    == (2 if (dr, dc) in module._TEMPLATE_MASK else 0)
                    for dr in range(3)
                    for dc in range(3)
                )
                if exact:
                    hits.append((r, c))
                    output[r + 1][c + 1] = 8
        return output, hits

    rival, exact_hits = exact_rival(mutated)

    canonical_row = None
    canonical_path = repo_root / "shared/data/canonical/puzzles.jsonl"
    for line in canonical_path.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == module.TASK_ID:
            canonical_row = row
            break
    if canonical_row is None:
        raise RuntimeError("canonical task row not found")
    canonical_pairs = [*canonical_row["train"], canonical_row["test"]]
    canonical_fits = [
        exact_rival(pair["input"])[0] == pair["output"]
        for pair in canonical_pairs
    ]

    input_path = out_dir / "input.json"
    rival_path = out_dir / "rival.json"
    input_path.write_text(json.dumps(mutated, indent=2) + "\n", encoding="utf-8")
    rival_path.write_text(json.dumps(rival, indent=2) + "\n", encoding="utf-8")

    metadata = {
        "schema": "arcpuzzles-audit-counterexample-build-v1",
        "task_id": module.TASK_ID,
        "generator_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "rule_hash_declared": module.RULE_HASH,
        "seed": seed,
        "sample_index": sample_index,
        "difficulty": difficulty,
        "overrides": overrides,
        "mutated_target_anchor": [tr, tc],
        "mutation_board_cell": [rr, cc],
        "mutation_input_cell": [rr, 4 + cc],
        "mutation_value": 3,
        "wildcard_hits_before": [list(hit) for hit in scene.target_hits],
        "exact_hits_after": [list(hit) for hit in exact_hits],
        "validator_errors_after": module.self_check(mutated),
        "documented_generator_domain": False,
        "reason_outside_domain": (
            "self_check explicitly rejects wildcard-zero overlaps even though "
            "the canonical Racket matcher permits them"
        ),
        "rival": "exact_3x3_copy_only",
        "canonical_pairs_checked": len(canonical_fits),
        "canonical_pairs_fit": sum(canonical_fits),
        "canonical_rival_fits_every_pair": all(canonical_fits),
        "command": [
            "python3",
            "run_with_racket.py",
            "python3",
            "../checks/audit/fd9ad93c2cc8/build_counterexample.py",
        ],
        "cwd": "packet_root",
        "input_sha256": hashlib.sha256(input_path.read_bytes()).hexdigest(),
        "rival_sha256": hashlib.sha256(rival_path.read_bytes()).hexdigest(),
    }
    (out_dir / "metadata.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(metadata, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
