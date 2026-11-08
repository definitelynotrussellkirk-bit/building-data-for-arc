from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

TASK_ID = "258e1a721c75"
TICKET_ID = "ticket-30fe1ef4c0aed250"
SEED_HEX = "e09f5ced9157801520ecc23a42e4c9b19405f549a7f01c2ae093e00ee0cf237d"
EXPECTED_SOURCE_SHA256 = "9cdc0d631cabeb95ff87a9c3bfecb77f8ca0dfcf82ef43abca7047243caa7e0a"
SOURCE = Path("generators") / TASK_ID / "generator.py"
OUT = Path("../checks/tickets") / TICKET_ID / "result.json"


def load_generator():
    spec = importlib.util.spec_from_file_location(f"ticket_{TASK_ID}", SOURCE)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {SOURCE}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def grid_sha256(grid) -> str:
    raw = json.dumps(grid, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def palette_size(grid) -> int:
    return sum(value not in (0, 2) for value in grid[0])


def main() -> None:
    source_sha = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    if source_sha != EXPECTED_SOURCE_SHA256:
        raise AssertionError(f"pinned source drift: {source_sha}")
    module = load_generator()
    seed = int(SEED_HEX, 16)
    calls = {
        "baseline": {},
        "valid_palette_size_2": {"palette_size": 2},
        "invalid_palette_size_999": {"palette_size": 999},
    }
    observed = {}
    for name, overrides in calls.items():
        try:
            grid = module.generate(seed, 0, **overrides)
        except Exception as exc:  # retain actual boundary behavior
            observed[name] = {
                "accepted": False,
                "exception_type": type(exc).__name__,
                "exception": str(exc),
            }
        else:
            observed[name] = {
                "accepted": True,
                "grid_sha256": grid_sha256(grid),
                "shape": [len(grid), len(grid[0])],
                "observed_palette_size": palette_size(grid),
                "grid": grid,
            }

    hashes = {
        row.get("grid_sha256")
        for row in observed.values()
        if row.get("accepted")
    }
    finding = (
        all(row.get("accepted") for row in observed.values())
        and len(hashes) == 1
        and observed["valid_palette_size_2"]["observed_palette_size"] == 3
        and observed["invalid_palette_size_999"]["observed_palette_size"] == 3
    )
    result = {
        "schema": "arcpuzzles-ticket-api-boundary-v1",
        "ticket_id": TICKET_ID,
        "task_id": TASK_ID,
        "source": {
            "path": str(SOURCE),
            "sha256": source_sha,
        },
        "probe_seed_hex": SEED_HEX,
        "sample_index": 0,
        "advertised_axis": module.AXES["palette_size"],
        "calls": calls,
        "observed": observed,
        "finding": finding,
        "finding_summary": (
            "The advertised palette_size override is not consumed: both the valid value 2 "
            "and invalid value 999 are accepted, produce the identical grid, and retain a "
            "three-color palette."
            if finding else
            "The retained calls did not establish the expected ignored-override boundary."
        ),
        "scope": "One pinned source, one seed/sample, one valid/invalid comparison; no peer battery.",
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "finding": finding,
        "source_sha256": source_sha,
        "grid_hashes": sorted(hashes),
        "observed_palette_sizes": {
            k: v.get("observed_palette_size") for k, v in observed.items()
        },
        "accepted": {k: v.get("accepted") for k, v in observed.items()},
        "result": str(OUT),
    }, indent=2, sort_keys=True))
    if not finding:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
