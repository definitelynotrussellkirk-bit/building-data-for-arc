from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

from reviewer_support import canonical_pairs


def load_generator(root: Path, task_id: str):
    path = root / "generators" / task_id / "generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_{task_id}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, path


def sizes_from_grid(module, grid):
    return sorted(len(comp) for comp in module._nonzero_components(grid))


def probe_4c(root: Path):
    task_id = "4c5a96f13170"
    module, path = load_generator(root, task_id)
    canonical = canonical_pairs(task_id, root=root, labeled_only=True)
    checked = []
    for index, pair in enumerate(canonical):
        findings = module.self_check(pair["input"])
        checked.append(
            {
                "index": index,
                "split": pair.get("split"),
                "component_sizes": sizes_from_grid(module, pair["input"]),
                "self_check_findings": findings,
            }
        )

    generated = []
    for difficulty in ("easy", None, "hard"):
        label = difficulty or "medium"
        for seed in range(40):
            grid = module.generate(seed, 0, difficulty=difficulty)
            sizes = sizes_from_grid(module, grid)
            generated.append(
                {
                    "difficulty": label,
                    "seed": seed,
                    "sizes": sizes,
                    "tied_sizes": len(sizes) != len(set(sizes)),
                    "self_check": module.self_check(grid),
                }
            )

    return {
        "task_id": task_id,
        "generator_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "canonical_pairs_checked": len(checked),
        "canonical": checked,
        "canonical_rejected": sum(bool(row["self_check_findings"]) for row in checked),
        "generated_draws": len(generated),
        "generated_tied_sizes": sum(row["tied_sizes"] for row in generated),
        "generated_self_check_failures": sum(bool(row["self_check"]) for row in generated),
        "generated_examples": generated,
        "finding": (
            "The generator classifies tied blob sizes as degenerate and its self_check "
            "rejects them, even though tied sizes occur in canonical examples."
        ),
    }


def component_from_seed(grid):
    h, w = len(grid), len(grid[0])
    start = next((r, c) for r in range(h) for c in range(w) if grid[r][c] == 2)
    seen = {start}
    stack = [start]
    while stack:
        r, c = stack.pop()
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] in (2, 3, 5):
                seen.add((nr, nc))
                stack.append((nr, nc))
    return seen


def shortcut_recolor_nonisolated_fives(grid):
    h, w = len(grid), len(grid[0])
    out = [row[:] for row in grid]
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 5:
                continue
            if any(
                0 <= r + dr < h and 0 <= c + dc < w and grid[r + dr][c + dc] in (2, 3, 5)
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))
            ):
                out[r][c] = 4
    return out


def probe_530(root: Path, work: Path):
    task_id = "530e5e07db4c"
    module, path = load_generator(root, task_id)
    draws = []
    for difficulty in ("easy", None, "hard"):
        label = difficulty or "medium"
        for seed in range(40):
            grid = module.generate(seed, 0, difficulty=difficulty)
            component = component_from_seed(grid)
            three = next((r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 3)
            draws.append(
                {
                    "difficulty": label,
                    "seed": seed,
                    "three_reached": three in component,
                    "self_check": module.self_check(grid),
                }
            )

    input_path = work / "checks" / "audit" / task_id / "disconnected-input.json"
    racket_path = work / "checks" / "audit" / task_id / "disconnected-racket.json"
    grid = json.loads(input_path.read_text())
    authority = json.loads(racket_path.read_text())
    expected = authority["results"][0]["output"]
    rival = shortcut_recolor_nonisolated_fives(grid)
    return {
        "task_id": task_id,
        "generator_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "executed_rule_hash": authority["executed_rule_hash"],
        "generated_draws": len(draws),
        "generated_disconnected": sum(not row["three_reached"] for row in draws),
        "generated_self_check_failures": sum(bool(row["self_check"]) for row in draws),
        "counterexample_input": grid,
        "authority_output": expected,
        "shortcut_output": rival,
        "outputs_disagree": expected != rival,
        "authority_leaves_input_unchanged": expected == grid,
        "finding": (
            "All sampled lessons take the connected branch, so recoloring every "
            "non-isolated 5 fits them; the Racket-labelled disconnected input refutes it."
        ),
        "draws": draws,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    root = Path.cwd().resolve()
    if not (root / "shared" / "data" / "canonical" / "puzzles.jsonl").is_file():
        raise RuntimeError(f"expected repository root cwd, got {root}")
    work = root.parent
    report = {
        "schema": "arcpuzzles-audit-probe-v1",
        "530e5e07db4c": probe_530(root, work),
        "4c5a96f13170": probe_4c(root),
    }
    out = Path(args.out)
    if not out.is_absolute():
        out = Path.cwd() / out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({
        "530_disconnected_generated": report["530e5e07db4c"]["generated_disconnected"],
        "530_outputs_disagree": report["530e5e07db4c"]["outputs_disagree"],
        "4c_canonical_rejected": report["4c5a96f13170"]["canonical_rejected"],
        "4c_generated_tied_sizes": report["4c5a96f13170"]["generated_tied_sizes"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
