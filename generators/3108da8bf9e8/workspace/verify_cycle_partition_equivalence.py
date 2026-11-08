#!/usr/bin/env python3
"""Exhaustively verify the generator's cycle-packing shortcut predicate."""
from __future__ import annotations

import importlib.util
import itertools
import json
import sys
from pathlib import Path

TASK_ID = "3108da8bf9e8"


def _load_generator():
    repo = Path(__file__).resolve().parents[3]
    runtime = repo / "shared" / "runtime"
    sys.path.insert(0, str(runtime))
    path = repo / "generators" / TASK_ID / "generator.py"
    spec = importlib.util.spec_from_file_location("cycle_partition_generator", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def integer_partitions(total: int, maximum: int | None = None):
    maximum = total if maximum is None else min(maximum, total)
    if total == 0:
        yield ()
        return
    for first in range(maximum, 0, -1):
        for rest in integer_partitions(total - first, first):
            yield (first, *rest)


def brute_pack(lengths: tuple[int, ...]) -> bool:
    for assignment in itertools.product(range(3), repeat=len(lengths)):
        bins = [0, 0, 0]
        for length, target in zip(lengths, assignment):
            bins[target] += length
        if bins == [3, 3, 3]:
            return True
    return False


def main() -> int:
    generator = _load_generator()
    rows = []
    for lengths in integer_partitions(9):
        expected = brute_pack(lengths)
        observed = generator._cycles_pack_into_three_triples(lengths)
        rows.append({"cycle_lengths": lengths, "brute": expected, "helper": observed})
        if expected != observed:
            print(json.dumps({"mismatch": rows[-1]}, indent=2))
            return 1
    print(json.dumps({"integer_partitions_checked": len(rows), "mismatches": 0, "rows": rows}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
