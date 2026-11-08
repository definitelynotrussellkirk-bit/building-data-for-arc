from __future__ import annotations
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "repo"
OUT = Path(__file__).resolve().parent


def load(tid):
    path = ROOT / "generators" / tid / "generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_{tid}", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module, path


def grid_hash(grid):
    payload = json.dumps(grid, separators=(",", ":"), sort_keys=True).encode()
    return hashlib.sha256(payload).hexdigest()


def main():
    tid = "d50ba3ef0962"
    gen, path = load(tid)
    variants = {
        "palette_warm": gen.generate(123, 5, palette_kind="warm"),
        "palette_cool": gen.generate(123, 5, palette_kind="cool"),
        "grid_w_9": gen.generate(123, 5, grid_w=9),
        "grid_w_18": gen.generate(123, 5, grid_w=18),
    }
    report = {
        "schema": "arc-audit-reproducer-v1",
        "task_id": tid,
        "generator_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "seed": 123,
        "sample_index": 5,
        "finding": "declared palette_kind and grid_w overrides are accepted but unobservable",
        "observations": {
            name: {
                "sha256": grid_hash(grid),
                "height": len(grid),
                "width": len(grid[0]),
                "self_check": gen.self_check(grid),
            }
            for name, grid in variants.items()
        },
        "equalities": {
            "palette_warm_equals_palette_cool": variants["palette_warm"] == variants["palette_cool"],
            "grid_w_9_equals_grid_w_18": variants["grid_w_9"] == variants["grid_w_18"],
        },
        "representative_grid": variants["grid_w_9"],
    }
    (OUT / f"{tid}-dead-controls.json").write_text(json.dumps(report, indent=2) + "\n")

    tid = "881173b7bc9d"
    gen, path = load(tid)
    malformed = {
        "single_cell": [[1]],
        "four_disconnected_singletons": [[1, 0, 2], [0, 0, 0], [3, 0, 4]],
    }
    report = {
        "schema": "arc-audit-reproducer-v1",
        "task_id": tid,
        "generator_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "finding": "self_check accepts grids with no rectangular frame under ordinary meta=None validation",
        "cases": [
            {
                "name": name,
                "grid": grid,
                "self_check": gen.self_check(grid),
            }
            for name, grid in malformed.items()
        ],
    }
    (OUT / f"{tid}-validator-hole.json").write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
