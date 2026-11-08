#!/usr/bin/env python3
"""Build compact, hash-bound evidence for the two assigned audit targets."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from collections import Counter, deque
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "repo" / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))

CANONICAL = ROOT / "repo" / "shared" / "data" / "canonical" / "puzzles.jsonl"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_generator(task_id: str):
    path = ROOT / "repo" / "generators" / task_id / "generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_{task_id}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, path


def full_gray_edges(grid):
    h, w = len(grid), len(grid[0])
    edges = []
    if all(grid[0][c] == 5 for c in range(w)):
        edges.append("top")
    if all(grid[h - 1][c] == 5 for c in range(w)):
        edges.append("bottom")
    if all(grid[r][0] == 5 for r in range(h)):
        edges.append("left")
    if all(grid[r][w - 1] == 5 for r in range(h)):
        edges.append("right")
    return edges


def right_only_rival(grid):
    """Project colored components right only; otherwise leave the grid alone."""
    h, w = len(grid), len(grid[0])
    if "right" not in full_gray_edges(grid):
        return [row[:] for row in grid]

    out = [row[:] for row in grid]
    seen = set()
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color in (0, 5) or (r, c) in seen:
                continue
            queue = deque([(r, c)])
            seen.add((r, c))
            component = []
            while queue:
                rr, cc = queue.popleft()
                component.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            rows = sorted({rr for rr, _ in component})
            start = min(cc for _, cc in component)
            for rr in rows:
                for cc in range(start, w - 1):
                    out[rr][cc] = color
    return out


def first_canonical_row(task_id: str):
    with CANONICAL.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == task_id:
                return row
    raise RuntimeError(task_id)


def build_b08():
    task_id = "b08e9fc77a85"
    module, path = load_generator(task_id)
    low = json.loads((ROOT / "checks" / "audit_b08_grid_h_11.jsonl").read_text())
    high = json.loads((ROOT / "checks" / "audit_b08_grid_h_15.jsonl").read_text())
    low_pair = low["train"][0]
    high_pair = high["train"][0]
    assert low_pair == high_pair
    assert module.self_check(low_pair["input"]) == []
    actual_h = len(low_pair["input"])
    assert actual_h not in (11, 15)
    return {
        "schema": "audit_counterexample/1",
        "task_id": task_id,
        "generator_sha256": sha(path),
        "declared_rule_hash": module.RULE_HASH,
        "executed_rule_hash": low["executed_rule_hash"],
        "finding": "advertised exact grid_h override is accepted but ignored",
        "seed": 44017,
        "sample_index": 0,
        "difficulty": "medium",
        "override_a": {"grid_h": 11},
        "override_b": {"grid_h": 15},
        "same_input_and_racket_output": True,
        "actual_shape": [len(low_pair["input"]), len(low_pair["input"][0])],
        "validator_findings": module.self_check(low_pair["input"]),
        "input": low_pair["input"],
        "actual_racket_output": low_pair["output"],
        "commands": [
            ["python3", "run_with_racket.py", "python3", "-m", "arcpuzzles", "generate", task_id, "--count", "1", "--seed", "44017", "--sample-index", "0", "--difficulty", "medium", "--train", "1", "--test", "1", "--override", "grid_h=11", "--allow-unapproved", "--out", "../checks/audit_b08_grid_h_11.jsonl"],
            ["python3", "run_with_racket.py", "python3", "-m", "arcpuzzles", "generate", task_id, "--count", "1", "--seed", "44017", "--sample-index", "0", "--difficulty", "medium", "--train", "1", "--test", "1", "--override", "grid_h=15", "--allow-unapproved", "--out", "../checks/audit_b08_grid_h_15.jsonl"],
        ],
        "cwd": "packet_root",
    }


def build_8a07():
    task_id = "8a07ec9e021a"
    module, path = load_generator(task_id)
    episode = json.loads((ROOT / "checks" / "audit_8a07_episode.jsonl").read_text())
    generated_pairs = episode["train"] + episode["test"]
    assert all(right_only_rival(pair["input"]) == pair["output"] for pair in generated_pairs)

    generated_edges = Counter()
    invalid = []
    unique = set()
    band_counts = {}
    for band_index, band in enumerate(("easy", "medium", "hard")):
        seed = 92000 + band_index * 10000
        local = Counter()
        for sample_index in range(100):
            grid = module.generate(seed, sample_index, difficulty=band)
            findings = module.self_check(grid, difficulty=band)
            if findings:
                invalid.append({"band": band, "sample_index": sample_index, "findings": findings})
            edges = tuple(full_gray_edges(grid))
            local[str(edges)] += 1
            generated_edges[str(edges)] += 1
            unique.add(json.dumps(grid, separators=(",", ":")))
        band_counts[band] = dict(local)

    canonical = first_canonical_row(task_id)
    canonical_pairs = canonical["train"] + canonical.get("test", [])
    canonical_edge_positions = [full_gray_edges(pair["input"]) for pair in canonical_pairs]
    counterexample = canonical["train"][1]
    assert full_gray_edges(counterexample["input"]) == ["bottom"]
    rival = right_only_rival(counterexample["input"])
    assert rival != counterexample["output"]

    return {
        "schema": "audit_counterexample/1",
        "task_id": task_id,
        "generator_sha256": sha(path),
        "declared_rule_hash": getattr(module, "RULE_HASH", None),
        "executed_rule_hash": episode["executed_rule_hash"],
        "finding": "edge-position domain collapses to right although canonical demonstrations cover all four outer edges",
        "generated_scan": {
            "sampler": "module.generate(seed, sample_index, difficulty=band)",
            "bands": band_counts,
            "draws_per_band": 100,
            "total_draws": 300,
            "unique_inputs": len(unique),
            "edge_counts": dict(generated_edges),
            "invalid_draws": invalid,
        },
        "racket_episode_check": {
            "seed": 123,
            "sample_indices": episode["sample_indices"],
            "pairs": len(generated_pairs),
            "right_only_rival_matches": sum(
                right_only_rival(pair["input"]) == pair["output"]
                for pair in generated_pairs
            ),
            "source": "checks/audit_8a07_episode.jsonl",
        },
        "canonical_edge_positions": canonical_edge_positions,
        "counterexample_source": "canonical train[1]",
        "counterexample_input": counterexample["input"],
        "actual_canonical_output": counterexample["output"],
        "right_only_rival_output": rival,
        "counterexample_in_generator_domain": False,
        "counterexample_validator_note": "Canonical authority example; generator never emits a bottom-edge case in the 300-draw scan.",
        "commands": [
            ["python3", "run_with_racket.py", "python3", "-m", "arcpuzzles", "generate", task_id, "--count", "1", "--seed", "123", "--sample-index", "0", "--difficulty", "medium", "--train", "3", "--test", "1", "--allow-unapproved", "--out", "../checks/audit_8a07_episode.jsonl"],
            ["python3", "checks/audit_findings_probe.py"],
        ],
        "cwd": "packet_root",
    }


if __name__ == "__main__":
    b08 = build_b08()
    a8 = build_8a07()
    (ROOT / "checks" / "audit_b08_override_counterexample.json").write_text(
        json.dumps(b08, indent=2, sort_keys=True) + "\n"
    )
    (ROOT / "checks" / "audit_8a07_edge_collapse.json").write_text(
        json.dumps(a8, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps({
        "b08": {"shape": b08["actual_shape"], "same": b08["same_input_and_racket_output"]},
        "8a07": {
            "generated": a8["generated_scan"]["edge_counts"],
            "canonical": a8["canonical_edge_positions"],
            "rival_matches": a8["racket_episode_check"]["right_only_rival_matches"],
        },
    }, indent=2, sort_keys=True))
