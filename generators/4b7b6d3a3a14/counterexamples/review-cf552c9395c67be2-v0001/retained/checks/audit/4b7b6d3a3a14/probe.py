#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import json
from collections import Counter
from pathlib import Path

TASK_ID = "4b7b6d3a3a14"
BANDS = ("easy", "medium", "hard")
DRAWS_PER_REQUEST = 100
BASE_SEED = 70_000


def load_generator(repo_root: Path):
    source = repo_root / "generators" / TASK_ID / "generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_{TASK_ID}", source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, source


def main() -> None:
    repo_root = Path(__file__).resolve().parents[3] / "repo"
    out_dir = Path(__file__).resolve().parent
    generator, source = load_generator(repo_root)
    by_band = {}
    selected = None

    for band_index, band in enumerate(BANDS):
        band_counts = {}
        for requested_marker in (1, 2):
            stats = Counter()
            for index in range(DRAWS_PER_REQUEST):
                seed = (
                    BASE_SEED
                    + 10_000 * band_index
                    + 1_000 * requested_marker
                    + index
                )
                grid = generator.generate(
                    seed,
                    index,
                    difficulty=band,
                    marker=requested_marker,
                )
                observed_marker = grid[0][0]
                meta = {"overrides": {"marker": requested_marker}}
                validator_errors = generator.self_check(grid, meta=meta)
                mismatch = observed_marker != requested_marker
                stats["draws"] += 1
                stats["mismatches"] += mismatch
                stats["mismatches_accepted_by_self_check"] += (
                    mismatch and not validator_errors
                )
                if selected is None and requested_marker == 2 and mismatch:
                    requested_input = [list(row) for row in grid]
                    requested_input[0][0] = 2
                    selected = {
                        "band": band,
                        "seed": seed,
                        "sample_index": index,
                        "requested_marker": requested_marker,
                        "observed_marker": observed_marker,
                        "validator_errors_with_requested_meta": validator_errors,
                        "input": grid,
                        "input_if_override_honored": requested_input,
                    }
            band_counts[str(requested_marker)] = dict(stats)
        by_band[band] = band_counts

    if selected is None:
        raise RuntimeError("no ignored marker override found")

    source_sha = hashlib.sha256(source.read_bytes()).hexdigest()
    report = {
        "schema": "arc-audit-exact-override-probe-v1",
        "task_id": TASK_ID,
        "generator_sha256": source_sha,
        "axis": "marker",
        "sample_recipe": {
            "bands": list(BANDS),
            "requests": [1, 2],
            "draws_per_request_per_band": DRAWS_PER_REQUEST,
            "seed": "70000 + 10000*band_index + 1000*requested_marker + index",
            "sample_index": "index",
        },
        "counts": by_band,
        "selected_witness": {
            key: value
            for key, value in selected.items()
            if key not in {"input", "input_if_override_honored"}
        },
    }
    (out_dir / "probe.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (out_dir / "input.json").write_text(
        json.dumps(selected["input"], indent=2) + "\n", encoding="utf-8"
    )
    (out_dir / "requested-input.json").write_text(
        json.dumps(selected["input_if_override_honored"], indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
