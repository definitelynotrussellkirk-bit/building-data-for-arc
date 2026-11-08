from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import sys


# Make the probe directly runnable from any working directory.
_REPO_ROOT = Path(__file__).resolve().parents[3]
for _path in (_REPO_ROOT / "src", _REPO_ROOT / "shared" / "runtime"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))


def load_generator(path: Path):
    spec = importlib.util.spec_from_file_location("candidate_6d26bc40cbb2", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def realistic_modal_only(module, grid):
    """Keep the full original payload, but copy only its modal color."""
    analysis = module.analyze_scene(grid)
    if analysis["errors"]:
        raise ValueError(analysis["errors"])
    facts = analysis["facts"]
    counts = Counter(grid[r][c] for r, c in facts["payload"])
    modal = min(counts, key=lambda color: (-counts[color], color))
    height, width = len(grid), len(grid[0])
    dr, dc = facts["delta"]
    out = module._payload_only(grid)
    for row, col in facts["payload"]:
        if grid[row][col] != modal:
            continue
        dst = row + dr, col + dc
        if 0 <= dst[0] < height and 0 <= dst[1] < width:
            out[dst[0]][dst[1]] = modal
    return out


def scan(generator_path: Path, *, seeds: int, max_index: int):
    module = load_generator(generator_path)
    total = refuted = multicolor = multicolor_refuted = 0
    windows = ambiguous_windows = 0
    unique_inputs = set()
    first_ambiguous = []
    first_nonrefuting = []
    by_band = {}

    for band in ("easy", "medium", "hard"):
        band_stats = Counter()
        for seed in range(1, seeds + 1):
            cache = {}
            for index in range(max_index + 1):
                grid = module.generate(seed, index, difficulty=band)
                encoded = json.dumps(grid, separators=(",", ":"))
                unique_inputs.add(encoded)
                authoritative = module.solve_python(grid)
                rival = realistic_modal_only(module, grid)
                disagree = rival != authoritative
                facts = module.analyze_scene(grid)["facts"]
                palette_size = facts["palette_size"]
                cache[index] = disagree

                total += 1
                refuted += int(disagree)
                band_stats["samples"] += 1
                band_stats["refuted"] += int(disagree)
                if palette_size > 1:
                    multicolor += 1
                    multicolor_refuted += int(disagree)
                    band_stats["multicolor"] += 1
                    band_stats["multicolor_refuted"] += int(disagree)
                    if not disagree and len(first_nonrefuting) < 10:
                        first_nonrefuting.append(
                            {
                                "band": band,
                                "seed": seed,
                                "sample_index": index,
                                "facts": facts,
                                "grid": grid,
                                "authoritative": authoritative,
                                "rival": rival,
                            }
                        )

            for start in range(max_index - 1):
                windows += 1
                band_stats["windows"] += 1
                indices = (start, start + 1, start + 2)
                if not any(cache[index] for index in indices):
                    ambiguous_windows += 1
                    band_stats["ambiguous_windows"] += 1
                    if len(first_ambiguous) < 25:
                        first_ambiguous.append(
                            {
                                "band": band,
                                "seed": seed,
                                "start": start,
                                "indices": list(indices),
                            }
                        )
        by_band[band] = dict(band_stats)

    raw = generator_path.read_bytes()
    return {
        "schema": "6d26bc40cbb2-modal-shortcut-probe-v2",
        "generator": str(generator_path),
        "generator_sha256": hashlib.sha256(raw).hexdigest(),
        "version": getattr(module, "VERSION", None),
        "seeds_per_band": seeds,
        "sample_indices": [0, max_index],
        "samples": total,
        "unique_inputs": len(unique_inputs),
        "shortcut_refuted": refuted,
        "shortcut_refuted_fraction": refuted / total,
        "multicolor_samples": multicolor,
        "multicolor_refuted": multicolor_refuted,
        "multicolor_refuted_fraction": multicolor_refuted / multicolor,
        "three_example_windows": windows,
        "ambiguous_three_example_windows": ambiguous_windows,
        "by_band": by_band,
        "first_ambiguous_windows": first_ambiguous,
        "first_nonrefuting_multicolor_samples": first_nonrefuting,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--generator", type=Path, default=Path(__file__).resolve().parents[1] / "generator.py")
    parser.add_argument("--out", type=Path, default=Path(__file__).with_name("modal_shortcut_probe_after.json"))
    parser.add_argument("--seeds", type=int, default=100)
    parser.add_argument("--max-index", type=int, default=52)
    args = parser.parse_args()

    report = scan(args.generator.resolve(), seeds=args.seeds, max_index=args.max_index)
    args.out.write_text(json.dumps(report, indent=2, default=list) + "\n")
    summary_keys = (
        "generator_sha256",
        "version",
        "samples",
        "unique_inputs",
        "multicolor_samples",
        "multicolor_refuted",
        "multicolor_refuted_fraction",
        "three_example_windows",
        "ambiguous_three_example_windows",
    )
    print(json.dumps({key: report[key] for key in summary_keys}, indent=2))
    if report["first_ambiguous_windows"]:
        print("FIRST_AMBIGUOUS", report["first_ambiguous_windows"][0])
    if report["first_nonrefuting_multicolor_samples"]:
        witness = report["first_nonrefuting_multicolor_samples"][0]
        print(
            "FIRST_NONREFUTING_MULTICOLOR",
            {key: witness[key] for key in ("band", "seed", "sample_index")},
        )


if __name__ == "__main__":
    main()
