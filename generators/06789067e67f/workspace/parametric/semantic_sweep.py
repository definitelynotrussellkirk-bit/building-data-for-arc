#!/usr/bin/env python3
"""Many-seed Python-mirror attack on the minimum two-demo lesson.

This tool is deliberately cheap enough for future authors to run after sampler
edits.  Protected Racket remains the semantic authority; ``adversarial_probe``
replays a matching candidate bank through that runtime.
"""
from __future__ import annotations

import argparse
import copy
import importlib.util
import json
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
TASK_ID = "06789067e67f"


def _load_prototype():
    path = HERE / "prototype.py"
    spec = importlib.util.spec_from_file_location("_semantic_06789067e67f", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _canonical_records(proto, grid):
    return sorted(
        proto._components(grid),
        key=lambda record: (-record["holes"], -record["area"], record["color"]),
    )


def _pack(records, *, gap=1, bottom=False, fill_bbox=False):
    height = max(len(record["crop"]) for record in records)
    width = sum(len(record["crop"][0]) for record in records) + gap * (len(records) - 1)
    if height > 30 or width > 30:
        raise ValueError("rival packed output exceeds ARC bounds")
    out = [[0] * width for _ in range(height)]
    offset = 0
    for record in records:
        crop = record["crop"]
        row_offset = height - len(crop) if bottom else 0
        for row, values in enumerate(crop):
            for col, value in enumerate(values):
                out[row_offset + row][offset + col] = record["color"] if fill_bbox else value
        offset += len(crop[0]) + gap
    return out


def _rank(proto, intermediate, *, order="left", value="rank", bbox=False, partial=False):
    records = proto._components(intermediate)
    if order == "left":
        records.sort(key=lambda record: (record["c1"], record["r1"]))
    elif order == "right":
        records.sort(key=lambda record: (-record["c2"], record["r1"]))
    elif order == "color":
        records.sort(key=lambda record: record["color"])
    elif order == "top":
        records.sort(key=lambda record: (record["r1"], record["c1"]))
    else:
        raise KeyError(order)
    out = copy.deepcopy(intermediate)
    for index, record in enumerate(records, start=1):
        paint = index if value == "rank" else (len(records) + 1 - index if value == "reverse" else 1)
        if bbox:
            cells = (
                (row, col)
                for row in range(record["r1"], record["r2"] + 1)
                for col in range(record["c1"], record["c2"] + 1)
            )
        else:
            cells = record["cells"]
        for row, col in cells:
            out[row][col] = paint
        if partial:
            break
    return out


def rival_outputs(proto, grid, setting: dict[str, str]) -> dict[str, list[list[int]]]:
    mode = setting["output_colors"]
    results: dict[str, list[list[int]]] = {
        name: proto.rival_transform(name, grid, setting)
        for name in proto.SORT_RIVALS
    }
    canonical_records = _canonical_records(proto, grid)
    canonical = _pack(canonical_records)

    def finish(intermediate):
        return intermediate if mode == "original" else proto.rank_recolor(intermediate)

    results.update(
        {
            "identity": copy.deepcopy(grid),
            "all_zero": [[0] * len(grid[0]) for _ in grid],
            "gap0": finish(_pack(canonical_records, gap=0)),
            "gap2": finish(_pack(canonical_records, gap=2)),
            "bottom_align": finish(_pack(canonical_records, bottom=True)),
            "filled_bbox": finish(_pack(canonical_records, fill_bbox=True)),
        }
    )
    if mode == "original":
        results["rank_setting"] = proto.rank_recolor(canonical)
    else:
        results.update(
            {
                "original_setting": canonical,
                "skip_pack_rank": proto.skip_pack_counterfactual(grid),
                "partial_rank_first": _rank(proto, canonical, partial=True),
                "reverse_rank": _rank(proto, canonical, value="reverse"),
                "color_rank": _rank(proto, canonical, order="color"),
                "right_to_left_rank": _rank(proto, canonical, order="right"),
                "bbox_rank": _rank(proto, canonical, bbox=True),
                "all_one_rank": _rank(proto, canonical, value="one"),
            }
        )
    return results


def build_report(*, seed_count: int = 200) -> dict[str, Any]:
    if type(seed_count) is not int or not 1 <= seed_count <= 10_000:
        raise ValueError("seed_count must be an exact integer in 1..10000")
    proto = _load_prototype()
    survivors = []
    rival_inventory: dict[str, tuple[str, ...]] = {}
    intermediate_hashes = set()
    source_position_orders = set()
    color_orders = set()
    stress_rows = []
    episodes = 0

    for setting in proto.SETTINGS:
        mode = setting["output_colors"]
        for seed in range(seed_count):
            episode = proto.generate(seed, setting, demos=2, queries=4)
            episodes += 1
            outputs: dict[str, list[list[list[int]]]] = {}
            for pair in episode["train"]:
                intermediate = proto.canonical_transform(pair["input"])
                intermediate_hashes.add(proto.digest(intermediate))
                records = proto._components(pair["input"])
                source_position_orders.add(tuple(record["color"] for record in sorted(records, key=lambda r: r["c1"])))
                color_orders.add(tuple(sorted(record["color"] for record in records)))
                for name, output in rival_outputs(proto, pair["input"], setting).items():
                    outputs.setdefault(name, []).append(output)
            names = tuple(sorted(outputs))
            if mode not in rival_inventory:
                rival_inventory[mode] = names
            elif rival_inventory[mode] != names:
                raise ValueError(f"rival inventory drift for {mode}")
            expected = [pair["output"] for pair in episode["train"]]
            for name, actual in outputs.items():
                if actual != expected:
                    continue
                expected_queries = [pair["output"] for pair in episode["test"]]
                actual_queries = [
                    rival_outputs(proto, pair["input"], setting)[name]
                    for pair in episode["test"]
                ]
                changed = [
                    index
                    for index, (got, want) in enumerate(zip(actual_queries, expected_queries, strict=True))
                    if got != want
                ]
                survivors.append(
                    {
                        "seed": seed,
                        "settings": setting,
                        "rival": name,
                        "query_differences": changed,
                        "ambiguous": bool(changed),
                    }
                )
            stress = episode["test"][3]
            profile = proto.analyze_input(stress["input"])
            if (profile["height"], profile["width"]) != (30, 30):
                raise ValueError("stress query is no longer 30x30")
            if proto.transform(stress["input"], setting) != stress["output"]:
                raise ValueError("stress query label drift")
            if seed < 8:
                stress_rows.append({"seed": seed, "settings": setting, **profile})

    ambiguous = [row for row in survivors if row["ambiguous"]]
    union = sorted({name for names in rival_inventory.values() for name in names})
    return {
        "schema": "arcpuzzles-parametric-semantic-sweep-v1",
        "task_id": TASK_ID,
        "status": "passed" if not survivors else "failed",
        "seed_count": seed_count,
        "episodes": episodes,
        "demos_per_episode": 2,
        "queries_per_episode": 4,
        "rival_inventory": {key: list(value) for key, value in rival_inventory.items()},
        "rival_count": len(union),
        "survivors": survivors,
        "survivor_count": len(survivors),
        "ambiguous_count": len(ambiguous),
        "crossed_controls": {
            "distinct_intermediates": len(intermediate_hashes),
            "source_position_color_orders": len(source_position_orders),
            "palette_orders": len(color_orders),
        },
        "stress_samples": stress_rows,
        "limits": (
            "Finite deterministic sweep over authored Python mirrors. Protected Racket "
            "execution remains authoritative and is exercised by adversarial_probe.py."
        ),
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, default=200)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.out.exists() or args.out.is_symlink():
        raise SystemExit(f"refusing existing output: {args.out}")
    report = build_report(seed_count=args.seeds)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "status": report["status"],
        "seed_count": report["seed_count"],
        "episodes": report["episodes"],
        "rival_count": report["rival_count"],
        "survivor_count": report["survivor_count"],
        "ambiguous_count": report["ambiguous_count"],
        "crossed_controls": report["crossed_controls"],
    }, sort_keys=True))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
