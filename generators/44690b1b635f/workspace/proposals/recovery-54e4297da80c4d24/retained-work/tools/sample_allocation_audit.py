#!/usr/bin/env python3
"""Reproduce the assignment-seeded allocation-audit sample from a packet manifest."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import random
import re
import sys


GENERATOR_PATH = re.compile(r"(?:^|/)repo/generators/([0-9a-f]{12})(?:/|$)")


def read_generator_ids(manifest: dict) -> list[str]:
    ids = set()
    explicit = manifest.get("generator_ids")
    if isinstance(explicit, list):
        ids.update(value for value in explicit if isinstance(value, str) and re.fullmatch(r"[0-9a-f]{12}", value))
    files = manifest.get("files", {})
    paths = files.keys() if isinstance(files, dict) else files if isinstance(files, list) else []
    for value in paths:
        path = value if isinstance(value, str) else value.get("path", "") if isinstance(value, dict) else ""
        match = GENERATOR_PATH.search(path)
        if match:
            ids.add(match.group(1))
    return sorted(ids)


def sample_ids(manifest: dict, seed: str, count: int = 3) -> dict:
    try:
        seed_int = int(seed, 16)
    except ValueError as exc:
        raise ValueError("seed must be hexadecimal") from exc
    ids = read_generator_ids(manifest)
    if not ids:
        raise ValueError("no generator IDs found in packet manifest")
    if count < 1:
        raise ValueError("count must be positive")
    rng = random.Random(seed_int)
    sampled = rng.sample(ids, min(count, len(ids)))
    return {
        "schema": "arcpuzzles-allocation-audit-sample-v1",
        "seed": seed,
        "population": len(ids),
        "sampled_ids": sampled,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--seed", required=True)
    parser.add_argument("--count", type=int, default=3)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    try:
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
        result = sample_ids(manifest, args.seed, args.count)
        text = json.dumps(result, indent=2, sort_keys=True) + "\n"
        if args.out:
            args.out.parent.mkdir(parents=True, exist_ok=True)
            args.out.write_text(text, encoding="utf-8")
        else:
            sys.stdout.write(text)
        return 0
    except (OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
