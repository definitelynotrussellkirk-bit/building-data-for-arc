"""Read-only Python geometry/override/proxy census, without Racket labels.

Run from any working directory with --out PATH. Bind source to this script's
own checkout or staged runtime, never to a sibling checkout or ambient cwd.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import re
import sys


for ancestor in Path(__file__).resolve().parents:
    for runtime in (ancestor / "shared" / "runtime", ancestor):
        if (runtime / "reviewer_support.py").is_file():
            sys.path.insert(0, str(runtime))
            break
    else:
        continue
    break

from reviewer_support import find_root

TASK_ID = "457b4958145b"
SEED = 31337
BANDS = (None, "easy", "medium", "hard")
SAMPLE_INDICES = (0, 1)


def load_generator():
    root = find_root(__file__)
    paths = (root / "generators" / TASK_ID / "generator.py",
             root / "puzzle_generators" / "per_puzzle" / TASK_ID / "generator.py")
    source = next(path for path in paths if path.is_file())
    spec = importlib.util.spec_from_file_location("hub_order_contract_probe", source)
    if spec is None or spec.loader is None:
        raise ValueError(f"Cannot load generator: {source}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return source, module


def axis_values(module, name):
    axis = module.AXES[name]
    match = re.fullmatch(r"(-?\d+)\.\.(-?\d+)", axis["valid"])
    if axis.get("type") != "int" or match is None:
        raise ValueError(f"Expected declared inclusive integer range for {name}: {axis}")
    low, high = map(int, match.groups())
    if high < low:
        raise ValueError(f"Reversed declared range for {name}: {axis}")
    return range(low, high + 1)


def valid_proxy_grid(grid):
    return (isinstance(grid, list) and 0 < len(grid) <= 30
            and all(isinstance(row, list) and 0 < len(row) <= 30 for row in grid)
            and len({len(row) for row in grid}) == 1
            and all(type(value) is int and 0 <= value <= 9 for row in grid for value in row))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True, help="JSON receipt destination")
    args = parser.parse_args()
    source, module = load_generator()
    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    ranges = {name: axis_values(module, name) for name in module.AXES}
    witnesses = dict(module.SEMANTIC_WITNESSES)
    rivals = dict(module.SEMANTIC_RIVALS)
    witness_rivals = dict(module.WITNESS_RIVALS)
    failures = []
    exact_count = contrast_count = adaptation_count = frequency_count = 0
    witness_counts = collections.Counter()
    rival_counts = collections.Counter()
    band_counts = {}

    for name, related in witness_rivals.items():
        if name not in witnesses or not set(related) <= set(rivals):
            failures.append({"kind": "undeclared_witness_or_rival", "witness": name,
                             "rivals": related})

    def inspect(grid, expected, context):
        diagnostics = module.self_check(grid)
        observed = module.observe_overrides(grid)
        if diagnostics or any(observed.get(name) != value for name, value in expected.items()):
            failures.append({"kind": "exact_axes_or_self_check", **context,
                             "expected": expected, "observed": observed,
                             "diagnostics": diagnostics})

    for band in BANDS:
        for height, width, n in itertools.product(ranges["grid_h"], ranges["grid_w"],
                                                   ranges["n_components"]):
            for palette in ranges["palette_size"]:
                if palette > n + 2:
                    continue
                for index in SAMPLE_INDICES:
                    overrides = {"grid_h": height, "grid_w": width,
                                 "n_components": n, "palette_size": palette}
                    context = {"band": band, "sample_index": index, "overrides": overrides}
                    exact_count += 1
                    try:
                        grid = module.generate(SEED, index, difficulty=band, **overrides)
                        inspect(grid, {**overrides, "n_distinct_colors": palette}, context)
                        # This source promises a combined contrast scene at even
                        # indices when >=3 object colors are available (total >=5).
                        if index == 0 and palette >= 5:
                            contrast_count += 1
                            observed_witnesses = {}
                            for name, hook in witnesses.items():
                                witness_counts[name] += 1
                                observed_witnesses[name] = bool(hook(grid))
                            if not all(observed_witnesses.values()):
                                failures.append({"kind": "contrast_rival_separation", **context,
                                                 "witnesses": observed_witnesses})
                            for name, hook in rivals.items():
                                rival_counts[name] += 1
                                if not valid_proxy_grid(hook(grid)):
                                    failures.append({"kind": "malformed_python_rival_output",
                                                     **context, "rival": name})
                    except Exception as exc:
                        failures.append({"kind": "scene_exception", **context,
                                         "exception": type(exc).__name__, "message": str(exc)})

        for palette in ranges["palette_size"]:
            for index in SAMPLE_INDICES:
                adaptation_count += 1
                context = {"band": band, "palette_size": palette, "sample_index": index}
                try:
                    grid = module.generate(17, index, difficulty=band, palette_size=palette)
                    inspect(grid, {"palette_size": palette, "n_distinct_colors": palette}, context)
                except Exception as exc:
                    failures.append({"kind": "palette_only_exception", **context,
                                     "exception": type(exc).__name__, "message": str(exc)})

        counts = collections.Counter()
        for seed in range(300):
            frequency_count += 1
            try:
                grid = module.generate(seed, seed % 10, difficulty=band)
                counts[module.observe_overrides(grid)["n_components"]] += 1
            except Exception as exc:
                failures.append({"kind": "band_frequency_exception", "band": band, "seed": seed,
                                 "exception": type(exc).__name__, "message": str(exc)})
        band_counts[str(band)] = dict(counts)

    final_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    if final_hash != source_hash:
        failures.append({"kind": "source_changed_during_probe", "before": source_hash,
                         "after": final_hash})
    exit_code = int(bool(failures))
    report = {
        "schema": "task-only-code-review-probe-v1", "task_id": TASK_ID,
        "generator_path": str(source), "generator_sha256": source_hash,
        "generator_sha256_after_probe": final_hash,
        "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "command": list(sys.orig_argv), "cwd": str(Path.cwd()),
        "racket_executions": 0, "label_authority_used": False,
        "scope": "Python geometry, exact observed axes, and declared Python witness/rival probes; no Racket labels.",
        "declared_axes": module.AXES,
        "declared_semantic_witnesses": list(witnesses), "declared_semantic_rivals": list(rivals),
        "declared_witness_rivals": witness_rivals,
        "exact_scene_census": {
            "seed": SEED, "bands": list(BANDS),
            "axis_ranges_inclusive": {name: [values.start, values.stop - 1]
                                       for name, values in ranges.items()},
            "palette_size": "all declared integers <= n_components + 2",
            "sample_indices": list(SAMPLE_INDICES), "scene_count": exact_count,
            "checks": ["self_check returns []", "all five observed axes match requested values and palette alias",
                       "sample_index=0 and palette_size>=5 fires every declared semantic witness",
                       "every declared Python rival produces a rectangular integer-color proxy grid"],
            "contrast_witness_scene_count": contrast_count,
            "witness_evaluations_by_name": dict(witness_counts),
            "rival_evaluations_by_name": dict(rival_counts),
        },
        "palette_only_adaptation": {
            "seed": 17, "bands": list(BANDS),
            "palette_size_inclusive": [ranges["palette_size"].start, ranges["palette_size"].stop - 1],
            "sample_indices": list(SAMPLE_INDICES), "scene_count": adaptation_count,
            "checks": ["self_check returns []", "both observed palette aliases equal requested total palette"],
        },
        "band_frequency_probe": {
            "seeds_inclusive": [0, 299], "sample_index": "seed % 10", "bands": list(BANDS),
            "scene_count": frequency_count, "counts_by_n_components": band_counts,
        },
        "total_generated_scene_count": exact_count + adaptation_count + frequency_count,
        "failure_count": len(failures), "failures": failures, "exit_code": exit_code,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"receipt": str(args.out), "generator_sha256": source_hash,
                      "probe_sha256": report["probe_sha256"], "exact_scene_count": exact_count,
                      "contrast_witness_scene_count": contrast_count,
                      "palette_only_scene_count": adaptation_count,
                      "band_frequency_scene_count": frequency_count,
                      "failure_count": len(failures), "exit_code": exit_code, "racket_executions": 0}))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
