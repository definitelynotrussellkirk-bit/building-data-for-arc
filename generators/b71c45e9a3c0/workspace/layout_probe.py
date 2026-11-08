"""Measure whether generated object positions escape outer-corner shortcuts."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from reference_probe import bbox, color3_components, load_generator


def audit(module, *, count: int = 128):
    source = Path(module.__file__).resolve()
    report = {
        "schema": "b71c45e9a3c0-layout-diversity-v1",
        "generator_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "sample_policy": {
            "per_band": count,
            "seed_start": 880_000,
            "sample_index_formula": "index*19",
        },
        "bands": {},
    }
    for band in (None, "easy", "medium", "hard"):
        samples_with_fully_interior_object = 0
        fully_interior_objects = 0
        total_objects = 0
        bbox_origins = set()
        for index in range(count):
            grid = module.generate(880_000 + index, index * 19, difficulty=band)
            sample_hit = False
            for component in color3_components(grid):
                top, left, bottom, right = bbox(component)
                total_objects += 1
                bbox_origins.add((top, left))
                hit = (
                    top > 1
                    and bottom < len(grid) - 1
                    and left > 0
                    and right < len(grid[0]) - 1
                )
                fully_interior_objects += int(hit)
                sample_hit |= hit
            samples_with_fully_interior_object += int(sample_hit)
        report["bands"][str(band)] = {
            "samples": count,
            "samples_with_fully_interior_object": samples_with_fully_interior_object,
            "fully_interior_objects": fully_interior_objects,
            "total_objects": total_objects,
            "unique_bbox_origins": len(bbox_origins),
        }
    return report


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=128)
    parser.add_argument("--generator")
    parser.add_argument("--out")
    args = parser.parse_args(argv)
    report = audit(load_generator(args.generator), count=args.count)
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
