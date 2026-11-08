"""Compare exact selection, RNG state, and allocations for explicit sources.

Run in the prepared task runtime, or supply its location through PYTHONPATH.
The timings include tracemalloc overhead and are descriptive, not test gates.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import random
import time
import tracemalloc


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ValueError(f"cannot load source: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _measure(path, name, *, require_side=False):
    module = _load(path, name)
    height, width, bbox, count = 15, 15, (2, 5, 5, 8), 3
    # Freeze the original maximum supported slot set so both source versions
    # measure the sampler mechanism even if placement coverage also changes.
    original_slots = [
        (row, col)
        for row in range(height)
        for col in range(width - 1)
        if row <= bbox[0] - 2 or row >= bbox[2] + 2
        or (require_side and bbox[0] <= row <= bbox[2]
            and (col <= bbox[1] - 3 or col >= bbox[3] + 2))
    ]
    module._legend_slots = lambda *args: original_slots
    rng = random.Random(42)
    tracemalloc.start()
    try:
        started = time.perf_counter()
        kwargs = {"require_side": True} if require_side else {}
        selected = module._choose_legend_slots(height, width, bbox, count, rng, **kwargs)
        elapsed = time.perf_counter() - started
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    state = rng.getstate()
    return {
        "candidate_slot_count": len(original_slots),
        "selected": selected,
        "next_rng_value": rng.random(),
        "peak_bytes": peak,
        "elapsed_seconds_under_tracemalloc": elapsed,
    }, state


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--before-source", required=True, type=Path)
    parser.add_argument("--after-source", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    before, before_state = _measure(args.before_source, "probe_before")
    after, after_state = _measure(args.after_source, "probe_after")
    after_required_side, _ = _measure(args.after_source, "probe_after_side", require_side=True)
    result = {
        "fixture": {"height": 15, "width": 15, "bbox": [2, 5, 5, 8], "pair_count": 3, "seed": 42, "slot_set": "original whole rows"},
        "before": before,
        "after": after,
        "same_selection": before["selected"] == after["selected"],
        "same_rng_state": before_state == after_state,
        "expanded_required_side_fixture": {"height": 15, "width": 15, "bbox": [2, 5, 5, 8], "pair_count": 3, "seed": 42, "slot_set": "whole rows plus left and right crop-row slots"},
        "after_required_side": after_required_side,
    }
    serialized = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.write_text(serialized)
    print(serialized, end="")


if __name__ == "__main__":
    main()
