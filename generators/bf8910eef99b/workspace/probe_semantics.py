"""Source-bound production and finite-rival probe for bf8910eef99b."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

from reference_probe import (RIVALS, canonical_pairs, load_generator, observed,
                             oracle_output, racket_outputs, witness_input)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--generator", type=Path)
    parser.add_argument("--per-band", type=int, default=250)
    parser.add_argument("--racket-limit", type=int, default=64)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.per_band < 1 or args.racket_limit < 0:
        parser.error("counts must be nonnegative and per-band must be positive")
    module = load_generator(args.generator)
    generator_path = Path(args.generator or Path(__file__).resolve().parents[1] / "generator.py")
    failures, samples, unique = [], [], set()
    counts = Counter()
    coverage = {str(band): {"profiles": set(), "palettes": set(), "shapes": set()}
                for band in (None, "easy", "medium", "hard")}

    labelled = canonical_pairs()
    for pair in labelled:
        if module.self_check(pair["input"]):
            failures.append({"kind": "canonical_rejected", "pair": [pair["split"], pair["pair_index"]]})
        if oracle_output(pair["input"]) != pair["output"]:
            failures.append({"kind": "oracle_canonical_mismatch", "pair": [pair["split"], pair["pair_index"]]})
    counts["canonical_pairs"] = len(labelled)

    for band_index, band in enumerate((None, "easy", "medium", "hard")):
        key = str(band)
        for index in range(args.per_band):
            grid = module.generate(12000 + band_index * 1000 + index, index * 17 + 3,
                                   difficulty=band)
            counts["generated"] += 1
            if grid != module.generate(12000 + band_index * 1000 + index, index * 17 + 3,
                                       difficulty=band):
                failures.append({"kind": "nondeterministic", "band": band, "index": index})
            errors = module.self_check(grid)
            if errors:
                failures.append({"kind": "self_check", "band": band, "index": index,
                                 "errors": errors})
                continue
            digest = hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()
            unique.add(digest)
            stats = observed(grid)
            coverage[key]["profiles"].add(stats["placement_profile"])
            coverage[key]["palettes"].add(stats["palette_id"])
            coverage[key]["shapes"].add((stats["grid_h"], stats["grid_w"]))
            truth = oracle_output(grid)
            for name, rival in RIVALS.items():
                counts[f"rival_refuted:{name}"] += rival(grid) != truth
                if rival(grid) == truth:
                    failures.append({"kind": "rival_survived", "rival": name,
                                     "band": band, "index": index, "input_sha256": digest})
            if len(samples) < args.racket_limit:
                samples.append(grid)

    racket = {"status": "not_requested", "checked": 0}
    if args.racket_limit:
        grids = [pair["input"] for pair in labelled] + [witness_input()] + samples
        outputs = racket_outputs(grids)
        mismatches = [index for index, (grid, out) in enumerate(zip(grids, outputs))
                      if oracle_output(grid) != out]
        racket = {"status": "passed" if not mismatches else "failed",
                  "checked": len(grids), "mismatches": mismatches}
        if mismatches:
            failures.append({"kind": "racket_mismatch", "indices": mismatches})

    normalized_coverage = {
        band: {"profiles": sorted(values["profiles"]),
               "palettes": sorted(values["palettes"]),
               "shapes": [list(shape) for shape in sorted(values["shapes"])]}
        for band, values in coverage.items()
    }
    report = {
        "schema": "bf8910eef99b-semantic-probe-v1",
        "generator_sha256": hashlib.sha256(generator_path.read_bytes()).hexdigest(),
        "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "per_band": args.per_band,
        "counts": dict(counts),
        "unique_inputs": len(unique),
        "coverage": normalized_coverage,
        "racket": racket,
        "failures": failures,
        "status": "passed" if not failures else "failed",
        "limitation": "Finite testing against five declared rivals; it is not a proof of unique induction.",
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": report["status"], "counts": report["counts"],
                      "unique_inputs": report["unique_inputs"], "racket": racket}, indent=2))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
